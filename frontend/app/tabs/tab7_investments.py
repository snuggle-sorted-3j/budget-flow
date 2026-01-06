"""Enhanced Investments tab with comprehensive error handling and UX improvements."""
import dash_bootstrap_components as dbc
from dash import dcc, html


def create_investments_tab_layout():
    """Create the layout for the Investments tab with enhanced UX."""
    
    return dbc.Container(
        [
            # Toast notifications container
            html.Div(id="inv-toast-container"),
            
            # Stores for pending deletions
            dcc.Store(id="inv-account-pending-delete-id"),
            dcc.Store(id="inv-category-pending-delete-id"),
            dcc.Store(id="inv-transfer-pending-delete-id"),
            
            html.H2("Global Investment Tracking", className="mb-4"),
            
            # --- Section 1: Investment Accounts ---
            dbc.Card(
                [
                    dbc.CardHeader(
                        html.Div(
                            [
                                html.H4("1. Investment Accounts", className="mb-0"),
                                html.Small("Manage brokerage accounts, crypto exchanges, or physical storage", className="text-muted")
                            ]
                        )
                    ),
                    dbc.CardBody(
                        [
                            # Alert container for form feedback
                            html.Div(id="inv-account-form-alert"),
                            
                            dbc.Form(
                                [
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                [
                                                    dbc.Label(
                                                        ["Account Name ", html.Span("*", className="text-danger")],
                                                        html_for="inv-account-name"
                                                    ),
                                                    dbc.Input(
                                                        id="inv-account-name",
                                                        placeholder="e.g. IBKR",
                                                        type="text",
                                                    ),
                                                    html.Small(
                                                        id="inv-account-name-error",
                                                        className="text-danger d-none"
                                                    ),
                                                ],
                                                md=3,
                                            ),
                                            dbc.Col(
                                                [
                                                    dbc.Label(
                                                        ["Type ", html.Span("*", className="text-danger")],
                                                        html_for="inv-account-type"
                                                    ),
                                                    dbc.Select(
                                                        id="inv-account-type",
                                                        options=[
                                                            {"label": "Brokerage", "value": "BROKERAGE"},
                                                            {"label": "Crypto Exchange", "value": "CRYPTO_EXCHANGE"},
                                                            {"label": "Physical Wallet/Safe", "value": "PHYSICAL"},
                                                        ],
                                                        placeholder="Select type...",
                                                    ),
                                                ],
                                                md=3,
                                            ),
                                            dbc.Col(
                                                [
                                                    dbc.Label("Notes (Optional)", html_for="inv-account-notes"),
                                                    dbc.Input(
                                                        id="inv-account-notes",
                                                        placeholder="Additional details",
                                                        type="text",
                                                    ),
                                                ],
                                                md=4,
                                            ),
                                            dbc.Col(
                                                [
                                                    dbc.Label(html.Br()),  # Spacer
                                                    dbc.Button(
                                                        [
                                                            dbc.Spinner(
                                                                size="sm",
                                                                spinner_class_name="me-2",
                                                                id="inv-account-submit-spinner",
                                                                spinner_style={"display": "none"}
                                                            ),
                                                            html.Span("Add Account")
                                                        ],
                                                        id="add-inv-account-btn",
                                                        color="primary",
                                                        className="w-100",
                                                        disabled=False
                                                    ),
                                                ],
                                                md=2,
                                            ),
                                        ],
                                        className="g-2 mb-4 align-items-end",
                                    ),
                                ]
                            ),
                            dbc.Spinner(
                                html.Div(id="inv-accounts-table-container"),
                                color="primary",
                                type="border"
                            ),
                        ]
                    ),
                ],
                className="mb-5 shadow-sm",
            ),
            
            # --- Section 2: Investment Categories (Holdings) ---
            dbc.Card(
                [
                    dbc.CardHeader(
                        html.Div(
                            [
                                html.H4("2. Investment Categories", className="mb-0"),
                                html.Small("Define what you are investing in (e.g. 'S&P 500 ETF', 'Bitcoin')", className="text-muted")
                            ]
                        )
                    ),
                    dbc.CardBody(
                        [
                            # Alert container for form feedback
                            html.Div(id="inv-category-form-alert"),
                            
                            dbc.Form(
                                [
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                [
                                                    dbc.Label(
                                                        ["Category Name ", html.Span("*", className="text-danger")],
                                                        html_for="inv-category-name"
                                                    ),
                                                    dbc.Input(
                                                        id="inv-category-name",
                                                        placeholder="e.g. Bitcoin",
                                                        type="text",
                                                    ),
                                                    html.Small(
                                                        id="inv-category-name-error",
                                                        className="text-danger d-none"
                                                    ),
                                                ],
                                                md=3,
                                            ),
                                            dbc.Col(
                                                [
                                                    dbc.Label(
                                                        ["Account ", html.Span("*", className="text-danger")],
                                                        html_for="inv-category-account-select"
                                                    ),
                                                    dcc.Dropdown(
                                                        id="inv-category-account-select",
                                                        placeholder="Select account...",
                                                        className="dash-bootstrap",
                                                    ),
                                                    html.Small(
                                                        id="inv-category-account-error",
                                                        className="text-danger d-none"
                                                    ),
                                                ],
                                                md=3,
                                            ),
                                            dbc.Col(
                                                [
                                                    dbc.Label("Opening Balance", html_for="inv-opening-balance"),
                                                    dbc.Input(
                                                        id="inv-opening-balance",
                                                        placeholder="0.00",
                                                        type="number",
                                                        step="0.01",
                                                        min=0
                                                    ),
                                                ],
                                                md=2,
                                            ),
                                            dbc.Col(
                                                [
                                                    dbc.Label("Currency", html_for="inv-opening-currency"),
                                                    dcc.Dropdown(
                                                        id="inv-opening-currency",
                                                        placeholder="Select...",
                                                        className="dash-bootstrap",
                                                    ),
                                                ],
                                                md=2,
                                            ),
                                            dbc.Col(
                                                [
                                                    dbc.Label("Date", html_for="inv-opening-date"),
                                                    dbc.Input(
                                                        id="inv-opening-date",
                                                        type="date",
                                                    ),
                                                ],
                                                md=2,
                                            ),
                                        ],
                                        className="g-2 mb-2",
                                    ),
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                [
                                                    dbc.Button(
                                                        [
                                                            dbc.Spinner(
                                                                size="sm",
                                                                spinner_class_name="me-2",
                                                                id="inv-category-submit-spinner",
                                                                spinner_style={"display": "none"}
                                                            ),
                                                            html.Span("Add Category")
                                                        ],
                                                        id="add-inv-category-btn",
                                                        color="primary",
                                                        className="w-100",
                                                        disabled=False
                                                    ),
                                                ],
                                                md=2,
                                                className="offset-md-10",
                                            )
                                        ],
                                        className="mb-4",
                                    ),
                                ]
                            ),
                            dbc.Spinner(
                                html.Div(id="inv-categories-table-container"),
                                color="primary",
                                type="border"
                            ),
                        ]
                    ),
                ],
                className="mb-5 shadow-sm",
            ),
            
            # --- Section 3: Transfers (Cash -> Investment) ---
            dbc.Card(
                [
                    dbc.CardHeader(
                        html.Div(
                            [
                                html.H4("3. Transfers to Investments", className="mb-0"),
                                html.Small("Record money moved from bank accounts to investments for this period", className="text-muted")
                            ]
                        )
                    ),
                    dbc.CardBody(
                        [
                            # Period check message
                            html.Div(id="inv-period-check-message", className="mb-3"),
                            
                            # Alert container for form feedback
                            html.Div(id="inv-transfer-form-alert"),
                            
                            dbc.Form(
                                [
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                [
                                                    dbc.Label(
                                                        ["Investment Category ", html.Span("*", className="text-danger")],
                                                        html_for="inv-transfer-category-select"
                                                    ),
                                                    dcc.Dropdown(
                                                        id="inv-transfer-category-select",
                                                        placeholder="Select category...",
                                                        className="dash-bootstrap",
                                                    ),
                                                    html.Small(
                                                        id="inv-transfer-category-error",
                                                        className="text-danger d-none"
                                                    ),
                                                ],
                                                md=3,
                                            ),
                                            dbc.Col(
                                                [
                                                    dbc.Label(
                                                        ["Amount (Cost) ", html.Span("*", className="text-danger")],
                                                        html_for="inv-transfer-amount"
                                                    ),
                                                    dbc.Input(
                                                        id="inv-transfer-amount",
                                                        placeholder="0.00",
                                                        type="number",
                                                        step="0.01",
                                                        min=0
                                                    ),
                                                    html.Small(
                                                        id="inv-transfer-amount-error",
                                                        className="text-danger d-none"
                                                    ),
                                                ],
                                                md=2,
                                            ),
                                            dbc.Col(
                                                [
                                                    dbc.Label("Units Purchased", html_for="inv-transfer-units"),
                                                    dbc.Input(
                                                        id="inv-transfer-units",
                                                        placeholder="Optional",
                                                        type="number",
                                                        step="0.00000001",
                                                        min=0
                                                    ),
                                                ],
                                                md=2,
                                            ),
                                            dbc.Col(
                                                [
                                                    dbc.Label(
                                                        ["Currency ", html.Span("*", className="text-danger")],
                                                        html_for="inv-transfer-currency"
                                                    ),
                                                    dcc.Dropdown(
                                                        id="inv-transfer-currency",
                                                        placeholder="Select...",
                                                        className="dash-bootstrap",
                                                    ),
                                                ],
                                                md=2,
                                            ),
                                            dbc.Col(
                                                [
                                                    dbc.Label(
                                                        ["Source Account ", html.Span("*", className="text-danger")],
                                                        html_for="inv-transfer-source-account"
                                                    ),
                                                    dcc.Dropdown(
                                                        id="inv-transfer-source-account",
                                                        placeholder="Select...",
                                                        className="dash-bootstrap",
                                                    ),
                                                ],
                                                md=3,
                                            ),
                                        ],
                                        className="g-2 mb-2",
                                    ),
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                [
                                                    dbc.Label("Transfer Date", html_for="inv-transfer-date"),
                                                    dbc.Input(id="inv-transfer-date", type="date"),
                                                ],
                                                md=2,
                                            ),
                                            dbc.Col(
                                                [
                                                    dbc.Label("Notes (Optional)", html_for="inv-transfer-notes"),
                                                    dbc.Input(
                                                        id="inv-transfer-notes",
                                                        placeholder="Additional details",
                                                        type="text",
                                                    ),
                                                ],
                                                md=8,
                                            ),
                                            dbc.Col(
                                                [
                                                    dbc.Label(html.Br()),  # Spacer
                                                    dbc.Button(
                                                        [
                                                            dbc.Spinner(
                                                                size="sm",
                                                                spinner_class_name="me-2",
                                                                id="inv-transfer-submit-spinner",
                                                                spinner_style={"display": "none"}
                                                            ),
                                                            html.Span("Record Transfer")
                                                        ],
                                                        id="add-inv-transfer-btn",
                                                        color="success",
                                                        className="w-100",
                                                        disabled=False
                                                    ),
                                                ],
                                                md=2,
                                            ),
                                        ],
                                        className="g-2 mb-4",
                                    ),
                                ]
                            ),
                            dbc.Spinner(
                                html.Div(id="inv-transfers-table-container"),
                                color="primary",
                                type="border"
                            ),
                        ]
                    ),
                ],
                className="mb-4 shadow-sm",
            ),
            
            # Confirmation modals for deletions
            dbc.Modal(
                [
                    dbc.ModalHeader(
                        dbc.ModalTitle(
                            [
                                html.I(className="bi bi-exclamation-triangle-fill text-warning me-2"),
                                "Confirm Account Deletion"
                            ]
                        )
                    ),
                    dbc.ModalBody(
                        [
                            html.P("Are you sure you want to delete this investment account?"),
                            html.P(
                                [
                                    html.I(className="bi bi-info-circle me-2"),
                                    html.Strong("This will also delete all associated categories and transfers.")
                                ],
                                className="text-danger mb-0"
                            )
                        ]
                    ),
                    dbc.ModalFooter(
                        [
                            dbc.Button("Cancel", id="inv-account-delete-cancel", className="me-2", color="secondary"),
                            dbc.Button("Delete", id="inv-account-delete-confirm", color="danger")
                        ]
                    )
                ],
                id="inv-account-delete-modal",
                is_open=False,
                centered=True
            ),
            
            dbc.Modal(
                [
                    dbc.ModalHeader(
                        dbc.ModalTitle(
                            [
                                html.I(className="bi bi-exclamation-triangle-fill text-warning me-2"),
                                "Confirm Category Deletion"
                            ]
                        )
                    ),
                    dbc.ModalBody(
                        [
                            html.P("Are you sure you want to delete this investment category?"),
                            html.P(
                                [
                                    html.I(className="bi bi-info-circle me-2"),
                                    html.Strong("This will also delete all associated transfers.")
                                ],
                                className="text-danger mb-0"
                            )
                        ]
                    ),
                    dbc.ModalFooter(
                        [
                            dbc.Button("Cancel", id="inv-category-delete-cancel", className="me-2", color="secondary"),
                            dbc.Button("Delete", id="inv-category-delete-confirm", color="danger")
                        ]
                    )
                ],
                id="inv-category-delete-modal",
                is_open=False,
                centered=True
            ),
            
            dbc.Modal(
                [
                    dbc.ModalHeader(
                        dbc.ModalTitle(
                            [
                                html.I(className="bi bi-exclamation-triangle-fill text-warning me-2"),
                                "Confirm Transfer Deletion"
                            ]
                        )
                    ),
                    dbc.ModalBody(
                        [
                            html.P("Are you sure you want to delete this transfer record?"),
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
                            dbc.Button("Cancel", id="inv-transfer-delete-cancel", className="me-2", color="secondary"),
                            dbc.Button("Delete", id="inv-transfer-delete-confirm", color="danger")
                        ]
                    )
                ],
                id="inv-transfer-delete-modal",
                is_open=False,
                centered=True
            ),
        ],
        fluid=True,
        className="py-4",
    )
