"""
Debug script to inspect actual DOM structure of login page
"""
import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from e2e.config.test_config import config

# Initialize WebDriver
service = Service(ChromeDriverManager().install())
options = config.get_browser_options()
driver = webdriver.Chrome(service=service, options=options)
driver.maximize_window()

try:
    # Navigate to login page
    driver.get(f"{config.BASE_URL}/login")
    time.sleep(5)  # Wait for page to fully load

    print("\n" + "=" * 80)
    print("INSPECTING LOGIN PAGE DOM STRUCTURE")
    print("=" * 80)

    # Get page source and find input elements
    from selenium.webdriver.common.by import By

    # Try to find all input elements
    print("\n1. ALL INPUT ELEMENTS:")
    try:
        inputs = driver.find_elements(By.TAG_NAME, "input")
        for i, inp in enumerate(inputs):
            print(f"\nInput {i+1}:")
            print(f"  Type: {inp.get_attribute('type')}")
            print(f"  Name: {inp.get_attribute('name')}")
            print(f"  ID: {inp.get_attribute('id')}")
            print(f"  Class: {inp.get_attribute('class')}")
            print(f"  Placeholder: {inp.get_attribute('placeholder')}")
            print(f"  Visible: {inp.is_displayed()}")
    except Exception as e:
        print(f"Error finding inputs: {e}")

    # Try to find form
    print("\n2. FORM ELEMENTS:")
    try:
        forms = driver.find_elements(By.TAG_NAME, "form")
        print(f"Found {len(forms)} form(s)")
        for i, form in enumerate(forms):
            print(f"\nForm {i+1}:")
            print(f"  Class: {form.get_attribute('class')}")
            print(f"  Action: {form.get_attribute('action')}")
    except Exception as e:
        print(f"Error finding forms: {e}")

    # Try to find buttons
    print("\n3. BUTTON ELEMENTS:")
    try:
        buttons = driver.find_elements(By.TAG_NAME, "button")
        for i, btn in enumerate(buttons):
            print(f"\nButton {i+1}:")
            print(f"  Type: {btn.get_attribute('type')}")
            print(f"  Class: {btn.get_attribute('class')}")
            print(f"  Text: {btn.text}")
            print(f"  Visible: {btn.is_displayed()}")
    except Exception as e:
        print(f"Error finding buttons: {e}")

    # Get a small sample of page HTML
    print("\n4. PAGE TITLE AND URL:")
    print(f"  Title: {driver.title}")
    print(f"  Current URL: {driver.current_url}")

    print("\n" + "=" * 80)
    print("Browser will stay open for 15 seconds for manual inspection...")
    print("=" * 80)
    time.sleep(15)

finally:
    driver.quit()
    print("\nBrowser closed")
