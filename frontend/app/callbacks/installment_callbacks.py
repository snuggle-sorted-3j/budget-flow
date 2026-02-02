"""Enhanced Installment callbacks with comprehensive error handling and UX improvements."""
from datetime import datetime
import dash
from dash import Input, Output, State, html, dcc, ctx, MATCH, ALL
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc

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

def register_installment_callbacks(app):
    api_client = APIClient()

    # --- Load Data ---
    @app.callback(
        [
            Output("inst-currency", "options"),
            Output("inst-start-period", "options"),
            Output("active-installments-container", "children"),
            Output("paid-off-installments-container", "children"),
            Output("inst-currency", "value"),
        ],
        [
            Input("url", "pathname"),
            Input("inst-trigger-refresh", "data"),
            Input("session-store", "data")
        ],
    )
    def load_installments_data(pathname, refresh, session_data):
        if not pathname or "installments" not in pathname:
            raise PreventUpdate
        
        if not session_data or "token" not in session_data:
            return [], [], html.Div("Please log in"), html.Div("Please log in"), dash.no_update

        try:
            api_client.set_token(session_data["token"])
            
            # Fetch Currencies
            currencies = api_client.get("/currencies/")
            if isinstance(currencies, list) and not currencies:
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

            # Fetch Periods
            periods = api_client.get("/periods/")
            period_opts = []
            if isinstance(periods, list):
                periods.sort(key=lambda x: x["start_date"], reverse=True)
                period_opts = [{"label": f"{p['period_name']} ({p['start_date']})", "value": p["id"]} for p in periods]

            # Fetch Items
            items = api_client.get("/installments/items")
            active_divs = []
            paid_divs = []
            
            if "error" in items:
                active_divs = display_error(items)
                paid_divs = ""
            else:
                active_items = [i for i in items if i["status"] == "ACTIVE"]
                paid_items = [i for i in items if i["status"] == "PAID_OFF"]
                
                if not active_items:
                    active_divs = create_empty_state("bi-credit-card", "No Active Installments", "Add a plan above to start tracking.")
                else:
                    active_items.sort(key=lambda x: x["item_name"])
                    active_divs = [create_installment_card(i, curr_map.get(i["currency_id"], "???")) for i in active_items]
                    
                if not paid_items:
                    paid_divs = html.Div("No paid off items yet.", className="text-muted p-3")
                else:
                    paid_items.sort(key=lambda x: x["item_name"])
                    paid_divs = [create_installment_card(i, curr_map.get(i["currency_id"], "???")) for i in paid_items]

            return curr_opts, period_opts, active_divs, paid_divs, default_curr
            
        except Exception as e:
            return [], [], display_error(f"Error loading installments: {str(e)}"), "", dash.no_update

    # --- Add Installment Item ---
    @app.callback(
        [
            Output("inst-form-alert", "children"),
            Output("inst-name", "value"),
            Output("inst-total", "value"),
            Output("inst-monthly", "value"),
            Output("inst-months", "value"),
            Output("inst-notes", "value"),
            Output("inst-trigger-refresh", "data"),
            Output("inst-submit-spinner", "spinner_style"),
            Output("inst-submit-text", "children"),
            Output("add-inst-btn", "disabled"),
            Output("inst-toast-container", "children"),
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
        
        # Validation
        is_valid, errors = validate_required_fields(item_name=name, total_price=total, currency=curr, start_period=period)
        if not is_valid:
            error_msg = ", ".join([f"{k}: {v}" for k, v in errors.items()])
            return display_warning(f"Required fields missing: {error_msg}"), dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, {"display": "none"}, "Create Installment", False, None

        try:
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
                return display_error(res), dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, {"display": "none"}, "Create Installment", False, None
                 
            toast = create_toast("Installment plan created successfully!", icon="bi-check-circle-fill", color="success")
            return None, "", "", "", "", "", datetime.now().timestamp(), {"display": "none"}, "Create Installment", False, toast
            
        except Exception as e:
            return display_error(f"Error: {str(e)}"), dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, {"display": "none"}, "Create Installment", False, None

    # --- Toggle History (MATCH) ---
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
             if "error" in payments:
                 children = html.Div("Error loading payments", className="text-danger small")
             else:
                 children = create_payment_history_table(payments)
        return new_state, children, icon_class

    # --- Payment Modal ---
    @app.callback(
        [
            Output("add-payment-modal", "is_open"),
            Output("payment-item-id-store", "data"),
            Output("payment-modal-title", "children"),
            Output("payment-modal-alert", "children"),
            Output("payment-amount", "value"),
            Output("payment-date", "value"),
            Output("payment-notes", "value"),
        ],
        [
            Input({"type": "add-payment-btn", "index": ALL}, "n_clicks"),
            Input("payment-cancel-btn", "n_clicks")
        ],
        prevent_initial_call=True
    )
    def handle_payment_modal(add_clicks, cancel_click):
        trig = ctx.triggered_id
        if trig == "payment-cancel-btn":
            return False, dash.no_update, "", None, "", "", ""
            
        if isinstance(trig, dict) and trig["type"] == "add-payment-btn":
             if any(add_clicks):
                 item_id = trig["index"]
                 return True, item_id, "Record New Payment", None, "", datetime.now().date().isoformat(), ""
        
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

    @app.callback(
        [
            Output("add-payment-modal", "is_open", allow_duplicate=True),
            Output("inst-trigger-refresh", "data", allow_duplicate=True),
            Output("payment-modal-alert", "children", allow_duplicate=True),
            Output("inst-toast-container", "children", allow_duplicate=True),
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
        if not amount or not date_str:
             return dash.no_update, dash.no_update, display_warning("Amount and Date are required"), None
        if not period_id:
             return dash.no_update, dash.no_update, display_error("No active period selected"), None
        try:
            api_client.set_token(session_data["token"])
            payload = {"payment_amount": float(amount), "payment_date": date_str, "notes": notes}
            res = api_client.post(f"/installments/items/{item_id}/payments?period_id={period_id}", payload)
            if "error" in res:
                return dash.no_update, dash.no_update, display_error(res), None
            toast = create_toast("Payment recorded!", icon="bi-cash-coin", color="success")
            return False, datetime.now().timestamp(), None, toast
        except Exception as e:
            return dash.no_update, dash.no_update, display_error(f"Error: {str(e)}"), None

    # --- Edit Modal ---
    @app.callback(
        [
            Output("edit-inst-modal", "is_open"),
            Output("edit-item-id-store", "data"),
            Output("edit-inst-name", "value"),
            Output("edit-inst-total", "value"),
            Output("edit-inst-monthly", "value"),
            Output("edit-inst-notes", "value"),
            Output("edit-inst-modal-alert", "children"),
        ],
        [
            Input({"type": "edit-inst-btn", "index": ALL}, "n_clicks"),
            Input("edit-inst-cancel-btn", "n_clicks")
        ],
        [State("session-store", "data")],
        prevent_initial_call=True
    )
    def handle_edit_modal(edit_clicks, cancel_click, session_data):
        trig = ctx.triggered_id
        if trig == "edit-inst-cancel-btn":
            return False, dash.no_update, "", "", "", "", None
            
        if isinstance(trig, dict) and trig["type"] == "edit-inst-btn":
             if any(edit_clicks):
                 item_id = trig["index"]
                 api_client.set_token(session_data["token"])
                 items = api_client.get("/installments/items")
                 item = next((i for i in items if i["id"] == item_id), None)
                 if item:
                     return True, item_id, item["item_name"], float(item["total_price"]), float(item["monthly_payment_amount"]) if item["monthly_payment_amount"] else None, item["notes"], None
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

    @app.callback(
        [
            Output("edit-inst-modal", "is_open", allow_duplicate=True),
            Output("inst-trigger-refresh", "data", allow_duplicate=True),
            Output("edit-inst-modal-alert", "children", allow_duplicate=True),
            Output("inst-toast-container", "children", allow_duplicate=True),
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
        if not n_clicks or not item_id: raise PreventUpdate
        try:
            api_client.set_token(session_data["token"])
            payload = {
                "item_name": name,
                "total_price": float(total) if total else None,
                "monthly_payment_amount": float(monthly) if monthly else None,
                "notes": notes
            }
            payload = {k: v for k, v in payload.items() if v is not None}
            res = api_client.patch(f"/installments/items/{item_id}", payload)
            if "error" in res:
                return dash.no_update, dash.no_update, display_error(res), None
            toast = create_toast("Changes saved!", icon="bi-save", color="success")
            return False, datetime.now().timestamp(), None, toast
        except Exception as e:
            return dash.no_update, dash.no_update, display_error(f"Error: {str(e)}"), None

    # --- Item Deletion ---
    @app.callback(
        [
            Output("inst-delete-modal", "is_open"),
            Output("inst-pending-delete-id", "data"),
        ],
        [
            Input({"type": "delete-item-btn", "index": ALL}, "n_clicks"),
            Input("inst-delete-cancel", "n_clicks"),
        ],
        [State("inst-delete-modal", "is_open")],
        prevent_initial_call=True
    )
    def toggle_delete_modal(delete_clicks, cancel_click, is_open):
        trig = ctx.triggered_id
        if trig == "inst-delete-cancel":
            return False, None
        if isinstance(trig, dict) and trig["type"] == "delete-item-btn":
            if any(delete_clicks):
                return True, trig["index"]
        return dash.no_update, dash.no_update

    @app.callback(
        [
            Output("inst-trigger-refresh", "data", allow_duplicate=True),
            Output("inst-delete-modal", "is_open", allow_duplicate=True),
            Output("inst-toast-container", "children", allow_duplicate=True),
        ],
        [Input("inst-delete-confirm", "n_clicks")],
        [
            State("inst-pending-delete-id", "data"),
            State("session-store", "data")
        ],
        prevent_initial_call=True
    )
    def confirm_delete_installment(n_clicks, item_id, session_data):
        if not n_clicks or not item_id: raise PreventUpdate
        try:
            api_client.set_token(session_data["token"])
            res = api_client.delete(f"/installments/items/{item_id}")
            if "error" in res:
                return dash.no_update, False, create_toast(f"Error: {parse_api_error(res)}", icon="bi-x-circle", color="danger")
            return datetime.now().timestamp(), False, create_toast("Installment plan deleted", icon="bi-trash", color="success")
        except Exception as e:
            return dash.no_update, False, create_toast(f"Error: {str(e)}", icon="bi-x-circle", color="danger")

    # --- Delete Payment ---
    @app.callback(
        [
            Output("inst-trigger-refresh", "data", allow_duplicate=True),
            Output("inst-toast-container", "children", allow_duplicate=True),
        ],
        [Input({"type": "delete-payment-btn", "index": ALL}, "n_clicks")],
        [State("session-store", "data")],
        prevent_initial_call=True
    )
    def delete_payment(n_clicks, session_data):
        if not ctx.triggered or not any(n_clicks): raise PreventUpdate
        try:
             payment_id = ctx.triggered_id["index"]
             api_client.set_token(session_data["token"])
             res = api_client.delete(f"/installments/payments/{payment_id}")
             if "error" in res:
                 return dash.no_update, create_toast(f"Error: {parse_api_error(res)}", icon="bi-x-circle", color="danger")
             return datetime.now().timestamp(), create_toast("Payment deleted", icon="bi-trash", color="info")
        except Exception as e:
             return dash.no_update, create_toast(f"Error: {str(e)}", icon="bi-x-circle", color="danger")

# --- UI Helpers ---
def create_installment_card(item, ticker):
    total = float(item["total_price"])
    remaining = float(item["remaining_balance"])
    paid = total - remaining
    pct = (paid / total) * 100 if total > 0 else 0
    return dbc.Card(
        dbc.CardBody([
            html.Div([
                html.Div([
                    html.H5(item["item_name"], className="card-title fw-bold mb-0 d-inline-block"),
                    dbc.Badge(item["status"], color="success" if item["status"]=="ACTIVE" else "secondary", className="ms-2")
                ]),
                html.Div([
                    dbc.Button(html.I(className="bi bi-pencil"), id={"type": "edit-inst-btn", "index": item["id"]}, color="link", size="sm", className="text-muted", title="Edit plan"),
                    dbc.Button(html.I(className="bi bi-trash"), id={"type": "delete-item-btn", "index": item["id"]}, color="link", size="sm", className="text-danger ps-2", title="Delete plan"),
                ])
            ], className="d-flex align-items-center justify-content-between mb-3"),
            html.Div([
                html.Span(f"{paid:,.2f} / {total:,.2f} {ticker}", className="fw-bold"),
                html.Span(f"{pct:.1f}% Paid", className="float-end text-muted small")
            ], className="mb-1"),
            dbc.Progress(value=pct, color="success" if item["status"]=="PAID_OFF" else "primary", className="mb-3", style={"height": "10px"}),
            dbc.Row([
                dbc.Col([
                    html.Div("Remaining", className="text-muted small text-uppercase"),
                    html.Div(f"{remaining:,.2f} {ticker}", className=f"fw-bold {'text-danger' if remaining > 0 else 'text-success'}")
                ], width=4),
                 dbc.Col([
                    html.Div("Monthly Plan", className="text-muted small text-uppercase"),
                    html.Div(f"{float(item['monthly_payment_amount']):,.2f} {ticker}" if item.get('monthly_payment_amount') else "-", className="fw-bold")
                ], width=4),
                 dbc.Col([
                    dbc.Button("Add Payment", id={"type": "add-payment-btn", "index": item["id"]}, size="sm", color="primary", className="w-100", disabled=(item["status"]=="PAID_OFF"))
                ], width=4, className="d-flex align-items-center"),
            ], className="mb-3 align-items-center"),
            html.Hr(),
            dbc.Button(
                [html.I(className="bi bi-chevron-down me-2", id={"type": "history-toggle-icon", "index": item["id"]}), f"Payment History ({len(item.get('payments',[]))})"],
                id={"type": "history-toggle", "index": item["id"]},
                color="link", size="sm", className="p-0 text-decoration-none text-muted"
            ),
            dbc.Collapse(
                html.Div(id={"type": "history-container", "index": item["id"]}, className="mt-3"),
                id={"type": "history-collapse", "index": item["id"]}, is_open=False
            )
        ]),
        className="mb-3 shadow-sm border-0"
    )

def create_payment_history_table(payments):
    if not payments or len(payments) == 0: 
        return html.Div("No payments recorded.", className="text-muted small italic")
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
        size="sm", hover=True, borderless=True, className="align-middle"
    )
