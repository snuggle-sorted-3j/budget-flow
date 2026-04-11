import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output

from callbacks.auth_callbacks import register_auth_callbacks
from callbacks.period_callbacks import register_period_callbacks
from callbacks.income_callbacks import register_income_callbacks
from callbacks.expense_callbacks import register_expense_callbacks
from callbacks.reconciliation_callbacks import register_reconciliation_callbacks
from callbacks.account_callbacks import register_account_callbacks
from callbacks.currency_callbacks import register_currency_callbacks
from callbacks.category_callbacks import register_category_callbacks
from callbacks.dashboard_callbacks import register_dashboard_home_callbacks
from callbacks.common_reconciliation_callbacks import register_common_reconciliation_callbacks
from callbacks.investment_callbacks import register_investment_callbacks
from callbacks.suspended_callbacks import register_suspended_callbacks
from callbacks.installment_callbacks import register_installment_callbacks
from callbacks.conversion_callbacks import register_conversion_callbacks
from callbacks.template_callbacks import register_template_callbacks
from callbacks.analytics_callbacks import register_analytics_callbacks
from callbacks.analytics_advanced_callbacks import register_analytics_advanced_callbacks
from callbacks.onboarding_callbacks import register_onboarding_callbacks
from layouts.login import create_login_layout
from layouts.register import create_register_layout
from layouts.dashboard import create_dashboard_layout
from tabs.dashboard_home import create_dashboard_home_layout
from tabs.tab1_period_setup import create_period_tab_layout
from tabs.tab2_income import create_income_tab_layout
from tabs.tab3_expenses import create_expenses_tab_layout
from tabs.tab8_reconciliation import create_reconciliation_tab_layout
from tabs.tab4_accounts import create_accounts_tab_layout
from tabs.tab5_currencies import create_currencies_tab_layout
from tabs.tab6_categories import create_categories_tab_layout
from tabs.tab7_investments import create_investments_tab_layout
from tabs.tab4_suspended import create_suspended_tab_layout
from tabs.tab9_installments import create_installments_tab_layout
from tabs.tab10_conversions import create_conversions_tab_layout
from tabs.tab11_templates import create_templates_tab_layout
from tabs.tab12_analytics_advanced import create_advanced_analytics_layout

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
        dcc.Store(id="auth-error-trigger", storage_type="memory"),
        html.Div(id="page-content"),
    ]
)


# Register callbacks
register_auth_callbacks(app)
register_period_callbacks(app)
register_income_callbacks(app)
register_expense_callbacks(app)
register_reconciliation_callbacks(app)
register_account_callbacks(app)
register_currency_callbacks(app)
register_category_callbacks(app)
register_dashboard_home_callbacks(app)
register_common_reconciliation_callbacks(app)
register_investment_callbacks(app)
register_suspended_callbacks(app)
register_installment_callbacks(app)
register_conversion_callbacks(app)
register_template_callbacks(app)
register_analytics_callbacks(app)
register_analytics_advanced_callbacks(app)
register_onboarding_callbacks(app)


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


# Sub-dashboard content rendering based on URL
@app.callback(
    Output("dashboard-content", "children"),
    [Input("url", "pathname")],
)
def render_dashboard_content(pathname):
    """Render content based on URL pathname."""
    if pathname == "/dashboard" or pathname == "/dashboard/":
        return create_dashboard_home_layout()
    elif pathname == "/dashboard/periods":
        return create_period_tab_layout()
    elif pathname == "/dashboard/income":
        return create_income_tab_layout()
    elif pathname == "/dashboard/expenses":
        return create_expenses_tab_layout()
    elif pathname == "/dashboard/reconciliation":
        return create_reconciliation_tab_layout()
    elif pathname == "/dashboard/accounts":
        return create_accounts_tab_layout()
    elif pathname == "/dashboard/currencies":
        return create_currencies_tab_layout()
    elif pathname == "/dashboard/categories":
        return create_categories_tab_layout()
    elif pathname == "/dashboard/investments":
        return create_investments_tab_layout()
    elif pathname == "/dashboard/suspended":
        return create_suspended_tab_layout()
    elif pathname == "/dashboard/installments":
        return create_installments_tab_layout()
    elif pathname == "/dashboard/conversions":
        return create_conversions_tab_layout()
    elif pathname == "/dashboard/templates":
        return create_templates_tab_layout()
    elif pathname == "/dashboard/analytics-advanced":
        return create_advanced_analytics_layout()
    
    # Default to dashboard home
    return create_dashboard_home_layout()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050, debug=True)
