"""
E2E Flow: Period Management

Covers:
- Period creation, listing, deletion
- Full reconciliation cycle (balanced → finalize)
- Period with unbalanced reconciliation (cannot finalize)
- Period unfreezing (unfinalize)
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
    add_income,
    add_expense,
    navigate_to,
)
from tests.e2e.pages.period_page import PeriodPage
from tests.e2e.pages.reconciliation_page import ReconciliationPage


@pytest.fixture
def period_setup(page: Page) -> dict:
    """Setup: fresh user with USD, account."""
    email = make_email("period")
    register_and_login(page, email)
    rid = rand_id()
    create_currency(page, "USD", "US Dollar", is_default=True)
    create_account(page, "Main Bank", "BANK", "USD")
    return {"rid": rid}


def test_create_and_list_period(page: Page, period_setup: dict) -> None:
    """Period appears in the table after creation."""
    navigate_to(page, "periods")
    pp = PeriodPage(page)
    period_name = f"List Test {period_setup['rid']}"
    pp.create_period(period_name, "2026-01-01", "2026-01-31")
    pp.expect_period_in_table(period_name)


def test_full_reconciliation_and_finalize(page: Page, period_setup: dict) -> None:
    """Full cycle: income + expense → balanced reconciliation → finalize."""
    rid = period_setup["rid"]
    period_name = f"Full Recon {rid}"
    create_period(page, period_name, "2026-01-01", "2026-01-31")
    select_period(page, period_name)

    add_income(page, "Salary", "5000", "USD")
    add_expense(page, "Rent", "1500", "USD")
    add_expense(page, "Food", "500", "USD")

    navigate_to(page, "reconciliation")
    recon = ReconciliationPage(page)
    recon.wait_for_content()
    # Expected balance: 5000 - 1500 - 500 = 3000
    recon.fill_first_snapshot("3000")
    recon.save_snapshots()
    recon.expect_snapshot_saved()
    recon.expect_recon_balanced()
    recon.open_finalize_modal()
    recon.confirm_finalize()
    recon.expect_period_finalized()


def test_unbalanced_period_cannot_finalize(page: Page, period_setup: dict) -> None:
    """A period with incorrect snapshot balance shows unbalanced status."""
    rid = period_setup["rid"]
    period_name = f"Unbalanced {rid}"
    create_period(page, period_name, "2026-02-01", "2026-02-28")
    select_period(page, period_name)

    add_income(page, "Income", "3000", "USD")

    navigate_to(page, "reconciliation")
    recon = ReconciliationPage(page)
    recon.wait_for_content()
    # Wrong balance: 999 instead of 3000
    recon.fill_first_snapshot("999")
    recon.save_snapshots()
    recon.expect_snapshot_saved()
    recon.expect_recon_unbalanced()
    # Finalize button should not be accessible / period should not be FINALIZED
    expect(
        page.locator("#global-period-selector")
    ).not_to_contain_text("FINALIZED", timeout=3_000)


def test_delete_period(page: Page, period_setup: dict) -> None:
    """Deleting a period removes it from the list."""
    rid = period_setup["rid"]
    period_name = f"Delete Me {rid}"
    navigate_to(page, "periods")
    pp = PeriodPage(page)
    pp.create_period(period_name, "2026-03-01", "2026-03-31")
    pp.expect_period_in_table(period_name)
    pp.delete_period(period_name)
    pp.expect_period_not_in_table(period_name)


def test_period_shows_in_global_selector(page: Page, period_setup: dict) -> None:
    """Newly created period appears in the global period selector."""
    rid = period_setup["rid"]
    period_name = f"Selector Test {rid}"
    create_period(page, period_name, "2026-04-01", "2026-04-30")
    # Navigate to any page and check selector
    navigate_to(page, "income")
    page.wait_for_timeout(1_000)
    selector_options = page.locator("#global-period-selector option").all_inner_texts()
    assert any(period_name.lower() in opt.lower() for opt in selector_options), (
        f"Period '{period_name}' not found in global selector options: {selector_options}"
    )
