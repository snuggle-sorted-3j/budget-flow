"""Templates tab layout for managing reusable period structures."""
import dash_bootstrap_components as dbc
from dash import dcc, html
from utils.ui_helpers import create_empty_state


def create_templates_loader():
    """Skeleton loader for template cards."""
    return dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.Div(className="skeleton skeleton-title mb-3", style={"width": "60%", "height": "20px"}),
                html.Div(className="skeleton mb-2", style={"width": "40%", "height": "15px"}),
                html.Div(className="skeleton mb-4", style={"width": "100%", "height": "40px"}),
                html.Div(className="skeleton-button", style={"width": "100%", "height": "35px"}),
            ])
        ], className="dashboard-card mb-4"), md=6, lg=4) for _ in range(3)
    ])


def create_templates_tab_layout():
    """Main layout for the Templates tab."""
    return dbc.Container([
        # Header Section
        html.Div([
            html.H2([html.I(className="bi bi-layers-half me-3 text-primary"), "Template Library"], 
                   className="fw-bold mb-2"),
            html.P("Capture and reuse your best budget structures to save time every month.", 
                  className="text-muted"),
        ], className="mb-4 pt-4"),

        # Action Buttons / Quick Actions (Section 3)
        html.Div(id="quick-actions-container", className="mb-4"),

        dbc.Row([
            # Section 1: Create New Template
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5([html.I(className="bi bi-plus-circle me-2"), "Create New Template"], 
                               className="mb-0 fw-bold")
                    ], className="bg-white border-bottom-0 pt-4 px-4"),
                    dbc.CardBody([
                        html.Div(id="tpl-form-alert"),
                        
                        dbc.Form([
                            html.Div([
                                dbc.Label("Template Name", className="fw-bold small text-uppercase"),
                                dbc.Input(id="tpl-name", placeholder="e.g., Monthly Standard Setup", className="mb-3"),
                            ]),
                            
                            html.Div([
                                dbc.Label("Template Type", className="fw-bold small text-uppercase"),
                                dbc.RadioItems(
                                    options=[
                                        {"label": "Expense Categories Only", "value": "EXPENSE_CATEGORIES"},
                                        {"label": "Income Sources Only", "value": "INCOME_SOURCES"},
                                        {"label": "Full Template (Recommended)", "value": "FULL"},
                                    ],
                                    value="FULL",
                                    id="tpl-type",
                                    className="mb-3 custom-radio-group",
                                ),
                                html.Div("Full template saves categories + recurring income + recurring expenses.", 
                                        className="text-muted x-small mb-3 italic"),
                            ]),
                            
                            html.Div([
                                dbc.Label("Source Period", className="fw-bold small text-uppercase"),
                                dbc.Select(id="tpl-source-period", placeholder="Select period to copy from", className="mb-3"),
                            ]),
                            
                            dbc.Checkbox(
                                id="tpl-is-default",
                                label="Set as my default template",
                                value=False,
                                className="mb-4 small",
                            ),
                            
                            dbc.Button([
                                dbc.Spinner(size="sm", spinner_class_name="me-2", id="tpl-save-spinner", spinner_style={"display": "none"}),
                                "Save Template to Library"
                            ], id="tpl-save-btn", color="primary", className="w-100 fw-bold py-2 shadow-sm"),
                        ])
                    ], className="px-4 pb-4")
                ], className="dashboard-card h-100 border-0 shadow-sm")
            ], md=12, lg=5),

            # Section 2: Library (Section 2 & 4)
            dbc.Col([
                html.Div([
                    html.Div([
                        html.H5([html.I(className="bi bi-collection me-2 text-primary"), "Your Templates"], 
                               className="mb-0 fw-bold"),
                        html.Div(id="tpl-count-badge"),
                    ], className="d-flex justify-content-between align-items-center mb-3"),
                    
                    dcc.Loading(
                        id="tpl-library-loading",
                        type="default",
                        children=html.Div(id="tpl-library-container", children=create_templates_loader())
                    )
                ])
            ], md=12, lg=7),
        ], className="g-4 mb-5"),

        # Modals
        # Apply Modal
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("Apply Template"), close_button=True),
            dbc.ModalBody([
                html.Div(id="tpl-apply-modal-content"),
                html.Div(id="tpl-apply-form-alert"),
                
                dbc.Form([
                    html.Div([
                        dbc.Label("Target Period", className="fw-bold small text-uppercase"),
                        dbc.Select(id="tpl-apply-target-period", placeholder="Select period to populate"),
                        html.Div("Note: This will ADD data to the selected period. Existing data won't be deleted.", 
                                className="text-muted x-small mt-2 italic"),
                    ], className="mb-3"),
                    
                    dbc.Checkbox(
                        id="tpl-apply-create-new",
                        label="Wait, I want to create a NEW period and apply this",
                        value=False,
                        className="mb-3 small",
                    ),
                    
                    html.Div(id="tpl-new-period-form", style={"display": "none"}, children=[
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("New Period Name", className="fw-bold small text-uppercase"),
                                dbc.Input(id="tpl-new-period-name", placeholder="e.g., February 2026"),
                            ], md=12, className="mb-3"),
                            dbc.Col([
                                dbc.Label("Start Date", className="fw-bold small text-uppercase"),
                                dbc.Input(id="tpl-new-period-start", type="date"),
                            ], md=6, className="mb-3"),
                            dbc.Col([
                                dbc.Label("End Date", className="fw-bold small text-uppercase"),
                                dbc.Input(id="tpl-new-period-end", type="date"),
                            ], md=6, className="mb-3"),
                        ])
                    ])
                ])
            ]),
            dbc.ModalFooter([
                dbc.Button("Cancel", id="tpl-apply-cancel", color="light", className="px-4"),
                dbc.Button("Apply Template", id="tpl-apply-confirm", color="primary", className="px-4"),
            ])
        ], id="tpl-apply-modal", centered=True, size="lg"),

        # Delete Confirmation Modal
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("Delete Template")),
            dbc.ModalBody(id="tpl-delete-modal-body"),
            dbc.ModalFooter([
                dbc.Button("Cancel", id="tpl-delete-cancel", color="light"),
                dbc.Button("Delete Permanently", id="tpl-delete-confirm", color="danger"),
            ])
        ], id="tpl-delete-modal", centered=True),

        # Stores
        dcc.Store(id="tpl-refresh-trigger", data=0),
        dcc.Store(id="tpl-pending-apply-id"),
        dcc.Store(id="tpl-pending-delete-id"),
        html.Div(id="tpl-toast-container"),
        
    ], fluid=True, className="py-2")
