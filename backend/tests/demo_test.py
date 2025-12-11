"""
Simple Demo Test - Login Page Interaction
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import logging

# Import our page objects
from e2e.config.test_config import config
from e2e.page_objects.login_page import LoginPage

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_demo_test():
    """Run a simple demo test to show Selenium in action"""

    logger.info("=" * 60)
    logger.info("Starting Selenium Demo Test")
    logger.info("=" * 60)

    # Initialize WebDriver
    logger.info("Initializing Chrome WebDriver...")
    service = Service(ChromeDriverManager().install())
    options = config.get_browser_options()
    driver = webdriver.Chrome(service=service, options=options)

    # Set timeouts
    driver.implicitly_wait(config.IMPLICIT_WAIT)
    driver.set_page_load_timeout(config.PAGE_LOAD_TIMEOUT)
    driver.maximize_window()

    logger.info("Browser opened successfully")

    try:
        # Create LoginPage instance
        login_page = LoginPage(driver, config)

        # Test 1: Navigate to login page
        logger.info("\n" + "=" * 60)
        logger.info("Test 1: Navigating to login page")
        logger.info("=" * 60)
        login_page.navigate()
        logger.info(f"Current URL: {driver.current_url}")
        time.sleep(3)  # Pause to see the page

        # Test 2: Check if we're on the login page
        current_url = driver.current_url
        if "/login" in current_url or "/welcome" in current_url:
            logger.info("Successfully reached login/welcome page")
        else:
            logger.warning(f"Unexpected page: {current_url}")

        time.sleep(2)

        # Test 3: Try to interact with form elements
        logger.info("\n" + "=" * 60)
        logger.info("Test 2: Attempting to fill login form")
        logger.info("=" * 60)

        try:
            # Try to find and fill username
            login_page.enter_username("demo_user")
            logger.info("Username field found and filled")
            time.sleep(2)

            # Try to find and fill password
            login_page.enter_password("demo_password")
            logger.info("Password field found and filled")
            time.sleep(2)

            logger.info("\n" + "=" * 60)
            logger.info("Demo completed! You should see:")
            logger.info("  1. Browser window opened")
            logger.info("  2. Navigated to login page")
            logger.info("  3. Username filled in")
            logger.info("  4. Password filled in")
            logger.info("=" * 60)

            # Keep browser open for a few more seconds
            logger.info("\nBrowser will stay open for 10 more seconds...")
            time.sleep(10)

        except Exception as e:
            logger.error(f"Error during form interaction: {e}")
            logger.info("This might be normal if the page structure is different")
            time.sleep(5)

    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        logger.info("\n" + "=" * 60)
        logger.info("Closing browser...")
        logger.info("=" * 60)
        time.sleep(2)
        driver.quit()
        logger.info("Browser closed")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("  SELENIUM DEMO TEST")
    print("  This will open a Chrome browser and interact with your Vue3 RAG application")
    print("=" * 80 + "\n")

    print("IMPORTANT: Make sure your application is running:")
    print("  Frontend: http://localhost:5173")
    print("  Backend:  http://localhost:8000")
    print("\nPress Ctrl+C to cancel, or wait 5 seconds to continue...")

    try:
        time.sleep(5)
        run_demo_test()
    except KeyboardInterrupt:
        print("\n\nTest cancelled by user.")
        sys.exit(0)
