from playwright.sync_api import Page, expect

from pages.common import ProfileMenu
from pages.login import LoginPage


def test_salesforce_login(app_page: Page, credentials: dict):
    LoginPage(app_page).navigate().login(credentials["username"], credentials["password"])

    # The profile avatar only appears once the user is logged in.
    profile_menu = ProfileMenu(app_page)
    expect(profile_menu.locator(profile_menu.view_profile)).to_be_visible(timeout=30_000)
