from playwright.sync_api import Page, expect

from pages.leads import LeadsPage


# Lead tests. They run after test_login (see conftest), in the same logged-in browser.


# The Leads list shows the expected columns (list_columns in lead_values.json).
def test_leads_list_columns(lead_details: dict, app_page: Page):
    leads_page = LeadsPage(app_page)
    leads_page.open_leads_tab()

    columns = leads_page.column_names()
    missing = [c for c in lead_details["list_columns"] if c not in columns]
    assert not missing, f"Leads list is missing columns {missing}; it shows {columns}"


def test_create_lead(lead_details: dict, app_page: Page):
    leads_page = LeadsPage(app_page)
    leads_page.create_lead(lead_details)

    # The pop-up closes once Salesforce has saved the lead.
    expect(leads_page.locator(leads_page.save_button)).to_be_hidden(timeout=30_000)


def edited(details: dict) -> dict:
    """The lead details after test_edit_lead, e.g. John Smith -> John Smith1."""
    return {**details, "last_name": details["edited_last_name"]}


# Runs after test_create_lead and renames the lead it created (last name -> edited_last_name).
def test_edit_lead(lead_details: dict, app_page: Page):
    leads_page = LeadsPage(app_page)
    leads_page.edit_lead(lead_details, lead_details["edited_last_name"])

    # The pop-up closes once Salesforce has saved the change.
    expect(leads_page.locator(leads_page.save_button)).to_be_hidden(timeout=30_000)


# Runs after test_edit_lead and removes the edited lead.
def test_delete_lead(lead_details: dict, app_page: Page):
    leads_page = LeadsPage(app_page)
    deleted = edited(lead_details)
    record_id = leads_page.delete_lead(deleted)

    # Salesforce confirms with a 'Lead "John Smith" was deleted.' toast.
    expect(leads_page.locator(leads_page.deleted_toast)).to_be_visible(timeout=30_000)

    # Searching for it again no longer shows that record (checked by id, since older leads
    # with the same name may still exist).
    leads_page.search(leads_page.full_name(deleted))
    expect(leads_page.record_row_locator(record_id)).to_have_count(0, timeout=30_000)
