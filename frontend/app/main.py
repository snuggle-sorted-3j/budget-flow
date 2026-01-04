import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output

from callbacks.auth_callbacks import register_auth_callbacks
from callbacks.period_callbacks import register_period_callbacks
from callbacks.income_callbacks import register_income_callbacks
from callbacks.expense_callbacks import register_expense_callbacks
from layouts.login import create_login_layout
from layouts.register import create_register_layout
from layouts.dashboard import create_dashboard_layout
from tabs.tab1_period_setup import create_period_tab_layout
from tabs.tab2_income import create_income_tab_layout
from tabs.tab3_expenses import create_expenses_tab_layout

# Initialize Dash app
app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css",
    ],
    suppress_callback_exceptions=True,
    title="BudgetFlow",
)
server = app.server

# Define app layout with routing
app.layout = html.Div(
    [
        dcc.Location(id="url", refresh=False),
        dcc.Store(id="session-store", storage_type="session"),
        dcc.Store(id="user-store", storage_type="session"),
        html.Div(id="page-content"),
    ]
)


# Register callbacks
register_auth_callbacks(app)
register_period_callbacks(app)
register_income_callbacks(app)
register_expense_callbacks(app)


@app.callback(
    Output("page-content", "children"),
    [Input("url", "pathname"), Input("session-store", "data"), Input("user-store", "data")],
)
def display_page(pathname, session_data, user_data):
    """Handle page routing based on URL and authentication state."""
    
    # Check if user is authenticated
    is_authenticated = session_data and "token" in session_data
    
    # Login page
    if pathname == "/login" or pathname == "/":
        if is_authenticated and pathname == "/":
            # Redirect to dashboard if already logged in
            user_email = user_data.get("email", "User") if user_data else "User"
            return create_dashboard_layout(user_email=user_email)
        return create_login_layout()
    
    # Registration page
    if pathname == "/register":
        return create_register_layout()
    
    # Dashboard and sub-pages
    if pathname and pathname.startswith("/dashboard"):
        if not is_authenticated:
            # Redirect to login if not authenticated
            return create_login_layout()
        
        user_email = user_data.get("email", "User") if user_data else "User"
        return create_dashboard_layout(user_email=user_email)
    
    # Default: redirect to login
    return create_login_layout()


# Tab switching callback
@app.callback(
    Output("dashboard-content", "children"),
    [Input("dashboard-tabs", "value")],
)
def render_tab_content(active_tab):
    """Render content based on selected tab."""
    if active_tab == "tab-periods":
        return create_period_tab_layout()
    elif active_tab == "tab-income":
        return create_income_tab_layout()
    elif active_tab == "tab-expenses":
        return create_expenses_tab_layout()
    elif active_tab == "tab-reconciliation":
        return html.Div("Reconciliation tab - Coming soon!", className="p-4")
    return html.Div("Select a tab", className="p-4")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050, debug=True)
