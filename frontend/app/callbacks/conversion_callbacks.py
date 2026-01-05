from datetime import datetime
import dash
from dash import Input, Output, State, html, dcc, ctx, ALL
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import plotly.graph_objects as go

from utils.api_client import APIClient
from utils.ui_helpers import create_empty_state, format_currency

def register_conversion_callbacks(app):
    api_client = APIClient()

    # --- Load Data ---
    @app.callback(
        [
            Output("conv-from-currency", "options"),
            Output("conv-to-currency", "options"),
            Output("conv-account", "options"),
            Output("conversions-table-container", "children"),
            Output("conv-date", "value"),
            Output("rate-pair-select", "options"),
        ],
        [
            Input("url", "pathname"),
            Input("conv-trigger-refresh", "data"),
            Input("current-period-id", "data"),
        ],
        [State("session-store", "data")]
    )
    def load_conversions_data(pathname, refresh, period_id, session_data):
        if not pathname or "conversions" not in pathname:
             raise PreventUpdate
        
        if not session_data or "token" not in session_data:
            return [], [], [], html.Div("Please log in"), dash.no_update, []

        api_client.set_token(session_data["token"])

        # Fetch Currencies and Accounts
        currencies = api_client.get("/currencies/")
        accounts = api_client.get("/accounts/")
        
        curr_opts = []
        if "error" not in currencies:
            curr_opts = [{"label": c["ticker"], "value": c["id"]} for c in currencies]
            
        acc_opts = [{"label": "None", "value": ""}]
        if "error" not in accounts:
            acc_opts += [{"label": a["account_name"], "value": a["id"]} for a in accounts]

        # Fetch Conversions for period
        table_content = html.Div("Select a period to view conversions.", className="text-muted")
        pair_opts = []
        if period_id:
            convs = api_client.get(f"/periods/{period_id}/currency-conversions")
            if "error" in convs:
                table_content = html.Div(f"Error: {convs['error']}", className="text-danger")
            elif not convs:
                table_content = create_empty_state("bi-arrow-left-right", "No Conversions Recorded", "Add an exchange transaction above.")
            else:
                table_content = create_conversions_table(convs)
                # Generate unique pairs for trends
                pairs = set()
                for c in convs:
                    if c.get("from_currency_ticker") and c.get("to_currency_ticker"):
                        pairs.add((c["from_currency_ticker"], c["to_currency_ticker"]))
                
                pair_opts = [{"label": f"{p[0]} → {p[1]}", "value": f"{p[0]}-{p[1]}"} for p in sorted(list(pairs))]

        # Default date to today
        today = datetime.now().strftime("%Y-%m-%d")

        return curr_opts, curr_opts, acc_opts, table_content, today, pair_opts

    # --- Bi-directional Calculation Logic ---
    @app.callback(
        [Output("conv-to-amount", "value"), Output("conv-rate", "value")],
        [
            Input("conv-from-amount", "value"),
            Input("conv-to-amount", "value"),
            Input("conv-rate", "value"),
        ],
        prevent_initial_call=True
    )
    def handle_conversions_math(from_amt, to_amt, rate):
        trig_id = ctx.triggered_id
        
        # We need at least "From" to calculate something usually, or "To" + "Rate" 
        # But per user request: if From and To are present, calc Rate. If Rate is changed, update To.
        
        if trig_id == "conv-from-amount":
            # If changed from, update TO if Rate exists
            if from_amt and rate and rate > 0:
                new_to = round(from_amt / rate, 2)
                return new_to, dash.no_update
                
        elif trig_id == "conv-to-amount":
            # If changed to, update RATE: Rate = From / To
            if from_amt and from_amt > 0 and to_amt and to_amt > 0:
                new_rate = round(from_amt / to_amt, 4)
                return dash.no_update, new_rate
                
        elif trig_id == "conv-rate":
            # If changed rate, update TO: To = From / Rate
            if from_amt and from_amt > 0 and rate and rate > 0:
                new_to = round(from_amt / rate, 2)
                return new_to, dash.no_update
                
        return dash.no_update, dash.no_update

    # --- Record Conversion ---
    @app.callback(
        [
            Output("conv-message", "children"),
            Output("conv-message", "color"),
            Output("conv-message-collapse", "is_open"),
            Output("conv-from-amount", "value", allow_duplicate=True),
            Output("conv-to-amount", "value", allow_duplicate=True),
            Output("conv-rate", "value", allow_duplicate=True),
            Output("conv-notes", "value"),
            Output("conv-trigger-refresh", "data", allow_duplicate=True),
        ],
        [Input("add-conv-btn", "n_clicks")],
        [
            State("conv-from-currency", "value"),
            State("conv-from-amount", "value"),
            State("conv-to-currency", "value"),
            State("conv-to-amount", "value"),
            State("conv-rate", "value"),
            State("conv-date", "value"),
            State("conv-account", "value"),
            State("conv-notes", "value"),
            State("current-period-id", "data"),
            State("session-store", "data"),
        ],
        prevent_initial_call=True
    )
    def record_conversion(n_clicks, from_curr, from_amt, to_curr, to_amt, rate, date_val, account_id, notes, period_id, session_data):
        if not n_clicks: raise PreventUpdate
        
        if not all([from_curr, from_amt, to_curr, to_amt, rate, date_val, period_id]):
            return "Please fill all required fields (*).", "warning", True, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

        if from_curr == to_curr:
            return "From and To currencies must be different.", "danger", True, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

        api_client.set_token(session_data["token"])
        
        payload = {
            "from_currency_id": from_curr,
            "to_currency_id": to_curr,
            "from_amount": float(from_amt),
            "to_amount": float(to_amt),
            "rate": float(rate),
            "conversion_date": date_val,
            "source_account_id": account_id if account_id else None,
            "notes": notes
        }
        
        res = api_client.post(f"/periods/{period_id}/currency-conversions", payload)
        if "error" in res:
             return f"Error: {res['error']}", "danger", True, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
             
        return "Conversion recorded!", "success", True, None, None, None, "", datetime.now().timestamp()

    # --- Delete Conversion ---
    @app.callback(
        Output("conv-trigger-refresh", "data", allow_duplicate=True),
        [Input({"type": "delete-conv-btn", "index": ALL}, "n_clicks")],
        [State("session-store", "data")],
        prevent_initial_call=True
    )
    def delete_conversion(n_clicks, session_data):
        if not ctx.triggered: raise PreventUpdate
        if not any(n_clicks): raise PreventUpdate
        
        trig = ctx.triggered_id
        if isinstance(trig, dict) and trig["type"] == "delete-conv-btn":
            conv_id = trig["index"]
            api_client.set_token(session_data["token"])
            api_client.delete(f"/currency-conversions/{conv_id}")
            return datetime.now().timestamp()
            
        raise PreventUpdate

    # --- Rate History Chart ---
    @app.callback(
        Output("rate-history-chart", "figure"),
        [Input("rate-pair-select", "value"), Input("conv-trigger-refresh", "data")],
        [State("current-period-id", "data"), State("session-store", "data")]
    )
    def update_rate_chart(pair, refresh, period_id, session_data):
        if not pair or not session_data:
            return go.Figure().update_layout(title="Select a currency pair to view trends")
        
        api_client.set_token(session_data["token"])
        if not period_id: return go.Figure()
        
        convs = api_client.get(f"/periods/{period_id}/currency-conversions")
        if "error" in convs or not convs: return go.Figure()
        
        # Filter for pair (ticker based)
        from_t, to_t = pair.split("-")
        filtered = [c for c in convs if c["from_currency_ticker"] == from_t and c["to_currency_ticker"] == to_t]
        
        if not filtered:
            return go.Figure().update_layout(title=f"No data for {pair} in this period")
            
        filtered.sort(key=lambda x: x["conversion_date"])
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=[c["conversion_date"] for c in filtered],
            y=[float(c["rate"]) for c in filtered],
            mode="lines+markers",
            name=f"{from_t} to {to_t}",
            line=dict(width=3, color="#0d6efd"),
            marker=dict(size=8)
        ))
        
        fig.update_layout(
            title=f"Exchange Rate Trend: {from_t} → {to_t}",
            xaxis_title="Date",
            yaxis_title=f"Rate ({from_t} per 1 {to_t})",
            template="plotly_white",
            hovermode="x unified",
            margin=dict(l=40, r=40, t=60, b=40)
        )
        return fig


def create_conversions_table(convs):
    rows = []
    for c in convs:
        from_display = f"{float(c['from_amount']):,.2f} {c['from_currency_ticker']}"
        to_display = f"{float(c['to_amount']):,.2f} {c['to_currency_ticker']}"
        rate_display = f"@ {float(c['rate']):,.2f}"
        
        rows.append(html.Tr([
            html.Td(c["conversion_date"]),
            html.Td(from_display, className="text-danger fw-bold"),
            html.Td(html.I(className="bi bi-arrow-right mx-2")),
            html.Td(to_display, className="text-success fw-bold"),
            html.Td(rate_display, className="text-muted small"),
            html.Td(c["source_account_name"] or "-"),
            html.Td(c["notes"] or ""),
            html.Td(dbc.Button(html.I(className="bi bi-trash"), id={"type": "delete-conv-btn", "index": c["id"]}, size="sm", color="link", className="text-danger p-0"))
        ]))
        
    return dbc.Table(
        [html.Thead(html.Tr([
            html.Th("Date"), html.Th("From"), html.Th(""), html.Th("To"), html.Th("Rate"), html.Th("Source"), html.Th("Notes"), html.Th("")
        ])),
         html.Tbody(rows)],
        hover=True, responsive=True, className="align-middle"
    )
