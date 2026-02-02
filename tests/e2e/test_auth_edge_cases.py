"""
E2E Tests for Authentication Edge Cases

Covers:
- Duplicate registration error
- Invalid login error
- Protected route redirection
- Logout flow
"""
import pytest
import re
import random
from playwright.sync_api import Page, expect

# Constants
BASE_URL = "http://localhost:8050"
RAND_ID = random.randint(1000, 9999)
EXISTING_EMAIL = f"existing_{RAND_ID}@example.com"
USER_PASS = "Password123!"

def setup_existing_user(page: Page, email: str = None):
    # Use provided email or the default one
    user_email = email or EXISTING_EMAIL
    # Helper to register a user for duplicate/login tests
    page.goto(f"{BASE_URL}/register")
    page.fill("#register-email", user_email)
    page.fill("#register-fullname", "Existing User")
    page.fill("#register-password", USER_PASS)
    page.click("#register-button")
    
    # Wait for either success redirect OR already exists message
    # If successful, redirect to /login
    # If fails because exists (from previous run), we are still happy for these tests
    page.wait_for_timeout(1000)
    if page.url.endswith("/register"):
        # Check if already registered
        if "already registered" in page.inner_text("#register-message"):
            pass
        else:
            # Maybe it redirected but Playwright didn't catch it yet?
            # Let's wait for /login specifically
            try:
                expect(page).to_have_url(f"{BASE_URL}/login", timeout=5000)
            except:
                pass
    else:
        expect(page).to_have_url(f"{BASE_URL}/login", timeout=5000)

def test_duplicate_registration(page: Page):
    """Test: Registering an existing email fails."""
    # 1. Setup existing user
    setup_existing_user(page)
    
    # 2. Try to register again
    page.goto(f"{BASE_URL}/register")
    page.fill("#register-email", EXISTING_EMAIL)
    page.fill("#register-fullname", "Duplicate Attempter")
    page.fill("#register-password", USER_PASS)
    page.click("#register-button")
    
    # 3. Expect Error Message (check UI implementation for ID or text)
    # Usually an alert or message container. E.g. #register-message
    expect(page.locator("#register-message")).to_contain_text("already registered", ignore_case=True)
    # Should stay on register page
    expect(page).to_have_url(f"{BASE_URL}/register")

def test_invalid_login(page: Page):
    """Test: Login with wrong password fails."""
    # Ensure user exists (optional, or just use registered one)
    # Let's assume user from previous test is separate or we register anew if needed.
    # Playwright tests here run sequentially or isolated contexts? Default is new context per test.
    # So we MUST register again if isolated.
    setup_existing_user(page)
    
    page.goto(f"{BASE_URL}/login")
    page.fill("#login-email", EXISTING_EMAIL)
    page.fill("#login-password", "WrongPass")
    page.click("#login-button")
    
    expect(page.locator("#login-error")).to_contain_text("Login failed", ignore_case=True)
    # The app renders login layout but might stay on URL or redirect.
    # Looking at main.py, it renders create_login_layout() but doesn't necessarily change URL if n_clicks failed.
    expect(page.locator("#login-button")).to_be_visible()

def test_protected_route_redirect(page: Page):
    """Test: Accessing dashboard without login redirects."""
    # New context means no session
    page.goto(f"{BASE_URL}/dashboard")
    # App renders login layout at /dashboard if not authenticated
    expect(page.locator("#login-button")).to_be_visible()

def test_logout_flow(page: Page):
    """Test: Login -> Logout -> Redirect."""
    unique_email = f"logout_{random.randint(10000, 99999)}@example.com"
    setup_existing_user(page, email=unique_email)
    
    # Login
    page.fill("#login-email", unique_email)
    page.fill("#login-password", USER_PASS)
    page.click("#login-button")
    expect(page).to_have_url(re.compile(f"{BASE_URL}/dashboard"), timeout=10000)
    
    # Logout - Click the dropdown first
    page.click(".user-dropdown-toggle")
    page.click("#logout-button")
    
    expect(page.locator("#login-button")).to_be_visible()
    
    # Verify can't go back (session cleared)
    page.goto(f"{BASE_URL}/dashboard")
    expect(page.locator("#login-button")).to_be_visible()

if __name__ == "__main__":
    import subprocess
    subprocess.run(["pytest", __file__, "-v", "--headed"])
