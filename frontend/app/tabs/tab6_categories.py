import dash_bootstrap_components as dbc
from dash import html, dcc, dash_table


def create_categories_tab_layout():
    """Create the Expense Categories Management tab layout."""
    
    return dbc.Container(
        [
            dbc.Card(
                [
                    dbc.CardHeader(html.H4("Add Expense Category")),
                    dbc.CardBody(
                        [
                            html.P(
                                "Create custom expense categories to organize your spending.",
                                className="text-muted mb-3",
                            ),
                            dbc.Alert(id="category-message", is_open=False, dismissable=True),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            dbc.Label("Category Name"),
                                            dbc.Input(id="category-name-input", type="text", placeholder="e.g., Groceries, Rent"),
                                        ],
                                        md=5,
                                    ),
                                    dbc.Col(
                                        [
                                            dbc.Label("Parent Category (Optional)"),
                                            dbc.Select(id="category-parent-input", options=[]),
                                        ],
                                        md=4,
                                    ),
                                    dbc.Col(
                                        [
                                            dbc.Label("Icon"),
                                            dbc.Input(id="category-description-input", type="text", placeholder="e.g. 🏠"),
                                        ],
                                        md=3,
                                    ),
                                ],
                                className="mb-3",
                            ),
                            dbc.Button("Add Category", id="add-category-btn", color="primary"),
                        ]
                    ),
                ],
                className="mb-4",
            ),
            dbc.Card(
                [
                    dbc.CardHeader(html.H4("Your Categories")),
                    dbc.CardBody([html.Div(id="category-table-container")]),
                ],
            ),
        ],
        fluid=True,
        className="py-4",
    )
