"""Page Object Model for the Suspended Transactions tab."""
from playwright.sync_api import Page, expect


class SuspendedPage:
    """Interactions with /dashboard/suspended."""

    def __init__(self, page: Page) -> None:
        self.page = page

    def add_suspended(
        self,
        item_name: str,
        amount: str,
        currency_ticker: str = "USD",
        susp_type: str = "LOAN_OUT",
        notes: str = "",
    ) -> None:
        """Add a new suspended transaction."""
        self.page.wait_for_selector("#susp-item-name", state="visible", timeout=10_000)
        self.page.fill("#susp-item-name", item_name)
        self.page.fill("#susp-amount", amount)
        # Currency is a dcc.Dropdown
        curr_dd = self.page.locator("#susp-currency")
        curr_dd.click()
        self.page.get_by_role("option", name=currency_ticker).first.click()
        self.page.select_option("#susp-type", value=susp_type)
        if notes:
            self.page.fill("#susp-notes", notes)
        self.page.click("#add-susp-btn")
        self.page.wait_for_timeout(1_200)

    def expect_success(self, timeout: int = 5_000) -> None:
        alert = self.page.locator("#susp-form-alert")
        expect(alert).to_be_visible(timeout=timeout)

    def expect_item_in_pending_table(self, item_name: str) -> None:
        expect(
            self.page.locator("#susp-pending-table-container").get_by_text(item_name)
        ).to_be_visible(timeout=8_000)

    def expect_item_in_history(self, item_name: str) -> None:
        expect(
            self.page.locator("#susp-history-table-container").get_by_text(item_name)
        ).to_be_visible(timeout=8_000)

    def settle_item(self, item_name: str, period_name_fragment: str) -> None:
        """Open the settle modal for an item and confirm."""
        self.page.locator("#susp-pending-table-container").get_by_text(
            item_name
        ).first.locator("xpath=ancestor::tr").get_by_role("button", name="Settle").click()
        self.page.wait_for_selector("#settle-period-select", state="visible", timeout=5_000)
        # settle-period-select is a dcc.Dropdown
        self.page.locator("#settle-period-select").click()
        self.page.get_by_role("option", name=period_name_fragment).first.click()
        self.page.click("#settle-confirm-btn")
        self.page.wait_for_timeout(1_500)

    def convert_to_expense(self, item_name: str, category_name_fragment: str) -> None:
        """Open the convert modal for an item and confirm."""
        self.page.locator("#susp-pending-table-container").get_by_text(
            item_name
        ).first.locator("xpath=ancestor::tr").get_by_role("button", name="Convert").click()
        self.page.wait_for_selector("#convert-category-select", state="visible", timeout=5_000)
        # convert-category-select is a dcc.Dropdown
        self.page.locator("#convert-category-select").click()
        self.page.get_by_role("option", name=category_name_fragment).first.click()
        self.page.click("#convert-confirm-btn")
        self.page.wait_for_timeout(1_500)

    def delete_item(self, item_name: str) -> None:
        self.page.locator("#susp-pending-table-container").get_by_text(
            item_name
        ).first.locator("xpath=ancestor::tr").get_by_role("button", name="Delete").click()
        self.page.locator("#susp-delete-confirm").click()
        self.page.wait_for_timeout(1_000)
