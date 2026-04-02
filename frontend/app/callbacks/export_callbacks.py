import dash
from dash import Input, Output, State, html, dcc
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import json
import base64
import pandas as pd
import io
from datetime import datetime

from utils.api_client import APIClient

def register_export_callbacks(app):
    """Register callbacks for the export & backup tab."""
    api_client = APIClient()

    # Populate period selector
    @app.callback(
        Output("export-period-select", "options"),
        [Input("url", "pathname"), Input("session-store", "data")],
    )
    def load_export_period_options(pathname, session_data):
        if not pathname or "/dashboard" not in pathname:
            raise PreventUpdate
        
        if not session_data or "token" not in session_data:
            return []

        try:
            api_client.set_token(session_data["token"])
            periods = api_client.get("/periods/")
            if isinstance(periods, list):
                return [{"label": p["period_name"], "value": p["id"]} for p in periods]
            return []
        except:
            return []

    # Export Period CSV
    @app.callback(
        Output("download-export-csv", "data"),
        Input("export-period-csv-btn", "n_clicks"),
        [State("export-period-select", "value"), State("session-store", "data")],
        prevent_initial_call=True
    )
    def export_period_csv(n_clicks, period_id, session_data):
        if not n_clicks or not period_id or not session_data:
            raise PreventUpdate
            
        try:
            api_client.set_token(session_data["token"])
            # Fetch period details to get a nice filename
            period = api_client.get(f"/periods/{period_id}")
            period_name = period.get("period_name", "Period") if isinstance(period, dict) else "Period"
            period_name = period_name.replace(" ", "_").replace("/", "-")

            import requests
            headers = {"Authorization": f"Bearer {session_data['token']}"}
            export_url = f"/export/period/{period_id}/csv"
            response = requests.get(f"{api_client.base_url}{export_url}", headers=headers)
            
            if response.status_code == 200:
                return dcc.send_bytes(
                    response.content, 
                    f"BudgetFlow_Transactions_{period_name}.csv",
                    type="text/csv"
                )
            return None
        except Exception as e:
            print(f"Export error: {e}")
            raise PreventUpdate

    # Export Reconciliation PDF
    @app.callback(
        Output("download-export-pdf", "data"),
        Input("export-recon-pdf-btn", "n_clicks"),
        [State("export-period-select", "value"), State("session-store", "data")],
        prevent_initial_call=True
    )
    def export_recon_pdf(n_clicks, period_id, session_data):
        if not n_clicks or not period_id or not session_data:
            raise PreventUpdate
            
        try:
            api_client.set_token(session_data["token"])
            period = api_client.get(f"/periods/{period_id}")
            period_name = period.get("period_name", "Period") if isinstance(period, dict) else "Period"
            period_name = period_name.replace(" ", "_").replace("/", "-")

            import requests
            headers = {"Authorization": f"Bearer {session_data['token']}"}
            export_url = f"/export/period/{period_id}/reconciliation-report"
            response = requests.get(f"{api_client.base_url}{export_url}", headers=headers)
            
            if response.status_code == 200:
                return dcc.send_bytes(
                    response.content, 
                    f"BudgetFlow_Reconciliation_{period_name}.pdf",
                    type="application/pdf"
                )
            return None
        except Exception as e:
            print(f"PDF Export error: {e}")
            raise PreventUpdate

    # Export Annual summary
    @app.callback(
        Output("download-export-annual", "data"),
        Input("export-annual-csv-btn", "n_clicks"),
        [State("export-year-input", "value"), State("session-store", "data")],
        prevent_initial_call=True
    )
    def export_annual_summary(n_clicks, year, session_data):
        if not n_clicks or not year or not session_data:
            raise PreventUpdate
            
        try:
            import requests
            headers = {"Authorization": f"Bearer {session_data['token']}"}
            export_url = f"/export/annual-summary?year={year}"
            response = requests.get(f"{api_client.base_url}{export_url}", headers=headers)
            
            if response.status_code == 200:
                return dcc.send_bytes(
                    response.content, 
                    f"BudgetFlow_Annual_Summary_{year}.csv",
                    type="text/csv"
                )
            return None
        except Exception as e:
            print(f"Annual export error: {e}")
            raise PreventUpdate

    # Full Backup
    @app.callback(
        Output("download-backup-json", "data"),
        Input("export-backup-btn", "n_clicks"),
        [State("session-store", "data")],
        prevent_initial_call=True
    )
    def create_full_backup(n_clicks, session_data):
        if not n_clicks or not session_data:
            raise PreventUpdate
            
        try:
            api_client.set_token(session_data["token"])
            data = api_client.get("/export/full-backup")
            filename = f"BudgetFlow_Backup_{datetime.now().strftime('%Y%m%d')}.json"
            return dcc.send_string(
                json.dumps(data, indent=2),
                filename,
                type="application/json"
            )
        except:
            raise PreventUpdate

    # Import logic
    @app.callback(
        [Output("import-file-name", "children"), Output("import-backup-btn", "disabled")],
        [Input("import-upload", "contents")],
        [State("import-upload", "filename")]
    )
    def update_import_file_info(contents, filename):
        if contents is None:
            return "No file selected", True
        return f"Selected: {filename}", False

    @app.callback(
        Output("import-status-container", "children"),
        Input("import-backup-btn", "n_clicks"),
        [State("import-upload", "contents"), State("session-store", "data")],
        prevent_initial_call=True
    )
    def import_backup(n_clicks, contents, session_data):
        if not n_clicks or not contents or not session_data:
            raise PreventUpdate
            
        try:
            content_type, content_string = contents.split(',')
            decoded = base64.b64decode(content_string)
            
            # Send to API
            import requests
            headers = {"Authorization": f"Bearer {session_data['token']}"}
            files = {'file': ('backup.json', decoded, 'application/json')}
            
            response = requests.post(f"{api_client.base_url}/export/import/backup", headers=headers, files=files)
            
            if response.status_code == 200:
                result = response.json()
                summary = result.get("summary", {})
                items = [
                    html.Li(f"{v} {k.replace('_imported', '').replace('_', ' ').title()}")
                    for k, v in summary.items() if v and v > 0
                ]
                return dbc.Alert([
                    html.H6("Successfully Imported!", className="fw-bold"),
                    html.Ul(items, className="mb-0 small") if items else html.P(
                        "No new data to import (all entries already exist).",
                        className="mb-0 small"
                    ),
                ], color="success")
            else:
                return dbc.Alert(f"Import failed: {response.text}", color="danger")
        except Exception as e:
            return dbc.Alert(f"Error during import: {str(e)}", color="danger")
