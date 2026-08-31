"""
Base Page Object for the Library Management System.
Provides common Selenium helper methods used by all page objects.
"""
import os
from datetime import datetime
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


class BasePage:
    """Base class for all Page Objects."""

    def __init__(self, driver):
        self._driver = driver

    @property
    def driver(self):
        return self._driver

    def find(self, locator, timeout=10):
        """Find a single visible element using explicit wait."""
        by, value = self._normalize_locator(locator)
        return WebDriverWait(self._driver, timeout).until(
            EC.visibility_of_element_located((by, value))
        )

    def find_all(self, locator, timeout=10):
        """Find all matching elements, waiting until at least one is present."""
        by, value = self._normalize_locator(locator)
        return WebDriverWait(self._driver, timeout).until(
            EC.presence_of_all_elements_located((by, value))
        )

    def wait_for_visible(self, locator, timeout=10):
        """Wait until an element is visible."""
        by, value = self._normalize_locator(locator)
        return WebDriverWait(self._driver, timeout).until(
            EC.visibility_of_element_located((by, value))
        )

    def wait_for_loading_to_finish(self, timeout=30):
        """Wait for any loading spinners to disappear."""
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support import expected_conditions as EC
        WebDriverWait(self._driver, timeout).until_not(
            EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="loading"], .animate-spin, [role="status"]'))
        )
        return self

    def wait_for_clickable(self, locator, timeout=10):
        """Wait until an element is clickable."""
        by, value = self._normalize_locator(locator)
        return WebDriverWait(self._driver, timeout).until(
            EC.element_to_be_clickable((by, value))
        )

    def is_visible(self, locator, timeout=3):
        """Check if an element is visible within the timeout."""
        by, value = self._normalize_locator(locator)
        try:
            WebDriverWait(self._driver, timeout).until(
                EC.visibility_of_element_located((by, value))
            )
            return True
        except Exception:
            return False

    def is_present(self, locator, timeout=3):
        """Check if an element is present in the DOM within the timeout."""
        by, value = self._normalize_locator(locator)
        try:
            WebDriverWait(self._driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return True
        except Exception:
            return False

    def screenshot(self, name):
        """Save a screenshot to tests/e2e/screenshots/."""
        screenshot_dir = os.path.join(
            os.path.dirname(__file__), "..", "screenshots"
        )
        os.makedirs(screenshot_dir, exist_ok=True)
        path = os.path.join(
            screenshot_dir,
            f"{name}_{datetime.now():%Y%m%d_%H%M%S}.png",
        )
        self._driver.save_screenshot(path)
        return path

    @staticmethod
    def _normalize_locator(locator):
        """Accept both (By, value) tuples and (str, str) shorthand.

        If the first element is already a By enum, return as-is.
        Otherwise assume CSS_SELECTOR.
        """
        if isinstance(locator[0], By):
            return locator
        return (By.CSS_SELECTOR, locator[0])
