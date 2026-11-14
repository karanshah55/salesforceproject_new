from pathlib import Path

from playwright.sync_api import Page
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from pages.base_page import BasePage
from utils.config_reader import load_selectors, load_values

PRODUCTS_DIR = Path(__file__).resolve().parent
SELECTORS_FILE = PRODUCTS_DIR / "products_selectors.yaml"
VALUES_FILE = PRODUCTS_DIR / "products_values.json"

SEARCH_RETRIES = 3
SEARCH_RETRY_WAIT = 10_000  # ms to wait for the row before searching again


def load_product_values() -> dict:
    return load_values(VALUES_FILE)


class ProductsPage(BasePage):
    """Page object for the Products tab: create, read, update and delete Products."""

    def __init__(self, page: Page):
        super().__init__(page)
        products = load_selectors(SELECTORS_FILE, "products")
        self.products_tab = products["products_tab"]
        self.new_button = products["new_button"]
        self.search_input = products["search_input"]
        self.row_actions = products["row_actions"]

        wizard = load_selectors(SELECTORS_FILE, "new_product_wizard")
        self.new_product_name = wizard["product_name"]
        self.new_product_code = wizard["product_code"]
        self.new_description = wizard["description"]
        self.next_button = wizard["next_button"]
        self.finish_button = wizard["finish_button"]

        form = load_selectors(SELECTORS_FILE, "product_form")
        self.product_name = form["product_name"]
        self.save_button = form["save_button"]

        edit = load_selectors(SELECTORS_FILE, "edit_product")
        self.edit_action = edit["edit_action"]

        delete = load_selectors(SELECTORS_FILE, "delete_product")
        self.delete_action = delete["delete_action"]
        self.confirm_delete = delete["confirm_delete"]
        self.deleted_toast = delete["deleted_toast"]

    # --- Navigation / list view -----------------------------------------------------

    def open_products_tab(self) -> "ProductsPage":
        self.click_if_enabled(self.products_tab)
        return self

    def search(self, text: str) -> "ProductsPage":
        """Type into 'Search this list...' and press Enter to filter the list."""
        self.fill(self.search_input, text)
        self.locator(self.search_input).press("Enter")
        self.pause()
        return self

    def open_row_actions(self, name: str) -> "ProductsPage":
        # Right after a rename the Products list search can return stale results for a
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

    # --- New Product wizard (Create) ------------------------------------------------

    def fill_new_product_form(self, details: dict) -> "ProductsPage":
        self.fill(self.new_product_name, details["product_name"])
        self.fill(self.new_product_code, details["product_code"])
        self.fill(self.new_description, details["description"])
        return self

    def click_next(self) -> "ProductsPage":
        self.click_if_enabled(self.next_button)
        return self

    def click_finish(self) -> "ProductsPage":
        # Step 2 (Price Book Entry) is optional, so finish without filling it.
        self.click_if_enabled(self.finish_button)
        return self

    # --- Edit form (Update) ---------------------------------------------------------

    def enter_product_name(self, product_name: str) -> "ProductsPage":
        self.fill(self.product_name, product_name)
        return self

    def click_save(self) -> "ProductsPage":
        self.click_if_enabled(self.save_button)
        return self

    # --- Create ---------------------------------------------------------------------

    def click_new(self) -> "ProductsPage":
        self.click_if_enabled(self.new_button)
        return self

    def create_product(self, details: dict) -> None:
        """Products tab -> New -> fill details -> Next -> Finish (skip price book entry)."""
        self.open_products_tab().click_new()
        self.fill_new_product_form(details)
        self.click_next().click_finish()

    # --- Update ---------------------------------------------------------------------

    def click_edit(self) -> "ProductsPage":
        self.click_if_enabled(self.edit_action)
        return self

    def edit_product(self, details: dict, new_product_name: str) -> None:
        """Products tab -> search by name -> row actions -> Edit -> change name -> Save."""
        name = details["product_name"]
        self.open_products_tab().search(name)
        self.open_row_actions(name).click_edit()
        self.enter_product_name(new_product_name)
        self.click_save()

    # --- Delete ---------------------------------------------------------------------

    def click_delete(self) -> "ProductsPage":
        self.click_if_enabled(self.delete_action)
        return self

    def click_confirm_delete(self) -> "ProductsPage":
        self.click_if_enabled(self.confirm_delete)
        return self

    def delete_product(self, details: dict) -> None:
        """Products tab -> search by name -> row actions -> Delete -> confirm."""
        name = details["product_name"]
        self.open_products_tab().search(name)
        self.open_row_actions(name).click_delete()
        self.click_confirm_delete()

    # --- Read: add here when that use case comes in. --------------------------------
