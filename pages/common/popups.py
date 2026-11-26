from pathlib import Path

from playwright.sync_api import Page

from pages.base_page import BasePage
from utils.config_reader import load_selectors

COMMON_DIR = Path(__file__).resolve().parent
SELECTORS_FILE = COMMON_DIR / "common_selectors.yaml"


class Popups(BasePage):
    """Closes Salesforce pop-ups that can appear at any moment and block the page."""

    def __init__(self, page: Page):
        super().__init__(page)
        config = load_selectors(SELECTORS_FILE, "popups")
        self.trial_ended_dialog = config["trial_ended_dialog"]
        self.trial_ended_close = config["trial_ended_close"]
        self.aura_error_dialog = config["aura_error_dialog"]
        self.aura_error_close = config["aura_error_close"]
        self.open_form_cancel = config["open_form_cancel"]

    def close_trial_ended(self) -> None:
        self.locator(self.trial_ended_close).click()

    def close_aura_error(self) -> None:
        self.locator(self.aura_error_close).click()

    def auto_close(self) -> "Popups":
        """Whenever one of these pop-ups shows up, close it before the next action (click, fill, ...).

        Playwright checks for the pop-ups before each action and runs the handler,
        so no test needs to know about them.
        """
        self.page.add_locator_handler(self.locator(self.trial_ended_dialog), self.close_trial_ended)
        self.page.add_locator_handler(self.locator(self.aura_error_dialog), self.close_aura_error)
        return self

    def close_open_form(self) -> None:
        """Cancel a New/Edit record pop-up a failed test left open, so it can't block the next test."""
        cancel = self.locator(self.open_form_cancel)
        if cancel.count() and cancel.is_visible():
            cancel.click()
            cancel.wait_for(state="hidden", timeout=10_000)
