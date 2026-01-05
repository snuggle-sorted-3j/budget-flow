import dash_bootstrap_components as dbc
from dash import html, dcc

def create_dashboard_home_layout():
    """Create the Dashboard Home layout."""
    return dbc.Container(
        [
            # Section 1: Current Period Overview
            html.Div(id="dashboard-period-overview"),
            
            # Section 2: Financial Summary
            html.Div(id="dashboard-financial-summary"),
            
            # Section 3: Quick Stats
            html.Div(id="dashboard-quick-stats"),

            # Section 4: Period List
            dbc.Card(
                [
                    dbc.CardHeader(html.H5("Recent Periods", className="mb-0 fw-bold")),
                    dbc.CardBody(
                        [
                            html.Div(id="dashboard-period-list-container"),
                        ],
                        className="p-0" # Remove padding for cleaner table look
                    ),
                ],
                className="mb-5 shadow-sm border-0",
            ),
        ],
        fluid=True,
        className="py-4",
    )
