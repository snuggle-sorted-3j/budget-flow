"""
E2E Test Configuration and Fixtures for BudgetFlow.

Provides:
- Playwright browser fixtures
- Authenticated page fixtures (pre-logged-in user)
- Unique test data generators
- Shared helpers for common setup flows
"""
import random
import string
import pytest
from playwright.sync_api import Page, Browser, BrowserContext, Playwright, expect

BASE_URL = "http://localhost:8050"
DEFAULT_PASSWORD = "Password123!"


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

def rand_id(n: int = 6) -> str:
    """Generate a short random alphanumeric ID."""
    return "".join(random.choices(string.digits, k=n))


def make_email(prefix: str = "e2e") -> str:
    return f"{prefix}_{rand_id(8)}@test.com"


def register_and_login(page: Page, email: str, password: str = DEFAULT_PASSWORD) -> None:
    """Register a new user and log them in. Leaves the page at the dashboard."""
    page.goto(f"{BASE_URL}/register")
    page.fill("#register-email", email)
    page.fill("#register-fullname", "E2E Test User")
    page.fill("#register-password", password)
    page.click("#register-button")
    # After register, redirected to login
    expect(page.locator("#login-button")).to_be_visible(timeout=15_000)

    page.fill("#login-email", email)
    page.fill("#login-password", password)
    page.click("#login-button")
    # After login, dashboard header should appear
    expect(page.locator(".user-dropdown-toggle")).to_be_visible(timeout=15_000)


def navigate_to(page: Page, section: str) -> None:
    """Navigate to a dashboard section by slug.

    Args:
        page: Playwright page object.
        section: URL slug, e.g. 'periods', 'income', 'accounts'.
    """
    page.goto(f"{BASE_URL}/dashboard/{section}")
    page.wait_for_load_state("networkidle", timeout=10_000)


def select_period(page: Page, period_name_fragment: str) -> None:
    """Select a period in the global header period selector.

    Args:
        page: Playwright page object.
        period_name_fragment: Part of the period name to match (case-insensitive).
    """
    selector = page.locator("#global-period-selector")
    selector.wait_for(state="visible", timeout=10_000)
    # Wait for options to load
    page.wait_for_function(
        f"document.querySelector('#global-period-selector option') !== null",
        timeout=10_000,
    )
    # Select by label containing the fragment
    options = selector.locator("option").all_inner_texts()
    target = next((opt for opt in options if period_name_fragment.lower() in opt.lower()), None)
    if target:
        selector.select_option(label=target)
    else:
        raise ValueError(f"Period matching '{period_name_fragment}' not found. Options: {options}")


def create_currency(page: Page, ticker: str, name: str, is_default: bool = False) -> None:
    """Create a currency on the Currencies tab."""
    navigate_to(page, "currencies")
    page.wait_for_selector("#currency-ticker", state="visible")
    page.fill("#currency-ticker", ticker)
    page.fill("#currency-name", name)
    if is_default:
        page.locator("#currency-default").check()
    page.click("#add-currency-btn")
    page.wait_for_timeout(1_000)


def create_account(page: Page, name: str, account_type: str = "BANK", currency_ticker: str = "USD") -> None:
    """Create a bank/cash account on the Accounts tab."""
    navigate_to(page, "accounts")
    page.wait_for_selector("#account-name-input", state="visible")
    page.fill("#account-name-input", name)
    page.select_option("#account-type-select", value=account_type)
    page.wait_for_selector(f"#account-currency-select option:has-text('{currency_ticker}')", state="attached")
    page.select_option("#account-currency-select", label=currency_ticker)
    page.click("#add-account-btn")
    page.wait_for_timeout(1_000)


def create_period(page: Page, name: str, start: str = "2026-01-01", end: str = "2026-01-31") -> None:
    """Create a calculation period on the Period Setup tab."""
    navigate_to(page, "periods")
    page.wait_for_selector("#period-name-input", state="visible")
    page.fill("#period-name-input", name)
    page.fill("#period-start-date", start)
    page.fill("#period-end-date", end)
    page.click("#create-period-btn")
    page.wait_for_timeout(1_500)


def add_income(page: Page, source: str, amount: str, currency_ticker: str = "USD") -> None:
    """Add an income entry to the currently selected period."""
    navigate_to(page, "income")
    page.wait_for_selector("#income-source-name", state="visible")
    page.fill("#income-source-name", source)
    page.fill("#income-amount", amount)
    page.wait_for_selector(f"#income-currency option:has-text('{currency_ticker}')", state="attached")
    page.select_option("#income-currency", label=f"{currency_ticker}")
    page.click("#add-income-btn")
    page.wait_for_timeout(1_000)


def add_expense(page: Page, item_name: str, amount: str, currency_ticker: str = "USD") -> None:
    """Add an expense entry to the currently selected period."""
    navigate_to(page, "expenses")
    page.wait_for_selector("#expense-item-name", state="visible")
    # Select first available category
    page.wait_for_selector("#expense-category option", state="attached")
    page.select_option("#expense-category", index=1)
    page.fill("#expense-item-name", item_name)
    page.fill("#expense-amount", amount)
    page.wait_for_selector(f"#expense-currency option:has-text('{currency_ticker}')", state="attached")
    page.select_option("#expense-currency", label=f"{currency_ticker}")
    page.click("#add-expense-btn")
    page.wait_for_timeout(1_000)


# ─────────────────────────────────────────────────────────────
# Pytest Fixtures
# ─────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Extend default browser context: larger viewport, no strict waits."""
    return {
        **browser_context_args,
        "viewport": {"width": 1400, "height": 900},
    }


@pytest.fixture
def fresh_user(page: Page) -> dict:
    """Register and log in a fresh user. Returns user info dict.

    Scope: function (each test gets an isolated user).
    """
    email = make_email()
    register_and_login(page, email)
    return {"email": email, "password": DEFAULT_PASSWORD}


@pytest.fixture
def user_with_basics(page: Page, fresh_user: dict) -> dict:
    """Fresh user + USD currency + Main Bank account + one period.

    Returns dict with keys: email, password, period_name.
    """
    period_name = f"Test Period {rand_id()}"
    create_currency(page, "USD", "US Dollar", is_default=True)
    create_account(page, "Main Bank", account_type="BANK", currency_ticker="USD")
    create_period(page, period_name)
    select_period(page, period_name)
    return {**fresh_user, "period_name": period_name, "currency": "USD"}


@pytest.fixture
def user_with_income_and_expense(page: Page, user_with_basics: dict) -> dict:
    """user_with_basics + income (5000 USD) + expense (1500 USD)."""
    add_income(page, "Salary", "5000", "USD")
    add_expense(page, "Rent", "1500", "USD")
    return user_with_basics
