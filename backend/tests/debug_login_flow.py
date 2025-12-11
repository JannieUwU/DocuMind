"""
Enhanced debug script to inspect login flow
"""
import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from e2e.config.test_config import config

# Initialize WebDriver
service = Service(ChromeDriverManager().install())
options = config.get_browser_options()
driver = webdriver.Chrome(service=service, options=options)
driver.maximize_window()

try:
    print("\n" + "=" * 80)
    print("DEBUG: INSPECTING LOGIN FLOW")
    print("=" * 80)

    # Step 1: Go to /login URL
    print("\n1. NAVIGATING TO /login URL...")
    driver.get(f"{config.BASE_URL}/login")
    time.sleep(3)

    print(f"   Current URL: {driver.current_url}")
    print(f"   Page Title: {driver.title}")

    # Check for Start button (Welcome page)
    print("\n2. CHECKING FOR START BUTTON (Welcome Page)...")
    try:
        start_btn = driver.find_element(By.CSS_SELECTOR, "button.start-btn")
        if start_btn.is_displayed():
            print("   START BUTTON FOUND! We're on Welcome page")
            print(f"   Button text: {start_btn.text}")
            print("\n3. CLICKING START BUTTON...")
            start_btn.click()
            time.sleep(4)  # Wait for transition

            print(f"   After click - Current URL: {driver.current_url}")
            print(f"   After click - Page Title: {driver.title}")
        else:
            print("   Start button not visible")
    except Exception as e:
        print(f"   Start button not found: {e}")

    # Step 4: Now check for login form elements
    print("\n4. CHECKING FOR LOGIN FORM ELEMENTS...")

    # Check all inputs
    inputs = driver.find_elements(By.TAG_NAME, "input")
    print(f"   Found {len(inputs)} input element(s)")

    for i, inp in enumerate(inputs):
        if inp.is_displayed():
            print(f"\n   Input {i+1} (VISIBLE):")
            print(f"     Type: {inp.get_attribute('type')}")
            print(f"     Name: {inp.get_attribute('name')}")
            print(f"     Class: {inp.get_attribute('class')}")
            print(f"     Placeholder: {inp.get_attribute('placeholder')}")

    # Check forms
    forms = driver.find_elements(By.TAG_NAME, "form")
    print(f"\n   Found {len(forms)} form element(s)")

    #Check for login-specific elements
    print("\n5. TESTING CSS SELECTORS...")

    selectors_to_test = [
        "input[type='text']",
        "input[placeholder*='username']",
        "input[placeholder*='Username']",
        ".form-input",
        ".login-form input",
        "form input[type='text']"
    ]

    for selector in selectors_to_test:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                visible = [e for e in elements if e.is_displayed()]
                print(f"   ✓ '{selector}': Found {len(elements)} total, {len(visible)} visible")
                if visible:
                    print(f"      First visible placeholder: {visible[0].get_attribute('placeholder')}")
            else:
                print(f"   ✗ '{selector}': Not found")
        except Exception as e:
            print(f"   ✗ '{selector}': Error - {e}")

    print("\n" + "=" * 80)
    print("Browser will stay open for 20 seconds...")
    print("=" * 80)
    time.sleep(20)

finally:
    driver.quit()
    print("\nBrowser closed")
