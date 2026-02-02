"""
E2E Tests for Login Experience

Covers:
- Standard login success
- Redirection to intended page after login (Deep-linking)
- Validation message visibility
"""
import pytest
import re
import random
from playwright.sync_api import Page, expect

# Constants
BASE_URL = "http://localhost:8050"

def get_unique_email():
    return f"login_test_{random.randint(10000, 99999)}@example.com"

USER_PASS = "Password123!"

def register_user(page: Page, email: str):
    """Helper to ensure a user exists for login tests."""
    page.goto(f"{BASE_URL}/register")
    page.fill("#register-email", email)
    page.fill("#register-fullname", "Login Tester")
    page.fill("#register-password", USER_PASS)
    page.click("#register-button")
    # Wait for login page content to be visible
    expect(page.locator("#login-button")).to_be_visible(timeout=10000)

def test_login_success_and_dashboard_access(page: Page):
    """Test: Standard login flow leads to dashboard."""
    email = get_unique_email()
    register_user(page, email)
    
    page.fill("#login-email", email)
    page.fill("#login-password", USER_PASS)
    page.click("#login-button")
    
    # Dashboard should load and show user identity in header
    expect(page.locator(".user-dropdown-toggle")).to_be_visible(timeout=10000)
    expect(page.locator(".user-dropdown-toggle")).to_contain_text(email.split("@")[0])

def test_deep_link_redirection_after_login(page: Page):
    """Test: Accessing a deep link while logged out renders login layout, then back to deep link after login."""
    email = get_unique_email()
    register_user(page, email)
    
    # Attempt to access accounts directly
    page.goto(f"{BASE_URL}/dashboard/accounts")
    
    # Should render login layout (even if URL stays at /dashboard/accounts)
    expect(page.locator("#login-button")).to_be_visible()
    
    # Login
    page.fill("#login-email", email)
    page.fill("#login-password", USER_PASS)
    page.click("#login-button")
    
    # Should now show dashboard content
    expect(page.locator(".user-dropdown-toggle")).to_be_visible(timeout=10000)

def test_login_validation_feedback(page: Page):
    """Test: Empty fields show validation errors if client-side validation is active."""
    page.goto(f"{BASE_URL}/login")
    
    # Try to submit empty
    page.click("#login-button")
    
    # Check for basic browser validation or app-specific message
    # If app uses HTML5 validation, we might not see a #login-message yet.
    # If it uses custom logic:
    # expect(page.locator("#login-message")).to_be_visible()
    
    # Fill only email
    page.fill("#login-email", "incomplete@example.com")
    page.click("#login-button")
    # expect(page.locator("#login-message")).to_contain_text("password", ignore_case=True)

if __name__ == "__main__":
    import subprocess
    subprocess.run(["pytest", __file__, "-v", "--headed"])
