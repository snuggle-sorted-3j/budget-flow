import dash_bootstrap_components as dbc
from dash import html, dcc, dash_table


def create_accounts_tab_layout():
    """Create the Accounts Management tab layout."""
    
    return dbc.Container(
        [
            dbc.Card(
                [
                    dbc.CardHeader(html.H4("Add Account")),
                    dbc.CardBody(
                        [
                            dbc.Alert(id="account-message", is_open=False, dismissable=True),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            dbc.Label("Account Name"),
                                            dbc.Input(id="account-name-input", type="text", placeholder="e.g. Main Bank Account"),
                                        ],
                                        md=3,
                                    ),
                                    dbc.Col(
                                        [
                                            dbc.Label("Type"),
                                            dbc.Select(
                                                id="account-type-select",
                                                options=[
                                                    {"label": "Bank Account", "value": "BANK"},
                                                    {"label": "Cash / Wallet", "value": "CASH"},
                                                ],
                                                value="BANK",
                                            ),
                                        ],
                                        md=2,
                                    ),
                                    dbc.Col(
                                        [
                                            dbc.Label("Currency"),
                                            dbc.Select(id="account-currency-select", placeholder="Select..."),
                                        ],
                                        md=2,
                                    ),
                                    dbc.Col(
                                        [
                                            dbc.Label("Opening Balance"),
                                            dbc.Input(id="account-opening-balance", type="number", value=0, step="0.01"),
                                            dbc.FormText("Balance at migration start", className="x-small"),
                                        ],
                                        md=2,
                                    ),
                                    dbc.Col(
                                        [
                                            dbc.Label("Opening Date"),
                                            dbc.Input(id="account-opening-date", type="date"),
                                        ],
                                        md=3,
                                    ),
                                ],
                                className="mb-3",
                            ),
                            dbc.Button("Add Account", id="add-account-btn", color="primary"),
                        ]
                    ),
                ],
                className="mb-4",
            ),
            dbc.Card(
                [
                    dbc.CardHeader(html.H4("Your Accounts")),
                    dbc.CardBody([html.Div(id="account-table-container")]),
                ],
            ),
        ],
        fluid=True,
        className="py-4",
    )
