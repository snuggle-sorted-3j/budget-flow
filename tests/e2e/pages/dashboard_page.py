"""Page Object Model for the BudgetFlow Dashboard (sidebar navigation + global controls)."""
from playwright.sync_api import Page, expect


BASE_URL = "http://localhost:8050"

# Sidebar section slugs
SECTIONS = {
    "dashboard": "/dashboard",
    "analytics": "/dashboard/analytics-advanced",
    "periods": "/dashboard/periods",
    "income": "/dashboard/income",
    "expenses": "/dashboard/expenses",
    "reconciliation": "/dashboard/reconciliation",
    "investments": "/dashboard/investments",
    "suspended": "/dashboard/suspended",
    "installments": "/dashboard/installments",
    "conversions": "/dashboard/conversions",
    "accounts": "/dashboard/accounts",
    "currencies": "/dashboard/currencies",
    "categories": "/dashboard/categories",
    "templates": "/dashboard/templates",
}


class DashboardPage:
    """Top-level dashboard interactions: navigation, period selector, header."""

    def __init__(self, page: Page) -> None:
        self.page = page

    def navigate_to(self, section: str) -> None:
        """Navigate to a dashboard section by key.

        Args:
            section: One of the keys in SECTIONS dict (e.g. 'income', 'periods').
        """
        path = SECTIONS.get(section, f"/dashboard/{section}")
        self.page.goto(f"{BASE_URL}{path}")
        self.page.wait_for_load_state("networkidle", timeout=10_000)

    def select_period(self, period_name_fragment: str) -> None:
        """Select a period by name fragment in the global header selector."""
        selector = self.page.locator("#global-period-selector")
        selector.wait_for(state="visible", timeout=10_000)
        page = self.page
        page.wait_for_function(
            "document.querySelector('#global-period-selector option') !== null",
            timeout=10_000,
        )
        options = selector.locator("option").all_inner_texts()
        target = next(
            (opt for opt in options if period_name_fragment.lower() in opt.lower()), None
        )
        if not target:
            raise ValueError(
                f"Period '{period_name_fragment}' not found. Available: {options}"
            )
        selector.select_option(label=target)
        self.page.wait_for_timeout(500)

    def get_current_period_value(self) -> str:
        return self.page.locator("#global-period-selector").input_value()

    def expect_header_visible(self) -> None:
        expect(self.page.locator(".user-dropdown-toggle")).to_be_visible()

    def expect_section_loaded(self, content_id: str, timeout: int = 10_000) -> None:
        expect(self.page.locator(f"#{content_id}")).to_be_visible(timeout=timeout)
