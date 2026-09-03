"""Page Object for the member profile and borrowing/reservation views."""
from selenium.webdriver.common.by import By
from .base_page import BasePage


class MemberPage(BasePage):
    """Page Object for the member profile page."""

    NAV_PROFILE = ('[data-testid="nav-profile"]',)
    MEMBER_PROFILE_PAGE = ('[data-testid="member-profile-page"]',)
    BORROWED_LIST = ('[data-testid="borrowed-list"]',)
    RESERVATIONS_LIST = ('[data-testid="reservations-list"]',)
    TAB_RESERVATIONS = ('[data-testid="tab-reservations"]',)

    def navigate(self, timeout=20):
        """Open the member profile through the real UI navigation.

        The header uses a React state transition rather than a URL route, so
        following an href is not valid here. Re-resolve the visible nav button
        and trigger its DOM click; then wait for the actual profile test id.
        """
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait

        def profile_page_visible(driver):
            return bool(driver.find_elements(By.CSS_SELECTOR, self.MEMBER_PROFILE_PAGE[0]))

        def click_profile(driver):
            buttons = driver.find_elements(By.CSS_SELECTOR, self.NAV_PROFILE[0])
            for button in buttons:
                try:
                    if button.is_displayed() and button.is_enabled():
                        driver.execute_script(
                            "arguments[0].scrollIntoView({block:'center'}); arguments[0].click();",
                            button,
                        )
                        return True
                except Exception:
                    continue
            return False

        # First attempt: real React button click. If React has just re-rendered
        # the header, the next poll resolves the new button automatically.
        WebDriverWait(self.driver, timeout, poll_frequency=0.25).until(click_profile)
        try:
            WebDriverWait(self.driver, 8, poll_frequency=0.25).until(profile_page_visible)
        except Exception:
            # One controlled retry handles a header re-render during the click.
            WebDriverWait(self.driver, timeout, poll_frequency=0.25).until(click_profile)
            WebDriverWait(self.driver, timeout, poll_frequency=0.25).until(profile_page_visible)
        # Profile rows mount with entrance animations; go quiet so they finish
        # before callers poll row text (see BasePage.settle).
        self.settle()
        return self

    def get_borrowed_rows(self):
        """Return currently displayed borrowed-book rows."""
        # Use a more specific selector to match only borrow-{id} rows, not borrow-progress or borrow-status-{id}
        all_elements = self.driver.find_elements(By.CSS_SELECTOR, '[data-testid^="borrow-"]')
        # Filter to only keep elements where testid matches "borrow-{number}" pattern
        borrowed_rows = []
        for elem in all_elements:
            testid = elem.get_attribute('data-testid')
            if testid and testid.startswith('borrow-'):
                # Check if it's a borrow row (borrow-{id}) and not progress/status
                suffix = testid[7:]  # Remove "borrow-"
                if suffix.isdigit():  # Only digits = borrow row
                    borrowed_rows.append(elem)
        return borrowed_rows

    def get_reservation_rows(self):
        """Return currently displayed reservation rows."""
        return self.driver.find_elements("css selector", '[data-testid^="reservation-"]')

    def open_reservations_tab(self):
        """Switch to the reservations tab and wait for its state to render."""
        self.wait_for_clickable(self.TAB_RESERVATIONS).click()
        return self

    # -- Membership plans -------------------------------------------------

    def get_plan_ids(self):
        """Return the ids of the rendered membership plan cards."""
        ids = []
        for card in self.driver.find_elements(By.CSS_SELECTOR, '[data-testid^="plan-"]'):
            testid = card.get_attribute("data-testid") or ""
            suffix = testid[5:]
            if testid.startswith("plan-") and suffix.isdigit():
                ids.append(int(suffix))
        return ids

    def get_current_plan_id(self):
        """Return the plan id whose card carries the Current badge, or None."""
        for card in self.driver.find_elements(By.CSS_SELECTOR, '[data-testid^="plan-"]'):
            badges = card.find_elements(
                By.XPATH, ".//span[normalize-space()='Current']"
            )
            if badges:
                testid = card.get_attribute("data-testid") or ""
                suffix = testid[5:]
                if testid.startswith("plan-") and suffix.isdigit():
                    return int(suffix)
        return None

    def switch_to_plan(self, plan_id):
        """Click the switch button on the given plan card."""
        button = self.wait_for_clickable((f'[data-testid="btn-switch-plan-{plan_id}"]',))
        self.driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'}); arguments[0].click();",
            button,
        )
        return self

    def wait_for_current_plan(self, plan_id, timeout=15):
        """Wait until the given plan card carries the Current badge."""
        from selenium.webdriver.support.ui import WebDriverWait

        WebDriverWait(self.driver, timeout, poll_frequency=0.25).until(
            lambda d: self.get_current_plan_id() == plan_id
        )
        return self
