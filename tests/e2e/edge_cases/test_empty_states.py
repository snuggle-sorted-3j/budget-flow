"""
E2E Edge Cases: Empty States

Verifies that all tabs handle the "no data" state gracefully
(no crashes, appropriate empty messages visible).
"""
import pytest
from playwright.sync_api import Page, expect

from tests.e2e.conftest import (
    make_email,
    register_and_login,
    navigate_to,
)


@pytest.fixture
def empty_user(page: Page) -> dict:
    """Fresh user with no data at all."""
    email = make_email("empty")
    register_and_login(page, email)
    return {"email": email}


def test_periods_empty_state(page: Page, empty_user: dict) -> None:
    """Period Setup tab loads without crashing on empty data."""
    navigate_to(page, "periods")
    page.wait_for_selector("#period-name-input", state="visible", timeout=10_000)
    # Form should be present even with no periods
    expect(page.locator("#create-period-btn")).to_be_visible()


def test_income_tab_no_period_selected(page: Page, empty_user: dict) -> None:
    """Income tab loads without crashing when no period is selected."""
    navigate_to(page, "income")
    page.wait_for_load_state("networkidle", timeout=10_000)
    # Income form is hidden until period selected, but page should not crash
    expect(page.locator("#global-period-selector")).to_be_visible()


def test_expenses_tab_no_period_selected(page: Page, empty_user: dict) -> None:
    """Expenses tab loads without crashing when no period is selected."""
    navigate_to(page, "expenses")
    page.wait_for_load_state("networkidle", timeout=10_000)
    expect(page.locator("#global-period-selector")).to_be_visible()


def test_accounts_empty_table(page: Page, empty_user: dict) -> None:
    """Accounts tab renders the add form even with no accounts."""
    navigate_to(page, "accounts")
    page.wait_for_selector("#add-account-btn", state="visible", timeout=10_000)
    expect(page.locator("#add-account-btn")).to_be_visible()


def test_currencies_empty_table(page: Page, empty_user: dict) -> None:
    """Currencies tab shows the add form even with no user currencies."""
    navigate_to(page, "currencies")
    page.wait_for_selector("#currency-ticker", state="visible", timeout=10_000)
    expect(page.locator("#add-currency-btn")).to_be_visible()


def test_categories_empty_table(page: Page, empty_user: dict) -> None:
    """Categories tab shows the add form even with no custom categories."""
    navigate_to(page, "categories")
    page.wait_for_selector("#category-name-input", state="visible", timeout=10_000)
    expect(page.locator("#add-category-btn")).to_be_visible()


def test_installments_empty_state(page: Page, empty_user: dict) -> None:
    """Installments tab loads without crashing with no installment data."""
    navigate_to(page, "installments")
    page.wait_for_selector("#inst-name", state="visible", timeout=10_000)
    expect(page.locator("#add-inst-btn")).to_be_visible()


def test_investments_empty_state(page: Page, empty_user: dict) -> None:
    """Investments tab loads without crashing with no investment data."""
    navigate_to(page, "investments")
    page.wait_for_selector("#inv-account-name", state="visible", timeout=10_000)
    expect(page.locator("#add-inv-account-btn")).to_be_visible()


def test_suspended_empty_state(page: Page, empty_user: dict) -> None:
    """Suspended tab loads without crashing with no suspended transactions."""
    navigate_to(page, "suspended")
    page.wait_for_selector("#susp-item-name", state="visible", timeout=10_000)
    expect(page.locator("#add-susp-btn")).to_be_visible()


def test_conversions_empty_state(page: Page, empty_user: dict) -> None:
    """Conversions tab loads without crashing with no conversions."""
    navigate_to(page, "conversions")
    page.wait_for_selector("#add-conv-btn", state="visible", timeout=10_000)
    expect(page.locator("#add-conv-btn")).to_be_visible()


def test_templates_empty_state(page: Page, empty_user: dict) -> None:
    """Templates tab loads without crashing with no templates."""
    navigate_to(page, "templates")
    page.wait_for_selector("#tpl-name", state="visible", timeout=10_000)
    expect(page.locator("#tpl-save-btn")).to_be_visible()


def test_analytics_empty_state(page: Page, empty_user: dict) -> None:
    """Analytics tab loads without crashing with no data."""
    navigate_to(page, "analytics")
    page.wait_for_selector("#advanced-report-btn", state="visible", timeout=15_000)
    expect(page.locator("#advanced-report-btn")).to_be_visible()
