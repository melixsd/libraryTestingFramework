from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import StaleElementReferenceException, ElementClickInterceptedException, TimeoutException
from selenium.webdriver.support import expected_conditions as EC

from .base_page import BasePage


class HomePage(BasePage):
    """Page Object for the Home / Book Catalog page."""

    NAV_HOME = ('[data-testid="nav-home"]',)
    SEARCH_SECTION = ('[data-testid="search-section"]',)
    SEARCH_INPUT = ('[data-testid="search-input"]',)
    BOOKS_GRID = ('[data-testid="books-grid"]',)
    NO_BOOKS = ('[data-testid="no-books-found"]',)
    BOOK_CARD_PREFIX = '[data-testid^="book-card-"]'
    BOOK_DETAIL = ('[data-testid="book-detail-page"]',)

    def search(self, query, expected_text=None, timeout=30):
        """Enter a search query and wait until the filtered result is stable."""
        # type_text verifies the query landed: Chrome's input stalls drop
        # trusted keystrokes silently, which would leave the catalogue
        # unfiltered and the settled wait below would time out.
        self.type_text(self.SEARCH_INPUT, query, timeout=timeout)
        # Quiet window between typing and polling: the filtered grid mounts
        # with an entrance animation that must finish before card text is
        # readable (see BasePage.settle).
        self.settle()

        query_lower = query.strip().lower()
        expected_lower = expected_text.lower() if expected_text else None

        def search_settled(driver):
            cards = driver.find_elements(By.CSS_SELECTOR, self.BOOK_CARD_PREFIX)
            no_books = driver.find_elements(By.CSS_SELECTOR, self.NO_BOOKS[0])

            if no_books and not cards:
                return True
            if not cards:
                return False

            try:
                texts = [card.text.lower() for card in cards]
            except StaleElementReferenceException:
                return False

            if not all(query_lower in text for text in texts):
                return False
            if expected_lower and not any(expected_lower in text for text in texts):
                return False
            return True

        WebDriverWait(self.driver, timeout, poll_frequency=0.25).until(search_settled)
        return self

    def open_book_by_title(self, title, timeout=20):
        """Open an exact book card and wait for the detail view.

        The catalogue is rendered by React + Framer Motion. After a search,
        the card can be replaced while the animation is settling, so the card
        is resolved from the live DOM and the click is retried if the first
        interaction does not transition to the detail view.
        """
        title = title.strip()
        title_lower = title.lower()
        exact_aria = f'View details for {title}'

        def find_card(driver):
            # Prefer the application's stable semantic locator.
            cards = driver.find_elements(
                By.CSS_SELECTOR,
                f'[data-testid^="book-card-"][aria-label="{exact_aria}"]',
            )
            for card in cards:
                try:
                    if card.is_displayed() and card.is_enabled():
                        return card
                except StaleElementReferenceException:
                    continue

            # Fallback for case differences / titles containing unusual markup.
            for card in driver.find_elements(By.CSS_SELECTOR, self.BOOK_CARD_PREFIX):
                try:
                    aria = (card.get_attribute("aria-label") or "").strip().lower()
                    text = (card.text or "").strip().lower()
                    if card.is_displayed() and card.is_enabled() and (
                        title_lower in aria or text == title_lower or title_lower in text
                    ):
                        return card
                except StaleElementReferenceException:
                    continue
            return False

        card = WebDriverWait(self.driver, timeout, poll_frequency=0.25).until(find_card)
        self.driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center', inline: 'center'});", card
        )

        # Re-resolve after scrolling because Framer Motion may replace the node.
        card = WebDriverWait(self.driver, timeout, poll_frequency=0.25).until(find_card)

        # Try normal Selenium interaction first, then browser-level click fallbacks.
        # Each attempt is followed by a short transition wait so we don't blindly
        # click the same element several times after a successful navigation.
        click_attempts = []
        click_attempts.append(lambda: card.click())
        click_attempts.append(
            lambda: self.driver.execute_script("arguments[0].click();", card)
        )

        for attempt in click_attempts:
            try:
                attempt()
            except (ElementClickInterceptedException, StaleElementReferenceException):
                pass

            try:
                WebDriverWait(self.driver, 4, poll_frequency=0.2).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, self.BOOK_DETAIL[0]))
                )
                return self
            except Exception:
                card = WebDriverWait(self.driver, timeout, poll_frequency=0.25).until(find_card)

        # Final deterministic fallback: dispatch a real bubbling mouse click on
        # the exact semantic button currently in the DOM. This handles cases where
        # an animated overlay briefly intercepts Selenium's native click.
        self.driver.execute_script(
            """
            const wanted = arguments[0];
            const card = Array.from(document.querySelectorAll('[data-testid^="book-card-"]'))
              .find(el => (el.getAttribute('aria-label') || '') === wanted);
            if (card) {
              card.scrollIntoView({block: 'center', inline: 'center'});
              card.dispatchEvent(new MouseEvent('click', {
                view: window, bubbles: true, cancelable: true
              }));
            }
            """,
            exact_aria,
        )

        WebDriverWait(self.driver, timeout, poll_frequency=0.25).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, self.BOOK_DETAIL[0]))
        )
        return self

    def clear_search(self):
        """Clear the search input and wait for the catalogue to refresh."""
        self.wait_for_visible(self.SEARCH_INPUT).clear()
        self.wait_for_catalogue_update()
        return self

    def wait_for_catalogue_update(self, timeout=20):
        """Wait until the catalogue has a rendered result state."""
        def catalogue_settled(driver):
            cards = driver.find_elements(By.CSS_SELECTOR, self.BOOK_CARD_PREFIX)
            no_books = driver.find_elements(By.CSS_SELECTOR, self.NO_BOOKS[0])
            return bool(cards or no_books)

        WebDriverWait(self.driver, timeout, poll_frequency=0.25).until(catalogue_settled)
        return self

    def get_book_cards(self):
        return self.driver.find_elements(By.CSS_SELECTOR, self.BOOK_CARD_PREFIX)

    def click_first_book(self, timeout=30):
        """Click the first visible book card and wait for the detail view."""
        def find_card(driver):
            for card in driver.find_elements(By.CSS_SELECTOR, self.BOOK_CARD_PREFIX):
                try:
                    if card.is_displayed() and card.is_enabled():
                        return card
                except StaleElementReferenceException:
                    continue
            return False

        card = WebDriverWait(self.driver, timeout, poll_frequency=0.25).until(find_card)
        self.driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center', inline: 'center'});", card
        )
        try:
            card.click()
        except (ElementClickInterceptedException, StaleElementReferenceException):
            card = WebDriverWait(self.driver, timeout).until(find_card)
            self.driver.execute_script("arguments[0].click();", card)
        try:
            # Chrome's input stalls can swallow the trusted click without any
            # exception; if the detail view does not follow shortly, re-click
            # through the DOM instead of burning the whole timeout.
            WebDriverWait(self.driver, 4, poll_frequency=0.25).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, self.BOOK_DETAIL[0]))
            )
        except TimeoutException:
            card = WebDriverWait(self.driver, timeout, poll_frequency=0.25).until(find_card)
            self.driver.execute_script("arguments[0].click();", card)
        WebDriverWait(self.driver, timeout, poll_frequency=0.25).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, self.BOOK_DETAIL[0]))
        )
        return self

    def click_book(self, book_id):
        locator = (f'[data-testid="book-card-{book_id}"]',)
        self.wait_for_clickable(locator).click()
        self.wait_for_visible(self.BOOK_DETAIL, timeout=20)
        return self

    def get_books_count(self):
        return len(self.get_book_cards())

    def is_loaded(self):
        return self.is_visible(self.NAV_HOME)

    def wait_for_home_content(self, timeout=60):
        """Wait for the search area and a completed catalogue state."""
        WebDriverWait(self.driver, timeout, poll_frequency=0.25).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, self.SEARCH_SECTION[0]))
        )

        def content_ready(driver):
            cards = driver.find_elements(By.CSS_SELECTOR, self.BOOK_CARD_PREFIX)
            no_books = driver.find_elements(By.CSS_SELECTOR, self.NO_BOOKS[0])
            return bool(cards or no_books)

        WebDriverWait(self.driver, timeout, poll_frequency=0.25).until(content_ready)
        # The catalogue mounts with entrance animations (grid, sidebar, cards)
        # that resolve on animation frames; go quiet so they finish before any
        # caller starts polling (see BasePage.settle).
        self.settle()
        return self
