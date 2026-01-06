"""Enhanced Suspended Transactions tab with comprehensive error handling and UX improvements."""
import dash_bootstrap_components as dbc
from dash import dcc, html


def create_suspended_tab_layout():
    """Create the Suspended Transactions tab layout with enhanced UX."""
    
    return dbc.Container(
        [
            # Toast notifications container
            html.Div(id="susp-toast-container"),
            
            # Stores
            dcc.Store(id="susp-trigger-refresh", data=0),
            dcc.Store(id="temp-item-id-store"),
            dcc.Store(id="susp-pending-delete-id"),
            
            html.H2("Suspended Transactions", className="mb-2"),
            html.P(
                "Record money temporarily out of circulation (e.g. loans given, pending refunds).",
                className="text-muted mb-4"
            ),
            
            # --- Section 1: Add Suspended Transaction ---
            dbc.Card(
                [
                    dbc.CardHeader(
                        html.Div(
                            [
                                html.H4("1. New Suspended Transaction", className="mb-0"),
                                html.Small("Track money temporarily unavailable", className="text-muted")
                            ]
                        )
                    ),
                    dbc.CardBody(
                        [
                            # Alert container for form feedback
                            html.Div(id="susp-form-alert"),
                            
                            dbc.Form(
                                [
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                [
                                                    dbc.Label(
                                                        ["Item Name ", html.Span("*", className="text-danger")],
                                                        html_for="susp-item-name"
                                                    ),
                                                    dbc.Input(
                                                        id="susp-item-name",
                                                        placeholder="e.g. Loan to John",
                                                        type="text"
                                                    ),
                                                    html.Small(
                                                        id="susp-item-name-error",
                                                        className="text-danger d-none"
                                                    ),
                                                ],
                                                md=3,
                                            ),
                                            dbc.Col(
                                                [
                                                    dbc.Label(
                                                        ["Amount ", html.Span("*", className="text-danger")],
                                                        html_for="susp-amount"
                                                    ),
                                                    dbc.Input(
                                                        id="susp-amount",
                                                        placeholder="0.00",
                                                        type="number",
                                                        step="0.01",
                                                        min=0
                                                    ),
                                                    html.Small(
                                                        id="susp-amount-error",
                                                        className="text-danger d-none"
                                                    ),
                                                ],
                                                md=2,
                                            ),
                                            dbc.Col(
                                                [
                                                    dbc.Label(
                                                        ["Currency ", html.Span("*", className="text-danger")],
                                                        html_for="susp-currency"
                                                    ),
                                                    dcc.Dropdown(
                                                        id="susp-currency",
                                                        placeholder="Select...",
                                                        className="dash-bootstrap"
                                                    ),
                                                    html.Small(
                                                        id="susp-currency-error",
                                                        className="text-danger d-none"
                                                    ),
                                                ],
                                                md=2,
                                            ),
                                            dbc.Col(
                                                [
                                                    dbc.Label(
                                                        ["Type ", html.Span("*", className="text-danger")],
                                                        html_for="susp-type"
                                                    ),
                                                    dbc.Select(
                                                        id="susp-type",
                                                        options=[
                                                            {"label": "Loan Out", "value": "LOAN_OUT"},
                                                            {"label": "Purchase Return Pending", "value": "PURCHASE_RETURN"},
                                                            {"label": "Other", "value": "OTHER"},
                                                        ],
                                                        placeholder="Select type...",
                                                    ),
                                                    html.Small(
                                                        id="susp-type-error",
                                                        className="text-danger d-none"
                                                    ),
                                                ],
                                                md=3,
                                            ),
                                            dbc.Col(
                                                [
                                                    dbc.Label(html.Br()),  # Spacer
                                                    dbc.Button(
                                                        [
                                                            dbc.Spinner(
                                                                size="sm",
                                                                spinner_class_name="me-2",
                                                                id="susp-submit-spinner",
                                                                spinner_style={"display": "none"}
                                                            ),
                                                            html.Span("Add")
                                                        ],
                                                        id="add-susp-btn",
                                                        color="warning",
                                                        className="w-100",
                                                        disabled=False
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
                                                    dbc.Label("Notes (Optional)", html_for="susp-notes"),
                                                    dbc.Input(
                                                        id="susp-notes",
                                                        placeholder="Additional details",
                                                        type="text"
                                                    ),
                                                ],
                                                md=12,
                                            ),
                                        ],
                                        className="mb-3",
                                    ),
                                ]
                            ),
                        ]
                    ),
                ],
                className="mb-4 shadow-sm",
            ),
            
            # --- Section 2: Pending Transactions ---
            dbc.Card(
                [
                    dbc.CardHeader(
                        dbc.Row(
                            [
                                dbc.Col(
                                    html.Div(
                                        [
                                            html.H4("2. Pending Transactions (Active)", className="mb-0 text-warning"),
                                            html.Small("Money currently suspended", className="text-muted")
                                        ]
                                    )
                                ),
                                dbc.Col(
                                    html.Div(id="susp-total-summary", className="text-end fw-bold"),
                                    width="auto"
                                ),
                            ]
                        )
                    ),
                    dbc.CardBody(
                        [
                            dbc.Spinner(
                                html.Div(id="susp-pending-table-container"),
                                color="warning",
                                type="border"
                            ),
                        ]
                    ),
                ],
                className="mb-4 shadow-sm border-warning",
            ),
            
            # --- Section 3: History ---
            dbc.Card(
                [
                    dbc.CardHeader(
                        html.Div(
                            [
                                html.H4("3. Settled / Converted History", className="mb-0"),
                                html.Small("Completed transactions", className="text-muted")
                            ]
                        )
                    ),
                    dbc.CardBody(
                        [
                            html.Div(id="susp-history-table-container"),
                        ]
                    ),
                ],
                className="mb-4 shadow-sm"
            ),
            
            # --- Modals ---
            # Settle Modal
            dbc.Modal(
                [
                    dbc.ModalHeader(
                        dbc.ModalTitle(
                            [
                                html.I(className="bi bi-check-circle me-2 text-success"),
                                "Settle Transaction"
                            ]
                        )
                    ),
                    dbc.ModalBody(
                        [
                            html.Div(id="settle-modal-alert"),
                            html.P("Mark this transaction as settled (money returned)."),
                            html.P(id="settle-modal-item-text", className="fw-bold mb-3"),
                            dbc.Label(
                                ["Select Settlement Period ", html.Span("*", className="text-danger")],
                                html_for="settle-period-select"
                            ),
                            html.Small("When did the money come back?", className="text-muted d-block mb-2"),
                            dcc.Dropdown(
                                id="settle-period-select",
                                className="dash-bootstrap mb-3",
                                placeholder="Select period..."
                            ),
                        ]
                    ),
                    dbc.ModalFooter(
                        [
                            dbc.Button("Cancel", id="settle-cancel-btn", className="me-2"),
                            dbc.Button("Confirm Settlement", id="settle-confirm-btn", color="success"),
                        ]
                    ),
                ],
                id="settle-modal",
                is_open=False,
                centered=True
            ),
            
            # Convert Modal
            dbc.Modal(
                [
                    dbc.ModalHeader(
                        dbc.ModalTitle(
                            [
                                html.I(className="bi bi-arrow-right-circle me-2 text-danger"),
                                "Convert to Expense"
                            ]
                        )
                    ),
                    dbc.ModalBody(
                        [
                            html.Div(id="convert-modal-alert"),
                            html.P("Convert this suspended item into a permanent expense (money lost/spent)."),
                            html.P(id="convert-modal-item-text", className="fw-bold mb-3"),
                            dbc.Label(
                                ["Select Expense Category ", html.Span("*", className="text-danger")],
                                html_for="convert-category-select"
                            ),
                            dcc.Dropdown(
                                id="convert-category-select",
                                className="dash-bootstrap mb-3",
                                placeholder="Select category..."
                            ),
                            dbc.Alert(
                                [
                                    html.I(className="bi bi-info-circle me-2"),
                                    "This will create a new expense entry in the current period and remove this suspended item."
                                ],
                                color="info",
                                className="mb-0"
                            ),
                        ]
                    ),
                    dbc.ModalFooter(
                        [
                            dbc.Button("Cancel", id="convert-cancel-btn", className="me-2"),
                            dbc.Button("Convert to Expense", id="convert-confirm-btn", color="danger"),
                        ]
                    ),
                ],
                id="convert-modal",
                is_open=False,
                centered=True
            ),
            
            # Delete Confirmation Modal
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
                            html.P("Are you sure you want to delete this suspended transaction?"),
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
                            dbc.Button("Cancel", id="susp-delete-cancel", className="me-2", color="secondary"),
                            dbc.Button("Delete", id="susp-delete-confirm", color="danger")
                        ]
                    )
                ],
                id="susp-delete-modal",
                is_open=False,
                centered=True
            ),
        ],
        fluid=True,
        className="py-4",
    )
