"""Page Object Model for BudgetFlow Auth pages (Login / Register / Logout)."""
from playwright.sync_api import Page, expect


BASE_URL = "http://localhost:8050"


class AuthPage:
    """Encapsulates all authentication interactions."""

    def __init__(self, page: Page) -> None:
        self.page = page
        self.base_url = BASE_URL

    # ── Register ──────────────────────────────────────────────

    def go_to_register(self) -> None:
        self.page.goto(f"{self.base_url}/register")

    def register(self, email: str, fullname: str, password: str) -> None:
        """Fill and submit the registration form."""
        self.go_to_register()
        self.page.fill("#register-email", email)
        self.page.fill("#register-fullname", fullname)
        self.page.fill("#register-password", password)
        self.page.click("#register-button")

    def expect_register_error(self, text: str) -> None:
        expect(self.page.locator("#register-message")).to_contain_text(text, timeout=5_000)

    # ── Login ─────────────────────────────────────────────────

    def go_to_login(self) -> None:
        self.page.goto(f"{self.base_url}/login")

    def login(self, email: str, password: str) -> None:
        """Fill and submit the login form."""
        self.page.wait_for_selector("#login-email", state="visible", timeout=10_000)
        self.page.fill("#login-email", email)
        self.page.fill("#login-password", password)
        self.page.click("#login-button")

    def expect_logged_in(self, timeout: int = 15_000) -> None:
        expect(self.page.locator(".user-dropdown-toggle")).to_be_visible(timeout=timeout)

    def expect_login_error(self, text: str) -> None:
        expect(self.page.locator("#login-message")).to_contain_text(text, timeout=5_000)

    def expect_login_page(self) -> None:
        expect(self.page.locator("#login-button")).to_be_visible(timeout=10_000)

    # ── Logout ────────────────────────────────────────────────

    def logout(self) -> None:
        """Click the user dropdown and then Sign Out."""
        self.page.locator(".user-dropdown-toggle").click()
        self.page.locator("#logout-button").click()
        self.page.wait_for_timeout(1_000)

    # ── Full flow helpers ─────────────────────────────────────

    def register_and_login(self, email: str, password: str, fullname: str = "Test User") -> None:
        """Register a new account and immediately log in."""
        self.register(email, fullname, password)
        expect(self.page.locator("#login-button")).to_be_visible(timeout=10_000)
        self.login(email, password)
        self.expect_logged_in()
