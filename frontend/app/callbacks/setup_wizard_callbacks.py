"""Callbacks for the initial setup wizard."""
from dash import Input, Output, State, callback, no_update
from dash.exceptions import PreventUpdate

from utils.api_client import APIClient

_api = APIClient()


def register_setup_wizard_callbacks(app):
    """Register all setup wizard callbacks."""

    # Step 1 → Step 2: save chosen currency, advance
    @app.callback(
        Output("wizard-step-store", "data", allow_duplicate=True),
        Output("wizard-currency-id-store", "data"),
        Input("wizard-step1-next", "n_clicks"),
        State("wizard-currency-select", "value"),
        State("session-store", "data"),
        prevent_initial_call=True,
    )
    def wizard_step1_next(n_clicks, currency_id, session_data):
        if not n_clicks or not currency_id:
            raise PreventUpdate
        # Set chosen currency as default via API
        try:
            _api.set_token(session_data["token"])
            _api.patch(f"/currencies/{currency_id}/set-default", {})
        except Exception:
            pass
        return 2, currency_id

    # Step 2 → Step 3: create account
    @app.callback(
        Output("wizard-step-store", "data", allow_duplicate=True),
        Output("wizard-account-error", "children"),
        Input("wizard-step2-next", "n_clicks"),
        State("wizard-account-name", "value"),
        State("wizard-account-type", "value"),
        State("wizard-account-balance", "value"),
        State("wizard-currency-id-store", "data"),
        State("session-store", "data"),
        prevent_initial_call=True,
    )
    def wizard_step2_next(n_clicks, name, acct_type, balance, currency_id, session_data):
        if not n_clicks:
            raise PreventUpdate
        if not name or not name.strip():
            return no_update, "Account name is required."
        try:
            _api.set_token(session_data["token"])
            _api.post("/accounts/", {
                "account_name": name.strip(),
                "account_type": acct_type or "BANK",
                "currency_id": currency_id,
                "opening_balance": float(balance or 0),
            })
            return 3, ""
        except Exception as e:
            return no_update, f"Error: {e}"

    # Step 2 back → Step 1
    @app.callback(
        Output("wizard-step-store", "data", allow_duplicate=True),
        Input("wizard-step2-back", "n_clicks"),
        prevent_initial_call=True,
    )
    def wizard_step2_back(n_clicks):
        if not n_clicks:
            raise PreventUpdate
        return 1

    # Step 3 → Step 4: create period
    @app.callback(
        Output("wizard-step-store", "data", allow_duplicate=True),
        Output("wizard-period-error", "children"),
        Input("wizard-step3-next", "n_clicks"),
        State("wizard-period-name", "value"),
        State("wizard-period-start", "value"),
        State("wizard-period-end", "value"),
        State("session-store", "data"),
        prevent_initial_call=True,
    )
    def wizard_step3_next(n_clicks, name, start, end, session_data):
        if not n_clicks:
            raise PreventUpdate
        if not name or not start or not end:
            return no_update, "All fields are required."
        if end < start:
            return no_update, "End date must be on or after start date."
        try:
            _api.set_token(session_data["token"])
            _api.post("/periods/", {
                "period_name": name.strip(),
                "start_date": start,
                "end_date": end,
                "snapshot_date": end,
            })
            return 4, ""
        except Exception as e:
            return no_update, f"Error: {e}"

    # Step 3 back → Step 2
    @app.callback(
        Output("wizard-step-store", "data", allow_duplicate=True),
        Input("wizard-step3-back", "n_clicks"),
        prevent_initial_call=True,
    )
    def wizard_step3_back(n_clicks):
        if not n_clicks:
            raise PreventUpdate
        return 2
