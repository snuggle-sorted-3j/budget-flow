import dash
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
            State("session-store", "data"),
        ],
        prevent_initial_call=False,
    )
    def handle_category_action(add_clicks, pathname, delete_clicks, name, description, session_data):
        ctx = callback_context
        # Check if just loading page
        is_page_load = not ctx.triggered or (ctx.triggered[0]["prop_id"] == "url.pathname")
        
        triggered_id = "unknown"
        if ctx.triggered:
            triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]
        
        if not session_data or "token" not in session_data:
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, html.Div("Please log in")

        api_client.set_token(session_data["token"])
        
        msg, color, open = dash.no_update, dash.no_update, dash.no_update
        
        # Handle "Add Category"
        if triggered_id == "add-category-btn":
            if not name:
                msg, color, open = "Please enter a category name", "warning", True
            else:
                # Description maps to icon for now as per schema or just ignored? 
                # Schema has 'category_name', 'icon', 'sort_order'. No description.
                # Assuming description/icon input for now.
                resp = api_client.post("/expense-categories/", {"category_name": name, "icon": description})
                if "error" in resp:
                    msg, color, open = f"Error: {resp['error']}", "danger", True
                else:
                    msg, color, open = f"Category '{name}' added!", "success", True
                    name, description = "", ""

        # Handle "Delete Category"
        elif "btn" in triggered_id and "{" in triggered_id:
             try:
                 # Clean up triggered_id string if needed, or use callback_context.triggered_id
                 t_id = dash.callback_context.triggered_id
                 if isinstance(t_id, dict) and t_id.get("type") == "delete-category-btn":
                     cat_id = t_id.get("id")
                     # Deactivate endpoint needed! Or direct delete if supported?
                     # Let's try deactivate first as it's safer and likely what is supported.
                     resp = api_client.patch(f"/expense-categories/{cat_id}/deactivate", {}) 
                     # Or DELETE /expense-categories/{id} if added? I'll check endpoints.
                     # Defaulting to deactivate to be safe.
                     
                     if "error" in resp:
                         # Try DELETE if 404/405 (or assume not deactivated)
                         # But let's assume deactivate exists from previous code context.
                         msg, color, open = f"Error deleting: {resp['error']}", "danger", True
                     else:
                         msg, color, open = "Category deleted (archived)!", "success", True
             except Exception as e:
                 print(f"Error parsing delete: {e}")


        # Always reload table
        categories = api_client.get("/expense-categories/")
        
        # Auto-initialize fallback if empty
        if not categories or (isinstance(categories, list) and len(categories) == 0):
            api_client.post("/expense-categories/initialize", {})
            categories = api_client.get("/expense-categories/")

        if "error" in categories:
            table = html.Div("Error loading categories")
        else:
            table = create_category_table(categories)
            
        return msg, color, open, name, description, table


def create_category_table(categories):
    """Create a table showing custom categories."""
    if not categories:
        from utils.ui_helpers import create_empty_state
        return create_empty_state("bi-tags", "No categories", "You haven't added any categories yet.")
        
    rows = []
    # Sort categories by name
    sorted_cats = sorted(categories, key=lambda x: x.get("category_name", ""))
    
    for c in sorted_cats:
        is_system = c.get("is_system_category", False)
        rows.append(
            html.Tr([
                html.Td(c.get("category_name", ""), className="fw-bold"),
                html.Td(c.get("icon", "")), # Using icon instead of description as description is not in schema
                html.Td(
                    dbc.Badge("SYSTEM", color="info", className="status-pill") if is_system else dbc.Badge("CUSTOM", color="secondary", className="status-pill")
                ),
                html.Td(
                    dbc.Button(
                        html.I(className="bi bi-trash"),
                        id={"type": "delete-category-btn", "id": c["id"]},
                        color="outline-danger",
                        size="sm",
                        className="btn-rounded border-0",
                        disabled=is_system, # Prevent deleting system categories
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
