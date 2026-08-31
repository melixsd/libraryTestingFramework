"""
Selenium E2E tests for the Library Management System frontend.

These tests require:
  1. The backend running at http://localhost:8000
  2. The frontend running at http://localhost:3000
  3. Chrome browser installed

Run with:  pytest tests/e2e/test_e2e.py -m e2e
"""
import os
import shutil
from pathlib import Path
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

from tests.e2e.pages.login_page import LoginPage
from tests.e2e.pages.home_page import HomePage
from tests.e2e.pages.book_detail_page import BookDetailPage
from tests.e2e.pages.admin_page import AdminPage


SCREENSHOT_DIR = os.path.join(os.path.dirname(__file__), "screenshots")

pytestmark = pytest.mark.e2e


def _unique_isbn():
    """Return a unique ISBN-shaped value accepted by the application validator."""
    import uuid

    # The application accepts ISBN-10/ISBN-13 by digit count (it does not
    # validate the checksum). Keep the generated value numeric and 13 digits.
    return "978" + str(uuid.uuid4().int)[-10:]


def _find_chromedriver():
    """Find a locally installed ChromeDriver without triggering a network download.

    Search order:
      1. CHROMEDRIVER_PATH
      2. tools/chromedriver.exe inside this project
      3. chromedriver.exe on PATH
      4. Selenium's local cache (if a driver was downloaded previously)
    """
    candidates = []

    configured = os.getenv("CHROMEDRIVER_PATH")
    if configured:
        candidates.append(Path(configured).expanduser())

    project_root = Path(__file__).resolve().parents[2]
    candidates.append(project_root / "tools" / "chromedriver.exe")
    candidates.append(project_root / "tools" / "chromedriver")

    on_path = shutil.which("chromedriver") or shutil.which("chromedriver.exe")
    if on_path:
        candidates.append(Path(on_path))

    user_profile = os.getenv("USERPROFILE")
    if user_profile:
        cache = Path(user_profile) / ".cache" / "selenium" / "chromedriver"
        if cache.exists():
            candidates.extend(sorted(cache.glob("**/chromedriver.exe"), reverse=True))

    for candidate in candidates:
        try:
            if candidate.is_file():
                return str(candidate.resolve())
        except OSError:
            continue
    return None


@pytest.fixture(scope="function")
def driver():
    """Set up an isolated Chrome WebDriver for each test.

    CHROMEDRIVER_PATH may be supplied when Selenium Manager cannot discover
    a locally installed driver. No machine-specific path is hard-coded.
    """
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1280,720")
    options.add_argument("--disable-gpu")

    chromedriver_path = _find_chromedriver()
    if chromedriver_path:
        service = ChromeService(executable_path=chromedriver_path)
        driver = webdriver.Chrome(service=service, options=options)
    elif os.getenv("ALLOW_SELENIUM_MANAGER"):
        # CI convenience: let Selenium Manager resolve a matching chromedriver
        # (requires internet). Local restricted environments keep failing fast.
        driver = webdriver.Chrome(options=options)
    else:
        # Selenium Manager may attempt an internet download. In restricted
        # environments that can fail with HTTP 403 and waste ~30 seconds per
        # test. Fail once with an actionable setup message instead.
        raise pytest.UsageError(
            "ChromeDriver was not found. Set CHROMEDRIVER_PATH to a compatible "
            "chromedriver.exe, put chromedriver.exe on PATH, place it under "
            "tools/chromedriver.exe, or set ALLOW_SELENIUM_MANAGER=1 to let "
            "Selenium Manager download a matching driver."
        )
    # Use explicit waits in Page Objects rather than mixing implicit and explicit waits.
    driver.implicitly_wait(0)
    yield driver
    driver.quit()


@pytest.fixture
def login_page(driver):
    """Provide a LoginPage instance."""
    return LoginPage(driver)


@pytest.fixture
def home_page(driver):
    """Provide a HomePage instance."""
    return HomePage(driver)


@pytest.fixture
def admin_page(driver):
    """Provide an AdminPage instance."""
    return AdminPage(driver)


# ==================================================================
# Login flow
# ==================================================================

class TestLoginFlow:
    """E2E tests for the login flow."""

    def test_admin_login_shows_admin_page(self, login_page):
        """Login as admin -> verify the admin nav item appears."""
        try:
            login_page.load().login("admin", "Admin123!")
            admin_nav = login_page.wait_for_visible(
                ('[data-testid="nav-admin"]',), timeout=10
            )
            assert admin_nav.is_displayed()
        except Exception:
            login_page.screenshot("admin_login")
            raise
        finally:
            login_page.logout()

    def test_member_login_shows_home_page(self, login_page, home_page):
        """Login as member1 -> verify home page content loads."""
        try:
            login_page.load().login("member1", "Member123!")
            assert home_page.is_loaded()
        except Exception:
            login_page.screenshot("member_login")
            raise
        finally:
            login_page.logout()

    def test_invalid_login_shows_error(self, login_page):
        """Login with wrong credentials -> error message displayed."""
        login_page.load()
        login_page.wait_for_visible(LoginPage.USERNAME_INPUT).send_keys("admin")
        login_page.wait_for_visible(LoginPage.PASSWORD_INPUT).send_keys("wrong")
        login_page.wait_for_clickable(LoginPage.SUBMIT_BUTTON).click()
        try:
            assert login_page.is_visible(LoginPage.ERROR, timeout=10)
        except Exception:
            login_page.screenshot("invalid_login")
            raise


# ==================================================================
# Browse and search
# ==================================================================

class TestBrowseAndSearch:
    """E2E tests for browsing books and using search/filter."""

    def test_search_books(self, login_page, home_page):
        """Login, type a search query, verify results update."""
        login_page.load().login("member1", "Member123!")
        try:
            home_page.search("Clean", expected_text="Clean Code")
            cards = home_page.get_book_cards()
            assert cards, "Searching for 'Clean' should return at least one book"
            assert any("Clean Code" in card.text for card in cards), (
                "Search results should contain the expected 'Clean Code' book"
            )
        except Exception:
            login_page.screenshot("search_books")
            raise
        finally:
            login_page.logout()

    def test_click_book_card_shows_detail(self, login_page, home_page):
        """Click a book card and verify the detail page loads."""
        login_page.load().login("member1", "Member123!")
        try:
            home_page.wait_for_catalogue_update()
            cards = home_page.get_book_cards()
            assert cards, "The catalogue should contain at least one book"
            home_page.click_first_book()
            detail = BookDetailPage(login_page.driver)
            assert detail.is_loaded(), "Clicking a book should open its detail page"
        except Exception:
            login_page.screenshot("book_detail")
            raise
        finally:
            login_page.logout()


# ==================================================================
# Admin operations
# ==================================================================

class TestAdminOperations:
    """E2E tests for admin CRUD operations."""

    def test_admin_can_navigate_to_admin_page(self, login_page, admin_page):
        """Login as admin, click admin nav, verify admin page loads."""
        login_page.load().login("admin", "Admin123!")
        try:
            admin_page.navigate()
            assert admin_page.is_loaded(), "Admin navigation should open the admin page"
        except Exception:
            login_page.screenshot("admin_page")
            raise
        finally:
            login_page.logout()

    def test_admin_books_tab_visible(self, login_page, admin_page):
        """Navigate to admin page and verify the Books tab is visible."""
        login_page.load().login("admin", "Admin123!")
        try:
            admin_page.navigate()
            assert admin_page.is_visible(AdminPage.TAB_BOOKS)
        except Exception:
            login_page.screenshot("admin_books_tab")
            raise
        finally:
            login_page.logout()


# ==================================================================
# Navigation
# ==================================================================

class TestNavigation:
    """E2E tests for role-based navigation items."""

    def test_admin_sees_admin_nav(self, login_page):
        """Admin user should see the Admin nav item."""
        login_page.load().login("admin", "Admin123!")
        try:
            admin_nav = login_page.wait_for_visible(
                ('[data-testid="nav-admin"]',), timeout=10
            )
            assert admin_nav.is_displayed()
        except Exception:
            login_page.screenshot("admin_nav_visible")
            raise
        finally:
            login_page.logout()

    def test_member_does_not_see_admin_nav(self, login_page):
        """Regular member should NOT see the Admin nav item."""
        login_page.load().login("member1", "Member123!")
        try:
            # Wait for the authenticated home page before checking role-based navigation.
            login_page.wait_for_visible(LoginPage.NAV_HOME, timeout=10)
            admin_navs = login_page.driver.find_elements(
                By.CSS_SELECTOR, '[data-testid="nav-admin"]'
            )
            assert len(admin_navs) == 0, "Member should not see admin nav"
        except Exception:
            login_page.screenshot("member_no_admin_nav")
            raise
        finally:
            login_page.logout()

# ==================================================================
# Core member workflows
# ==================================================================

class TestMemberWorkflows:
    """High-value end-to-end workflows covering real member behavior."""

    def test_member_can_borrow_and_see_book_in_profile(self, login_page, home_page):
        """Member login -> search -> borrow -> verify the borrow in My Profile."""
        from tests.e2e.pages.book_detail_page import BookDetailPage
        from tests.e2e.pages.member_page import MemberPage
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.common.by import By

        login_page.load().login("member1", "Member123!")
        try:
            # Wait for nav-home to appear (indicates successful login and redirect)
            login_page.wait_for_visible(LoginPage.NAV_HOME)
            # Wait for home page content to be fully rendered (books fetched, search section, books grid)
            home_page.wait_for_home_content(timeout=45)
            home_page.search("1984", expected_text="1984")
            home_page.open_book_by_title("1984")

            detail = BookDetailPage(login_page.driver)
            assert detail.is_loaded(), "The selected book should open its detail page"
            assert detail.get_title() == "1984"
            assert detail.get_availability() == "Available"

            detail.click_borrow().wait_for_borrow_button_to_finish()
            # Do not continue until the UI reflects the server-side mutation.
            WebDriverWait(login_page.driver, 15).until(
                lambda d: d.find_elements(By.CSS_SELECTOR, '[data-testid="status-checked-out"]')
            )

            member_page = MemberPage(login_page.driver).navigate()
            # Wait for borrowed row to appear
            WebDriverWait(login_page.driver, 10).until(
                lambda d: len(d.find_elements(By.CSS_SELECTOR, '[data-testid^="borrow-"]')) > 0
            )
            borrowed_rows = member_page.get_borrowed_rows()
            assert borrowed_rows, "A successful borrow should appear in My Profile"

            # Clean up the borrow created by this test. Never assume a database
            # primary key (for example borrow-1); seeded data already contains
            # other borrow records and IDs can differ between runs.
            target_row = next(
                (row for row in borrowed_rows if "1984" in row.text),
                None,
            )
            assert target_row is not None, "The 1984 borrow should appear in My Profile"
            borrow_testid = target_row.get_attribute("data-testid")
            return_button = target_row.find_element(
                By.CSS_SELECTOR, f'[data-testid="btn-return-{borrow_testid.split("-", 1)[1]}"]'
            )
            return_button.click()
            WebDriverWait(login_page.driver, 10).until(
                lambda d: not d.find_elements(
                    By.CSS_SELECTOR, f'[data-testid="{borrow_testid}"]'
                )
            )
        except Exception:
            login_page.screenshot("member_borrow_workflow")
            raise
        finally:
            login_page.logout()

    def test_member_can_reserve_unavailable_book(self, login_page, home_page, admin_page):
        """Admin creates a one-copy book -> member borrows it -> another member reserves it."""
        from tests.e2e.pages.book_detail_page import BookDetailPage
        from tests.e2e.pages.member_page import MemberPage

        isbn = _unique_isbn()
        title = f"E2E Reservation {isbn[-8:]}"

        # Prepare a deterministic unavailable-book scenario through the real admin UI.
        login_page.load().login("admin", "Admin123!")
        try:
            admin_page.navigate()
            admin_page.create_book(title, isbn, copies="1")
        finally:
            login_page.logout()

        # Member 2 takes the only available copy.
        login_page.load().login("member2", "Member123!")
        try:
            home_page.search(title, expected_text=title)
            home_page.open_book_by_title(title)
            detail = BookDetailPage(login_page.driver)
            assert detail.get_availability() == "Available"
            detail.click_borrow().wait_for_borrow_button_to_finish()
        finally:
            login_page.logout()

        # Member 1 should now see the book as unavailable and be able to reserve it.
        login_page.load().login("member1", "Member123!")
        try:
            # The application is a single-page app: navigation is state-based,
            # not URL-based. Do not call driver.get() here because that can race
            # session restoration and leave the catalogue component unmounted.
            # Instead, use the real Browse navigation and then perform a fresh
            # server-side search for the book. The search itself calls GET /books
            # and therefore gives us the post-borrow availability state.
            login_page.wait_for_visible(LoginPage.NAV_HOME, timeout=15)
            browse = WebDriverWait(login_page.driver, 15).until(
                lambda d: next(
                    (el for el in d.find_elements(By.CSS_SELECTOR, '[data-testid="nav-browse"]')
                     if el.is_displayed() and el.is_enabled()),
                    False,
                )
            )
            login_page.driver.execute_script(
                "arguments[0].click();", browse
            )
            WebDriverWait(login_page.driver, 15).until(
                lambda d: d.find_elements(By.CSS_SELECTOR, '[data-testid="home-title"]')
            )
            home_page.search(title, expected_text=title, timeout=45)
            home_page.open_book_by_title(title)
            detail = BookDetailPage(login_page.driver)
            assert detail.get_availability() == "Checked out", (
                "After the only copy is borrowed, the book should be unavailable"
            )
            detail.click_reserve().wait_for_reserve_button_to_finish()

            member_page = MemberPage(login_page.driver).navigate()
            member_page.open_reservations_tab()
            reservations = member_page.get_reservation_rows()
            assert reservations, "A successful reservation should appear in My Profile"
        except Exception:
            login_page.screenshot("member_reservation_workflow")
            raise
        finally:
            login_page.logout()

    def test_admin_can_create_book_and_see_it_in_catalogue(self, login_page, admin_page):
        """Admin login -> create book -> verify the new book appears in the admin catalogue."""
        title = f"E2E Admin Book {_unique_isbn()[-8:]}"
        isbn = _unique_isbn()

        login_page.load().login("admin", "Admin123!")
        try:
            admin_page.navigate()
            row = admin_page.create_book(title, isbn, copies="1")
            assert title in row.text, "The newly created book should appear in the Books table"
            assert isbn in row.text, "The newly created book should display its ISBN"
        except Exception:
            login_page.screenshot("admin_create_book_workflow")
            raise
        finally:
            login_page.logout()


class TestMembershipPlanChange:
    """Membership plan switching through the member profile page."""

    def test_member_can_switch_plan_and_back(self, login_page, home_page):
        """Member switches to another plan, sees the Current badge move, switches back."""
        from tests.e2e.pages.member_page import MemberPage
        from selenium.webdriver.support.ui import WebDriverWait

        login_page.load().login("member3", "Member123!")
        member_page = None
        original_plan = None
        try:
            member_page = MemberPage(login_page.driver).navigate()

            # All seeded plans render as comparable cards.
            WebDriverWait(login_page.driver, 15).until(
                lambda d: len(member_page.get_plan_ids()) >= 3
            )
            plan_ids = member_page.get_plan_ids()
            assert len(plan_ids) >= 3, "The plans section should list every seeded plan"

            original_plan = member_page.get_current_plan_id()
            assert original_plan is not None, "The current plan should carry the Current badge"

            target = next(pid for pid in plan_ids if pid != original_plan)
            member_page.switch_to_plan(target)
            member_page.wait_for_current_plan(target)

            # The previous plan now offers a way back.
            member_page.wait_for_clickable(
                (f'[data-testid="btn-switch-plan-{original_plan}"]',)
            )

            # Switch back so repeated runs start from the same state.
            member_page.switch_to_plan(original_plan)
            member_page.wait_for_current_plan(original_plan)
        except Exception:
            login_page.screenshot("member_plan_change_workflow")
            raise
        finally:
            # Restore the original plan if a mid-test failure left it changed.
            if member_page is not None and original_plan is not None:
                try:
                    if member_page.get_current_plan_id() != original_plan:
                        member_page.switch_to_plan(original_plan)
                        member_page.wait_for_current_plan(original_plan, timeout=8)
                except Exception:
                    pass
            login_page.logout()
