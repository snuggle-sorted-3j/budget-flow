import dash_bootstrap_components as dbc
from dash import html, dcc

def create_dashboard_home_layout():
    """Create the comprehensive Analytics Dashboard layout."""
    return dbc.Container(
        [
            # Header with Period Selector (Handled by Global Header but we can add title)
            dbc.Row(
                [
                    dbc.Col(html.H2("Analytics Dashboard", className="fw-bold mb-0"), md=8),
                    dbc.Col(
                        dbc.Button(
                            [html.I(className="bi bi-arrow-clockwise me-2"), "Refresh Data"],
                            id="analytics-refresh-btn",
                            color="primary",
                            outline=True,
                            size="sm",
                        ),
                        md=4,
                        className="d-flex justify-content-end align-items-center",
                    ),
                ],
                className="mb-4 align-items-center",
            ),

            # Section 1: Quick Stats Bar
            html.Div(id="analytics-quick-stats", className="mb-4"),

            # Section 2: Income vs Expenses Trend
            dbc.Card(
                [
                    dbc.CardHeader(html.H5("Income vs Expenses - Last 6 Periods", className="mb-0 fw-bold")),
                    dbc.CardBody(
                        dcc.Loading(
                            id="loading-income-expenses",
                            children=html.Div(id="analytics-income-expenses-chart"),
                            type="circle",
                        )
                    ),
                ],
                className="mb-4 shadow-sm border-0",
            ),

            # Section 3: Two-column layout (Pie Chart & Top Expenses)
            dbc.Row(
                [
                    # Left: Spending by Category
                    dbc.Col(
                        dbc.Card(
                            [
                                dbc.CardHeader(html.H5("Spending Breakdown", className="mb-0 fw-bold")),
                                dbc.CardBody(
                                    dcc.Loading(
                                        id="loading-spending-pie",
                                        children=html.Div(id="analytics-spending-pie-chart"),
                                        type="circle",
                                    )
                                ),
                            ],
                            className="shadow-sm border-0 h-100",
                        ),
                        md=6,
                        className="mb-4",
                    ),
                    # Right: Top Expenses Table
                    dbc.Col(
                        dbc.Card(
                            [
                                dbc.CardHeader(html.H5("Largest Expenses This Period", className="mb-0 fw-bold")),
                                dbc.CardBody(
                                    dcc.Loading(
                                        id="loading-top-expenses",
                                        children=html.Div(id="analytics-top-expenses-table"),
                                        type="circle",
                                    ),
                                    className="p-0", # Clean table look
                                ),
                            ],
                            className="shadow-sm border-0 h-100",
                        ),
                        md=6,
                        className="mb-4",
                    ),
                ],
                className="mb-2",
            ),

            # Section 4: Net Worth Trend
            dbc.Card(
                [
                    dbc.CardHeader(html.H5("Net Worth Over Time", className="mb-0 fw-bold")),
                    dbc.CardBody(
                        dcc.Loading(
                            id="loading-net-worth",
                            children=html.Div(id="analytics-net-worth-chart"),
                            type="circle",
                        )
                    ),
                ],
                className="mb-4 shadow-sm border-0",
            ),

            # Section 5: Category Trends
            dbc.Card(
                [
                    dbc.CardHeader(
                        dbc.Row(
                            [
                                dbc.Col(html.H5("Category Spending Trend", className="mb-0 fw-bold"), md=6),
                                dbc.Col(
                                    dcc.Dropdown(
                                        id="analytics-category-dropdown",
                                        placeholder="Select category...",
                                        className="text-dark",
                                    ),
                                    md=6,
                                ),
                            ],
                            className="align-items-center",
                        )
                    ),
                    dbc.CardBody(
                        dcc.Loading(
                            id="loading-category-trend",
                            children=html.Div(id="analytics-category-trend-chart"),
                            type="circle",
                        )
                    ),
                ],
                className="mb-4 shadow-sm border-0",
            ),

            # Section 6: Period Comparison
            dbc.Card(
                [
                    dbc.CardHeader(
                        dbc.Row(
                            [
                                dbc.Col(html.H5("Period Comparison", className="mb-0 fw-bold"), md=4),
                                dbc.Col(
                                    dcc.Dropdown(
                                        id="compare-period-1",
                                        placeholder="First Period",
                                        className="text-dark",
                                    ),
                                    md=4,
                                ),
                                dbc.Col(
                                    dcc.Dropdown(
                                        id="compare-period-2",
                                        placeholder="Second Period",
                                        className="text-dark",
                                    ),
                                    md=4,
                                ),
                            ],
                            className="align-items-center",
                        )
                    ),
                    dbc.CardBody(
                        dcc.Loading(
                            id="loading-comparison",
                            children=html.Div(id="analytics-comparison-container"),
                            type="circle",
                        )
                    ),
                ],
                className="mb-5 shadow-sm border-0",
            ),
            
            # Stores for caching (optional)
            dcc.Store(id="analytics-data-cache", storage_type="memory"),
            dcc.Store(id="analytics-trigger-refresh", data=0),
        ],
        fluid=True,
        className="py-4",
    )
