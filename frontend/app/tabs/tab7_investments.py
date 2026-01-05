import dash_bootstrap_components as dbc
from dash import dcc, html


def create_investments_tab_layout():
    """Create the layout for the Investments tab."""
    return dbc.Container(
        [
            html.H2("Global Investment Tracking", className="mb-4"),
            
            # --- Section 1: Investment Accounts ---
            dbc.Card(
                [
                    dbc.CardHeader(html.H4("1. Investment Accounts", className="mb-0")),
                    dbc.CardBody(
                        [
                            html.P(
                                "Manage your brokerage accounts, crypto exchanges, or physical storage locations.",
                                className="text-muted",
                            ),
                            # Form
                            dbc.Row(
                                [
                                    dbc.Col(
                                        dbc.Input(
                                            id="inv-account-name",
                                            placeholder="Account Name (e.g. IBKR)",
                                            type="text",
                                        ),
                                        md=3,
                                    ),
                                    dbc.Col(
                                        dbc.Select(
                                            id="inv-account-type",
                                            options=[
                                                {"label": "Brokerage", "value": "BROKERAGE"},
                                                {"label": "Crypto Exchange", "value": "CRYPTO_EXCHANGE"},
                                                {"label": "Physical Wallet/Safe", "value": "PHYSICAL"},
                                            ],
                                            placeholder="Type",
                                        ),
                                        md=3,
                                    ),
                                    dbc.Col(
                                        dbc.Input(
                                            id="inv-account-notes",
                                            placeholder="Notes (Optional)",
                                            type="text",
                                        ),
                                        md=4,
                                    ),
                                    dbc.Col(
                                        dbc.Button(
                                            "Add Account",
                                            id="add-inv-account-btn",
                                            color="primary",
                                            className="w-100",
                                        ),
                                        md=2,
                                    ),
                                ],
                                className="g-2 mb-4 align-items-center",
                            ),
                            # Message area
                            dbc.Collapse(
                                dbc.Alert(id="inv-account-message", dismissable=True),
                                id="inv-account-message-collapse",
                            ),
                            # Table
                            html.Div(id="inv-accounts-table-container"),
                        ]
                    ),
                ],
                className="mb-5 shadow-sm",
            ),
            
            # --- Section 2: Investment Categories (Holdings) ---
            dbc.Card(
                [
                    dbc.CardHeader(html.H4("2. Investment Categories", className="mb-0")),
                    dbc.CardBody(
                        [
                            html.P(
                                "Define what you are investing in (e.g. 'S&P 500 ETF', 'Bitcoin').",
                                className="text-muted",
                            ),
                            # Form
                            dbc.Row(
                                [
                                    dbc.Col(
                                        dbc.Input(
                                            id="inv-category-name",
                                            placeholder="Category Name",
                                            type="text",
                                        ),
                                        md=3,
                                    ),
                                    dbc.Col(
                                        dcc.Dropdown(
                                            id="inv-category-account-select",
                                            placeholder="Select Account",
                                            className="dash-bootstrap",
                                        ),
                                        md=3,
                                    ),
                                    dbc.Col(
                                        dbc.Input(
                                            id="inv-opening-balance",
                                            placeholder="Opening Balance (Optional)",
                                            type="number",
                                        ),
                                        md=2,
                                    ),
                                    dbc.Col(
                                        dcc.Dropdown(
                                            id="inv-opening-currency",
                                            placeholder="Currency",
                                            className="dash-bootstrap",
                                        ),
                                        md=2,
                                    ),
                                    dbc.Col(
                                        dbc.Input(
                                            id="inv-opening-date",
                                            type="date",
                                            placeholder="Date",
                                        ),
                                        md=2,
                                    ),
                                ],
                                className="g-2 mb-2",
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        dbc.Button(
                                            "Add Category",
                                            id="add-inv-category-btn",
                                            color="primary",
                                            className="w-100",
                                        ),
                                        md=2,
                                        className="offset-md-10",
                                    )
                                ],
                                className="mb-4",
                            ),
                            # Message area
                            dbc.Collapse(
                                dbc.Alert(id="inv-category-message", dismissable=True),
                                id="inv-category-message-collapse",
                            ),
                            # Table
                            html.Div(id="inv-categories-table-container"),
                        ]
                    ),
                ],
                className="mb-5 shadow-sm",
            ),
            
            # --- Section 3: Transfers (Cash -> Investment) ---
            dbc.Card(
                [
                    dbc.CardHeader(html.H4("3. Transfers to Investments", className="mb-0")),
                    dbc.CardBody(
                        [
                            html.P(
                                "Record money moved from your bank accounts to investments for this period.",
                                className="text-muted",
                            ),
                            # Period check
                            html.Div(id="inv-period-check-message", className="mb-3"),
                            
                            # Form
                            dbc.Row(
                                [
                                    dbc.Col(
                                        dcc.Dropdown(
                                            id="inv-transfer-category-select",
                                            placeholder="Investment Category",
                                            className="dash-bootstrap",
                                        ),
                                        md=3,
                                    ),
                                    dbc.Col(
                                        dbc.Input(
                                            id="inv-transfer-amount",
                                            placeholder="Amount (Cost)",
                                            type="number",
                                        ),
                                        md=2,
                                    ),
                                    dbc.Col(
                                        dbc.Input(
                                            id="inv-transfer-units",
                                            placeholder="Units Purchased (Optional)",
                                            type="number",
                                        ),
                                        md=2,
                                    ),
                                    dbc.Col(
                                        dcc.Dropdown(
                                            id="inv-transfer-currency",
                                            placeholder="Currency",
                                            className="dash-bootstrap",
                                        ),
                                        md=2,
                                    ),
                                    dbc.Col(
                                        dcc.Dropdown(
                                            id="inv-transfer-source-account",
                                            placeholder="Source Account",
                                            className="dash-bootstrap",
                                        ),
                                        md=3,
                                    ),
                                    dbc.Col(
                                        dbc.Input(
                                            id="inv-transfer-date",
                                            type="date",
                                        ),
                                        md=2,
                                    ),
                                ],
                                className="g-2 mb-2",
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        dbc.Input(
                                            id="inv-transfer-notes",
                                            placeholder="Notes (Optional)",
                                            type="text",
                                        ),
                                        md=10,
                                    ),
                                    dbc.Col(
                                        dbc.Button(
                                            "Record Transfer",
                                            id="add-inv-transfer-btn",
                                            color="success",
                                            className="w-100",
                                        ),
                                        md=2,
                                    ),
                                ],
                                className="g-2 mb-4",
                            ),
                            # Message area
                            dbc.Collapse(
                                dbc.Alert(id="inv-transfer-message", dismissable=True),
                                id="inv-transfer-message-collapse",
                            ),
                            # Table
                            html.Div(id="inv-transfers-table-container"),
                        ]
                    ),
                ],
                className="mb-4 shadow-sm",
            ),
        ],
        fluid=True,
        className="py-4",
    )
