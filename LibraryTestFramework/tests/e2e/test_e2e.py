"""
Selenium E2E tests for the Library Management System frontend.

These tests require:
  1. The backend running at http://localhost:8000
  2. The frontend running at http://localhost:3000
  3. Chrome browser installed

Run with:  pytest tests/e2e/test_e2e.py -m e2e
"""
import os
import re
import shutil
from pathlib import Path
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

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


def _return_member_active_borrows(username, password, keep_copy_ids=()):
    """Return a member's active loans via the backend API.

    The reserve scenario intentionally leaves member2 holding the one-copy
    book while member1 reserves it. On a reused database those loans
    accumulate, and once the member reaches the plan's max_books limit the
    borrow API silently fails (the UI swallows the rejection) — so tests
    clear leftovers. member2 holds no seeded loans; member1's seeded Clean
    Code loan (copy 1) is preserved through keep_copy_ids.
    """
    import json as _json
    import urllib.parse
    import urllib.request

    base = "http://127.0.0.1:8000"

    def _call(path, data=None, token=None, method=None):
        # A system proxy can intercept localhost calls from urllib; bypass it.
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        request = urllib.request.Request(
            f"{base}{path}",
            data=urllib.parse.urlencode(data).encode() if data else None,
            method=method or ("POST" if data else "GET"),
        )
        if data:
            request.add_header("Content-Type", "application/x-www-form-urlencoded")
        if token:
            request.add_header("Authorization", f"Bearer {token}")
        with opener.open(request, timeout=15) as response:
            return _json.loads(response.read().decode())

    token = _call("/auth/login", data={"username": username, "password": password})[
        "access_token"
    ]
    summary = _call("/members/me/summary", token=token)
    for borrow in summary.get("active_borrows", []):
        if borrow["copy_id"] in keep_copy_ids:
            continue
        try:
            _call(f"/return/{borrow['id']}", token=token, method="POST")
        except OSError:
            pass  # cleanup is best-effort; the borrow may already be gone


def _active_borrow_ids(username, password):
    """Return the set of the member's active borrow ids via the backend API.

    The profile UI lists loans as "Borrow #id (Copy #id)" without the book
    title, so tests snapshot loan ids before a borrow and recognise the new
    profile row by the id that appears afterwards.
    """
    import json as _json
    import urllib.parse
    import urllib.request

    base = "http://127.0.0.1:8000"

    def _call(path, data=None, token=None, method=None):
        # A system proxy can intercept localhost calls from urllib; bypass it.
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        request = urllib.request.Request(
            f"{base}{path}",
            data=urllib.parse.urlencode(data).encode() if data else None,
            method=method or ("POST" if data else "GET"),
        )
        if data:
            request.add_header("Content-Type", "application/x-www-form-urlencoded")
        if token:
            request.add_header("Authorization", f"Bearer {token}")
        with opener.open(request, timeout=15) as response:
            return _json.loads(response.read().decode())

    token = _call("/auth/login", data={"username": username, "password": password})[
        "access_token"
    ]
    summary = _call("/members/me/summary", token=token)
    return {borrow["id"] for borrow in summary.get("active_borrows", [])}


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
    a locally installed driver. CHROME_BINARY pins the browser executable —
    when both are set, Selenium Manager is bypassed entirely, which is how
    CI guarantees the Chrome/chromedriver versions can never drift apart
    (mismatched pairs silently drop keystrokes and clicks).
    """
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    options = Options()
    chrome_binary = os.getenv("CHROME_BINARY")
    if chrome_binary:
        if not Path(chrome_binary).is_file():
            raise pytest.UsageError(
                f"CHROME_BINARY is set but the file does not exist: {chrome_binary}"
            )
        options.binary_location = chrome_binary
    options.add_argument("--headless=new")
    # Reduced motion keeps the compositor idle between interactions. Chrome
    # headless can silently drop trusted input (keystrokes, clicks) while
    # infinite animations keep the frame sink busy — the app honours the
    # prefers-reduced-motion media query via framer-motion's MotionConfig.
    options.add_argument("--force-prefers-reduced-motion")
    # Incognito is what actually stops the input loss: in a normal profile,
    # right after a successful password login, Chrome shows an invisible
    # headless bubble (save-password flow) that swallows all raw keyboard and
    # mouse input for the tab. Keystrokes and clicks then vanish while the
    # page stays scriptable, survives navigation, and is not fixed by
    # credentials_enable_service prefs or reduced motion — but incognito
    # never shows the bubble (verified: input alive indefinitely).
    options.add_argument("--incognito")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1280,720")
    options.add_argument("--disable-gpu")
    # Browser console + network logs feed the input-delivery diagnostics.
    options.set_capability("goog:loggingPrefs", {"browser": "ALL", "performance": "ALL"})

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
        """Member login -> borrow -> verify the borrow in My Profile."""
        from tests.e2e.pages.book_detail_page import BookDetailPage
        from tests.e2e.pages.member_page import MemberPage

        login_page.load().login("member1", "Member123!")
        try:
            # Wait for nav-home to appear (indicates successful login and redirect)
            login_page.wait_for_visible(LoginPage.NAV_HOME)
            # Wait for home page content to be fully rendered (books fetched, search section, books grid)
            home_page.wait_for_home_content(timeout=45)
            # 1984 is in the seeded catalogue and typed search has its own
            # test (test_search_books), so the card is opened straight from
            # the unfiltered catalogue.
            home_page.open_book_by_title("1984")

            detail = BookDetailPage(login_page.driver)
            assert detail.is_loaded(), "The selected book should open its detail page"
            assert detail.get_title() == "1984"
            assert detail.get_availability() == "Available"

            # Do not continue until the UI reflects the server-side mutation.
            # Borrowing one copy of a multi-copy title keeps the badge on
            # "Available" — the observable change is the remaining-copies
            # count dropping (2 -> 1 for the seeded 1984). Capture the count
            # before clicking: it reads the post-borrow value afterwards.
            copies_before = detail.get_copies_available()
            # Snapshot the member's loan ids through the API so the new profile
            # row can be recognised by id even though the UI shows no titles.
            borrow_ids_before = _active_borrow_ids("member1", "Member123!")
            detail.click_borrow().wait_for_borrow_button_to_finish()
            detail.wait_for_copies_to_change(copies_before)

            member_page = MemberPage(login_page.driver).navigate()
            # Profile borrow rows render as "Borrow #id (Copy #id)" without the
            # book title, so the new loan is identified by its borrow id: the
            # row that appears after the borrow and was not there before. The
            # borrow itself is tied to 1984 by the copies-drop check above.
            def _new_borrow_row(d):
                for row in d.find_elements(By.CSS_SELECTOR, '[data-testid^="borrow-"]'):
                    match = re.fullmatch(r"borrow-(\d+)", row.get_attribute("data-testid") or "")
                    if match and int(match.group(1)) not in borrow_ids_before:
                        return row
                return False

            target_row = WebDriverWait(login_page.driver, 15).until(_new_borrow_row)
            # Clean up the borrow created by this test. Never assume a database
            # primary key (for example borrow-1); seeded data already contains
            # other borrow records and IDs can differ between runs.
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
            # A failed run must not leave the borrowed copy behind: the next
            # run would then see "Checked out" before even borrowing. The
            # seeded Clean Code loan (copy 1) is part of the expected state
            # and is kept.
            try:
                _return_member_active_borrows(
                    "member1", "Member123!", keep_copy_ids={1}
                )
            except Exception:
                pass

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
        # Clear loans left by earlier failed runs first: the Student plan
        # allows 3 books, and a full card means the borrow API rejects the
        # new loan (the UI swallows the error and the book stays Available).
        _return_member_active_borrows("member2", "Member123!")
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


# ==================================================================
# Signup + admin approval workflow
# ==================================================================

class TestSignupApprovalWorkflow:
    """Self-registration stays pending until an administrator approves it."""

    def test_signup_requires_approval_then_member_can_sign_in(self, login_page, admin_page):
        """Sign up -> login refused while pending -> admin approves -> login works."""
        import uuid

        from tests.e2e.pages.login_page import LoginPage

        suffix = str(uuid.uuid4().int)[-8:]
        username = f"e2euser{suffix}"
        email = f"e2euser{suffix}@test.com"
        full_name = f"E2E Signup {suffix}"
        password = "E2eSignup123!"

        # 1. Self-registration from the public auth page.
        login_page.load().open_signup().signup(full_name, username, email, password)
        try:
            # 2. Back on the sign-in form, the pending account must be refused.
            login_page.back_to_login()
            login_page.type_text(LoginPage.USERNAME_INPUT, username)
            login_page.type_text(LoginPage.PASSWORD_INPUT, password)
            login_page.wait_for_clickable(LoginPage.SUBMIT_BUTTON).click()
            assert login_page.is_visible(LoginPage.ERROR, timeout=10), (
                "A pending signup must not be able to sign in"
            )
            assert "pending" in login_page.get_error_text().lower()
        except Exception:
            login_page.screenshot("signup_pending_login_rejected")
            raise

        # 3. The admin finds the pending signup in the Members tab and approves it.
        login_page.load().login("admin", "Admin123!")
        try:
            admin_page.navigate().open_members_tab()
            admin_page.approve_member(email)
        except Exception:
            login_page.screenshot("signup_admin_approve")
            raise
        finally:
            login_page.logout()

        # 4. The approved member can now sign in.
        login_page.load().login(username, password)
        try:
            login_page.wait_for_visible(LoginPage.NAV_HOME, timeout=15)
        except Exception:
            login_page.screenshot("signup_approved_login")
            raise
        finally:
            login_page.logout()
