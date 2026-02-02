"""
Enhanced conversion callbacks with comprehensive error handling, loading states, and UX improvements.
"""
from datetime import datetime
import dash
from dash import Input, Output, State, html, dcc, ctx, ALL
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import plotly.graph_objects as go

from utils.api_client import APIClient
from utils.ui_helpers import (
    create_empty_state, 
    format_currency, 
    create_loading_skeleton,
    create_toast
)
from utils.error_handler import (
    display_error,
    display_success,
    display_warning,
    validate_required_fields,
    validate_positive_number,
    validate_date,
    parse_api_error
)


def register_conversion_callbacks(app):
    api_client = APIClient()

    # --- Load Data with Error Handling ---
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
        [State("session-store", "data")],
        prevent_initial_call=True
    )
    def load_conversions_data(pathname, refresh, period_id, session_data):
        if not pathname or "conversions" not in pathname:
            raise PreventUpdate
        
        if not session_data or "token" not in session_data:
            error_msg = create_empty_state(
                "bi-shield-lock",
                "Authentication Required",
                "Please log in to view conversions."
            )
            return [], [], [], error_msg, dash.no_update, []

        try:
            api_client.set_token(session_data["token"])

            # Fetch Currencies and Accounts with error handling
            try:
                currencies = api_client.get("/currencies/")
                curr_opts = []
                if isinstance(currencies, list):
                    curr_opts = [{"label": c["ticker"], "value": c["id"]} for c in currencies]
                elif "error" in currencies:
                    raise Exception(parse_api_error(currencies))
            except Exception as e:
                curr_opts = []
                print(f"Error loading currencies: {e}")
            
            try:
                accounts = api_client.get("/accounts/")
                acc_opts = [{"label": "None", "value": ""}]
                if isinstance(accounts, list):
                    acc_opts += [{"label": a["account_name"], "value": a["id"]} for a in accounts]
            except Exception as e:
                acc_opts = [{"label": "None", "value": ""}]
                print(f"Error loading accounts: {e}")

            # Fetch Conversions for period
            table_content = create_empty_state(
                "bi-calendar-check",
                "No Period Selected",
                "Select a monitoring period to view conversions."
            )
            pair_opts = []
            
            if period_id:
                try:
                    convs = api_client.get(f"/periods/{period_id}/currency-conversions")
                    
                    if "error" in convs:
                        table_content = display_error(convs)
                    elif not convs or len(convs) == 0:
                        table_content = create_empty_state(
                            "bi-arrow-left-right",
                            "No Conversions Recorded",
                            "Track your currency exchanges by adding your first conversion above.",
                            cta_button=None
                        )
                    else:
                        table_content = create_conversions_table(convs)
                        
                        # Generate unique pairs for trends
                        pairs = set()
                        for c in convs:
                            if c.get("from_currency_ticker") and c.get("to_currency_ticker"):
                                pairs.add((c["from_currency_ticker"], c["to_currency_ticker"]))
                        
                        pair_opts = [
                            {"label": f"{p[0]} → {p[1]}", "value": f"{p[0]}-{p[1]}"} 
                            for p in sorted(list(pairs))
                        ]
                except Exception as e:
                    table_content = display_error(f"Failed to load conversions: {str(e)}")

            # Default date to today
            today = datetime.now().strftime("%Y-%m-%d")

            return curr_opts, curr_opts, acc_opts, table_content, today, pair_opts
            
        except Exception as e:
            error_content = display_error(f"Unexpected error: {str(e)}")
            return [], [], [], error_content, dash.no_update, []

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
        
        try:
            if trig_id == "conv-from-amount":
                if from_amt and rate and rate > 0:
                    new_to = round(from_amt / rate, 2)
                    return new_to, dash.no_update
                    
            elif trig_id == "conv-to-amount":
                if from_amt and from_amt > 0 and to_amt and to_amt > 0:
                    new_rate = round(from_amt / to_amt, 4)
                    return dash.no_update, new_rate
                    
            elif trig_id == "conv-rate":
                if from_amt and from_amt > 0 and rate and rate > 0:
                    new_to = round(from_amt / rate, 2)
                    return new_to, dash.no_update
        except (ValueError, ZeroDivisionError, TypeError):
            pass
                
        return dash.no_update, dash.no_update

    # --- Record Conversion with Validation ---
    @app.callback(
        [
            Output("conv-form-alert", "children"),
            Output("conv-from-amount", "value", allow_duplicate=True),
            Output("conv-to-amount", "value", allow_duplicate=True),
            Output("conv-rate", "value", allow_duplicate=True),
            Output("conv-notes", "value"),
            Output("conv-trigger-refresh", "data"),
            Output("add-conv-btn", "disabled"),
            Output("conv-toast-container", "children"),
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
    def record_conversion(n_clicks, from_curr, from_amt, to_curr, to_amt, rate, date_val, 
                         account_id, notes, period_id, session_data):
        if not n_clicks:
            raise PreventUpdate
        
        try:
            # Validate required fields
            is_valid, errors = validate_required_fields(
                from_currency=from_curr,
                from_amount=from_amt,
                to_currency=to_curr,
                to_amount=to_amt,
                rate=rate,
                date=date_val,
                period=period_id
            )
            
            if not is_valid:
                error_list = [f"{field}: {msg}" for field, msg in errors.items()]
                return (
                    display_warning("Please fill all required fields (*): " + ", ".join(error_list)),
                    dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                    dash.no_update, False, None
                )
            
            # Validate amounts are positive
            is_valid, error_msg = validate_positive_number(from_amt, "From Amount")
            if not is_valid:
                return (
                    display_warning(error_msg),
                    dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                    dash.no_update, False, None
                )
            
            is_valid, error_msg = validate_positive_number(to_amt, "To Amount")
            if not is_valid:
                return (
                    display_warning(error_msg),
                    dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                    dash.no_update, False, None
                )
            
            is_valid, error_msg = validate_positive_number(rate, "Exchange Rate")
            if not is_valid:
                return (
                    display_warning(error_msg),
                    dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                    dash.no_update, False, None
                )
            
            # Validate date
            is_valid, error_msg = validate_date(date_val, allow_future=False, field_name="Conversion Date")
            if not is_valid:
                return (
                    display_warning(error_msg),
                    dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                    dash.no_update, False, None
                )
            
            # Check currencies are different
            if from_curr == to_curr:
                return (
                    display_warning("From and To currencies must be different."),
                    dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                    dash.no_update, False, None
                )

            # Disable button during API call
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
            
            if "error" in res or "detail" in res:
                return (
                    display_error(res),
                    dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                    dash.no_update, False, None
                )
            
            # Success - clear form and show toast
            toast = create_toast(
                "Conversion recorded successfully!",
                icon="bi-check-circle-fill",
                color="success"
            )
            
            return (
                display_success("Conversion recorded successfully!"),
                None, None, None, "",
                datetime.now().timestamp(),
                False,
                toast
            )
            
        except Exception as e:
            return (
                display_error(f"Unexpected error: {str(e)}"),
                dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update, False, None
            )

    # --- Delete Conversion with Confirmation ---
    @app.callback(
        [
            Output("conv-delete-modal", "is_open"),
            Output("conv-pending-delete-id", "data"),
        ],
        [
            Input({"type": "delete-conv-btn", "index": ALL}, "n_clicks"),
            Input("conv-delete-cancel", "n_clicks"),
        ],
        [State("conv-delete-modal", "is_open")],
        prevent_initial_call=True
    )
    def toggle_delete_modal(delete_clicks, cancel_click, is_open):
        if not ctx.triggered:
            raise PreventUpdate
        
        trig = ctx.triggered_id
        
        if trig == "conv-delete-cancel":
            return False, None
        
        if isinstance(trig, dict) and trig["type"] == "delete-conv-btn":
            if any(delete_clicks):
                conv_id = trig["index"]
                return True, conv_id
        
        return dash.no_update, dash.no_update

    @app.callback(
        [
            Output("conv-trigger-refresh", "data", allow_duplicate=True),
            Output("conv-delete-modal", "is_open", allow_duplicate=True),
            Output("conv-toast-container", "children", allow_duplicate=True),
        ],
        [Input("conv-delete-confirm", "n_clicks")],
        [
            State("conv-pending-delete-id", "data"),
            State("session-store", "data")
        ],
        prevent_initial_call=True
    )
    def confirm_delete_conversion(n_clicks, conv_id, session_data):
        if not n_clicks or not conv_id:
            raise PreventUpdate
        
        try:
            api_client.set_token(session_data["token"])
            result = api_client.delete(f"/currency-conversions/{conv_id}")
            
            if "error" in result:
                toast = create_toast(
                    f"Failed to delete: {parse_api_error(result)}",
                    icon="bi-x-circle-fill",
                    color="danger"
                )
                return dash.no_update, False, toast
            
            toast = create_toast(
                "Conversion deleted successfully",
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

    # --- Rate History Chart ---
    @app.callback(
        Output("rate-history-chart", "figure"),
        [Input("rate-pair-select", "value"), Input("conv-trigger-refresh", "data")],
        [State("current-period-id", "data"), State("session-store", "data")]
    )
    def update_rate_chart(pair, refresh, period_id, session_data):
        if not pair or not session_data:
            return go.Figure().update_layout(
                title="Select a currency pair to view trends",
                template="plotly_white"
            )
        
        try:
            api_client.set_token(session_data["token"])
            if not period_id:
                return go.Figure().update_layout(
                    title="No period selected",
                    template="plotly_white"
                )
            
            convs = api_client.get(f"/periods/{period_id}/currency-conversions")
            
            if "error" in convs or not convs:
                return go.Figure().update_layout(
                    title="No data available",
                    template="plotly_white"
                )
            
            # Filter for pair
            from_t, to_t = pair.split("-")
            filtered = [
                c for c in convs 
                if c["from_currency_ticker"] == from_t and c["to_currency_ticker"] == to_t
            ]
            
            if not filtered:
                return go.Figure().update_layout(
                    title=f"No data for {pair} in this period",
                    template="plotly_white"
                )
            
            filtered.sort(key=lambda x: x["conversion_date"])
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=[c["conversion_date"] for c in filtered],
                y=[float(c["rate"]) for c in filtered],
                mode="lines+markers",
                name=f"{from_t} to {to_t}",
                line=dict(width=3, color="#0d6efd"),
                marker=dict(size=8),
                hovertemplate="<b>%{x}</b><br>Rate: %{y:.4f}<extra></extra>"
            ))
            
            fig.update_layout(
                title=f"Exchange Rate Trend: {from_t} → {to_t}",
                xaxis_title="Date",
                yaxis_title=f"Rate ({from_t} per 1 {to_t})",
                template="plotly_white",
                hovermode="x unified",
                margin=dict(l=40, r=40, t=60, b=40),
                height=400
            )
            return fig
            
        except Exception as e:
            return go.Figure().update_layout(
                title=f"Error loading chart: {str(e)}",
                template="plotly_white"
            )


def create_conversions_table(convs):
    """Create conversions table with proper formatting and error handling."""
    if not convs:
        return create_empty_state(
            "bi-inbox",
            "No Conversions",
            "No conversion data available."
        )
    
    rows = []
    for c in convs:
        try:
            from_display = f"{float(c['from_amount']):,.2f} {c['from_currency_ticker']}"
            to_display = f"{float(c['to_amount']):,.2f} {c['to_currency_ticker']}"
            rate_display = f"@ {float(c['rate']):,.2f}"
            
            rows.append(html.Tr([
                html.Td(c["conversion_date"]),
                html.Td(from_display, className="text-danger fw-bold"),
                html.Td(html.I(className="bi bi-arrow-right mx-2")),
                html.Td(to_display, className="text-success fw-bold"),
                html.Td(rate_display, className="text-muted small"),
                html.Td(c.get("source_account_name") or "-"),
                html.Td(c.get("notes") or ""),
                html.Td(
                    dbc.Button(
                        html.I(className="bi bi-trash"),
                        id={"type": "delete-conv-btn", "index": c["id"]},
                        size="sm",
                        color="link",
                        className="text-danger p-0",
                        title="Delete conversion"
                    )
                )
            ]))
        except (KeyError, ValueError, TypeError) as e:
            print(f"Error rendering conversion row: {e}")
            continue
    
    if not rows:
        return create_empty_state(
            "bi-exclamation-triangle",
            "Data Error",
            "Unable to display conversion data."
        )
    
    return dbc.Table(
        [
            html.Thead(html.Tr([
                html.Th("Date"),
                html.Th("From"),
                html.Th(""),
                html.Th("To"),
                html.Th("Rate"),
                html.Th("Source"),
                html.Th("Notes"),
                html.Th("Actions", className="text-center")
            ])),
            html.Tbody(rows)
        ],
        hover=True,
        responsive=True,
        className="align-middle"
    )
