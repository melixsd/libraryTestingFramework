from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from .base_page import BasePage


class BookDetailPage(BasePage):
    """Page Object for the Book Detail page."""

    BOOK_DETAIL_PAGE = ('[data-testid="book-detail-page"]',)
    BOOK_TITLE = ('[data-testid="book-title"]',)
    AVAILABILITY = ('[data-testid="status-available"], [data-testid="status-checked-out"]',)
    BORROW_BUTTON = ('[data-testid="btn-borrow"]',)
    RESERVE_BUTTON = ('[data-testid="btn-reserve"]',)

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

    def click_borrow(self):
        """Click the borrow button."""
        self.wait_for_clickable(self.BORROW_BUTTON).click()
        return self

    def click_reserve(self):
        """Click the reserve button."""
        self.wait_for_clickable(self.RESERVE_BUTTON).click()
        return self

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
