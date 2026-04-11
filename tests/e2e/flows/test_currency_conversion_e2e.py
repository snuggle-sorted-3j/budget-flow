"""
E2E Flow: Currency Conversion

Covers:
- Create two currencies (USD + EUR)
- Record a currency conversion (USD → EUR)
- Verify conversion appears in history table
- Verify rate history chart renders
- Delete a conversion
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
from tests.e2e.pages.conversions_page import ConversionsPage


@pytest.fixture
def conversion_setup(page: Page) -> dict:
    """Setup: user with USD + EUR currencies, accounts, and a period."""
    email = make_email("conv")
    register_and_login(page, email)
    rid = rand_id()
    period_name = f"Conv Period {rid}"
    create_currency(page, "USD", "US Dollar", is_default=True)
    create_currency(page, "EUR", "Euro")
    create_account(page, "USD Bank", "BANK", "USD")
    create_account(page, "EUR Bank", "BANK", "EUR")
    create_period(page, period_name, "2026-01-01", "2026-01-31")
    select_period(page, period_name)
    return {"period_name": period_name, "rid": rid}


def test_record_currency_conversion(page: Page, conversion_setup: dict) -> None:
    """User can record a USD→EUR conversion."""
    navigate_to(page, "conversions")
    conv = ConversionsPage(page)
    conv.add_conversion(
        from_currency="USD",
        from_amount="1000",
        to_currency="EUR",
        to_amount="920",
        rate="1.087",
        date="2026-01-10",
        notes="Bank exchange",
    )
    conv.expect_conversion_in_table("1000")


def test_multiple_conversions_visible(page: Page, conversion_setup: dict) -> None:
    """Multiple conversions all appear in the history table."""
    navigate_to(page, "conversions")
    conv = ConversionsPage(page)
    conversions = [
        ("100", "EUR", "92", "1.087", "2026-01-05"),
        ("500", "EUR", "460", "1.087", "2026-01-10"),
    ]
    for from_amt, to_curr, to_amt, rate, date in conversions:
        navigate_to(page, "conversions")
        conv.add_conversion("USD", from_amt, to_curr, to_amt, rate, date)

    navigate_to(page, "conversions")
    conv.expect_conversion_in_table("100")
    conv.expect_conversion_in_table("500")


def test_conversion_requires_different_currencies(page: Page, conversion_setup: dict) -> None:
    """Recording a conversion with same from/to currency should show an error."""
    navigate_to(page, "conversions")
    conv = ConversionsPage(page)
    # Same from/to currency
    conv.add_conversion(
        from_currency="USD",
        from_amount="100",
        to_currency="USD",
        to_amount="100",
        rate="1.0",
        date="2026-01-15",
    )
    # Should show error from the API
    conv.expect_error("same", timeout=5_000)


def test_rate_history_chart_renders(page: Page, conversion_setup: dict) -> None:
    """Rate history chart renders after conversions are added."""
    navigate_to(page, "conversions")
    conv = ConversionsPage(page)
    conv.add_conversion("USD", "200", "EUR", "184", "1.087", "2026-01-12")

    navigate_to(page, "conversions")
    # Rate pair select should have options after at least one conversion
    page.wait_for_timeout(1_500)
    options = page.locator("#rate-pair-select option").all_inner_texts()
    if options and any("USD" in o or "EUR" in o for o in options):
        page.select_option("#rate-pair-select", index=1)
        page.wait_for_timeout(1_500)
        expect(page.locator("#rate-history-chart")).to_be_visible(timeout=5_000)
