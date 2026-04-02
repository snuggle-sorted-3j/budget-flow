import dash
from dash import Input, Output, State, html
import dash_bootstrap_components as dbc
from utils.api_client import APIClient
from utils.financial_helpers import create_financial_summary_card

def register_common_reconciliation_callbacks(app):
    """Register callbacks for shared reconciliation summary components."""
    api_client = APIClient()

    # Shared logic to fetch and format reconciliation data
    def get_recon_data(period_id, token):
        api_client.set_token(token)
        response = api_client.get(f"/periods/{period_id}/reconciliation")

        if "error" in response:
            return None, False, f"Error: {response['error']}", None

        reconciliations = response.get("reconciliations", [])
        overall_balanced = response.get("overall_balanced", False)
        period_status = response.get("status", "")

        cards = []
        for cs in reconciliations:
            total_income = float(cs.get("total_income", 0))
            total_expenses = float(cs.get("total_expenses", 0))
            starting = float(cs.get("starting_balance", 0))
            if total_income != 0 or total_expenses != 0 or starting != 0:
                cards.append(create_financial_summary_card(cs))

        return cards, overall_balanced, None, period_status

    def _finalized_banner():
        return dbc.Alert(
            [
                html.I(className="bi bi-lock-fill me-2"),
                html.Strong("This period is FINALIZED. "),
                "Transactions are locked and cannot be added, edited, or deleted.",
            ],
            color="secondary",
            className="mb-3",
        )

    # Tab-specific callbacks to avoid "Nonexistent Object" errors
    # 1. Expenses Tab Summary
    @app.callback(
        Output("expense-recon-summary", "children"),
        [Input("current-period-id", "data"), Input("recon-trigger-store", "data")],
        [State("session-store", "data")],
        prevent_initial_call="initial_duplicate"
    )
    def update_expense_recon(period_id, trigger, session_data):
        if not period_id or not session_data or "token" not in session_data:
             return dash.no_update

        cards, balanced, error, period_status = get_recon_data(period_id, session_data["token"])
        if error: return html.Div(error, className="text-danger")

        children = []
        if period_status == "FINALIZED":
            children.append(_finalized_banner())
        if not cards:
            children.append(html.Div("No financial data for this period", className="text-muted small italic"))
        else:
            children.append(html.H6("Live Period Status", className="mb-3 fw-bold text-muted small text-uppercase"))
            children.append(dbc.Row(cards))

        return html.Div(children)

    # 2. Income Tab Summary
    @app.callback(
        Output("income-recon-summary", "children"),
        [Input("current-period-id", "data"), Input("recon-trigger-store", "data")],
        [State("session-store", "data")],
        prevent_initial_call="initial_duplicate"
    )
    def update_income_recon(period_id, trigger, session_data):
        if not period_id or not session_data or "token" not in session_data:
             return dash.no_update

        cards, balanced, error, period_status = get_recon_data(period_id, session_data["token"])
        if error: return html.Div(error, className="text-danger")

        children = []
        if period_status == "FINALIZED":
            children.append(_finalized_banner())
        if not cards:
            children.append(html.Div("No financial data for this period", className="text-muted small italic"))
        else:
            children.append(html.H6("Live Period Status", className="mb-3 fw-bold text-muted small text-uppercase"))
            children.append(dbc.Row(cards))

        return html.Div(children)

    # 3. Reconciliation Tab Main Summary & Finalize Visibility
    @app.callback(
        [
            Output("recon-summary-container", "children", allow_duplicate=True),
            Output("recon-balanced-store", "data", allow_duplicate=True),
            Output("finalize-section-container", "style"),
        ],
        [Input("current-period-id", "data"), Input("recon-trigger-store", "data")],
        [State("session-store", "data")],
        prevent_initial_call="initial_duplicate"
    )
    def update_recon_tab_summary(period_id, trigger, session_data):
        if not period_id or not session_data or "token" not in session_data:
             return dash.no_update, dash.no_update, dash.no_update
        
        cards, balanced, error, period_status = get_recon_data(period_id, session_data["token"])
        if error: return html.Div(error, className="text-danger"), False, {"display": "none"}
        
        overall_banner = dbc.Alert(
            [
                html.I(className=f"bi bi-{'check-circle' if balanced else 'x-circle'} me-2"),
                html.Strong(
                    "All currencies are balanced! You can finalize this period." if balanced
                    else "Some currencies are not balanced. Please review and adjust before finalizing."
                ),
            ],
            color="success" if balanced else "danger",
            className="mb-4 shadow-sm",
        )
        
        finalize_style = {"display": "block"} if balanced else {"display": "none"}
        summary_content = html.Div([overall_banner, dbc.Row(cards)]) if cards else html.Div("No data yet.")
        
        return summary_content, balanced, finalize_style
