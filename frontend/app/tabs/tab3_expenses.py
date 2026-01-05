import dash_bootstrap_components as dbc
from dash import html, dcc, dash_table


def create_expenses_tab_layout():
    """Create the Expenses Management tab layout."""
    
    return dbc.Container(
        [
            # Add Expense Form (hidden until period selected)
            html.Div(
                id="expense-form-container",
                children=[
                    # Live Reconciliation Summary
                    html.Div(id="expense-recon-summary", className="mb-4"),
                    dbc.Card(
                        [
                            dbc.CardHeader(html.H4("Add Expense")),
                            dbc.CardBody(
                                [
                                    dbc.Alert(
                                        id="expense-message",
                                        is_open=False,
                                        dismissable=True,
                                    ),
                                    dbc.Form(
                                        [
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        [
                                                            html.Div([
                                                                dbc.Label("Category"),
                                                                html.A("Manage", href="/dashboard/categories", className="float-end small text-decoration-none"),
                                                            ]),
                                                            dbc.Select(
                                                                id="expense-category",
                                                                placeholder="Select category...",
                                                            ),
                                                        ],
                                                        md=4,
                                                    ),
                                                    dbc.Col(
                                                        [
                                                            dbc.Label("Item Name"),
                                                            dbc.Input(
                                                                id="expense-item-name",
                                                                type="text",
                                                                placeholder="e.g., Groceries, Rent",
                                                            ),
                                                        ],
                                                        md=4,
                                                    ),
                                                    dbc.Col(
                                                        [
                                                            dbc.Label("Amount"),
                                                            dbc.Input(
                                                                id="expense-amount",
                                                                type="number",
                                                                step="0.01",
                                                                placeholder="0.00",
                                                            ),
                                                        ],
                                                        md=2,
                                                    ),
                                                    dbc.Col(
                                                        [
                                                            dbc.Label("Currency"),
                                                            dbc.Select(
                                                                id="expense-currency",
                                                                placeholder="Select...",
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
                                                            dbc.Label("Expense Date (Optional)"),
                                                            dbc.Input(
                                                                id="expense-date",
                                                                type="date",
                                                            ),
                                                        ],
                                                        md=4,
                                                    ),
                                                    dbc.Col(
                                                        [
                                                            dbc.Label("Notes (Optional)"),
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
                                                                id="expense-tax-deductible",
                                                                label="Tax Deductible",
                                                                value=False,
                                                            ),
                                                            dbc.FormText("Mark if this expense can be used for tax deductions (e.g., business expenses)."),
                                                        ],
                                                        md=4,
                                                    ),
                                                ],
                                                className="mb-3",
                                            ),
                                            dbc.Button(
                                                "Add Expense",
                                                id="add-expense-btn",
                                                color="danger",
                                                className="mt-2",
                                            ),
                                        ]
                                    ),
                                ]
                            ),
                        ],
                        className="mb-4",
                    ),
                    # Expenses List
                    dbc.Card(
                        [
                            dbc.CardHeader(html.H4("Expense Entries")),
                            dbc.CardBody(
                                [
                                    html.Div(id="expense-table-container"),
                                ]
                            ),
                        ],
                    ),
                ],
                style={"display": "none"},
            ),
        ],
        fluid=True,
        className="py-4",
    )
