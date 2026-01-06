"""Enhanced Installments tab with comprehensive error handling and UX improvements."""
import dash_bootstrap_components as dbc
from dash import html, dcc


def create_installments_tab_layout():
    """Create the Installment Tracking tab layout with enhanced UX."""
    
    return dbc.Container(
        [
            # Toast notifications container
            html.Div(id="inst-toast-container"),
            
            # Stores
            dcc.Store(id="inst-trigger-refresh", data=0),
            dcc.Store(id="payment-item-id-store"),
            dcc.Store(id="edit-item-id-store"),
            dcc.Store(id="inst-pending-delete-id"),
            
            html.H2("Installment Tracking", className="mb-2"),
            html.P(
                "Track items you're paying for in installments. Log payments monthly to update balances.",
                className="text-muted mb-4"
            ),
            
            # --- Section 1: Add New Installment ---
            dbc.Card(
                [
                    dbc.CardHeader(
                        html.Div(
                            [
                                html.H4("Add New Installment Plan", className="mb-0"),
                                html.Small("Create a payment plan for items purchased in installments", className="text-muted")
                            ]
                        )
                    ),
                    dbc.CardBody(
                        [
                            # Alert container for form feedback
                            html.Div(id="inst-form-alert"),
                            
                            dbc.Form(
                                [
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                [
                                                    dbc.Label(
                                                        ["Item Name ", html.Span("*", className="text-danger")],
                                                        html_for="inst-name"
                                                    ),
                                                    dbc.Input(
                                                        id="inst-name",
                                                        placeholder="e.g. iPhone 15 Pro",
                                                        type="text"
                                                    ),
                                                    html.Small(
                                                        id="inst-name-error",
                                                        className="text-danger d-none"
                                                    ),
                                                ],
                                                md=4,
                                            ),
                                            dbc.Col(
                                                [
                                                    dbc.Label(
                                                        ["Total Price ", html.Span("*", className="text-danger")],
                                                        html_for="inst-total"
                                                    ),
                                                    dbc.Input(
                                                        id="inst-total",
                                                        placeholder="0.00",
                                                        type="number",
                                                        step="0.01",
                                                        min=0
                                                    ),
                                                    html.Small(
                                                        id="inst-total-error",
                                                        className="text-danger d-none"
                                                    ),
                                                ],
                                                md=3,
                                            ),
                                            dbc.Col(
                                                [
                                                    dbc.Label(
                                                        ["Currency ", html.Span("*", className="text-danger")],
                                                        html_for="inst-currency"
                                                    ),
                                                    dbc.Select(id="inst-currency"),
                                                    html.Small(
                                                        id="inst-currency-error",
                                                        className="text-danger d-none"
                                                    ),
                                                ],
                                                md=2,
                                            ),
                                            dbc.Col(
                                                [
                                                    dbc.Label(
                                                        ["Start Period ", html.Span("*", className="text-danger")],
                                                        html_for="inst-start-period"
                                                    ),
                                                    dbc.Select(id="inst-start-period"),
                                                    html.Small(
                                                        id="inst-start-period-error",
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
                                                    dbc.Label("Monthly Payment (Optional)", html_for="inst-monthly"),
                                                    dbc.Input(
                                                        id="inst-monthly",
                                                        placeholder="Planned amount",
                                                        type="number",
                                                        step="0.01",
                                                        min=0
                                                    ),
                                                ],
                                                md=4,
                                            ),
                                            dbc.Col(
                                                [
                                                    dbc.Label("Months to Pay (Optional)", html_for="inst-months"),
                                                    dbc.Input(
                                                        id="inst-months",
                                                        placeholder="e.g. 12",
                                                        type="number",
                                                        min=1
                                                    ),
                                                ],
                                                md=3,
                                            ),
                                            dbc.Col(
                                                [
                                                    dbc.Label("Notes", html_for="inst-notes"),
                                                    dbc.Input(id="inst-notes", type="text"),
                                                ],
                                                md=5,
                                            ),
                                        ],
                                        className="mb-3",
                                    ),
                                    dbc.Button(
                                        [
                                            dbc.Spinner(
                                                size="sm",
                                                spinner_class_name="me-2",
                                                id="inst-submit-spinner",
                                                spinner_style={"display": "none"}
                                            ),
                                            html.Span("Create Installment", id="inst-submit-text")
                                        ],
                                        id="add-inst-btn",
                                        color="primary",
                                        disabled=False
                                    ),
                                ]
                            ),
                        ]
                    ),
                ],
                className="mb-5 shadow-sm",
            ),
            
            # --- Section 2: Active Installments ---
            dbc.Card(
                [
                    dbc.CardHeader(
                        html.Div(
                            [
                                html.H4("Active Installments", className="mb-0"),
                                html.Small("Items currently being paid off", className="text-muted")
                            ]
                        )
                    ),
                    dbc.CardBody(
                        [
                            dbc.Spinner(
                                html.Div(id="active-installments-container"),
                                color="primary",
                                type="border"
                            ),
                        ]
                    ),
                ],
                className="mb-4 shadow-sm"
            ),
            
            # --- Section 3: Paid Off Items ---
            dbc.Card(
                [
                    dbc.CardHeader(
                        html.Div(
                            [
                                html.H4("Paid Off Items", className="mb-0"),
                                html.Small("Completed installment plans", className="text-muted")
                            ]
                        )
                    ),
                    dbc.CardBody(
                        [
                            html.Div(id="paid-off-installments-container"),
                        ]
                    ),
                ],
                className="mb-5 shadow-sm"
            ),
            
            # --- Modals ---
            # Add Payment Modal
            dbc.Modal(
                [
                    dbc.ModalHeader(
                        dbc.ModalTitle(
                            [
                                html.I(className="bi bi-cash-coin me-2"),
                                "Add Installment Payment"
                            ]
                        )
                    ),
                    dbc.ModalBody(
                        [
                            html.Div(id="payment-modal-alert"),
                            html.Div(id="payment-modal-title", className="mb-3 fw-bold"),
                            dbc.Label(
                                ["Payment Amount ", html.Span("*", className="text-danger")],
                                html_for="payment-amount"
                            ),
                            dbc.Input(
                                id="payment-amount",
                                type="number",
                                placeholder="0.00",
                                step="0.01",
                                min=0,
                                className="mb-3"
                            ),
                            dbc.Label(
                                ["Payment Date ", html.Span("*", className="text-danger")],
                                html_for="payment-date"
                            ),
                            dbc.Input(id="payment-date", type="date", className="mb-3"),
                            dbc.Label("Notes", html_for="payment-notes"),
                            dbc.Input(id="payment-notes", type="text", className="mb-3"),
                        ]
                    ),
                    dbc.ModalFooter(
                        [
                            dbc.Button("Cancel", id="payment-cancel-btn", className="me-2"),
                            dbc.Button("Save Payment", id="payment-save-btn", color="success"),
                        ]
                    ),
                ],
                id="add-payment-modal",
                is_open=False,
                centered=True
            ),

            # Edit Item Modal
            dbc.Modal(
                [
                    dbc.ModalHeader(
                        dbc.ModalTitle(
                            [
                                html.I(className="bi bi-pencil-square me-2"),
                                "Edit Installment Plan"
                            ]
                        )
                    ),
                    dbc.ModalBody(
                        [
                            html.Div(id="edit-inst-modal-alert"),
                            dbc.Label("Item Name", html_for="edit-inst-name"),
                            dbc.Input(id="edit-inst-name", type="text", className="mb-3"),
                            dbc.Label("Total Price", html_for="edit-inst-total"),
                            dbc.Input(id="edit-inst-total", type="number", step="0.01", className="mb-3"),
                            dbc.Label("Monthly Payment", html_for="edit-inst-monthly"),
                            dbc.Input(id="edit-inst-monthly", type="number", step="0.01", className="mb-3"),
                            dbc.Label("Notes", html_for="edit-inst-notes"),
                            dbc.Input(id="edit-inst-notes", type="text", className="mb-3"),
                        ]
                    ),
                    dbc.ModalFooter(
                        [
                            dbc.Button("Cancel", id="edit-inst-cancel-btn", className="me-2"),
                            dbc.Button("Save Changes", id="edit-inst-save-btn", color="primary"),
                        ]
                    ),
                ],
                id="edit-inst-modal",
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
                            html.P("Are you sure you want to delete this installment plan?"),
                            html.P(
                                [
                                    html.I(className="bi bi-info-circle me-2"),
                                    html.Strong("This action cannot be undone and will delete all associated payment records.")
                                ],
                                className="text-danger mb-0"
                            )
                        ]
                    ),
                    dbc.ModalFooter(
                        [
                            dbc.Button("Cancel", id="inst-delete-cancel", className="me-2", color="secondary"),
                            dbc.Button("Delete", id="inst-delete-confirm", color="danger")
                        ]
                    )
                ],
                id="inst-delete-modal",
                is_open=False,
                centered=True
            ),
        ],
        fluid=True,
        className="py-4",
    )
