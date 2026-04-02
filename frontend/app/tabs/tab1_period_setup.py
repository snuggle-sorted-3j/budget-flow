"""Enhanced Period Setup tab with comprehensive error handling and UX improvements."""
import dash_bootstrap_components as dbc
from dash import html, dcc


def create_period_tab_layout():
    """Create the Period Setup tab layout with enhanced UX."""
    
    return dbc.Container(
        [
            # Toast notifications container
            html.Div(id="period-toast-container"),
            
            # Store for pending deletion
            dcc.Store(id="period-pending-delete-id"),
            
            # Section 1: Create New Period
            dbc.Card(
                [
                    dbc.CardHeader(
                        html.Div(
                            [
                                html.H4("Create New Period", className="mb-0"),
                                html.Small("Define monitoring periods for budget tracking", className="text-muted")
                            ]
                        )
                    ),
                    dbc.CardBody(
                        [
                            # Alert container for form feedback
                            html.Div(id="period-form-alert"),
                            
                            dbc.Form(
                                [
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                [
                                                    dbc.Label(
                                                        ["Period Name ", html.Span("*", className="text-danger")],
                                                        html_for="period-name-input"
                                                    ),
                                                    dbc.Input(
                                                        id="period-name-input",
                                                        type="text",
                                                        placeholder="e.g., January 2026",
                                                    ),
                                                    html.Small(
                                                        id="period-name-error",
                                                        className="text-danger d-none"
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
                                                    dbc.Label(
                                                        ["Start Date ", html.Span("*", className="text-danger")],
                                                        html_for="period-start-date"
                                                    ),
                                                    dbc.Input(
                                                        id="period-start-date",
                                                        type="date",
                                                    ),
                                                    html.Small(
                                                        id="period-start-date-error",
                                                        className="text-danger d-none"
                                                    ),
                                                ],
                                                md=6,
                                            ),
                                            dbc.Col(
                                                [
                                                    dbc.Label(
                                                        ["End Date ", html.Span("*", className="text-danger")],
                                                        html_for="period-end-date"
                                                    ),
                                                    dbc.Input(
                                                        id="period-end-date",
                                                        type="date",
                                                    ),
                                                    html.Small(
                                                        id="period-end-date-error",
                                                        className="text-danger d-none"
                                                    ),
                                                    html.Small(
                                                        "End date will be used as snapshot date",
                                                        className="text-muted mt-1 d-block"
                                                    ),
                                                ],
                                                md=6,
                                            ),
                                        ],
                                        className="mb-3",
                                    ),
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                [
                                                    dbc.Checkbox(
                                                        id="period-apply-template-check",
                                                        label="Apply a template to this period",
                                                        value=False,
                                                        className="small text-muted",
                                                    ),
                                                ],
                                                md=12,
                                            ),
                                        ],
                                        className="mb-2",
                                    ),
                                    # Template selector — shown only when checkbox is checked
                                    html.Div(
                                        id="period-template-selector",
                                        children=[
                                            dbc.Row([
                                                dbc.Col([
                                                    dbc.Label("Select Template", html_for="period-template-dropdown", className="small"),
                                                    dbc.Select(
                                                        id="period-template-dropdown",
                                                        placeholder="Choose a template...",
                                                    ),
                                                    html.Div(id="period-template-preview", className="mt-2"),
                                                ], md=8),
                                            ]),
                                        ],
                                        style={"display": "none"},
                                        className="mb-4 ps-3 border-start border-primary",
                                    ),
                                    dbc.Button(
                                        [
                                            dbc.Spinner(
                                                size="sm",
                                                spinner_class_name="me-2",
                                                id="period-submit-spinner",
                                                spinner_style={"display": "none"}
                                            ),
                                            html.Span("Create Period", id="period-submit-text")
                                        ],
                                        id="create-period-btn",
                                        color="primary",
                                        className="mt-2",
                                        disabled=False
                                    ),
                                ]
                            ),
                        ]
                    ),
                ],
                className="mb-4 shadow-sm",
            ),
            
            # Section 2: Period List
            dbc.Card(
                [
                    dbc.CardHeader(
                        html.Div(
                            [
                                html.H4("Your Periods", className="mb-0"),
                                html.Small("Manage your budget monitoring periods", className="text-muted")
                            ]
                        )
                    ),
                    dbc.CardBody(
                        [
                            dbc.Spinner(
                                html.Div(id="period-table-container"),
                                color="primary",
                                type="border"
                            ),
                        ]
                    ),
                ],
                className="shadow-sm"
            ),
            
            # Confirmation modal for deletions
            dbc.Modal(
                [
                    dbc.ModalHeader(
                        dbc.ModalTitle(
                            [
                                html.I(className="bi bi-exclamation-triangle-fill text-warning me-2"),
                                "Confirm Deletion"
                            ]
                        )
                    ),
                    dbc.ModalBody(
                        [
                            html.P("Are you sure you want to delete this period?"),
                            html.P(
                                [
                                    html.I(className="bi bi-info-circle me-2"),
                                    html.Strong("This action cannot be undone and will delete all associated income, expenses, and reconciliation data.")
                                ],
                                className="text-danger mb-0"
                            )
                        ]
                    ),
                    dbc.ModalFooter(
                        [
                            dbc.Button(
                                "Cancel",
                                id="period-delete-cancel",
                                className="me-2",
                                color="secondary"
                            ),
                            dbc.Button(
                                "Delete",
                                id="period-delete-confirm",
                                color="danger"
                            )
                        ]
                    )
                ],
                id="period-delete-modal",
                is_open=False,
                centered=True
            ),
        ],
        fluid=True,
        className="py-4",
    )
