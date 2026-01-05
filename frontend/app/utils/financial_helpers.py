import dash_bootstrap_components as dbc
from dash import html
from utils.ui_helpers import get_amount_class, format_currency

def create_financial_summary_card(cs):
    """Create a polished financial summary card for a specific currency."""
    total_income = float(cs.get("total_income", 0))
    total_expenses = float(cs.get("total_expenses", 0))
    total_installments = float(cs.get("total_installments", 0))
    net_diff = total_income - total_expenses - total_installments
    
    diff_class = get_amount_class(net_diff)
    formatted_net = format_currency(net_diff, show_sign=True)
    
    is_balanced = cs.get("is_balanced", False)
    recon_diff = float(cs.get("difference", 0))
    
    status_pill_class = "status-balanced" if is_balanced else "status-difference"
    recon_status = "BALANCED ✓" if is_balanced else f"DIFFERENCE: {format_currency(recon_diff)}"
    
    border_class = "card-balanced" if is_balanced else "card-unbalanced"

    return dbc.Col(
        dbc.Card([
            dbc.CardBody([
                html.Div([
                    html.Span(cs["currency_ticker"], className="currency-ticker float-end"),
                    html.Div("Period Cashflow", className="text-muted small fw-bold text-uppercase mb-1"),
                    html.Div(formatted_net, className=f"amount-display {diff_class} mb-3"),
                    
                    dbc.Row([
                        dbc.Col([
                            html.Div("Income", className="text-muted x-small fw-bold text-uppercase"),
                            html.Div(f"{total_income:,.2f}", className="fw-bold"),
                        ], width=4),
                        dbc.Col([
                            html.Div("Expenses", className="text-muted x-small fw-bold text-uppercase"),
                            html.Div(f"{total_expenses:,.2f}", className="fw-bold"),
                        ], width=4),
                        dbc.Col([
                            html.Div("Installments", className="text-muted x-small fw-bold text-uppercase"),
                            html.Div(f"{total_installments:,.2f}", className="fw-bold"),
                        ], width=4),
                    ], className="mb-3"),
                    
                    html.Hr(className="my-2 opacity-25"),
                    
                    html.Div([
                        html.Span("Reconciliation:", className="text-muted small me-2"),
                        html.Span("Balanced ✓" if is_balanced else f"Unreconciled Gap: {format_currency(recon_diff)}", 
                                 className=f"status-pill {status_pill_class}"),
                    ], className="d-flex align-items-center justify-content-between")
                ])
            ])
        ], className=f"dashboard-card {border_class} mb-4"),
        md=12, lg=6, xl=4 # Wider on smaller screens
    )

def create_financial_summary_row(reconciliations):
    """Create a Row containing financial summary cards."""
    if not reconciliations:
        return html.Div("No financial data for this period")
    
    cards = []
    for cs in reconciliations:
        # We can decide whether to skip empty ones here
        cards.append(create_financial_summary_card(cs))
    
    return dbc.Row(cards)
