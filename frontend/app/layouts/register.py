import dash_bootstrap_components as dbc
from dash import html, dcc


def create_register_layout():
    """Create the registration page layout."""
    return dbc.Container(
        [
            dbc.Row(
                dbc.Col(
                    [
                        html.Div(
                            [
                                html.H1("BudgetFlow", className="text-center mb-4"),
                                html.P(
                                    "Join us to start managing your budget!",
                                    className="text-center text-muted mb-5",
                                ),
                            ]
                        ),
                        dbc.Card(
                            [
                                dbc.CardBody(
                                    [
                                        html.H4("Register", className="card-title mb-4"),
                                        dbc.Alert(
                                            id="register-message",
                                            is_open=False,
                                            dismissable=True,
                                        ),
                                        dbc.Input(
                                            id="register-email",
                                            type="email",
                                            placeholder="Email",
                                            className="mb-3",
                                        ),
                                        dbc.Input(
                                            id="register-fullname",
                                            type="text",
                                            placeholder="Full Name",
                                            className="mb-3",
                                        ),
                                        dbc.Input(
                                            id="register-password",
                                            type="password",
                                            placeholder="Password",
                                            className="mb-3",
                                        ),
                                        dbc.Button(
                                            "Register",
                                            id="register-button",
                                            color="success",
                                            className="w-100 mb-3",
                                        ),
                                        html.Hr(),
                                        html.Div(
                                            [
                                                html.Span("Already have an account? "),
                                                dcc.Link(
                                                    "Login here",
                                                    href="/login",
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
