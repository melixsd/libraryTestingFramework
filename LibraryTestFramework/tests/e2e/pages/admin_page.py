from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from .base_page import BasePage


class AdminPage(BasePage):
    """Page Object for the Admin page."""

    ADMIN_PAGE = ('[data-testid="admin-page"]',)
    NAV_ADMIN = ('[data-testid="nav-admin"]',)
    TAB_BOOKS = ('[data-testid="tab-books"]',)
    BOOKS_TOOLBAR_ADD = ('[data-testid="books-toolbar-add"]',)
    ADD_BOOK_TITLE = ('[data-testid="add-book-title"]',)
    ADD_BOOK_AUTHOR = ('[data-testid="add-book-author"]',)
    ADD_BOOK_ISBN = ('[data-testid="add-book-isbn"]',)
    ADD_BOOK_PRICE = ('[data-testid="add-book-price"]',)
    ADD_BOOK_COPIES = ('[data-testid="add-book-copies"]',)
    ADD_BOOK_DESCRIPTION = ('[data-testid="add-book-desc"]',)
    ADD_BOOK_SUBMIT = ('[data-testid="btn-add-book-submit"]',)
    BOOKS_TABLE = ('[data-testid="books-table"]',)

    def navigate(self):
        """Navigate to the admin page by clicking the admin nav link."""
        self.wait_for_clickable(self.NAV_ADMIN).click()
        self.wait_for_visible(self.ADMIN_PAGE)
        return self

    def get_active_tab(self):
        """Return the currently active tab text, or empty string."""
        tabs = self.driver.find_elements(
            By.CSS_SELECTOR, '[data-testid^="tab-"][class*="active"]'
        )
        if tabs:
            return tabs[0].text
        return ""

    def click_tab(self, tab):
        """Click a specific tab by its data-testid value (e.g. 'tab-books')."""
        locator = (f'[data-testid="{tab}"]',)
        self.wait_for_clickable(locator).click()

    def create_book(self, title, isbn, author_id=None, price="19.99", copies="1", description="E2E test book"):
        """Create a book through the real admin UI and wait for it to appear."""
        from selenium.webdriver.support.ui import Select

        self.wait_for_clickable(self.BOOKS_TOOLBAR_ADD).click()
        self.wait_for_visible(self.ADD_BOOK_TITLE).send_keys(title)

        author = self.wait_for_visible(self.ADD_BOOK_AUTHOR)
        WebDriverWait(self.driver, 10).until(
            lambda d: len(d.find_elements(By.CSS_SELECTOR, self.ADD_BOOK_AUTHOR[0] + " option")) > 0
        )
        select = Select(author)
        if author_id is not None:
            select.select_by_value(str(author_id))
        else:
            # No author explicitly requested — pick the first real option,
            # skipping a leading empty/placeholder option if present, so the
            # form is actually submittable (a human would always pick one).
            for option in select.options:
                value = option.get_attribute("value")
                if value:
                    select.select_by_value(value)
                    break

        self.wait_for_visible(self.ADD_BOOK_ISBN).send_keys(isbn)
        self.wait_for_visible(self.ADD_BOOK_PRICE).clear()
        self.driver.find_element(By.CSS_SELECTOR, self.ADD_BOOK_PRICE[0]).send_keys(price)
        self.wait_for_visible(self.ADD_BOOK_COPIES).clear()
        self.driver.find_element(By.CSS_SELECTOR, self.ADD_BOOK_COPIES[0]).send_keys(copies)
        self.wait_for_visible(self.ADD_BOOK_DESCRIPTION).send_keys(description)
        self.wait_for_clickable(self.ADD_BOOK_SUBMIT).click()

        return self.wait_for_book_title(title)

    def wait_for_book_title(self, title, timeout=30):
        """Wait until a book row containing the supplied title is rendered."""
        def find_row(driver):
            rows = driver.find_elements(By.CSS_SELECTOR, '[data-testid^="book-row-"]')
            for row in rows:
                if title.lower() in row.text.lower():
                    return row
            return False

        return WebDriverWait(self.driver, timeout).until(find_row)

    def is_loaded(self):
        """Return True if the admin page element is visible."""
        return self.is_visible(self.ADMIN_PAGE)
