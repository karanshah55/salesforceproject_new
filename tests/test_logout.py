from playwright.sync_api import Page, expect

from pages.login import LoginPage
from pages.logout import LogoutPage


# Runs last, after test_login (see conftest), ending the shared logged-in session.
def test_salesforce_logout(app_page: Page):
    LogoutPage(app_page).logout()

    # After logging out Salesforce returns to the login page.
    login_page = LoginPage(app_page)
    expect(login_page.locator(login_page.username_input)).to_be_visible(timeout=30_000)
