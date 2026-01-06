"""Enhanced Account callbacks with comprehensive error handling and UX improvements."""
from datetime import datetime
import dash
from dash import Input, Output, State, html, ctx, ALL
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc

from utils.api_client import APIClient
from utils.ui_helpers import create_empty_state, format_currency, create_toast
from utils.error_handler import (
    display_error,
    display_success,
    display_warning,
    validate_required_fields,
    validate_date,
    parse_api_error
)


def register_account_callbacks(app):
    """Register account management callbacks with enhanced error handling."""
    
    api_client = APIClient()

    @app.callback(
        [
            Output("account-table-container", "children"),
            Output("account-currency-select", "options"),
            Output("account-currency-select", "value"),
        ],
        [
            Input("url", "pathname"),
            Input("account-refresh-trigger", "data"),
            Input("session-store", "data")
        ],
    )
    def load_accounts_data(pathname, refresh_trigger, session_data):
        """Load accounts and currencies when navigating to the accounts page."""
        if not session_data or "token" not in session_data:
            return (
                create_empty_state(
                    "bi-lock",
                    "Authentication Required",
                    "Please log in to view accounts."
                ),
                [],
                None
            )

        try:
            token = session_data["token"]
            api_client.set_token(token)

            # Fetch Currencies
            currencies_response = api_client.get("/currencies/")
            
            # Auto-initialize if empty
            if isinstance(currencies_response, list) and len(currencies_response) == 0:
                api_client.post("/currencies/initialize", {})
                currencies_response = api_client.get("/currencies/")
            
            currency_options = []
            currency_map = {}
            default_curr = None
            
            if isinstance(currencies_response, list):
                for c in currencies_response:
                    ticker = c.get('ticker', '')
                    curr_id = c.get('id', '')
                    currency_options.append({
                        "label": f"{ticker} - {c.get('name', '')}",
                        "value": curr_id
                    })
                    currency_map[curr_id] = ticker
                    if c.get("is_default"):
                        default_curr = curr_id
                
                if not default_curr and currency_options:
                    default_curr = currency_options[0]["value"]

            # Fetch Accounts
            accounts_response = api_client.get("/accounts/")
            
            if "error" in accounts_response:
                return display_error(accounts_response), currency_options, default_curr
            
            # Enrich accounts with currency ticker
            if isinstance(accounts_response, list):
                for acc in accounts_response:
                    acc["currency_ticker"] = currency_map.get(acc.get("currency_id"), "Unknown")
            
            table = create_accounts_table(accounts_response)
            
            return table, currency_options, default_curr
            
        except Exception as e:
            return (
                display_error(f"Error loading accounts: {str(e)}"),
                [],
                None
            )

    @app.callback(
        [
            Output("account-form-alert", "children"),
            Output("account-name-input", "value"),
            Output("account-opening-balance", "value"),
            Output("account-opening-date", "value"),
            Output("account-refresh-trigger", "data"),
            Output("add-account-btn", "disabled"),
            Output("account-toast-container", "children"),
        ],
        [Input("add-account-btn", "n_clicks")],
        [
            State("account-name-input", "value"),
            State("account-type-select", "value"),
            State("account-currency-select", "value"),
            State("account-opening-balance", "value"),
            State("account-opening-date", "value"),
            State("session-store", "data")
        ],
        prevent_initial_call=True
    )
    def add_account(n_clicks, name, atype, currency_id, opening_balance, opening_date, session_data):
        """Handle adding account with comprehensive validation."""
        if not n_clicks:
            raise PreventUpdate

        try:
            # Validate required fields
            is_valid, errors = validate_required_fields(
                account_name=name,
                currency=currency_id
            )
            
            if not is_valid:
                error_list = [f"{field}: {msg}" for field, msg in errors.items()]
                return (
                    display_warning("Please fill all required fields (*): " + ", ".join(error_list)),
                    dash.no_update, dash.no_update, dash.no_update,
                    dash.no_update, False, None
                )
            
            # Validate opening date if provided
            if opening_date:
                is_valid, error_msg = validate_date(opening_date, allow_future=False, field_name="Opening Date")
                if not is_valid:
                    return (
                        display_warning(error_msg),
                        dash.no_update, dash.no_update, dash.no_update,
                        dash.no_update, False, None
                    )

            if not session_data or "token" not in session_data:
                return (
                    display_error("Please log in first"),
                    dash.no_update, dash.no_update, dash.no_update,
                    dash.no_update, False, None
                )

            token = session_data["token"]
            api_client.set_token(token)

            # Prepare payload
            opening_bal_val = float(opening_balance) if opening_balance is not None else 0.0
            opening_date_val = opening_date if opening_date else datetime.now().date().isoformat()
            
            payload = {
                "account_name": name,
                "account_type": atype,
                "currency_id": currency_id,
                "opening_balance": opening_bal_val,
                "opening_balance_date": opening_date_val
            }

            response = api_client.post("/accounts/", payload)

            if "error" in response or "detail" in response:
                return (
                    display_error(response),
                    dash.no_update, dash.no_update, dash.no_update,
                    dash.no_update, False, None
                )

            # Success - clear form
            toast = create_toast(
                f"Account '{name}' added successfully!",
                icon="bi-check-circle-fill",
                color="success"
            )

            return (
                display_success(f"Account '{name}' added successfully!"),
                "",  # Clear name
                0,   # Reset balance
                datetime.now().date().isoformat(),  # Reset date
                datetime.now().timestamp(),  # Trigger refresh
                False,
                toast
            )
            
        except Exception as e:
            return (
                display_error(f"Unexpected error: {str(e)}"),
                dash.no_update, dash.no_update, dash.no_update,
                dash.no_update, False, None
            )

    # --- Delete Account with Confirmation ---
    @app.callback(
        [
            Output("account-delete-modal", "is_open"),
            Output("account-pending-delete-id", "data"),
        ],
        [
            Input({"type": "delete-account-btn", "index": ALL}, "n_clicks"),
            Input("account-delete-cancel", "n_clicks"),
        ],
        [State("account-delete-modal", "is_open")],
        prevent_initial_call=True
    )
    def toggle_delete_modal(delete_clicks, cancel_click, is_open):
        """Toggle delete confirmation modal."""
        if not ctx.triggered:
            raise PreventUpdate
        
        trig = ctx.triggered_id
        
        if trig == "account-delete-cancel":
            return False, None
        
        if isinstance(trig, dict) and trig["type"] == "delete-account-btn":
            if any(delete_clicks):
                account_id = trig["index"]
                return True, account_id
        
        return dash.no_update, dash.no_update

    @app.callback(
        [
            Output("account-refresh-trigger", "data", allow_duplicate=True),
            Output("account-delete-modal", "is_open", allow_duplicate=True),
            Output("account-toast-container", "children", allow_duplicate=True),
        ],
        [Input("account-delete-confirm", "n_clicks")],
        [
            State("account-pending-delete-id", "data"),
            State("session-store", "data")
        ],
        prevent_initial_call=True
    )
    def confirm_delete_account(n_clicks, account_id, session_data):
        """Confirm and execute account deletion."""
        if not n_clicks or not account_id:
            raise PreventUpdate
        
        try:
            api_client.set_token(session_data["token"])
            result = api_client.delete(f"/accounts/{account_id}")
            
            if "error" in result or "detail" in result:
                toast = create_toast(
                    f"Failed to delete: {parse_api_error(result)}",
                    icon="bi-x-circle-fill",
                    color="danger"
                )
                return dash.no_update, False, toast
            
            toast = create_toast(
                "Account deleted successfully",
                icon="bi-check-circle-fill",
                color="success"
            )
            
            return datetime.now().timestamp(), False, toast
            
        except Exception as e:
            toast = create_toast(
                f"Error: {str(e)}",
                icon="bi-x-circle-fill",
                color="danger"
            )
            return dash.no_update, False, toast


def create_accounts_table(accounts):
    """Create an enhanced accounts table with delete functionality."""
    if not accounts or len(accounts) == 0:
        return create_empty_state(
            "bi-bank",
            "No Accounts Found",
            "Add your bank accounts or cash wallets to start tracking."
        )

    try:
        rows = []
        for a in accounts:
            acc_id = a.get("id", "")
            is_active = a.get("is_active", True)
            
            rows.append(
                html.Tr([
                    html.Td(a.get("account_name", ""), className="fw-bold"),
                    html.Td(
                        dbc.Badge(
                            a.get("account_type", ""),
                            color="info",
                            className="px-3 py-2"
                        )
                    ),
                    html.Td(a.get("currency_ticker", "")),
                    html.Td(
                        format_currency(
                            a.get('opening_balance', 0),
                            currency_ticker=a.get("currency_ticker", "")
                        )
                    ),
                    html.Td(
                        dbc.Badge(
                            "Active" if is_active else "Inactive",
                            color="success" if is_active else "secondary",
                            className="px-3 py-2"
                        )
                    ),
                    html.Td(
                        dbc.Button(
                            html.I(className="bi bi-trash"),
                            id={"type": "delete-account-btn", "index": acc_id},
                            size="sm",
                            color="link",
                            className="text-danger p-0",
                            title="Delete account"
                        ),
                        className="text-center"
                    )
                ])
            )

        return dbc.Table(
            [
                html.Thead(html.Tr([
                    html.Th("Account"),
                    html.Th("Type"),
                    html.Th("Currency"),
                    html.Th("Opening Balance"),
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
        print(f"Error creating accounts table: {e}")
        return display_error(f"Error displaying account data: {str(e)}")
