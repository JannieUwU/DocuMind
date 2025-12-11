"""
Base Page Object - All page objects inherit from this
"""
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import logging

logger = logging.getLogger(__name__)


class BasePage:
    """Base class for all page objects"""

    def __init__(self, driver, config):
        self.driver = driver
        self.config = config
        self.wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    def open(self, url):
        """Navigate to URL"""
        logger.info(f"Navigating to: {url}")
        self.driver.get(url)

    def find_element(self, locator):
        """Find element with explicit wait"""
        try:
            element = self.wait.until(EC.presence_of_element_located(locator))
            logger.debug(f"Found element: {locator}")
            return element
        except TimeoutException:
            logger.error(f"Element not found: {locator}")
            raise

    def click(self, locator, use_js_fallback=True):
        """Click element with wait and optional JavaScript fallback"""
        try:
            element = self.wait.until(EC.element_to_be_clickable(locator))
            logger.info(f"Clicking element: {locator}")
            element.click()
        except TimeoutException:
            if use_js_fallback:
                logger.warning(f"Standard click failed for {locator}, trying JavaScript click")
                element = self.find_element(locator)
                self.driver.execute_script("arguments[0].click();", element)
                logger.info(f"JavaScript click succeeded for {locator}")
            else:
                raise

    def type_text(self, locator, text):
        """Type text into input field"""
        element = self.find_element(locator)
        element.clear()
        logger.info(f"Typing text into {locator}: {text}")
        element.send_keys(text)

    def get_text(self, locator):
        """Get element text"""
        element = self.find_element(locator)
        text = element.text
        logger.debug(f"Got text from {locator}: {text}")
        return text

    def is_element_visible(self, locator, timeout=None):
        """Check if element is visible"""
        try:
            wait_time = timeout or self.config.EXPLICIT_WAIT
            wait = WebDriverWait(self.driver, wait_time)
            wait.until(EC.visibility_of_element_located(locator))
            return True
        except TimeoutException:
            return False

    def get_current_url(self):
        """Get current page URL"""
        return self.driver.current_url

    def wait_for_page_load(self):
        """Wait for page to load completely"""
        self.wait.until(
            lambda driver: driver.execute_script("return document.readyState") == "complete"
        )
        logger.info("Page loaded completely")
