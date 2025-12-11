"""
Page Object Model - Register Page
Encapsulates register page elements and actions
"""
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import logging

logger = logging.getLogger(__name__)


class RegisterPage:
    """Register page object model"""

    def __init__(self, driver, config):
        self.driver = driver
        self.config = config
        self.wait = WebDriverWait(driver, config.DEFAULT_TIMEOUT)
        self.url = f"{config.BASE_URL}/#/register"

    # Locators
    USERNAME_INPUT = (By.CSS_SELECTOR, "input[type='text']")
    EMAIL_INPUT = (By.CSS_SELECTOR, "input[type='email']")
    VERIFICATION_CODE_INPUT = (By.CSS_SELECTOR, "input[maxlength='6']")
    PASSWORD_INPUTS = (By.CSS_SELECTOR, "input[type='password']")
    SEND_CODE_BUTTON = (By.CSS_SELECTOR, "button.send-code-btn")
    REGISTER_BUTTON = (By.CSS_SELECTOR, "button[type='submit']")
    LOGIN_LINK = (By.CSS_SELECTOR, ".login-link a")
    ERROR_MESSAGE = (By.CSS_SELECTOR, ".global-error")
    REGISTER_TITLE = (By.CSS_SELECTOR, "h2")

    def navigate(self):
        """Navigate to register page"""
        logger.info(f"Navigating to {self.url}")
        self.driver.get(self.url)
        return self

    def wait_for_page_load(self):
        """Wait for register page to fully load"""
        logger.info("Waiting for register page to load")

        # Wait for app element
        self.wait.until(EC.presence_of_element_located((By.ID, "app")))

        # Wait for animation
        self.driver.implicitly_wait(self.config.ANIMATION_WAIT)

        # Wait for form to be visible
        self.wait_for_element_visible(self.USERNAME_INPUT)

        logger.info("Register page loaded successfully")
        return self

    def wait_for_element_visible(self, locator, timeout=None):
        """Wait for element to be visible"""
        wait_time = timeout or self.config.DEFAULT_TIMEOUT
        wait = WebDriverWait(self.driver, wait_time)
        return wait.until(EC.visibility_of_element_located(locator))

    def is_loaded(self):
        """Check if register page is loaded"""
        try:
            self.driver.find_element(*self.USERNAME_INPUT)
            self.driver.find_element(*self.EMAIL_INPUT)
            self.driver.find_element(*self.SEND_CODE_BUTTON)
            return True
        except:
            return False

    def get_title_text(self):
        """Get register page title text"""
        try:
            return self.wait_for_element_visible(self.REGISTER_TITLE).text
        except TimeoutException:
            return None

    def fill_username(self, username):
        """Fill username field"""
        logger.info(f"Filling username: {username}")
        element = self.wait_for_element_visible(self.USERNAME_INPUT)
        element.clear()
        element.send_keys(username)
        return self

    def fill_email(self, email):
        """Fill email field"""
        logger.info(f"Filling email: {email}")
        element = self.wait_for_element_visible(self.EMAIL_INPUT)
        element.clear()
        element.send_keys(email)
        return self

    def fill_verification_code(self, code):
        """Fill verification code field"""
        logger.info("Filling verification code")
        element = self.wait_for_element_visible(self.VERIFICATION_CODE_INPUT)
        element.clear()
        element.send_keys(code)
        return self

    def fill_password(self, password):
        """Fill password field (first password input)"""
        logger.info("Filling password")
        # Use JS to target first password input
        self.driver.execute_script("""
            const pwdInputs = document.querySelectorAll('input[type="password"]');
            if (pwdInputs[0]) {
                pwdInputs[0].value = arguments[0];
                pwdInputs[0].dispatchEvent(new Event('input', { bubbles: true }));
            }
        """, password)
        return self

    def fill_confirm_password(self, password):
        """Fill confirm password field (second password input)"""
        logger.info("Filling confirm password")
        # Use JS to target second password input
        self.driver.execute_script("""
            const pwdInputs = document.querySelectorAll('input[type="password"]');
            if (pwdInputs[1]) {
                pwdInputs[1].value = arguments[0];
                pwdInputs[1].dispatchEvent(new Event('input', { bubbles: true }));
            }
        """, password)
        return self

    def fill_complete_form(self, username, email, code, password):
        """Fill all registration fields"""
        logger.info(f"Filling complete registration form for {username}")
        self.fill_username(username)
        self.fill_email(email)
        self.fill_verification_code(code)
        self.fill_password(password)
        self.fill_confirm_password(password)
        return self

    def click_send_code(self):
        """Click send verification code button"""
        logger.info("Clicking send code button")
        button = self.wait_for_element_visible(self.SEND_CODE_BUTTON)
        button.click()
        self.driver.implicitly_wait(self.config.SHORT_WAIT)
        return self

    def click_register(self):
        """Click register button"""
        logger.info("Clicking register button")
        button = self.wait_for_element_visible(self.REGISTER_BUTTON)
        button.click()
        self.driver.implicitly_wait(self.config.SHORT_WAIT)
        return self

    def click_login_link(self):
        """Click login link"""
        logger.info("Clicking login link")
        link = self.wait_for_element_visible(self.LOGIN_LINK)
        link.click()
        self.driver.implicitly_wait(self.config.SHORT_WAIT)
        return self

    def is_send_code_button_enabled(self):
        """Check if send code button is enabled"""
        try:
            button = self.wait_for_element_visible(self.SEND_CODE_BUTTON, timeout=3)
            return button.is_enabled()
        except TimeoutException:
            return False

    def get_error_message(self):
        """Get error message text if present"""
        try:
            error = self.wait_for_element_visible(self.ERROR_MESSAGE, timeout=3)
            return error.text
        except TimeoutException:
            return None

    def has_error_message(self):
        """Check if error message is displayed"""
        return self.get_error_message() is not None

    def get_current_hash(self):
        """Get current URL hash"""
        return self.driver.execute_script("return window.location.hash;")
