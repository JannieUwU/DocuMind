"""
Test Suite: Register Page Tests
Tests all aspects of the register page functionality
"""
import pytest
from pages.register_page import RegisterPage
import time


class TestRegisterPage:
    """Test cases for Register page"""

    def test_01_register_page_loads(self, driver, config):
        """Test that register page loads successfully"""
        register_page = RegisterPage(driver, config)
        register_page.navigate().wait_for_page_load()

        assert register_page.is_loaded(), "Register page did not load properly"
        assert "#/register" in register_page.get_current_hash(), "Not on register page"

    def test_02_register_page_elements_present(self, driver, config):
        """Test that all register page elements are present"""
        register_page = RegisterPage(driver, config)
        register_page.navigate().wait_for_page_load()

        # Check all major elements exist
        username_present = driver.execute_script(
            'return document.querySelector("input[type=\'text\']") !== null;'
        )
        email_present = driver.execute_script(
            'return document.querySelector("input[type=\'email\']") !== null;'
        )
        code_present = driver.execute_script(
            'return document.querySelector("input[maxlength=\'6\']") !== null;'
        )
        password_count = driver.execute_script(
            'return document.querySelectorAll("input[type=\'password\']").length;'
        )

        assert username_present, "Username input not found"
        assert email_present, "Email input not found"
        assert code_present, "Verification code input not found"
        assert password_count == 2, f"Expected 2 password fields, found {password_count}"

    def test_03_register_page_title(self, driver, config):
        """Test register page title"""
        register_page = RegisterPage(driver, config)
        register_page.navigate().wait_for_page_load()

        title = register_page.get_title_text()
        assert title is not None, "Register title not found"
        assert "Account" in title or "Register" in title, f"Unexpected title: {title}"

    def test_04_fill_username_field(self, driver, config):
        """Test filling username field"""
        register_page = RegisterPage(driver, config)
        register_page.navigate().wait_for_page_load()

        test_username = "test_register_user"
        register_page.fill_username(test_username)

        # Verify value
        username_value = driver.execute_script(
            'return document.querySelector("input[type=\'text\']").value;'
        )
        assert username_value == test_username, "Username not filled correctly"

    def test_05_fill_email_field(self, driver, config):
        """Test filling email field"""
        register_page = RegisterPage(driver, config)
        register_page.navigate().wait_for_page_load()

        test_email = "test@example.com"
        register_page.fill_email(test_email)

        # Verify value
        email_value = driver.execute_script(
            'return document.querySelector("input[type=\'email\']").value;'
        )
        assert email_value == test_email, "Email not filled correctly"

    def test_06_send_code_button_enabled(self, driver, config):
        """Test that send code button is initially enabled"""
        register_page = RegisterPage(driver, config)
        register_page.navigate().wait_for_page_load()

        # Initially button should be enabled
        assert register_page.is_send_code_button_enabled(), \
            "Send code button should be enabled initially"

    def test_07_fill_verification_code(self, driver, config):
        """Test filling verification code field"""
        register_page = RegisterPage(driver, config)
        register_page.navigate().wait_for_page_load()

        test_code = "123456"
        register_page.fill_verification_code(test_code)

        # Verify value
        code_value = driver.execute_script(
            'return document.querySelector("input[maxlength=\'6\']").value;'
        )
        assert code_value == test_code, "Verification code not filled correctly"

    def test_08_fill_password_fields(self, driver, config):
        """Test filling both password fields"""
        register_page = RegisterPage(driver, config)
        register_page.navigate().wait_for_page_load()

        test_password = "TestPass123"
        register_page.fill_password(test_password)
        register_page.fill_confirm_password(test_password)

        # Verify both passwords set
        passwords = driver.execute_script("""
            return Array.from(document.querySelectorAll('input[type="password"]'))
                .map(input => input.value);
        """)

        assert len(passwords) == 2, "Should have 2 password fields"
        assert passwords[0] == test_password, "First password not filled"
        assert passwords[1] == test_password, "Second password not filled"

    def test_09_fill_complete_registration_form(self, driver, config):
        """Test filling complete registration form"""
        register_page = RegisterPage(driver, config)
        register_page.navigate().wait_for_page_load()

        # Fill all fields
        register_page.fill_complete_form(
            username="selenium_test_user",
            email="selenium@test.com",
            code="123456",
            password="TestPass123"
        )

        # Verify all fields filled
        values = driver.execute_script("""
            return {
                username: document.querySelector('input[type="text"]').value,
                email: document.querySelector('input[type="email"]').value,
                code: document.querySelector('input[maxlength="6"]').value,
                passwords: Array.from(document.querySelectorAll('input[type="password"]')).map(i => i.value)
            };
        """)

        assert values['username'] == "selenium_test_user", "Username not filled"
        assert values['email'] == "selenium@test.com", "Email not filled"
        assert values['code'] == "123456", "Code not filled"
        assert len(values['passwords']) == 2, "Should have 2 passwords"
        assert all(p == "TestPass123" for p in values['passwords']), "Passwords not filled"

    def test_10_navigate_to_login(self, driver, config):
        """Test navigation to login page from register"""
        register_page = RegisterPage(driver, config)
        register_page.navigate().wait_for_page_load()

        register_page.click_login_link()
        time.sleep(2)

        # Should be on login page
        current_hash = register_page.get_current_hash()
        assert "#/login" in current_hash, f"Should be on login page, got: {current_hash}"

    @pytest.mark.parametrize("width,height", [
        (1920, 1080),  # Desktop
        (768, 1024),   # Tablet
        (375, 667),    # Mobile
    ])
    def test_11_responsive_design(self, driver, config, width, height):
        """Test register page on different screen sizes"""
        driver.set_window_size(width, height)

        register_page = RegisterPage(driver, config)
        register_page.navigate().wait_for_page_load()

        # Check elements exist at this size
        elements_present = driver.execute_script("""
            return {
                username: document.querySelector('input[type="text"]') !== null,
                email: document.querySelector('input[type="email"]') !== null,
                sendCode: document.querySelector('button.send-code-btn') !== null,
                register: document.querySelector('button[type="submit"]') !== null
            };
        """)

        assert elements_present['username'], f"Username missing at {width}x{height}"
        assert elements_present['email'], f"Email missing at {width}x{height}"
        assert elements_present['sendCode'], f"Send code missing at {width}x{height}"
        assert elements_present['register'], f"Register button missing at {width}x{height}"

    def test_12_empty_form_validation(self, driver, config):
        """Test validation when submitting empty form"""
        register_page = RegisterPage(driver, config)
        register_page.navigate().wait_for_page_load()

        # Try to register without filling anything
        register_page.click_register()
        time.sleep(1)

        # Should still be on register page
        assert "#/register" in register_page.get_current_hash(), \
            "Should stay on register page with empty form"

    def test_13_password_hint_text(self, driver, config):
        """Test that password hint text is present"""
        register_page = RegisterPage(driver, config)
        register_page.navigate().wait_for_page_load()

        # Check for password hint
        has_hint = driver.execute_script("""
            return document.querySelector('.password-hint') !== null;
        """)

        assert has_hint, "Password hint should be present"

    def test_14_input_maxlength_verification_code(self, driver, config):
        """Test that verification code input has maxlength of 6"""
        register_page = RegisterPage(driver, config)
        register_page.navigate().wait_for_page_load()

        maxlength = driver.execute_script("""
            return document.querySelector('input[maxlength="6"]').getAttribute('maxlength');
        """)

        assert maxlength == "6", "Verification code should have maxlength of 6"

    def test_15_page_title_document(self, driver, config):
        """Test document title on register page"""
        register_page = RegisterPage(driver, config)
        register_page.navigate().wait_for_page_load()

        page_title = driver.title
        assert "RAG" in page_title or "Register" in page_title, \
            f"Unexpected page title: {page_title}"
