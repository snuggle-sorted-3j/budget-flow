"""Callbacks for Template management and application."""
from datetime import datetime
import dash
from dash import Input, Output, State, html, dcc, ALL, ctx
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import uuid

from utils.api_client import APIClient
from utils.ui_helpers import create_empty_state, create_toast
from utils.error_handler import (
    display_error,
    display_success,
    display_warning,
    validate_required_fields,
    parse_api_error
)

def register_template_callbacks(app):
    api_client = APIClient()

    # --- 1. Initial Load & Refresh ---
    @app.callback(
        [
            Output("tpl-source-period", "options"),
            Output("tpl-apply-target-period", "options"),
            Output("tpl-library-container", "children"),
            Output("tpl-count-badge", "children"),
            Output("quick-actions-container", "children"),
        ],
        [
            Input("url", "pathname"),
            Input("tpl-refresh-trigger", "data"),
        ],
        [State("session-store", "data")]
    )
    def load_templates_tab_data(pathname, refresh, session_data):
        if not pathname or "templates" not in pathname:
            raise PreventUpdate
        
        if not session_data or "token" not in session_data:
            return [], [], [html.Div("Please log in")], None, None

        api_client.set_token(session_data["token"])
        
        # A. Get Periods for dropdowns
        periods = api_client.get("/periods/")
        period_opts = []
        if isinstance(periods, list):
            periods.sort(key=lambda x: x["start_date"], reverse=True)
            period_opts = [{"label": f"{p['period_name']} ({p['start_date']})", "value": p["id"]} for p in periods]

        # B. Get Templates
        templates = api_client.get("/templates/")
        if "error" in templates:
            return period_opts, period_opts, display_error(templates), None, None

        if not templates:
            empty_state = create_empty_state(
                "bi-collection", 
                "No Templates Yet", 
                "Capture your first period structure to reuse it later."
            )
            return period_opts, period_opts, empty_state, dbc.Badge("0", color="secondary"), None

        # C. Build Template Cards
        template_cards = []
        default_tpl = None
        for tpl in templates:
            if tpl.get("is_default"):
                default_tpl = tpl
            
            # Extract preview info
            data = tpl.get("template_data", {})
            cats_count = len(data.get("categories", []))
            income_count = len(data.get("income_sources", []))
            exp_count = len(data.get("recurring_expenses", []))
            
            type_colors = {
                "EXPENSE_CATEGORIES": "info",
                "INCOME_SOURCES": "success",
                "FULL": "primary"
            }
            
            card = dbc.Col(
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.H5(tpl["template_name"], className="card-title fw-bold mb-1 text-truncate"),
                            html.Div([
                                dbc.Badge(tpl["template_type"], color=type_colors.get(tpl["template_type"], "secondary"), className="me-2 small"),
                                html.Span("⭐", className="text-warning") if tpl.get("is_default") else None
                            ])
                        ], className="mb-3"),
                        
                        html.Div([
                            html.Div([
                                html.I(className="bi bi-tag me-2"), 
                                f"{cats_count} Categories"
                            ], className="small text-muted mb-1"),
                            html.Div([
                                html.I(className="bi bi-cash-stack me-2"), 
                                f"{income_count} Income Sources"
                            ], className="small text-muted mb-1") if tpl["template_type"] != "EXPENSE_CATEGORIES" else None,
                            html.Div([
                                html.I(className="bi bi-arrow-repeat me-2"), 
                                f"{exp_count} Recurring Expenses"
                            ], className="small text-muted mb-3") if tpl["template_type"] == "FULL" else None,
                        ]),
                        
                        html.Div("Created: " + tpl.get("created_at", "").split("T")[0], className="x-small text-muted mb-4 italic"),
                        
                        html.Div([
                            dbc.Button("Apply to Period", id={"type": "tpl-apply-btn", "index": tpl["id"]}, color="primary", size="sm", className="me-2 flex-grow-1"),
                            dbc.DropdownMenu([
                                dbc.DropdownMenuItem("Set as Default", id={"type": "tpl-default-btn", "index": tpl["id"]}) if not tpl.get("is_default") else None,
                                dbc.DropdownMenuItem("Delete Template", id={"type": "tpl-delete-trigger", "index": tpl["id"]}, className="text-danger"),
                            ], label=html.I(className="bi bi-three-dots-vertical"), nav=True, caret=False, in_navbar=False, align_end=True, className="btn-group", toggle_style={"padding": "0 8px"})
                        ], className="d-flex align-items-center")
                    ])
                ], className=f"dashboard-card h-100 {'border-primary border-2 shadow-sm' if tpl.get('is_default') else 'border-0 shadow-sm'}"),
                md=6, lg=4, className="mb-4"
            )
            template_cards.append(card)

        # D. Quick Actions
        quick_actions = None
        if default_tpl:
            quick_actions = dbc.Alert([
                html.Div([
                    html.Div([
                        html.Strong("Quick Start: "),
                        f"Your default template '{default_tpl['template_name']}' is ready."
                    ]),
                    dbc.Button([
                        html.I(className="bi bi-lightning-fill me-2"), 
                        "Create New Period from Default"
                    ], id={"type": "tpl-quick-btn", "index": "default"}, color="primary", size="sm", className="mt-2 mt-md-0 shadow-sm fw-bold")
                ], className="d-flex flex-column flex-md-row justify-content-between align-items-center")
            ], color="primary", className="border-0 shadow-sm py-3 px-4")

        return period_opts, period_opts, dbc.Row(template_cards), dbc.Badge(str(len(templates)), color="primary", pill=True), quick_actions

    # --- 2. Save Template ---
    @app.callback(
        [
            Output("tpl-form-alert", "children"),
            Output("tpl-name", "value"),
            Output("tpl-refresh-trigger", "data"),
            Output("tpl-save-spinner", "spinner_style"),
            Output("tpl-toast-container", "children"),
        ],
        [Input("tpl-save-btn", "n_clicks")],
        [
            State("tpl-name", "value"),
            State("tpl-type", "value"),
            State("tpl-source-period", "value"),
            State("tpl-is-default", "value"),
            State("session-store", "data")
        ],
        prevent_initial_call=True
    )
    def save_template(n_clicks, name, t_type, source_id, is_default, session_data):
        if not n_clicks: raise PreventUpdate
        
        is_valid, _ = validate_required_fields(name=name, type=t_type, period=source_id)
        if not is_valid:
            return display_warning("Please fill all required fields"), dash.no_update, dash.no_update, {"display": "none"}, None
            
        api_client.set_token(session_data["token"])
        try:
            payload = {
                "template_name": name,
                "template_type": t_type,
                "source_period_id": source_id,
                "is_default": is_default
            }
            res = api_client.post("/templates/from-period", payload)
            if "error" in res:
                return display_error(res), dash.no_update, dash.no_update, {"display": "none"}, None
            
            # If set as default, we need to PATCH it separately if the backend POST doesn't handle is_default 
            # (The user request said TemplateCreate should have is_default though)
            if is_default and res.get("id"):
                api_client.patch(f"/templates/{res['id']}", {"is_default": True})

            toast = create_toast(f"Template '{name}' saved successfully", icon="bi-check-circle", color="success")
            return None, "", datetime.now().timestamp(), {"display": "none"}, toast
        except Exception as e:
            return display_error(f"Error: {str(e)}"), dash.no_update, dash.no_update, {"display": "none"}, None

    # --- 3. Toggle Apply Modal ---
    @app.callback(
        [
            Output("tpl-apply-modal", "is_open"),
            Output("tpl-pending-apply-id", "data"),
            Output("tpl-apply-modal-content", "children"),
        ],
        [
            Input({"type": "tpl-apply-btn", "index": ALL}, "n_clicks"),
            Input("tpl-apply-cancel", "n_clicks"),
            Input({"type": "tpl-quick-btn", "index": ALL}, "n_clicks"),
        ],
        [
            State("session-store", "data"),
        ],
        prevent_initial_call=True
    )
    def toggle_apply_modal(btn_clicks, cancel_clicks, quick_clicks, session_data):
        trig = ctx.triggered_id
        if not trig: raise PreventUpdate
        
        # Check if actually clicked
        if isinstance(trig, dict):
            if trig["type"] == "tpl-apply-btn" and not any(btn_clicks): raise PreventUpdate
            if trig["type"] == "tpl-quick-btn" and not any(quick_clicks): raise PreventUpdate
        elif trig == "tpl-apply-cancel":
            if not cancel_clicks: raise PreventUpdate
        
        if trig == "tpl-apply-cancel":
            return False, None, ""

        api_client.set_token(session_data["token"])
        
        if isinstance(trig, dict) and trig.get("type") == "tpl-quick-btn":
            # Find default template ID
            templates = api_client.get("/templates/")
            default_tpl = next((t for t in templates if t.get("is_default")), None)
            if not default_tpl:
                 return False, None, ""
            return True, default_tpl["id"], html.H6(f"Creating period from default: {default_tpl['template_name']}", className="mb-3")

        if isinstance(trig, dict) and trig["type"] == "tpl-apply-btn":
            tpl_id = trig["index"]
            tpl = api_client.get(f"/templates/") # Could be optimized if we have GET /templates/{id}
            # Finding name from the list for the UI
            tpl_name = "Selected Template"
            if isinstance(tpl, list):
                 curr = next((t for t in tpl if t["id"] == tpl_id), None)
                 if curr: tpl_name = curr["template_name"]
            
            return True, tpl_id, html.H6(f"Template: {tpl_name}", className="mb-3")
            
        return dash.no_update, dash.no_update, dash.no_update

    @app.callback(
        Output("tpl-new-period-form", "style"),
        [Input("tpl-apply-create-new", "value")]
    )
    def show_new_period_form(create_new):
        return {"display": "block"} if create_new else {"display": "none"}

    # --- 4. Apply Template ---
    @app.callback(
        [
            Output("tpl-apply-form-alert", "children"),
            Output("tpl-apply-modal", "is_open", allow_duplicate=True),
            Output("tpl-toast-container", "children", allow_duplicate=True),
            Output("url", "pathname", allow_duplicate=True),
        ],
        [Input("tpl-apply-confirm", "n_clicks")],
        [
            State("tpl-pending-apply-id", "data"),
            State("tpl-apply-target-period", "value"),
            State("tpl-apply-create-new", "value"),
            State("tpl-new-period-name", "value"),
            State("tpl-new-period-start", "value"),
            State("tpl-new-period-end", "value"),
            State("session-store", "data")
        ],
        prevent_initial_call=True
    )
    def handle_template_application(n_clicks, tpl_id, target_id, create_new, new_name, start_date, end_date, session_data):
        if not n_clicks or not tpl_id: raise PreventUpdate
        
        api_client.set_token(session_data["token"])
        
        try:
            period_id = target_id
            
            # 1. Create period if needed
            if create_new:
                is_p_valid, _ = validate_required_fields(name=new_name, start=start_date, end=end_date)
                if not is_p_valid:
                    return display_warning("Please fill all period details"), True, dash.no_update, dash.no_update
                
                period_res = api_client.post("/periods/", {
                    "period_name": new_name,
                    "start_date": start_date,
                    "end_date": end_date
                })
                if "error" in period_res:
                    return display_error(period_res), True, dash.no_update, dash.no_update
                period_id = period_res["id"]

            if not period_id:
                return display_warning("Please select a target period"), True, dash.no_update, dash.no_update

            # 2. Apply template
            apply_res = api_client.post(f"/templates/{tpl_id}/apply", {"target_period_id": period_id})
            if "error" in apply_res:
                return display_error(apply_res), True, dash.no_update, dash.no_update
            
            summary = f"Applied! Created {apply_res.get('categories', 0)} cats, {apply_res.get('income_sources', 0)} inc, {apply_res.get('expenses', 0)} exp."
            toast = create_toast(summary, icon="bi-check-all", color="success")
            
            # Redirect to periods or stay
            return None, False, toast, "/dashboard/periods"
            
        except Exception as e:
            return display_error(f"Error: {str(e)}"), True, dash.no_update, dash.no_update

    # --- 5. Set Default ---
    @app.callback(
        [
            Output("tpl-refresh-trigger", "data", allow_duplicate=True),
            Output("tpl-toast-container", "children", allow_duplicate=True),
        ],
        [Input({"type": "tpl-default-btn", "index": ALL}, "n_clicks")],
        [State("session-store", "data")],
        prevent_initial_call=True
    )
    def set_default_template(clicks, session_data):
        trig = ctx.triggered_id
        if not trig or not any(clicks): raise PreventUpdate
        
        tpl_id = trig["index"]
        api_client.set_token(session_data["token"])
        try:
            res = api_client.patch(f"/templates/{tpl_id}", {"is_default": True})
            if "error" in res:
                 return dash.no_update, create_toast(parse_api_error(res), color="danger")
            
            return datetime.now().timestamp(), create_toast("Default template updated", icon="bi-star-fill")
        except Exception as e:
            return dash.no_update, create_toast(str(e), color="danger")

    # --- 6. Delete Logic ---
    @app.callback(
        [
            Output("tpl-delete-modal", "is_open"),
            Output("tpl-pending-delete-id", "data"),
            Output("tpl-delete-modal-body", "children"),
        ],
        [
            Input({"type": "tpl-delete-trigger", "index": ALL}, "n_clicks"),
            Input("tpl-delete-cancel", "n_clicks"),
        ],
        prevent_initial_call=True
    )
    def toggle_delete_modal(trig_clicks, cancel_clicks):
        trig = ctx.triggered_id
        if not trig: raise PreventUpdate
        
        # Ensure it was a real click
        if isinstance(trig, dict) and not any(trig_clicks):
            raise PreventUpdate
        if trig == "tpl-delete-cancel" and not cancel_clicks:
            raise PreventUpdate
        
        if trig == "tpl-delete-cancel":
            return False, None, ""
        
        if isinstance(trig, dict) and trig["type"] == "tpl-delete-trigger":
            return True, trig["index"], f"Are you sure you want to delete this template? This cannot be undone."
            
        return dash.no_update, dash.no_update, dash.no_update

    @app.callback(
        [
            Output("tpl-refresh-trigger", "data", allow_duplicate=True),
            Output("tpl-delete-modal", "is_open", allow_duplicate=True),
            Output("tpl-toast-container", "children", allow_duplicate=True),
        ],
        [Input("tpl-delete-confirm", "n_clicks")],
        [State("tpl-pending-delete-id", "data"), State("session-store", "data")],
        prevent_initial_call=True
    )
    def confirm_delete_template(n_clicks, tpl_id, session_data):
        if not n_clicks or not tpl_id: raise PreventUpdate
        
        api_client.set_token(session_data["token"])
        try:
            res = api_client.delete(f"/templates/{tpl_id}")
            if "error" in res:
                 return dash.no_update, False, create_toast(parse_api_error(res), color="danger")
            
            return datetime.now().timestamp(), False, create_toast("Template deleted", icon="bi-trash")
        except Exception as e:
            return dash.no_update, False, create_toast(str(e), color="danger")
