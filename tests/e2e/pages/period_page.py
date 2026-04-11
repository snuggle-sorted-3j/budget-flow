"""Page Object Model for the Period Setup tab."""
from playwright.sync_api import Page, expect


class PeriodPage:
    """Interactions with /dashboard/periods."""

    def __init__(self, page: Page) -> None:
        self.page = page

    def create_period(
        self,
        name: str,
        start_date: str = "2026-01-01",
        end_date: str = "2026-01-31",
    ) -> None:
        """Fill and submit the Create Period form."""
        self.page.wait_for_selector("#period-name-input", state="visible", timeout=10_000)
        self.page.fill("#period-name-input", name)
        self.page.fill("#period-start-date", start_date)
        self.page.fill("#period-end-date", end_date)
        self.page.click("#create-period-btn")
        self.page.wait_for_timeout(1_500)

    def create_period_with_template(
        self,
        name: str,
        template_name_fragment: str,
        start_date: str = "2026-02-01",
        end_date: str = "2026-02-28",
    ) -> None:
        """Create a period and apply a template."""
        self.page.wait_for_selector("#period-name-input", state="visible", timeout=10_000)
        self.page.fill("#period-name-input", name)
        self.page.fill("#period-start-date", start_date)
        self.page.fill("#period-end-date", end_date)
        self.page.locator("#period-apply-template-check").check()
        self.page.wait_for_selector("#period-template-dropdown", state="visible", timeout=5_000)
        self.page.wait_for_timeout(1_000)  # let dropdown populate
        self.page.select_option("#period-template-dropdown", label=template_name_fragment)
        self.page.click("#create-period-btn")
        self.page.wait_for_timeout(2_000)

    def expect_success(self, timeout: int = 5_000) -> None:
        # Success shows up in the form alert or toast
        alert = self.page.locator("#period-form-alert")
        expect(alert).to_be_visible(timeout=timeout)
        expect(alert).not_to_contain_text("error", timeout=timeout)

    def expect_period_in_table(self, period_name: str) -> None:
        expect(
            self.page.locator("#period-table-container").get_by_text(period_name)
        ).to_be_visible(timeout=10_000)

    def delete_period(self, period_name: str) -> None:
        """Click delete for a period row and confirm."""
        row = self.page.locator("#period-table-container").get_by_text(period_name).first
        row.locator("xpath=ancestor::tr").get_by_role("button", name="Delete").click()
        self.page.locator("#period-delete-confirm").click()
        self.page.wait_for_timeout(1_500)

    def expect_period_not_in_table(self, period_name: str) -> None:
        expect(
            self.page.locator("#period-table-container").get_by_text(period_name)
        ).not_to_be_visible(timeout=5_000)
