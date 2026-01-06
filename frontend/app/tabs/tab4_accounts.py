"""Enhanced Accounts Management tab with comprehensive error handling and UX improvements."""
import dash_bootstrap_components as dbc
from dash import html, dcc


def create_accounts_tab_layout():
    """Create the Accounts Management tab layout with enhanced UX."""
    
    return dbc.Container(
        [
            # Toast notifications container
            html.Div(id="account-toast-container"),
            
            # Store for pending deletion
            dcc.Store(id="account-pending-delete-id"),
            
            # Store for triggering refresh
            dcc.Store(id="account-refresh-trigger"),
            
            dbc.Card(
                [
                    dbc.CardHeader(
                        html.Div(
                            [
                                html.H4("Add Account", className="mb-0"),
                                html.Small("Track bank accounts and cash wallets", className="text-muted")
                            ]
                        )
                    ),
                    dbc.CardBody(
                        [
                            # Alert container for form feedback
                            html.Div(id="account-form-alert"),
                            
                            dbc.Form(
                                [
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                [
                                                    dbc.Label(
                                                        ["Account Name ", html.Span("*", className="text-danger")],
                                                        html_for="account-name-input"
                                                    ),
                                                    dbc.Input(
                                                        id="account-name-input",
                                                        type="text",
                                                        placeholder="e.g. Main Bank Account"
                                                    ),
                                                    html.Small(
                                                        id="account-name-error",
                                                        className="text-danger d-none"
                                                    ),
                                                ],
                                                md=3,
                                            ),
                                            dbc.Col(
                                                [
                                                    dbc.Label(
                                                        ["Type ", html.Span("*", className="text-danger")],
                                                        html_for="account-type-select"
                                                    ),
                                                    dbc.Select(
                                                        id="account-type-select",
                                                        options=[
                                                            {"label": "Bank Account", "value": "BANK"},
                                                            {"label": "Cash / Wallet", "value": "CASH"},
                                                        ],
                                                        value="BANK",
                                                    ),
                                                ],
                                                md=2,
                                            ),
                                            dbc.Col(
                                                [
                                                    dbc.Label(
                                                        ["Currency ", html.Span("*", className="text-danger")],
                                                        html_for="account-currency-select"
                                                    ),
                                                    dbc.Select(
                                                        id="account-currency-select",
                                                        placeholder="Select..."
                                                    ),
                                                    html.Small(
                                                        id="account-currency-error",
                                                        className="text-danger d-none"
                                                    ),
                                                ],
                                                md=2,
                                            ),
                                            dbc.Col(
                                                [
                                                    dbc.Label(
                                                        "Opening Balance",
                                                        html_for="account-opening-balance"
                                                    ),
                                                    dbc.Input(
                                                        id="account-opening-balance",
                                                        type="number",
                                                        value=0,
                                                        step="0.01"
                                                    ),
                                                    html.Small(
                                                        "Balance at migration start",
                                                        className="text-muted mt-1 d-block"
                                                    ),
                                                ],
                                                md=2,
                                            ),
                                            dbc.Col(
                                                [
                                                    dbc.Label(
                                                        "Opening Date",
                                                        html_for="account-opening-date"
                                                    ),
                                                    dbc.Input(
                                                        id="account-opening-date",
                                                        type="date"
                                                    ),
                                                    html.Small(
                                                        id="account-opening-date-error",
                                                        className="text-danger d-none"
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
                                                id="account-submit-spinner",
                                                spinner_style={"display": "none"}
                                            ),
                                            html.Span("Add Account", id="account-submit-text")
                                        ],
                                        id="add-account-btn",
                                        color="primary",
                                        disabled=False
                                    ),
                                ]
                            ),
                        ]
                    ),
                ],
                className="mb-4 shadow-sm",
            ),
            
            dbc.Card(
                [
                    dbc.CardHeader(
                        html.Div(
                            [
                                html.H4("Your Accounts", className="mb-0"),
                                html.Small("Manage your financial accounts", className="text-muted")
                            ]
                        )
                    ),
                    dbc.CardBody(
                        [
                            dbc.Spinner(
                                html.Div(id="account-table-container"),
                                color="primary",
                                type="border"
                            ),
                        ]
                    ),
                ],
                className="shadow-sm"
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
                            html.P("Are you sure you want to delete this account?"),
                            html.P(
                                [
                                    html.I(className="bi bi-info-circle me-2"),
                                    html.Strong("This action cannot be undone and may affect your balance snapshots.")
                                ],
                                className="text-danger mb-0"
                            )
                        ]
                    ),
                    dbc.ModalFooter(
                        [
                            dbc.Button(
                                "Cancel",
                                id="account-delete-cancel",
                                className="me-2",
                                color="secondary"
                            ),
                            dbc.Button(
                                "Delete",
                                id="account-delete-confirm",
                                color="danger"
                            )
                        ]
                    )
                ],
                id="account-delete-modal",
                is_open=False,
                centered=True
            ),
        ],
        fluid=True,
        className="py-4",
    )
