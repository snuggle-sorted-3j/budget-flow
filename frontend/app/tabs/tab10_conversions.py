import dash_bootstrap_components as dbc
from dash import html, dcc
import plotly.graph_objects as go

def create_conversions_tab_layout():
    return dbc.Container(
        [
            dcc.Store(id="conv-trigger-refresh", data=0),
            
            html.H2("Currency Conversions", className="mb-4"),
            html.P("Track money moving between currencies (e.g., bank exchanges, ATM withdrawals, crypto).", className="text-muted mb-4"),
            
            # --- Section 1: Record Conversion ---
            dbc.Card(
                [
                    dbc.CardHeader(html.H4("Record New Conversion")),
                    dbc.CardBody(
                        [
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            dbc.Label(["From Currency ", html.Span("*", className="text-danger")]),
                                            dbc.Select(id="conv-from-currency"),
                                        ],
                                        md=3,
                                    ),
                                    dbc.Col(
                                        [
                                            dbc.Label(["From Amount ", html.Span("*", className="text-danger")]),
                                            dbc.Input(id="conv-from-amount", type="number", placeholder="0.00"),
                                        ],
                                        md=3,
                                    ),
                                    dbc.Col(
                                        [
                                            dbc.Label(["To Currency ", html.Span("*", className="text-danger")]),
                                            dbc.Select(id="conv-to-currency"),
                                        ],
                                        md=3,
                                    ),
                                    dbc.Col(
                                        [
                                            dbc.Label(["To Amount ", html.Span("*", className="text-danger")]),
                                            dbc.Input(id="conv-to-amount", type="number", placeholder="0.00"),
                                        ],
                                        md=3,
                                    ),
                                ],
                                className="mb-3",
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            dbc.Label(["Unit Cost (Rate) ", html.Span("*", className="text-danger")]),
                                            dbc.Input(id="conv-rate", type="number", step="0.01", placeholder="0.00"),
                                            html.Small("Rate = From / To (Cost per 1 unit of 'To')", className="text-muted mt-1 d-block"),
                                        ],
                                        md=3,
                                    ),
                                    dbc.Col(
                                        [
                                            dbc.Label(["Conversion Date ", html.Span("*", className="text-danger")]),
                                            dbc.Input(id="conv-date", type="date"),
                                        ],
                                        md=3,
                                    ),
                                    dbc.Col(
                                        [
                                            dbc.Label("Source Account (Optional)"),
                                            dbc.Select(id="conv-account"),
                                        ],
                                        md=3,
                                    ),
                                    dbc.Col(
                                        [
                                            dbc.Label("Notes"),
                                            dbc.Input(id="conv-notes", type="text", placeholder="e.g. Bank exchange"),
                                        ],
                                        md=3,
                                    ),
                                ],
                                className="mb-3",
                            ),
                            dbc.Button("Record Conversion", id="add-conv-btn", color="primary"),
                            dbc.Collapse(
                                dbc.Alert(id="conv-message", color="success", className="mt-3"),
                                id="conv-message-collapse",
                                is_open=False,
                            ),
                        ]
                    ),
                ],
                className="mb-5 shadow-sm",
            ),
            
            # --- Section 2: Conversions Table ---
            html.H4("History for Selected Period", className="mb-3"),
            html.Div(id="conversions-table-container"),
            
            html.Hr(className="my-5"),
            
            # --- Section 3: Rate History Trends ---
            dbc.Card(
                [
                    dbc.CardHeader(html.H4("Exchange Rate Trends")),
                    dbc.CardBody(
                        [
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Pair Selection"),
                                    dbc.Select(
                                        id="rate-pair-select",
                                        options=[], 
                                        placeholder="Select pair to view chart",
                                        className="mb-3"
                                    )
                                ], md=4)
                            ]),
                            dcc.Graph(id="rate-history-chart")
                        ]
                    )
                ],
                className="mb-5 shadow-sm"
            )
        ],
        fluid=True,
        className="py-4",
    )
