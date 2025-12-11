"""
Test Environment Configuration
"""
import os
from dataclasses import dataclass


@dataclass
class TestConfig:
    """Test configuration settings"""

    # Application URLs
    BASE_URL: str = 'http://localhost:5173'
    API_BASE_URL: str = 'http://localhost:8000'

    # Test User Credentials
    TEST_USERNAME: str = 'test_user'
    TEST_PASSWORD: str = 'Test@123456'
    TEST_EMAIL: str = 'test@example.com'

    # Browser Settings
    BROWSER: str = 'chrome'  # chrome, firefox, edge
    HEADLESS: bool = False  # Set to False to see the browser
    WINDOW_SIZE: tuple = (1920, 1080)

    # Timeouts (seconds)
    IMPLICIT_WAIT: int = 10
    EXPLICIT_WAIT: int = 20
    PAGE_LOAD_TIMEOUT: int = 30

    # Screenshot Settings
    SCREENSHOT_ON_FAILURE: bool = True
    SCREENSHOT_DIR: str = 'tests/reports/screenshots'

    @classmethod
    def get_browser_options(cls):
        """Get browser-specific options"""
        if cls.BROWSER == 'chrome':
            from selenium.webdriver.chrome.options import Options
            options = Options()
            if cls.HEADLESS:
                options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument(f'--window-size={cls.WINDOW_SIZE[0]},{cls.WINDOW_SIZE[1]}')
            # Add options to see what's happening
            options.add_argument('--start-maximized')
            options.add_experimental_option('excludeSwitches', ['enable-logging'])
            return options
        return None


config = TestConfig()
