"""Enhanced Suspended Transactions callbacks with comprehensive error handling and UX improvements."""
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

def register_suspended_callbacks(app):
    api_client = APIClient()

    # --- Load Data ---
    @app.callback(
        [
            Output("susp-currency", "options"),
            Output("susp-pending-table-container", "children"),
            Output("susp-history-table-container", "children"),
            Output("susp-total-summary", "children"),
            Output("settle-period-select", "options"),
            Output("convert-category-select", "options"),
            Output("susp-currency", "value"),
        ],
        [
            Input("url", "pathname"),
            Input("susp-trigger-refresh", "data"),
            Input("current-period-id", "data"),
        ],
        [State("session-store", "data")]
    )
    def load_suspended_data(pathname, refresh, current_period_id, session_data):
        if not pathname or "suspended" not in pathname:
             raise PreventUpdate
        if not session_data or "token" not in session_data:
            return [], [html.Div("Please log in")], [html.Div("Please log in")], "", [], [], dash.no_update

        try:
            api_client.set_token(session_data["token"])

            # 1. Currencies
            currencies = api_client.get("/currencies/")
            if not currencies:
                 api_client.post("/currencies/initialize", {})
                 currencies = api_client.get("/currencies/")
            curr_opts = []
            curr_map = {}
            default_curr = None
            if isinstance(currencies, list):
                curr_opts = [{"label": c["ticker"], "value": c["id"]} for c in currencies]
                curr_map = {c["id"]: c["ticker"] for c in currencies}
                for c in currencies:
                    if c.get("is_default"): default_curr = c["id"]
                if not default_curr and currencies: default_curr = currencies[0]["id"]

            # 2. Points of interest
            susp_items = api_client.get("/suspended/")
            periods = api_client.get("/periods/")
            categories = api_client.get("/expense-categories/")

            # 3. Periods
            period_opts = []
            if isinstance(periods, list):
                periods.sort(key=lambda x: x["start_date"], reverse=True)
                period_opts = [{"label": f"{p['period_name']} ({p['start_date']})", "value": p["id"]} for p in periods]
                
            # 4. Categories
            cat_opts = []
            if isinstance(categories, list):
                # Build hierarchical options
                parents = [c for c in categories if not c.get("parent_category_id")]
                children_map = {}
                for c in categories:
                    pid = c.get("parent_category_id")
                    if pid:
                        if pid not in children_map:
                            children_map[pid] = []
                        children_map[pid].append(c)
                
                for p in sorted(parents, key=lambda x: x.get("category_name", "")):
                    cat_opts.append({
                        "label": f"📁 {p['category_name']}",
                        "value": p["id"]
                    })
                    children = children_map.get(p["id"], [])
                    for child in sorted(children, key=lambda x: x.get("category_name", "")):
                        cat_opts.append({
                            "label": f"   └─ {child['category_name']}",
                            "value": child["id"]
                        })

            # 5. Tables
            if "error" in susp_items:
                return curr_opts, display_error(susp_items), display_error(susp_items), "", period_opts, cat_opts, default_curr

            pending = [i for i in susp_items if i["status"] == "PENDING"]
            history = [i for i in susp_items if i["status"] != "PENDING"]
            
            pending_table = create_pending_table(pending, curr_map)
            history_table = create_history_table(history, curr_map)
            summary_text = build_summary(pending, curr_map)
            
            return curr_opts, pending_table, history_table, summary_text, period_opts, cat_opts, default_curr
        except Exception as e:
            return [], [], [], "", [], [], dash.no_update

    # --- Add Item ---
    @app.callback(
        [
            Output("susp-form-alert", "children"),
            Output("susp-item-name", "value"), 
            Output("susp-amount", "value"),
            Output("susp-trigger-refresh", "data"),
            Output("susp-submit-spinner", "spinner_style"),
            Output("susp-submit-text", "children"),
            Output("add-susp-btn", "disabled"),
            Output("susp-toast-container", "children"),
        ],
        [Input("add-susp-btn", "n_clicks")],
        [
            State("susp-item-name", "value"),
            State("susp-amount", "value"),
            State("susp-currency", "value"),
            State("susp-type", "value"),
            State("susp-notes", "value"),
            State("current-period-id", "data"),
            State("session-store", "data"),
        ],
        prevent_initial_call=True
    )
    def add_suspended(n_clicks, name, amount, curr, stype, notes, period_id, session_data):
        if not n_clicks: raise PreventUpdate
        
        is_valid, _ = validate_required_fields(name=name, amount=amount, currency=curr, type=stype)
        if not is_valid:
            return display_warning("Please fill all required fields"), dash.no_update, dash.no_update, dash.no_update, {"display": "none"}, "Add", False, None
            
        if not period_id:
             return display_error("No active period found"), dash.no_update, dash.no_update, dash.no_update, {"display": "none"}, "Add", False, None

        try:
            api_client.set_token(session_data["token"])
            payload = {"item_name": name, "amount": float(amount), "currency_id": curr, "transaction_type": stype, "notes": notes}
            res = api_client.post(f"/suspended/{period_id}", payload)
            if "error" in res:
                 return display_error(res), dash.no_update, dash.no_update, dash.no_update, {"display": "none"}, "Add", False, None
                 
            toast = create_toast("Suspended transaction added", icon="bi-pause-circle", color="warning")
            return None, "", "", datetime.now().timestamp(), {"display": "none"}, "Add", False, toast
        except Exception as e:
            return display_error(f"Error: {str(e)}"), dash.no_update, dash.no_update, dash.no_update, {"display": "none"}, "Add", False, None

    # --- Modals (Settle / Convert) ---
    @app.callback(
        [
            Output("settle-modal", "is_open"),
            Output("convert-modal", "is_open"),
            Output("settle-modal-item-text", "children"), 
            Output("convert-modal-item-text", "children"), 
            Output("temp-item-id-store", "data"),
            Output("settle-modal-alert", "children"),
            Output("convert-modal-alert", "children"),
        ],
        [
            Input({"type": "settle-btn", "index": ALL}, "n_clicks"),
            Input({"type": "convert-btn", "index": ALL}, "n_clicks"),
            Input("settle-cancel-btn", "n_clicks"),
            Input("convert-cancel-btn", "n_clicks"),
        ],
        prevent_initial_call=True
    )
    def toggle_modals(settle_clicks, convert_clicks, cancel1, cancel2):
        trig = ctx.triggered_id
        if not trig: raise PreventUpdate
        
        if trig in ["settle-cancel-btn", "convert-cancel-btn"]:
            return False, False, "", "", dash.no_update, None, None

        if isinstance(trig, dict):
            item_id = trig["index"]
            if trig["type"] == "settle-btn" and any(settle_clicks):
                return True, False, f"Settling Item ID: {item_id}", "", item_id, None, None
            if trig["type"] == "convert-btn" and any(convert_clicks):
                return False, True, "", f"Converting Item ID: {item_id}", item_id, None, None
                
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, None, None

    @app.callback(
        [
            Output("settle-modal", "is_open", allow_duplicate=True),
            Output("convert-modal", "is_open", allow_duplicate=True),
            Output("susp-trigger-refresh", "data", allow_duplicate=True),
            Output("settle-modal-alert", "children", allow_duplicate=True),
            Output("convert-modal-alert", "children", allow_duplicate=True),
            Output("susp-toast-container", "children", allow_duplicate=True),
        ],
        [
            Input("settle-confirm-btn", "n_clicks"),
            Input("convert-confirm-btn", "n_clicks"),
        ],
        [
            State("temp-item-id-store", "data"),
            State("settle-period-select", "value"),
            State("convert-category-select", "value"),
            State("current-period-id", "data"), 
            State("session-store", "data")
        ],
        prevent_initial_call=True
    )
    def handle_confirm(s_click, c_click, item_id, settle_period, convert_category, current_period, session_data):
        if not item_id: raise PreventUpdate
        trig = ctx.triggered_id
        
        api_client.set_token(session_data["token"])
        try:
            if trig == "settle-confirm-btn":
                if not settle_period: return dash.no_update, dash.no_update, dash.no_update, display_warning("Please select a period"), dash.no_update, None
                res = api_client.patch(f"/suspended/{item_id}/settle/{settle_period}", {})
                msg = "Transaction settled"
            elif trig == "convert-confirm-btn":
                if not convert_category: return dash.no_update, dash.no_update, dash.no_update, dash.no_update, display_warning("Please select a category"), None
                res = api_client.patch(f"/suspended/{item_id}/convert", params={"period_id": current_period, "category_id": convert_category})
                msg = "Converted to expense"
            else:
                return dash.no_update

            if "error" in res:
                alert = display_error(res)
                return dash.no_update, dash.no_update, dash.no_update, (alert if trig=="settle-confirm-btn" else None), (alert if trig=="convert-confirm-btn" else None), None

            return False, False, datetime.now().timestamp(), None, None, create_toast(msg, icon="bi-check-circle", color="success")
        except Exception as e:
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, create_toast(str(e), color="danger")

    # --- Deletion ---
    @app.callback(
        [
            Output("susp-delete-modal", "is_open"),
            Output("susp-pending-delete-id", "data"),
        ],
        [
            Input({"type": "delete-susp-btn", "index": ALL}, "n_clicks"),
            Input("susp-delete-cancel", "n_clicks"),
        ],
        prevent_initial_call=True
    )
    def toggle_delete_modal(clicks, cancel):
        trig = ctx.triggered_id
        if trig == "susp-delete-cancel": return False, None
        if isinstance(trig, dict) and trig["type"] == "delete-susp-btn" and any(clicks):
            return True, trig["index"]
        return dash.no_update, dash.no_update

    @app.callback(
        [
            Output("susp-trigger-refresh", "data", allow_duplicate=True),
            Output("susp-delete-modal", "is_open", allow_duplicate=True),
            Output("susp-toast-container", "children", allow_duplicate=True),
        ],
        [Input("susp-delete-confirm", "n_clicks")],
        [State("susp-pending-delete-id", "data"), State("session-store", "data")],
        prevent_initial_call=True
    )
    def confirm_delete(n_clicks, item_id, session_data):
        if not n_clicks or not item_id: raise PreventUpdate
        try:
            api_client.set_token(session_data["token"])
            res = api_client.delete(f"/suspended/{item_id}")
            if "error" in res:
                return dash.no_update, False, create_toast(parse_api_error(res), color="danger")
            return datetime.now().timestamp(), False, create_toast("Transaction deleted", icon="bi-trash", color="success")
        except Exception as e:
            return dash.no_update, False, create_toast(str(e), color="danger")

# --- UI Helpers ---
def create_pending_table(items, curr_map):
    if not items: return create_empty_state("bi-check-circle", "Nothing Pending", "Your suspended transactions are all clear.")
    rows = []
    for i in items:
        ticker = curr_map.get(i["currency_id"], "???")
        rows.append(html.Tr([
            html.Td(i["item_name"], className="fw-bold"),
            html.Td(f"{float(i['amount']):,.2f} {ticker}", className="text-primary fw-bold"),
            html.Td(dbc.Badge(i["transaction_type"], color="warning")),
            html.Td(i.get("notes", ""), className="text-muted small"),
            html.Td([
                dbc.Button("Settle", id={"type": "settle-btn", "index": i["id"]}, size="sm", color="success", className="me-2"),
                dbc.Button("Convert", id={"type": "convert-btn", "index": i["id"]}, size="sm", color="outline-danger", className="me-2"),
                dbc.Button(html.I(className="bi bi-trash"), id={"type": "delete-susp-btn", "index": i["id"]}, size="sm", color="link", className="text-danger p-0"),
            ], className="text-end")
        ]))
    return dbc.Table([
        html.Thead(html.Tr([html.Th("Item"), html.Th("Amount"), html.Th("Type"), html.Th("Notes"), html.Th("", className="text-end")])),
        html.Tbody(rows)
    ], hover=True, striped=True, className="align-middle")

def create_history_table(items, curr_map):
    if not items: return html.Div("No transaction history.", className="text-muted text-center p-3 italic")
    rows = []
    for i in items:
        ticker = curr_map.get(i["currency_id"], "???")
        status_color = "success" if i["status"] == "SETTLED" else "danger"
        rows.append(html.Tr([
            html.Td(i["item_name"]),
            html.Td(f"{float(i['amount']):,.2f} {ticker}"),
            html.Td(i["transaction_type"]),
            html.Td(dbc.Badge(i["status"], color=status_color)),
            html.Td(i.get("notes", ""), className="text-muted small"),
        ]))
    return dbc.Table([
        html.Thead(html.Tr([html.Th("Item"), html.Th("Amount"), html.Th("Type"), html.Th("Status"), html.Th("Notes")])),
        html.Tbody(rows)
    ], hover=True, size="sm", className="align-middle")

def build_summary(items, curr_map):
    sums = {}
    for i in items:
        cid = i["currency_id"]
        sums[cid] = sums.get(cid, 0) + float(i["amount"])
    parts = []
    for cid, amount in sums.items():
        ticker = curr_map.get(cid, "?")
        parts.append(f"{amount:,.2f} {ticker}")
    return "Total Pending: " + (" | ".join(parts) if parts else "0.00")
