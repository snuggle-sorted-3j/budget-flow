import dash
from dash import Input, Output, State, html, dcc, dash_table
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, date
import pandas as pd

from utils.api_client import APIClient
from utils.ui_helpers import format_currency, get_amount_class, create_empty_state

# Brand Colors
COLOR_INCOME = "#10b981"
COLOR_EXPENSE = "#ef4444"
COLOR_NEUTRAL = "#3b82f6"
COLOR_BG = "#f9fafb"

def register_analytics_callbacks(app):
    """Register all callbacks for the analytics dashboard."""
    api_client = APIClient()

    # 1. Quick Stats Callback
    @app.callback(
        Output("analytics-quick-stats", "children"),
        [
            Input("current-period-id", "data"),
            Input("analytics-trigger-refresh", "data"),
            Input("url", "pathname"),
        ],
        [State("session-store", "data")],
    )
    def update_quick_stats(period_id, refresh_trigger, pathname, session_data):
        if not pathname or (pathname != "/dashboard" and pathname != "/dashboard/"):
            raise PreventUpdate
        
        if not session_data or "token" not in session_data:
            return html.Div("Please log in")

        try:
            api_client.set_token(session_data["token"])
            
            # Fetch net worth trend (last 2 periods for comparison)
            nw_data = api_client.get("/analytics/net-worth-trend?num_periods=2")
            
            # Fetch spending by category for the current period (for largest category)
            spending_data = api_client.get(f"/analytics/spending-by-category?period_id={period_id}") if period_id else {}
            
            # Fetch income vs expenses for current period summary
            # We can use the reconciliation endpoint or the new analytics one
            # Using analytics/income-vs-expenses?num_periods=1
            ive_data = api_client.get("/analytics/income-vs-expenses?num_periods=1")
            
            # Process Net Worth Stat
            total_balance = 0.0
            nw_diff_str = "No history"
            nw_diff_class = "text-muted"
            
            if nw_data and "periods" in nw_data and len(nw_data["periods"]) > 0:
                current_nw = nw_data["periods"][-1]
                total_balance = current_nw["total_balance"]
                if len(nw_data["periods"]) > 1:
                    prev_nw = nw_data["periods"][-2]
                    diff = current_nw["total_balance"] - prev_nw["total_balance"]
                    nw_diff_str = f"{'+' if diff >= 0 else ''}{format_currency(diff)}"
                    nw_diff_class = "text-success" if diff >= 0 else "text-danger"

            # Process This Period Net
            this_period_net = 0.0
            if ive_data and "periods" in ive_data and len(ive_data["periods"]) > 0:
                this_period_net = ive_data["periods"][-1]["net"]
            
            # Process Avg Monthly Net
            avg_net = 0.0
            if ive_data and "totals" in ive_data:
                # We might want to fetch more periods for a better average
                ive_6_data = api_client.get("/analytics/income-vs-expenses?num_periods=6")
                if ive_6_data and "totals" in ive_6_data:
                    avg_net = ive_6_data["totals"]["average_monthly_net"]

            # Process Largest Expense Category
            top_category_name = "N/A"
            top_category_amt = 0.0
            if spending_data and "by_category" in spending_data and len(spending_data["by_category"]) > 0:
                top_cat = sorted(spending_data["by_category"], key=lambda x: x["total"], reverse=True)[0]
                top_category_name = top_cat["category_name"]
                top_category_amt = top_cat["total"]

            # Create Cards
            def create_stat_card(title, value, subtitle=None, subtitle_class="", icon="bi-graph-up"):
                return dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.Div(
                                    [
                                        html.Small(title, className="text-secondary text-uppercase fw-bold small"),
                                        html.I(className=f"bi {icon} text-primary opacity-50"),
                                    ],
                                    className="d-flex justify-content-between align-items-center mb-2",
                                ),
                                html.H3(value, className="fw-bold mb-1"),
                                html.Div(subtitle, className=f"small {subtitle_class}") if subtitle else None,
                            ]
                        ),
                        className="border-0 shadow-sm h-100",
                    ),
                    md=3,
                    className="mb-3",
                )

            return dbc.Row(
                [
                    create_stat_card("Total Balance", format_currency(total_balance), nw_diff_str, nw_diff_class, "bi-wallet2"),
                    create_stat_card("Period Net", format_currency(this_period_net), "This monitoring period", "text-success" if this_period_net >= 0 else "text-danger", "bi-cash-coin"),
                    create_stat_card("Avg Monthly Net", format_currency(avg_net), "Last 6 periods", icon="bi-calculator"),
                    create_stat_card("Top Category", top_category_name, f"{format_currency(top_category_amt)} this period", icon="bi-tag"),
                ]
            )

        except Exception as e:
            return dbc.Alert(f"Error loading quick stats: {str(e)}", color="danger")

    # 2. Income vs Expenses Chart Callback
    @app.callback(
        Output("analytics-income-expenses-chart", "children"),
        [
            Input("analytics-trigger-refresh", "data"),
            Input("url", "pathname"),
        ],
        [State("session-store", "data")],
    )
    def update_ive_chart(refresh_trigger, pathname, session_data):
        if not pathname or (pathname != "/dashboard" and pathname != "/dashboard/"):
            raise PreventUpdate
        
        if not session_data or "token" not in session_data:
            return None

        try:
            api_client.set_token(session_data["token"])
            data = api_client.get("/analytics/income-vs-expenses?num_periods=6")
            
            if not data or "periods" not in data or not data["periods"]:
                return create_empty_state("bi-bar-chart", "No data", "Add income and expenses across periods to see trends.")

            periods = data["periods"]
            names = [p["period_name"] for p in periods]
            income = [p["income"] for p in periods]
            expenses = [p["expenses"] for p in periods]
            net = [p["net"] for p in periods]

            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                x=names, y=income, name="Income",
                marker_color=COLOR_INCOME,
                hovertemplate="%{y:,.2f}"
            ))
            
            fig.add_trace(go.Bar(
                x=names, y=expenses, name="Expenses",
                marker_color=COLOR_EXPENSE,
                hovertemplate="%{y:,.2f}"
            ))
            
            fig.add_trace(go.Scatter(
                x=names, y=net, name="Net",
                mode="lines+markers",
                line=dict(color=COLOR_NEUTRAL, width=3),
                marker=dict(size=8),
                hovertemplate="%{y:,.2f}"
            ))

            fig.update_layout(
                barmode="group",
                margin=dict(l=20, r=20, t=10, b=20),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                xaxis=dict(showgrid=False),
                yaxis=dict(gridcolor="#f0f0f0"),
                hovermode="x unified"
            )

            return dcc.Graph(figure=fig, config={"displayModeBar": False})

        except Exception as e:
            return html.Div(f"Error: {str(e)}", className="text-danger")

    # 3. Spending Pie Chart Callback
    @app.callback(
        Output("analytics-spending-pie-chart", "children"),
        [
            Input("current-period-id", "data"),
            Input("analytics-trigger-refresh", "data"),
            Input("url", "pathname"),
        ],
        [State("session-store", "data")],
    )
    def update_spending_pie(period_id, refresh_trigger, pathname, session_data):
        if not pathname or (pathname != "/dashboard" and pathname != "/dashboard/"):
            raise PreventUpdate
        
        if not session_data or "token" not in session_data:
            return None

        if not period_id:
            return create_empty_state("bi-pie-chart", "Select Period", "Please select a period to see spending breakdown.")

        try:
            api_client.set_token(session_data["token"])
            data = api_client.get(f"/analytics/spending-by-category?period_id={period_id}")
            
            if not data or "by_category" not in data or not data["by_category"]:
                return create_empty_state("bi-pie-chart", "No Spending", "No expenses recorded in this period.")

            cats = sorted(data["by_category"], key=lambda x: x["total"], reverse=True)
            
            # Group into top 8 + Other
            if len(cats) > 8:
                top_cats = cats[:8]
                other_sum = sum(c["total"] for c in cats[8:])
                top_cats.append({"category_name": "Other", "total": other_sum})
                cats = top_cats

            fig = px.pie(
                cats, 
                values="total", 
                names="category_name",
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Safe
            )
            
            fig.update_traces(
                textinfo="percent+label",
                hovertemplate="%{label}: %{value:,.2f} (%{percent})"
            )
            
            fig.update_layout(
                margin=dict(l=20, r=20, t=20, b=20),
                paper_bgcolor="rgba(0,0,0,0)",
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
            )

            return dcc.Graph(figure=fig, config={"displayModeBar": False})

        except Exception as e:
            return html.Div(f"Error: {str(e)}", className="text-danger")

    # 4. Top Expenses Table Callback
    @app.callback(
        Output("analytics-top-expenses-table", "children"),
        [
            Input("current-period-id", "data"),
            Input("analytics-trigger-refresh", "data"),
            Input("url", "pathname"),
        ],
        [State("session-store", "data")],
    )
    def update_top_expenses(period_id, refresh_trigger, pathname, session_data):
        if not pathname or (pathname != "/dashboard" and pathname != "/dashboard/"):
            raise PreventUpdate
        
        if not session_data or "token" not in session_data:
            return None

        if not period_id:
            return html.Div("Please select a period", className="text-muted text-center py-5")

        try:
            api_client.set_token(session_data["token"])
            expenses = api_client.get(f"/analytics/top-expenses?period_id={period_id}&limit=10")
            
            if not expenses:
                return html.Div("No expenses found for this period", className="text-muted text-center py-5")

            # Transform for DataTable
            data = [
                {
                    "item": e["item_name"],
                    "category": e["category"],
                    "amount": format_currency(e["amount"]),
                    "date": e["date"]
                }
                for e in expenses
            ]

            return dash_table.DataTable(
                columns=[
                    {"name": "Item", "id": "item"},
                    {"name": "Category", "id": "category"},
                    {"name": "Amount", "id": "amount"},
                ],
                data=data,
                style_cell={"textAlign": "left", "padding": "12px", "fontSize": "14px", "fontFamily": "Inter, sans-serif"},
                style_header={"backgroundColor": "#f8f9fa", "fontWeight": "bold", "color": "#6c757d"},
                style_data_conditional=[{"if": {"row_index": "odd"}, "backgroundColor": "#fcfcfc"}],
                style_as_list_view=True,
            )

        except Exception as e:
            return html.Div(f"Error: {str(e)}", className="text-danger")

    # 5. Net Worth Trend Callback
    @app.callback(
        Output("analytics-net-worth-chart", "children"),
        [
            Input("analytics-trigger-refresh", "data"),
            Input("url", "pathname"),
        ],
        [State("session-store", "data")],
    )
    def update_net_worth_chart(refresh_trigger, pathname, session_data):
        if not pathname or (pathname != "/dashboard" and pathname != "/dashboard/"):
            raise PreventUpdate
        
        if not session_data or "token" not in session_data:
            return None

        try:
            api_client.set_token(session_data["token"])
            data = api_client.get("/analytics/net-worth-trend?num_periods=12")
            
            if not data or "periods" not in data or len(data["periods"]) < 2:
                return create_empty_state("bi-graph-up", "Insufficient Data", "Complete a few monitoring periods and finalize them to see net worth trends.")

            periods = data["periods"]
            dates = [p["snapshot_date"] for p in periods]
            balances = [p["total_balance"] for p in periods]

            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=dates, y=balances,
                fill='tozeroy',
                mode='lines+markers',
                line=dict(color=COLOR_NEUTRAL, width=3),
                fillcolor='rgba(59, 130, 246, 0.1)',
                marker=dict(size=8, color=COLOR_NEUTRAL, line=dict(color='white', width=2)),
                hovertemplate="Date: %{x}<br>Balance: %{y:,.2f}"
            ))

            fig.update_layout(
                margin=dict(l=20, r=20, t=10, b=20),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(showgrid=False),
                yaxis=dict(gridcolor="#f0f0f0")
            )

            return dcc.Graph(figure=fig, config={"displayModeBar": False})

        except Exception as e:
            return html.Div(f"Error: {str(e)}", className="text-danger text-center py-5")

    # 6. Category Trends Callbacks
    @app.callback(
        Output("analytics-category-dropdown", "options"),
        [Input("url", "pathname"), Input("session-store", "data")],
    )
    def load_category_options(pathname, session_data):
        if not pathname or (pathname != "/dashboard" and pathname != "/dashboard/"):
            raise PreventUpdate
        
        if not session_data or "token" not in session_data:
            return []

        try:
            api_client.set_token(session_data["token"])
            categories = api_client.get("/expense-categories/")
            # Only active categories
            options = [{"label": c["category_name"], "value": c["id"]} for c in categories if c.get("is_active")]
            return options
        except:
            return []

    @app.callback(
        Output("analytics-category-trend-chart", "children"),
        [
            Input("analytics-category-dropdown", "value"),
            Input("analytics-trigger-refresh", "data"),
        ],
        [State("session-store", "data")],
    )
    def update_category_trend(cat_id, refresh_trigger, session_data):
        if not cat_id or not session_data:
            return html.Div("Select a category above to see spending trends", className="text-muted text-center py-5")

        try:
            api_client.set_token(session_data["token"])
            data = api_client.get(f"/analytics/category-trends/{cat_id}?num_periods=6")
            
            if not data or "periods" not in data or not data["periods"]:
                return html.Div("No history for this category", className="text-muted text-center py-5")

            periods = data["periods"]
            names = [p["period_name"] for p in periods]
            amounts = [p["amount"] for p in periods]
            avg = data["average"]
            trend = data["trend"]

            trend_icons = {"increasing": "↗️", "decreasing": "↘️", "stable": "➡️"}
            trend_icon = trend_icons.get(trend, "")

            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=names, y=amounts,
                mode='lines+markers',
                name="Spending",
                line=dict(color=COLOR_EXPENSE, width=3),
                marker=dict(size=10),
                hovertemplate="%{y:,.2f}"
            ))
            
            # Average Line
            fig.add_hline(y=avg, line_dash="dash", line_color="#666", annotation_text=f"Avg: {avg:,.2f}")

            fig.update_layout(
                margin=dict(l=20, r=20, t=10, b=20),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(showgrid=False),
                yaxis=dict(gridcolor="#f0f0f0")
            )

            return html.Div([
                html.Div(f"Trend: {trend.capitalize()} {trend_icon}", className="fw-bold mb-2 text-center text-secondary"),
                dcc.Graph(figure=fig, config={"displayModeBar": False})
            ])

        except Exception as e:
            return html.Div(f"Error: {str(e)}", className="text-danger")

    # 7. Period Comparison Callbacks
    @app.callback(
        [Output("compare-period-1", "options"), Output("compare-period-2", "options")],
        [Input("url", "pathname"), Input("session-store", "data")],
    )
    def load_compare_period_options(pathname, session_data):
        if not pathname or (pathname != "/dashboard" and pathname != "/dashboard/"):
            raise PreventUpdate
        
        if not session_data or "token" not in session_data:
            return [], []

        try:
            api_client.set_token(session_data["token"])
            periods = api_client.get("/periods/")
            options = [{"label": p["period_name"], "value": p["id"]} for p in periods]
            return options, options
        except:
            return [], []

    @app.callback(
        Output("analytics-comparison-container", "children"),
        [
            Input("compare-period-1", "value"),
            Input("compare-period-2", "value"),
        ],
        [State("session-store", "data")],
    )
    def update_comparison(p1_id, p2_id, session_data):
        if not p1_id or not p2_id:
            return html.Div("Select two periods to compare directly", className="text-muted text-center py-5")

        try:
            api_client.set_token(session_data["token"])
            data = api_client.get(f"/analytics/compare-periods?period_id_1={p1_id}&period_id_2={p2_id}")
            
            if not data or "differences" not in data:
                return html.Div("Comparison data unavailable", className="text-muted text-center py-5")

            diffs = data["differences"]
            p1 = data["period_1"]
            p2 = data["period_2"]

            rows = [
                ("Total Income", p1["income"], p2["income"], diffs["income_diff"], True),
                ("Total Expenses", p1["expenses"], p2["expenses"], diffs["expenses_diff"], False),
                ("Net Result", p1["net"], p2["net"], diffs["net_diff"], True),
            ]

            table_rows = []
            for metric, v1, v2, diff, higher_is_better in rows:
                diff_class = "text-success" if (diff >= 0) == higher_is_better else "text-danger"
                if diff == 0: diff_class = "text-muted"
                
                table_rows.append(html.Tr([
                    html.Td(metric, className="fw-bold"),
                    html.Td(format_currency(v1)),
                    html.Td(format_currency(v2)),
                    html.Td(format_currency(diff, show_sign=True), className=f"fw-bold {diff_class}")
                ]))

            # Top 5 Category changes
            cat_changes = sorted(data["category_changes"], key=lambda x: abs(x["diff"]), reverse=True)[:5]
            if cat_changes:
                table_rows.append(html.Tr([html.Th("Category breakdown", colSpan=4, className="bg-light")], className="table-secondary"))
                for c in cat_changes:
                    # For expenses, lower diff is better
                    diff_class = "text-success" if c["diff"] <= 0 else "text-danger"
                    table_rows.append(html.Tr([
                        html.Td(c["category"]),
                        html.Td(format_currency(c["period_1"])),
                        html.Td(format_currency(c["period_2"])),
                        html.Td(format_currency(c["diff"], show_sign=True), className=diff_class)
                    ]))

            return dbc.Table(
                [
                    html.Thead(html.Tr([html.Th("Metric"), html.Th("Period 1"), html.Th("Period 2"), html.Th("Difference")])),
                    html.Tbody(table_rows)
                ],
                bordered=False,
                hover=True,
                responsive=True,
                className="mb-0 align-middle"
            )

        except Exception as e:
            return html.Div(f"Error: {str(e)}", className="text-danger")

    # 8. Refresh Toggle Callback
    @app.callback(
        Output("analytics-trigger-refresh", "data"),
        [Input("analytics-refresh-btn", "n_clicks")],
        [State("analytics-trigger-refresh", "data")],
        prevent_initial_call=True
    )
    def trigger_refresh(n, current):
        return (current or 0) + 1
