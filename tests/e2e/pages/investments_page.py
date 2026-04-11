"""Page Object Model for the Investments tab."""
from playwright.sync_api import Page, expect


class InvestmentsPage:
    """Interactions with /dashboard/investments."""

    def __init__(self, page: Page) -> None:
        self.page = page

    # ── Section 1: Investment Accounts ────────────────────────

    def add_investment_account(
        self,
        name: str,
        account_type: str = "BROKERAGE",
        notes: str = "",
    ) -> None:
        self.page.wait_for_selector("#inv-account-name", state="visible", timeout=10_000)
        self.page.fill("#inv-account-name", name)
        self.page.select_option("#inv-account-type", value=account_type)
        if notes:
            self.page.fill("#inv-account-notes", notes)
        self.page.click("#add-inv-account-btn")
        self.page.wait_for_timeout(1_200)

    def expect_account_in_table(self, name: str) -> None:
        expect(
            self.page.locator("#inv-accounts-table-container").get_by_text(name)
        ).to_be_visible(timeout=8_000)

    def expect_account_form_success(self, timeout: int = 5_000) -> None:
        alert = self.page.locator("#inv-account-form-alert")
        expect(alert).to_be_visible(timeout=timeout)

    # ── Section 2: Investment Categories ─────────────────────

    def add_investment_category(
        self,
        name: str,
        account_name_fragment: str,
        opening_balance: float = 0.0,
        currency_ticker: str = "USD",
    ) -> None:
        self.page.wait_for_selector("#inv-category-name", state="visible", timeout=10_000)
        self.page.fill("#inv-category-name", name)
        # Dropdown is a dcc.Dropdown
        account_dropdown = self.page.locator("#inv-category-account-select")
        account_dropdown.click()
        self.page.get_by_role("option", name=account_name_fragment).first.click()
        if opening_balance > 0:
            self.page.fill("#inv-opening-balance", str(opening_balance))
            currency_dd = self.page.locator("#inv-opening-currency")
            currency_dd.click()
            self.page.get_by_role("option", name=currency_ticker).first.click()
        self.page.click("#add-inv-category-btn")
        self.page.wait_for_timeout(1_200)

    def expect_category_in_table(self, name: str) -> None:
        expect(
            self.page.locator("#inv-categories-table-container").get_by_text(name)
        ).to_be_visible(timeout=8_000)

    def expect_category_form_success(self, timeout: int = 5_000) -> None:
        alert = self.page.locator("#inv-category-form-alert")
        expect(alert).to_be_visible(timeout=timeout)

    # ── Section 3: Transfers ───────────────────────────────────

    def add_transfer(
        self,
        category_name_fragment: str,
        amount: str,
        currency_ticker: str = "USD",
        source_account_fragment: str = "",
        date: str = "2026-01-15",
        units: str = "",
    ) -> None:
        self.page.wait_for_selector("#inv-transfer-amount", state="visible", timeout=10_000)
        # Category dropdown
        cat_dd = self.page.locator("#inv-transfer-category-select")
        cat_dd.click()
        self.page.get_by_role("option", name=category_name_fragment).first.click()
        self.page.fill("#inv-transfer-amount", amount)
        if units:
            self.page.fill("#inv-transfer-units", units)
        # Currency dropdown
        curr_dd = self.page.locator("#inv-transfer-currency")
        curr_dd.click()
        self.page.get_by_role("option", name=currency_ticker).first.click()
        if source_account_fragment:
            acct_dd = self.page.locator("#inv-transfer-source-account")
            acct_dd.click()
            self.page.get_by_role("option", name=source_account_fragment).first.click()
        self.page.fill("#inv-transfer-date", date)
        self.page.click("#add-inv-transfer-btn")
        self.page.wait_for_timeout(1_200)

    def expect_transfer_in_table(self, amount_fragment: str) -> None:
        expect(
            self.page.locator("#inv-transfers-table-container").get_by_text(amount_fragment)
        ).to_be_visible(timeout=8_000)

    def expect_transfer_form_success(self, timeout: int = 5_000) -> None:
        alert = self.page.locator("#inv-transfer-form-alert")
        expect(alert).to_be_visible(timeout=timeout)
