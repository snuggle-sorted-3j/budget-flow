import dash_bootstrap_components as dbc
from dash import html, dcc


def create_login_layout():
    """Create the login page layout."""
    return dbc.Container(
        [
            dbc.Row(
                dbc.Col(
                    [
                        html.Div(
                            [
                                html.H1("BudgetFlow", className="text-center mb-4"),
                                html.P(
                                    "Paycheck-to-Paycheck Budget Management",
                                    className="text-center text-muted mb-5",
                                ),
                            ]
                        ),
                        dbc.Card(
                            [
                                dbc.CardBody(
                                    [
                                        html.H4("Login", className="card-title mb-4"),
                                        dbc.Alert(
                                            id="login-error",
                                            color="danger",
                                            is_open=False,
                                            dismissable=True,
                                        ),
                                        dbc.Input(
                                            id="login-email",
                                            type="email",
                                            placeholder="Email",
                                            className="mb-3",
                                        ),
                                        dbc.Input(
                                            id="login-password",
                                            type="password",
                                            placeholder="Password",
                                            className="mb-3",
                                        ),
                                        dbc.Button(
                                            "Login",
                                            id="login-button",
                                            color="primary",
                                            className="w-100 mb-3",
                                        ),
                                        html.Hr(),
                                        html.Div(
                                            [
                                                html.Span("Don't have an account? "),
                                                dcc.Link(
                                                    "Register here",
                                                    href="/register",
                                                    className="text-primary",
                                                ),
                                            ],
                                            className="text-center",
                                        ),
                                    ]
                                )
                            ],
                            className="shadow",
                        ),
                    ],
                    width=12,
                    md=6,
                    lg=4,
                ),
                justify="center",
                className="min-vh-100 align-items-center",
            )
        ],
        fluid=True,
    )
