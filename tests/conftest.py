"""
Base Test Configuration and Fixtures
Provides common setup and teardown for all tests
"""
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import logging
import os
from datetime import datetime


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Config:
    """Test configuration"""
    BASE_URL = "http://localhost:5173"
    BACKEND_URL = "http://localhost:8000"
    DEFAULT_TIMEOUT = 15
    ANIMATION_WAIT = 2
    SHORT_WAIT = 1
    LONG_WAIT = 5

    # Browser settings
    HEADLESS = os.getenv("HEADLESS", "false").lower() == "true"
    WINDOW_SIZE = "1920,1080"

    # Test data
    TEST_USERNAME = "selenium_test_user"
    TEST_PASSWORD = "TestPass123"
    TEST_EMAIL = "selenium@test.com"


@pytest.fixture(scope="session")
def config():
    """Provide configuration to all tests"""
    return Config()


@pytest.fixture(scope="function")
def driver(config):
    """
    Setup and teardown Chrome WebDriver for each test
    Yields driver instance and ensures cleanup
    """
    logger.info("Setting up Chrome WebDriver")

    # Chrome options
    chrome_options = Options()
    if config.HEADLESS:
        chrome_options.add_argument("--headless=new")
    chrome_options.add_argument(f"--window-size={config.WINDOW_SIZE}")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--start-maximized")

    # Disable images for faster loading (optional)
    # chrome_options.add_argument("--blink-settings=imagesEnabled=false")

    # Setup Chrome driver
    try:
        driver_path = ChromeDriverManager().install()
        # Fix webdriver-manager returning wrong file
        if 'THIRD_PARTY_NOTICES' in driver_path or 'LICENSE' in driver_path:
            import os
            driver_dir = os.path.dirname(driver_path)
            driver_path = os.path.join(driver_dir, 'chromedriver.exe')
        service = Service(driver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
    except Exception as e:
        logger.error(f"Failed to initialize Chrome driver: {e}")
        # Fallback: try without webdriver-manager
        driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(30)

    logger.info(f"Chrome WebDriver started - Headless: {config.HEADLESS}")

    yield driver

    # Cleanup
    logger.info("Tearing down Chrome WebDriver")
    driver.quit()


@pytest.fixture(scope="function")
def wait(driver, config):
    """Provide WebDriverWait instance"""
    return WebDriverWait(driver, config.DEFAULT_TIMEOUT)


@pytest.fixture(scope="function")
def authenticated_driver(driver, config):
    """
    Provide an authenticated driver session
    Logs in before test and maintains session
    """
    logger.info("Creating authenticated session")

    # Navigate to login
    driver.get(f"{config.BASE_URL}/#/login")

    # Wait for page load
    wait = WebDriverWait(driver, config.DEFAULT_TIMEOUT)
    wait.until(EC.presence_of_element_located((By.ID, "app")))

    # Wait for Vue to render
    driver.implicitly_wait(config.ANIMATION_WAIT)

    # Fill login form using JavaScript (more reliable)
    driver.execute_script("""
        const username = document.querySelector('input[type="text"]');
        const password = document.querySelector('input[type="password"]');
        if (username && password) {
            username.value = arguments[0];
            password.value = arguments[1];
            username.dispatchEvent(new Event('input', { bubbles: true }));
            password.dispatchEvent(new Event('input', { bubbles: true }));
        }
    """, config.TEST_USERNAME, config.TEST_PASSWORD)

    # Click login button
    driver.execute_script("""
        const btn = document.querySelector('button[type="submit"]');
        if (btn) btn.click();
    """)

    # Wait for navigation (or error)
    driver.implicitly_wait(config.LONG_WAIT)

    logger.info("Authentication attempt completed")

    return driver


@pytest.fixture(autouse=True)
def clear_storage(driver, config):
    """Clear localStorage and sessionStorage before each test"""
    driver.get(config.BASE_URL)
    driver.execute_script("localStorage.clear(); sessionStorage.clear();")


@pytest.fixture(scope="function")
def screenshot_on_failure(request, driver):
    """Take screenshot on test failure"""
    yield

    if request.node.rep_call.failed:
        # Create screenshots directory
        screenshot_dir = "tests/screenshots"
        os.makedirs(screenshot_dir, exist_ok=True)

        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        test_name = request.node.name
        filename = f"{screenshot_dir}/{test_name}_{timestamp}.png"

        # Take screenshot
        driver.save_screenshot(filename)
        logger.error(f"Test failed - Screenshot saved: {filename}")


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Hook to make test result available to fixtures
    Allows screenshot_on_failure to detect failures
    """
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)
