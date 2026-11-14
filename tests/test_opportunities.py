from playwright.sync_api import Page, expect

from pages.opportunities import OpportunitiesPage


# Opportunity CRUD tests. They run after test_login (see conftest), in the same logged-in
# browser, top to bottom: create -> edit -> delete the same opportunity.


def edited(details: dict) -> dict:
    """The opportunity details after test_edit_opportunity, e.g. Deal -> Deal1."""
    return {**details, "opportunity_name": details["edited_opportunity_name"]}


def test_create_opportunity(opportunity_details: dict, app_page: Page):
    opportunities_page = OpportunitiesPage(app_page)
    opportunities_page.create_opportunity(opportunity_details)

    # The pop-up closes once Salesforce has saved the opportunity.
    expect(opportunities_page.locator(opportunities_page.save_button)).to_be_hidden(timeout=30_000)


# Runs after test_create_opportunity and renames it (name -> edited_opportunity_name).
def test_edit_opportunity(opportunity_details: dict, app_page: Page):
    opportunities_page = OpportunitiesPage(app_page)
    opportunities_page.edit_opportunity(
        opportunity_details, opportunity_details["edited_opportunity_name"]
    )

    # The pop-up closes once Salesforce has saved the change.
    expect(opportunities_page.locator(opportunities_page.save_button)).to_be_hidden(timeout=30_000)


# Runs after test_edit_opportunity and removes the edited opportunity.
def test_delete_opportunity(opportunity_details: dict, app_page: Page):
    opportunities_page = OpportunitiesPage(app_page)
    opportunities_page.delete_opportunity(edited(opportunity_details))

    # Salesforce confirms with an 'Opportunity "..." was deleted.' toast.
    expect(opportunities_page.locator(opportunities_page.deleted_toast)).to_be_visible(timeout=30_000)
