"""
Welcome Page Object - The landing page before login
"""
from selenium.webdriver.common.by import By
from .base_page import BasePage
import logging
import time

logger = logging.getLogger(__name__)


class WelcomePage(BasePage):
    """Welcome page object model"""

    # Locators
    START_BUTTON = (By.CSS_SELECTOR, "button.start-btn")
    WELCOME_TEXT = (By.CSS_SELECTOR, ".text-3xl, .md\\:text-7xl")

    def __init__(self, driver, config):
        super().__init__(driver, config)
        self.url = f"{config.BASE_URL}/"

    def navigate(self):
        """Navigate to welcome page"""
        self.open(self.url)
        self.wait_for_page_load()
        logger.info("Navigated to welcome page")
        time.sleep(2)

    def is_on_welcome_page(self):
        """Check if on welcome page"""
        try:
            return self.is_element_visible(self.START_BUTTON, timeout=5)
        except:
            return False

    def click_start(self):
        """Click Start button to proceed to login"""
        logger.info("Clicking Start button")
        self.click(self.START_BUTTON)
        time.sleep(3)  # Wait for transition animation

    def start_and_go_to_login(self):
        """Complete flow from welcome to login"""
        if self.is_on_welcome_page():
            self.click_start()
            time.sleep(2)
            logger.info("Transitioned from welcome to login")
        else:
            logger.info("Not on welcome page, may already be past it")
