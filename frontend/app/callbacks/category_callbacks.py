import dash
from datetime import datetime
from dash import Input, Output, State, html, callback_context
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from utils.api_client import APIClient


def register_category_callbacks(app):
    api_client = APIClient()

    @app.callback(
        [
            Output("category-message", "children"),
            Output("category-message", "color"),
            Output("category-message", "is_open"),
            Output("category-name-input", "value"),
            Output("category-description-input", "value"),
            Output("category-parent-input", "value"),
            Output("category-parent-input", "options"),
            Output("category-table-container", "children"),
        ],
        [
            Input("add-category-btn", "n_clicks"),
            Input("url", "pathname"),
            Input({"type": "delete-category-btn", "id": dash.ALL}, "n_clicks"),
        ],
        [
            State("category-name-input", "value"),
            State("category-description-input", "value"),
            State("category-parent-input", "value"),
            State("session-store", "data"),
        ],
    )
    def handle_category_action(add_clicks, pathname, delete_clicks, name, description, parent_id, session_data):
        ctx = callback_context
        triggered_id = "unknown"
        if ctx.triggered:
            triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]
        
        if not session_data or "token" not in session_data:
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, [], html.Div("Please log in")

        api_client.set_token(session_data["token"])
        
        msg, color, open = dash.no_update, dash.no_update, dash.no_update
        
        # Handle "Add Category"
        if triggered_id == "add-category-btn":
            if not name:
                msg, color, open = "Please enter a category name", "warning", True
            else:
                payload = {
                    "category_name": name, 
                    "icon": description,
                    "parent_category_id": parent_id if parent_id else None
                }
                resp = api_client.post("/expense-categories/", payload)
                if "error" in resp:
                    msg, color, open = f"Error: {resp['error']}", "danger", True
                else:
                    msg, color, open = f"Category '{name}' added!", "success", True
                    name, description, parent_id = "", "", None

        # Handle "Delete Category"
        elif "btn" in triggered_id and "{" in triggered_id:
             try:
                 t_id = dash.callback_context.triggered_id
                 if isinstance(t_id, dict) and t_id.get("type") == "delete-category-btn":
                     cat_id = t_id.get("id")
                     resp = api_client.patch(f"/expense-categories/{cat_id}/deactivate", {}) 
                     
                     if "error" in resp:
                         msg, color, open = f"Error deleting: {resp['error']}", "danger", True
                     else:
                         msg, color, open = "Category deleted (archived)!", "success", True
             except Exception as e:
                 print(f"Error parsing delete: {e}")

        # Fetch Categories for Table and Dropdown
        categories = api_client.get("/expense-categories/")
        
        # Auto-initialize fallback if empty
        if isinstance(categories, list) and len(categories) == 0:
            api_client.post("/expense-categories/initialize", {})
            categories = api_client.get("/expense-categories/")

        if isinstance(categories, dict) and "error" in categories:
            table = html.Div(f"Error loading categories: {categories['error']}")
            parent_options = []
        else:
            cat_list = categories if isinstance(categories, list) else []
            table = create_category_table(cat_list)
            # Only top-level categories can be parents (prevent infinite depth for now as per PRD "Two-level")
            parent_options = [{"label": "--- Top Level ---", "value": ""}] + [
                {"label": c["category_name"], "value": c["id"]}
                for c in cat_list if not c.get("parent_category_id")
            ]
            
        return msg, color, open, name, description, parent_id, parent_options, table


def create_category_table(categories):
    """Create a table showing custom categories with visual nesting."""
    if not categories:
        from utils.ui_helpers import create_empty_state
        return create_empty_state("bi-tags", "No categories", "You haven't added any categories yet.")
        
    # Build a simple tree for 2 levels
    parents = [c for c in categories if not c.get("parent_category_id")]
    children_map = {}
    for c in categories:
        pid = c.get("parent_category_id")
        if pid:
            if pid not in children_map:
                children_map[pid] = []
            children_map[pid].append(c)
            
    rows = []
    # Sort parents by name
    for p in sorted(parents, key=lambda x: x.get("category_name", "")):
        is_system = p.get("is_system_category", False)
        # Parent row
        rows.append(
            html.Tr([
                html.Td([
                    html.I(className="bi bi-folder2-open me-2 text-primary"),
                    html.Span(p.get("category_name", ""), className="fw-bold")
                ]),
                html.Td(p.get("icon", "")),
                html.Td(
                    dbc.Badge("SYSTEM", color="info", className="status-pill") if is_system else dbc.Badge("CUSTOM", color="secondary", className="status-pill")
                ),
                html.Td(
                    dbc.Button(
                        html.I(className="bi bi-trash"),
                        id={"type": "delete-category-btn", "id": p["id"]},
                        color="outline-danger",
                        size="sm",
                        className="btn-rounded border-0",
                        disabled=is_system,
                    )
                , className="text-end")
            ], className="table-light")
        )
        
        # Child rows
        children = children_map.get(p["id"], [])
        for c in sorted(children, key=lambda x: x.get("category_name", "")):
            rows.append(
                html.Tr([
                    html.Td([
                        html.I(className="bi bi-arrow-return-right ms-4 me-2 text-muted"),
                        html.Span(c.get("category_name", ""))
                    ]),
                    html.Td(c.get("icon", ""), className="ps-4"),
                    html.Td(
                        dbc.Badge("CUSTOM", color="secondary", className="status-pill")
                    ),
                    html.Td(
                        dbc.Button(
                            html.I(className="bi bi-trash"),
                            id={"type": "delete-category-btn", "id": c["id"]},
                            color="outline-danger",
                            size="sm",
                            className="btn-rounded border-0",
                        )
                    , className="text-end")
                ])
            )
        
    return dbc.Table(
        [
            html.Thead(html.Tr([
                html.Th("Category Name"),
                html.Th("Icon/Notes"),
                html.Th("Source"),
                html.Th("Actions"),
            ])),
            html.Tbody(rows)
        ],
        bordered=False,
        hover=True,
        responsive=True,
        className="align-middle custom-table"
    )
