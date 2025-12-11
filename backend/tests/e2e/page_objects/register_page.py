"""
Register Page Object
"""
from selenium.webdriver.common.by import By
from .base_page import BasePage
import logging
import time

logger = logging.getLogger(__name__)


class RegisterPage(BasePage):
    """Register page object model"""

    # Locators
    USERNAME_INPUT = (By.CSS_SELECTOR, "input[placeholder*='username']")
    EMAIL_INPUT = (By.CSS_SELECTOR, "input[type='email']")
    CODE_INPUT = (By.CSS_SELECTOR, "input[placeholder*='code'], input[placeholder*='Code']")
    PASSWORD_INPUT = (By.CSS_SELECTOR, "input[type='password']")
    CONFIRM_PASSWORD_INPUT = (By.CSS_SELECTOR, "input[placeholder*='Confirm'], input[placeholder*='confirm']")
    SEND_CODE_BUTTON = (By.CSS_SELECTOR, "button.send-code-btn, button:contains('Send Code')")
    REGISTER_BUTTON = (By.CSS_SELECTOR, "button[type='submit']")
    LOGIN_LINK = (By.CSS_SELECTOR, "a[href='/login']")
    ERROR_MESSAGE = (By.CSS_SELECTOR, ".error-text, .global-error")

    def __init__(self, driver, config):
        super().__init__(driver, config)
        self.url = f"{config.BASE_URL}/register"

    def navigate(self):
        """Navigate to register page"""
        self.open(self.url)
        self.wait_for_page_load()
        logger.info("Navigated to register page")
        time.sleep(2)

    def enter_username(self, username):
        """Enter username"""
        logger.info(f"Entering username: {username}")
        self.type_text(self.USERNAME_INPUT, username)
        time.sleep(1)

    def enter_email(self, email):
        """Enter email"""
        logger.info(f"Entering email: {email}")
        self.type_text(self.EMAIL_INPUT, email)
        time.sleep(1)

    def click_send_code(self):
        """Click send verification code button"""
        logger.info("Clicking send code button")
        try:
            self.click(self.SEND_CODE_BUTTON)
            time.sleep(2)
            return True
        except Exception as e:
            logger.warning(f"Could not click send code button: {e}")
            return False

    def enter_verification_code(self, code):
        """Enter verification code"""
        logger.info("Entering verification code")
        self.type_text(self.CODE_INPUT, code)
        time.sleep(1)

    def enter_password(self, password):
        """Enter password"""
        logger.info("Entering password")
        self.type_text(self.PASSWORD_INPUT, password)
        time.sleep(1)

    def enter_confirm_password(self, password):
        """Enter confirm password"""
        logger.info("Entering confirm password")
        self.type_text(self.CONFIRM_PASSWORD_INPUT, password)
        time.sleep(1)

    def click_register(self):
        """Click register button"""
        logger.info("Clicking register button")
        self.click(self.REGISTER_BUTTON)
        time.sleep(2)

    def get_error_message(self):
        """Get error message text"""
        if self.is_element_visible(self.ERROR_MESSAGE, timeout=5):
            return self.get_text(self.ERROR_MESSAGE)
        return None
