"""
E2E Flow: Installment Lifecycle

Covers:
- Create an installment plan
- Make payments over multiple months
- Verify status transitions (ACTIVE → PAID_OFF)
- Delete an installment plan
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
from tests.e2e.pages.installments_page import InstallmentsPage


@pytest.fixture
def installment_setup(page: Page) -> dict:
    """Setup: fresh user with USD, account, and a period."""
    email = make_email("inst")
    register_and_login(page, email)
    rid = rand_id()
    period_name = f"Jan 2026 {rid}"
    create_currency(page, "USD", "US Dollar", is_default=True)
    create_account(page, "Main Bank", "BANK", "USD")
    create_period(page, period_name, "2026-01-01", "2026-01-31")
    select_period(page, period_name)
    return {"period_name": period_name}


def test_create_installment_plan(page: Page, installment_setup: dict) -> None:
    """User can create an installment plan that appears in the active list."""
    navigate_to(page, "installments")
    inst = InstallmentsPage(page)
    inst.add_installment(
        name="Laptop Pro 16",
        total_price="3600",
        currency_ticker="USD",
        start_period_fragment=installment_setup["period_name"],
        monthly_payment="300",
        months="12",
    )
    inst.expect_installment_in_active_list("Laptop Pro 16")


def test_installment_partial_payment(page: Page, installment_setup: dict) -> None:
    """User can make a partial payment reducing the remaining balance."""
    navigate_to(page, "installments")
    inst = InstallmentsPage(page)
    plan_name = f"Phone {rand_id()}"
    inst.add_installment(
        name=plan_name,
        total_price="1200",
        currency_ticker="USD",
        start_period_fragment=installment_setup["period_name"],
        monthly_payment="100",
    )
    inst.expect_installment_in_active_list(plan_name)
    # Make a payment
    inst.open_payment_modal_for(plan_name)
    inst.fill_payment("100", "2026-01-15")
    inst.expect_installment_in_active_list(plan_name)


def test_installment_paid_off_transition(page: Page, installment_setup: dict) -> None:
    """Paying the full amount moves installment to Paid Off section."""
    navigate_to(page, "installments")
    inst = InstallmentsPage(page)
    plan_name = f"SmallItem {rand_id()}"
    inst.add_installment(
        name=plan_name,
        total_price="100",
        currency_ticker="USD",
        start_period_fragment=installment_setup["period_name"],
    )
    inst.expect_installment_in_active_list(plan_name)
    # Pay off completely in one payment
    inst.open_payment_modal_for(plan_name)
    inst.fill_payment("100", "2026-01-10")
    # Should now be in paid-off section
    inst.expect_installment_paid_off(plan_name)


def test_delete_installment_plan(page: Page, installment_setup: dict) -> None:
    """Deleting a plan removes it from the active list."""
    navigate_to(page, "installments")
    inst = InstallmentsPage(page)
    plan_name = f"Deletable {rand_id()}"
    inst.add_installment(
        name=plan_name,
        total_price="500",
        currency_ticker="USD",
        start_period_fragment=installment_setup["period_name"],
    )
    inst.expect_installment_in_active_list(plan_name)
    inst.delete_installment(plan_name)
    # Should no longer be in active list
    expect(
        page.locator("#active-installments-container").get_by_text(plan_name)
    ).not_to_be_visible(timeout=5_000)
