import dash_bootstrap_components as dbc
from dash import html, dcc, dash_table


def create_income_tab_layout():
    """Create the Income Management tab layout."""
    
    return dbc.Container(
        [
            # Period Selector
            dbc.Card(
                [
                    dbc.CardHeader(html.H4("Select Period")),
                    dbc.CardBody(
                        [
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            dbc.Label("Period"),
                                            dbc.Select(
                                                id="income-period-selector",
                                                placeholder="Select a period...",
                                            ),
                                        ],
                                        md=6,
                                    ),
                                ],
                            ),
                        ]
                    ),
                ],
                className="mb-4",
            ),
            # Add Income Form (hidden until period selected)
            html.Div(
                id="income-form-container",
                children=[
                    dbc.Card(
                        [
                            dbc.CardHeader(html.H4("Add Income")),
                            dbc.CardBody(
                                [
                                    dbc.Alert(
                                        id="income-message",
                                        is_open=False,
                                        dismissable=True,
                                    ),
                                    dbc.Form(
                                        [
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        [
                                                            dbc.Label("Source Name"),
                                                            dbc.Input(
                                                                id="income-source-name",
                                                                type="text",
                                                                placeholder="e.g., Salary, Freelance",
                                                            ),
                                                        ],
                                                        md=6,
                                                    ),
                                                    dbc.Col(
                                                        [
                                                            dbc.Label("Amount"),
                                                            dbc.Input(
                                                                id="income-amount",
                                                                type="number",
                                                                step="0.01",
                                                                placeholder="0.00",
                                                            ),
                                                        ],
                                                        md=3,
                                                    ),
                                                    dbc.Col(
                                                        [
                                                            dbc.Label("Currency"),
                                                            dbc.Select(
                                                                id="income-currency",
                                                                placeholder="Select currency...",
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
                                                            dbc.Label("Income Date (Optional)"),
                                                            dbc.Input(
                                                                id="income-date",
                                                                type="date",
                                                            ),
                                                        ],
                                                        md=4,
                                                    ),
                                                    dbc.Col(
                                                        [
                                                            dbc.Label("Notes (Optional)"),
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
                                                "Add Income",
                                                id="add-income-btn",
                                                color="success",
                                                className="mt-2",
                                            ),
                                        ]
                                    ),
                                ]
                            ),
                        ],
                        className="mb-4",
                    ),
                    # Income List
                    dbc.Card(
                        [
                            dbc.CardHeader(html.H4("Income Entries")),
                            dbc.CardBody(
                                [
                                    html.Div(id="income-table-container"),
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
