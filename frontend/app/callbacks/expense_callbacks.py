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
        Output("expense-period-selector", "options"),
        [Input("url", "pathname"), Input("session-store", "data")],
    )
    def load_expense_periods(pathname, session_data):
        """Load periods for expense dropdown."""
        if not pathname or not pathname.startswith("/dashboard"):
            raise PreventUpdate

        if not session_data or "token" not in session_data:
            return []

        token = session_data["token"]
        api_client.set_token(token)

        response = api_client.get("/periods/")

        if "error" in response:
            return []

        return [
            {"label": p.get("period_name", ""), "value": p.get("id", "")}
            for p in response
        ]

    @app.callback(
        [
            Output("expense-form-container", "style"),
            Output("expense-category", "options"),
            Output("expense-currency", "options"),
        ],
        [Input("expense-period-selector", "value"), Input("session-store", "data")],
    )
    def show_expense_form(period_id, session_data):
        """Show expense form and load categories/currencies when period is selected."""
        if not period_id or not session_data or "token" not in session_data:
            return {"display": "none"}, [], []

        token = session_data["token"]
        api_client.set_token(token)

        # Load categories
        categories_response = api_client.get("/categories/")
        category_options = []
        if "error" not in categories_response:
            category_options = [
                {"label": c.get("category_name", ""), "value": c.get("id", "")}
                for c in categories_response
            ]

        # Load currencies
        currencies_response = api_client.get("/currencies/")
        currency_options = []
        if "error" not in currencies_response:
            currency_options = [
                {"label": f"{c.get('currency_code', '')} - {c.get('currency_name', '')}", "value": c.get("id", "")}
                for c in currencies_response
            ]

        return {"display": "block"}, category_options, currency_options

    @app.callback(
        [
            Output("expense-message", "children"),
            Output("expense-message", "color"),
            Output("expense-message", "is_open"),
            Output("expense-category", "value"),
            Output("expense-item-name", "value"),
            Output("expense-amount", "value"),
            Output("expense-currency", "value"),
            Output("expense-date", "value"),
            Output("expense-notes", "value"),
            Output("expense-tax-deductible", "value"),
            Output("expense-table-container", "children", allow_duplicate=True),
        ],
        [Input("add-expense-btn", "n_clicks")],
        [
            State("expense-period-selector", "value"),
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
    def add_expense(n_clicks, period_id, category_id, item_name, amount, currency_id, expense_date, notes, tax_deductible, session_data):
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
            None,  # Clear category
            "",  # Clear item name
            "",  # Clear amount
            None,  # Clear currency
            "",  # Clear date
            "",  # Clear notes
            False,  # Reset checkbox
            table,
        )

    @app.callback(
        Output("expense-table-container", "children"),
        [Input("expense-period-selector", "value"), Input("session-store", "data")],
    )
    def load_expense_table(period_id, session_data):
        """Load expense entries for selected period."""
        if not period_id or not session_data or "token" not in session_data:
            return html.Div("Select a period to view expense entries", className="text-muted")

        token = session_data["token"]
        api_client.set_token(token)

        response = api_client.get(f"/periods/{period_id}/expenses")

        if "error" in response:
            return html.Div(f"Error loading expenses: {response['error']}", className="text-danger")

        return create_expense_table(response, period_id, api_client)


def create_expense_table(expense_entries, period_id, api_client):
    """Create a DataTable from expense entries."""
    if not expense_entries or len(expense_entries) == 0:
        return html.Div(
            "No expense entries found. Add your first expense above!",
            className="text-muted text-center py-4",
        )

    # Prepare data for table
    table_data = [
        {
            "category": entry.get("category_name", ""),
            "item_name": entry.get("item_name", ""),
            "amount": f"{entry.get('amount', 0):.2f}",
            "currency": entry.get("currency_code", ""),
            "date": entry.get("expense_date", "N/A"),
            "id": entry.get("id", ""),
        }
        for entry in expense_entries
    ]

    return dash_table.DataTable(
        id="expense-table",
        columns=[
            {"name": "Category", "id": "category"},
            {"name": "Item", "id": "item_name"},
            {"name": "Amount", "id": "amount"},
            {"name": "Currency", "id": "currency"},
            {"name": "Date", "id": "date"},
        ],
        data=table_data,
        style_table={"overflowX": "auto"},
        style_cell={
            "textAlign": "left",
            "padding": "10px",
        },
        style_header={
            "backgroundColor": "rgb(230, 230, 230)",
            "fontWeight": "bold",
        },
        page_size=10,
    )
