from dash import Input, Output, State, html
import dash
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from dash import dash_table

from utils.api_client import APIClient


def register_period_callbacks(app):
    """Register period management callbacks."""
    
    api_client = APIClient()

    @app.callback(
        [
            Output("period-create-message", "children"),
            Output("period-create-message", "color"),
            Output("period-create-message", "is_open"),
            Output("period-name-input", "value"),
            Output("period-start-date", "value"),
            Output("period-end-date", "value"),
            Output("period-table-container", "children", allow_duplicate=True),
        ],
        [Input("create-period-btn", "n_clicks")],
        [
            State("period-name-input", "value"),
            State("period-start-date", "value"),
            State("period-end-date", "value"),
            State("session-store", "data"),
        ],
        prevent_initial_call=True,
    )
    def create_period(n_clicks, period_name, start_date, end_date, session_data):
        """Handle period creation."""
        print(f"DEBUG: create_period triggered, n_clicks={n_clicks}, name={period_name}")
        if not n_clicks:
            raise PreventUpdate

        # Validate inputs
        if not period_name or not start_date or not end_date:
            return (
                "Please fill in all fields",
                "warning",
                True,
                period_name,
                start_date,
                end_date,
                [],
            )

        # Validate dates
        if start_date > end_date:
            return (
                "Start date must be before or equal to end date",
                "danger",
                True,
                period_name,
                start_date,
                end_date,
                [],
            )

        # Get token
        if not session_data or "token" not in session_data:
            return (
                "Please log in first",
                "danger",
                True,
                period_name,
                start_date,
                end_date,
                [],
            )

        token = session_data["token"]
        api_client.set_token(token)

        # Create period (snapshot_date = end_date)
        response = api_client.post(
            "/periods/",
            {
                "period_name": period_name,
                "start_date": start_date,
                "end_date": end_date,
                "snapshot_date": end_date,  # Auto-set as per requirement
            },
        )

        if "error" in response:
            return (
                f"Error creating period: {response['error']}",
                "danger",
                True,
                period_name,
                start_date,
                end_date,
                [],
            )

        # Success - clear form and refresh table
        periods_response = api_client.get("/periods/")
        table = create_period_table(periods_response if "error" not in periods_response else [])

        return (
            f"Period '{period_name}' created successfully!",
            "success",
            True,
            "",  # Clear name
            "",  # Clear start date
            "",  # Clear end date
            table,
        )

    @app.callback(
        Output("period-table-container", "children"),
        [Input("url", "pathname"), Input("session-store", "data")],
    )
    def load_periods(pathname, session_data):
        """Load periods when navigating to the periods page."""
        if not pathname or not pathname.startswith("/dashboard"):
            raise PreventUpdate

        if not session_data or "token" not in session_data:
            return html.Div("Please log in to view periods", className="text-muted")

        token = session_data["token"]
        api_client.set_token(token)

        response = api_client.get("/periods/")

        if "error" in response:
            return html.Div(
                f"Error loading periods: {response['error']}", className="text-danger"
            )

        return create_period_table(response)


    @app.callback(
        Output("period-table-container", "children", allow_duplicate=True),
        [Input({"type": "delete-period-btn", "id": dash.ALL}, "n_clicks")],
        [State("session-store", "data")],
        prevent_initial_call=True
    )
    def delete_period(n_clicks, session_data):
        """Handle period deletion."""
        ctx = dash.callback_context
        if not ctx.triggered:
            raise PreventUpdate
            
        triggered = ctx.triggered[0]
        # Check if actually clicked (n_clicks > 0)
        if not triggered["value"]:
            raise PreventUpdate

        import json
        try:
            # triggered["prop_id"] is likely like '{"id":"...","type":"..."}.n_clicks'
            prop_id = triggered["prop_id"].split(".")[0]
            btn_id = json.loads(prop_id)
            period_id = btn_id["id"]
        except:
             return dash.no_update

        if not session_data or "token" not in session_data:
            return dash.no_update # Or show error toast?

        api_client.set_token(session_data["token"])
        
        # Call delete endpoint (assuming it exists, otherwise we need to add it!)
        # Backend usually supports DELETE /periods/{id}
        resp = api_client.delete(f"/periods/{period_id}")
        
        # Refresh table
        periods = api_client.get("/periods/")
        if "error" in periods:
            return html.Div(f"Error loading periods: {periods['error']}")
            
        return create_period_table(periods)

from utils.ui_helpers import create_empty_state

def create_period_table(periods):
    """Create a dbc.Table from periods data."""
    if not periods or len(periods) == 0:
        return create_empty_state(
            "bi-calendar-x",
            "No periods found",
            "Create your first period above to start managing your budget."
        )

    # Sort by start_date descending
    sorted_periods = sorted(
        periods, key=lambda x: x.get("start_date", ""), reverse=True
    )

    rows = []
    for p in sorted_periods:
        status_color = "success" if p["status"] == "FINALIZED" else "warning"
        is_draft = p["status"] == "DRAFT"
        
        rows.append(
            html.Tr([
                html.Td(p["period_name"], className="fw-bold"),
                html.Td(p["start_date"]),
                html.Td(p["end_date"]),
                html.Td(dbc.Badge(p["status"], color=status_color, className="status-pill")),
                html.Td(
                    dbc.Button(
                        html.I(className="bi bi-trash"),
                        id={"type": "delete-period-btn", "id": p["id"]},
                        color="outline-danger",
                        size="sm",
                        className="btn-rounded border-0",
                        disabled=not is_draft, # Only allow deleting drafts?
                        title="Delete Period (Drafts Only)"
                    )
                , className="text-end")
            ])
        )

    return dbc.Table(
        [
            html.Thead(html.Tr([
                html.Th("Period Name"),
                html.Th("Start Date"),
                html.Th("End Date"),
                html.Th("Status"),
                html.Th("Actions", className="text-end"),
            ])),
            html.Tbody(rows)
        ],
        bordered=False,
        hover=True,
        responsive=True,
        className="align-middle custom-table"
    )
