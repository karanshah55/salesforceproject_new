import re

from playwright.sync_api import Page, expect

from pages.case import CasePage
from pages.case.case_page import CASE_RECORD_URL
from utils.screenshots import StepScreenshots


# Case test. Runs after test_login (see conftest), in the same logged-in browser, and just
# before test_logout, because it switches the browser to the Service app.
def test_create_case(case_details: dict, app_page: Page):
    case_page = CasePage(app_page)
    # Step screenshots go to screenshots/case/create_case/<run time>/.
    case_page.screenshots = StepScreenshots(app_page, "case", "create_case")
    case_page.create_case(case_details)

    # Saved: the pop-up closes, Salesforce confirms with 'Case "00001001" was created.'
    # and opens the new Case record.
    expect(case_page.locator(case_page.save_button)).to_be_hidden(timeout=30_000)
    expect(case_page.locator(case_page.created_toast)).to_be_visible(timeout=30_000)
    expect(app_page).to_have_url(re.compile(CASE_RECORD_URL), timeout=30_000)
    case_page.screenshot("case_saved")
