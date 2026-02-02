"""Enhanced Income callbacks with comprehensive error handling and UX improvements."""
from datetime import datetime
import dash
from dash import Input, Output, State, html, ctx, ALL
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from dash import dash_table

from utils.api_client import APIClient
from utils.ui_helpers import create_empty_state, format_currency, create_toast
from utils.error_handler import (
    display_error,
    display_success,
    display_warning,
    validate_required_fields,
    validate_positive_number,
    validate_date,
    parse_api_error
)


def register_income_callbacks(app):
    """Register income management callbacks with enhanced error handling."""
    
    api_client = APIClient()

    @app.callback(
        [
            Output("income-form-container", "style"),
            Output("income-currency", "options"),
            Output("income-currency", "value"),
        ],
        [Input("current-period-id", "data"), Input("session-store", "data")],
    )
    def show_income_form(period_id, session_data):
        """Show income form and load currencies when period is selected."""
        if not period_id or not session_data or "token" not in session_data:
            return {"display": "none"}, [], None

        try:
            token = session_data["token"]
            api_client.set_token(token)

            # Load currencies
            currencies_response = api_client.get("/currencies/")
            currency_options = []
            default_currency_id = None
            
            if isinstance(currencies_response, list):
                for c in currencies_response:
                    ticker = c.get('ticker', '')
                    curr_id = c.get('id', '')
                    currency_options.append({
                        "label": f"{ticker} - {c.get('name', '')}", 
                        "value": curr_id
                    })
                    if c.get("is_default"):
                        default_currency_id = curr_id
                
                # Fallback to first one
                if not default_currency_id and currency_options:
                    default_currency_id = currency_options[0]["value"]
            elif "error" in currencies_response:
                print(f"Error loading currencies: {parse_api_error(currencies_response)}")

            return {"display": "block"}, currency_options, default_currency_id
            
        except Exception as e:
            print(f"Error in show_income_form: {e}")
            return {"display": "none"}, [], None

    @app.callback(
        [
            Output("income-form-alert", "children"),
            Output("income-source-name", "value"),
            Output("income-amount", "value"),
            Output("income-currency", "value", allow_duplicate=True),
            Output("income-date", "value"),
            Output("income-notes", "value"),
            Output("income-tax-applicable", "value"),
            Output("income-is-recurring", "value"),
            Output("income-table-container", "children", allow_duplicate=True),
            Output("recon-trigger-store", "data", allow_duplicate=True),
            Output("add-income-btn", "disabled"),
            Output("income-toast-container", "children"),
            Output("auth-error-trigger", "data", allow_duplicate=True),
        ],
        [Input("add-income-btn", "n_clicks")],
        [
            State("current-period-id", "data"),
            State("income-source-name", "value"),
            State("income-amount", "value"),
            State("income-currency", "value"),
            State("income-date", "value"),
            State("income-notes", "value"),
            State("income-tax-applicable", "value"),
            State("income-is-recurring", "value"),
            State("session-store", "data"),
        ],
        prevent_initial_call=True,
    )
    def add_income(n_clicks, period_id, source_name, amount, currency_id, income_date, 
                   notes, tax_applicable, is_recurring, session_data):
        """Handle adding income with comprehensive validation."""
        if not n_clicks:
            raise PreventUpdate

        try:
            # Validate required fields
            is_valid, errors = validate_required_fields(
                source_name=source_name,
                amount=amount,
                currency=currency_id,
                period=period_id
            )
            
            if not is_valid:
                error_list = [f"{field}: {msg}" for field, msg in errors.items()]
                return (
                    display_warning("Please fill all required fields (*): " + ", ".join(error_list)),
                    dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                    dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                    False, None, dash.no_update
                )
            
            # Validate amount is positive
            is_valid, error_msg = validate_positive_number(amount, "Amount")
            if not is_valid:
                return (
                    display_warning(error_msg),
                    dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                    dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                    False, None, dash.no_update
                )
            
            # Validate date if provided
            if income_date:
                is_valid, error_msg = validate_date(income_date, allow_future=False, field_name="Income Date")
                if not is_valid:
                    return (
                        display_warning(error_msg),
                        dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                        dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                        False, None, dash.no_update
                    )

            if not session_data or "token" not in session_data:
                return (
                    display_error("Please log in first"),
                    dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                    dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                    False, None, datetime.now().timestamp()
                )

            token = session_data["token"]
            api_client.set_token(token)

            # Create income entry
            payload = {
                "source_name": source_name,
                "amount": float(amount),
                "currency_id": currency_id,
                "tax_applicable": tax_applicable or False,
                "is_recurring": is_recurring or False,
            }
            
            if income_date:
                payload["income_date"] = income_date
            if notes:
                payload["notes"] = notes

            response = api_client.post(f"/periods/{period_id}/incomes", payload)

            if "error" in response or "detail" in response:
                auth_error = response.get("error") == "AUTHENTICATION_ERROR"
                return (
                    display_error(response),
                    dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                    dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                    False, None, datetime.now().timestamp() if auth_error else dash.no_update
                )

            # Success - clear form and refresh table
            income_response = api_client.get(f"/periods/{period_id}/incomes")
            table = create_income_table(
                income_response if isinstance(income_response, list) else [], 
                period_id, 
                api_client
            )

            toast = create_toast(
                f"Income '{source_name}' added successfully!",
                icon="bi-check-circle-fill",
                color="success"
            )

            return (
                display_success(f"Income '{source_name}' added successfully!"),
                "",  # Clear source name
                "",  # Clear amount
                dash.no_update,  # Keep current currency
                "",  # Clear date
                "",  # Clear notes
                False,  # Reset tax checkbox
                False,  # Reset recurring checkbox
                table,
                datetime.now().timestamp(),
                False,
                toast,
                dash.no_update
            )
            
        except Exception as e:
            return (
                display_error(f"Unexpected error: {str(e)}"),
                dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                False, None, dash.no_update
            )

    @app.callback(
        Output("recon-trigger-store", "data", allow_duplicate=True),
        [Input("income-table-container", "children")],
        prevent_initial_call=True
    )
    def trigger_recon_on_income_change(child):
        """Trigger reconciliation update when income changes."""
        return datetime.now().timestamp()

    @app.callback(
        Output("income-table-container", "children"),
        [Input("current-period-id", "data"), Input("session-store", "data")],
    )
    def load_income_table(period_id, session_data):
        """Load income entries for selected period."""
        if not period_id or not session_data or "token" not in session_data:
            return create_empty_state(
                "bi-calendar-check",
                "No Period Selected",
                "Select a monitoring period in the header to view income entries."
            )

        try:
            token = session_data["token"]
            api_client.set_token(token)

            response = api_client.get(f"/periods/{period_id}/incomes")

            if "error" in response:
                return display_error(response)

            return create_income_table(
                response if isinstance(response, list) else [], 
                period_id, 
                api_client
            )
            
        except Exception as e:
            return display_error(f"Error loading income: {str(e)}")

    # --- Delete Income with Confirmation ---
    @app.callback(
        [
            Output("income-delete-modal", "is_open"),
            Output("income-pending-delete-id", "data"),
        ],
        [
            Input({"type": "delete-income-btn", "index": ALL}, "n_clicks"),
            Input("income-delete-cancel", "n_clicks"),
        ],
        [State("income-delete-modal", "is_open")],
        prevent_initial_call=True
    )
    def toggle_delete_modal(delete_clicks, cancel_click, is_open):
        """Toggle delete confirmation modal."""
        if not ctx.triggered:
            raise PreventUpdate
        
        trig = ctx.triggered_id
        
        if trig == "income-delete-cancel":
            return False, None
        
        if isinstance(trig, dict) and trig["type"] == "delete-income-btn":
            if any(delete_clicks):
                income_id = trig["index"]
                return True, income_id
        
        return dash.no_update, dash.no_update

    @app.callback(
        [
            Output("income-table-container", "children", allow_duplicate=True),
            Output("income-delete-modal", "is_open", allow_duplicate=True),
            Output("income-toast-container", "children", allow_duplicate=True),
            Output("recon-trigger-store", "data", allow_duplicate=True),
        ],
        [Input("income-delete-confirm", "n_clicks")],
        [
            State("income-pending-delete-id", "data"),
            State("current-period-id", "data"),
            State("session-store", "data")
        ],
        prevent_initial_call=True
    )
    def confirm_delete_income(n_clicks, income_id, period_id, session_data):
        """Confirm and execute income deletion."""
        if not n_clicks or not income_id:
            raise PreventUpdate
        
        try:
            api_client.set_token(session_data["token"])
            result = api_client.delete(f"/incomes/{income_id}")
            
            if "error" in result:
                toast = create_toast(
                    f"Failed to delete: {parse_api_error(result)}",
                    icon="bi-x-circle-fill",
                    color="danger"
                )
                return dash.no_update, False, toast, dash.no_update
            
            # Reload table
            income_response = api_client.get(f"/periods/{period_id}/incomes")
            table = create_income_table(
                income_response if isinstance(income_response, list) else [],
                period_id,
                api_client
            )
            
            toast = create_toast(
                "Income entry deleted successfully",
                icon="bi-check-circle-fill",
                color="success"
            )
            
            return table, False, toast, datetime.now().timestamp()
            
        except Exception as e:
            toast = create_toast(
                f"Error: {str(e)}",
                icon="bi-x-circle-fill",
                color="danger"
            )
            return dash.no_update, False, toast, dash.no_update


def create_income_table(income_entries, period_id, api_client):
    """Create an enhanced income table with delete functionality."""
    if not income_entries or len(income_entries) == 0:
        return create_empty_state(
            "bi-cash-stack",
            "No Income Entries",
            "Add your first income source using the form above to start tracking your earnings."
        )

    try:
        # Create table rows with delete buttons
        rows = []
        for entry in income_entries:
            rows.append(html.Tr([
                html.Td([
                    entry.get("source_name", ""),
                    html.I(className="bi bi-arrow-repeat ms-2 text-primary", title="Recurring") if entry.get("is_recurring") else None
                ], className="fw-bold"),
                html.Td(
                    format_currency(entry.get('amount', 0), currency_ticker=entry.get("currency_code", "")),
                    className="text-success fw-bold"
                ),
                html.Td(entry.get("income_date", "N/A")),
                html.Td(
                    dbc.Badge("Yes", color="success") if entry.get("tax_applicable", False) 
                    else dbc.Badge("No", color="secondary")
                ),
                html.Td(entry.get("notes", "-"), className="text-muted small"),
                html.Td(
                    dbc.Button(
                        html.I(className="bi bi-trash"),
                        id={"type": "delete-income-btn", "index": entry.get("id", "")},
                        size="sm",
                        color="link",
                        className="text-danger p-0",
                        title="Delete income entry"
                    ),
                    className="text-center"
                )
            ]))

        return dbc.Table(
            [
                html.Thead(html.Tr([
                    html.Th("Source"),
                    html.Th("Amount"),
                    html.Th("Date"),
                    html.Th("Tax Applicable"),
                    html.Th("Notes"),
                    html.Th("Actions", className="text-center")
                ])),
                html.Tbody(rows)
            ],
            hover=True,
            responsive=True,
            className="align-middle"
        )
        
    except Exception as e:
        print(f"Error creating income table: {e}")
        return display_error(f"Error displaying income data: {str(e)}")
