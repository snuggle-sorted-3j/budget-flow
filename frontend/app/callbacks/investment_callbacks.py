from datetime import datetime

import dash_bootstrap_components as dbc
from dash import Input, Output, State, dash_table, html, dcc, ALL
from dash.exceptions import PreventUpdate
import dash

from utils.api_client import APIClient
from utils.ui_helpers import create_empty_state, format_currency


def register_investment_callbacks(app):
    """Register callbacks for investment tracking."""
    api_client = APIClient()

    # --- Load Data into Dropdowns & Tables ---
    @app.callback(
        [
            Output("inv-account-type", "value"), # Dummy reset mostly
            Output("inv-accounts-table-container", "children"),
            Output("inv-category-account-select", "options"),
            Output("inv-opening-currency", "options"),
            Output("inv-categories-table-container", "children"),
            Output("inv-transfer-category-select", "options"),
            Output("inv-transfer-currency", "options"),
            Output("inv-transfer-source-account", "options"),
            Output("inv-transfers-table-container", "children"),
            Output("inv-period-check-message", "children"),
        ],
        [
            Input("url", "pathname"), 
            Input("current-period-id", "data"), 
            Input("session-store", "data"),
            Input("inv-trigger-refresh", "data") # Trigger dynamic refresh
        ],
    )
    def load_investment_data(pathname, period_id, session_data, _):
        if not pathname or "investments" not in pathname:
             raise PreventUpdate

        if not session_data or "token" not in session_data:
            return [dash.no_update] * 10

        api_client.set_token(session_data["token"])

        # 1. Fetch Investment Accounts
        inv_accounts = api_client.get("/investments/accounts")
        if "error" in inv_accounts: inv_accounts = []
        
        account_options = [{"label": a["account_name"], "value": a["id"]} for a in inv_accounts]
        accounts_table = create_inv_accounts_table(inv_accounts)

        # 2. Fetch Currencies
        currencies = api_client.get("/currencies/")
        if "error" in currencies: currencies = []
        currency_options = [{"label": c["ticker"], "value": c["id"]} for c in currencies]

        # 3. Fetch Investment Categories
        investments = api_client.get("/investments/")
        if "error" in investments: investments = []
        
        category_options = [{"label": i["category_name"], "value": i["id"]} for i in investments]
        categories_table = create_inv_categories_table(investments)
        
        # 4. Fetch Regular Accounts (Sources)
        reg_accounts = api_client.get("/accounts/")
        if "error" in reg_accounts: reg_accounts = []
        source_options = [{"label": a["account_name"], "value": a["id"]} for a in reg_accounts]

        # 5. Fetch Transfers if period selected
        transfers_table = html.Div("Select a period to view transfers", className="text-muted")
        period_msg = html.Div("No period selected", className="text-danger")
        
        if period_id:
            period_msg = html.Div([
                html.I(className="bi bi-calendar-check me-2 text-success"),
                "Recording transfers for the selected active period."
            ], className="text-success fw-bold")
            
            transfers = api_client.get(f"/investments/transfers/{period_id}")
            if "error" not in transfers:
                transfers_table = create_inv_transfers_table(transfers)
            else:
                transfers_table = html.Div("Error loading transfers")

        return (
            dash.no_update, # account type
            accounts_table,
            account_options,
            currency_options,
            categories_table,
            category_options,
            currency_options,
            source_options,
            transfers_table,
            period_msg
        )

    # --- Add Investment Account ---
    @app.callback(
        [
            Output("inv-account-message", "children"),
            Output("inv-account-message", "color"),
            Output("inv-account-message-collapse", "is_open"),
            Output("inv-account-name", "value"),
            Output("inv-account-notes", "value"),
            Output("inv-trigger-refresh", "data", allow_duplicate=True),
        ],
        [Input("add-inv-account-btn", "n_clicks")],
        [
            State("inv-account-name", "value"),
            State("inv-account-type", "value"),
            State("inv-account-notes", "value"),
            State("session-store", "data"),
        ],
        prevent_initial_call=True,
    )
    def add_investment_account(n_clicks, name, acc_type, notes, session_data):
        if not n_clicks: raise PreventUpdate
        if not name or not acc_type:
            return "Name and Type are required", "danger", True, dash.no_update, dash.no_update, datetime.now().timestamp()

        api_client.set_token(session_data["token"])
        payload = {
            "account_name": name,
            "account_type": acc_type,
            "notes": notes,
            "is_active": True
        }
        res = api_client.post("/investments/accounts", payload)
        
        if "error" in res:
            return f"Error: {res['error']}", "danger", True, dash.no_update, dash.no_update, datetime.now().timestamp()
        
        return "Account Added!", "success", True, "", "", datetime.now().timestamp()

    # --- Add Investment Category ---
    @app.callback(
        [
            Output("inv-category-message", "children"),
            Output("inv-category-message", "color"),
            Output("inv-category-message-collapse", "is_open"),
            Output("inv-category-name", "value"),
            Output("inv-opening-balance", "value"),
            Output("inv-trigger-refresh", "data", allow_duplicate=True),
        ],
        [Input("add-inv-category-btn", "n_clicks")],
        [
            State("inv-category-name", "value"),
            State("inv-category-account-select", "value"),
            State("inv-opening-balance", "value"),
            State("inv-opening-currency", "value"),
            State("inv-opening-date", "value"),
            State("session-store", "data"),
        ],
        prevent_initial_call=True,
    )
    def add_investment_category(n_clicks, name, acc_id, open_bal, open_curr, open_date, session_data):
        if not n_clicks: raise PreventUpdate
        if not name:
            return "Category Name is required", "danger", True, dash.no_update, dash.no_update, datetime.now().timestamp()

        api_client.set_token(session_data["token"])
        payload = {
            "category_name": name,
            "investment_account_id": acc_id,
        }
        if open_bal: # Currency/Date optional if balance not set, but logic below implies if balance then curr/date
            payload["opening_balance"] = float(open_bal)
            payload["opening_balance_currency_id"] = open_curr
            payload["opening_balance_date"] = open_date or datetime.now().date().isoformat()
            
        res = api_client.post("/investments/", payload)
        if "error" in res:
            return f"Error: {res['error']}", "danger", True, dash.no_update, dash.no_update, datetime.now().timestamp()

        return "Category Added!", "success", True, "", "", datetime.now().timestamp()

    # --- Add Investment Transfer ---
    @app.callback(
        [
            Output("inv-transfer-message", "children"),
            Output("inv-transfer-message", "color"),
            Output("inv-transfer-message-collapse", "is_open"),
            Output("inv-transfer-amount", "value"),
            Output("inv-transfer-units", "value"),
            Output("inv-transfer-notes", "value"),
            Output("recon-trigger-store", "data", allow_duplicate=True),
            Output("inv-trigger-refresh", "data", allow_duplicate=True),
        ],
        [Input("add-inv-transfer-btn", "n_clicks")],
        [
            State("current-period-id", "data"),
            State("inv-transfer-category-select", "value"),
            State("inv-transfer-amount", "value"),
            State("inv-transfer-units", "value"),
            State("inv-transfer-currency", "value"),
            State("inv-transfer-source-account", "value"),
            State("inv-transfer-date", "value"),
            State("inv-transfer-notes", "value"),
            State("session-store", "data"),
        ],
        prevent_initial_call=True,
    )
    def add_investment_transfer(n_clicks, period_id, inv_id, amount, units, curr_id, source_id, date_val, notes, session_data):
        if not n_clicks: raise PreventUpdate
        if not period_id:
             return "Select a period first", "warning", True, dash.no_update, dash.no_update, dash.no_update, datetime.now().timestamp()
        
        if not all([inv_id, amount, curr_id, source_id, date_val]):
             return "All fields except Notes are required", "danger", True, dash.no_update, dash.no_update, dash.no_update, datetime.now().timestamp()

        api_client.set_token(session_data["token"])
        payload = {
            "investment_id": inv_id,
            "amount_transferred": float(amount),
            "units_added": float(units) if units else None,
            "currency_id": curr_id,
            "source_account_id": source_id,
            "transfer_date": date_val,
            "notes": notes
        }
        res = api_client.post(f"/investments/transfers/{period_id}", payload)
        
        if "error" in res:
             return f"Error: {res['error']}", "danger", True, dash.no_update, dash.no_update, dash.no_update, datetime.now().timestamp()

        return "Transfer Recorded!", "success", True, "", "", "", datetime.now().timestamp(), datetime.now().timestamp()

    # --- Delete Handlers ---
    @app.callback(
        Output("inv-trigger-refresh", "data", allow_duplicate=True),
        [
            Input({"type": "delete-inv-account-btn", "index": ALL}, "n_clicks"),
            Input({"type": "delete-inv-category-btn", "index": ALL}, "n_clicks"),
            Input({"type": "delete-inv-transfer-btn", "index": ALL}, "n_clicks"),
        ],
        [State("session-store", "data")],
        prevent_initial_call=True
    )
    def handle_deletions(acct_clicks, cat_clicks, trans_clicks, session_data):
        ctx = dash.callback_context
        if not ctx.triggered: raise PreventUpdate
        
        button_id = ctx.triggered[0]["prop_id"].split(".")[0]
        try:
            btn_data = eval(button_id) 
            item_id = btn_data["index"]
            btn_type = btn_data["type"]
        except:
            raise PreventUpdate
            
        # Check if button actually clicked (n_clicks > 0)
        # This is tricky with ALL pattern. 
        # But since we use ctx.triggered, we know which one triggered.
        
        api_client.set_token(session_data["token"])
        
        if btn_type == "delete-inv-account-btn":
             res = api_client.delete(f"/investments/accounts/{item_id}")
        elif btn_type == "delete-inv-category-btn":
             res = api_client.delete(f"/investments/{item_id}")
        elif btn_type == "delete-inv-transfer-btn":
             res = api_client.delete(f"/investments/transfers/{item_id}")
        else:
            return dash.no_update
            
        # Success or fail we refresh to show state (fail might need error toast, but let's just refresh for now)
        return datetime.now().timestamp()


def create_inv_accounts_table(accounts):
    if not accounts: return create_empty_state("bi-bank2", "No Accounts", "Add an investment account.")
    
    rows = []
    for acc in accounts:
        rows.append(html.Tr([
            html.Td(acc["account_name"]),
            html.Td(acc["account_type"]),
            html.Td(acc.get("notes", "")),
            html.Td(
                dbc.Button(
                    html.I(className="bi bi-trash"),
                    id={"type": "delete-inv-account-btn", "index": acc["id"]},
                    color="link",
                    className="text-danger p-0",
                ),
                className="text-end"
            )
        ]))

    return dbc.Table(
        [
            html.Thead(html.Tr([html.Th("Account"), html.Th("Type"), html.Th("Notes"), html.Th("")])),
            html.Tbody(rows)
        ],
        hover=True, striped=True, responsive=True
    )

def create_inv_categories_table(investments):
    if not investments: return create_empty_state("bi-graph-up-arrow", "No Investments", "Define an investment category.")
    
    rows = []
    for i in investments:
        op_bal = f"{format_currency(i.get('opening_balance', 0))} {i.get('currency_ticker', '')}" if i.get('opening_balance') else "-"
        # TODO: Add Date column as requested
        # We need to map it if backend sends it. 
        # Backend schema sends opening_balance_date in InvestmentResponse? Yes.
        op_date = i.get("opening_balance_date", "-") if i.get("opening_balance") else "-"
        
        rows.append(html.Tr([
            html.Td(i["category_name"]),
            html.Td(i.get("account_name", "Unallocated")),
            html.Td(op_bal),
            html.Td(op_date),
            html.Td(
                dbc.Button(
                    html.I(className="bi bi-trash"),
                    id={"type": "delete-inv-category-btn", "index": i["id"]},
                    color="link",
                    className="text-danger p-0",
                ),
                className="text-end"
            )
        ]))

    return dbc.Table(
        [
            html.Thead(html.Tr([
                html.Th("Category"), 
                html.Th("Held In"), 
                html.Th("Opening Position"), 
                html.Th("Date"),
                html.Th("")
            ])),
            html.Tbody(rows)
        ],
        hover=True, striped=True, responsive=True
    )

def create_inv_transfers_table(transfers):
    if not transfers: return create_empty_state("bi-arrow-right-circle", "No Transfers", "No transfers for this period.")
    
    rows = []
    for t in transfers:
        rows.append(html.Tr([
            html.Td(t["transfer_date"]),
            html.Td(f"{format_currency(t['amount_transferred'])} {t.get('currency_ticker', '')}"),
            html.Td(f"{t.get('units_added', '-')}" if t.get('units_added') else "-"),
            html.Td(t.get("investment_category_name", "")),
            html.Td(t.get("source_account_name", "")),
            html.Td(t.get("notes", "")),
            html.Td(
                dbc.Button(
                    html.I(className="bi bi-trash"),
                    id={"type": "delete-inv-transfer-btn", "index": t["id"]},
                    color="link",
                    className="text-danger p-0",
                ),
                className="text-end"
            )
        ]))

    return dbc.Table(
        [
            html.Thead(html.Tr([
                html.Th("Date"), 
                html.Th("Amount (Cost)"), 
                html.Th("Units"),
                html.Th("To Investment"), 
                html.Th("From Account"),
                html.Th("Notes"),
                html.Th("")
            ])),
            html.Tbody(rows)
        ],
        hover=True, striped=True, responsive=True
    )
