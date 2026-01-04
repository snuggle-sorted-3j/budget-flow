import dash_bootstrap_components as dbc
from dash import html, dcc, dash_table
from datetime import date


def create_period_tab_layout():
    """Create the Period Setup tab layout."""
    
    return dbc.Container(
        [
            # Section 1: Create New Period
            dbc.Card(
                [
                    dbc.CardHeader(html.H4("Create New Period")),
                    dbc.CardBody(
                        [
                            dbc.Alert(
                                id="period-create-message",
                                is_open=False,
                                dismissable=True,
                            ),
                            dbc.Form(
                                [
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                [
                                                    dbc.Label("Period Name"),
                                                    dbc.Input(
                                                        id="period-name-input",
                                                        type="text",
                                                        placeholder="e.g., January 2026",
                                                    ),
                                                ],
                                                md=12,
                                            ),
                                        ],
                                        className="mb-3",
                                    ),
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                [
                                                    dbc.Label("Start Date"),
                                                    dbc.Input(
                                                        id="period-start-date",
                                                        type="date",
                                                    ),
                                                ],
                                                md=6,
                                            ),
                                            dbc.Col(
                                                [
                                                    dbc.Label("End Date"),
                                                    dbc.Input(
                                                        id="period-end-date",
                                                        type="date",
                                                    ),
                                                ],
                                                md=6,
                                            ),
                                        ],
                                        className="mb-3",
                                    ),
                                    dbc.Button(
                                        "Create Period",
                                        id="create-period-btn",
                                        color="primary",
                                        className="mt-2",
                                    ),
                                ]
                            ),
                        ]
                    ),
                ],
                className="mb-4",
            ),
            # Section 2: Period List
            dbc.Card(
                [
                    dbc.CardHeader(html.H4("Your Periods")),
                    dbc.CardBody(
                        [
                            html.Div(id="period-table-container"),
                        ]
                    ),
                ],
            ),
        ],
        fluid=True,
        className="py-4",
    )
