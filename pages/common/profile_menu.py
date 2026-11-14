from pathlib import Path

from playwright.sync_api import Page

from pages.base_page import BasePage
from utils.config_reader import load_selectors

COMMON_DIR = Path(__file__).resolve().parent
SELECTORS_FILE = COMMON_DIR / "common_selectors.yaml"


class ProfileMenu(BasePage):
    """Reusable component for the user avatar / profile menu shown on every logged-in page."""

    def __init__(self, page: Page):
        super().__init__(page)
        config = load_selectors(SELECTORS_FILE, "profile_menu")
        self.view_profile = config["view_profile"]

    def open(self) -> "ProfileMenu":
        self.click_if_enabled(self.view_profile)
        return self
