from dash import Input, Output, State, html
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


def create_period_table(periods):
    """Create a DataTable from periods data."""
    if not periods or len(periods) == 0:
        return html.Div(
            "No periods found. Create your first period above!",
            className="text-muted text-center py-4",
        )

    # Sort by start_date descending
    sorted_periods = sorted(
        periods, key=lambda x: x.get("start_date", ""), reverse=True
    )

    # Prepare data for table
    table_data = [
        {
            "period_name": p.get("period_name", ""),
            "start_date": p.get("start_date", ""),
            "end_date": p.get("end_date", ""),
            "status": p.get("status", "DRAFT"),
            "id": p.get("id", ""),
        }
        for p in sorted_periods
    ]

    return dash_table.DataTable(
        id="periods-table",
        columns=[
            {"name": "Period Name", "id": "period_name"},
            {"name": "Start Date", "id": "start_date"},
            {"name": "End Date", "id": "end_date"},
            {"name": "Status", "id": "status"},
        ],
        data=table_data,
        style_table={"overflowX": "auto"},
        style_cell={
            "textAlign": "left",
            "padding": "10px",
        },
        style_header={
            "backgroundColor": "rgb(230, 230, 230)",
            "fontWeight": "bold",
        },
        style_data_conditional=[
            {
                "if": {"filter_query": "{status} = FINALIZED"},
                "backgroundColor": "rgba(0, 255, 0, 0.1)",
            },
            {
                "if": {"filter_query": "{status} = DRAFT"},
                "backgroundColor": "rgba(255, 255, 0, 0.1)",
            },
        ],
        page_size=10,
    )
