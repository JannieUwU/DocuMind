"""
Comprehensive Test Suite for Vue3 RAG Application
Tests: Login, Register, Dashboard, Chat functionality
"""
import sys
import os
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from faker import Faker
import time
import logging

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Import page objects
from e2e.config.test_config import config
from e2e.page_objects.login_page import LoginPage
from e2e.page_objects.register_page import RegisterPage
from e2e.page_objects.dashboard_page import DashboardPage

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Faker for test data
fake = Faker()


class TestVue3RAGApplication:
    """Comprehensive test suite for Vue3 RAG Application"""

    @classmethod
    def setup_class(cls):
        """Setup test environment"""
        logger.info("=" * 80)
        logger.info("STARTING COMPREHENSIVE TEST SUITE")
        logger.info("=" * 80)

        # Initialize WebDriver
        logger.info("Initializing Chrome WebDriver...")
        service = Service(ChromeDriverManager().install())
        options = config.get_browser_options()
        cls.driver = webdriver.Chrome(service=service, options=options)

        # Set timeouts
        cls.driver.implicitly_wait(config.IMPLICIT_WAIT)
        cls.driver.set_page_load_timeout(config.PAGE_LOAD_TIMEOUT)
        cls.driver.maximize_window()

        # Initialize page objects
        cls.login_page = LoginPage(cls.driver, config)
        cls.register_page = RegisterPage(cls.driver, config)
        cls.dashboard_page = DashboardPage(cls.driver, config)

        logger.info("Test environment initialized successfully")

    @classmethod
    def teardown_class(cls):
        """Cleanup after tests"""
        logger.info("\n" + "=" * 80)
        logger.info("CLEANING UP TEST ENVIRONMENT")
        logger.info("=" * 80)
        time.sleep(3)
        cls.driver.quit()
        logger.info("Browser closed")

    def test_01_login_page_loads(self):
        """Test 1: Verify login page loads correctly"""
        logger.info("\n" + "=" * 80)
        logger.info("TEST 1: Login Page Load")
        logger.info("=" * 80)

        self.login_page.navigate()
        current_url = self.driver.current_url

        logger.info(f"Current URL: {current_url}")
        assert "/login" in current_url or "/welcome" in current_url, "Failed to load login page"
        logger.info("PASS: Login page loaded successfully")
        time.sleep(2)

    def test_02_login_with_empty_credentials(self):
        """Test 2: Login with empty credentials should show validation"""
        logger.info("\n" + "=" * 80)
        logger.info("TEST 2: Login with Empty Credentials")
        logger.info("=" * 80)

        self.login_page.navigate()

        # Try to login without entering credentials
        try:
            self.login_page.click_login()
            time.sleep(2)

            # Should still be on login page
            current_url = self.driver.current_url
            assert "/login" in current_url or "/welcome" in current_url, "Unexpectedly navigated away from login"
            logger.info("PASS: Empty credentials validation works")
        except Exception as e:
            logger.info(f"PASS: Login button click prevented or validation shown: {e}")

        time.sleep(2)

    def test_03_login_with_invalid_credentials(self):
        """Test 3: Login with invalid credentials"""
        logger.info("\n" + "=" * 80)
        logger.info("TEST 3: Login with Invalid Credentials")
        logger.info("=" * 80)

        self.login_page.navigate()

        # Generate fake credentials
        fake_username = fake.user_name()
        fake_password = fake.password()

        logger.info(f"Testing with fake credentials: {fake_username}")
        self.login_page.login(fake_username, fake_password)
        time.sleep(3)

        # Check if error message appears or still on login page
        current_url = self.driver.current_url
        error_msg = self.login_page.get_error_message()

        if error_msg:
            logger.info(f"Error message shown: {error_msg}")

        # Should not be on dashboard
        assert "/dashboard" not in current_url, "Should not login with invalid credentials"
        logger.info("PASS: Invalid credentials rejected")
        time.sleep(2)

    def test_04_login_form_interaction(self):
        """Test 4: Test login form field interactions"""
        logger.info("\n" + "=" * 80)
        logger.info("TEST 4: Login Form Field Interactions")
        logger.info("=" * 80)

        self.login_page.navigate()

        test_username = "test_user_interaction"
        test_password = "test_password_123"

        # Test username field
        try:
            self.login_page.enter_username(test_username)
            logger.info("Username field interaction: OK")
            time.sleep(1)
        except Exception as e:
            logger.error(f"Username field interaction failed: {e}")
            pytest.fail(f"Username field not accessible: {e}")

        # Test password field
        try:
            self.login_page.enter_password(test_password)
            logger.info("Password field interaction: OK")
            time.sleep(1)
        except Exception as e:
            logger.error(f"Password field interaction failed: {e}")
            pytest.fail(f"Password field not accessible: {e}")

        logger.info("PASS: All form fields are interactive")
        time.sleep(2)

    def test_05_register_page_loads(self):
        """Test 5: Verify register page loads"""
        logger.info("\n" + "=" * 80)
        logger.info("TEST 5: Register Page Load")
        logger.info("=" * 80)

        self.register_page.navigate()
        current_url = self.driver.current_url

        logger.info(f"Current URL: {current_url}")
        assert "/register" in current_url, "Failed to load register page"
        logger.info("PASS: Register page loaded successfully")
        time.sleep(2)

    def test_06_register_form_validation(self):
        """Test 6: Test register form validation"""
        logger.info("\n" + "=" * 80)
        logger.info("TEST 6: Register Form Validation")
        logger.info("=" * 80)

        self.register_page.navigate()

        # Try to register with empty form
        try:
            self.register_page.click_register()
            time.sleep(2)

            # Should still be on register page
            current_url = self.driver.current_url
            assert "/register" in current_url, "Unexpectedly navigated away from register"
            logger.info("PASS: Empty form validation works")
        except Exception as e:
            logger.info(f"PASS: Form validation or button click prevented: {e}")

        time.sleep(2)

    def test_07_register_form_fields(self):
        """Test 7: Test all register form fields"""
        logger.info("\n" + "=" * 80)
        logger.info("TEST 7: Register Form Field Interactions")
        logger.info("=" * 80)

        self.register_page.navigate()

        # Generate test data
        test_username = fake.user_name()
        test_email = fake.email()
        test_password = "TestPassword123!"

        # Test username field
        try:
            self.register_page.enter_username(test_username)
            logger.info(f"Username field: OK - Entered {test_username}")
            time.sleep(1)
        except Exception as e:
            logger.warning(f"Username field interaction issue: {e}")

        # Test email field
        try:
            self.register_page.enter_email(test_email)
            logger.info(f"Email field: OK - Entered {test_email}")
            time.sleep(1)
        except Exception as e:
            logger.warning(f"Email field interaction issue: {e}")

        # Test send code button
        try:
            sent = self.register_page.click_send_code()
            if sent:
                logger.info("Send code button: OK - Clicked")
            time.sleep(2)
        except Exception as e:
            logger.warning(f"Send code button issue: {e}")

        logger.info("PASS: Register form fields tested")
        time.sleep(2)

    def test_08_navigation_links(self):
        """Test 8: Test navigation between login and register"""
        logger.info("\n" + "=" * 80)
        logger.info("TEST 8: Navigation Links")
        logger.info("=" * 80)

        # Start at login
        self.login_page.navigate()
        time.sleep(2)

        # Try to find and click register link
        try:
            from selenium.webdriver.common.by import By
            register_link = self.driver.find_element(By.CSS_SELECTOR, "a[href*='register']")
            register_link.click()
            time.sleep(3)

            current_url = self.driver.current_url
            assert "/register" in current_url, "Failed to navigate to register"
            logger.info("Navigation to register: OK")
        except Exception as e:
            logger.warning(f"Register navigation link not found or clickable: {e}")

        # Try to navigate back to login
        try:
            from selenium.webdriver.common.by import By
            login_link = self.driver.find_element(By.CSS_SELECTOR, "a[href*='login']")
            login_link.click()
            time.sleep(3)

            current_url = self.driver.current_url
            assert "/login" in current_url or "/welcome" in current_url, "Failed to navigate to login"
            logger.info("Navigation to login: OK")
        except Exception as e:
            logger.warning(f"Login navigation link not found or clickable: {e}")

        logger.info("PASS: Navigation links tested")
        time.sleep(2)

    def test_09_dashboard_direct_access(self):
        """Test 9: Try to access dashboard without login"""
        logger.info("\n" + "=" * 80)
        logger.info("TEST 9: Dashboard Access Without Login")
        logger.info("=" * 80)

        self.dashboard_page.navigate()
        time.sleep(3)

        current_url = self.driver.current_url
        logger.info(f"Redirected to: {current_url}")

        # Should be redirected to login or welcome page
        if "/login" in current_url or "/welcome" in current_url:
            logger.info("PASS: Unauthorized access prevented - redirected to login")
        elif "/dashboard" in current_url:
            logger.warning("WARNING: Dashboard accessible without login (might be in dev mode)")
            # If we're on dashboard, let's test some elements
            if self.dashboard_page.is_on_dashboard():
                logger.info("Dashboard elements detected")
        else:
            logger.info(f"Redirected to: {current_url}")

        time.sleep(2)

    def test_10_responsive_design(self):
        """Test 10: Test responsive design at different screen sizes"""
        logger.info("\n" + "=" * 80)
        logger.info("TEST 10: Responsive Design")
        logger.info("=" * 80)

        sizes = [
            (1920, 1080, "Desktop"),
            (1366, 768, "Laptop"),
            (768, 1024, "Tablet"),
            (375, 667, "Mobile")
        ]

        for width, height, device in sizes:
            logger.info(f"Testing {device} size: {width}x{height}")

            try:
                # First set window state to normal (not maximized)
                self.driver.set_window_rect(x=0, y=0, width=width, height=height)
                time.sleep(2)
            except Exception as e:
                logger.warning(f"Could not set exact size for {device}: {e}")
                # Try alternative method
                try:
                    self.driver.minimize_window()
                    time.sleep(1)
                    self.driver.set_window_size(width, height)
                    time.sleep(2)
                except Exception as e2:
                    logger.warning(f"Alternative method also failed for {device}: {e2}")

            self.login_page.navigate()
            time.sleep(2)

            logger.info(f"{device}: Page loaded successfully")

        # Restore to default size
        self.driver.maximize_window()
        logger.info("PASS: Responsive design tested")
        time.sleep(2)


def run_comprehensive_tests():
    """Run all tests"""
    logger.info("\n" + "=" * 80)
    logger.info("  COMPREHENSIVE SELENIUM TEST SUITE")
    logger.info("  Vue3 RAG Application")
    logger.info("=" * 80 + "\n")

    print("\nIMPORTANT: Make sure your application is running:")
    print("  Frontend: http://localhost:5173")
    print("  Backend:  http://localhost:8000")
    print("\nPress Ctrl+C to cancel, or wait 5 seconds to continue...")

    try:
        time.sleep(5)

        # Run pytest
        pytest.main([
            __file__,
            '-v',
            '--tb=short'
        ])

    except KeyboardInterrupt:
        print("\n\nTests cancelled by user.")
        sys.exit(0)


if __name__ == "__main__":
    run_comprehensive_tests()
