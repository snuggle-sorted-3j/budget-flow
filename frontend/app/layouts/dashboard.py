import dash_bootstrap_components as dbc
from dash import html, dcc


def create_dashboard_layout(user_email: str = "User"):
    """Create the dashboard layout with sidebar navigation."""
    
    sidebar = html.Div(
        [
            html.H2("BudgetFlow", className="text-white mb-4"),
            html.Hr(className="bg-light"),
            dbc.Nav(
                [
                    dbc.NavLink(
                        [html.I(className="bi bi-calendar3 me-2"), "Periods"],
                        href="/dashboard/periods",
                        active="exact",
                    ),
                    dbc.NavLink(
                        [html.I(className="bi bi-cash-coin me-2"), "Income"],
                        href="/dashboard/income",
                        active="exact",
                    ),
                    dbc.NavLink(
                        [html.I(className="bi bi-cart me-2"), "Expenses"],
                        href="/dashboard/expenses",
                        active="exact",
                    ),
                    dbc.NavLink(
                        [html.I(className="bi bi-calculator me-2"), "Reconciliation"],
                        href="/dashboard/reconciliation",
                        active="exact",
                    ),
                    dbc.NavLink(
                        [html.I(className="bi bi-wallet2 me-2"), "Accounts"],
                        href="/dashboard/accounts",
                        active="exact",
                    ),
                    dbc.NavLink(
                        [html.I(className="bi bi-currency-exchange me-2"), "Currencies"],
                        href="/dashboard/currencies",
                        active="exact",
                    ),
                ],
                vertical=True,
                pills=True,
            ),
        ],
        className="sidebar bg-dark text-white p-3",
        style={
            "position": "fixed",
            "top": 0,
            "left": 0,
            "bottom": 0,
            "width": "250px",
            "padding": "20px",
            "overflow": "auto",
        },
    )

    header = dbc.Navbar(
        dbc.Container(
            [
                html.Div(
                    [
                        html.I(className="bi bi-person-circle me-2"),
                        html.Span(user_email, className="me-3"),
                        dbc.Button(
                            [html.I(className="bi bi-box-arrow-right me-2"), "Logout"],
                            id="logout-button",
                            color="outline-light",
                            size="sm",
                        ),
                    ],
                    className="ms-auto d-flex align-items-center",
                ),
            ],
            fluid=True,
        ),
        color="light",
        light=True,
        className="mb-3",
        style={"marginLeft": "250px"},
    )

    content = html.Div(
        id="dashboard-content",
        style={"marginLeft": "250px", "padding": "20px"},
    )

    return html.Div([sidebar, header, content])
