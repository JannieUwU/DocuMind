"""
Dashboard Page Object
"""
from selenium.webdriver.common.by import By
from .base_page import BasePage
import logging
import time

logger = logging.getLogger(__name__)


class DashboardPage(BasePage):
    """Dashboard page object model"""

    # Locators
    CHAT_INPUT = (By.CSS_SELECTOR, "textarea, input[placeholder*='message'], input[placeholder*='Message']")
    SEND_BUTTON = (By.CSS_SELECTOR, "button[type='submit'], button:has(svg)")
    FILE_UPLOAD_BUTTON = (By.CSS_SELECTOR, "input[type='file'], button:has(.upload)")
    NEW_CHAT_BUTTON = (By.CSS_SELECTOR, "button:contains('New'), button[title*='New']")
    CONVERSATION_LIST = (By.CSS_SELECTOR, ".conversation-item, .chat-item")
    MESSAGE_CONTAINER = (By.CSS_SELECTOR, ".chat-message, .message")
    USER_MENU = (By.CSS_SELECTOR, ".user-menu, .avatar")
    LOGOUT_BUTTON = (By.CSS_SELECTOR, "button:contains('Logout'), a[href*='logout']")

    def __init__(self, driver, config):
        super().__init__(driver, config)
        self.url = f"{config.BASE_URL}/dashboard"

    def navigate(self):
        """Navigate to dashboard page"""
        self.open(self.url)
        self.wait_for_page_load()
        logger.info("Navigated to dashboard page")
        time.sleep(2)

    def is_on_dashboard(self):
        """Check if on dashboard page"""
        current_url = self.get_current_url()
        return "/dashboard" in current_url

    def enter_message(self, message):
        """Enter a chat message"""
        logger.info(f"Entering message: {message}")
        try:
            self.type_text(self.CHAT_INPUT, message)
            time.sleep(1)
            return True
        except Exception as e:
            logger.warning(f"Could not enter message: {e}")
            return False

    def click_send(self):
        """Click send button"""
        logger.info("Clicking send button")
        try:
            self.click(self.SEND_BUTTON)
            time.sleep(2)
            return True
        except Exception as e:
            logger.warning(f"Could not click send button: {e}")
            return False

    def send_message(self, message):
        """Complete flow to send a message"""
        if self.enter_message(message):
            return self.click_send()
        return False

    def get_messages_count(self):
        """Get count of messages in chat"""
        try:
            messages = self.driver.find_elements(*self.MESSAGE_CONTAINER)
            return len(messages)
        except:
            return 0

    def click_new_chat(self):
        """Click new chat button"""
        logger.info("Clicking new chat button")
        try:
            self.click(self.NEW_CHAT_BUTTON)
            time.sleep(2)
            return True
        except Exception as e:
            logger.warning(f"Could not click new chat button: {e}")
            return False

    def upload_file(self, file_path):
        """Upload a file"""
        logger.info(f"Uploading file: {file_path}")
        try:
            file_input = self.find_element(self.FILE_UPLOAD_BUTTON)
            file_input.send_keys(file_path)
            time.sleep(3)
            return True
        except Exception as e:
            logger.warning(f"Could not upload file: {e}")
            return False
