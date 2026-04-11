"""
E2E Flow: Investment Tracking

Covers:
- Create investment account
- Create investment category (holding)
- Record transfer from bank account to investment
- Verify all items appear in their respective tables
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
from tests.e2e.pages.investments_page import InvestmentsPage


@pytest.fixture
def investment_setup(page: Page) -> dict:
    """Setup: fresh user, USD currency, two bank accounts, and a period."""
    email = make_email("inv")
    register_and_login(page, email)
    rid = rand_id()
    period_name = f"Inv Period {rid}"
    create_currency(page, "USD", "US Dollar", is_default=True)
    create_account(page, "Main Bank", "BANK", "USD")
    create_period(page, period_name, "2026-01-01", "2026-01-31")
    select_period(page, period_name)
    return {"period_name": period_name}


def test_create_investment_account(page: Page, investment_setup: dict) -> None:
    """User can create an investment account."""
    navigate_to(page, "investments")
    inv = InvestmentsPage(page)
    acct_name = f"IBKR {rand_id()}"
    inv.add_investment_account(name=acct_name, account_type="BROKERAGE", notes="Interactive Brokers")
    inv.expect_account_in_table(acct_name)


def test_create_investment_category(page: Page, investment_setup: dict) -> None:
    """User can create an investment category linked to an account."""
    navigate_to(page, "investments")
    inv = InvestmentsPage(page)
    acct_name = f"Crypto {rand_id()}"
    inv.add_investment_account(name=acct_name, account_type="CRYPTO_EXCHANGE")
    inv.expect_account_in_table(acct_name)

    cat_name = f"Bitcoin {rand_id()}"
    inv.add_investment_category(
        name=cat_name,
        account_name_fragment=acct_name,
    )
    inv.expect_category_in_table(cat_name)


def test_record_investment_transfer(page: Page, investment_setup: dict) -> None:
    """User can record a transfer from bank to investment account."""
    navigate_to(page, "investments")
    inv = InvestmentsPage(page)
    acct_name = f"Brokerage {rand_id()}"
    inv.add_investment_account(name=acct_name, account_type="BROKERAGE")

    cat_name = f"SP500 ETF {rand_id()}"
    inv.add_investment_category(
        name=cat_name,
        account_name_fragment=acct_name,
    )

    # Navigate to investments again to record transfer
    navigate_to(page, "investments")
    inv.add_transfer(
        category_name_fragment=cat_name,
        amount="1000",
        currency_ticker="USD",
        source_account_fragment="Main Bank",
        date="2026-01-15",
        units="2.5",
    )
    inv.expect_transfer_in_table("1000")


def test_investment_full_workflow(page: Page, investment_setup: dict) -> None:
    """Full workflow: account → category → transfer → all visible."""
    navigate_to(page, "investments")
    inv = InvestmentsPage(page)
    rid = rand_id()

    inv.add_investment_account(name=f"Full Test Acct {rid}", account_type="BROKERAGE")
    inv.add_investment_category(
        name=f"Index Fund {rid}",
        account_name_fragment=f"Full Test Acct {rid}",
        opening_balance=500.0,
        currency_ticker="USD",
    )
    navigate_to(page, "investments")
    inv.add_transfer(
        category_name_fragment=f"Index Fund {rid}",
        amount="500",
        currency_ticker="USD",
        source_account_fragment="Main Bank",
        date="2026-01-20",
    )

    inv.expect_account_in_table(f"Full Test Acct {rid}")
    inv.expect_category_in_table(f"Index Fund {rid}")
    inv.expect_transfer_in_table("500")
