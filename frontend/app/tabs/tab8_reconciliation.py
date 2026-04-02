import dash_bootstrap_components as dbc
from dash import html, dcc
from utils.tooltips import help_icon, TIPS, make_tooltip


def create_reconciliation_tab_layout():
    """Create the Reconciliation tab layout - BudgetFlow's core feature."""
    
    return dbc.Container(
        [
            dcc.Store(id="recon-balanced-store", data=False),
            # Reconciliation Content (hidden until period selected)
            html.Div(
                id="recon-content-container",
                children=[
                    # Section 1: Balance Snapshots
                    dbc.Card(
                        [
                            dbc.CardHeader(
                                html.H4([
                                    "Step 1: Enter Balance Snapshots",
                                    help_icon("tip-recon-snapshot", "reconciliation_snapshot", placement="right"),
                                ])
                            ),
                            dbc.CardBody(
                                [
                                    dbc.Alert(
                                        [
                                            html.I(className="bi bi-info-circle me-2"),
                                            "Enter your actual bank account balances as of the snapshot date. "
                                            "These will be compared against expected balances calculated from income and expenses.",
                                        ],
                                        color="info",
                                        className="mb-3",
                                    ),
                                    dbc.Alert(
                                        id="snapshot-message",
                                        is_open=False,
                                        dismissable=True,
                                    ),
                                    html.Div(id="snapshot-date-display", className="mb-3"),
                                    html.Div(id="snapshots-table-container"),
                                    dbc.Button(
                                        [html.I(className="bi bi-save me-2"), "Save Snapshots"],
                                        id="save-snapshots-btn",
                                        color="primary",
                                        className="mt-3",
                                    ),
                                ]
                            ),
                        ],
                        className="mb-4",
                    ),
                    # Section 2: Reconciliation Summary
                    dbc.Card(
                        [
                            dbc.CardHeader(
                                html.H4("Step 2: Period Reconciliation Summary")
                            ),
                            dbc.CardBody(
                                [
                                    # This is now updated dynamically via common_reconciliation_callbacks.py
                                    html.Div(id="recon-summary-container"),
                                ]
                            ),
                        ],
                        className="mb-4",
                    ),
                    # Section 3: Finalize Period
                    html.Div(
                        id="finalize-section-container",
                        children=[
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        html.H4("Step 3: Finalize Period")
                                    ),
                                    dbc.CardBody(
                                        [
                                            dbc.Alert(
                                                [
                                                    html.I(className="bi bi-exclamation-triangle me-2"),
                                                    html.Strong("Warning: "),
                                                    "Once finalized, transactions in this period cannot be edited. "
                                                    "Ensure all balances are reconciled before proceeding.",
                                                ],
                                                color="warning",
                                                className="mb-3",
                                            ),
                                            dbc.Alert(
                                                id="finalize-message",
                                                is_open=False,
                                                dismissable=True,
                                            ),
                                            html.Div(id="finalize-button-container"),
                                        ]
                                    ),
                                ],
                            ),
                        ],
                        style={"display": "none"},
                    ),
                ],
                style={"display": "none"},
            ),
            # Confirmation Modal
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle("Confirm Period Finalization")),
                    dbc.ModalBody(
                        [
                            html.P("Are you sure you want to finalize this period?"),
                            html.P(
                                [
                                    html.Strong("This action cannot be undone. "),
                                    "All transactions will be locked and cannot be modified.",
                                ],
                                className="text-danger",
                            ),
                        ]
                    ),
                    dbc.ModalFooter(
                        [
                            dbc.Button(
                                "Cancel",
                                id="finalize-cancel-btn",
                                color="secondary",
                                className="me-2",
                            ),
                            dbc.Button(
                                "Finalize Period",
                                id="finalize-confirm-btn",
                                color="danger",
                            ),
                        ]
                    ),
                ],
                id="finalize-modal",
                is_open=False,
            ),
        ],
        fluid=True,
        className="py-4",
    )
