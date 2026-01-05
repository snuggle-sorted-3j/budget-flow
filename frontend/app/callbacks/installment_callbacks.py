from datetime import datetime, date
import dash
from dash import Input, Output, State, html, dcc, ctx, MATCH, ALL
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc

from utils.api_client import APIClient
from utils.ui_helpers import create_empty_state, format_currency

def register_installment_callbacks(app):
    api_client = APIClient()

    # --- Load Data (Dropdowns & Main Lists) ---
    @app.callback(
        [
            Output("inst-currency", "options"),
            Output("inst-start-period", "options"),
            Output("active-installments-container", "children"),
            Output("paid-off-installments-container", "children"),
            Output("inst-currency", "value"), # Set default
        ],
        [
            Input("url", "pathname"),
            Input("inst-trigger-refresh", "data"),
        ],
        [State("session-store", "data")]
    )
    def load_installments_data(pathname, refresh, session_data):
        if not pathname or "installments" not in pathname:
             raise PreventUpdate
        
        if not session_data or "token" not in session_data:
            return [], [], html.Div("Please log in"), html.Div("Please log in"), dash.no_update

        api_client.set_token(session_data["token"])

        # Fetch Data
        currencies = api_client.get("/currencies/")
        periods = api_client.get("/periods/")
        items = api_client.get("/installments/items")

        # Process Currencies
        curr_opts = []
        default_curr = None
        if "error" not in currencies:
            curr_opts = [{"label": c["ticker"], "value": c["id"]} for c in currencies]
            for c in currencies:
                if c.get("is_default"): default_curr = c["id"]
            if not default_curr and currencies: default_curr = currencies[0]["id"]

        # Process Periods
        period_opts = []
        if "error" not in periods:
            periods.sort(key=lambda x: x["start_date"], reverse=True)
            period_opts = [{"label": f"{p['period_name']} ({p['start_date']})", "value": p["id"]} for p in periods]

        # Process Items
        active_divs = []
        paid_divs = []
        
        if "error" in items:
            active_divs = html.Div("Error loading items")
        else:
            active_items = [i for i in items if i["status"] == "ACTIVE"]
            paid_items = [i for i in items if i["status"] == "PAID_OFF"]
            
            if not active_items:
                active_divs = create_empty_state("bi-credit-card", "No Active Installments", "Add a plan above to start tracking.")
            else:
                # We need to sort active items by name? 
                active_items.sort(key=lambda x: x["item_name"])
                active_divs = [create_installment_card(i) for i in active_items]
                
            if not paid_items:
                 paid_divs = html.Div("No paid off items yet.", className="text-muted p-3")
            else:
                 paid_items.sort(key=lambda x: x["item_name"])
                 paid_divs = create_paid_off_table(paid_items)

        return curr_opts, period_opts, active_divs, paid_divs, default_curr

    # --- Add Installment Item ---
    @app.callback(
        [
            Output("inst-message", "children"),
            Output("inst-message", "color"),
            Output("inst-message-collapse", "is_open"),
            Output("inst-name", "value"),
            Output("inst-total", "value"),
            Output("inst-monthly", "value"),
            Output("inst-months", "value"),
            Output("inst-notes", "value"),
            Output("inst-trigger-refresh", "data", allow_duplicate=True),
        ],
        [Input("add-inst-btn", "n_clicks")],
        [
            State("inst-name", "value"),
            State("inst-total", "value"),
            State("inst-currency", "value"),
            State("inst-start-period", "value"),
            State("inst-monthly", "value"),
            State("inst-months", "value"),
            State("inst-notes", "value"),
            State("session-store", "data"),
        ],
        prevent_initial_call=True
    )
    def add_installment(n_clicks, name, total, curr, period, monthly, months, notes, session_data):
        if not n_clicks: raise PreventUpdate
        
        if not all([name, total, curr, period]):
            return "Fill required fields (*)", "warning", True, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

        api_client.set_token(session_data["token"])
        
        payload = {
            "item_name": name,
            "total_price": float(total),
            "currency_id": curr,
            "initial_period_id": period,
            "monthly_payment_amount": float(monthly) if monthly else None,
            "months_to_pay": int(months) if months else None,
            "notes": notes
        }
        
        res = api_client.post("/installments/items", payload)
        if "error" in res:
             return f"Error: {res['error']}", "danger", True, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
             
        return "Installment created!", "success", True, "", "", "", "", "", datetime.now().timestamp()

    # --- Toggle History ---
    @app.callback(
        [
            Output({"type": "history-collapse", "index": MATCH}, "is_open"),
            Output({"type": "history-container", "index": MATCH}, "children"),
            Output({"type": "history-toggle-icon", "index": MATCH}, "className"),
        ],
        [Input({"type": "history-toggle", "index": MATCH}, "n_clicks")],
        [
            State({"type": "history-collapse", "index": MATCH}, "is_open"),
            State("session-store", "data")
        ],
        prevent_initial_call=True
    )
    def toggle_history(n_clicks, is_open, session_data):
        if not n_clicks: raise PreventUpdate
        new_state = not is_open
        icon_class = "bi bi-chevron-up me-2" if new_state else "bi bi-chevron-down me-2"
        children = dash.no_update
        if new_state:
             trig_id = ctx.triggered_id
             item_id = trig_id["index"]
             api_client.set_token(session_data["token"])
             payments = api_client.get(f"/installments/items/{item_id}/payments")
             children = create_payment_history_table(payments)
        return new_state, children, icon_class

    # --- Open Payment Modal ---
    @app.callback(
        [
            Output("add-payment-modal", "is_open"),
            Output("payment-item-id-store", "data"),
            Output("payment-modal-title", "children"),
            Output("payment-modal-error", "is_open"),
        ],
        [
            Input({"type": "add-payment-btn", "index": ALL}, "n_clicks"),
            Input("payment-cancel-btn", "n_clicks")
        ],
        prevent_initial_call=True
    )
    def open_payment_modal(add_clicks, cancel_click):
        if not ctx.triggered: raise PreventUpdate
        if not ctx.triggered[0]["value"]: return dash.no_update
        
        trig = ctx.triggered_id
        if trig == "payment-cancel-btn":
            return False, dash.no_update, "", False
            
        if isinstance(trig, dict) and trig["type"] == "add-payment-btn":
             item_id = trig["index"]
             return True, item_id, "Record New Payment", False
             
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update

    # --- Save Payment ---
    @app.callback(
        [
            Output("add-payment-modal", "is_open", allow_duplicate=True),
            Output("inst-trigger-refresh", "data", allow_duplicate=True),
            Output("payment-amount", "value"),
            Output("payment-date", "value"),
            Output("payment-notes", "value"),
            Output("payment-modal-error", "children"),
            Output("payment-modal-error", "is_open", allow_duplicate=True),
        ],
        [Input("payment-save-btn", "n_clicks")],
        [
            State("payment-amount", "value"),
            State("payment-date", "value"),
            State("payment-notes", "value"),
            State("payment-item-id-store", "data"),
            State("current-period-id", "data"),
            State("session-store", "data")
        ],
        prevent_initial_call=True
    )
    def save_payment(n_clicks, amount, date_str, notes, item_id, period_id, session_data):
        if not n_clicks: raise PreventUpdate
        if not ctx.triggered[0]["value"]: raise PreventUpdate
        
        # Validation
        if not amount or not date_str:
             return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, "Please enter Amount and Date.", True
             
        if not period_id:
             return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, "Error: No active period selected.", True
             
        api_client.set_token(session_data["token"])
        payload = {
            "payment_amount": float(amount),
            "payment_date": date_str,
            "notes": notes
        }
        
        res = api_client.post(f"/installments/items/{item_id}/payments?period_id={period_id}", payload)
        if "error" in res:
             return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, f"API Error: {res['error']}", True
        
        return False, datetime.now().timestamp(), None, None, "", "", False

    # --- Edit Item Modal ---
    @app.callback(
        [
            Output("edit-inst-modal", "is_open"),
            Output("edit-item-id-store", "data"),
            Output("edit-inst-name", "value"),
            Output("edit-inst-total", "value"),
            Output("edit-inst-monthly", "value"),
            Output("edit-inst-notes", "value"),
            Output("edit-inst-modal-error", "is_open"),
        ],
        [
            Input({"type": "edit-inst-btn", "index": ALL}, "n_clicks"),
            Input("edit-inst-cancel-btn", "n_clicks")
        ],
        [State("session-store", "data")],
        prevent_initial_call=True
    )
    def open_edit_modal(edit_clicks, cancel_click, session_data):
        if not ctx.triggered: raise PreventUpdate
        if not ctx.triggered[0]["value"]: return dash.no_update
        
        trig = ctx.triggered_id
        if trig == "edit-inst-cancel-btn":
            return False, dash.no_update, "", "", "", "", False
            
        if isinstance(trig, dict) and trig["type"] == "edit-inst-btn":
             item_id = trig["index"]
             api_client.set_token(session_data["token"])
             # Fetch all items or just one? Better to fetch details if we had an endpoint, but we have get items.
             # Let's find in the list? Or better get/installment-items/{id}?
             # I added get_installment_item in backend but maybe not endpoint.
             # Let's just use the list from store if we had it, but we don't.
             # Fetching all items for now (small list).
             items = api_client.get("/installments/items")
             item = next((i for i in items if i["id"] == item_id), None)
             if not item: return dash.no_update
             
             return True, item_id, item["item_name"], float(item["total_price"]), float(item["monthly_payment_amount"]) if item["monthly_payment_amount"] else None, item["notes"], False
             
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

    # --- Save Edit ---
    @app.callback(
        [
            Output("edit-inst-modal", "is_open", allow_duplicate=True),
            Output("inst-trigger-refresh", "data", allow_duplicate=True),
            Output("edit-inst-modal-error", "children"),
            Output("edit-inst-modal-error", "is_open", allow_duplicate=True),
        ],
        [Input("edit-inst-save-btn", "n_clicks")],
        [
            State("edit-item-id-store", "data"),
            State("edit-inst-name", "value"),
            State("edit-inst-total", "value"),
            State("edit-inst-monthly", "value"),
            State("edit-inst-notes", "value"),
            State("session-store", "data")
        ],
        prevent_initial_call=True
    )
    def save_edit(n_clicks, item_id, name, total, monthly, notes, session_data):
        if not n_clicks: raise PreventUpdate
        if not item_id: return dash.no_update
        
        api_client.set_token(session_data["token"])
        payload = {
            "item_name": name,
            "total_price": float(total) if total else None,
            "monthly_payment_amount": float(monthly) if monthly else None,
            "notes": notes
        }
        # Clean None to avoid overwriting with null if that's not intended? 
        # But here we want to update.
        payload = {k: v for k, v in payload.items() if v is not None}
        
        res = api_client.patch(f"/installments/items/{item_id}", payload)
        if "error" in res:
             return dash.no_update, dash.no_update, f"Error: {res['error']}", True
             
        return False, datetime.now().timestamp(), "", False


    # --- Delete Payment ---
    @app.callback(
        Output("inst-trigger-refresh", "data", allow_duplicate=True),
        [Input({"type": "delete-payment-btn", "index": ALL}, "n_clicks")],
        [State("session-store", "data")],
        prevent_initial_call=True
    )
    def delete_payment(n_clicks, session_data):
        if not ctx.triggered: raise PreventUpdate
        if not ctx.triggered[0]["value"]: raise PreventUpdate
        
        try:
             trig_dict = ctx.triggered_id
             payment_id = trig_dict["index"]
        except: raise PreventUpdate
        
        api_client.set_token(session_data["token"])
        api_client.delete(f"/installments/payments/{payment_id}")
        
        return datetime.now().timestamp()


def create_installment_card(item):
    total = float(item["total_price"])
    remaining = float(item["remaining_balance"])
    paid = total - remaining
    pct = (paid / total) * 100 if total > 0 else 0
    ticker = item.get("currency_ticker", "")
    
    return dbc.Card(
        dbc.CardBody([
            html.Div([
                html.Div([
                    html.H5(item["item_name"], className="card-title fw-bold mb-0 d-inline-block"),
                    dbc.Badge(item["status"], color="success" if item["status"]=="ACTIVE" else "secondary", className="ms-2")
                ]),
                html.Div([
                    dbc.Button(html.I(className="bi bi-pencil"), id={"type": "edit-inst-btn", "index": item["id"]}, color="link", size="sm", className="text-muted"),
                ])
            ], className="d-flex align-items-center justify-content-between mb-3"),
            
            html.Div([
                html.Span(f"{paid:,.2f} / {total:,.2f} {ticker}", className="fw-bold"),
                html.Span(f"{pct:.1f}% Paid", className="float-end text-muted small")
            ], className="mb-1"),
            
            dbc.Progress(value=pct, color="success" if item["status"]=="PAID_OFF" else "primary", className="mb-3", style={"height": "10px"}),
            
            dbc.Row([
                dbc.Col([
                    html.Div("Remaining", className="text-muted x-small uppercase"),
                    html.Div(f"{remaining:,.2f} {ticker}", className=f"fw-bold {'text-danger' if remaining > 0 else 'text-success'}")
                ], width=4),
                 dbc.Col([
                    html.Div("Monthly Plan", className="text-muted x-small uppercase"),
                    html.Div(f"{float(item['monthly_payment_amount']):,.2f}" if item.get('monthly_payment_amount') else "-", className="fw-bold")
                ], width=4),
                 dbc.Col([
                    dbc.Button("Add Payment", id={"type": "add-payment-btn", "index": item["id"]}, size="sm", color="primary", className="w-100", disabled=(item["status"]=="PAID_OFF"))
                ], width=4, className="d-flex align-items-center"),
            ], className="mb-3"),
            
            html.Hr(),
            
            dbc.Button(
                [html.I(className="bi bi-chevron-down me-2", id={"type": "history-toggle-icon", "index": item["id"]}), f"Payment History ({len(item.get('payments',[]))})"],
                id={"type": "history-toggle", "index": item["id"]},
                color="link",
                size="sm",
                className="p-0 text-decoration-none text-muted"
            ),
            
            dbc.Collapse(
                html.Div(id={"type": "history-container", "index": item["id"]}, className="mt-3"),
                id={"type": "history-collapse", "index": item["id"]},
                is_open=False
            )
        ]),
        className="mb-3 shadow-sm border-0"
    )

def create_payment_history_table(payments):
    if not payments or (isinstance(payments, dict) and "error" in payments) or len(payments) == 0: 
        return html.Div("No payments recorded.", className="text-muted small")
        
    rows = []
    for p in payments:
        rows.append(html.Tr([
            html.Td(p["payment_date"]),
            html.Td(f"{float(p['payment_amount']):,.2f}"),
            html.Td(p.get("period_name", "-")),
            html.Td(p.get("notes", "")),
            html.Td(dbc.Button(html.I(className="bi bi-trash"), id={"type": "delete-payment-btn", "index": p["id"]}, size="sm", color="link", className="text-danger p-0"))
        ]))
        
    return dbc.Table(
        [html.Thead(html.Tr([html.Th("Date"), html.Th("Amount"), html.Th("Period"), html.Th("Notes"), html.Th("")])),
         html.Tbody(rows)],
        size="sm", hover=True, borderless=True
    )

def create_paid_off_table(items):
    return [create_installment_card(i) for i in items]
