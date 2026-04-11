"""
E2E Flow: Analytics Dashboard

Covers:
- Analytics page loads with existing data
- All chart sections render (savings rate, insights, anomalies, deep dive, recurring)
- Download CSV button is present and clickable
- Date range analysis trigger
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
from tests.e2e.pages.analytics_page import AnalyticsPage


@pytest.fixture
def analytics_setup(page: Page) -> dict:
    """Setup: user with 2 periods of data for meaningful analytics."""
    email = make_email("analytics")
    register_and_login(page, email)
    rid = rand_id()

    create_currency(page, "USD", "US Dollar", is_default=True)
    create_account(page, "Main Bank", "BANK", "USD")

    period1 = f"Jan 2026 {rid}"
    create_period(page, period1, "2026-01-01", "2026-01-31")
    select_period(page, period1)
    add_income(page, "Salary", "5000", "USD")
    add_expense(page, "Rent", "1500", "USD")
    add_expense(page, "Food", "500", "USD")
    add_expense(page, "Transport", "200", "USD")

    period2 = f"Feb 2026 {rid}"
    create_period(page, period2, "2026-02-01", "2026-02-28")
    select_period(page, period2)
    add_income(page, "Salary", "5200", "USD")
    add_expense(page, "Rent", "1500", "USD")
    add_expense(page, "Food", "600", "USD")

    return {"period1": period1, "period2": period2, "rid": rid}


def test_analytics_page_loads(page: Page, analytics_setup: dict) -> None:
    """Analytics page loads and shows the download report button."""
    navigate_to(page, "analytics")
    analytics = AnalyticsPage(page)
    analytics.wait_for_load()
    expect(page.locator("#advanced-report-btn")).to_be_visible()


def test_analytics_sections_render(page: Page, analytics_setup: dict) -> None:
    """All main analytics sections are visible on the page."""
    navigate_to(page, "analytics")
    analytics = AnalyticsPage(page)
    analytics.wait_for_load()

    analytics.expect_savings_rate_chart_visible()
    analytics.expect_insights_visible()
    analytics.expect_anomalies_visible()
    analytics.expect_category_deep_dive_visible()
    analytics.expect_recurring_patterns_visible()


def test_analytics_date_range_trigger(page: Page, analytics_setup: dict) -> None:
    """Clicking Analyze Range does not crash the page."""
    navigate_to(page, "analytics")
    analytics = AnalyticsPage(page)
    analytics.wait_for_load()
    analytics.click_analyze_range()
    # After click, page should remain stable
    expect(page.locator("#advanced-report-btn")).to_be_visible(timeout=10_000)


def test_analytics_export_csv_available(page: Page, analytics_setup: dict) -> None:
    """Export CSV button is present and clickable."""
    navigate_to(page, "analytics")
    analytics = AnalyticsPage(page)
    analytics.wait_for_load()
    expect(page.locator("#export-range-csv")).to_be_visible()
    # Click without crashing
    analytics.click_export_csv()
    page.wait_for_timeout(1_000)


def test_analytics_no_crash_with_no_data(page: Page) -> None:
    """Analytics page does not crash for a user with no data."""
    email = make_email("nodata_analytics")
    register_and_login(page, email)
    navigate_to(page, "analytics")
    analytics = AnalyticsPage(page)
    analytics.wait_for_load()
    expect(page.locator("#advanced-report-btn")).to_be_visible()
