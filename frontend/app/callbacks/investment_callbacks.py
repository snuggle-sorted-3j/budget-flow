"""Enhanced Investment callbacks with comprehensive error handling and UX improvements."""
from datetime import datetime
import dash
from dash import Input, Output, State, html, dcc, ctx, ALL
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc

from utils.api_client import APIClient
from utils.ui_helpers import create_empty_state, format_currency, create_toast
from utils.error_handler import (
    display_error,
    display_success,
    display_warning,
    validate_required_fields,
    parse_api_error
)

def register_investment_callbacks(app):
    api_client = APIClient()

    # --- Load Data ---
    @app.callback(
        [
            Output("inv-account-type", "value"),
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
            Input("inv-trigger-refresh", "data")
        ],
    )
    def load_investment_data(pathname, period_id, session_data, _):
        if not pathname or "investments" not in pathname:
             raise PreventUpdate
        if not session_data or "token" not in session_data:
            return [dash.no_update] * 10

        try:
            api_client.set_token(session_data["token"])

            # 1. Accounts
            inv_accounts = api_client.get("/investments/accounts")
            if "error" in inv_accounts: inv_accounts = []
            account_options = [{"label": a["account_name"], "value": a["id"]} for a in inv_accounts]
            accounts_table = create_inv_accounts_table(inv_accounts)

            # 2. Currencies
            currencies = api_client.get("/currencies/")
            if "error" in currencies: currencies = []
            currency_options = [{"label": c["ticker"], "value": c["id"]} for c in currencies]

            # 3. Categories
            investments = api_client.get("/investments/")
            if "error" in investments: investments = []
            category_options = [{"label": i["category_name"], "value": i["id"]} for i in investments]
            categories_table = create_inv_categories_table(investments)
            
            # 4. Regular Accounts (Sources)
            reg_accounts = api_client.get("/accounts/")
            if "error" in reg_accounts: reg_accounts = []
            source_options = [{"label": a["account_name"], "value": a["id"]} for a in reg_accounts]

            # 5. Transfers
            transfers_table = html.Div("Select a period to view transfers", className="text-muted p-3")
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
                    transfers_table = display_error("Error loading transfers")

            return dash.no_update, accounts_table, account_options, currency_options, categories_table, category_options, currency_options, source_options, transfers_table, period_msg
        except Exception as e:
            return [dash.no_update] * 10

    # --- Add Investment Account ---
    @app.callback(
        [
            Output("inv-account-form-alert", "children"),
            Output("inv-account-name", "value"),
            Output("inv-account-notes", "value"),
            Output("inv-trigger-refresh", "data"),
            Output("inv-toast-container", "children"),
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
        
        is_valid, errors = validate_required_fields(name=name, type=acc_type)
        if not is_valid:
            return display_warning("Name and Type are required"), dash.no_update, dash.no_update, dash.no_update, dash.no_update

        try:
            api_client.set_token(session_data["token"])
            payload = {"account_name": name, "account_type": acc_type, "notes": notes, "is_active": True}
            res = api_client.post("/investments/accounts", payload)
            if "error" in res:
                return display_error(res), dash.no_update, dash.no_update, dash.no_update, None
            
            toast = create_toast("Investment account added", icon="bi-check-circle", color="success")
            return None, "", "", datetime.now().timestamp(), toast
        except Exception as e:
            return display_error(f"Error: {str(e)}"), dash.no_update, dash.no_update, dash.no_update, None

    # --- Add Investment Category ---
    @app.callback(
        [
            Output("inv-category-form-alert", "children"),
            Output("inv-category-name", "value"),
            Output("inv-opening-balance", "value"),
            Output("inv-trigger-refresh", "data", allow_duplicate=True),
            Output("inv-toast-container", "children", allow_duplicate=True),
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
        
        is_valid, _ = validate_required_fields(name=name, account=acc_id)
        if not is_valid:
            return display_warning("Category Name and Account are required"), dash.no_update, dash.no_update, dash.no_update, dash.no_update

        try:
            api_client.set_token(session_data["token"])
            payload = {"category_name": name, "investment_account_id": acc_id}
            if open_bal:
                payload["opening_balance"] = float(open_bal)
                payload["opening_balance_currency_id"] = open_curr
                payload["opening_balance_date"] = open_date or datetime.now().date().isoformat()
            
            res = api_client.post("/investments/", payload)
            if "error" in res:
                return display_error(res), dash.no_update, dash.no_update, dash.no_update, dash.no_update
            
            toast = create_toast("Investment category added", icon="bi-tag", color="success")
            return None, "", "", datetime.now().timestamp(), toast
        except Exception as e:
            return display_error(f"Error: {str(e)}"), dash.no_update, dash.no_update, dash.no_update, dash.no_update

    # --- Add Investment Transfer ---
    @app.callback(
        [
            Output("inv-transfer-form-alert", "children"),
            Output("inv-transfer-amount", "value"),
            Output("inv-transfer-units", "value"),
            Output("inv-transfer-notes", "value"),
            Output("recon-trigger-store", "data", allow_duplicate=True),
            Output("inv-trigger-refresh", "data", allow_duplicate=True),
            Output("inv-toast-container", "children", allow_duplicate=True),
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
             return display_warning("Select a period first"), dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
        
        is_valid, _ = validate_required_fields(category=inv_id, amount=amount, currency=curr_id, source=source_id, date=date_val)
        if not is_valid:
             return display_warning("All fields except units and notes are required"), dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

        try:
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
                 return display_error(res), dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

            toast = create_toast("Transfer recorded", icon="bi-arrow-left-right", color="success")
            return None, "", "", "", datetime.now().timestamp(), datetime.now().timestamp(), toast
        except Exception as e:
            return display_error(f"Error: {str(e)}"), dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

    # --- Delete Modals Logic ---
    @app.callback(
        [
            Output("inv-account-delete-modal", "is_open"),
            Output("inv-account-pending-delete-id", "data"),
            Output("inv-category-delete-modal", "is_open"),
            Output("inv-category-pending-delete-id", "data"),
            Output("inv-transfer-delete-modal", "is_open"),
            Output("inv-transfer-pending-delete-id", "data"),
        ],
        [
            Input({"type": "delete-inv-account-btn", "index": ALL}, "n_clicks"),
            Input({"type": "delete-inv-category-btn", "index": ALL}, "n_clicks"),
            Input({"type": "delete-inv-transfer-btn", "index": ALL}, "n_clicks"),
            Input("inv-account-delete-cancel", "n_clicks"),
            Input("inv-category-delete-cancel", "n_clicks"),
            Input("inv-transfer-delete-cancel", "n_clicks"),
        ],
        prevent_initial_call=True
    )
    def toggle_delete_modals(acc_clicks, cat_clicks, trans_clicks, acc_cancel, cat_cancel, trans_cancel):
        trig = ctx.triggered_id
        if not trig: raise PreventUpdate
        
        if trig == "inv-account-delete-cancel": return False, None, dash.no_update, dash.no_update, dash.no_update, dash.no_update
        if trig == "inv-category-delete-cancel": return dash.no_update, dash.no_update, False, None, dash.no_update, dash.no_update
        if trig == "inv-transfer-delete-cancel": return dash.no_update, dash.no_update, dash.no_update, dash.no_update, False, None
        
        if isinstance(trig, dict):
            if trig["type"] == "delete-inv-account-btn" and any(acc_clicks):
                return True, trig["index"], False, None, False, None
            if trig["type"] == "delete-inv-category-btn" and any(cat_clicks):
                return False, None, True, trig["index"], False, None
            if trig["type"] == "delete-inv-transfer-btn" and any(trans_clicks):
                return False, None, False, None, True, trig["index"]
                
        return [dash.no_update] * 6

    @app.callback(
        [
            Output("inv-trigger-refresh", "data", allow_duplicate=True),
            Output("inv-account-delete-modal", "is_open", allow_duplicate=True),
            Output("inv-category-delete-modal", "is_open", allow_duplicate=True),
            Output("inv-transfer-delete-modal", "is_open", allow_duplicate=True),
            Output("inv-toast-container", "children", allow_duplicate=True),
        ],
        [
            Input("inv-account-delete-confirm", "n_clicks"),
            Input("inv-category-delete-confirm", "n_clicks"),
            Input("inv-transfer-delete-confirm", "n_clicks"),
        ],
        [
            State("inv-account-pending-delete-id", "data"),
            State("inv-category-pending-delete-id", "data"),
            State("inv-transfer-pending-delete-id", "data"),
            State("session-store", "data")
        ],
        prevent_initial_call=True
    )
    def confirm_deletions(acc_conf, cat_conf, trans_conf, acc_id, cat_id, trans_id, session_data):
        trig = ctx.triggered_id
        if not trig: raise PreventUpdate
        
        api_client.set_token(session_data["token"])
        try:
            if trig == "inv-account-delete-confirm" and acc_id:
                res = api_client.delete(f"/investments/accounts/{acc_id}")
                msg = "Investment account deleted"
            elif trig == "inv-category-delete-confirm" and cat_id:
                res = api_client.delete(f"/investments/{cat_id}")
                msg = "Investment category deleted"
            elif trig == "inv-transfer-delete-confirm" and trans_id:
                res = api_client.delete(f"/investments/transfers/{trans_id}")
                msg = "Transfer record deleted"
            else:
                raise PreventUpdate
                
            if "error" in res:
                return dash.no_update, False, False, False, create_toast(parse_api_error(res), icon="bi-x-circle", color="danger")
            
            return datetime.now().timestamp(), False, False, False, create_toast(msg, icon="bi-trash", color="success")
        except Exception as e:
            return dash.no_update, False, False, False, create_toast(str(e), icon="bi-x-circle", color="danger")

# --- UI Creation Helpers ---
def create_inv_accounts_table(accounts):
    if not accounts: return create_empty_state("bi-bank", "No Accounts", "Add an investment account to get started.")
    rows = []
    for acc in accounts:
        rows.append(html.Tr([
            html.Td(acc["account_name"], className="fw-bold"),
            html.Td(acc["account_type"]),
            html.Td(acc.get("notes", ""), className="text-muted small"),
            html.Td(
                dbc.Button(html.I(className="bi bi-trash"), id={"type": "delete-inv-account-btn", "index": acc["id"]}, color="link", className="text-danger p-0"),
                className="text-end"
            )
        ]))
    return dbc.Table([
        html.Thead(html.Tr([html.Th("Account"), html.Th("Type"), html.Th("Notes"), html.Th("", className="text-end")])),
        html.Tbody(rows)
    ], hover=True, striped=True, className="align-middle")

def create_inv_categories_table(investments):
    if not investments: return create_empty_state("bi-graph-up-arrow", "No Categories", "Define an investment category (e.g. S&P 500, BTC).")
    rows = []
    for i in investments:
        op_bal = f"{format_currency(i.get('opening_balance', 0))} {i.get('currency_ticker', '')}" if i.get('opening_balance') else "-"
        op_date = i.get("opening_balance_date", "-") if i.get("opening_balance") else "-"
        rows.append(html.Tr([
            html.Td(i["category_name"], className="fw-bold"),
            html.Td(i.get("account_name", "Unallocated")),
            html.Td(op_bal),
            html.Td(op_date),
            html.Td(
                dbc.Button(html.I(className="bi bi-trash"), id={"type": "delete-inv-category-btn", "index": i["id"]}, color="link", className="text-danger p-0"),
                className="text-end"
            )
        ]))
    return dbc.Table([
        html.Thead(html.Tr([html.Th("Category"), html.Th("Held In"), html.Th("Opening Position"), html.Th("Date"), html.Th("", className="text-end")])),
        html.Tbody(rows)
    ], hover=True, striped=True, className="align-middle")

def create_inv_transfers_table(transfers):
    if not transfers: return html.Div("No transfers in this period.", className="text-muted text-center p-4 italic")
    rows = []
    for t in transfers:
        rows.append(html.Tr([
            html.Td(t["transfer_date"]),
            html.Td(f"{format_currency(t['amount_transferred'])} {t.get('currency_ticker', '')}", className="fw-bold text-primary"),
            html.Td(f"{t.get('units_added', '-')}" if t.get('units_added') else "-"),
            html.Td(t.get("investment_category_name", "")),
            html.Td(t.get("source_account_name", "")),
            html.Td(t.get("notes", ""), className="text-muted small"),
            html.Td(
                dbc.Button(html.I(className="bi bi-trash"), id={"type": "delete-inv-transfer-btn", "index": t["id"]}, color="link", className="text-danger p-0"),
                className="text-end"
            )
        ]))
    return dbc.Table([
        html.Thead(html.Tr([html.Th("Date"), html.Th("Amount"), html.Th("Units"), html.Th("To"), html.Th("From"), html.Th("Notes"), html.Th("", className="text-end")])),
        html.Tbody(rows)
    ], hover=True, striped=True, className="align-middle")
