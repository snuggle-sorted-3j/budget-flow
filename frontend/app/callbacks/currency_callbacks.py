import dash
from dash import Input, Output, State, html, dash_table, callback_context
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from utils.api_client import APIClient


def register_currency_callbacks(app):
    api_client = APIClient()

    @app.callback(
        [
            Output("currency-message", "children"),
            Output("currency-message", "color"),
            Output("currency-message", "is_open"),
            Output("currency-ticker", "value"),
            Output("currency-name", "value"),
            Output("currency-table-container", "children"),
        ],
        [
            Input("add-currency-btn", "n_clicks"),
            Input("url", "pathname"),
            Input({"type": "set-default-btn", "id": dash.ALL}, "n_clicks"),
            Input({"type": "delete-currency-btn", "id": dash.ALL}, "n_clicks"),
        ],
        [
            State("currency-ticker", "value"),
            State("currency-name", "value"),
            State("currency-default", "value"),
            State("session-store", "data"),
        ],
        prevent_initial_call=False,
    )
    def handle_currency_action(add_clicks, pathname, set_default_clicks, delete_clicks, ticker, name, is_default, session_data):
        ctx = callback_context
        triggered_id_raw = "unknown"
        if ctx.triggered:
            triggered_id_raw = ctx.triggered[0]["prop_id"].split(".")[0]
        
        if not session_data or "token" not in session_data:
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, html.Div("Please log in")

        api_client.set_token(session_data["token"])
        
        msg, color, open = dash.no_update, dash.no_update, dash.no_update
        
        # Handle "Add Currency"
        if triggered_id_raw == "add-currency-btn":
            if not ticker or not name:
                msg, color, open = "Please fill all fields", "warning", True
            else:
                resp = api_client.post("/currencies/", {"ticker": ticker, "name": name, "is_default": bool(is_default)})
                if "error" in resp:
                    msg, color, open = f"Error: {resp['error']}", "danger", True
                else:
                    msg, color, open = f"Currency {ticker} added!", "success", True
                    ticker, name = "", ""

        # Handle Actions (Set Default or Delete)
        elif "btn" in triggered_id_raw and "{" in triggered_id_raw:
            try:
                t_id = dash.callback_context.triggered_id
                if isinstance(t_id, dict):
                    currency_id = t_id.get("id")
                    action_type = t_id.get("type")
                    
                    if action_type == "set-default-btn":
                        resp = api_client.patch(f"/currencies/{currency_id}/set-default", {})
                        if "error" in resp:
                            msg, color, open = f"Error setting default: {resp['error']}", "danger", True
                        else:
                            msg, color, open = f"Default currency updated!", "success", True
                            
                    elif action_type == "delete-currency-btn":
                        # Check confirm logic here if possible, but for now direct delete
                        resp = api_client.delete(f"/currencies/{currency_id}")
                        if "error" in resp:
                            msg, color, open = f"Error deleting: {resp['error']}", "danger", True
                        else:
                            msg, color, open = f"Currency deleted successfully!", "success", True

            except Exception as e:
                print(f"Error parsing triggered_id: {e}")

        # Always reload table
        currencies = api_client.get("/currencies/")
        
        # Auto-initialize fallback if empty
        if not currencies or (isinstance(currencies, list) and len(currencies) == 0):
            api_client.post("/currencies/initialize", {})
            currencies = api_client.get("/currencies/")

        if "error" in currencies:
            table = html.Div(f"Error loading currencies: {currencies.get('error', 'Unknown error')}")
        else:
            table = create_currency_table(currencies)
            
        return msg, color, open, ticker, name, table


def create_currency_table(currencies):
    """Create a table showing currencies with a 'Set as Default' button."""
    if not currencies:
        from utils.ui_helpers import create_empty_state
        return create_empty_state("bi-currency-exchange", "No currencies", "You haven't added any currencies yet.")
        
    rows = []
    sorted_currencies = sorted(currencies, key=lambda x: x["ticker"])
    
    for c in sorted_currencies:
        is_default = c.get("is_default", False)
        rows.append(
            html.Tr([
                html.Td(c["ticker"], className="fw-bold"),
                html.Td(c["name"]),
                html.Td(
                    dbc.Badge("DEFAULT", color="success", className="status-pill status-balanced") if is_default else ""
                ),
                html.Td([
                    dbc.Button(
                        "Set Default",
                        id={"type": "set-default-btn", "id": c["id"]},
                        color="outline-primary",
                        size="sm",
                        className="btn-rounded me-2",
                        disabled=is_default,
                    ),
                    dbc.Button(
                        html.I(className="bi bi-trash"),
                        id={"type": "delete-currency-btn", "id": c["id"]},
                        color="outline-danger",
                        size="sm",
                        className="btn-rounded",
                        disabled=is_default, # prevent deleting default currency
                    )
                ])
            ])
        )
        
    return dbc.Table(
        [
            html.Thead(html.Tr([
                html.Th("Ticker"),
                html.Th("Name"),
                html.Th("Default"),
                html.Th("Actions"),
            ])),
            html.Tbody(rows)
        ],
        bordered=False,
        hover=True,
        responsive=True,
        className="align-middle custom-table"
    )
