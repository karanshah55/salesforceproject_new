import warnings
from pathlib import Path

from playwright.sync_api import Locator, Page
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from pages.base_page import BasePage
from utils.config_reader import load_selectors, load_values

LEADS_DIR = Path(__file__).resolve().parent
SELECTORS_FILE = LEADS_DIR / "leads_selectors.yaml"
VALUES_FILE = LEADS_DIR / "lead_values.json"


def load_lead_values() -> dict:
    return load_values(VALUES_FILE)


class LeadsPage(BasePage):
    """Page object for the Leads tab: create, read, update and delete Leads."""

    def __init__(self, page: Page):
        super().__init__(page)
        leads = load_selectors(SELECTORS_FILE, "leads")
        self.leads_tab = leads["leads_tab"]
        self.new_button = leads["new_button"]
        self.search_input = leads["search_input"]
        self.column_headers = leads["column_headers"]
        self.row_actions = leads["row_actions"]
        self.row_name_link = leads["row_name_link"]
        self.record_row = leads["record_row"]

        form = load_selectors(SELECTORS_FILE, "lead_form")
        self.salutation = form["salutation"]
        self.salutation_option = form["salutation_option"]
        self.first_name = form["first_name"]
        self.last_name = form["last_name"]
        self.company = form["company"]
        self.save_button = form["save_button"]

        edit = load_selectors(SELECTORS_FILE, "edit_lead")
        self.edit_action = edit["edit_action"]

        delete = load_selectors(SELECTORS_FILE, "delete_lead")
        self.delete_action = delete["delete_action"]
        self.confirm_delete = delete["confirm_delete"]
        self.deleted_toast = delete["deleted_toast"]

    @staticmethod
    def full_name(details: dict) -> str:
        """Name as Salesforce shows it in the list view, e.g. 'John Smith'."""
        return f"{details['first_name']} {details['last_name']}"

    # --- Navigation / list view -----------------------------------------------------

    def open_leads_tab(self) -> "LeadsPage":
        self.click_if_enabled(self.leads_tab)
        # Wait until the list view has rendered before acting on it (New, search, rows).
        self.locator(self.column_headers).filter(visible=True).first.wait_for(
            state="visible", timeout=self.DEFAULT_TIMEOUT
        )
        self.pause()
        return self

    def search(self, text: str) -> "LeadsPage":
        """Type into 'Search this list...' and press Enter to filter the list."""
        self.fill(self.search_input, text)
        self.locator(self.search_input).press("Enter")
        self.pause()
        return self

    def open_row_actions(self, name: str) -> "LeadsPage":
        self.click_if_enabled(self.row_actions.format(name=name))
        return self

    def row_record_id(self, name: str) -> str:
        """Salesforce id of the first visible row with this name (the row the actions act on)."""
        return self.wait_for_visible(self.row_name_link.format(name=name)).get_attribute("data-recordid")

    def record_row_locator(self, record_id: str) -> Locator:
        """Visible list row(s) for one record - empty once that record is deleted."""
        return self.locator(self.record_row.format(record_id=record_id))

    # --- Lead form (shared by Create and Update) ------------------------------------

    def select_salutation(self, salutation: str) -> "LeadsPage":
        # Lightning dropdown: open it, then click the matching option.
        self.click_if_enabled(self.salutation)
        self.click_if_enabled(self.salutation_option.format(value=salutation))
        return self

    def enter_first_name(self, first_name: str) -> "LeadsPage":
        self.fill(self.first_name, first_name)
        return self

    def enter_last_name(self, last_name: str) -> "LeadsPage":
        self.fill(self.last_name, last_name)
        return self

    def enter_company(self, company: str) -> "LeadsPage":
        self.fill(self.company, company)
        return self

    def fill_lead_form(self, details: dict) -> "LeadsPage":
        self.select_salutation(details["Salutation"])
        self.enter_first_name(details["first_name"])
        self.enter_last_name(details["last_name"])
        self.enter_company(details["company"])
        return self

    def click_save(self) -> "LeadsPage":
        self.click_if_enabled(self.save_button)
        return self

    # --- Create ---------------------------------------------------------------------

    def click_new(self, attempts: int = 3) -> "LeadsPage":
        """Click New and wait for the New Lead pop-up.

        Right after the Leads tab opens, Lightning is still re-rendering the list view, and a
        click on New in that window is swallowed (the button takes focus, no pop-up opens).
        So wait for the pop-up and click again if it did not appear.
        """
        for attempt in range(1, attempts + 1):
            self.click_if_enabled(self.new_button)
            try:
                self.wait_for_visible(self.first_name, timeout=10_000)
                return self
            except PlaywrightTimeoutError:
                if attempt == attempts:
                    raise
                warnings.warn(f"New Lead pop-up did not open on click {attempt}; clicking New again")
        return self

    def create_lead(self, details: dict) -> None:
        """Leads tab -> New -> fill the pop-up -> Save."""
        self.open_leads_tab().click_new()
        self.fill_lead_form(details)
        self.click_save()

    # --- Update ---------------------------------------------------------------------

    def click_edit(self) -> "LeadsPage":
        self.click_if_enabled(self.edit_action)
        return self

    def edit_lead(self, details: dict, new_last_name: str) -> None:
        """Leads tab -> search by name -> row actions -> Edit -> change last name -> Save."""
        name = self.full_name(details)
        self.open_leads_tab().search(name)
        self.open_row_actions(name).click_edit()
        self.enter_last_name(new_last_name)
        self.click_save()

    # --- Delete ---------------------------------------------------------------------

    def click_delete(self) -> "LeadsPage":
        self.click_if_enabled(self.delete_action)
        return self

    def click_confirm_delete(self) -> "LeadsPage":
        self.click_if_enabled(self.confirm_delete)
        return self

    def delete_lead(self, details: dict) -> str:
        """Leads tab -> search by name -> row actions -> Delete -> confirm.

        Returns the deleted lead's record id, so the caller can check it is gone.
        """
        name = self.full_name(details)
        self.open_leads_tab().search(name)
        record_id = self.row_record_id(name)
        self.open_row_actions(name).click_delete()
        self.click_confirm_delete()
        return record_id

    # --- Read -----------------------------------------------------------------------

    def column_names(self) -> list[str]:
        """Labels of the visible list view columns, e.g. ['Name', 'Title', 'Company', ...]."""
        # Lightning keeps hidden copies of list views in the page, so only read visible ones.
        headers = self.locator(self.column_headers).filter(visible=True)
        headers.first.wait_for(state="visible", timeout=self.DEFAULT_TIMEOUT)
        return [header.get_attribute("title") for header in headers.all()]
