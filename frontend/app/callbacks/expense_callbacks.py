import dash
from dash import Input, Output, State, html
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from dash import dash_table

from utils.api_client import APIClient


def register_expense_callbacks(app):
    """Register expense management callbacks."""
    
    api_client = APIClient()

    @app.callback(
        [
            Output("expense-form-container", "style"),
            Output("expense-category", "options"),
            Output("expense-currency", "options"),
            Output("expense-currency", "value"),
        ],
        [Input("current-period-id", "data"), Input("session-store", "data")],
    )
    def show_expense_form(period_id, session_data):
        """Show expense form and load categories/currencies when period is selected."""
        if not period_id or not session_data or "token" not in session_data:
            return {"display": "none"}, [], [], None

        token = session_data["token"]
        api_client.set_token(token)

        # Load categories
        categories_response = api_client.get("/expense-categories/")
        
        # Auto-init fallback for categories
        if not categories_response or (isinstance(categories_response, list) and len(categories_response) == 0):
            api_client.post("/expense-categories/initialize", {})
            categories_response = api_client.get("/expense-categories/")
            
        category_options = []
        if categories_response and "error" not in categories_response:
            category_options = [
                {"label": c.get("category_name", ""), "value": c.get("id", "")}
                for c in categories_response
            ]

        # Load currencies
        currencies_response = api_client.get("/currencies/")
        
        # Auto-init fallback for currencies
        if not currencies_response or (isinstance(currencies_response, list) and len(currencies_response) == 0):
            api_client.post("/currencies/initialize", {})
            currencies_response = api_client.get("/currencies/")
            
        currency_options = []
        default_currency_id = None
        if currencies_response and "error" not in currencies_response:
            for c in currencies_response:
                ticker = c.get('ticker', '')
                name = c.get('name', '')
                curr_id = c.get('id', '')
                currency_options.append({"label": f"{ticker} - {name}", "value": curr_id})
                if c.get("is_default"):
                    default_currency_id = curr_id
            
            # Fallback to first one if no default set
            if not default_currency_id and currency_options:
                default_currency_id = currency_options[0]["value"]

        return {"display": "block"}, category_options, currency_options, default_currency_id

    @app.callback(
        [
            Output("expense-message", "children"),
            Output("expense-message", "color"),
            Output("expense-message", "is_open"),
            Output("expense-category", "value"),
            Output("expense-item-name", "value"),
            Output("expense-amount", "value"),
            Output("expense-currency", "value", allow_duplicate=True),
            Output("expense-date", "value"),
            Output("expense-notes", "value"),
            Output("expense-tax-deductible", "value"),
            Output("expense-table-container", "children", allow_duplicate=True),
        ],
        [Input("add-expense-btn", "n_clicks")],
        [
            State("current-period-id", "data"),
            State("expense-category", "value"),
            State("expense-item-name", "value"),
            State("expense-amount", "value"),
            State("expense-currency", "value"),
            State("expense-date", "value"),
            State("expense-notes", "value"),
            State("expense-tax-deductible", "value"),
            State("session-store", "data"),
        ],
        prevent_initial_call=True,
    )
    def add_expense(
        n_clicks,
        period_id,
        category_id,
        item_name,
        amount,
        currency_id,
        expense_date,
        notes,
        tax_deductible,
        session_data,
    ):
        """Handle adding expense."""
        if not n_clicks:
            raise PreventUpdate

        # Validate inputs
        if not item_name or not amount or not currency_id or not category_id or not period_id:
            return (
                "Please fill in all required fields",
                "warning",
                True,
                category_id,
                item_name,
                amount,
                currency_id,
                expense_date,
                notes,
                tax_deductible,
                dash.no_update,
            )

        if not session_data or "token" not in session_data:
            return (
                "Please log in first",
                "danger",
                True,
                category_id,
                item_name,
                amount,
                currency_id,
                expense_date,
                notes,
                tax_deductible,
                dash.no_update,
            )

        token = session_data["token"]
        api_client.set_token(token)

        # Create expense entry
        payload = {
            "category_id": category_id,
            "item_name": item_name,
            "amount": float(amount),
            "currency_id": currency_id,
            "is_tax_deductible": tax_deductible or False,
        }
        
        if expense_date:
            payload["expense_date"] = expense_date
        if notes:
            payload["notes"] = notes

        response = api_client.post(f"/periods/{period_id}/expenses", payload)

        if "error" in response:
            return (
                f"Error adding expense: {response['error']}",
                "danger",
                True,
                category_id,
                item_name,
                amount,
                currency_id,
                expense_date,
                notes,
                tax_deductible,
                dash.no_update,
            )

        # Success - clear form and refresh table
        expenses_response = api_client.get(f"/periods/{period_id}/expenses")
        table = create_expense_table(expenses_response if "error" not in expenses_response else [], period_id, api_client)

        return (
            f"Expense '{item_name}' added successfully!",
            "success",
            True,
            None,  # Reset category
            "",  # Clear name
            "",  # Clear amount
            dash.no_update,  # Keep current currency
            "",  # Clear date
            "",  # Clear notes
            False,  # Reset checkbox
            table,
        )

    @app.callback(
        [
            Output("expense-message", "children", allow_duplicate=True),
            Output("expense-message", "color", allow_duplicate=True),
            Output("expense-message", "is_open", allow_duplicate=True),
            Output("expense-table-container", "children", allow_duplicate=True),
        ],
        [Input({"type": "delete-expense-btn", "id": dash.ALL}, "n_clicks")],
        [
            State("current-period-id", "data"),
            State("session-store", "data"),
        ],
        prevent_initial_call=True,
    )
    def delete_expense(n_clicks, period_id, session_data):
        """Handle deleting an expense."""
        ctx = dash.callback_context
        if not ctx.triggered or not any(n_clicks):
            raise PreventUpdate

        # Find which specific button was clicked
        triggered_prop = ctx.triggered[0]["prop_id"]
        import json
        prop_dict = json.loads(triggered_prop.split(".")[0])
        expense_id = prop_dict["id"]

        if not session_data or "token" not in session_data:
            return "Please log in first", "danger", True, dash.no_update

        api_client.set_token(session_data["token"])
        
        # Delete the expense
        response = api_client.delete(f"/expenses/{expense_id}")
        
        if "error" in response:
            return f"Error deleting expense: {response['error']}", "danger", True, dash.no_update

        # Success - refresh table
        expenses_response = api_client.get(f"/periods/{period_id}/expenses")
        
        # Fetch maps for table refresh
        categories = api_client.get("/expense-categories/")
        cat_map = {c["id"]: c["category_name"] for c in categories} if categories and "error" not in categories else {}
        currencies = api_client.get("/currencies/")
        cur_map = {c["id"]: c["ticker"] for c in currencies} if currencies and "error" not in currencies else {}

        table = create_expense_table(expenses_response if "error" not in expenses_response else [], period_id, api_client, cat_map, cur_map)

        return "Expense deleted successfully", "success", True, table

    @app.callback(
        Output("recon-trigger-store", "data", allow_duplicate=True),
        [Input("expense-table-container", "children")],
        prevent_initial_call=True
    )
    def trigger_recon_on_expense_change(child):
        from datetime import datetime
        return datetime.now().timestamp()

    @app.callback(
        Output("expense-table-container", "children"),
        [Input("current-period-id", "data"), Input("session-store", "data")],
    )
    def load_expense_table(period_id, session_data):
        """Load expense entries for selected period."""
        if not period_id or not session_data or "token" not in session_data:
            return html.Div("Select a period in the header to view expense entries", className="text-muted")

        token = session_data["token"]
        api_client.set_token(token)

        response = api_client.get(f"/periods/{period_id}/expenses")
        if "error" in response:
            return html.Div(f"Error loading expenses: {response['error']}", className="text-danger")

        # Fetch maps
        categories = api_client.get("/expense-categories/")
        cat_map = {c["id"]: c["category_name"] for c in categories} if categories and "error" not in categories else {}
        
        currencies = api_client.get("/currencies/")
        cur_map = {c["id"]: c["ticker"] for c in currencies} if currencies and "error" not in currencies else {}

        return create_expense_table(response, period_id, api_client, cat_map, cur_map)


from utils.ui_helpers import create_empty_state, format_currency

def create_expense_table(expense_entries, period_id, api_client, cat_map=None, cur_map=None):
    """Create a dbc.Table from expense entries."""
    if not expense_entries or len(expense_entries) == 0:
        return create_empty_state(
            "bi-cart-x",
            "No expenses recorded",
            "Keep track of your spending by adding your first expense above."
        )
    
    cat_map = cat_map or {}
    cur_map = cur_map or {}

    rows = []
    # Sort by recent first (if date present), or created_at
    # Assuming 'created_at' is in response or just use list order
    
    for entry in expense_entries:
        cat_name = cat_map.get(entry["category_id"], "Unknown")
        cur_code = cur_map.get(entry["currency_id"], "Unknown")
        exp_id = entry["id"]

        rows.append(
            html.Tr([
                html.Td(cat_name, className="fw-bold"),
                html.Td(entry["item_name"]),
                html.Td(format_currency(entry.get('amount', 0))),
                html.Td(cur_code),
                html.Td(entry.get("expense_date", "N/A")),
                html.Td([
                    # Edit/Delete buttons placeholders (actions)
                    dbc.Button(
                         html.I(className="bi bi-trash"),
                         id={"type": "delete-expense-btn", "id": exp_id},
                         color="outline-danger",
                         size="sm",
                         className="btn-rounded border-0"
                    )
                ], className="text-end")
            ])
        )

    return dbc.Table(
        [
            html.Thead(html.Tr([
                html.Th("Category"),
                html.Th("Item"),
                html.Th("Amount"),
                html.Th("Currency"),
                html.Th("Date"),
                html.Th("Action", className="text-end"),
            ])),
            html.Tbody(rows)
        ],
        bordered=False,
        hover=True,
        responsive=True,
        className="align-middle custom-table"
    )

