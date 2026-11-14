from pathlib import Path

from playwright.sync_api import Page

from pages.base_page import BasePage
from pages.common import ProfileMenu
from utils.config_reader import load_selectors

LOGOUT_DIR = Path(__file__).resolve().parent
SELECTORS_FILE = LOGOUT_DIR / "logout_selectors.yaml"


class LogoutPage(BasePage):
    """Page object for logging out via the profile menu."""

    def __init__(self, page: Page):
        super().__init__(page)
        config = load_selectors(SELECTORS_FILE, "logout")
        self.logout_link = config["logout_link"]
        self.profile_menu = ProfileMenu(page)

    def click_logout(self) -> "LogoutPage":
        # click_if_enabled waits for the link to become visible before clicking.
        self.click_if_enabled(self.logout_link)
        return self

    def logout(self) -> None:
        """View profile -> wait for Log Out -> click it."""
        self.profile_menu.open()
        self.click_logout()
