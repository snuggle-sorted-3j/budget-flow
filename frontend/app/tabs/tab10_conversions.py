import dash_bootstrap_components as dbc
from dash import html, dcc

def create_conversions_tab_layout():
    return dbc.Container(
        [
            dcc.Store(id="conv-trigger-refresh", data=0),
            dcc.Store(id="conv-loading", data=False),
            
            # Toast notifications container
            html.Div(id="conv-toast-container"),
            
            html.H2("Currency Conversions", className="mb-4"),
            html.P(
                "Track money moving between currencies (e.g., bank exchanges, ATM withdrawals, crypto).", 
                className="text-muted mb-4"
            ),
            
            # --- Section 1: Record Conversion ---
            dbc.Card(
                [
                    dbc.CardHeader(html.H4("Record New Conversion")),
                    dbc.CardBody(
                        [
                            # Alert container for form feedback
                            html.Div(id="conv-form-alert"),
                            
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            dbc.Label(
                                                ["From Currency ", html.Span("*", className="text-danger")],
                                                html_for="conv-from-currency"
                                            ),
                                            dbc.Select(
                                                id="conv-from-currency",
                                                placeholder="Select currency"
                                            ),
                                            html.Small(
                                                id="conv-from-currency-error",
                                                className="text-danger d-none"
                                            ),
                                        ],
                                        md=3,
                                    ),
                                    dbc.Col(
                                        [
                                            dbc.Label(
                                                ["From Amount ", html.Span("*", className="text-danger")],
                                                html_for="conv-from-amount"
                                            ),
                                            dbc.Input(
                                                id="conv-from-amount",
                                                type="number",
                                                placeholder="0.00",
                                                min=0,
                                                step="any"
                                            ),
                                            html.Small(
                                                id="conv-from-amount-error",
                                                className="text-danger d-none"
                                            ),
                                        ],
                                        md=3,
                                    ),
                                    dbc.Col(
                                        [
                                            dbc.Label(
                                                ["To Currency ", html.Span("*", className="text-danger")],
                                                html_for="conv-to-currency"
                                            ),
                                            dbc.Select(
                                                id="conv-to-currency",
                                                placeholder="Select currency"
                                            ),
                                            html.Small(
                                                id="conv-to-currency-error",
                                                className="text-danger d-none"
                                            ),
                                        ],
                                        md=3,
                                    ),
                                    dbc.Col(
                                        [
                                            dbc.Label(
                                                ["To Amount ", html.Span("*", className="text-danger")],
                                                html_for="conv-to-amount"
                                            ),
                                            dbc.Input(
                                                id="conv-to-amount",
                                                type="number",
                                                placeholder="0.00",
                                                min=0,
                                                step="any"
                                            ),
                                            html.Small(
                                                id="conv-to-amount-error",
                                                className="text-danger d-none"
                                            ),
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
                                            dbc.Label(
                                                ["Unit Cost (Rate) ", html.Span("*", className="text-danger")],
                                                html_for="conv-rate"
                                            ),
                                            dbc.Input(
                                                id="conv-rate",
                                                type="number",
                                                step="0.01",
                                                placeholder="0.00",
                                                min=0
                                            ),
                                            html.Small(
                                                "Rate = From / To (Cost per 1 unit of 'To')",
                                                className="text-muted mt-1 d-block"
                                            ),
                                            html.Small(
                                                id="conv-rate-error",
                                                className="text-danger d-none"
                                            ),
                                        ],
                                        md=3,
                                    ),
                                    dbc.Col(
                                        [
                                            dbc.Label(
                                                ["Conversion Date ", html.Span("*", className="text-danger")],
                                                html_for="conv-date"
                                            ),
                                            dbc.Input(
                                                id="conv-date",
                                                type="date"
                                            ),
                                            html.Small(
                                                id="conv-date-error",
                                                className="text-danger d-none"
                                            ),
                                        ],
                                        md=3,
                                    ),
                                    dbc.Col(
                                        [
                                            dbc.Label(
                                                "Source Account (Optional)",
                                                html_for="conv-account"
                                            ),
                                            dbc.Select(
                                                id="conv-account",
                                                placeholder="Select account"
                                            ),
                                        ],
                                        md=3,
                                    ),
                                    dbc.Col(
                                        [
                                            dbc.Label("Notes", html_for="conv-notes"),
                                            dbc.Input(
                                                id="conv-notes",
                                                type="text",
                                                placeholder="e.g. Bank exchange"
                                            ),
                                        ],
                                        md=3,
                                    ),
                                ],
                                className="mb-3",
                            ),
                            dbc.Button(
                                [
                                    dbc.Spinner(
                                        size="sm",
                                        spinner_class_name="me-2",
                                        id="conv-submit-spinner",
                                        spinner_style={"display": "none"}
                                    ),
                                    html.Span("Record Conversion", id="conv-submit-text")
                                ],
                                id="add-conv-btn",
                                color="primary",
                                disabled=False
                            ),
                        ]
                    ),
                ],
                className="mb-5 shadow-sm",
            ),
            
            # --- Section 2: Conversions Table ---
            html.Div(
                [
                    html.H4("History for Selected Period", className="mb-3"),
                    dbc.Spinner(
                        html.Div(id="conversions-table-container"),
                        color="primary",
                        type="border",
                        fullscreen=False,
                    ),
                ],
                className="mb-5"
            ),
            
            html.Hr(className="my-5"),
            
            # --- Section 3: Rate History Trends ---
            dbc.Card(
                [
                    dbc.CardHeader(html.H4("Exchange Rate Trends")),
                    dbc.CardBody(
                        [
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Pair Selection", html_for="rate-pair-select"),
                                    dbc.Select(
                                        id="rate-pair-select",
                                        options=[],
                                        placeholder="Select pair to view chart",
                                        className="mb-3"
                                    )
                                ], md=4)
                            ]),
                            dbc.Spinner(
                                dcc.Graph(id="rate-history-chart"),
                                color="primary"
                            )
                        ]
                    )
                ],
                className="mb-5 shadow-sm"
            ),
            
            # Confirmation modal for deletions
            dbc.Modal(
                [
                    dbc.ModalHeader(
                        dbc.ModalTitle(
                            [
                                html.I(className="bi bi-exclamation-triangle-fill text-warning me-2"),
                                "Confirm Deletion"
                            ]
                        )
                    ),
                    dbc.ModalBody(
                        [
                            html.P("Are you sure you want to delete this conversion?"),
                            html.P(
                                [
                                    html.I(className="bi bi-info-circle me-2"),
                                    html.Strong("This action cannot be undone.")
                                ],
                                className="text-danger mb-0"
                            )
                        ]
                    ),
                    dbc.ModalFooter(
                        [
                            dbc.Button(
                                "Cancel",
                                id="conv-delete-cancel",
                                className="me-2",
                                color="secondary"
                            ),
                            dbc.Button(
                                "Delete",
                                id="conv-delete-confirm",
                                color="danger"
                            )
                        ]
                    )
                ],
                id="conv-delete-modal",
                is_open=False,
                centered=True
            ),
            
            # Store for pending deletion
            dcc.Store(id="conv-pending-delete-id"),
        ],
        fluid=True,
        className="py-4",
    )
