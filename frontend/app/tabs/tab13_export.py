from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
from utils.ui_helpers import create_empty_state

def create_export_tab_layout():
    """Create the Export & Backup tab layout."""
    return dbc.Container([
        html.Div([
            html.H2([html.I(className="bi bi-download me-3 text-primary"), "Export & Backup"], 
                   className="fw-bold mb-2"),
            html.P("Manage your data ownership with comprehensive export and backup options.", 
                  className="text-muted"),
        ], className="mb-4 pt-4"),

        dbc.Row([
            # Card: Export Data
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5([html.I(className="bi bi-file-earmark-arrow-down me-2"), "Export Data"], 
                               className="mb-0 fw-bold")
                    ], className="bg-white border-bottom-0 pt-4 px-4"),
                    dbc.CardBody([
                        html.Div([
                            dbc.Label("Period Export", className="fw-bold small text-uppercase mb-2"),
                            dbc.Select(id="export-period-select", placeholder="Select period to export", className="mb-3"),
                            dbc.ButtonGroup([
                                dbc.Button([html.I(className="bi bi-filetype-csv me-2"), "Export Period (CSV)"], 
                                          id="export-period-csv-btn", color="primary", outline=True, className="me-2"),
                                dbc.Button([html.I(className="bi bi-filetype-pdf me-2"), "Reconciliation Report (PDF)"], 
                                          id="export-recon-pdf-btn", color="info", outline=True),
                            ], className="w-100 mb-2"),
                            html.Div("Reconciliation reports are available for all periods, including drafts.", 
                                    className="text-muted x-small italic mb-4"),
                            
                            html.Hr(),
                            
                            dbc.Label("Annual Summary", className="fw-bold small text-uppercase mb-2"),
                            dbc.Row([
                                dbc.Col(dbc.Input(id="export-year-input", type="number", value=2026, min=2000, max=2100), width=4),
                                dbc.Col(dbc.Button([html.I(className="bi bi-calendar-check me-2"), "Export Annual Summary"], 
                                                 id="export-annual-csv-btn", color="secondary", className="w-100"), width=8),
                            ], className="align-items-center mb-3"),
                        ])
                    ], className="px-4 pb-4")
                ], className="dashboard-card h-100 border-0 shadow-sm")
            ], md=12, lg=6),

            # Card: Full Backup
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5([html.I(className="bi bi-database-fill-down me-2"), "Full Backup"], 
                               className="mb-0 fw-bold")
                    ], className="bg-white border-bottom-0 pt-4 px-4"),
                    dbc.CardBody([
                        html.P("Download a complete backup of all your financial data including periods, accounts, and all transactions.", 
                              className="mb-4"),
                        dbc.Button([html.I(className="bi bi-file-earmark-zip-fill me-2"), "Create Full Backup (JSON)"], 
                                  id="export-backup-btn", color="success", className="w-100 py-3 mb-3 fw-bold"),
                        dbc.Alert([
                            html.I(className="bi bi-exclamation-triangle-fill me-2"),
                            "Store this file securely. It contains all your sensitive financial data."
                        ], color="warning", className="small py-2")
                    ], className="px-4 pb-4")
                ], className="dashboard-card mb-4 border-0 shadow-sm"),

                # Card: Import Backup
                dbc.Card([
                    dbc.CardHeader([
                        html.H5([html.I(className="bi bi-database-fill-up me-2"), "Import Backup"], 
                               className="mb-0 fw-bold")
                    ], className="bg-white border-bottom-0 pt-4 px-4"),
                    dbc.CardBody([
                        dcc.Upload(
                            id='import-upload',
                            children=html.Div([
                                html.I(className="bi bi-cloud-upload fs-2 text-primary mb-2 d-block"),
                                'Drag and Drop or ',
                                html.A('Select Backup File', className="text-primary fw-bold")
                            ], className="py-4 border-dashed rounded text-center"),
                            multiple=False,
                            className="mb-3"
                        ),
                        html.Div(id="import-file-name", className="text-muted small mb-3 text-center"),
                        dbc.Button("Import Backup", id="import-backup-btn", color="primary", className="w-100", disabled=True),
                        html.Div(id="import-status-container", className="mt-3")
                    ], className="px-4 pb-4")
                ], className="dashboard-card border-0 shadow-sm")
            ], md=12, lg=6),
        ], className="g-4 mb-5"),

        # Download components
        dcc.Download(id="download-export-csv"),
        dcc.Download(id="download-export-pdf"),
        dcc.Download(id="download-export-annual"),
        dcc.Download(id="download-backup-json"),
        
    ], fluid=True, className="py-2")
