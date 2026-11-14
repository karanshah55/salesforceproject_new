from pathlib import Path

from playwright.sync_api import Locator, Page

from pages.base_page import BasePage
from utils.config_reader import load_selectors, load_values

SETUP_DIR = Path(__file__).resolve().parent
SELECTORS_FILE = SETUP_DIR / "setup_selectors.yaml"
VALUES_FILE = SETUP_DIR / "setup_values.json"


def load_setup_values() -> dict:
    return load_values(VALUES_FILE)


class SetupPage(BasePage):
    """Page object for the Setup tab: find and open Setup pages from the left-hand menu."""

    def __init__(self, page: Page):
        super().__init__(page)
        config = load_selectors(SELECTORS_FILE, "setup")
        self.quick_find_input = config["quick_find"]
        self.menu_result = config["menu_result"]
        self.page_heading = config["page_heading"]

    def quick_find(self, text: str) -> "SetupPage":
        """Type into 'Quick Find' - the menu filters as each key is typed."""
        self.fill(self.quick_find_input, text)
        return self

    def open_result(self, name: str) -> "SetupPage":
        self.click_if_enabled(self.menu_result.format(name=name))
        return self

    def open_setup_page(self, name: str) -> "SetupPage":
        """Quick Find -> click the matching menu entry, e.g. 'App Manager'."""
        return self.quick_find(name).open_result(name)

    def heading(self, text: str) -> Locator:
        return self.locator(self.page_heading.format(heading=text))
