from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from .base_page import BasePage


class BookDetailPage(BasePage):
    """Page Object for the Book Detail page."""

    BOOK_DETAIL_PAGE = ('[data-testid="book-detail-page"]',)
    BOOK_TITLE = ('[data-testid="book-title"]',)
    AVAILABILITY = ('[data-testid="status-available"], [data-testid="status-checked-out"]',)
    COPIES_AVAILABLE = ('[data-testid="copies-available"]',)
    BORROW_BUTTON = ('[data-testid="btn-borrow"]',)
    RESERVE_BUTTON = ('[data-testid="btn-reserve"]',)

    def get_copies_available(self):
        """Return the 'N of M' copies text of the availability card."""
        if self.is_visible(self.COPIES_AVAILABLE):
            return " ".join(self.find(self.COPIES_AVAILABLE).text.split())
        return ""

    def wait_for_copies_to_change(self, previous, timeout=15):
        """Wait until the remaining-copies count leaves its pre-mutation value.

        Borrowing one copy of a multi-copy title keeps the badge on
        "Available" — the observable refresh is the copies count dropping.
        """
        WebDriverWait(self.driver, timeout, poll_frequency=0.25).until(
            lambda d: self.get_copies_available() not in (previous, "")
        )
        return self

    def get_title(self):
        """Return the book title text."""
        if self.is_visible(self.BOOK_TITLE):
            return self.find(self.BOOK_TITLE).text
        return ""

    def get_availability(self):
        """Return the availability status text."""
        if self.is_visible(self.AVAILABILITY):
            return self.find(self.AVAILABILITY).text
        return ""

    def _click_action_button(self, locator, busy_text, effect):
        """Click Borrow/Reserve, verifying the click actually registered.

        Chrome's input stalls can swallow a trusted click without raising.
        `effect` is a zero-arg callable reporting whether the mutation is
        visible (busy state, button removal, or the copies count changing).
        When nothing happens shortly after the native click, re-click
        through the DOM.
        """
        button = self.wait_for_clickable(locator)
        button.click()

        by, value = self._normalize_locator(locator)

        def registered(driver):
            buttons = driver.find_elements(By.CSS_SELECTOR, value)
            if not buttons or busy_text in buttons[0].text:
                return True
            return effect()

        try:
            WebDriverWait(self.driver, 3, poll_frequency=0.2).until(registered)
        except Exception:
            buttons = self.driver.find_elements(By.CSS_SELECTOR, value)
            if buttons:
                self.driver.execute_script("arguments[0].click();", buttons[0])
        return self

    def click_borrow(self):
        """Click the borrow button."""
        before = self.get_copies_available()
        return self._click_action_button(
            self.BORROW_BUTTON,
            "Borrowing",
            effect=lambda: self.get_copies_available() not in ("", before),
        )

    def click_reserve(self):
        """Click the reserve button."""
        before = self.get_availability()
        return self._click_action_button(
            self.RESERVE_BUTTON,
            "Reserving",
            effect=lambda: self.get_availability() != before,
        )

    def wait_for_borrow_button_to_finish(self, timeout=10):
        """Wait until the borrow button leaves its loading state."""
        WebDriverWait(self.driver, timeout).until(
            lambda d: not d.find_elements(By.CSS_SELECTOR, self.BORROW_BUTTON[0])
            or "Borrowing..." not in d.find_element(By.CSS_SELECTOR, self.BORROW_BUTTON[0]).text
        )
        return self

    def wait_for_reserve_button_to_finish(self, timeout=10):
        """Wait until the reserve button leaves its loading state."""
        WebDriverWait(self.driver, timeout).until(
            lambda d: not d.find_elements(By.CSS_SELECTOR, self.RESERVE_BUTTON[0])
            or "Reserving..." not in d.find_element(By.CSS_SELECTOR, self.RESERVE_BUTTON[0]).text
        )
        return self

    def is_loaded(self):
        """Return True if the book detail page element is visible."""
        return self.is_visible(self.BOOK_DETAIL_PAGE)
