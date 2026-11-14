from pathlib import Path

from playwright.sync_api import Page

from pages.base_page import BasePage
from utils.config_reader import load_selectors

COMMON_DIR = Path(__file__).resolve().parent
SELECTORS_FILE = COMMON_DIR / "common_selectors.yaml"


class QuickSettings(BasePage):
    """Reusable component for the 'Quick Settings' gear icon in the header."""

    def __init__(self, page: Page):
        super().__init__(page)
        config = load_selectors(SELECTORS_FILE, "quick_settings")
        self.quick_settings_button = config["quick_settings_button"]
        self.advanced_setup_link = config["advanced_setup_link"]

    def open(self) -> "QuickSettings":
        self.click_if_enabled(self.quick_settings_button)
        return self

    def close(self) -> "QuickSettings":
        # The gear icon toggles its panel.
        self.click_if_enabled(self.quick_settings_button)
        return self

    def open_advanced_setup(self) -> Page:
        """Click 'Open Advanced Setup' and return the new Setup tab it opens."""
        with self.page.context.expect_page() as new_tab:
            self.click_if_enabled(self.advanced_setup_link)
        setup_tab = new_tab.value
        setup_tab.wait_for_load_state("domcontentloaded")
        return setup_tab
