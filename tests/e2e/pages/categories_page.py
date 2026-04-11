"""Page Object Model for the Expense Categories tab."""
from playwright.sync_api import Page, expect


class CategoriesPage:
    """Interactions with /dashboard/categories."""

    def __init__(self, page: Page) -> None:
        self.page = page

    def add_category(self, name: str, parent_index: int = 0, icon: str = "") -> None:
        """Fill and submit the Add Category form.

        Args:
            name: Category display name.
            parent_index: Index of parent category in dropdown (0 = no parent).
            icon: Optional emoji icon string.
        """
        self.page.wait_for_selector("#category-name-input", state="visible", timeout=10_000)
        self.page.fill("#category-name-input", name)
        if parent_index > 0:
            self.page.select_option("#category-parent-input", index=parent_index)
        if icon:
            self.page.fill("#category-description-input", icon)
        self.page.click("#add-category-btn")
        self.page.wait_for_timeout(1_000)

    def expect_success_message(self, text_fragment: str = "added", timeout: int = 5_000) -> None:
        expect(self.page.locator("#category-message")).to_contain_text(text_fragment, timeout=timeout)

    def expect_category_in_table(self, name: str) -> None:
        expect(
            self.page.locator("#category-table-container").get_by_text(name)
        ).to_be_visible(timeout=8_000)

    def expect_error_message(self, text_fragment: str, timeout: int = 5_000) -> None:
        expect(self.page.locator("#category-message")).to_contain_text(text_fragment, timeout=timeout)
