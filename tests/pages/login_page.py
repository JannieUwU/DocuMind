"""
Page Object Model - Login Page
Encapsulates login page elements and actions
"""
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import logging

logger = logging.getLogger(__name__)


class LoginPage:
    """Login page object model"""

    def __init__(self, driver, config):
        self.driver = driver
        self.config = config
        self.wait = WebDriverWait(driver, config.DEFAULT_TIMEOUT)
        self.url = f"{config.BASE_URL}/#/login"

    # Locators
    USERNAME_INPUT = (By.CSS_SELECTOR, "input[type='text']")
    PASSWORD_INPUT = (By.CSS_SELECTOR, "input[type='password']")
    LOGIN_BUTTON = (By.CSS_SELECTOR, "button[type='submit']")
    REGISTER_LINK = (By.CSS_SELECTOR, ".register-link a")
    FORGOT_PASSWORD_LINK = (By.CSS_SELECTOR, ".forgot-password-link a")
    ERROR_MESSAGE = (By.CSS_SELECTOR, ".global-error")
    LOGIN_TITLE = (By.CSS_SELECTOR, "h2")

    def navigate(self):
        """Navigate to login page"""
        logger.info(f"Navigating to {self.url}")
        self.driver.get(self.url)
        return self

    def wait_for_page_load(self):
        """Wait for login page to fully load"""
        logger.info("Waiting for login page to load")

        # Wait for app element
        self.wait.until(EC.presence_of_element_located((By.ID, "app")))

        # Wait for animation
        self.driver.implicitly_wait(self.config.ANIMATION_WAIT)

        # Wait for login form to be visible
        self.wait_for_element_visible(self.USERNAME_INPUT)

        logger.info("Login page loaded successfully")
        return self

    def wait_for_element_visible(self, locator, timeout=None):
        """Wait for element to be visible"""
        wait_time = timeout or self.config.DEFAULT_TIMEOUT
        wait = WebDriverWait(self.driver, wait_time)
        return wait.until(EC.visibility_of_element_located(locator))

    def wait_for_element_present(self, locator, timeout=None):
        """Wait for element to be present in DOM"""
        wait_time = timeout or self.config.DEFAULT_TIMEOUT
        wait = WebDriverWait(self.driver, wait_time)
        return wait.until(EC.presence_of_element_located(locator))

    def is_loaded(self):
        """Check if login page is loaded"""
        try:
            self.driver.find_element(*self.USERNAME_INPUT)
            self.driver.find_element(*self.PASSWORD_INPUT)
            self.driver.find_element(*self.LOGIN_BUTTON)
            return True
        except:
            return False

    def get_title_text(self):
        """Get login page title text"""
        try:
            return self.wait_for_element_visible(self.LOGIN_TITLE).text
        except TimeoutException:
            return None

    def fill_username(self, username):
        """Fill username field"""
        logger.info(f"Filling username: {username}")
        element = self.wait_for_element_visible(self.USERNAME_INPUT)
        element.clear()
        element.send_keys(username)
        return self

    def fill_password(self, password):
        """Fill password field"""
        logger.info("Filling password")
        element = self.wait_for_element_visible(self.PASSWORD_INPUT)
        element.clear()
        element.send_keys(password)
        return self

    def fill_credentials(self, username, password):
        """Fill both username and password"""
        self.fill_username(username)
        self.fill_password(password)
        return self

    def click_login(self):
        """Click login button"""
        logger.info("Clicking login button")
        button = self.wait_for_element_visible(self.LOGIN_BUTTON)
        button.click()
        self.driver.implicitly_wait(self.config.SHORT_WAIT)
        return self

    def login(self, username, password):
        """Complete login flow"""
        logger.info(f"Logging in as {username}")
        self.fill_credentials(username, password)
        self.click_login()
        return self

    def login_with_js(self, username, password):
        """Login using JavaScript (more reliable for Vue)"""
        logger.info(f"Logging in with JS as {username}")

        # Fill form using JS
        self.driver.execute_script("""
            const username = document.querySelector('input[type="text"]');
            const password = document.querySelector('input[type="password"]');
            if (username && password) {
                username.value = arguments[0];
                password.value = arguments[1];
                username.dispatchEvent(new Event('input', { bubbles: true }));
                password.dispatchEvent(new Event('input', { bubbles: true }));
            }
        """, username, password)

        # Click button using JS
        self.driver.execute_script("""
            const btn = document.querySelector('button[type="submit"]');
            if (btn) btn.click();
        """)

        self.driver.implicitly_wait(self.config.LONG_WAIT)
        return self

    def click_register_link(self):
        """Click sign up link"""
        logger.info("Clicking register link")
        link = self.wait_for_element_visible(self.REGISTER_LINK)
        link.click()
        self.driver.implicitly_wait(self.config.SHORT_WAIT)
        return self

    def click_forgot_password_link(self):
        """Click forgot password link"""
        logger.info("Clicking forgot password link")
        link = self.wait_for_element_visible(self.FORGOT_PASSWORD_LINK)
        link.click()
        self.driver.implicitly_wait(self.config.SHORT_WAIT)
        return self

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

    def is_username_field_visible(self):
        """Check if username field is visible"""
        try:
            self.wait_for_element_visible(self.USERNAME_INPUT, timeout=3)
            return True
        except TimeoutException:
            return False

    def is_password_field_visible(self):
        """Check if password field is visible"""
        try:
            self.wait_for_element_visible(self.PASSWORD_INPUT, timeout=3)
            return True
        except TimeoutException:
            return False

    def is_login_button_visible(self):
        """Check if login button is visible"""
        try:
            self.wait_for_element_visible(self.LOGIN_BUTTON, timeout=3)
            return True
        except TimeoutException:
            return False

    def get_current_url(self):
        """Get current page URL"""
        return self.driver.current_url

    def get_current_hash(self):
        """Get current URL hash"""
        return self.driver.execute_script("return window.location.hash;")
