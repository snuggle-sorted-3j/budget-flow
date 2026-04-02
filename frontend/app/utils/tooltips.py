"""Tooltip definitions and helper for BudgetFlow UI.

Usage:
    from utils.tooltips import make_tooltip, TIPS

    # In a layout, place next to a label:
    make_tooltip("income-tax-applicable", TIPS["income_tax_applicable"])
"""
from dash import html
import dash_bootstrap_components as dbc

# ------------------------------------------------------------------
# Tooltip text registry
# ------------------------------------------------------------------
TIPS: dict[str, str] = {
    # Income
    "income_tax_applicable": (
        "Mark if this income is subject to income tax. "
        "Used in Polish B2B tax calculations to compute monthly tax obligations."
    ),
    "income_recurring": (
        "Recurring income auto-appears as a suggestion in future periods. "
        "You can still edit or remove it each period."
    ),
    # Expenses
    "expense_tax_deductible": (
        "Mark costs that are deductible business expenses (e.g. equipment, software, travel). "
        "Reduces your taxable income in B2B tax mode."
    ),
    "expense_recurring": (
        "Recurring expenses (e.g. subscriptions, rent) are suggested each period. "
        "Amounts can be adjusted before confirming."
    ),
    "expense_type": (
        "REGULAR: a one-off or recurring expense. "
        "INSTALLMENT_PAYMENT: a scheduled payment toward an installment plan tracked separately."
    ),
    # Reconciliation
    "reconciliation_difference": (
        "The gap between your expected balance (calculated from income minus expenses) "
        "and your actual bank balance. Must reach 0 to finalize the period. "
        "Use 'Untracked Expenses' to account for any unknown spending."
    ),
    "reconciliation_starting_balance": (
        "The verified account balance at the start of this period. "
        "Carried forward automatically from the previous period's final snapshot."
    ),
    "reconciliation_snapshot": (
        "Your actual bank balance right now (or at period end). "
        "Enter the exact figure from your banking app — this is what gets reconciled."
    ),
    # Suspended expenses
    "suspended_type": (
        "LOAN_OUT: money you lent to someone (expect return). "
        "PURCHASE_RETURN: item returned, awaiting refund. "
        "OTHER: any other temporarily removed transaction."
    ),
    "suspended_status": (
        "PENDING: still outstanding. "
        "SETTLED: money was returned — add to income when settled. "
        "CONVERTED_TO_EXPENSE: decided to keep as a regular expense."
    ),
    # Installments
    "installment_remaining": (
        "Automatically decremented as you record payments. "
        "The plan is marked PAID_OFF when this reaches zero."
    ),
    # Currency conversion
    "conversion_rate": (
        "Exchange rate applied (units of target currency per 1 unit of source). "
        "Example: 1 USD → 0.92 EUR means rate = 0.92."
    ),
    # Periods
    "period_snapshot_date": (
        "The date you record your actual account balances for reconciliation. "
        "Usually the last day of the period or your pay date."
    ),
}


def make_tooltip(target_id: str, text: str, placement: str = "right") -> dbc.Tooltip:
    """Return a dbc.Tooltip targeting *target_id* with the given *text*."""
    return dbc.Tooltip(
        text,
        target=target_id,
        placement=placement,
        style={"maxWidth": "320px"},
    )


def help_icon(target_id: str, tip_key: str, placement: str = "right") -> html.Span:
    """Return a small help icon + tooltip inline with a label.

    Place this directly after the label text in any form row.

    Args:
        target_id: A unique HTML id for the icon element (used as tooltip target).
        tip_key: Key into the TIPS dict.
        placement: Bootstrap tooltip placement (right/top/bottom/left).
    """
    text = TIPS.get(tip_key, "")
    return html.Span(
        [
            html.I(
                className="bi bi-question-circle text-muted ms-1",
                id=target_id,
                style={"cursor": "help", "fontSize": "0.85rem"},
            ),
            dbc.Tooltip(text, target=target_id, placement=placement, style={"maxWidth": "320px"}),
        ]
    )
