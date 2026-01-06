"""Enhanced Income Management tab with comprehensive error handling and UX improvements."""
import dash_bootstrap_components as dbc
from dash import html, dcc


def create_income_tab_layout():
    """Create the Income Management tab layout with enhanced UX."""
    
    return dbc.Container(
        [
            # Toast notifications container
            html.Div(id="income-toast-container"),
            
            # Store for pending deletion
            dcc.Store(id="income-pending-delete-id"),
            
            # Add Income Form (hidden until period selected)
            html.Div(
                id="income-form-container",
                children=[
                    # Live Reconciliation Summary
                    html.Div(id="income-recon-summary", className="mb-4"),
                    
                    dbc.Card(
                        [
                            dbc.CardHeader(html.H4("Add Income Entry")),
                            dbc.CardBody(
                                [
                                    # Alert container for form feedback
                                    html.Div(id="income-form-alert"),
                                    
                                    dbc.Form(
                                        [
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        [
                                                            dbc.Label(
                                                                ["Source Name ", html.Span("*", className="text-danger")],
                                                                html_for="income-source-name"
                                                            ),
                                                            dbc.Input(
                                                                id="income-source-name",
                                                                type="text",
                                                                placeholder="e.g., Salary, Freelance",
                                                            ),
                                                            html.Small(
                                                                id="income-source-name-error",
                                                                className="text-danger d-none"
                                                            ),
                                                        ],
                                                        md=6,
                                                    ),
                                                    dbc.Col(
                                                        [
                                                            dbc.Label(
                                                                ["Amount ", html.Span("*", className="text-danger")],
                                                                html_for="income-amount"
                                                            ),
                                                            dbc.Input(
                                                                id="income-amount",
                                                                type="number",
                                                                step="0.01",
                                                                min=0,
                                                                placeholder="0.00",
                                                            ),
                                                            html.Small(
                                                                id="income-amount-error",
                                                                className="text-danger d-none"
                                                            ),
                                                        ],
                                                        md=3,
                                                    ),
                                                    dbc.Col(
                                                        [
                                                            dbc.Label(
                                                                ["Currency ", html.Span("*", className="text-danger")],
                                                                html_for="income-currency"
                                                            ),
                                                            dbc.Select(
                                                                id="income-currency",
                                                                placeholder="Select currency...",
                                                            ),
                                                            html.Small(
                                                                id="income-currency-error",
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
                                                            dbc.Label("Income Date (Optional)", html_for="income-date"),
                                                            dbc.Input(
                                                                id="income-date",
                                                                type="date",
                                                            ),
                                                            html.Small(
                                                                id="income-date-error",
                                                                className="text-danger d-none"
                                                            ),
                                                        ],
                                                        md=4,
                                                    ),
                                                    dbc.Col(
                                                        [
                                                            dbc.Label("Notes (Optional)", html_for="income-notes"),
                                                            dbc.Textarea(
                                                                id="income-notes",
                                                                placeholder="Additional notes...",
                                                                rows=1,
                                                            ),
                                                        ],
                                                        md=8,
                                                    ),
                                                ],
                                                className="mb-3",
                                            ),
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        [
                                                            dbc.Checkbox(
                                                                id="income-tax-applicable",
                                                                label="Tax Applicable",
                                                                value=False,
                                                            ),
                                                        ],
                                                        md=4,
                                                    ),
                                                ],
                                                className="mb-3",
                                            ),
                                            dbc.Button(
                                                [
                                                    dbc.Spinner(
                                                        size="sm",
                                                        spinner_class_name="me-2",
                                                        id="income-submit-spinner",
                                                        spinner_style={"display": "none"}
                                                    ),
                                                    html.Span("Add Income", id="income-submit-text")
                                                ],
                                                id="add-income-btn",
                                                color="success",
                                                className="mt-2",
                                                disabled=False
                                            ),
                                        ]
                                    ),
                                ]
                            ),
                        ],
                        className="mb-4 shadow-sm",
                    ),
                    
                    # Income List
                    dbc.Card(
                        [
                            dbc.CardHeader(
                                html.Div(
                                    [
                                        html.H4("Income Entries", className="mb-0"),
                                        html.Small("Track all income sources for this period", className="text-muted")
                                    ]
                                )
                            ),
                            dbc.CardBody(
                                [
                                    dbc.Spinner(
                                        html.Div(id="income-table-container"),
                                        color="primary",
                                        type="border"
                                    ),
                                ]
                            ),
                        ],
                        className="shadow-sm"
                    ),
                ],
                style={"display": "none"},
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
                            html.P("Are you sure you want to delete this income entry?"),
                            html.P(
                                [
                                    html.I(className="bi bi-info-circle me-2"),
                                    html.Strong("This action cannot be undone and will affect your reconciliation.")
                                ],
                                className="text-danger mb-0"
                            )
                        ]
                    ),
                    dbc.ModalFooter(
                        [
                            dbc.Button(
                                "Cancel",
                                id="income-delete-cancel",
                                className="me-2",
                                color="secondary"
                            ),
                            dbc.Button(
                                "Delete",
                                id="income-delete-confirm",
                                color="danger"
                            )
                        ]
                    )
                ],
                id="income-delete-modal",
                is_open=False,
                centered=True
            ),
        ],
        fluid=True,
        className="py-4",
    )
