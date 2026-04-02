"""Enhanced Expenses Management tab with comprehensive error handling and UX improvements."""
import dash_bootstrap_components as dbc
from dash import html, dcc


def create_expenses_tab_layout():
    """Create the Expenses Management tab layout with enhanced UX."""
    
    return dbc.Container(
        [
            # Toast notifications container
            html.Div(id="expense-toast-container"),
            
            # Store for pending deletion
            dcc.Store(id="expense-pending-delete-id"),
            # Auto-save draft store
            dcc.Store(id="expense-draft-store", storage_type="session"),
            # Auto-save indicator
            html.Div(
                id="expense-autosave-indicator",
                className="text-muted small text-end mb-1",
                style={"minHeight": "20px"},
            ),
            
            # Add Expense Form (hidden until period selected)
            html.Div(
                id="expense-form-container",
                children=[
                    # Live Reconciliation Summary
                    html.Div(id="expense-recon-summary", className="mb-4"),
                    
                    dbc.Card(
                        [
                            dbc.CardHeader(html.H4("Add Expense Entry")),
                            dbc.CardBody(
                                [
                                    # Alert container for form feedback
                                    html.Div(id="expense-form-alert"),
                                    
                                    dbc.Form(
                                        [
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        [
                                                            html.Div([
                                                                dbc.Label(
                                                                    ["Category ", html.Span("*", className="text-danger")],
                                                                    html_for="expense-category"
                                                                ),
                                                                html.A(
                                                                    "Manage",
                                                                    href="/dashboard/categories",
                                                                    className="float-end small text-decoration-none"
                                                                ),
                                                            ]),
                                                            dbc.Select(
                                                                id="expense-category",
                                                                placeholder="Select category...",
                                                            ),
                                                            html.Small(
                                                                id="expense-category-error",
                                                                className="text-danger d-none"
                                                            ),
                                                        ],
                                                        md=4,
                                                    ),
                                                    dbc.Col(
                                                        [
                                                            dbc.Label(
                                                                ["Item Name ", html.Span("*", className="text-danger")],
                                                                html_for="expense-item-name"
                                                            ),
                                                            dbc.Input(
                                                                id="expense-item-name",
                                                                type="text",
                                                                placeholder="e.g., Groceries, Rent",
                                                            ),
                                                            html.Small(
                                                                id="expense-item-name-error",
                                                                className="text-danger d-none"
                                                            ),
                                                        ],
                                                        md=4,
                                                    ),
                                                    dbc.Col(
                                                        [
                                                            dbc.Label(
                                                                ["Amount ", html.Span("*", className="text-danger")],
                                                                html_for="expense-amount"
                                                            ),
                                                            dbc.Input(
                                                                id="expense-amount",
                                                                type="number",
                                                                step="0.01",
                                                                min=0,
                                                                placeholder="0.00",
                                                            ),
                                                            html.Small(
                                                                id="expense-amount-error",
                                                                className="text-danger d-none"
                                                            ),
                                                        ],
                                                        md=2,
                                                    ),
                                                    dbc.Col(
                                                        [
                                                            dbc.Label(
                                                                ["Currency ", html.Span("*", className="text-danger")],
                                                                html_for="expense-currency"
                                                            ),
                                                            dbc.Select(
                                                                id="expense-currency",
                                                                placeholder="Select...",
                                                            ),
                                                            html.Small(
                                                                id="expense-currency-error",
                                                                className="text-danger d-none"
                                                            ),
                                                        ],
                                                        md=2,
                                                    ),
                                                ],
                                                className="mb-3",
                                            ),
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        [
                                                            dbc.Label("Expense Date (Optional)", html_for="expense-date"),
                                                            dbc.Input(
                                                                id="expense-date",
                                                                type="date",
                                                            ),
                                                            html.Small(
                                                                id="expense-date-error",
                                                                className="text-danger d-none"
                                                            ),
                                                        ],
                                                        md=4,
                                                    ),
                                                    dbc.Col(
                                                        [
                                                            dbc.Label("Notes (Optional)", html_for="expense-notes"),
                                                            dbc.Textarea(
                                                                id="expense-notes",
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
                                                                id="expense-is-recurring",
                                                                label="Recurring Expense",
                                                                value=False,
                                                            ),
                                                            html.Small("(e.g., rent, subscriptions)", className="text-muted d-block ms-4"),
                                                        ],
                                                        md=12,
                                                    ),
                                                ],
                                                className="mb-3",
                                            ),
                                            dbc.Button(
                                                [
                                                    dbc.Spinner(
                                                        size="sm",
                                                        spinner_class_name="me-2",
                                                        id="expense-submit-spinner",
                                                        spinner_style={"display": "none"}
                                                    ),
                                                    html.Span("Add Expense", id="expense-submit-text")
                                                ],
                                                id="add-expense-btn",
                                                color="danger",
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
                    
                    # Expense List
                    dbc.Card(
                        [
                            dbc.CardHeader(
                                html.Div(
                                    [
                                        html.H4("Expense Entries", className="mb-0"),
                                        html.Small("Track all expenses for this period", className="text-muted")
                                    ]
                                )
                            ),
                            dbc.CardBody(
                                [
                                    dbc.Spinner(
                                        html.Div(id="expense-table-container"),
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
                            html.P("Are you sure you want to delete this expense entry?"),
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
                                id="expense-delete-cancel",
                                className="me-2",
                                color="secondary"
                            ),
                            dbc.Button(
                                "Delete",
                                id="expense-delete-confirm",
                                color="danger"
                            )
                        ]
                    )
                ],
                id="expense-delete-modal",
                is_open=False,
                centered=True
            ),
        ],
        fluid=True,
        className="py-4",
    )
