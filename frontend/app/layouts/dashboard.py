import dash_bootstrap_components as dbc
from dash import html, dcc


def create_dashboard_layout(user_email: str = "User"):
    """Create the dashboard layout with a sleek fixed sidebar."""
    
    sidebar = html.Div(
        [
            html.Div(
                [
                    html.I(className="bi bi-lightning-charge-fill me-2 text-primary"),
                    html.Span("BudgetFlow", className="fw-bold tracking-tight"),
                ],
                className="sidebar-brand d-flex align-items-center mb-4 px-3",
                style={"fontSize": "1.5rem", "color": "#fff"}
            ),
            html.Hr(className="bg-light opacity-25 mx-3"),
            dbc.Nav(
                [
                    dbc.NavLink(
                        [html.I(className="bi bi-speedometer2 me-3"), "Dashboard"],
                        href="/dashboard",
                        active="exact",
                        className="px-3"
                    ),
                    dbc.NavLink(
                        [html.I(className="bi bi-bar-chart-line me-3"), "Advanced Analytics"],
                        href="/dashboard/analytics-advanced",
                        active="exact",
                        className="px-3"
                    ),
                    html.Div("CORE FEATURES", className="nav-section-title px-3 mt-4 mb-2"),
                    dbc.NavLink(
                        [html.I(className="bi bi-calendar3 me-3"), "Periods"],
                        href="/dashboard/periods",
                        active="exact",
                        className="px-3"
                    ),
                    dbc.NavLink(
                        [html.I(className="bi bi-cash-coin me-3"), "Income"],
                        href="/dashboard/income",
                        active="exact",
                        className="px-3"
                    ),
                    dbc.NavLink(
                        [html.I(className="bi bi-cart me-3"), "Expenses"],
                        href="/dashboard/expenses",
                        active="exact",
                        className="px-3"
                    ),
                    dbc.NavLink(
                        [html.I(className="bi bi-calculator me-3"), "Reconciliation"],
                        href="/dashboard/reconciliation",
                        active="exact",
                        className="px-3"
                    ),
                    dbc.NavLink(
                        [html.I(className="bi bi-graph-up-arrow me-3"), "Investments"],
                        href="/dashboard/investments",
                        active="exact",
                        className="px-3"
                    ),
                    dbc.NavLink(
                        [html.I(className="bi bi-pause-circle me-3"), "Suspended"],
                        href="/dashboard/suspended",
                        active="exact",
                        className="px-3"
                    ),
                    dbc.NavLink(
                        [html.I(className="bi bi-credit-card me-3"), "Installments"],
                        href="/dashboard/installments",
                        active="exact",
                        className="px-3"
                    ),
                    dbc.NavLink(
                        [html.I(className="bi bi-arrow-left-right me-3"), "Conversions"],
                        href="/dashboard/conversions",
                        active="exact",
                        className="px-3"
                    ),
                    html.Div("SETTINGS", className="nav-section-title px-3 mt-4 mb-2"),
                    dbc.NavLink(
                        [html.I(className="bi bi-wallet2 me-3"), "Accounts"],
                        href="/dashboard/accounts",
                        active="exact",
                        className="px-3"
                    ),
                    dbc.NavLink(
                        [html.I(className="bi bi-currency-exchange me-3"), "Currencies"],
                        href="/dashboard/currencies",
                        active="exact",
                        className="px-3"
                    ),
                    dbc.NavLink(
                        [html.I(className="bi bi-tags me-3"), "Categories"],
                        href="/dashboard/categories",
                        active="exact",
                        className="px-3"
                    ),
                    dbc.NavLink(
                        [html.I(className="bi bi-layers-half me-3"), "Templates"],
                        href="/dashboard/templates",
                        active="exact",
                        className="px-3"
                    ),
                ],
                vertical=True,
                pills=True,
                className="flex-column flex-nowrap"
            ),
        ],
        className="sidebar",
    )

    header = dbc.Navbar(
        dbc.Container(
            [
                html.Div(
                    [
                        html.Span("Monitoring Period:", className="me-3 text-muted small fw-bold text-uppercase"),
                        dbc.Select(
                            id="global-period-selector",
                            placeholder="Select Period",
                            className="global-period-selector border-0 bg-light shadow-none",
                            style={"width": "220px"}
                        ),
                    ],
                    className="d-flex align-items-center me-auto",
                ),
                html.Div(
                    [
                        dbc.DropdownMenu(
                            [
                                dbc.DropdownMenuItem(
                                    [html.Div([
                                        html.Div(user_email.split("@")[0], className="fw-bold"),
                                        html.Div(user_email, className="small text-muted")
                                    ])],
                                    disabled=True,
                                ),
                                dbc.DropdownMenuItem(divider=True),
                                dbc.DropdownMenuItem(
                                    [html.I(className="bi bi-box-arrow-right me-2 text-danger"), "Sign Out"],
                                    id="logout-button",
                                    n_clicks=0,
                                ),
                            ],
                            nav=True,
                            in_navbar=True,
                            label=html.Div([
                                html.I(className="bi bi-person-circle fs-5 me-2"),
                                html.Span(user_email.split("@")[0], className="fw-semibold")
                            ], className="d-flex align-items-center user-dropdown-toggle"),
                            className="ms-auto",
                            align_end=True,
                        ),
                    ],
                    className="d-flex align-items-center",
                ),
            ],
            fluid=True,
        ),
        color="white",
        className="header-navbar sticky-top border-bottom py-2",
    )

    content = html.Div(
        [
            dcc.Store(id="current-period-id", storage_type="session"),
            dcc.Store(id="recon-trigger-store", data=0),
            dcc.Store(id="inv-trigger-refresh", data=0),
            html.Div(id="dashboard-content", className="fade-in"),
        ],
        className="main-content-wrapper"
    )

    return html.Div([sidebar, header, content], className="dashboard-container")
