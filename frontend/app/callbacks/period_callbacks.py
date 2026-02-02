"""Enhanced Period callbacks with comprehensive error handling and UX improvements."""
from datetime import datetime
import dash
from dash import Input, Output, State, html, ctx, ALL
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc

from utils.api_client import APIClient
from utils.ui_helpers import create_empty_state, create_toast
from utils.error_handler import (
    display_error,
    display_success,
    display_warning,
    validate_required_fields,
    validate_date,
    parse_api_error
)


def register_period_callbacks(app):
    """Register period management callbacks with enhanced error handling."""
    
    api_client = APIClient()

    @app.callback(
        [
            Output("period-form-alert", "children"),
            Output("period-name-input", "value"),
            Output("period-start-date", "value"),
            Output("period-end-date", "value"),
            Output("period-table-container", "children", allow_duplicate=True),
            Output("create-period-btn", "disabled"),
            Output("period-toast-container", "children"),
            Output("auth-error-trigger", "data", allow_duplicate=True),
        ],
        [Input("create-period-btn", "n_clicks")],
        [
            State("period-name-input", "value"),
            State("period-start-date", "value"),
            State("period-end-date", "value"),
            State("period-apply-template-check", "value"),
            State("session-store", "data"),
        ],
        prevent_initial_call=True,
    )
    def create_period(n_clicks, period_name, start_date, end_date, apply_template, session_data):
        """Handle period creation with comprehensive validation."""
        if not n_clicks:
            raise PreventUpdate

        try:
            # Validate required fields
            is_valid, errors = validate_required_fields(
                period_name=period_name,
                start_date=start_date,
                end_date=end_date
            )
            
            if not is_valid:
                error_list = [f"{field}: {msg}" for field, msg in errors.items()]
                return (
                    display_warning("Please fill all required fields (*): " + ", ".join(error_list)),
                    dash.no_update, dash.no_update, dash.no_update,
                    dash.no_update, False, None, dash.no_update
                )
            
            # Validate start date
            is_valid, error_msg = validate_date(start_date, allow_future=True, field_name="Start Date")
            if not is_valid:
                return (
                    display_warning(error_msg),
                    dash.no_update, dash.no_update, dash.no_update,
                    dash.no_update, False, None, dash.no_update
                )
            
            # Validate end date
            is_valid, error_msg = validate_date(end_date, allow_future=True, field_name="End Date")
            if not is_valid:
                return (
                    display_warning(error_msg),
                    dash.no_update, dash.no_update, dash.no_update,
                    dash.no_update, False, None, dash.no_update
                )
            
            # Validate date range
            if start_date > end_date:
                return (
                    display_warning("Start date must be before or equal to end date"),
                    dash.no_update, dash.no_update, dash.no_update,
                    dash.no_update, False, None, dash.no_update
                )

            if not session_data or "token" not in session_data:
                return (
                    display_error("Please log in first"),
                    dash.no_update, dash.no_update, dash.no_update,
                    dash.no_update, False, None, datetime.now().timestamp()
                )

            token = session_data["token"]
            api_client.set_token(token)

            # Create period (snapshot_date = end_date)
            payload = {
                "period_name": period_name,
                "start_date": start_date,
                "end_date": end_date,
                "snapshot_date": end_date,  # Auto-set as per requirement
            }

            response = api_client.post("/periods/", payload)

            if "error" in response or "detail" in response:
                auth_error = response.get("error") == "AUTHENTICATION_ERROR"
                return (
                    display_error(response),
                    dash.no_update, dash.no_update, dash.no_update,
                    dash.no_update, False, None, 
                    datetime.now().timestamp() if auth_error else dash.no_update
                )

            period_id = response.get("id")
            template_msg = ""
            
            # Auto-apply default template if requested
            if apply_template and period_id:
                templates = api_client.get("/templates/")
                if isinstance(templates, list):
                    default_tpl = next((t for t in templates if t.get("is_default")), None)
                    if default_tpl:
                        apply_res = api_client.post(f"/templates/{default_tpl['id']}/apply", {"target_period_id": period_id})
                        if "error" not in apply_res:
                            template_msg = f" (Applied template: {default_tpl['template_name']})"

            # Success - clear form and refresh table
            periods_response = api_client.get("/periods/")
            table = create_period_table(
                periods_response if isinstance(periods_response, list) else []
            )

            toast = create_toast(
                f"Period '{period_name}' created successfully!{template_msg}",
                icon="bi-check-circle-fill",
                color="success"
            )

            return (
                display_success(f"Period '{period_name}' created successfully!{template_msg}"),
                "",  # Clear name
                "",  # Clear start date
                "",  # Clear end date
                table,
                False,
                toast,
                dash.no_update
            )
            
        except Exception as e:
            return (
                display_error(f"Unexpected error: {str(e)}"),
                dash.no_update, dash.no_update, dash.no_update,
                dash.no_update, False, None
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
            return create_empty_state(
                "bi-lock",
                "Authentication Required",
                "Please log in to view periods."
            )

        try:
            token = session_data["token"]
            api_client.set_token(token)

            response = api_client.get("/periods/")

            if "error" in response:
                return display_error(response)

            return create_period_table(response)
            
        except Exception as e:
            return display_error(f"Error loading periods: {str(e)}")

    # --- Delete Period with Confirmation ---
    @app.callback(
        [
            Output("period-delete-modal", "is_open"),
            Output("period-pending-delete-id", "data"),
        ],
        [
            Input({"type": "delete-period-btn", "index": ALL}, "n_clicks"),
            Input("period-delete-cancel", "n_clicks"),
        ],
        [State("period-delete-modal", "is_open")],
        prevent_initial_call=True
    )
    def toggle_delete_modal(delete_clicks, cancel_click, is_open):
        """Toggle delete confirmation modal."""
        if not ctx.triggered:
            raise PreventUpdate
        
        trig = ctx.triggered_id
        
        if trig == "period-delete-cancel":
            return False, None
        
        if isinstance(trig, dict) and trig["type"] == "delete-period-btn":
            if any(delete_clicks):
                period_id = trig["index"]
                return True, period_id
        
        return dash.no_update, dash.no_update

    @app.callback(
        [
            Output("period-table-container", "children", allow_duplicate=True),
            Output("period-delete-modal", "is_open", allow_duplicate=True),
            Output("period-toast-container", "children", allow_duplicate=True),
            Output("auth-error-trigger", "data", allow_duplicate=True),
        ],
        [Input("period-delete-confirm", "n_clicks")],
        [
            State("period-pending-delete-id", "data"),
            State("session-store", "data")
        ],
        prevent_initial_call=True,
    )
    def confirm_delete_period(n_clicks, period_id, session_data):
        """Confirm and execute period deletion."""
        if not n_clicks or not period_id:
            raise PreventUpdate
        
        try:
            api_client.set_token(session_data["token"])
            result = api_client.delete(f"/periods/{period_id}")
            
            if "error" in result or "detail" in result:
                auth_error = result.get("error") == "AUTHENTICATION_ERROR"
                toast = create_toast(
                    f"Failed to delete: {parse_api_error(result)}",
                    icon="bi-x-circle-fill",
                    color="danger"
                )
                return dash.no_update, False, toast, datetime.now().timestamp() if auth_error else dash.no_update
            
            # Reload table
            periods_response = api_client.get("/periods/")
            table = create_period_table(
                periods_response if isinstance(periods_response, list) else []
            )
            
            toast = create_toast(
                "Period deleted successfully",
                icon="bi-check-circle-fill",
                color="success"
            )
            
            return table, False, toast, dash.no_update
            
        except Exception as e:
            toast = create_toast(
                f"Error: {str(e)}",
                icon="bi-x-circle-fill",
                color="danger"
            )
            return dash.no_update, False, toast, dash.no_update


def create_period_table(periods):
    """Create an enhanced period table with delete functionality."""
    if not periods or len(periods) == 0:
        return create_empty_state(
            "bi-calendar-x",
            "No Periods Found",
            "Create your first period above to start managing your budget."
        )

    try:
        # Sort by start_date descending
        sorted_periods = sorted(
            periods, key=lambda x: x.get("start_date", ""), reverse=True
        )

        rows = []
        for p in sorted_periods:
            status = p.get("status", "DRAFT")
            status_color = "success" if status == "FINALIZED" else "warning"
            is_draft = status == "DRAFT"
            
            rows.append(
                html.Tr([
                    html.Td(p.get("period_name", ""), className="fw-bold"),
                    html.Td(p.get("start_date", "")),
                    html.Td(p.get("end_date", "")),
                    html.Td(
                        dbc.Badge(
                            status,
                            color=status_color,
                            className="px-3 py-2"
                        )
                    ),
                    html.Td(
                        dbc.Button(
                            html.I(className="bi bi-trash"),
                            id={"type": "delete-period-btn", "index": p.get("id", "")},
                            size="sm",
                            color="link",
                            className="text-danger p-0",
                            disabled=not is_draft,  # Only allow deleting drafts
                            title="Delete Period (Drafts Only)" if is_draft else "Cannot delete finalized period"
                        ),
                        className="text-center"
                    )
                ])
            )

        return dbc.Table(
            [
                html.Thead(html.Tr([
                    html.Th("Period Name"),
                    html.Th("Start Date"),
                    html.Th("End Date"),
                    html.Th("Status"),
                    html.Th("Actions", className="text-center"),
                ])),
                html.Tbody(rows)
            ],
            hover=True,
            responsive=True,
            className="align-middle"
        )
        
    except Exception as e:
        print(f"Error creating period table: {e}")
        return display_error(f"Error displaying period data: {str(e)}")
