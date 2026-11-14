from playwright.sync_api import Page, expect

from pages.products import ProductsPage


# Product CRUD tests. They run after test_login (see conftest), in the same logged-in browser,
# top to bottom: create -> edit -> delete the same product.


def edited(details: dict) -> dict:
    """The product details after test_edit_product, e.g. Widget -> Widget1."""
    return {**details, "product_name": details["edited_product_name"]}


def test_create_product(product_details: dict, app_page: Page):
    products_page = ProductsPage(app_page)
    products_page.create_product(product_details)

    # The wizard closes once Salesforce has saved the product.
    expect(products_page.locator(products_page.finish_button)).to_be_hidden(timeout=30_000)


# Runs after test_create_product and renames it (name -> edited_product_name).
def test_edit_product(product_details: dict, app_page: Page):
    products_page = ProductsPage(app_page)
    products_page.edit_product(product_details, product_details["edited_product_name"])

    # The pop-up closes once Salesforce has saved the change.
    expect(products_page.locator(products_page.save_button)).to_be_hidden(timeout=30_000)


# Runs after test_edit_product and removes the edited product.
def test_delete_product(product_details: dict, app_page: Page):
    products_page = ProductsPage(app_page)
    products_page.delete_product(edited(product_details))

    # Salesforce confirms with a 'Product "..." was deleted.' toast.
    expect(products_page.locator(products_page.deleted_toast)).to_be_visible(timeout=30_000)
