from pathlib import Path

from playwright.sync_api import Page

from pages.base_page import BasePage
from utils.config_reader import load_selectors, load_values

ACCOUNTS_DIR = Path(__file__).resolve().parent
SELECTORS_FILE = ACCOUNTS_DIR / "accounts_selectors.yaml"
VALUES_FILE = ACCOUNTS_DIR / "accounts_values.json"


def load_account_values() -> dict:
    return load_values(VALUES_FILE)


class AccountsPage(BasePage):
    """Page object for the Accounts tab: create, read, update and delete Accounts."""

    def __init__(self, page: Page):
        super().__init__(page)
        accounts = load_selectors(SELECTORS_FILE, "accounts")
        self.accounts_tab = accounts["accounts_tab"]
        self.new_button = accounts["new_button"]
        self.search_input = accounts["search_input"]
        self.row_actions = accounts["row_actions"]

        form = load_selectors(SELECTORS_FILE, "account_form")
        self.account_name = form["account_name"]
        self.phone = form["phone"]
        self.website = form["website"]
        self.save_button = form["save_button"]

        edit = load_selectors(SELECTORS_FILE, "edit_account")
        self.edit_action = edit["edit_action"]

        delete = load_selectors(SELECTORS_FILE, "delete_account")
        self.delete_action = delete["delete_action"]
        self.confirm_delete = delete["confirm_delete"]
        self.deleted_toast = delete["deleted_toast"]

    # --- Navigation / list view -----------------------------------------------------

    def open_accounts_tab(self) -> "AccountsPage":
        self.click_if_enabled(self.accounts_tab)
        return self

    def search(self, text: str) -> "AccountsPage":
        """Type into 'Search this list...' and press Enter to filter the list."""
        self.fill(self.search_input, text)
        self.locator(self.search_input).press("Enter")
        self.pause()
        return self

    def open_row_actions(self, name: str) -> "AccountsPage":
        self.click_if_enabled(self.row_actions.format(name=name))
        return self

    # --- Account form (shared by Create and Update) ---------------------------------

    def enter_account_name(self, account_name: str) -> "AccountsPage":
        self.fill(self.account_name, account_name)
        return self

    def enter_phone(self, phone: str) -> "AccountsPage":
        self.fill(self.phone, phone)
        return self

    def enter_website(self, website: str) -> "AccountsPage":
        self.fill(self.website, website)
        return self

    def fill_account_form(self, details: dict) -> "AccountsPage":
        self.enter_account_name(details["account_name"])
        self.enter_phone(details["phone"])
        self.enter_website(details["website"])
        return self

    def click_save(self) -> "AccountsPage":
        self.click_if_enabled(self.save_button)
        return self

    # --- Create ---------------------------------------------------------------------

    def click_new(self) -> "AccountsPage":
        self.click_if_enabled(self.new_button)
        return self

    def create_account(self, details: dict) -> None:
        """Accounts tab -> New -> fill the pop-up -> Save."""
        self.open_accounts_tab().click_new()
        self.fill_account_form(details)
        self.click_save()

    # --- Update ---------------------------------------------------------------------

    def click_edit(self) -> "AccountsPage":
        self.click_if_enabled(self.edit_action)
        return self

    def edit_account(self, details: dict, new_account_name: str) -> None:
        """Accounts tab -> search by name -> row actions -> Edit -> change name -> Save."""
        name = details["account_name"]
        self.open_accounts_tab().search(name)
        self.open_row_actions(name).click_edit()
        self.enter_account_name(new_account_name)
        self.click_save()

    # --- Delete ---------------------------------------------------------------------

    def click_delete(self) -> "AccountsPage":
        self.click_if_enabled(self.delete_action)
        return self

    def click_confirm_delete(self) -> "AccountsPage":
        self.click_if_enabled(self.confirm_delete)
        return self

    def delete_account(self, details: dict) -> None:
        """Accounts tab -> search by name -> row actions -> Delete -> confirm."""
        name = details["account_name"]
        self.open_accounts_tab().search(name)
        self.open_row_actions(name).click_delete()
        self.click_confirm_delete()

    # --- Read: add here when that use case comes in. --------------------------------
