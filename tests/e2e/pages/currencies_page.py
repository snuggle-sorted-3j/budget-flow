"""Page Object Model for the Currencies Management tab."""
from playwright.sync_api import Page, expect


class CurrenciesPage:
    """Interactions with /dashboard/currencies."""

    def __init__(self, page: Page) -> None:
        self.page = page

    def add_currency(self, ticker: str, name: str, is_default: bool = False) -> None:
        """Fill and submit the Add Currency form."""
        self.page.wait_for_selector("#currency-ticker", state="visible", timeout=10_000)
        self.page.fill("#currency-ticker", ticker)
        self.page.fill("#currency-name", name)
        if is_default:
            self.page.locator("#currency-default").check()
        else:
            # Ensure checkbox is unchecked
            cb = self.page.locator("#currency-default")
            if cb.is_checked():
                cb.uncheck()
        self.page.click("#add-currency-btn")
        self.page.wait_for_timeout(1_000)

    def expect_success_message(self, text_fragment: str = "added", timeout: int = 5_000) -> None:
        expect(self.page.locator("#currency-message")).to_contain_text(text_fragment, timeout=timeout)

    def expect_currency_in_table(self, ticker: str) -> None:
        expect(
            self.page.locator("#currency-table-container").get_by_text(ticker)
        ).to_be_visible(timeout=8_000)

    def expect_error_message(self, text_fragment: str, timeout: int = 5_000) -> None:
        expect(self.page.locator("#currency-message")).to_contain_text(text_fragment, timeout=timeout)
