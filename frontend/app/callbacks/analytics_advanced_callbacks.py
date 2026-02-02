import dash
from dash import Input, Output, State, html, dcc, dash_table
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, date, timedelta
import pandas as pd
import io

from utils.api_client import APIClient
from utils.ui_helpers import format_currency, get_amount_class, create_empty_state

COLOR_INCOME = "#10b981"
COLOR_EXPENSE = "#ef4444"
COLOR_NEUTRAL = "#3b82f6"

def register_analytics_advanced_callbacks(app):
    """Register callbacks for the advanced analytics tab."""
    api_client = APIClient()

    # 1. Custom Range Analysis
    @app.callback(
        Output("advanced-range-results", "children"),
        [Input("analyze-range-btn", "n_clicks")],
        [
            State("analytics-date-range", "start_date"),
            State("analytics-date-range", "end_date"),
            State("session-store", "data"),
        ],
        prevent_initial_call=False # Load initial if possible
    )
    def update_range_analysis(n, start_date, end_date, session_data):
        if not session_data or not start_date or not end_date:
            return html.Div("Select a date range and click Apply", className="text-muted text-center py-4")

        try:
            api_client.set_token(session_data["token"])
            spending = api_client.get(f"/analytics/spending-by-category?start_date={start_date}&end_date={end_date}")
            top_exp = api_client.get(f"/analytics/top-expenses?start_date={start_date}&end_date={end_date}&limit=5")
            
            if not spending or not spending.get("by_category"):
                return create_empty_state("bi-search", "No Results", "No data found for this range.")

            # Create range charts
            fig_pie = px.pie(spending["by_category"], values="total", names="category_name", hole=0.3)
            fig_pie.update_layout(margin=dict(l=0, r=0, t=0, b=0), showlegend=False)

            return dbc.Row([
                dbc.Col([
                    html.H6("Range Spending Breakdown", className="fw-bold text-center"),
                    dcc.Graph(figure=fig_pie, style={"height": "300px"})
                ], md=6),
                dbc.Col([
                    html.H6("Top Expenses in Range", className="fw-bold"),
                    dbc.ListGroup([
                        dbc.ListGroupItem([
                            html.Div([
                                html.Span(e["item_name"], className="fw-bold"),
                                html.Span(format_currency(e["amount"]), className="float-end text-danger")
                            ]),
                            html.Small(f"{e['category']} • {e['date']}", className="text-muted")
                        ]) for e in (top_exp if isinstance(top_exp, list) else [])
                    ], flush=True)
                ], md=6)
            ])
        except Exception as e:
            return html.Div(f"Error: {str(e)}", className="text-danger")

    # 2. Savings Rate & Insights
    @app.callback(
        [Output("advanced-savings-rate-chart", "children"), Output("advanced-insights-container", "children")],
        [Input("url", "pathname")],
        [State("session-store", "data")],
    )
    def update_savings_and_insights(pathname, session_data):
        if pathname != "/dashboard/analytics-advanced" or not session_data:
            raise PreventUpdate

        try:
            api_client.set_token(session_data["token"])
            ive_data = api_client.get("/analytics/income-vs-expenses?num_periods=6")
            
            # Savings Rate Gauge
            gauge_div = html.Div("No data for savings rate", className="text-muted")
            insights = []

            if ive_data and ive_data.get("periods"):
                current = ive_data["periods"][-1]
                inc = current["income"]
                exp = current["expenses"]
                rate = ((inc - exp) / inc * 100) if inc > 0 else 0
                
                fig = go.Figure(go.Indicator(
                    mode = "gauge+number",
                    value = rate,
                    domain = {'x': [0, 1], 'y': [0, 1]},
                    title = {'text': "Current Savings Rate (%)", 'font': {'size': 14}},
                    gauge = {
                        'axis': {'range': [None, 100]},
                        'bar': {'color': COLOR_INCOME},
                        'steps': [
                            {'range': [0, 15], 'color': "rgba(239, 68, 68, 0.1)"},
                            {'range': [15, 30], 'color': "rgba(59, 130, 246, 0.1)"},
                            {'range': [30, 100], 'color': "rgba(16, 185, 129, 0.1)"}
                        ],
                        'threshold': {'line': {'color': "black", 'width': 2}, 'thickness': 0.75, 'value': 20}
                    }
                ))
                fig.update_layout(height=250, margin=dict(l=20, r=20, t=50, b=20))
                gauge_div = dcc.Graph(figure=fig, config={"displayModeBar": False})

                # Insights logic
                if rate > 30:
                    insights.append(("bi-star-fill text-warning", "Excellent savings rate! You are building wealth fast."))
                elif rate < 10:
                    insights.append(("bi-exclamation-triangle text-danger", "Low savings rate. Review your expenses to increase margin."))
                
                # Compare to Average
                avg_net = ive_data["totals"]["average_monthly_net"]
                if current["net"] > avg_net * 1.2:
                    insights.append(("bi-arrow-up-circle text-success", f"This period's net is 20% higher than your average!"))

            if not insights:
                insights = [("bi-info-circle", "Stay consistent! Track items daily for better insights.")]

            insights_list = html.Div([
                html.Div([
                    html.I(className=f"bi {icon} me-3 fs-5"),
                    html.Span(text)
                ], className="d-flex align-items-center mb-3 p-3 bg-light rounded")
                for icon, text in insights
            ])

            return gauge_div, insights_list

        except Exception as e:
            return html.Div(f"Error: {str(e)}"), html.Div("Analysis failed")

    # 3. Recurring Patterns
    @app.callback(
        Output("advanced-recurring-patterns", "children"),
        [Input("url", "pathname")],
        [State("session-store", "data")],
    )
    def update_recurring(pathname, session_data):
        if pathname != "/dashboard/analytics-advanced" or not session_data:
            raise PreventUpdate

        try:
            api_client.set_token(session_data["token"])
            patterns = api_client.get("/analytics/recurring-patterns")
            
            if not patterns:
                return create_empty_state("bi-clock-history", "No Patterns Yet", "Recurring expenses will appear here after 3 months of tracking.")

            rows = []
            for p in patterns:
                rows.append(html.Tr([
                    html.Td(p["item_name"], className="fw-bold"),
                    html.Td(p["category"]),
                    html.Td(format_currency(p["average_amount"])),
                    html.Td(p["frequency"]),
                    html.Td(dbc.Badge(p["confidence"].capitalize(), color="success" if p["confidence"]=="high" else "info"))
                ]))

            return dbc.Table([
                html.Thead(html.Tr([html.Th("Item"), html.Th("Category"), html.Th("Avg Amount"), html.Th("Frequency"), html.Th("Confidence")])),
                html.Tbody(rows)
            ], hover=True, borderless=True)

        except:
            return html.Div("Failed to detect patterns")

    # 4. Anomalies
    @app.callback(
        Output("advanced-anomalies-container", "children"),
        [Input("current-period-id", "data")],
        [State("session-store", "data")],
    )
    def update_anomalies(period_id, session_data):
        if not period_id or not session_data:
            return html.Div("Select a period to check for anomalies", className="text-muted text-center py-4")

        try:
            api_client.set_token(session_data["token"])
            anomalies = api_client.get(f"/analytics/anomalies?period_id={period_id}")
            
            if not anomalies:
                return html.Div([
                    html.I(className="bi bi-shield-check text-success me-2"),
                    "No significant spending anomalies detected in this period."
                ], className="text-center py-4")

            return html.Div([
                dbc.Alert([
                    html.Div([
                        html.I(className="bi bi-exclamation-octagon-fill me-2"),
                        html.Span(a["message"], className="fw-bold")
                    ], className="mb-1"),
                    html.Div(f"{a['item_name']}: {format_currency(a['amount'])} (Avg: {format_currency(a['historical_average'])})", className="small")
                ], color="warning", className="mb-2 shadow-sm")
                for a in anomalies
            ])
        except:
            return html.Div("Anomaly detection failed")

    # 5. Export CSV
    @app.callback(
        Output("download-advanced-csv", "data"),
        Input("export-range-csv", "n_clicks"),
        [
            State("analytics-date-range", "start_date"),
            State("analytics-date-range", "end_date"),
            State("session-store", "data"),
        ],
        prevent_initial_call=True
    )
    def export_csv(n, start, end, session_data):
        if not n or not session_data:
            raise PreventUpdate
        
        try:
            api_client.set_token(session_data["token"])
            # We don't have a direct "export" endpoint yet, so we'll fetch spending by category or expenses
            # For now, let's just export the category breakdown of that range
            data = api_client.get(f"/analytics/spending-by-category?start_date={start}&end_date={end}")
            df = pd.DataFrame(data["by_category"])
            return dcc.send_data_frame(df.to_csv, "budgetflow_range_analysis.csv", index=False)
        except:
            raise PreventUpdate
