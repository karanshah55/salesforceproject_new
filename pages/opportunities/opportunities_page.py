from pathlib import Path

from playwright.sync_api import Page

from pages.base_page import BasePage
from utils.config_reader import load_selectors, load_values

OPPORTUNITIES_DIR = Path(__file__).resolve().parent
SELECTORS_FILE = OPPORTUNITIES_DIR / "opportunities_selectors.yaml"
VALUES_FILE = OPPORTUNITIES_DIR / "opportunities_values.json"


def load_opportunity_values() -> dict:
    return load_values(VALUES_FILE)


class OpportunitiesPage(BasePage):
    """Page object for the Opportunities tab: create, read, update and delete Opportunities."""

    def __init__(self, page: Page):
        super().__init__(page)
        opportunities = load_selectors(SELECTORS_FILE, "opportunities")
        self.opportunities_tab = opportunities["opportunities_tab"]
        self.new_button = opportunities["new_button"]
        self.search_input = opportunities["search_input"]
        self.row_actions = opportunities["row_actions"]

        form = load_selectors(SELECTORS_FILE, "opportunity_form")
        self.opportunity_name = form["opportunity_name"]
        self.account_name = form["account_name"]
        self.account_option = form["account_option"]
        self.close_date = form["close_date"]
        self.stage = form["stage"]
        self.stage_option = form["stage_option"]
        self.amount = form["amount"]
        self.save_button = form["save_button"]

        edit = load_selectors(SELECTORS_FILE, "edit_opportunity")
        self.edit_action = edit["edit_action"]

        delete = load_selectors(SELECTORS_FILE, "delete_opportunity")
        self.delete_action = delete["delete_action"]
        self.confirm_delete = delete["confirm_delete"]
        self.deleted_toast = delete["deleted_toast"]

    # --- Navigation / list view -----------------------------------------------------

    def open_opportunities_tab(self) -> "OpportunitiesPage":
        self.click_if_enabled(self.opportunities_tab)
        return self

    def search(self, text: str) -> "OpportunitiesPage":
        """Type into 'Search this list...' and press Enter to filter the list."""
        self.fill(self.search_input, text)
        self.locator(self.search_input).press("Enter")
        self.pause()
        return self

    def open_row_actions(self, name: str) -> "OpportunitiesPage":
        self.click_if_enabled(self.row_actions.format(name=name))
        return self

    # --- Opportunity form (shared by Create and Update) -----------------------------

    def enter_opportunity_name(self, opportunity_name: str) -> "OpportunitiesPage":
        self.fill(self.opportunity_name, opportunity_name)
        return self

    def select_account(self, account_name: str) -> "OpportunitiesPage":
        # Lookup field: typing searches Accounts, then click the matching result.
        self.fill(self.account_name, account_name)
        self.click_if_enabled(self.account_option.format(value=account_name))
        return self

    def enter_close_date(self, close_date: str) -> "OpportunitiesPage":
        self.fill(self.close_date, close_date)
        # Tab away so the date picker pop-up closes and doesn't cover the next field.
        self.locator(self.close_date).press("Tab")
        return self

    def select_stage(self, stage: str) -> "OpportunitiesPage":
        # Lightning dropdown: open it, then click the matching option.
        self.click_if_enabled(self.stage)
        self.click_if_enabled(self.stage_option.format(value=stage))
        return self

    def enter_amount(self, amount: str) -> "OpportunitiesPage":
        self.fill(self.amount, amount)
        return self

    def fill_opportunity_form(self, details: dict) -> "OpportunitiesPage":
        self.enter_opportunity_name(details["opportunity_name"])
        self.select_account(details["account_name"])
        self.enter_close_date(details["close_date"])
        self.select_stage(details["stage"])
        self.enter_amount(details["amount"])
        return self

    def click_save(self) -> "OpportunitiesPage":
        self.click_if_enabled(self.save_button)
        return self

    # --- Create ---------------------------------------------------------------------

    def click_new(self) -> "OpportunitiesPage":
        self.click_if_enabled(self.new_button)
        return self

    def create_opportunity(self, details: dict) -> None:
        """Opportunities tab -> New -> fill the pop-up -> Save."""
        self.open_opportunities_tab().click_new()
        self.fill_opportunity_form(details)
        self.click_save()

    # --- Update ---------------------------------------------------------------------

    def click_edit(self) -> "OpportunitiesPage":
        self.click_if_enabled(self.edit_action)
        return self

    def edit_opportunity(self, details: dict, new_opportunity_name: str) -> None:
        """Opportunities tab -> search by name -> row actions -> Edit -> change name -> Save."""
        name = details["opportunity_name"]
        self.open_opportunities_tab().search(name)
        self.open_row_actions(name).click_edit()
        self.enter_opportunity_name(new_opportunity_name)
        self.click_save()

    # --- Delete ---------------------------------------------------------------------

    def click_delete(self) -> "OpportunitiesPage":
        self.click_if_enabled(self.delete_action)
        return self

    def click_confirm_delete(self) -> "OpportunitiesPage":
        self.click_if_enabled(self.confirm_delete)
        return self

    def delete_opportunity(self, details: dict) -> None:
        """Opportunities tab -> search by name -> row actions -> Delete -> confirm."""
        name = details["opportunity_name"]
        self.open_opportunities_tab().search(name)
        self.open_row_actions(name).click_delete()
        self.click_confirm_delete()

    # --- Read: add here when that use case comes in. --------------------------------
