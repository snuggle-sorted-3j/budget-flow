import dash_bootstrap_components as dbc
from dash import dcc, html

def create_suspended_tab_layout():
    return dbc.Container(
        [
            dcc.Store(id="susp-trigger-refresh", data=0),
            dcc.Store(id="temp-item-id-store"),
            html.H2("Suspended Transactions", className="mb-4"),
            
            # --- Section 1: Add Suspended Transaction ---
            dbc.Card(
                [
                    dbc.CardHeader(html.H4("1. New Suspended Transaction", className="mb-0")),
                    dbc.CardBody(
                        [
                            html.P(
                                "Record money temporarily out of circulation (e.g. loans given, pending refunds).",
                                className="text-muted",
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        dbc.Input(id="susp-item-name", placeholder="Item Name (e.g. Loan to John)", type="text"),
                                        md=3,
                                    ),
                                    dbc.Col(
                                        dbc.Input(id="susp-amount", placeholder="Amount", type="number"),
                                        md=2,
                                    ),
                                    dbc.Col(
                                        dcc.Dropdown(id="susp-currency", placeholder="Currency", className="dash-bootstrap"),
                                        md=2,
                                    ),
                                    dbc.Col(
                                        dbc.Select(
                                            id="susp-type",
                                            options=[
                                                {"label": "Loan Out", "value": "LOAN_OUT"},
                                                {"label": "Purchase Return Pending", "value": "PURCHASE_RETURN"},
                                                {"label": "Other", "value": "OTHER"},
                                            ],
                                            placeholder="Type",
                                        ),
                                        md=3,
                                    ),
                                    dbc.Col(
                                        dbc.Button("Add", id="add-susp-btn", color="warning", className="w-100"),
                                        md=2,
                                    ),
                                ],
                                className="g-2 mb-2",
                            ),
                            dbc.Input(id="susp-notes", placeholder="Notes (Optional)", type="text", className="mb-3"),
                            
                            dbc.Collapse(
                                dbc.Alert(id="susp-message", dismissable=True),
                                id="susp-message-collapse",
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
                        dbc.Row([
                            dbc.Col(html.H4("2. Pending Transactions (Active)", className="mb-0 text-warning")),
                            dbc.Col(html.Div(id="susp-total-summary", className="text-end fw-bold")),
                        ])
                    ),
                    dbc.CardBody(
                        html.Div(id="susp-pending-table-container")
                    ),
                ],
                className="mb-4 shadow-sm border-warning",
            ),
            
            # --- Section 3: History ---
            dbc.Accordion(
                [
                    dbc.AccordionItem(
                        html.Div(id="susp-history-table-container"),
                        title="3. Settled / Converted History (Click to expand)",
                    ),
                ],
                start_collapsed=True,
            ),
            
            # --- Modals ---
            # Settle Modal
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle("Settle Transaction")),
                    dbc.ModalBody(
                        [
                            html.P("Mark this transaction as settled (money returned)."),
                            html.P(id="settle-modal-item-text", className="fw-bold"),
                            html.Label("Select Settlement Period (when money came back):"),
                            dcc.Dropdown(id="settle-period-select", className="dash-bootstrap mb-3"),
                        ]
                    ),
                    dbc.ModalFooter(
                        [
                            dbc.Button("Cancel", id="settle-cancel-btn", className="ms-auto", n_clicks=0),
                            dbc.Button("Confirm Settlement", id="settle-confirm-btn", color="success", n_clicks=0),
                        ]
                    ),
                ],
                id="settle-modal",
                is_open=False,
            ),
            
            # Convert Modal
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle("Convert to Expense")),
                    dbc.ModalBody(
                        [
                            html.P("Convert this suspended item into a permanent expense (money lost/spent)."),
                            html.P(id="convert-modal-item-text", className="fw-bold"),
                            html.Label("Select Expense Category:"),
                            dcc.Dropdown(id="convert-category-select", className="dash-bootstrap mb-3"),
                            html.P("This will create a new expense entry in the current period and remove this suspended item.", className="text-muted small"),
                        ]
                    ),
                    dbc.ModalFooter(
                        [
                            dbc.Button("Cancel", id="convert-cancel-btn", className="ms-auto", n_clicks=0),
                            dbc.Button("Convert to Expense", id="convert-confirm-btn", color="danger", n_clicks=0),
                        ]
                    ),
                ],
                id="convert-modal",
                is_open=False,
            ),
        ],
        fluid=True,
        className="py-4",
    )
