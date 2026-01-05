from datetime import datetime
import dash
from dash import Input, Output, State, html, dcc, ctx, ALL
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc

from utils.api_client import APIClient
from utils.ui_helpers import create_empty_state, format_currency

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
            return [], html.Div("Please log in"), html.Div("Please log in"), "", [], [], dash.no_update

        api_client.set_token(session_data["token"])

        # Fetch Data
        currencies = api_client.get("/currencies/")
        if not currencies or (isinstance(currencies, list) and len(currencies) == 0):
             api_client.post("/currencies/initialize", {})
             currencies = api_client.get("/currencies/")
             
        susp_items = api_client.get("/suspended/")
        periods = api_client.get("/periods/")
        categories = api_client.get("/expense-categories/")

        # Process Currencies
        curr_opts = []
        curr_map = {}
        default_curr = None
        
        if "error" not in currencies:
            curr_opts = [{"label": c["ticker"], "value": c["id"]} for c in currencies]
            curr_map = {c["id"]: c["ticker"] for c in currencies}
            for c in currencies:
                if c.get("is_default"): default_curr = c["id"]
            if not default_curr and currencies: default_curr = currencies[0]["id"]

        # Process Periods (for settle modal)
        period_opts = []
        if "error" not in periods:
            # Sort by start_date desc
            periods.sort(key=lambda x: x["start_date"], reverse=True)
            period_opts = [
                {"label": f"{p['period_name']} ({p['start_date']})", "value": p["id"]} 
                for p in periods
            ]
            
        # Process Categories (for convert modal)
        cat_opts = []
        if "error" not in categories:
            cat_opts = [{"label": c["category_name"], "value": c["id"]} for c in categories]

        # Process Suspended Items
        if "error" in susp_items:
            return curr_opts, html.Div("Error loading data"), html.Div("Error"), "", period_opts, cat_opts, default_curr

        pending_items = [i for i in susp_items if i["status"] == "PENDING"]
        history_items = [i for i in susp_items if i["status"] != "PENDING"]
        
        # Build Tables
        pending_table = create_pending_table(pending_items, curr_map)
        history_table = create_history_table(history_items, curr_map)
        
        # Build Summary
        summary_text = build_summary(pending_items, curr_map)
        
        return curr_opts, pending_table, history_table, summary_text, period_opts, cat_opts, default_curr

    # --- Add Suspended Item ---
    @app.callback(
        [
            Output("susp-message", "children"),
            Output("susp-message", "color"),
            Output("susp-message-collapse", "is_open"),
            Output("susp-item-name", "value"), 
            Output("susp-amount", "value"),
            Output("susp-trigger-refresh", "data", allow_duplicate=True),
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
        
        if not all([name, amount, curr, stype]):
            return "Please fill all required fields", "warning", True, dash.no_update, dash.no_update, dash.no_update
            
        if not period_id:
             return "No active period found", "danger", True, dash.no_update, dash.no_update, dash.no_update

        api_client.set_token(session_data["token"])
        
        payload = {
            "item_name": name,
            "amount": float(amount),
            "currency_id": curr,
            "transaction_type": stype,
            "notes": notes
        }
        
        res = api_client.post(f"/suspended/{period_id}", payload)
        if "error" in res:
             return f"Error: {res['error']}", "danger", True, dash.no_update, dash.no_update, dash.no_update
             
        return "Transaction added!", "success", True, "", "", datetime.now().timestamp()

    # --- Handle Modal Open (Settle / Convert) ---
    @app.callback(
        [
            Output("settle-modal", "is_open"),
            Output("convert-modal", "is_open"),
            Output("settle-modal-item-text", "children"), 
            Output("convert-modal-item-text", "children"), 
            Output("temp-item-id-store", "data"),
        ],
        [
            Input({"type": "settle-btn", "index": ALL}, "n_clicks"),
            Input({"type": "convert-btn", "index": ALL}, "n_clicks"),
            Input("settle-cancel-btn", "n_clicks"),
            Input("convert-cancel-btn", "n_clicks"),
        ],
        [State("session-store", "data")],
        prevent_initial_call=True
    )
    def toggle_modals(settle_clicks, convert_clicks, cancel1, cancel2, session_data):
        if not ctx.triggered: raise PreventUpdate
        trig_id = ctx.triggered[0]["prop_id"].split(".")[0]
        
        if "cancel" in trig_id:
            return False, False, "", "", dash.no_update
            
        # Verify valid click (ignore initial None/0 triggered by component creation)
        if not ctx.triggered[0]["value"]:
             return dash.no_update

        try:
            trig_dict = ctx.triggered_id
            if not trig_dict: raise Exception
            
            item_id = trig_dict["index"]
            action = trig_dict["type"]
            
            text = f"Selected Item ID: {item_id}" # Ideally we'd map this to name if we had it in store
            
            if action == "settle-btn":
                return True, False, text, "", item_id
            elif action == "convert-btn":
                return False, True, "", text, item_id
                
        except:
            return dash.no_update
            
        return dash.no_update

    # --- Handle Modal Confirm Actions ---
    @app.callback(
        [
            Output("settle-modal", "is_open", allow_duplicate=True),
            Output("convert-modal", "is_open", allow_duplicate=True),
            Output("susp-trigger-refresh", "data", allow_duplicate=True),
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
    def handle_modal_confirm(click_settle, click_convert, item_id, settle_period, convert_category, current_period, session_data):
        if not item_id: raise PreventUpdate
        
        if not ctx.triggered: raise PreventUpdate
        trig = ctx.triggered_id
        
        api_client.set_token(session_data["token"])
        
        if trig == "settle-confirm-btn":
            if not settle_period: return dash.no_update 
            res = api_client.patch(f"/suspended/{item_id}/settle/{settle_period}", {})
            if "error" in res: return dash.no_update 
            return False, False, datetime.now().timestamp()
            
        elif trig == "convert-confirm-btn":
            if not convert_category: return dash.no_update
            res = api_client.patch(f"/suspended/{item_id}/convert", params={
                "period_id": current_period,
                "category_id": convert_category
            }) 
            
            if res and "error" in res: return dash.no_update
            
            return False, False, datetime.now().timestamp()
            
        return dash.no_update

    # --- Handle Delete ---
    @app.callback(
        Output("susp-trigger-refresh", "data", allow_duplicate=True),
        [Input({"type": "delete-susp-btn", "index": ALL}, "n_clicks")],
        [State("session-store", "data")],
        prevent_initial_call=True
    )
    def delete_suspended(n_clicks, session_data):
        if not ctx.triggered: raise PreventUpdate
        
        # Check actual click
        if not ctx.triggered[0]["value"]: raise PreventUpdate
        
        try:
             trig_dict = ctx.triggered_id
             item_id = trig_dict["index"]
        except:
             raise PreventUpdate
             
        api_client.set_token(session_data["token"])
        # Backend deletes it; if it fails (e.g. not found), we still refresh
        res = api_client.delete(f"/suspended/{item_id}")
        
        return datetime.now().timestamp()


def create_pending_table(items, curr_map):
    if not items: return create_empty_state("bi-pause-circle", "No Pending Items", "All caught up!")
    
    rows = []
    for i in items:
        ticker = curr_map.get(i["currency_id"], "")
        rows.append(html.Tr([
            html.Td(i["item_name"], className="fw-bold"),
            html.Td(f"{float(i['amount']):,.2f} {ticker}"),
            html.Td(i["transaction_type"]),
            html.Td(i.get("notes", "")),
            html.Td([
                dbc.Button("Settle", id={"type": "settle-btn", "index": i["id"]}, size="sm", color="success", className="me-2"),
                dbc.Button("Convert", id={"type": "convert-btn", "index": i["id"]}, size="sm", color="outline-danger", className="me-2"),
                dbc.Button(html.I(className="bi bi-trash"), id={"type": "delete-susp-btn", "index": i["id"]}, size="sm", color="link", className="text-danger"),
            ], className="text-end")
        ]))
        
    return dbc.Table(
        [html.Thead(html.Tr([html.Th("Item"), html.Th("Amount"), html.Th("Type"), html.Th("Notes"), html.Th("Actions", className="text-end")])),
         html.Tbody(rows)],
        hover=True, striped=True, className="align-middle"
    )

def create_history_table(items, curr_map):
    if not items: return html.Div("No history yet.", className="text-muted p-3")
    
    rows = []
    for i in items:
        ticker = curr_map.get(i["currency_id"], "")
        status_color = "success" if i["status"] == "SETTLED" else "danger"
        rows.append(html.Tr([
            html.Td(i["item_name"]),
            html.Td(f"{float(i['amount']):,.2f} {ticker}"),
            html.Td(i["transaction_type"]),
            html.Td(i["status"], className=f"text-{status_color}"),
            # html.Td(i.get("settled_period_id", "-") if i["status"]=="SETTLED" else "-"),
            html.Td(i.get("notes", "")),
        ]))
        
    return dbc.Table(
        [html.Thead(html.Tr([html.Th("Item"), html.Th("Amount"), html.Th("Type"), html.Th("Status"), html.Th("Notes")])),
         html.Tbody(rows)],
        hover=True, size="sm"
    )

def build_summary(items, curr_map):
    # Sum by currency
    sums = {}
    for i in items:
        cid = i["currency_id"]
        sums[cid] = sums.get(cid, 0) + float(i["amount"])
        
    parts = []
    for cid, amount in sums.items():
        ticker = curr_map.get(cid, "?")
        parts.append(f"{amount:,.2f} {ticker}")
        
    if not parts: return "Total Pending: 0.00"
    return "Total Pending: " + " | ".join(parts)
