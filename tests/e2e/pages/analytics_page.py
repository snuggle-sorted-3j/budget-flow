"""Page Object Model for the Advanced Analytics tab."""
from playwright.sync_api import Page, expect


class AnalyticsPage:
    """Interactions with /dashboard/analytics-advanced."""

    def __init__(self, page: Page) -> None:
        self.page = page

    def wait_for_load(self, timeout: int = 15_000) -> None:
        """Wait for the analytics page content to load."""
        self.page.wait_for_selector("#advanced-report-btn", state="visible", timeout=timeout)

    def click_analyze_range(self) -> None:
        self.page.click("#analyze-range-btn")
        self.page.wait_for_timeout(2_000)

    def click_export_csv(self) -> None:
        self.page.click("#export-range-csv")
        self.page.wait_for_timeout(2_000)

    def click_download_full_report(self) -> None:
        self.page.click("#advanced-report-btn")
        self.page.wait_for_timeout(2_000)

    def expect_savings_rate_chart_visible(self, timeout: int = 10_000) -> None:
        expect(self.page.locator("#advanced-savings-rate-chart")).to_be_visible(
            timeout=timeout
        )

    def expect_insights_visible(self, timeout: int = 10_000) -> None:
        expect(self.page.locator("#advanced-insights-container")).to_be_visible(
            timeout=timeout
        )

    def expect_anomalies_visible(self, timeout: int = 10_000) -> None:
        expect(self.page.locator("#advanced-anomalies-container")).to_be_visible(
            timeout=timeout
        )

    def expect_category_deep_dive_visible(self, timeout: int = 10_000) -> None:
        expect(self.page.locator("#advanced-category-deep-dive")).to_be_visible(
            timeout=timeout
        )

    def expect_recurring_patterns_visible(self, timeout: int = 10_000) -> None:
        expect(self.page.locator("#advanced-recurring-patterns")).to_be_visible(
            timeout=timeout
        )
