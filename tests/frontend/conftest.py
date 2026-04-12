"""
Frontend test configuration for BudgetFlow Dash app.

Uses dash.testing (DashComposite) which starts the Dash app in-process and
drives it via Selenium/ChromeDriver.  All API calls are intercepted via
pytest-mock so the backend is not required for layout/callback wiring tests.

Requirements (host machine):
    pip install "dash[testing]" selenium webdriver-manager pytest-mock

ChromeDriver is managed automatically by webdriver-manager.
"""
import sys
import os
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# ---------------------------------------------------------------------------
# Make frontend/app importable
# ---------------------------------------------------------------------------
FRONTEND_APP_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../frontend/app")
)
if FRONTEND_APP_DIR not in sys.path:
    sys.path.insert(0, FRONTEND_APP_DIR)


# ---------------------------------------------------------------------------
# Ensure ChromeDriver is available on PATH
# ---------------------------------------------------------------------------
def _setup_chromedriver():
    """Download ChromeDriver using webdriver-manager and ensure it's on PATH."""
    chromedriver_path = ChromeDriverManager().install()

    # Create ~/bin if it doesn't exist
    bin_dir = Path.home() / "bin"
    bin_dir.mkdir(exist_ok=True)

    # Symlink/copy chromedriver to ~/bin/chromedriver
    chromedriver_link = bin_dir / "chromedriver"
    if not chromedriver_link.exists():
        try:
            chromedriver_link.symlink_to(chromedriver_path)
        except Exception:
            # If symlink fails, copy the file
            shutil.copy(chromedriver_path, chromedriver_link)
            chromedriver_link.chmod(0o755)

    # Ensure ~/bin is on PATH
    path_dirs = os.environ.get("PATH", "").split(":")
    bin_dir_str = str(bin_dir)
    if bin_dir_str not in path_dirs:
        os.environ["PATH"] = f"{bin_dir_str}:{os.environ.get('PATH', '')}"

    return chromedriver_link


# Setup chromedriver on module load
_setup_chromedriver()


# ---------------------------------------------------------------------------
# Standard mock API responses used across all tests
# ---------------------------------------------------------------------------

MOCK_TOKEN = "test-jwt-token-abc123"

MOCK_LOGIN_RESPONSE = {"access_token": MOCK_TOKEN, "token_type": "bearer"}

MOCK_ME_RESPONSE = {
    "id": "00000000-0000-0000-0000-000000000001",
    "email": "test@example.com",
    "full_name": "Test User",
}

MOCK_CURRENCIES = [
    {"id": "uuid-c1", "ticker": "PLN", "name": "Polish Zloty", "is_default": True},
    {"id": "uuid-c2", "ticker": "USD", "name": "US Dollar", "is_default": False},
    {"id": "uuid-c3", "ticker": "EUR", "name": "Euro", "is_default": False},
]

MOCK_ACCOUNTS = [
    {
        "id": "uuid-a1",
        "account_name": "Main Bank",
        "account_type": "BANK",
        "currency_ticker": "PLN",
        "opening_balance": "5000.00",
        "created_at": "2026-01-01T00:00:00Z",
    }
]

MOCK_PERIODS = [
    {
        "id": "uuid-p1",
        "period_name": "January 2026",
        "start_date": "2026-01-01",
        "end_date": "2026-01-31",
        "is_finalized": False,
        "created_at": "2026-01-01T00:00:00Z",
    }
]

MOCK_CATEGORIES = [
    {"id": "uuid-cat1", "category_name": "Groceries", "parent_id": None, "icon": "🛒"},
    {"id": "uuid-cat2", "category_name": "Rent", "parent_id": None, "icon": "🏠"},
]

MOCK_INCOME = [
    {
        "id": "uuid-inc1",
        "source_name": "Salary",
        "amount": "5000.00",
        "currency_ticker": "PLN",
        "income_date": "2026-01-15",
        "notes": "",
        "is_recurring": True,
        "is_tax_applicable": True,
    }
]

MOCK_EXPENSES = [
    {
        "id": "uuid-exp1",
        "item_name": "Groceries Jan",
        "amount": "300.00",
        "currency_ticker": "PLN",
        "expense_date": "2026-01-10",
        "category_name": "Groceries",
        "notes": "",
        "is_recurring": False,
    }
]

MOCK_RECONCILIATION = {
    "currencies": [
        {
            "currency_ticker": "PLN",
            "starting_balance": "5000.00",
            "total_income": "5000.00",
            "total_expenses": "300.00",
            "expected_balance": "9700.00",
            "actual_balance": "9700.00",
            "difference": "0.00",
        }
    ]
}

MOCK_INVESTMENTS_ACCOUNTS = []
MOCK_INVESTMENTS_CATEGORIES = []
MOCK_INVESTMENTS_TRANSFERS = []

MOCK_INSTALLMENTS = []
MOCK_SUSPENDED = []
MOCK_CONVERSIONS = []
MOCK_TEMPLATES = []

MOCK_ANALYTICS = {
    "total_income": "5000.00",
    "total_expenses": "300.00",
    "net_savings": "4700.00",
    "savings_rate": 94.0,
    "by_category": [],
}


def _api_get_side_effect(endpoint: str):
    """Route mock GET requests to appropriate fixtures."""
    if "/auth/me" in endpoint:
        return MOCK_ME_RESPONSE
    if "/currencies" in endpoint:
        return MOCK_CURRENCIES
    if "/accounts" in endpoint:
        return MOCK_ACCOUNTS
    if "/periods" in endpoint:
        return MOCK_PERIODS
    if "/expense-categories" in endpoint:
        return MOCK_CATEGORIES
    if "/income" in endpoint:
        return MOCK_INCOME
    if "/expenses" in endpoint:
        return MOCK_EXPENSES
    if "/reconciliation" in endpoint:
        return MOCK_RECONCILIATION
    if "/investments/accounts" in endpoint:
        return MOCK_INVESTMENTS_ACCOUNTS
    if "/investments" in endpoint:
        return MOCK_INVESTMENTS_CATEGORIES
    if "/installments" in endpoint:
        return MOCK_INSTALLMENTS
    if "/suspended" in endpoint:
        return MOCK_SUSPENDED
    if "/conversions" in endpoint:
        return MOCK_CONVERSIONS
    if "/templates" in endpoint:
        return MOCK_TEMPLATES
    if "/analytics" in endpoint:
        return MOCK_ANALYTICS
    return {}


# ---------------------------------------------------------------------------
# Pytest fixtures
# ---------------------------------------------------------------------------

def _build_chrome_options() -> Options:
    options = Options()
    options.binary_location = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1400,900")
    options.add_argument("--log-level=3")
    return options


@pytest.fixture(scope="session")
def chrome_options():
    """Chrome options fixture consumed by dash.testing's dash_duo."""
    return _build_chrome_options()


@pytest.fixture(scope="session")
def driver():
    """
    Selenium WebDriver fixture.
    ChromeDriver is set up on PATH by _setup_chromedriver() at module load.
    """
    options = _build_chrome_options()
    # ChromeDriver is now on PATH, so webdriver.Chrome() will find it
    drv = webdriver.Chrome(options=options)
    drv.set_page_load_timeout(30)
    yield drv
    drv.quit()


@pytest.fixture
def mock_api(mocker):
    """
    Patch APIClient so all callbacks work without a real backend.
    Returns the mock so tests can configure per-call overrides.
    """
    mock = MagicMock()
    mock.get.side_effect = _api_get_side_effect
    mock.post.return_value = {"access_token": MOCK_TOKEN}
    mock.patch.return_value = {"success": True}
    mock.delete.return_value = {"success": True}
    mock.set_token.return_value = None

    mocker.patch("utils.api_client.APIClient", return_value=mock)
    # Also patch each callback module that creates its own APIClient instance
    for module in [
        "callbacks.auth_callbacks",
        "callbacks.account_callbacks",
        "callbacks.income_callbacks",
        "callbacks.expense_callbacks",
        "callbacks.reconciliation_callbacks",
        "callbacks.currency_callbacks",
        "callbacks.category_callbacks",
        "callbacks.investment_callbacks",
        "callbacks.suspended_callbacks",
        "callbacks.installment_callbacks",
        "callbacks.conversion_callbacks",
        "callbacks.template_callbacks",
        "callbacks.analytics_callbacks",
        "callbacks.analytics_advanced_callbacks",
        "callbacks.dashboard_callbacks",
        "callbacks.period_callbacks",
        "callbacks.common_reconciliation_callbacks",
    ]:
        try:
            mocker.patch(f"{module}.APIClient", return_value=mock)
        except Exception:
            pass

    return mock


@pytest.fixture
def dash_app(mock_api):
    """Import and return the Dash app instance with mocked API."""
    # Force fresh import so patches take effect
    import importlib
    import main as main_module
    importlib.reload(main_module)
    return main_module.app


@pytest.fixture
def authenticated_session_data():
    """Session store data representing a logged-in user."""
    return {"token": MOCK_TOKEN}
