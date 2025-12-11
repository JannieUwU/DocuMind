"""
Login Page Object
"""
from selenium.webdriver.common.by import By
from .base_page import BasePage
import logging
import time

logger = logging.getLogger(__name__)


class LoginPage(BasePage):
    """Login page object model"""

    # Locators - using correct selectors based on actual HTML
    USERNAME_INPUT = (By.CSS_SELECTOR, "input.form-input[type='text'], input[placeholder*='username'], input[placeholder*='Username']")
    PASSWORD_INPUT = (By.CSS_SELECTOR, "input[type='password']")
    LOGIN_BUTTON = (By.CSS_SELECTOR, "button.login-btn, button[type='submit']:not(.send-code-btn)")
    ERROR_MESSAGE = (By.CSS_SELECTOR, ".error-text, .global-error")

    def __init__(self, driver, config):
        super().__init__(driver, config)
        self.url = f"{config.BASE_URL}/login"

    def navigate(self):
        """Navigate to login page"""
        self.open(self.url)
        self.wait_for_page_load()

        # Check if we're on the welcome page and need to click Start
        from selenium.webdriver.common.by import By
        try:
            start_button = self.driver.find_element(By.CSS_SELECTOR, "button.start-btn")
            if start_button.is_displayed():
                logger.info("On welcome page, clicking Start button")
                start_button.click()
                time.sleep(3)  # Wait for transition
        except:
            logger.info("Not on welcome page or Start button not found")

        logger.info("Navigated to login page")
        time.sleep(2)  # Give time to see the page

    def enter_username(self, username):
        """Enter username"""
        logger.info(f"Entering username: {username}")
        self.type_text(self.USERNAME_INPUT, username)
        time.sleep(1)

    def enter_password(self, password):
        """Enter password"""
        logger.info("Entering password")
        self.type_text(self.PASSWORD_INPUT, password)
        time.sleep(1)

    def click_login(self):
        """Click login button"""
        logger.info("Clicking login button")
        # Extra wait to ensure form validation is complete
        time.sleep(1)
        self.click(self.LOGIN_BUTTON)
        time.sleep(2)

    def login(self, username, password):
        """Complete login flow"""
        logger.info(f"Logging in with username: {username}")
        self.enter_username(username)
        self.enter_password(password)
        self.click_login()

        # Wait for redirect to dashboard
        try:
            self.wait.until(lambda driver: "/dashboard" in driver.current_url or "/login" in driver.current_url)
            logger.info(f"Login completed. Current URL: {self.get_current_url()}")
        except:
            logger.warning("No redirect detected")

    def is_login_successful(self):
        """Check if login was successful"""
        current_url = self.get_current_url()
        return "/dashboard" in current_url

    def get_error_message(self):
        """Get error message text"""
        if self.is_element_visible(self.ERROR_MESSAGE, timeout=5):
            return self.get_text(self.ERROR_MESSAGE)
        return None
