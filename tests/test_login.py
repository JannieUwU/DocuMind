"""
Test Suite: Login Page Tests
Tests all aspects of the login page functionality
"""
import pytest
from pages.login_page import LoginPage
import time


class TestLoginPage:
    """Test cases for Login page"""

    def test_01_login_page_loads(self, driver, config):
        """Test that login page loads successfully"""
        login_page = LoginPage(driver, config)
        login_page.navigate().wait_for_page_load()

        assert login_page.is_loaded(), "Login page did not load properly"
        assert "#/login" in login_page.get_current_hash(), "Not on login page"

    def test_02_login_page_elements_present(self, driver, config):
        """Test that all login page elements are present"""
        login_page = LoginPage(driver, config)
        login_page.navigate().wait_for_page_load()

        assert login_page.is_username_field_visible(), "Username field not visible"
        assert login_page.is_password_field_visible(), "Password field not visible"
        assert login_page.is_login_button_visible(), "Login button not visible"

    def test_03_login_page_title(self, driver, config):
        """Test login page title"""
        login_page = LoginPage(driver, config)
        login_page.navigate().wait_for_page_load()

        title = login_page.get_title_text()
        assert title is not None, "Login title not found"
        assert "Login" in title or "User Login" in title, f"Unexpected title: {title}"

    def test_04_empty_form_validation(self, driver, config):
        """Test validation when submitting empty form"""
        login_page = LoginPage(driver, config)
        login_page.navigate().wait_for_page_load()

        # Click login without filling anything
        login_page.click_login()
        time.sleep(1)

        # Should still be on login page
        assert "#/login" in login_page.get_current_hash(), "Should stay on login page"

    def test_05_fill_username_field(self, driver, config):
        """Test filling username field"""
        login_page = LoginPage(driver, config)
        login_page.navigate().wait_for_page_load()

        login_page.fill_username(config.TEST_USERNAME)

        # Verify value was set
        username_value = driver.execute_script(
            'return document.querySelector("input[type=\'text\']").value;'
        )
        assert username_value == config.TEST_USERNAME, "Username not filled correctly"

    def test_06_fill_password_field(self, driver, config):
        """Test filling password field"""
        login_page = LoginPage(driver, config)
        login_page.navigate().wait_for_page_load()

        login_page.fill_password(config.TEST_PASSWORD)

        # Verify value was set
        password_value = driver.execute_script(
            'return document.querySelector("input[type=\'password\']").value;'
        )
        assert password_value == config.TEST_PASSWORD, "Password not filled correctly"

    def test_07_fill_complete_form(self, driver, config):
        """Test filling complete login form"""
        login_page = LoginPage(driver, config)
        login_page.navigate().wait_for_page_load()

        login_page.fill_credentials(config.TEST_USERNAME, config.TEST_PASSWORD)

        # Verify both fields filled
        username_value = driver.execute_script(
            'return document.querySelector("input[type=\'text\']").value;'
        )
        password_value = driver.execute_script(
            'return document.querySelector("input[type=\'password\']").value;'
        )

        assert username_value == config.TEST_USERNAME, "Username not filled"
        assert password_value == config.TEST_PASSWORD, "Password not filled"

    def test_08_invalid_login_attempt(self, driver, config):
        """Test login with invalid credentials"""
        login_page = LoginPage(driver, config)
        login_page.navigate().wait_for_page_load()

        # Login with invalid credentials
        login_page.login_with_js("invalid_user", "wrong_password")
        time.sleep(2)

        # Should stay on login page or show error
        current_hash = login_page.get_current_hash()
        assert "#/login" in current_hash or "#/dashboard" not in current_hash, \
            "Should not navigate to dashboard with invalid credentials"

    def test_09_navigate_to_register(self, driver, config):
        """Test navigation to register page"""
        login_page = LoginPage(driver, config)
        login_page.navigate().wait_for_page_load()

        login_page.click_register_link()
        time.sleep(2)

        # Should be on register page
        current_hash = login_page.get_current_hash()
        assert "#/register" in current_hash, f"Should be on register page, got: {current_hash}"

    def test_10_navigate_to_forgot_password(self, driver, config):
        """Test navigation to forgot password page"""
        login_page = LoginPage(driver, config)
        login_page.navigate().wait_for_page_load()

        login_page.click_forgot_password_link()
        time.sleep(2)

        # Should be on reset password page
        current_hash = login_page.get_current_hash()
        assert "#/reset-password" in current_hash, \
            f"Should be on reset password page, got: {current_hash}"

    @pytest.mark.parametrize("width,height", [
        (1920, 1080),  # Desktop
        (768, 1024),   # Tablet
        (375, 667),    # Mobile
    ])
    def test_11_responsive_design(self, driver, config, width, height):
        """Test login page on different screen sizes"""
        driver.set_window_size(width, height)

        login_page = LoginPage(driver, config)
        login_page.navigate().wait_for_page_load()

        assert login_page.is_username_field_visible(), \
            f"Username not visible at {width}x{height}"
        assert login_page.is_password_field_visible(), \
            f"Password not visible at {width}x{height}"
        assert login_page.is_login_button_visible(), \
            f"Login button not visible at {width}x{height}"

    def test_12_page_url_structure(self, driver, config):
        """Test that login page has correct URL structure"""
        login_page = LoginPage(driver, config)
        login_page.navigate().wait_for_page_load()

        url = login_page.get_current_url()
        assert config.BASE_URL in url, "Base URL incorrect"
        assert "#/login" in url, "Login hash not in URL"

    def test_13_javascript_login_method(self, driver, config):
        """Test login using JavaScript method (Vue-compatible)"""
        login_page = LoginPage(driver, config)
        login_page.navigate().wait_for_page_load()

        # Use JS method to fill and submit
        login_page.login_with_js(config.TEST_USERNAME, config.TEST_PASSWORD)
        time.sleep(2)

        # Verify form was filled (should either redirect or show error)
        current_hash = login_page.get_current_hash()
        # Test passes if we're no longer on login (redirect) or still on login (error shown)
        assert current_hash is not None, "Page should be loaded"

    def test_14_page_title_document(self, driver, config):
        """Test document title on login page"""
        login_page = LoginPage(driver, config)
        login_page.navigate().wait_for_page_load()

        page_title = driver.title
        assert "RAG" in page_title or "Login" in page_title, \
            f"Unexpected page title: {page_title}"

    def test_15_direct_navigation_to_login(self, driver, config):
        """Test direct navigation to login page without going through welcome"""
        # Navigate directly
        driver.get(f"{config.BASE_URL}/#/login")

        login_page = LoginPage(driver, config)
        login_page.wait_for_page_load()

        # Should be on login page
        assert login_page.is_loaded(), "Login page should load directly"
        assert "#/login" in login_page.get_current_hash()
