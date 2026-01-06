import dash_bootstrap_components as dbc
from dash import html

def create_empty_state(icon_class, title, message, cta_button=None):
    """
    Create a polished empty state component.
    
    Args:
        icon_class: Bootstrap icon class (e.g., 'bi-inbox')
        title: Empty state title
        message: Empty state message
        cta_button: Optional dict with 'text', 'id', and 'href' for call-to-action button
    """
    content = [
        html.Div(className=f"bi {icon_class} empty-state-icon"),
        html.H4(title, className="fw-bold mb-2"),
        html.P(message, className="text-muted mb-3")
    ]
    
    if cta_button:
        if cta_button.get('href'):
            content.append(
                dbc.Button(
                    cta_button['text'],
                    href=cta_button['href'],
                    color="primary",
                    className="mt-2"
                )
            )
        elif cta_button.get('id'):
            content.append(
                dbc.Button(
                    cta_button['text'],
                    id=cta_button['id'],
                    color="primary",
                    className="mt-2"
                )
            )
    
    return html.Div(content, className="empty-state-container shadow-sm border-0")


def format_currency(amount, show_sign=False, currency_ticker=""):
    """
    Format number with thousand separators and 2 decimal places.
    
    Args:
        amount: Numeric amount
        show_sign: Whether to show +/- sign
        currency_ticker: Optional currency ticker to append
    """
    try:
        val = float(amount)
        formatted = f"{abs(val):,.2f}"
        if show_sign:
            sign = "+" if val >= 0 else "-"
            result = f"{sign}{formatted}"
        else:
            result = formatted if val >= 0 else f"-{formatted}"
        
        if currency_ticker:
            result = f"{result} {currency_ticker}"
        
        return result
    except (ValueError, TypeError):
        return "0.00" + (f" {currency_ticker}" if currency_ticker else "")


def get_amount_class(amount):
    """Get color class based on amount value."""
    try:
        val = float(amount)
        return "amount-positive" if val >= 0 else "amount-negative"
    except (ValueError, TypeError):
        return ""


def create_loading_skeleton(rows=5):
    """
    Create a skeleton loader for tables.
    
    Args:
        rows: Number of skeleton rows to display
    """
    skeleton_rows = []
    for _ in range(rows):
        skeleton_rows.append(
            html.Tr([
                html.Td(html.Div(className="skeleton-line", style={"width": "80%"})),
                html.Td(html.Div(className="skeleton-line", style={"width": "60%"})),
                html.Td(html.Div(className="skeleton-line", style={"width": "70%"})),
                html.Td(html.Div(className="skeleton-line", style={"width": "50%"})),
            ])
        )
    
    return dbc.Table(
        [html.Tbody(skeleton_rows)],
        className="skeleton-table"
    )


def create_toast(message, icon="bi-check-circle-fill", color="success"):
    """
    Create a toast notification.
    
    Args:
        message: Toast message
        icon: Bootstrap icon class
        color: Toast color (success, danger, warning, info)
    """
    return dbc.Toast(
        [
            html.I(className=f"{icon} me-2"),
            message
        ],
        header="Notification",
        icon=color,
        dismissable=True,
        duration=3000,
        style={
            "position": "fixed",
            "top": 20,
            "right": 20,
            "minWidth": "300px",
            "zIndex": 9999
        }
    )


def format_number(value, decimals=2):
    """
    Format a number with thousand separators.
    
    Args:
        value: Numeric value
        decimals: Number of decimal places
    """
    try:
        return f"{float(value):,.{decimals}f}"
    except (ValueError, TypeError):
        return "0" + ("." + "0" * decimals if decimals > 0 else "")


def truncate_text(text, max_length=50):
    """
    Truncate text with ellipsis.
    
    Args:
        text: Text to truncate
        max_length: Maximum length before truncation
    """
    if not text:
        return ""
    
    text_str = str(text)
    if len(text_str) <= max_length:
        return text_str
    
    return text_str[:max_length - 3] + "..."


def create_badge(text, color="primary"):
    """
    Create a styled badge.
    
    Args:
        text: Badge text
        color: Badge color
    """
    return dbc.Badge(text, color=color, className="me-1")
