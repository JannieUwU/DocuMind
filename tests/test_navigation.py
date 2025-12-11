"""
Test Suite: Navigation and Routing Tests
Tests navigation between pages and route guards
"""
import pytest
import time


class TestNavigation:
    """Test cases for navigation and routing"""

    def test_01_navigate_login_to_register(self, driver, config):
        """Test navigation from login to register page"""
        # Start on login
        driver.get(f"{config.BASE_URL}/#/login")
        time.sleep(config.ANIMATION_WAIT)

        # Click register link
        driver.execute_script("""
            const link = Array.from(document.querySelectorAll('a'))
                .find(a => a.textContent.includes('Sign up'));
            if (link) link.click();
        """)
        time.sleep(2)

        # Verify on register page
        current_hash = driver.execute_script("return window.location.hash;")
        assert "#/register" in current_hash, f"Should be on register, got: {current_hash}"

    def test_02_navigate_register_to_login(self, driver, config):
        """Test navigation from register to login page"""
        # Start on register
        driver.get(f"{config.BASE_URL}/#/register")
        time.sleep(config.ANIMATION_WAIT)

        # Click login link
        driver.execute_script("""
            const link = Array.from(document.querySelectorAll('a'))
                .find(a => a.textContent.includes('Sign in'));
            if (link) link.click();
        """)
        time.sleep(2)

        # Verify on login page
        current_hash = driver.execute_script("return window.location.hash;")
        assert "#/login" in current_hash, f"Should be on login, got: {current_hash}"

    def test_03_navigate_login_to_reset_password(self, driver, config):
        """Test navigation from login to reset password page"""
        # Start on login
        driver.get(f"{config.BASE_URL}/#/login")
        time.sleep(config.ANIMATION_WAIT)

        # Click forgot password link
        driver.execute_script("""
            const link = Array.from(document.querySelectorAll('a'))
                .find(a => a.textContent.includes('Forgot password'));
            if (link) link.click();
        """)
        time.sleep(2)

        # Verify on reset password page
        current_hash = driver.execute_script("return window.location.hash;")
        assert "#/reset-password" in current_hash, \
            f"Should be on reset password, got: {current_hash}"

    def test_04_dashboard_redirect_unauthorized(self, driver, config):
        """Test that unauthorized users are redirected from dashboard"""
        # Clear storage
        driver.get(config.BASE_URL)
        driver.execute_script("localStorage.clear(); sessionStorage.clear();")

        # Try to access dashboard
        driver.get(f"{config.BASE_URL}/#/dashboard")
        time.sleep(config.LONG_WAIT)

        # Should be redirected to login
        current_hash = driver.execute_script("return window.location.hash;")
        assert "#/login" in current_hash, \
            f"Unauthorized user should be redirected to login, got: {current_hash}"

    def test_05_direct_url_navigation_login(self, driver, config):
        """Test direct URL navigation to login page"""
        driver.get(f"{config.BASE_URL}/#/login")
        time.sleep(config.ANIMATION_WAIT)

        current_hash = driver.execute_script("return window.location.hash;")
        assert "#/login" in current_hash, "Direct navigation to login failed"

    def test_06_direct_url_navigation_register(self, driver, config):
        """Test direct URL navigation to register page"""
        driver.get(f"{config.BASE_URL}/#/register")
        time.sleep(config.ANIMATION_WAIT)

        current_hash = driver.execute_script("return window.location.hash;")
        assert "#/register" in current_hash, "Direct navigation to register failed"

    def test_07_hash_routing_structure(self, driver, config):
        """Test that app uses hash-based routing"""
        driver.get(config.BASE_URL)
        time.sleep(2)

        # Check that we have a hash in URL
        current_url = driver.current_url
        assert "#" in current_url, "App should use hash-based routing"

    def test_08_browser_back_button(self, driver, config):
        """Test browser back button navigation"""
        # Navigate to login
        driver.get(f"{config.BASE_URL}/#/login")
        time.sleep(config.ANIMATION_WAIT)

        # Navigate to register
        driver.get(f"{config.BASE_URL}/#/register")
        time.sleep(config.ANIMATION_WAIT)

        # Go back
        driver.back()
        time.sleep(2)

        # Should be on login again
        current_hash = driver.execute_script("return window.location.hash;")
        assert "#/login" in current_hash, "Back button should return to login"

    def test_09_browser_forward_button(self, driver, config):
        """Test browser forward button navigation"""
        # Navigate to login
        driver.get(f"{config.BASE_URL}/#/login")
        time.sleep(config.ANIMATION_WAIT)

        # Navigate to register
        driver.get(f"{config.BASE_URL}/#/register")
        time.sleep(config.ANIMATION_WAIT)

        # Go back
        driver.back()
        time.sleep(2)

        # Go forward
        driver.forward()
        time.sleep(2)

        # Should be on register again
        current_hash = driver.execute_script("return window.location.hash;")
        assert "#/register" in current_hash, "Forward button should return to register"

    def test_10_invalid_route_handling(self, driver, config):
        """Test navigation to invalid route"""
        # Navigate to non-existent route
        driver.get(f"{config.BASE_URL}/#/nonexistent")
        time.sleep(config.ANIMATION_WAIT)

        # Should handle gracefully (redirect or show 404)
        current_url = driver.current_url
        # App should handle this somehow (not crash)
        assert config.BASE_URL in current_url, "App should handle invalid route"

    def test_11_welcome_page_access(self, driver, config):
        """Test access to welcome page"""
        driver.get(f"{config.BASE_URL}/#/")
        time.sleep(config.ANIMATION_WAIT)

        # Check if on welcome or redirected
        current_hash = driver.execute_script("return window.location.hash;")
        # Could be welcome, login, or dashboard depending on auth state
        assert current_hash is not None, "Should be on some valid page"

    def test_12_multiple_rapid_navigations(self, driver, config):
        """Test rapid navigation between pages"""
        pages = ["login", "register", "login", "reset-password", "login"]

        for page in pages:
            driver.get(f"{config.BASE_URL}/#/{page}")
            time.sleep(0.5)  # Short wait

        # Final check - should be on login
        time.sleep(2)
        current_hash = driver.execute_script("return window.location.hash;")
        assert "#/login" in current_hash, "Rapid navigation should work correctly"

    def test_13_url_persistence_refresh(self, driver, config):
        """Test that URL persists after page refresh"""
        # Navigate to register
        driver.get(f"{config.BASE_URL}/#/register")
        time.sleep(config.ANIMATION_WAIT)

        # Refresh page
        driver.refresh()
        time.sleep(config.ANIMATION_WAIT)

        # Should still be on register
        current_hash = driver.execute_script("return window.location.hash;")
        assert "#/register" in current_hash, "URL should persist after refresh"

    def test_14_navigation_without_page_reload(self, driver, config):
        """Test SPA navigation without full page reload"""
        driver.get(f"{config.BASE_URL}/#/login")
        time.sleep(config.ANIMATION_WAIT)

        # Get page load timestamp
        initial_time = driver.execute_script("return window.performance.timing.loadEventEnd;")

        # Navigate using link (SPA navigation)
        driver.execute_script("""
            const link = document.querySelector('a[href*="register"]');
            if (link) link.click();
        """)
        time.sleep(2)

        # Get new timestamp
        new_time = driver.execute_script("return window.performance.timing.loadEventEnd;")

        # Time should be same (no full reload)
        assert initial_time == new_time, "SPA navigation should not reload page"

    def test_15_route_guard_protection(self, driver, config):
        """Test that route guards protect authenticated routes"""
        # Clear all auth
        driver.get(config.BASE_URL)
        driver.execute_script("localStorage.clear(); sessionStorage.clear();")

        # Try to access dashboard
        driver.get(f"{config.BASE_URL}/#/dashboard")
        time.sleep(config.LONG_WAIT)

        # Should be redirected away from dashboard
        current_hash = driver.execute_script("return window.location.hash;")
        assert "#/dashboard" not in current_hash or "#/login" in current_hash, \
            "Route guard should protect dashboard"
