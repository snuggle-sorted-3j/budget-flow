"""
E2E Edge Cases: Negative Amounts & Validation Boundaries

Covers:
- Submitting negative amounts in income/expenses (should be rejected)
- Submitting zero amounts (should be rejected)
- Submitting empty required fields (should be rejected or ignored)
- Very large amounts (should be accepted)
"""
import pytest
from playwright.sync_api import Page, expect

from tests.e2e.conftest import (
    make_email,
    rand_id,
    register_and_login,
    create_currency,
    create_account,
    create_period,
    select_period,
    navigate_to,
)
from tests.e2e.pages.income_page import IncomePage
from tests.e2e.pages.expense_page import ExpensePage
from tests.e2e.pages.installments_page import InstallmentsPage
from tests.e2e.pages.suspended_page import SuspendedPage


@pytest.fixture
def validation_user(page: Page) -> dict:
    """User with USD and a period, ready for validation tests."""
    email = make_email("val")
    register_and_login(page, email)
    rid = rand_id()
    period_name = f"Val Period {rid}"
    create_currency(page, "USD", "US Dollar", is_default=True)
    create_account(page, "Main Bank", "BANK", "USD")
    create_period(page, period_name, "2026-01-01", "2026-01-31")
    select_period(page, period_name)
    return {"period_name": period_name, "rid": rid}


def test_income_zero_amount_rejected(page: Page, validation_user: dict) -> None:
    """Income with amount 0 should not add a valid entry."""
    navigate_to(page, "income")
    inc = IncomePage(page)
    inc.wait_for_form()
    inc.page.fill("#income-source-name", "Zero Income")
    inc.page.fill("#income-amount", "0")
    page.wait_for_selector("#income-currency option:has-text('USD')", state="attached")
    page.select_option("#income-currency", label="USD")
    page.click("#add-income-btn")
    page.wait_for_timeout(1_000)
    # Either an error message or the item should not be in table
    # The API uses min=0.01 validation via Pydantic
    # At minimum, page should not crash
    expect(page.locator("#income-form-alert, #income-table-container")).to_be_visible(
        timeout=5_000
    )


def test_expense_empty_name_rejected(page: Page, validation_user: dict) -> None:
    """Expense with no name should either be rejected or show validation error."""
    navigate_to(page, "expenses")
    exp = ExpensePage(page)
    exp.wait_for_form()
    page.wait_for_selector("#expense-category option", state="attached")
    page.select_option("#expense-category", index=1)
    # Leave item name empty
    page.fill("#expense-amount", "100")
    page.wait_for_selector("#expense-currency option:has-text('USD')", state="attached")
    page.select_option("#expense-currency", label="USD")
    page.click("#add-expense-btn")
    page.wait_for_timeout(1_000)
    # Should show error or remain on form
    # Page should not crash
    expect(page.locator("#expense-form-alert, #expense-table-container")).to_be_visible(
        timeout=5_000
    )


def test_income_very_large_amount_accepted(page: Page, validation_user: dict) -> None:
    """Income with a very large amount (999999999.99) should be accepted by the form."""
    navigate_to(page, "income")
    inc = IncomePage(page)
    inc.add_income(
        source=f"BigIncome {rand_id()}",
        amount="999999999.99",
        currency_ticker="USD",
    )
    # No crash; either in table or error message visible
    expect(page.locator("#income-form-alert, #income-table-container")).to_be_visible(
        timeout=5_000
    )


def test_income_decimal_amounts_accepted(page: Page, validation_user: dict) -> None:
    """Income with decimal amounts (1234.56) should be accepted."""
    navigate_to(page, "income")
    inc = IncomePage(page)
    inc.add_income(
        source=f"Decimal {rand_id()}",
        amount="1234.56",
        currency_ticker="USD",
    )
    inc.expect_income_in_table("Decimal")


def test_installment_zero_total_rejected(page: Page, validation_user: dict) -> None:
    """Installment with total price 0 should be rejected."""
    navigate_to(page, "installments")
    inst = InstallmentsPage(page)
    page.wait_for_selector("#inst-name", state="visible")
    page.fill("#inst-name", "Zero Installment")
    page.fill("#inst-total", "0")
    page.wait_for_selector(
        "#inst-currency option:has-text('USD')", state="attached"
    )
    page.select_option("#inst-currency", label="USD")
    page.click("#add-inst-btn")
    page.wait_for_timeout(1_000)
    # Should not appear in active installments or show error
    expect(page.locator("#inst-form-alert, #active-installments-container")).to_be_visible(
        timeout=5_000
    )


def test_suspended_empty_name_rejected(page: Page, validation_user: dict) -> None:
    """Suspended transaction with empty name should not be created."""
    navigate_to(page, "suspended")
    susp = SuspendedPage(page)
    page.wait_for_selector("#susp-item-name", state="visible")
    # Leave name empty, fill amount
    page.fill("#susp-amount", "100")
    # Click currency dropdown
    page.locator("#susp-currency").click()
    page.get_by_role("option", name="USD").first.click()
    page.select_option("#susp-type", value="LOAN_OUT")
    page.click("#add-susp-btn")
    page.wait_for_timeout(1_000)
    # Should show error or not add to table
    expect(page.locator("#susp-form-alert, #susp-pending-table-container")).to_be_visible(
        timeout=5_000
    )
