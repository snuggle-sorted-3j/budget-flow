"""Page Object Model for the Income Management tab."""
from playwright.sync_api import Page, expect


class IncomePage:
    """Interactions with /dashboard/income."""

    def __init__(self, page: Page) -> None:
        self.page = page

    def wait_for_form(self) -> None:
        self.page.wait_for_selector("#income-source-name", state="visible", timeout=10_000)

    def add_income(
        self,
        source: str,
        amount: str,
        currency_ticker: str = "USD",
        notes: str = "",
        tax_applicable: bool = False,
        is_recurring: bool = False,
    ) -> None:
        """Fill and submit the Add Income form."""
        self.wait_for_form()
        self.page.fill("#income-source-name", source)
        self.page.fill("#income-amount", amount)
        self.page.wait_for_selector(
            f"#income-currency option:has-text('{currency_ticker}')", state="attached"
        )
        self.page.select_option("#income-currency", label=currency_ticker)
        if notes:
            self.page.fill("#income-notes", notes)
        if tax_applicable:
            self.page.locator("#income-tax-applicable").check()
        if is_recurring:
            self.page.locator("#income-is-recurring").check()
        self.page.click("#add-income-btn")
        self.page.wait_for_timeout(1_000)

    def expect_success(self, timeout: int = 5_000) -> None:
        alert = self.page.locator("#income-form-alert")
        expect(alert).to_be_visible(timeout=timeout)

    def expect_income_in_table(self, source: str) -> None:
        expect(
            self.page.locator("#income-table-container").get_by_text(source)
        ).to_be_visible(timeout=8_000)

    def delete_income(self, source: str) -> None:
        """Delete an income entry by source name."""
        row_text = self.page.locator("#income-table-container").get_by_text(source).first
        row_text.locator("xpath=ancestor::tr").get_by_role("button", name="Delete").click()
        self.page.locator("#income-delete-confirm").click()
        self.page.wait_for_timeout(1_000)
