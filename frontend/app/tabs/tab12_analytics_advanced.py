import dash_bootstrap_components as dbc
from dash import html, dcc
from datetime import date

def create_advanced_analytics_layout():
    """Create the Advanced Analytics tab layout."""
    return dbc.Container(
        [
            dbc.Row(
                [
                    dbc.Col(html.H2("Advanced Analytics", className="fw-bold mb-0"), md=8),
                    dbc.Col(
                        dbc.Button(
                            [html.I(className="bi bi-download me-2"), "Download Full Report"],
                            id="advanced-report-btn",
                            color="success",
                            size="sm",
                        ),
                        md=4,
                        className="d-flex justify-content-end align-items-center",
                    ),
                ],
                className="mb-4 align-items-center",
            ),

            # Section 1: Custom Date Range Analysis
            dbc.Card(
                [
                    dbc.CardHeader(html.H5("Custom Date Range Analysis", className="mb-0 fw-bold")),
                    dbc.CardBody(
                        [
                            dbc.Row(
                                [
                                    dbc.Col(
                                        dcc.DatePickerRange(
                                            id="analytics-date-range",
                                            min_date_allowed=date(2020, 1, 1),
                                            max_date_allowed=date(2030, 12, 31),
                                            initial_visible_month=date.today(),
                                            className="border-0",
                                        ),
                                        md=6,
                                    ),
                                    dbc.Col(
                                        dbc.Button("Analyze Range", id="analyze-range-btn", color="primary"),
                                        md=3,
                                    ),
                                    dbc.Col(
                                        dbc.Button("Export CSV", id="export-range-csv", color="secondary", outline=True),
                                        md=3,
                                        className="text-end",
                                    ),
                                ],
                                className="mb-4 align-items-center",
                            ),
                            html.Div(id="advanced-range-results"),
                        ]
                    ),
                ],
                className="mb-4 shadow-sm border-0",
            ),

            # Section 2 & 6: Savings Rate & Insights
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            [
                                dbc.CardHeader(html.H5("Savings Rate Analysis", className="mb-0 fw-bold")),
                                dbc.CardBody(
                                    dcc.Loading(
                                        children=html.Div(id="advanced-savings-rate-chart"),
                                        type="circle",
                                    )
                                ),
                            ],
                            className="shadow-sm border-0 h-100",
                        ),
                        md=6,
                    ),
                    dbc.Col(
                        dbc.Card(
                            [
                                dbc.CardHeader(html.H5("Automated Insights", className="mb-0 fw-bold")),
                                dbc.CardBody(
                                    dcc.Loading(
                                        children=html.Div(id="advanced-insights-container"),
                                        type="circle",
                                    )
                                ),
                            ],
                            className="shadow-sm border-0 h-100",
                        ),
                        md=6,
                    ),
                ],
                className="mb-4",
            ),

            # Section 4: Recurring Patterns
            dbc.Card(
                [
                    dbc.CardHeader(html.H5("Recurring Patterns Detection", className="mb-0 fw-bold")),
                    dbc.CardBody(
                        dcc.Loading(
                            children=html.Div(id="advanced-recurring-patterns"),
                            type="circle",
                        )
                    ),
                ],
                className="mb-4 shadow-sm border-0",
            ),

            # Section 2: Category Deep Dive (Table)
            dbc.Card(
                [
                    dbc.CardHeader(html.H5("Category Performance Deep Dive", className="mb-0 fw-bold")),
                    dbc.CardBody(
                        dcc.Loading(
                            children=html.Div(id="advanced-category-deep-dive"),
                            type="circle",
                        ),
                        className="p-0",
                    ),
                ],
                className="mb-4 shadow-sm border-0",
            ),

            # Section 5: Anomaly Detection
            dbc.Card(
                [
                    dbc.CardHeader(html.H5("Spending Anomalies & Alerts", className="mb-0 fw-bold")),
                    dbc.CardBody(
                        dcc.Loading(
                            children=html.Div(id="advanced-anomalies-container"),
                            type="circle",
                        )
                    ),
                ],
                className="mb-5 shadow-sm border-0",
            ),
            
            # Hidden download component
            dcc.Download(id="download-advanced-csv"),
        ],
        fluid=True,
        className="py-4",
    )

