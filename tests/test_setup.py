from playwright.sync_api import Page, expect

from pages.common import QuickSettings
from pages.setup import SetupPage


# Runs after test_login (see conftest), from the same logged-in browser.
def test_open_app_manager(setup_details: dict, app_page: Page):
    # Quick Settings -> Open Advanced Setup opens Setup in a new tab.
    quick_settings = QuickSettings(app_page).open()
    setup_tab = quick_settings.open_advanced_setup()
    try:
        setup_page = SetupPage(setup_tab)
        setup_page.open_setup_page(setup_details["quick_find"])

        expect(setup_page.heading(setup_details["app_manager_heading"])).to_be_visible(timeout=30_000)
    finally:
        # Back to the main tab so the following tests (and logout) carry on there.
        setup_tab.close()
        quick_settings.close()
