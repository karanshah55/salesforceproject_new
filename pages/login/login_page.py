import sys
from pathlib import Path

from playwright.sync_api import Page

from pages.base_page import BasePage
from utils.config_reader import load_selectors, load_values
from utils.device_state import save_device_state

LOGIN_DIR = Path(__file__).resolve().parent
SELECTORS_FILE = LOGIN_DIR / "login_selectors.yaml"
VALUES_FILE = LOGIN_DIR / "login_values.json"

VERIFICATION_URL_PART = "/_ui/identity/verification/"
LOGGED_IN_URL_PART = "/lightning/"
VERIFICATION_TIMEOUT = 300_000  # ms - time allowed to type the emailed code by hand


def load_login_values() -> dict:
    return load_values(VALUES_FILE)


class LoginPage(BasePage):
    """Page object for the Salesforce login page."""

    def __init__(self, page: Page):
        super().__init__(page)
        config = load_selectors(SELECTORS_FILE, "login")
        self.url = config["url"]
        self.username_input = config["username"]
        self.password_input = config["password"]
        self.login_button = config["login_button"]

    def navigate(self) -> "LoginPage":
        self.open(self.url)
        return self

    def enter_username(self, username: str) -> "LoginPage":
        self.wait_for_visible(self.username_input)
        self.fill(self.username_input, username)
        return self

    def enter_password(self, password: str) -> "LoginPage":
        self.wait_for_visible(self.password_input)
        self.fill(self.password_input, password)
        return self

    def click_login(self) -> "LoginPage":
        self.click_if_enabled(self.login_button)
        return self

    def login(self, username: str, password: str) -> None:
        """Username -> Login, then password -> Login, as per the use case."""
        self.enter_username(username).click_login()
        self.enter_password(password).click_login()
        self.wait_for_login_to_finish()
        save_device_state(self.page.context)

    def wait_for_login_to_finish(self) -> None:
        """Wait for the app to load, pausing for a manual code if Salesforce asks to verify."""
        self.page.wait_for_url(
            lambda url: VERIFICATION_URL_PART in url or LOGGED_IN_URL_PART in url,
            wait_until="domcontentloaded",
            timeout=self.DEFAULT_TIMEOUT,
        )
        if VERIFICATION_URL_PART in self.page.url:
            # Only needed once: the saved device state lets later runs skip this screen.
            try:
                print(
                    "\n>>> Salesforce sent a verification code to your email. Enter it in the "
                    "browser and click Verify (keep 'Don't ask again' ticked).",
                    file=sys.__stderr__,
                    flush=True,
                )
            except (OSError, AttributeError):
                # No usable console (e.g. pytest capture on Windows) - just keep waiting.
                pass
            self.page.wait_for_url(
                lambda url: LOGGED_IN_URL_PART in url,
                wait_until="domcontentloaded",
                timeout=VERIFICATION_TIMEOUT,
            )
