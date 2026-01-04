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
        if not n_clicks:
            raise PreventUpdate

        if not email or not password:
            return None, "Please enter both email and password", True, "/"

        # Call login endpoint (JSON version)
        response = api_client.post(
            "/auth/login/json",
            {"email": email, "password": password}
        )

        if "error" in response:
            return None, f"Login failed: {response['error']}", True, "/"

        if "access_token" in response:
            token = response["access_token"]
            return {"token": token}, "", False, "/dashboard"

        return None, "Invalid response from server", True, "/"

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
        if not n_clicks:
            raise PreventUpdate

        if not email or not full_name or not password:
            return "Please fill in all fields", "warning", True, "/register"

        # Call register endpoint
        response = api_client.post(
            "/auth/register",
            {"email": email, "full_name": full_name, "password": password}
        )

        if "error" in response:
            return f"Registration failed: {response['error']}", "danger", True, "/register"

        # Success - redirect to login
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
        return None, None, "/login"
