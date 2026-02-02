"""Enhanced Expense callbacks with comprehensive error handling and UX improvements."""
from datetime import datetime
import dash
from dash import Input, Output, State, html, ctx, ALL
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc

from utils.api_client import APIClient
from utils.ui_helpers import create_empty_state, format_currency, create_toast
from utils.error_handler import (
    display_error,
    display_success,
    display_warning,
    validate_required_fields,
    validate_positive_number,
    validate_date,
    parse_api_error
)


def register_expense_callbacks(app):
    """Register expense management callbacks with enhanced error handling."""
    
    api_client = APIClient()

    @app.callback(
        [
            Output("expense-form-container", "style"),
            Output("expense-currency", "options"),
            Output("expense-currency", "value"),
            Output("expense-category", "options"),
        ],
        [Input("current-period-id", "data"), Input("session-store", "data")],
    )
    def show_expense_form(period_id, session_data):
        """Show expense form and load currencies/categories when period is selected."""
        if not period_id or not session_data or "token" not in session_data:
            return {"display": "none"}, [], None, []

        try:
            token = session_data["token"]
            api_client.set_token(token)

            # Load currencies
            currencies_response = api_client.get("/currencies/")
            currency_options = []
            default_currency_id = None
            
            if isinstance(currencies_response, list):
                for c in currencies_response:
                    ticker = c.get('ticker', '')
                    curr_id = c.get('id', '')
                    currency_options.append({
                        "label": f"{ticker} - {c.get('name', '')}", 
                        "value": curr_id
                    })
                    if c.get("is_default"):
                        default_currency_id = curr_id
                
                if not default_currency_id and currency_options:
                    default_currency_id = currency_options[0]["value"]
            
            # Load categories
            categories_response = api_client.get("/expense-categories/")
            
            # Auto-initialize if empty
            if isinstance(categories_response, list) and len(categories_response) == 0:
                api_client.post("/expense-categories/initialize", {})
                categories_response = api_client.get("/expense-categories/")
            
            category_options = []
            if isinstance(categories_response, list):
                # Build hierarchical options
                parents = [c for c in categories_response if not c.get("parent_category_id")]
                children_map = {}
                for c in categories_response:
                    pid = c.get("parent_category_id")
                    if pid:
                        if pid not in children_map:
                            children_map[pid] = []
                        children_map[pid].append(c)
                
                for p in sorted(parents, key=lambda x: x.get("category_name", "")):
                    category_options.append({
                        "label": f"📁 {p['category_name']}",
                        "value": p["id"]
                    })
                    children = children_map.get(p["id"], [])
                    for child in sorted(children, key=lambda x: x.get("category_name", "")):
                        category_options.append({
                            "label": f"   └─ {child['category_name']}",
                            "value": child["id"]
                        })
            elif isinstance(categories_response, dict) and "error" in categories_response:
                print(f"Error loading categories: {parse_api_error(categories_response)}")

            return {"display": "block"}, currency_options, default_currency_id, category_options
            
        except Exception as e:
            print(f"Error in show_expense_form: {e}")
            return {"display": "none"}, [], None, []

    @app.callback(
        [
            Output("expense-form-alert", "children"),
            Output("expense-category", "value"),
            Output("expense-item-name", "value"),
            Output("expense-amount", "value"),
            Output("expense-currency", "value", allow_duplicate=True),
            Output("expense-date", "value"),
            Output("expense-notes", "value"),
            Output("expense-table-container", "children", allow_duplicate=True),
            Output("recon-trigger-store", "data", allow_duplicate=True),
            Output("add-expense-btn", "disabled"),
            Output("expense-toast-container", "children"),
            Output("auth-error-trigger", "data", allow_duplicate=True),
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
            State("expense-is-recurring", "value"),
            State("session-store", "data"),
        ],
        prevent_initial_call=True,
    )
    def add_expense(n_clicks, period_id, category_id, item_name, amount, currency_id,
                    expense_date, notes, is_recurring, session_data):
        """Handle adding expense with comprehensive validation."""
        if not n_clicks:
            raise PreventUpdate

        try:
            # Validate required fields
            is_valid, errors = validate_required_fields(
                category=category_id,
                item_name=item_name,
                amount=amount,
                currency=currency_id,
                period=period_id
            )
            
            if not is_valid:
                error_list = [f"{field}: {msg}" for field, msg in errors.items()]
                return (
                    display_warning("Please fill all required fields (*): " + ", ".join(error_list)),
                    dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                    dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                    False, None, dash.no_update
                )
            
            # Validate amount is positive
            is_valid, error_msg = validate_positive_number(amount, "Amount")
            if not is_valid:
                return (
                    display_warning(error_msg),
                    dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                    dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                    False, None, dash.no_update
                )
            
            # Validate date if provided
            if expense_date:
                is_valid, error_msg = validate_date(expense_date, allow_future=False, field_name="Expense Date")
                if not is_valid:
                    return (
                        display_warning(error_msg),
                        dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                        dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                        False, None, dash.no_update
                    )

            if not session_data or "token" not in session_data:
                return (
                    display_error("Please log in first"),
                    dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                    dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                    False, None, datetime.now().timestamp()
                )

            token = session_data["token"]
            api_client.set_token(token)

            # Create expense entry
            payload = {
                "category_id": category_id,
                "item_name": item_name,
                "amount": float(amount),
                "currency_id": currency_id,
                "is_recurring": is_recurring or False,
            }
            
            if expense_date:
                payload["expense_date"] = expense_date
            if notes:
                payload["notes"] = notes

            response = api_client.post(f"/periods/{period_id}/expenses", payload)

            if "error" in response or "detail" in response:
                auth_error = response.get("error") == "AUTHENTICATION_ERROR"
                return (
                    display_error(response),
                    dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                    dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                    False, None, datetime.now().timestamp() if auth_error else dash.no_update
                )

            # Success - clear form and refresh table
            expense_response = api_client.get(f"/periods/{period_id}/expenses")
            table = create_expense_table(
                expense_response if isinstance(expense_response, list) else [],
                period_id,
                api_client
            )

            toast = create_toast(
                f"Expense '{item_name}' added successfully!",
                icon="bi-check-circle-fill",
                color="success"
            )

            return (
                display_success(f"Expense '{item_name}' added successfully!"),
                dash.no_update,  # Keep category
                "",  # Clear item name
                "",  # Clear amount
                dash.no_update,  # Keep currency
                "",  # Clear date
                "",  # Clear notes
                False,  # Reset recurring checkbox
                table,
                datetime.now().timestamp(),
                False,
                toast,
                dash.no_update
            )
            
        except Exception as e:
            return (
                display_error(f"Unexpected error: {str(e)}"),
                dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                False, None, dash.no_update
            )

    @app.callback(
        Output("recon-trigger-store", "data", allow_duplicate=True),
        [Input("expense-table-container", "children")],
        prevent_initial_call=True
    )
    def trigger_recon_on_expense_change(child):
        """Trigger reconciliation update when expenses change."""
        return datetime.now().timestamp()

    @app.callback(
        Output("expense-table-container", "children"),
        [Input("current-period-id", "data"), Input("session-store", "data")],
    )
    def load_expense_table(period_id, session_data):
        """Load expense entries for selected period."""
        if not period_id or not session_data or "token" not in session_data:
            return create_empty_state(
                "bi-calendar-check",
                "No Period Selected",
                "Select a monitoring period in the header to view expense entries."
            )

        try:
            token = session_data["token"]
            api_client.set_token(token)

            response = api_client.get(f"/periods/{period_id}/expenses")

            if "error" in response:
                return display_error(response)

            return create_expense_table(
                response if isinstance(response, list) else [], 
                period_id, 
                api_client
            )
            
        except Exception as e:
            return display_error(f"Error loading expenses: {str(e)}")

    # --- Delete Expense with Confirmation ---
    @app.callback(
        [
            Output("expense-delete-modal", "is_open"),
            Output("expense-pending-delete-id", "data"),
        ],
        [
            Input({"type": "delete-expense-btn", "index": ALL}, "n_clicks"),
            Input("expense-delete-cancel", "n_clicks"),
        ],
        [State("expense-delete-modal", "is_open")],
        prevent_initial_call=True
    )
    def toggle_delete_modal(delete_clicks, cancel_click, is_open):
        """Toggle delete confirmation modal."""
        if not ctx.triggered:
            raise PreventUpdate
        
        trig = ctx.triggered_id
        
        if trig == "expense-delete-cancel":
            return False, None
        
        if isinstance(trig, dict) and trig["type"] == "delete-expense-btn":
            if any(delete_clicks):
                expense_id = trig["index"]
                return True, expense_id
        
        return dash.no_update, dash.no_update

    @app.callback(
        [
            Output("expense-table-container", "children", allow_duplicate=True),
            Output("expense-delete-modal", "is_open", allow_duplicate=True),
            Output("expense-toast-container", "children", allow_duplicate=True),
            Output("recon-trigger-store", "data", allow_duplicate=True),
        ],
        [Input("expense-delete-confirm", "n_clicks")],
        [
            State("expense-pending-delete-id", "data"),
            State("current-period-id", "data"),
            State("session-store", "data")
        ],
        prevent_initial_call=True
    )
    def confirm_delete_expense(n_clicks, expense_id, period_id, session_data):
        """Confirm and execute expense deletion."""
        if not n_clicks or not expense_id:
            raise PreventUpdate
        
        try:
            api_client.set_token(session_data["token"])
            result = api_client.delete(f"/expenses/{expense_id}")
            
            if "error" in result:
                toast = create_toast(
                    f"Failed to delete: {parse_api_error(result)}",
                    icon="bi-x-circle-fill",
                    color="danger"
                )
                return dash.no_update, False, toast, dash.no_update
            
            # Reload table
            expense_response = api_client.get(f"/periods/{period_id}/expenses")
            table = create_expense_table(
                expense_response if isinstance(expense_response, list) else [],
                period_id,
                api_client
            )
            
            toast = create_toast(
                "Expense entry deleted successfully",
                icon="bi-check-circle-fill",
                color="success"
            )
            
            return table, False, toast, datetime.now().timestamp()
            
        except Exception as e:
            toast = create_toast(
                f"Error: {str(e)}",
                icon="bi-x-circle-fill",
                color="danger"
            )
            return dash.no_update, False, toast, dash.no_update


def create_expense_table(expense_entries, period_id, api_client):
    """Create an enhanced expense table with delete functionality."""
    if not expense_entries or len(expense_entries) == 0:
        return create_empty_state(
            "bi-receipt",
            "No Expense Entries",
            "Add your first expense using the form above to start tracking your spending."
        )

    try:
        # Create table rows with delete buttons
        rows = []
        for entry in expense_entries:
            rows.append(html.Tr([
                html.Td(
                    dbc.Badge(
                        entry.get("category_name", "Uncategorized"),
                        color="primary",
                        className="me-1"
                    )
                ),
                html.Td([
                    entry.get("item_name", ""),
                    html.I(className="bi bi-arrow-repeat ms-2 text-primary", title="Recurring") if entry.get("is_recurring") else None
                ], className="fw-bold"),
                html.Td(
                    format_currency(entry.get('amount', 0), currency_ticker=entry.get("currency_code", "")),
                    className="text-danger fw-bold"
                ),
                html.Td(entry.get("expense_date", "N/A")),
                html.Td(entry.get("notes", "-"), className="text-muted small"),
                html.Td(
                    dbc.Button(
                        html.I(className="bi bi-trash"),
                        id={"type": "delete-expense-btn", "index": entry.get("id", "")},
                        size="sm",
                        color="link",
                        className="text-danger p-0",
                        title="Delete expense entry"
                    ),
                    className="text-center"
                )
            ]))

        return dbc.Table(
            [
                html.Thead(html.Tr([
                    html.Th("Category"),
                    html.Th("Item"),
                    html.Th("Amount"),
                    html.Th("Date"),
                    html.Th("Notes"),
                    html.Th("Actions", className="text-center")
                ])),
                html.Tbody(rows)
            ],
            hover=True,
            responsive=True,
            className="align-middle"
        )
        
    except Exception as e:
        print(f"Error creating expense table: {e}")
        return display_error(f"Error displaying expense data: {str(e)}")
