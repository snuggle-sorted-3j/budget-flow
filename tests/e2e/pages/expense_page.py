"""Page Object Model for the Expenses Management tab."""
from playwright.sync_api import Page, expect


class ExpensePage:
    """Interactions with /dashboard/expenses."""

    def __init__(self, page: Page) -> None:
        self.page = page

    def wait_for_form(self) -> None:
        self.page.wait_for_selector("#expense-item-name", state="visible", timeout=10_000)

    def add_expense(
        self,
        item_name: str,
        amount: str,
        currency_ticker: str = "USD",
        category_index: int = 1,
        notes: str = "",
        is_recurring: bool = False,
    ) -> None:
        """Fill and submit the Add Expense form."""
        self.wait_for_form()
        self.page.wait_for_selector("#expense-category option", state="attached")
        self.page.select_option("#expense-category", index=category_index)
        self.page.fill("#expense-item-name", item_name)
        self.page.fill("#expense-amount", amount)
        self.page.wait_for_selector(
            f"#expense-currency option:has-text('{currency_ticker}')", state="attached"
        )
        self.page.select_option("#expense-currency", label=currency_ticker)
        if notes:
            self.page.fill("#expense-notes", notes)
        if is_recurring:
            self.page.locator("#expense-is-recurring").check()
        self.page.click("#add-expense-btn")
        self.page.wait_for_timeout(1_000)

    def expect_success(self, timeout: int = 5_000) -> None:
        alert = self.page.locator("#expense-form-alert")
        expect(alert).to_be_visible(timeout=timeout)

    def expect_expense_in_table(self, item_name: str) -> None:
        expect(
            self.page.locator("#expense-table-container").get_by_text(item_name)
        ).to_be_visible(timeout=8_000)

    def delete_expense(self, item_name: str) -> None:
        row_text = self.page.locator("#expense-table-container").get_by_text(item_name).first
        row_text.locator("xpath=ancestor::tr").get_by_role("button", name="Delete").click()
        self.page.locator("#expense-delete-confirm").click()
        self.page.wait_for_timeout(1_000)
