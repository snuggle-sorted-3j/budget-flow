"""
Tests for authentication callbacks:
- Login form validation (empty fields)
- Login error display on bad credentials
- Successful login redirects to dashboard
- Register form validation
- Logout clears session
"""
import time
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def _wait_dash(driver, extra=0.3):
    WebDriverWait(driver, 10).until(
        lambda d: d.execute_script("return typeof window.dash_clientside !== 'undefined'")
    )
    time.sleep(extra)


def _element(driver, element_id, timeout=8):
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.ID, element_id))
    )


def _click(driver, element_id):
    el = _element(driver, element_id)
    driver.execute_script("arguments[0].scrollIntoView(true);", el)
    el.click()


def _type(driver, element_id, text):
    el = _element(driver, element_id)
    el.clear()
    el.send_keys(text)


def _is_visible(driver, element_id):
    try:
        el = driver.find_element(By.ID, element_id)
        return el.is_displayed()
    except Exception:
        return False


@pytest.mark.frontend
class TestLoginCallbacks:

    def test_empty_login_shows_error(self, dash_duo, dash_app, mock_api):
        """Clicking Login with empty fields shows the error alert."""
        mock_api.post.return_value = {"error": "Please enter both email and password"}

        dash_duo.start_server(dash_app)
        dash_duo.driver.get(dash_duo.server_url + "/")
        _wait_dash(dash_duo.driver)

        _click(dash_duo.driver, "login-button")
        time.sleep(0.8)

        # Error alert should be open
        error = _element(dash_duo.driver, "login-error")
        assert error.is_displayed(), "Login error alert should be visible after empty submit"

    def test_bad_credentials_shows_error(self, dash_duo, dash_app, mock_api):
        """Backend error is surfaced in the login alert."""
        mock_api.post.return_value = {"error": "Invalid credentials"}

        dash_duo.start_server(dash_app)
        dash_duo.driver.get(dash_duo.server_url + "/")
        _wait_dash(dash_duo.driver)

        _type(dash_duo.driver, "login-email", "bad@example.com")
        _type(dash_duo.driver, "login-password", "wrongpassword")
        _click(dash_duo.driver, "login-button")
        time.sleep(1.0)

        error = _element(dash_duo.driver, "login-error")
        assert error.is_displayed()
        assert "Login failed" in error.text or "Invalid" in error.text

    def test_successful_login_redirects(self, dash_duo, dash_app, mock_api):
        """Successful login redirects to /dashboard."""
        mock_api.post.return_value = {"access_token": "good-token", "token_type": "bearer"}
        mock_api.get.side_effect = lambda ep: (
            {"id": "u1", "email": "test@example.com", "full_name": "Test"}
            if "/auth/me" in ep else []
        )

        dash_duo.start_server(dash_app)
        dash_duo.driver.get(dash_duo.server_url + "/")
        _wait_dash(dash_duo.driver)

        _type(dash_duo.driver, "login-email", "test@example.com")
        _type(dash_duo.driver, "login-password", "Password123")
        _click(dash_duo.driver, "login-button")

        WebDriverWait(dash_duo.driver, 10).until(
            lambda d: "/dashboard" in d.current_url
        )
        assert "/dashboard" in dash_duo.driver.current_url

    def test_login_button_exists_and_is_clickable(self, dash_duo, dash_app):
        """Login button is present and enabled."""
        dash_duo.start_server(dash_app)
        dash_duo.driver.get(dash_duo.server_url + "/")
        _wait_dash(dash_duo.driver)

        btn = _element(dash_duo.driver, "login-button")
        assert btn.is_enabled()
        assert btn.is_displayed()


@pytest.mark.frontend
class TestRegisterCallbacks:

    def test_empty_register_shows_warning(self, dash_duo, dash_app, mock_api):
        """Clicking Register with empty fields shows the warning alert."""
        mock_api.post.return_value = {"error": "Please fill in all fields"}

        dash_duo.start_server(dash_app)
        dash_duo.driver.get(dash_duo.server_url + "/register")
        _wait_dash(dash_duo.driver)

        _click(dash_duo.driver, "register-button")
        time.sleep(0.8)

        msg = _element(dash_duo.driver, "register-message")
        assert msg.is_displayed()

    def test_successful_register_redirects_to_login(self, dash_duo, dash_app, mock_api):
        """Successful registration redirects to /login."""
        mock_api.post.return_value = {"id": "new-user-id", "email": "new@example.com"}

        dash_duo.start_server(dash_app)
        dash_duo.driver.get(dash_duo.server_url + "/register")
        _wait_dash(dash_duo.driver)

        _type(dash_duo.driver, "register-email", "new@example.com")
        _type(dash_duo.driver, "register-fullname", "New User")
        _type(dash_duo.driver, "register-password", "SecurePass123")
        _click(dash_duo.driver, "register-button")

        WebDriverWait(dash_duo.driver, 10).until(
            lambda d: "/login" in d.current_url or "register" not in d.current_url
        )

    def test_register_duplicate_email_shows_error(self, dash_duo, dash_app, mock_api):
        """Duplicate email registration shows error."""
        mock_api.post.return_value = {"error": "Email already registered"}

        dash_duo.start_server(dash_app)
        dash_duo.driver.get(dash_duo.server_url + "/register")
        _wait_dash(dash_duo.driver)

        _type(dash_duo.driver, "register-email", "existing@example.com")
        _type(dash_duo.driver, "register-fullname", "Existing User")
        _type(dash_duo.driver, "register-password", "Password123")
        _click(dash_duo.driver, "register-button")
        time.sleep(0.8)

        msg = _element(dash_duo.driver, "register-message")
        assert msg.is_displayed()
        assert "Registration failed" in msg.text or "Email" in msg.text


@pytest.mark.frontend
class TestLogout:

    def _login(self, driver, base_url, mock_api):
        """Helper: inject auth state directly."""
        driver.get(base_url + "/")
        _wait_dash(driver)
        driver.execute_script(
            "sessionStorage.setItem('session-store', JSON.stringify({token: 'tok'}));"
            "sessionStorage.setItem('user-store', JSON.stringify({email: 'test@example.com'}));"
        )
        driver.get(base_url + "/dashboard")
        _wait_dash(driver)

    def test_logout_button_present_in_dashboard(self, dash_duo, dash_app, mock_api):
        """Logout button is present in the header dropdown."""
        dash_duo.start_server(dash_app)
        self._login(dash_duo.driver, dash_duo.server_url, mock_api)

        btn = _element(dash_duo.driver, "logout-button")
        assert btn is not None

    def test_logout_redirects_to_login(self, dash_duo, dash_app, mock_api):
        """Clicking logout navigates to /login."""
        dash_duo.start_server(dash_app)
        self._login(dash_duo.driver, dash_duo.server_url, mock_api)

        # Open the dropdown first, then click logout
        _click(dash_duo.driver, "logout-button")

        WebDriverWait(dash_duo.driver, 8).until(
            lambda d: "/login" in d.current_url or d.find_elements(By.ID, "login-button")
        )
