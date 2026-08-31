"""LoginPage Page Object.
Wraps Selenium operations for the login form.
"""
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from .base_page import BasePage


class LoginPage(BasePage):
    """Page Object for the Login page."""

    URL = "http://localhost:3000"

    FORM = ('[data-testid="login-form"]',)
    USERNAME_INPUT = ('[data-testid="login-username"]',)
    PASSWORD_INPUT = ('[data-testid="login-password"]',)
    SUBMIT_BUTTON = ('[data-testid="login-submit"]',)
    ERROR = ('[data-testid="login-error"]',)
    NAV_HOME = ('[data-testid="nav-home"]',)
    LOGOUT_BUTTON = ('[data-testid="btn-logout"]',)

    def load(self):
        """Navigate to the login page and wait for the form."""
        self.driver.get(self.URL)
        self.wait_for_visible(self.FORM)
        return self

    def login(self, username, password):
        """Fill credentials, submit, and wait for authenticated navigation."""
        self.wait_for_visible(self.USERNAME_INPUT).send_keys(username)
        self.wait_for_visible(self.PASSWORD_INPUT).send_keys(password)
        self.wait_for_clickable(self.SUBMIT_BUTTON).click()

        WebDriverWait(self.driver, 10).until(
            lambda d: not d.find_elements(By.CSS_SELECTOR, self.FORM[0])
            or d.find_elements(By.CSS_SELECTOR, self.NAV_HOME[0])
        )
        return self

    def get_error_text(self):
        """Return the text of the error message, or empty string if not shown."""
        if self.is_visible(self.ERROR, timeout=5):
            return self.find(self.ERROR).text
        return ""

    def is_loaded(self):
        """Return True if the login form is visible."""
        return self.is_visible(self.FORM)

    def logout(self):
        """Log out reliably, including when the current page is mid-animation.

        The app stores authentication in localStorage. If the UI logout click
        is intercepted or its React transition is interrupted, simply navigating
        to the root page is not enough because the stored token restores the
        authenticated session. The fallback therefore clears the same token the
        application uses before reloading the login page.
        """
        # Close any open modal first.
        try:
            modals = self.driver.find_elements(By.CSS_SELECTOR, '[data-testid="modal"]')
            for modal in modals:
                if modal.is_displayed():
                    close_btn = modal.find_elements(
                        By.CSS_SELECTOR, '[data-testid="modal-close"]'
                    )
                    if close_btn:
                        close_btn[0].click()
                    else:
                        self.driver.execute_script(
                            "arguments[0].click();", modal
                        )
                    break
        except Exception:
            pass

        buttons = self.driver.find_elements(By.CSS_SELECTOR, self.LOGOUT_BUTTON[0])
        if buttons:
            try:
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center'});", buttons[0]
                )
                try:
                    buttons[0].click()
                except Exception:
                    self.driver.execute_script("arguments[0].click();", buttons[0])

                # Normal application logout clears localStorage and causes the
                # login form to render. Give that path a chance first.
                WebDriverWait(self.driver, 5).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, self.FORM[0]))
                )
                return self
            except Exception:
                pass

        # Deterministic fallback: clear the app's persisted token, then reload.
        # This is preferable to repeatedly waiting for a login form that cannot
        # appear while localStorage still contains a valid token.
        try:
            self.driver.execute_script(
                "window.localStorage.removeItem('library_token'); window.sessionStorage.clear();"
            )
        except Exception:
            pass
        self.driver.get(self.URL)
        self.wait_for_visible(self.FORM, timeout=10)
        return self
