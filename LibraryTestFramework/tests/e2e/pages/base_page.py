"""
Base Page Object for the Library Management System.
Provides common Selenium helper methods used by all page objects.
"""
import os
import time
from datetime import datetime
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
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

    # Chrome can silently drop trusted keystrokes mid-session (input delivery
    # stalls that survive navigation — see the e2e probe notes). The drop is
    # invisible to Selenium: send_keys returns normally, the field just stays
    # empty, and React never sees an input event. The workaround is to verify
    # the field value after typing and, when the keystrokes were swallowed,
    # set the value through the native setter and dispatch a bubbling input
    # event — the same signal React's controlled inputs listen for.
    _JS_SET_VALUE = """
        const el = arguments[0], text = arguments[1];
        const proto = el instanceof HTMLTextAreaElement
          ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
        Object.getOwnPropertyDescriptor(proto, 'value').set.call(el, text);
        el.dispatchEvent(new Event('input', { bubbles: true }));
        el.dispatchEvent(new Event('change', { bubbles: true }));
        return el.value;
    """

    def type_text(self, locator, text, timeout=10):
        """Type text into a field, verifying that it actually landed.

        Native keystrokes are attempted first; whenever the value does not
        stick, the element is re-resolved (React may have replaced the node)
        and the text is set through the native setter with a bubbling input
        event, which React's controlled inputs register like real typing.
        """
        deadline = time.monotonic() + timeout
        last_error = None
        while time.monotonic() < deadline:
            el = self.wait_for_visible(locator, timeout=2)
            try:
                el.clear()
                el.send_keys(text)
            except StaleElementReferenceException:
                continue
            if el.get_attribute("value") == text:
                return el
            try:
                el = self.wait_for_visible(locator, timeout=2)
                self._driver.execute_script(self._JS_SET_VALUE, el, text)
            except StaleElementReferenceException:
                continue
            if el.get_attribute("value") == text:
                return el
            time.sleep(0.5)
        raise last_error or TimeoutException(
            f"could not type {text!r} into {locator}: value never verified"
        )

    def settle(self, seconds=2.5):
        """Pause all Selenium/CDP activity to let headless Chrome finish rendering.

        React + framer-motion apply entrance states (opacity 0) synchronously
        and resolve them on later animation frames. Continuous CDP polling from
        the instant the elements appear can leave that work unfinished: the
        DOM is complete but the subtree stays at opacity 0, so Selenium reads
        no text and is_displayed() is False no matter how long it keeps
        polling. A short quiet window consistently lets the page reach its
        final rendered state (verified with browser-side probes).
        """
        time.sleep(seconds)
        return self

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
