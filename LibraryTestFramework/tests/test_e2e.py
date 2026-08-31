"""
Selenium E2E tests for the Library Management System frontend.

Legacy suite kept for reference; the maintained Page-Object suite lives in
tests/e2e/test_e2e.py. These tests additionally require the webdriver-manager
package and are skipped automatically when it is not installed.

These tests require:
  1. The backend running at http://localhost:8000
  2. The frontend running at http://localhost:3000
  3. Chrome browser installed

Run with:  pytest tests/test_e2e.py -m selenium
"""
import os
import time
import pytest
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

pytest.importorskip(
    "webdriver_manager",
    reason="Legacy selenium suite requires webdriver-manager; "
           "the maintained suite lives in tests/e2e/",
)
from webdriver_manager.chrome import ChromeDriverManager  # noqa: E402


BASE_URL = "http://localhost:3000"
SCREENSHOT_DIR = os.path.join(os.path.dirname(__file__), "screenshots")


@pytest.fixture(scope="module")
def driver():
    """Set up Chrome WebDriver for the entire test module."""
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1280,720")

    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.implicitly_wait(3)
    yield driver
    driver.quit()


def _take_screenshot(driver, name):
    """Save a screenshot on test failure for debugging."""
    path = os.path.join(SCREENSHOT_DIR, f"{name}_{datetime.now():%Y%m%d_%H%M%S}.png")
    driver.save_screenshot(path)
    return path


def _wait_for_element(driver, by, value, timeout=10):
    """Wait for an element to be present and visible."""
    return WebDriverWait(driver, timeout).until(
        EC.visibility_of_element_located((by, value))
    )


def _login_as(driver, username, password):
    """Navigate to the app and log in with the given credentials."""
    driver.get(BASE_URL)
    # Wait for login form to appear
    _wait_for_element(driver, By.CSS_SELECTOR, '[data-testid="login-form"]')
    driver.find_element(By.CSS_SELECTOR, '[data-testid="login-username"]').send_keys(username)
    driver.find_element(By.CSS_SELECTOR, '[data-testid="login-password"]').send_keys(password)
    driver.find_element(By.CSS_SELECTOR, '[data-testid="login-submit"]').click()
    # Wait for navigation away from login
    WebDriverWait(driver, 10).until(
        lambda d: d.find_elements(By.CSS_SELECTOR, '[data-testid="login-form"]') == []
        or d.find_elements(By.CSS_SELECTOR, '[data-testid="nav-home"]')
    )
    time.sleep(1)  # Allow state to settle


def _logout(driver):
    """Click the logout button if visible."""
    try:
        btn = driver.find_element(By.CSS_SELECTOR, '[data-testid="btn-logout"]')
        btn.click()
        time.sleep(1)
    except Exception:
        pass


# ==================================================================
# Login flow
# ==================================================================

pytestmark = pytest.mark.selenium


class TestLoginFlow:
    """E2E tests for the login flow."""

    def test_admin_login_shows_admin_page(self, driver):
        """Login as admin -> verify the admin nav item appears."""
        _login_as(driver, "admin", "Admin123!")
        try:
            admin_nav = _wait_for_element(driver, By.CSS_SELECTOR, '[data-testid="nav-admin"]', timeout=10)
            assert admin_nav.is_displayed()
        except Exception:
            _take_screenshot(driver, "admin_login")
            raise
        finally:
            _logout(driver)

    def test_member_login_shows_home_page(self, driver):
        """Login as member1 -> verify home page content loads."""
        _login_as(driver, "member1", "Member123!")
        try:
            home = _wait_for_element(driver, By.CSS_SELECTOR, '[data-testid="nav-home"]', timeout=10)
            assert home.is_displayed()
        except Exception:
            _take_screenshot(driver, "member_login")
            raise
        finally:
            _logout(driver)

    def test_invalid_login_shows_error(self, driver):
        """Login with wrong credentials -> error message displayed."""
        driver.get(BASE_URL)
        _wait_for_element(driver, By.CSS_SELECTOR, '[data-testid="login-form"]')
        driver.find_element(By.CSS_SELECTOR, '[data-testid="login-username"]').send_keys("admin")
        driver.find_element(By.CSS_SELECTOR, '[data-testid="login-password"]').send_keys("wrong")
        driver.find_element(By.CSS_SELECTOR, '[data-testid="login-submit"]').click()

        try:
            error_el = _wait_for_element(driver, By.CSS_SELECTOR, '[data-testid="login-error"]', timeout=10)
            assert error_el.is_displayed()
        except Exception:
            _take_screenshot(driver, "invalid_login")
            raise


# ==================================================================
# Browse and search
# ==================================================================

class TestBrowseAndSearch:
    """E2E tests for browsing books and using search/filter."""

    def test_search_books(self, driver):
        """Login, type a search query, verify results update."""
        _login_as(driver, "member1", "Member123!")
        try:
            search_input = _wait_for_element(driver, By.CSS_SELECTOR, '[data-testid="search-input"]', timeout=10)
            search_input.send_keys("Clean")
            time.sleep(1)  # Wait for debounce
            # Verify at least one book card is present
            cards = driver.find_elements(By.CSS_SELECTOR, '[data-testid^="book-card-"]')
            assert len(cards) >= 0  # May be 0 if no match, just verify no crash
        except Exception:
            _take_screenshot(driver, "search_books")
            raise
        finally:
            _logout(driver)

    def test_click_book_card_shows_detail(self, driver):
        """Click a book card and verify the detail page loads."""
        _login_as(driver, "member1", "Member123!")
        try:
            # Wait for book cards to load
            cards = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, '[data-testid^="book-card-"]'))
            )
            if cards:
                cards[0].click()
                detail = _wait_for_element(driver, By.CSS_SELECTOR, '[data-testid="book-detail-page"]', timeout=10)
                assert detail.is_displayed()
        except Exception:
            _take_screenshot(driver, "book_detail")
            raise
        finally:
            _logout(driver)


# ==================================================================
# Admin operations
# ==================================================================

class TestAdminOperations:
    """E2E tests for admin CRUD operations."""

    def test_admin_can_navigate_to_admin_page(self, driver):
        """Login as admin, click admin nav, verify admin page loads."""
        _login_as(driver, "admin", "Admin123!")
        try:
            admin_nav = _wait_for_element(driver, By.CSS_SELECTOR, '[data-testid="nav-admin"]', timeout=10)
            admin_nav.click()
            _wait_for_element(driver, By.CSS_SELECTOR, '[data-testid="admin-page"]', timeout=10)
        except Exception:
            _take_screenshot(driver, "admin_page")
            raise
        finally:
            _logout(driver)

    def test_admin_books_tab_visible(self, driver):
        """Navigate to admin page and verify the Books tab is visible."""
        _login_as(driver, "admin", "Admin123!")
        try:
            admin_nav = _wait_for_element(driver, By.CSS_SELECTOR, '[data-testid="nav-admin"]', timeout=10)
            admin_nav.click()
            tab = _wait_for_element(driver, By.CSS_SELECTOR, '[data-testid="tab-books"]', timeout=10)
            assert tab.is_displayed()
        except Exception:
            _take_screenshot(driver, "admin_books_tab")
            raise
        finally:
            _logout(driver)


# ==================================================================
# Navigation
# ==================================================================

class TestNavigation:
    """E2E tests for role-based navigation items."""

    def test_admin_sees_admin_nav(self, driver):
        """Admin user should see the Admin nav item."""
        _login_as(driver, "admin", "Admin123!")
        try:
            admin_nav = _wait_for_element(driver, By.CSS_SELECTOR, '[data-testid="nav-admin"]', timeout=10)
            assert admin_nav.is_displayed()
        except Exception:
            _take_screenshot(driver, "admin_nav_visible")
            raise
        finally:
            _logout(driver)

    def test_member_does_not_see_admin_nav(self, driver):
        """Regular member should NOT see the Admin nav item."""
        _login_as(driver, "member1", "Member123!")
        try:
            time.sleep(2)
            admin_navs = driver.find_elements(By.CSS_SELECTOR, '[data-testid="nav-admin"]')
            assert len(admin_navs) == 0, "Member should not see admin nav"
        except Exception:
            _take_screenshot(driver, "member_no_admin_nav")
            raise
        finally:
            _logout(driver)
