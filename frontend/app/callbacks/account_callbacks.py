from dash import Input, Output, State, html, dash_table
from datetime import datetime
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from utils.api_client import APIClient
from utils.ui_helpers import create_empty_state
import dash
import json

def create_accounts_table(accounts):
    """Create a polished dbc.Table from accounts list."""
    if not accounts or len(accounts) == 0:
        return create_empty_state(
            "bi-bank",
            "No accounts found",
            "Add your bank accounts or cash wallets to start tracking."
        )

    rows = []
    for a in accounts:
        acc_id = a["id"]
        rows.append(
            html.Tr([
                html.Td(a["account_name"], className="fw-bold"),
                html.Td(a["account_type"]),
                html.Td(a.get("currency_ticker", "")),
                html.Td(f"{float(a.get('opening_balance', 0)):,.2f}"),
                html.Td("Active" if a["is_active"] else "Inactive", 
                        className="text-success" if a["is_active"] else "text-muted"),
                html.Td([
                    dbc.Button(
                        html.I(className="bi bi-trash"),
                        id={"type": "delete-account-btn", "id": acc_id},
                        color="outline-danger",
                        size="sm",
                        className="btn-rounded border-0"
                    )
                ], className="text-end")
            ])
        )

    return dbc.Table(
        [
            html.Thead(html.Tr([
                html.Th("Account"),
                html.Th("Type"),
                html.Th("Currency"),
                html.Th("Opening Bal"),
                html.Th("Status"),
                html.Th("Action", className="text-end"),
            ])),
            html.Tbody(rows)
        ],
        bordered=False,
        hover=True,
        responsive=True,
        className="align-middle custom-table"
    )

def register_account_callbacks(app):
    api_client = APIClient()

    # --- 1. Load Data (Accounts & Currencies) ---
    @app.callback(
        [
            Output("account-table-container", "children"),
            Output("account-currency-select", "options"), 
            Output("account-currency-select", "value"),
        ],
        [
            Input("url", "pathname"),
            Input("inv-trigger-refresh", "data") # Listen to global refresh trigger
        ],
        [State("session-store", "data")],
    )
    def load_accounts_data(pathname, refresh_trigger, session_data):
        if not session_data or "token" not in session_data:
            return html.Div("Please log in"), [], None

        api_client.set_token(session_data["token"])

        # Fetch Currencies
        currencies = api_client.get("/currencies/")
        if not currencies or (isinstance(currencies, list) and len(currencies) == 0):
             # Initialize if needed
             api_client.post("/currencies/initialize", {})
             currencies = api_client.get("/currencies/")
        
        currency_options = []
        currency_map = {}
        default_curr = None
        
        if currencies and "error" not in currencies:
            currency_options = [{"label": c["ticker"], "value": c["id"]} for c in currencies]
            for c in currencies:
                currency_map[c["id"]] = c["ticker"]
                if c.get("is_default"): default_curr = c["id"]
            if not default_curr and currencies: default_curr = currencies[0]["id"]

        # Fetch Accounts
        accounts = api_client.get("/accounts/")
        
        table = html.Div("Error loading accounts")
        if "error" not in accounts:
            for acc in accounts:
                acc["currency_ticker"] = currency_map.get(acc["currency_id"], "Unknown")
            table = create_accounts_table(accounts)
            
        return table, currency_options, default_curr

    # --- 2. Add Account ---
    @app.callback(
        [
            Output("account-message", "children"), 
            Output("account-message", "color"), 
            Output("account-message", "is_open"),
            Output("account-name-input", "value"), 
            Output("account-opening-balance", "value"),
            Output("account-opening-date", "value"),
            Output("inv-trigger-refresh", "data", allow_duplicate=True),
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
        if not n_clicks: raise PreventUpdate
        
        if not session_data or "token" not in session_data:
            return "Please log in first", "danger", True, dash.no_update, dash.no_update, dash.no_update, dash.no_update

        if not name or not currency_id:
             return "Please fill all fields", "warning", True, dash.no_update, dash.no_update, dash.no_update, dash.no_update

        api_client.set_token(session_data["token"])
        
        opening_bal_val = float(opening_balance) if opening_balance is not None else 0.0
        opening_date_val = opening_date if opening_date else datetime.now().date().isoformat()
        
        resp = api_client.post("/accounts/", {
            "account_name": name, 
            "account_type": atype, 
            "currency_id": currency_id,
            "opening_balance": opening_bal_val,
            "opening_balance_date": opening_date_val
        })
        
        if "error" in resp:
            return f"Error: {resp['error']}", "danger", True, dash.no_update, dash.no_update, dash.no_update, dash.no_update
            
        # Success: Clear inputs, return success msg, update trigger
        return (
            f"Account {name} added!", "success", True, 
            "", 0, datetime.now().date().isoformat(), # Clear inputs
            datetime.now().timestamp() # Trigger refresh
        )

    # --- 3. Delete Account ---
    @app.callback(
        [
            Output("account-message", "children", allow_duplicate=True),
            Output("account-message", "color", allow_duplicate=True),
            Output("account-message", "is_open", allow_duplicate=True),
            Output("inv-trigger-refresh", "data", allow_duplicate=True),
        ],
        [Input({"type": "delete-account-btn", "id": dash.ALL}, "n_clicks")],
        [State("session-store", "data")],
        prevent_initial_call=True
    )
    def delete_account(n_clicks, session_data):
        ctx = dash.callback_context
        if not ctx.triggered or not any(n_clicks):
            raise PreventUpdate

        triggered_prop = ctx.triggered[0]["prop_id"]
        try:
            prop_dict = json.loads(triggered_prop.split(".")[0])
            account_id = prop_dict["id"]
        except:
            raise PreventUpdate

        if not session_data or "token" not in session_data:
            return "Please log in first", "danger", True, dash.no_update

        api_client.set_token(session_data["token"])
        response = api_client.delete(f"/accounts/{account_id}")
        
        if "error" in response:
            return f"{response['error']}", "danger", True, dash.no_update
            
        return "Account deleted successfully", "success", True, datetime.now().timestamp()
