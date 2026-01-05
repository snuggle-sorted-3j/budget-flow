import dash
from dash import Input, Output, State, html
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from dash import dash_table

from utils.api_client import APIClient


def register_income_callbacks(app):
    """Register income management callbacks."""
    
    api_client = APIClient()

    @app.callback(
        [
            Output("income-form-container", "style"),
            Output("income-currency", "options"),
            Output("income-currency", "value"),
        ],
        [Input("current-period-id", "data"), Input("session-store", "data")],
    )
    def show_income_form(period_id, session_data):
        """Show income form and load currencies when period is selected."""
        if not period_id or not session_data or "token" not in session_data:
            return {"display": "none"}, [], None

        token = session_data["token"]
        api_client.set_token(token)

        # Load currencies
        currencies_response = api_client.get("/currencies/")
        currency_options = []
        default_currency_id = None
        if "error" not in currencies_response:
            for c in currencies_response:
                ticker = c.get('ticker', '')
                curr_id = c.get('id', '')
                currency_options.append({"label": f"{ticker} - {c.get('name', '')}", "value": curr_id})
                if c.get("is_default"):
                    default_currency_id = curr_id
            
            # Fallback to first one
            if not default_currency_id and currency_options:
                default_currency_id = currency_options[0]["value"]

        return {"display": "block"}, currency_options, default_currency_id

    @app.callback(
        [
            Output("income-message", "children"),
            Output("income-message", "color"),
            Output("income-message", "is_open"),
            Output("income-source-name", "value"),
            Output("income-amount", "value"),
            Output("income-currency", "value", allow_duplicate=True),
            Output("income-date", "value"),
            Output("income-notes", "value"),
            Output("income-tax-applicable", "value"),
            Output("income-table-container", "children", allow_duplicate=True),
            Output("recon-trigger-store", "data", allow_duplicate=True),
        ],
        [Input("add-income-btn", "n_clicks")],
        [
            State("current-period-id", "data"),
            State("income-source-name", "value"),
            State("income-amount", "value"),
            State("income-currency", "value"),
            State("income-date", "value"),
            State("income-notes", "value"),
            State("income-tax-applicable", "value"),
            State("session-store", "data"),
        ],
        prevent_initial_call=True,
    )
    def add_income(n_clicks, period_id, source_name, amount, currency_id, income_date, notes, tax_applicable, session_data):
        """Handle adding income."""
        if not n_clicks:
            raise PreventUpdate

        # Validate inputs
        if not source_name or not amount or not currency_id or not period_id:
            return (
                "Please fill in all required fields",
                "warning",
                True,
                source_name,
                amount,
                currency_id,
                income_date,
                notes,
                tax_applicable,
                dash.no_update,
            )

        if not session_data or "token" not in session_data:
            return (
                "Please log in first",
                "danger",
                True,
                source_name,
                amount,
                currency_id,
                income_date,
                notes,
                tax_applicable,
                dash.no_update,
            )

        token = session_data["token"]
        api_client.set_token(token)

        # Create income entry
        payload = {
            "source_name": source_name,
            "amount": float(amount),
            "currency_id": currency_id,
            "tax_applicable": tax_applicable or False,
        }
        
        if income_date:
            payload["income_date"] = income_date
        if notes:
            payload["notes"] = notes

        response = api_client.post(f"/periods/{period_id}/incomes", payload)

        if "error" in response:
            return (
                f"Error adding income: {response['error']}",
                "danger",
                True,
                source_name,
                amount,
                currency_id,
                income_date,
                notes,
                tax_applicable,
                dash.no_update,
            )

        # Success - clear form and refresh table
        income_response = api_client.get(f"/periods/{period_id}/incomes")
        table = create_income_table(income_response if "error" not in income_response else [], period_id, api_client)

        return (
            f"Income '{source_name}' added successfully!",
            "success",
            True,
            "",  # Clear source name
            "",  # Clear amount
            dash.no_update,  # Keep current currency
            "",  # Clear date
            "",  # Clear notes
            False,  # Reset checkbox
            table,
            dash.no_update # Will be handled by return if we wanted to increment, but let's just use current time
        )

    @app.callback(
        Output("recon-trigger-store", "data", allow_duplicate=True),
        [Input("income-table-container", "children")],
        prevent_initial_call=True
    )
    def trigger_recon_on_income_change(child):
        from datetime import datetime
        return datetime.now().timestamp()

    @app.callback(
        Output("income-table-container", "children"),
        [Input("current-period-id", "data"), Input("session-store", "data")],
    )
    def load_income_table(period_id, session_data):
        """Load income entries for selected period."""
        if not period_id or not session_data or "token" not in session_data:
            return html.Div("Select a period in the header to view income entries", className="text-muted")

        token = session_data["token"]
        api_client.set_token(token)

        response = api_client.get(f"/periods/{period_id}/incomes")

        if "error" in response:
            return html.Div(f"Error loading income: {response['error']}", className="text-danger")

        return create_income_table(response, period_id, api_client)


from utils.ui_helpers import create_empty_state, format_currency

def create_income_table(income_entries, period_id, api_client):
    """Create a DataTable from income entries."""
    if not income_entries or len(income_entries) == 0:
        return create_empty_state(
            "bi-cash-stack",
            "No income entries yet",
            "Add your first income source using the form above."
        )

    # Prepare data for table
    table_data = [
        {
            "source_name": entry.get("source_name", ""),
            "amount": format_currency(entry.get('amount', 0)),
            "currency": entry.get("currency_code", ""),
            "date": entry.get("income_date", "N/A"),
            "tax_applicable": "Yes" if entry.get("tax_applicable", False) else "No",
            "id": entry.get("id", ""),
        }
        for entry in income_entries
    ]

    return dash_table.DataTable(
        id="income-table",
        columns=[
            {"name": "Source", "id": "source_name"},
            {"name": "Amount", "id": "amount"},
            {"name": "Currency", "id": "currency"},
            {"name": "Date", "id": "date"},
            {"name": "Tax Applicable", "id": "tax_applicable"},
        ],
        data=table_data,
        style_table={"overflowX": "auto", "borderRadius": "8px", "overflow": "hidden"},
        style_cell={
            "textAlign": "left",
            "padding": "12px",
            "fontSize": "14px",
            "border": "none",
            "borderBottom": "1px solid #edf2f7"
        },
        style_header={
            "backgroundColor": "#f7fafc",
            "fontWeight": "bold",
            "color": "#4a5568",
            "textTransform": "uppercase",
            "fontSize": "12px",
            "border": "none"
        },
        style_data_conditional=[
            {
                "if": {"row_index": "odd"},
                "backgroundColor": "#fcfdfd",
            }
        ],
        page_size=10,
    )
