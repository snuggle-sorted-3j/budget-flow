"""Page Object Model for the Currency Conversions tab."""
from playwright.sync_api import Page, expect


class ConversionsPage:
    """Interactions with /dashboard/conversions."""

    def __init__(self, page: Page) -> None:
        self.page = page

    def add_conversion(
        self,
        from_currency: str,
        from_amount: str,
        to_currency: str,
        to_amount: str,
        rate: str,
        date: str,
        notes: str = "",
    ) -> None:
        """Fill and submit the Record Conversion form."""
        self.page.wait_for_selector("#conv-from-currency", state="visible", timeout=10_000)
        self.page.wait_for_selector(
            f"#conv-from-currency option:has-text('{from_currency}')", state="attached"
        )
        self.page.select_option("#conv-from-currency", label=from_currency)
        self.page.fill("#conv-from-amount", from_amount)
        self.page.wait_for_selector(
            f"#conv-to-currency option:has-text('{to_currency}')", state="attached"
        )
        self.page.select_option("#conv-to-currency", label=to_currency)
        self.page.fill("#conv-to-amount", to_amount)
        self.page.fill("#conv-rate", rate)
        self.page.fill("#conv-date", date)
        if notes:
            self.page.fill("#conv-notes", notes)
        self.page.click("#add-conv-btn")
        self.page.wait_for_timeout(1_200)

    def expect_success(self, timeout: int = 5_000) -> None:
        alert = self.page.locator("#conv-form-alert")
        expect(alert).to_be_visible(timeout=timeout)

    def expect_conversion_in_table(self, text_fragment: str) -> None:
        expect(
            self.page.locator("#conversions-table-container").get_by_text(text_fragment)
        ).to_be_visible(timeout=8_000)

    def expect_error(self, text_fragment: str, timeout: int = 5_000) -> None:
        alert = self.page.locator("#conv-form-alert")
        expect(alert).to_contain_text(text_fragment, timeout=timeout)
