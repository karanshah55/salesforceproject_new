from pathlib import Path

from playwright.sync_api import Page
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from pages.base_page import BasePage
from utils.config_reader import load_selectors, load_values

CONTACTS_DIR = Path(__file__).resolve().parent
SELECTORS_FILE = CONTACTS_DIR / "contacts_selectors.yaml"
VALUES_FILE = CONTACTS_DIR / "contacts_values.json"

SEARCH_RETRIES = 3
SEARCH_RETRY_WAIT = 10_000  # ms to wait for the row before searching again


def load_contact_values() -> dict:
    return load_values(VALUES_FILE)


class ContactsPage(BasePage):
    """Page object for the Contacts tab: create, read, update and delete Contacts."""

    def __init__(self, page: Page):
        super().__init__(page)
        contacts = load_selectors(SELECTORS_FILE, "contacts")
        self.contacts_tab = contacts["contacts_tab"]
        self.new_button = contacts["new_button"]
        self.search_input = contacts["search_input"]
        self.row_actions = contacts["row_actions"]

        form = load_selectors(SELECTORS_FILE, "contact_form")
        self.salutation = form["salutation"]
        self.salutation_option = form["salutation_option"]
        self.first_name = form["first_name"]
        self.last_name = form["last_name"]
        self.account_name = form["account_name"]
        self.account_option = form["account_option"]
        self.email = form["email"]
        self.phone = form["phone"]
        self.save_button = form["save_button"]

        edit = load_selectors(SELECTORS_FILE, "edit_contact")
        self.edit_action = edit["edit_action"]

        delete = load_selectors(SELECTORS_FILE, "delete_contact")
        self.delete_action = delete["delete_action"]
        self.confirm_delete = delete["confirm_delete"]
        self.deleted_toast = delete["deleted_toast"]

    @staticmethod
    def full_name(details: dict) -> str:
        """Name as Salesforce shows it in the list view, e.g. 'Jane Doe'."""
        return f"{details['first_name']} {details['last_name']}"

    # --- Navigation / list view -----------------------------------------------------

    def open_contacts_tab(self) -> "ContactsPage":
        self.click_if_enabled(self.contacts_tab)
        return self

    def search(self, text: str) -> "ContactsPage":
        """Type into 'Search this list...' and press Enter to filter the list."""
        self.fill(self.search_input, text)
        self.locator(self.search_input).press("Enter")
        self.pause()
        return self

    def open_row_actions(self, name: str) -> "ContactsPage":
        # Right after a rename the Contacts list search can return stale results for a
        # while, so search again until the row shows up.
        row_actions = self.row_actions.format(name=name)
        for _ in range(SEARCH_RETRIES):
            try:
                self.wait_for_visible(row_actions, timeout=SEARCH_RETRY_WAIT)
                break
            except PlaywrightTimeoutError:
                self.search(name)
        self.click_if_enabled(row_actions)
        return self

    # --- Contact form (shared by Create and Update) ---------------------------------

    def select_salutation(self, salutation: str) -> "ContactsPage":
        # Lightning dropdown: open it, then click the matching option.
        self.click_if_enabled(self.salutation)
        self.click_if_enabled(self.salutation_option.format(value=salutation))
        return self

    def enter_first_name(self, first_name: str) -> "ContactsPage":
        self.fill(self.first_name, first_name)
        return self

    def enter_last_name(self, last_name: str) -> "ContactsPage":
        self.fill(self.last_name, last_name)
        return self

    def select_account(self, account_name: str) -> "ContactsPage":
        # Lookup field: typing searches Accounts, then click the matching result.
        self.fill(self.account_name, account_name)
        self.click_if_enabled(self.account_option.format(value=account_name))
        return self

    def enter_email(self, email: str) -> "ContactsPage":
        self.fill(self.email, email)
        return self

    def enter_phone(self, phone: str) -> "ContactsPage":
        self.fill(self.phone, phone)
        return self

    def fill_contact_form(self, details: dict) -> "ContactsPage":
        self.select_salutation(details["Salutation"])
        self.enter_first_name(details["first_name"])
        self.enter_last_name(details["last_name"])
        self.select_account(details["account_name"])
        self.enter_email(details["email"])
        self.enter_phone(details["phone"])
        return self

    def click_save(self) -> "ContactsPage":
        self.click_if_enabled(self.save_button)
        return self

    # --- Create ---------------------------------------------------------------------

    def click_new(self) -> "ContactsPage":
        self.click_if_enabled(self.new_button)
        return self

    def create_contact(self, details: dict) -> None:
        """Contacts tab -> New -> fill the pop-up -> Save."""
        self.open_contacts_tab()
        self.wait_for_visible(self.new_button)
        self.screenshot("contacts_tab")

        self.click_new()
        self.wait_for_visible(self.first_name)
        self.screenshot("new_contact_form")

        self.fill_contact_form(details)
        # The pop-up scrolls inside itself, so capture both halves of the filled form.
        self.locator(self.salutation).scroll_into_view_if_needed()
        self.screenshot("form_filled_name_account")
        self.locator(self.email).scroll_into_view_if_needed()
        self.screenshot("form_filled_phone_email")
        self.click_save()

    # --- Update ---------------------------------------------------------------------

    def click_edit(self) -> "ContactsPage":
        self.click_if_enabled(self.edit_action)
        return self

    def edit_contact(self, details: dict, new_last_name: str) -> None:
        """Contacts tab -> search by name -> row actions -> Edit -> change last name -> Save."""
        name = self.full_name(details)
        self.open_contacts_tab().search(name)
        self.open_row_actions(name).click_edit()
        self.enter_last_name(new_last_name)
        self.click_save()

    # --- Delete ---------------------------------------------------------------------

    def click_delete(self) -> "ContactsPage":
        self.click_if_enabled(self.delete_action)
        return self

    def click_confirm_delete(self) -> "ContactsPage":
        self.click_if_enabled(self.confirm_delete)
        return self

    def delete_contact(self, details: dict) -> None:
        """Contacts tab -> search by name -> row actions -> Delete -> confirm."""
        name = self.full_name(details)
        self.open_contacts_tab().search(name)
        self.open_row_actions(name).click_delete()
        self.click_confirm_delete()

    # --- Read: add here when that use case comes in. --------------------------------
