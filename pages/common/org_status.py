from pathlib import Path

from playwright.sync_api import Page

from pages.base_page import BasePage
from utils.config_reader import load_selectors

COMMON_DIR = Path(__file__).resolve().parent
SELECTORS_FILE = COMMON_DIR / "common_selectors.yaml"


class OrgStatus(BasePage):
    """What the logged-in org allows, read from the page."""

    def __init__(self, page: Page):
        super().__init__(page)
        config = load_selectors(SELECTORS_FILE, "org_status")
        self.read_only_banner = config["read_only_banner"]

    def is_read_only(self) -> bool:
        """True when the 'Your trial has ended.' banner shows: Salesforce blocks add, edit and delete."""
        return self.locator(self.read_only_banner).first.is_visible()
