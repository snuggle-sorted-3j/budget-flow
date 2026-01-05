import dash_bootstrap_components as dbc
from dash import html, dcc

def create_installments_tab_layout():
    return dbc.Container(
        [
            dcc.Store(id="inst-trigger-refresh", data=0),
            dcc.Store(id="payment-item-id-store"),
            dcc.Store(id="edit-item-id-store"),
            
            html.H2("Installment Tracking", className="mb-4"),
            html.P("Track items you're paying for in installments. Log payments monthly to update balances.", className="text-muted mb-4"),
            
            # --- Section 1: Add New Installment ---
            dbc.Card(
                [
                    dbc.CardHeader(html.H4("Add New Installment Plan")),
                    dbc.CardBody(
                        [
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            dbc.Label(["Item Name ", html.Span("*", className="text-danger")]),
                                            dbc.Input(id="inst-name", placeholder="e.g. iPhone 15 Pro", type="text"),
                                        ],
                                        md=4,
                                    ),
                                    dbc.Col(
                                        [
                                            dbc.Label(["Total Price ", html.Span("*", className="text-danger")]),
                                            dbc.Input(id="inst-total", placeholder="0.00", type="number"),
                                        ],
                                        md=3,
                                    ),
                                    dbc.Col(
                                        [
                                            dbc.Label(["Currency ", html.Span("*", className="text-danger")]),
                                            dbc.Select(id="inst-currency"), # Options loaded via callback
                                        ],
                                        md=2,
                                    ),
                                    dbc.Col(
                                        [
                                            dbc.Label(["Start Period ", html.Span("*", className="text-danger")]),
                                            dbc.Select(id="inst-start-period"), # Options loaded via callback
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
                                            dbc.Label("Monthly Payment (Optional)"),
                                            dbc.Input(id="inst-monthly", placeholder="Planned amount", type="number"),
                                        ],
                                        md=4,
                                    ),
                                    dbc.Col(
                                        [
                                            dbc.Label("Months to Pay (Optional)"),
                                            dbc.Input(id="inst-months", placeholder="e.g. 12", type="number"),
                                        ],
                                        md=3,
                                    ),
                                    dbc.Col(
                                        [
                                            dbc.Label("Notes"),
                                            dbc.Input(id="inst-notes", type="text"),
                                        ],
                                        md=5,
                                    ),
                                ],
                                className="mb-3",
                            ),
                            dbc.Button("Create Installment", id="add-inst-btn", color="primary"),
                            dbc.Collapse(
                                dbc.Alert(id="inst-message", color="success", className="mt-3"),
                                id="inst-message-collapse",
                                is_open=False,
                            ),
                        ]
                    ),
                ],
                className="mb-5 shadow-sm",
            ),
            
            # --- Section 2: Active Installments ---
            html.H4("Active Installments", className="mb-3"),
            html.Div(id="active-installments-container"), # Cards injected here
            
            html.Hr(className="my-5"),
            
            # --- Section 3: Paid Off Items ---
            dbc.Accordion(
                [
                    dbc.AccordionItem(
                        html.Div(id="paid-off-installments-container"),
                        title="Paid Off Items",
                    ),
                ],
                start_collapsed=True,
                className="mb-5",
            ),
            
            # --- Modals ---
            # Add Payment Modal
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle("Add Installment Payment")),
                    dbc.ModalBody(
                        [
                            dbc.Alert(id="payment-modal-error", color="danger", is_open=False, dismissable=True),
                            html.Div(id="payment-modal-title", className="mb-3 fw-bold"),
                            dbc.Label(["Payment Amount ", html.Span("*", className="text-danger")]),
                            dbc.Input(id="payment-amount", type="number", placeholder="0.00", className="mb-3"),
                            dbc.Label(["Payment Date ", html.Span("*", className="text-danger")]),
                            dbc.Input(id="payment-date", type="date", className="mb-3"),
                            dbc.Label("Notes"),
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
            ),

            # Edit Item Modal (for total price increase etc)
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle("Edit Installment Plan")),
                    dbc.ModalBody(
                        [
                            dbc.Alert(id="edit-inst-modal-error", color="danger", is_open=False, dismissable=True),
                            dbc.Label("Item Name"),
                            dbc.Input(id="edit-inst-name", type="text", className="mb-3"),
                            dbc.Label("Total Price (increase/decrease here)"),
                            dbc.Input(id="edit-inst-total", type="number", className="mb-3"),
                             dbc.Label("Monthly Payment"),
                            dbc.Input(id="edit-inst-monthly", type="number", className="mb-3"),
                            dbc.Label("Notes"),
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
            ),
        ],
        fluid=True,
        className="py-4",
    )
