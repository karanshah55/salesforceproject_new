from pathlib import Path

from playwright.sync_api import Page

from pages.base_page import BasePage
from utils.config_reader import load_selectors, load_values

CASE_DIR = Path(__file__).resolve().parent
SELECTORS_FILE = CASE_DIR / "case_selectors.yaml"
VALUES_FILE = CASE_DIR / "case_values.json"

# Matches a saved Case record page, e.g. /lightning/r/Case/500QH00000Abc12YAB/view
CASE_RECORD_URL = r"/lightning/r/Case/500\w+/view"


def load_case_values() -> dict:
    return load_values(VALUES_FILE)


class CasePage(BasePage):
    """Page object for Cases in the Service app: create a Case."""

    def __init__(self, page: Page):
        super().__init__(page)
        app_menu = load_selectors(SELECTORS_FILE, "app_menu")
        self.service_app = app_menu["service_app"]

        cases = load_selectors(SELECTORS_FILE, "cases")
        self.cases_tab = cases["cases_tab"]
        self.new_button = cases["new_button"]
        self.search_input = cases["search_input"]

        form = load_selectors(SELECTORS_FILE, "case_form")
        self.modal_title = form["modal_title"]
        self.status = form["status"]
        self.case_origin = form["case_origin"]
        self.priority = form["priority"]
        self.picklist_option = form["picklist_option"]
        self.contact_name = form["contact_name"]
        self.contact_option = form["contact_option"]
        self.account_name = form["account_name"]
        self.account_option = form["account_option"]
        self.subject = form["subject"]
        self.description = form["description"]
        self.save_button = form["save_button"]

        created = load_selectors(SELECTORS_FILE, "created_case")
        self.created_toast = created["created_toast"]

    # --- Navigation -----------------------------------------------------------------

    def open_service_app(self) -> "CasePage":
        """Left-hand menu -> Service."""
        self.click_if_enabled(self.service_app)
        return self

    def open_cases_tab(self) -> "CasePage":
        self.click_if_enabled(self.cases_tab)
        self.wait_for_visible(self.search_input)
        return self

    # --- Case form ------------------------------------------------------------------

    def select_picklist(self, dropdown: str, value: str) -> "CasePage":
        # Lightning dropdown: open it, then click the matching option.
        self.click_if_enabled(dropdown)
        self.click_if_enabled(self.picklist_option.format(value=value))
        return self

    def select_status(self, status: str) -> "CasePage":
        return self.select_picklist(self.status, status)

    def select_case_origin(self, case_origin: str) -> "CasePage":
        return self.select_picklist(self.case_origin, case_origin)

    def select_priority(self, priority: str) -> "CasePage":
        return self.select_picklist(self.priority, priority)

    def select_contact(self, contact_name: str) -> "CasePage":
        # Lookup field: typing searches Contacts, then click the matching result.
        self.fill(self.contact_name, contact_name)
        self.click_if_enabled(self.contact_option.format(value=contact_name))
        return self

    def select_account(self, account_name: str) -> "CasePage":
        # Lookup field: typing searches Accounts, then click the matching result.
        self.fill(self.account_name, account_name)
        self.click_if_enabled(self.account_option.format(value=account_name))
        return self

    def enter_subject(self, subject: str) -> "CasePage":
        self.fill(self.subject, subject)
        return self

    def enter_description(self, description: str) -> "CasePage":
        self.fill(self.description, description)
        return self

    def fill_case_form(self, details: dict) -> "CasePage":
        self.select_status(details["status"])
        self.select_case_origin(details["case_origin"])
        self.select_priority(details["priority"])
        self.select_contact(details["contact_name"])
        self.select_account(details["account_name"])
        self.enter_subject(details["subject"])
        self.enter_description(details["description"])
        return self

    def click_save(self) -> "CasePage":
        self.click_if_enabled(self.save_button)
        return self

    # --- Create ---------------------------------------------------------------------

    def click_new(self) -> "CasePage":
        self.click_if_enabled(self.new_button)
        self.wait_for_visible(self.modal_title)
        return self

    def create_case(self, details: dict) -> None:
        """Service app -> Cases tab -> New -> fill the pop-up -> Save."""
        self.open_service_app()
        self.open_cases_tab()
        self.screenshot("cases_tab")

        self.click_new()
        self.screenshot("new_case_form")

        self.fill_case_form(details)
        # The pop-up scrolls inside itself, so capture both halves of the filled form.
        self.locator(self.status).scroll_into_view_if_needed()
        self.screenshot("form_filled_case_contact")
        self.locator(self.description).scroll_into_view_if_needed()
        self.screenshot("form_filled_description")
        self.click_save()
