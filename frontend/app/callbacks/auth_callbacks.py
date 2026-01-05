import dash
from dash import Input, Output, State, callback_context
from dash.exceptions import PreventUpdate
import json

from utils.api_client import APIClient


def register_auth_callbacks(app):
    """Register authentication-related callbacks."""
    
    api_client = APIClient()

    @app.callback(
        [
            Output("session-store", "data"),
            Output("login-error", "children"),
            Output("login-error", "is_open"),
            Output("url", "pathname", allow_duplicate=True),
        ],
        [Input("login-button", "n_clicks")],
        [
            State("login-email", "value"),
            State("login-password", "value"),
        ],
        prevent_initial_call=True,
    )
    def handle_login(n_clicks, email, password):
        """Handle login button click."""
        print(f"DEBUG: Login button clicked. n_clicks: {n_clicks}")
        if not n_clicks:
            raise PreventUpdate

        if not email or not password:
            print("DEBUG: Missing email or password")
            return dash.no_update, "Please enter both email and password", True, dash.no_update

        # Call login endpoint (JSON version)
        print(f"DEBUG: Sending login request for {email}")
        response = api_client.post(
            "/auth/login/json",
            {"email": email, "password": password}
        )
        print(f"DEBUG: Login response: {response}")

        if "error" in response:
            return dash.no_update, f"Login failed: {response['error']}", True, dash.no_update

        if "access_token" in response:
            token = response["access_token"]
            print("DEBUG: Login successful")
            return {"token": token}, "", False, "/dashboard"

        return dash.no_update, "Invalid response from server", True, dash.no_update

    @app.callback(
        [
            Output("register-message", "children"),
            Output("register-message", "color"),
            Output("register-message", "is_open"),
            Output("url", "pathname", allow_duplicate=True),
        ],
        [Input("register-button", "n_clicks")],
        [
            State("register-email", "value"),
            State("register-fullname", "value"),
            State("register-password", "value"),
        ],
        prevent_initial_call=True,
    )
    def handle_register(n_clicks, email, full_name, password):
        """Handle registration button click."""
        print(f"DEBUG: Register button clicked. n_clicks: {n_clicks}")
        if not n_clicks:
            raise PreventUpdate

        if not email or not full_name or not password:
            print("DEBUG: Missing registration fields")
            return "Please fill in all fields", "warning", True, dash.no_update

        # Call register endpoint
        print(f"DEBUG: Sending register request for {email}")
        response = api_client.post(
            "/auth/register",
            {"email": email, "full_name": full_name, "password": password}
        )
        print(f"DEBUG: Register response: {response}")

        if "error" in response:
            return f"Registration failed: {response['error']}", "danger", True, dash.no_update

        # Success - redirect to login
        print("DEBUG: Registration successful")
        return "Registration successful! Please login.", "success", True, "/login"

    @app.callback(
        Output("user-store", "data"),
        [Input("session-store", "data")],
        prevent_initial_call=False,
    )
    def load_user_data(session_data):
        """Load user data when token is available."""
        if not session_data or "token" not in session_data:
            raise PreventUpdate

        token = session_data["token"]
        api_client.set_token(token)

        # Call /auth/me endpoint
        response = api_client.get("/auth/me")

        if "error" in response:
            return None

        return response

    @app.callback(
        [
            Output("session-store", "data", allow_duplicate=True),
            Output("user-store", "data", allow_duplicate=True),
            Output("current-period-id", "data", allow_duplicate=True),
            Output("url", "pathname", allow_duplicate=True),
        ],
        [Input("logout-button", "n_clicks")],
        prevent_initial_call=True,
    )
    def handle_logout(n_clicks):
        """Handle logout button click."""
        if not n_clicks:
            raise PreventUpdate

        # Clear stores and redirect to login
        return None, None, None, "/login"
