"""
E2E Flow: Suspended Transaction Workflows

Covers:
- Create a suspended transaction (loan out)
- Settle it (money returned) → verify moves to history
- Convert another one to expense → verify moves to history
- Carry-forward scenario (pending item in table)
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
from tests.e2e.pages.suspended_page import SuspendedPage


@pytest.fixture
def suspended_setup(page: Page) -> dict:
    """Setup: fresh user, USD, account, period."""
    email = make_email("susp")
    register_and_login(page, email)
    rid = rand_id()
    period_name = f"Susp Period {rid}"
    create_currency(page, "USD", "US Dollar", is_default=True)
    create_account(page, "Main Bank", "BANK", "USD")
    create_period(page, period_name, "2026-01-01", "2026-01-31")
    select_period(page, period_name)
    return {"period_name": period_name}


def test_create_suspended_transaction(page: Page, suspended_setup: dict) -> None:
    """User can create a suspended transaction."""
    navigate_to(page, "suspended")
    susp = SuspendedPage(page)
    item_name = f"Loan to Alex {rand_id()}"
    susp.add_suspended(
        item_name=item_name,
        amount="500",
        currency_ticker="USD",
        susp_type="LOAN_OUT",
        notes="Will return next month",
    )
    susp.expect_item_in_pending_table(item_name)


def test_settle_suspended_transaction(page: Page, suspended_setup: dict) -> None:
    """Settling a suspended transaction moves it to history."""
    navigate_to(page, "suspended")
    susp = SuspendedPage(page)
    item_name = f"Loan Settled {rand_id()}"
    susp.add_suspended(
        item_name=item_name,
        amount="200",
        currency_ticker="USD",
        susp_type="LOAN_OUT",
    )
    susp.expect_item_in_pending_table(item_name)
    susp.settle_item(item_name, period_name_fragment=suspended_setup["period_name"])
    susp.expect_item_in_history(item_name)
    # Should not be in pending anymore
    expect(
        page.locator("#susp-pending-table-container").get_by_text(item_name)
    ).not_to_be_visible(timeout=5_000)


def test_convert_suspended_to_expense(page: Page, suspended_setup: dict) -> None:
    """Converting a suspended transaction to expense moves it to history."""
    navigate_to(page, "suspended")
    susp = SuspendedPage(page)
    item_name = f"Return Never Came {rand_id()}"
    susp.add_suspended(
        item_name=item_name,
        amount="150",
        currency_ticker="USD",
        susp_type="PURCHASE_RETURN",
    )
    susp.expect_item_in_pending_table(item_name)
    # Convert to expense (use first available category)
    susp.convert_to_expense(item_name, category_name_fragment="")
    susp.expect_item_in_history(item_name)


def test_delete_suspended_transaction(page: Page, suspended_setup: dict) -> None:
    """User can delete a pending suspended transaction."""
    navigate_to(page, "suspended")
    susp = SuspendedPage(page)
    item_name = f"To Delete {rand_id()}"
    susp.add_suspended(
        item_name=item_name,
        amount="75",
        currency_ticker="USD",
        susp_type="OTHER",
    )
    susp.expect_item_in_pending_table(item_name)
    susp.delete_item(item_name)
    expect(
        page.locator("#susp-pending-table-container").get_by_text(item_name)
    ).not_to_be_visible(timeout=5_000)


def test_multiple_suspended_items_visible(page: Page, suspended_setup: dict) -> None:
    """Multiple suspended items are all shown in pending table."""
    navigate_to(page, "suspended")
    susp = SuspendedPage(page)
    rid = rand_id()
    items = [
        (f"Loan A {rid}", "100"),
        (f"Loan B {rid}", "200"),
        (f"Return C {rid}", "50"),
    ]
    for name, amt in items:
        navigate_to(page, "suspended")
        susp.add_suspended(name, amt, "USD", "LOAN_OUT")

    navigate_to(page, "suspended")
    for name, _ in items:
        susp.expect_item_in_pending_table(name)
