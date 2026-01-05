import dash_bootstrap_components as dbc
from dash import html, dcc, dash_table


def create_currencies_tab_layout():
    """Create the Currencies Management tab layout."""
    
    return dbc.Container(
        [
            dbc.Card(
                [
                    dbc.CardHeader(html.H4("Add Custom Currency")),
                    dbc.CardBody(
                        [
                            html.P(
                                "Add custom currencies (BTC, ETH, USDT, etc.). Major world currencies are already pre-initialized.",
                                className="text-muted mb-3",
                            ),
                            dbc.Alert(id="currency-message", is_open=False, dismissable=True),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            dbc.Label("Ticker"),
                                            dbc.Input(id="currency-ticker", type="text", placeholder="USD"),
                                        ],
                                        md=4,
                                    ),
                                    dbc.Col(
                                        [
                                            dbc.Label("Name"),
                                            dbc.Input(id="currency-name", type="text", placeholder="US Dollar"),
                                        ],
                                        md=6,
                                    ),
                                    dbc.Col(
                                        [
                                            dbc.Label("Default?"),
                                            dbc.Checkbox(id="currency-default", value=False),
                                        ],
                                        md=2,
                                        className="d-flex align-items-center justify-content-center",
                                    ),
                                ],
                                className="mb-3",
                            ),
                            dbc.Button("Add Currency", id="add-currency-btn", color="primary"),
                        ]
                    ),
                ],
                className="mb-4",
            ),
            dbc.Card(
                [
                    dbc.CardHeader(html.H4("Your Currencies")),
                    dbc.CardBody([html.Div(id="currency-table-container")]),
                ],
            ),
        ],
        fluid=True,
        className="py-4",
    )
