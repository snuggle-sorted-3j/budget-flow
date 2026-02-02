import dash
from dash import Input, Output, State, html, dcc, dash_table
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from datetime import datetime
from utils.api_client import APIClient
from utils.ui_helpers import get_amount_class, format_currency

def register_dashboard_home_callbacks(app):
    """Register callbacks for the dashboard home and global period selector."""
    api_client = APIClient()

    @app.callback(
        [
            Output("global-period-selector", "options"),
            Output("global-period-selector", "value"),
            Output("current-period-id", "data"),
        ],
        [Input("url", "pathname"), Input("session-store", "data")],
        [State("current-period-id", "data")],
    )
    def load_global_periods(pathname, session_data, current_p_id):
        """Load periods into global selector and handle initial selection."""
        if not pathname or not pathname.startswith("/dashboard"):
            raise PreventUpdate
        
        if not session_data or "token" not in session_data:
            return [], None, None

        try:
            api_client.set_token(session_data["token"])
            periods = api_client.get("/periods/")
            
            if "error" in periods:
                return [], None, None
            
            if not periods:
                return [], None, None

            options = [
                {"label": p["period_name"], "value": p["id"]} 
                for p in sorted(periods, key=lambda x: x["start_date"], reverse=True)
            ]
            
            # Determine value: existing store > first in list
            if current_p_id and any(o["value"] == current_p_id for o in options):
                val = current_p_id
            else:
                val = options[0]["value"] if options else None
                
            return options, val, val
        except Exception:
            return [], None, None

    @app.callback(
        Output("current-period-id", "data", allow_duplicate=True),
        [Input("global-period-selector", "value")],
        prevent_initial_call=True
    )
    def update_period_store(period_id):
        """Update the store when the global selector changes."""
        if not period_id:
            raise PreventUpdate
        return period_id

    # The following callback is disabled as it targets IDs removed during the analytics dashboard upgrade.
    # Logic has been moved to analytics_callbacks.py
    """
    @app.callback(
        [
            Output("dashboard-period-overview", "children"),
            Output("dashboard-financial-summary", "children"),
            Output("dashboard-quick-stats", "children"),
            Output("dashboard-period-list-container", "children"),
        ],
        [
            Input("current-period-id", "data"), 
            Input("url", "pathname"),
            Input("recon-trigger-store", "data"),
        ],
        [State("session-store", "data")],
    )
    def update_dashboard_home(period_id, pathname, recon_trigger, session_data):
        ...
    """

    # Callback to handle row clicks in the period list table
    @app.callback(
        Output("global-period-selector", "value", allow_duplicate=True),
        [Input("dashboard-period-list-table", "active_cell")],
        [State("dashboard-period-list-table", "data")],
        prevent_initial_call=True
    )
    def switch_period_from_table(active_cell, table_data):
        """Switch the global period when a row is clicked in the table."""
        if not active_cell or not table_data:
            raise PreventUpdate
        
        row_idx = active_cell["row"]
        period_id = table_data[row_idx]["id"]
        return period_id

def create_overview_section(period):
    """Create Section 1: Current Period Overview."""
    if not period or "error" in period:
        return dbc.Alert("Error loading period overview", color="danger")
    
    start_date = datetime.strptime(period["start_date"], "%Y-%m-%d")
    end_date = datetime.strptime(period["end_date"], "%Y-%m-%d")
    days = (end_date - start_date).days + 1
    
    status_text = period["status"].replace("_", " ")
    status_bg = "bg-soft-success text-success" if period["status"] == "FINALIZED" else "bg-soft-warning text-warning"
    
    return dbc.Card(
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.H6("CURRENT PERIOD", className="text-secondary fw-bold small mb-2"),
                    html.H2(period["period_name"], className="fw-bold mb-2 text-dark"),
                    html.Div([
                        html.I(className="bi bi-calendar3 me-2 text-muted"),
                        html.Span(f"{period['start_date']} to {period['end_date']}", className="text-muted fs-5"),
                    ], className="d-flex align-items-center"),
                ], md=8),
                dbc.Col([
                    html.Div([
                        dbc.Badge(
                            status_text, 
                            className=f"mb-2 px-3 py-2 {status_bg}", 
                            style={"fontSize": "0.9rem", "fontWeight": "800"}
                        ),
                        html.Div([
                            html.I(className="bi bi-clock-history me-1"), 
                            f"{days} days"
                        ], className="text-muted fw-bold"),
                        html.Small(f"Snapshot: {period.get('snapshot_date', 'N/A')}", className="text-muted d-block mt-1")
                    ], className="text-end")
                ], md=4),
            ], className="align-items-center")
        ]),
        className="mb-4 shadow-sm border-0 bg-white"
    )

def create_dashboard_financial_card(cs):
    """Create a specific dashboard version of the financial card."""
    currency = cs.get("currency_ticker", "")
    
    # Values
    starting = float(cs.get("starting_balance", 0))
    income = float(cs.get("total_income", 0))
    expenses = float(cs.get("total_expenses", 0))
    
    expected = float(cs.get("expected_balance", 0))
    actual = cs.get("actual_balance") # Can be None if not set
    actual_val = float(actual) if actual is not None else 0.0
    
    diff = float(cs.get("difference", 0))
    is_balanced = cs.get("is_balanced", False)
    
    # Styles
    diff_class = get_amount_class(diff)
    status_class = "text-success" if is_balanced else "text-danger" if diff != 0 else "text-warning"
    status_icon = "bi-check-circle-fill" if is_balanced else "bi-exclamation-triangle-fill"
    status_text = "BALANCED" if is_balanced else f"DIFFERENCE: {format_currency(diff)}"

    return dbc.Col(
        dbc.Card([
            dbc.CardBody([
                html.Div([
                    html.H4(currency, className="fw-bold mb-3"),
                    
                    dbc.Row([
                        # LEFT COLUMN: Flows
                        dbc.Col([
                            html.Div("FLOWS", className="text-muted x-small fw-bold mb-2"),
                            
                            html.Div([
                                html.Span("Starting:", className="text-muted me-2 small"),
                                html.Span(format_currency(starting), className="fw-bold float-end")
                            ], className="mb-1 d-flex justify-content-between"),
                            
                            html.Div([
                                html.Span("Income:", className="text-muted me-2 small"),
                                html.Span(f"+{format_currency(income)}", className="text-success fw-bold float-end")
                            ], className="mb-1 d-flex justify-content-between"),
                            
                            html.Div([
                                html.Span("Expenses:", className="text-muted me-2 small"),
                                html.Span(f"-{format_currency(expenses)}", className="text-danger fw-bold float-end")
                            ], className="mb-1 d-flex justify-content-between"),

                            html.Hr(className="my-2 opacity-50"),
                        ], md=6, className="border-end pe-4"),
                        
                        # RIGHT COLUMN: Balances
                        dbc.Col([
                            html.Div("BALANCES", className="text-muted x-small fw-bold mb-2"),
                            
                            html.Div([
                                html.Span("Expected:", className="text-muted me-2 small"),
                                html.Span(format_currency(expected), className="fw-bold float-end")
                            ], className="mb-1 d-flex justify-content-between"),
                            
                            html.Div([
                                html.Span("Actual:", className="text-muted me-2 small"),
                                html.Span(
                                    format_currency(actual_val) if actual is not None else "Not set", 
                                    className="fw-bold float-end"
                                )
                            ], className="mb-1 d-flex justify-content-between"),
                            
                            html.Hr(className="my-2 opacity-50"),
                            
                            html.Div([
                                html.Span("Difference:", className="fw-bold me-2 small"),
                                html.Span(
                                    format_currency(diff, show_sign=True), 
                                    className=f"{diff_class} fw-bold float-end fs-5"
                                )
                            ], className="mb-1 d-flex justify-content-between align-items-center"),
                            
                        ], md=6, className="ps-4"),
                    ]),
                    
                    # Status Footer
                    html.Div([
                        html.Hr(className="mt-3 mb-2"),
                        html.Div([
                            html.I(className=f"bi {status_icon} me-2 {status_class}"),
                            html.Span(status_text, className=f"{status_class} fw-bold")
                        ], className="text-center bg-light rounded py-1 mt-2")
                    ])
                ])
            ])
        ], className="h-100 shadow-sm border-0"),
        md=12, lg=6, className="mb-4"
    )

def create_financial_summary_section(recon):
    """Create Section 2: Financial Summary."""
    if not recon or "error" in recon:
        return dbc.Alert("Error loading financial summary", color="danger")
    
    reconciliations = recon.get("reconciliations", [])
    if not reconciliations:
        return html.Div() # Show nothing if no data, or maybe empty state?
        
    cards = []
    for cs in reconciliations:
        # Check if active (has any numbers)
        starting = float(cs.get("starting_balance", 0))
        income = float(cs.get("total_income", 0))
        expenses = float(cs.get("total_expenses", 0))
        actual = cs.get("actual_balance")
        actual_val = float(actual) if actual is not None else 0.0
        
        # Consider a currency "active" if it has any non-zero flow/balance OR if an actual balance was explicitly set
        has_activity = (starting != 0) or (income != 0) or (expenses != 0) or (actual_val != 0)
        
        # If absolutely nothing happened with this currency, skip it
        if not has_activity:
            continue
            
        cards.append(create_dashboard_financial_card(cs))
    
    if not cards:
        return html.Div([
            html.Div(className="bi bi-wallet2 empty-state-icon"),
            html.H5("No Financial Data", className="fw-bold"),
            html.P("Add accounts, income, or expenses to see your financial overview.")
        ], className="text-center py-5 text-muted bg-light rounded mb-4")

    # Use a grid layout for cards
    return html.Div(dbc.Row(cards), className="mb-2")


def create_quick_stats_section(accounts, incomes, expenses, period):
    """Create Section 3: Quick Stats Bar."""
    # Data processing
    acct_list = accounts if accounts and "error" not in accounts else []
    inc_list = incomes if incomes and "error" not in incomes else []
    exp_list = expenses if expenses and "error" not in expenses else []
    
    total_accounts = len(acct_list)
    
    # Active currencies (from accounts + transactions)
    currencies = set()
    for a in acct_list:
        if a.get("currency_id"): currencies.add(a["currency_id"])
    active_currencies_count = len(currencies)
    
    # Transaction counts
    tx_count = len(inc_list) + len(exp_list)
    
    # Tax deductible
    tax_deductible_total = sum(float(e["amount"]) for e in exp_list if e.get("is_tax_deductible"))
    
    stats = [
        ("Total Accounts", str(total_accounts), "bi-bank"),
        ("Active Currencies", str(active_currencies_count), "bi-currency-exchange"),
        ("Transactions", str(tx_count), "bi-list-check"),
        ("Tax Deductible", f"{tax_deductible_total:,.2f}", "bi-receipt"),
    ]
    
    cols = []
    for label, value, icon in stats:
        cols.append(dbc.Col(
            dbc.Card([
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col(html.Div(className=f"bi {icon} text-primary fs-3 opacity-75"), width="auto"),
                        dbc.Col([
                            html.H3(value, className="mb-0 fw-bold"),
                            html.Small(label, className="text-muted text-uppercase fw-bold x-small"),
                        ])
                    ], className="align-items-center g-2")
                ])
            ], className="border-0 shadow-sm h-100"),
            width=6, lg=3, className="mb-4"
        ))
        
    return dbc.Row(cols)

def create_period_list_table(periods, current_period_id):
    """Create Section 4: Recent Periods List."""
    if not periods or "error" in periods:
        return html.Div("No periods found", className="text-muted text-center py-4")

    # Sort by start_date descending -> Show last 5
    sorted_periods = sorted(periods, key=lambda x: x["start_date"], reverse=True)[:5]
    
    data = []
    for p in sorted_periods:
        status_norm = p["status"].replace("_", " ")
        data.append({
            "period_name": p["period_name"],
            "dates": f"{p['start_date']} to {p['end_date']}",
            "status": status_norm,
            "id": p["id"],
        })

    return dash_table.DataTable(
        id="dashboard-period-list-table",
        columns=[
            {"name": "Period Name", "id": "period_name"},
            {"name": "Dates", "id": "dates"},
            {"name": "Status", "id": "status"},
        ],
        data=data,
        style_table={"borderRadius": "8px", "overflow": "hidden"},
        style_cell={
            "textAlign": "left", 
            "padding": "15px", 
            "fontSize": "14px",
            "border": "none",
            "borderBottom": "1px solid #edf2f7",
            "fontFamily": "Inter, sans-serif"
        },
        style_header={
            "backgroundColor": "#f8f9fa", 
            "fontWeight": "bold", 
            "color": "#6c757d",
            "textTransform": "uppercase",
            "fontSize": "12px",
            "borderBottom": "2px solid #edf2f7",
            "padding": "15px"
        },
        style_data_conditional=[
            {
                "if": {"filter_query": f"{{id}} = '{current_period_id}'"},
                "backgroundColor": "#e7f1ff",
                "color": "#0d6efd",
                "fontWeight": "bold",
            },
            {
                "if": {"row_index": "odd"},
                "backgroundColor": "#ffffff",
            },
            {
                 "if": {"state": "active"},
                 "backgroundColor": "rgba(0, 116, 217, 0.05)",
                 "border": "1px solid rgb(0, 116, 217)",
                 "color": "inherit"
             }
        ],
        row_selectable=False,
        cell_selectable=True, # Needed for active_cell
    )
