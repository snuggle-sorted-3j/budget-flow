import dash_bootstrap_components as dbc
from dash import html

def create_empty_state(icon_class, title, message):
    """Create a polished empty state component."""
    return html.Div([
        html.Div(className=f"bi {icon_class} empty-state-icon"),
        html.H4(title, className="fw-bold mb-2"),
        html.P(message, className="text-muted mb-0")
    ], className="empty-state-container shadow-sm border-0")

def format_currency(amount, show_sign=False):
    """Format number with thousand separators and 2 decimal places."""
    try:
        val = float(amount)
        formatted = f"{abs(val):,.2f}"
        if show_sign:
            sign = "+" if val >= 0 else "-"
            return f"{sign}{formatted}"
        return formatted
    except (ValueError, TypeError):
        return "0.00"

def get_amount_class(amount):
    """Get color class based on amount value."""
    try:
        val = float(amount)
        return "amount-positive" if val >= 0 else "amount-negative"
    except (ValueError, TypeError):
        return ""
