"""Page Object Model for the Accounts Management tab."""
from playwright.sync_api import Page, expect


class AccountsPage:
    """Interactions with /dashboard/accounts."""

    def __init__(self, page: Page) -> None:
        self.page = page

    def add_account(
        self,
        name: str,
        account_type: str = "BANK",
        currency_ticker: str = "USD",
        opening_balance: float = 0.0,
    ) -> None:
        """Fill and submit the Add Account form."""
        self.page.wait_for_selector("#account-name-input", state="visible", timeout=10_000)
        self.page.fill("#account-name-input", name)
        self.page.select_option("#account-type-select", value=account_type)
        self.page.wait_for_selector(
            f"#account-currency-select option:has-text('{currency_ticker}')", state="attached"
        )
        self.page.select_option("#account-currency-select", label=currency_ticker)
        if opening_balance != 0.0:
            self.page.fill("#account-opening-balance", str(opening_balance))
        self.page.click("#add-account-btn")
        self.page.wait_for_timeout(1_000)

    def expect_success(self, timeout: int = 5_000) -> None:
        alert = self.page.locator("#account-form-alert")
        expect(alert).to_be_visible(timeout=timeout)

    def expect_account_in_table(self, name: str) -> None:
        expect(
            self.page.locator("#account-table-container").get_by_text(name)
        ).to_be_visible(timeout=8_000)

    def delete_account(self, name: str) -> None:
        row = self.page.locator("#account-table-container").get_by_text(name).first
        row.locator("xpath=ancestor::tr").get_by_role("button", name="Delete").click()
        self.page.locator("#account-delete-confirm").click()
        self.page.wait_for_timeout(1_000)
