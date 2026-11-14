from playwright.sync_api import Page, expect

from pages.accounts import AccountsPage


# Account CRUD tests. They run after test_login (see conftest), in the same logged-in browser,
# top to bottom: create -> edit -> delete the same account.


def edited(details: dict) -> dict:
    """The account details after test_edit_account, e.g. Acme -> Acme1."""
    return {**details, "account_name": details["edited_account_name"]}


def test_create_account(account_details: dict, app_page: Page):
    accounts_page = AccountsPage(app_page)
    accounts_page.create_account(account_details)

    # The pop-up closes once Salesforce has saved the account.
    expect(accounts_page.locator(accounts_page.save_button)).to_be_hidden(timeout=30_000)


# Runs after test_create_account and renames it (name -> edited_account_name).
def test_edit_account(account_details: dict, app_page: Page):
    accounts_page = AccountsPage(app_page)
    accounts_page.edit_account(account_details, account_details["edited_account_name"])

    # The pop-up closes once Salesforce has saved the change.
    expect(accounts_page.locator(accounts_page.save_button)).to_be_hidden(timeout=30_000)


# Runs after test_edit_account and removes the edited account.
def test_delete_account(account_details: dict, app_page: Page):
    accounts_page = AccountsPage(app_page)
    accounts_page.delete_account(edited(account_details))

    # Salesforce confirms with an 'Account "..." was deleted.' toast.
    expect(accounts_page.locator(accounts_page.deleted_toast)).to_be_visible(timeout=30_000)
