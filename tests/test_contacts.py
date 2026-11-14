from playwright.sync_api import Page, expect

from pages.contacts import ContactsPage
from utils.screenshots import StepScreenshots


# Contact CRUD tests. They run after test_login (see conftest), in the same logged-in browser,
# top to bottom: create -> edit -> delete the same contact.


def edited(details: dict) -> dict:
    """The contact details after test_edit_contact, e.g. Jane Doe -> Jane Doe1."""
    return {**details, "last_name": details["edited_last_name"]}


def test_create_contact(contact_details: dict, app_page: Page):
    contacts_page = ContactsPage(app_page)
    # Step screenshots go to screenshots/contacts/create_contact/<run time>/.
    contacts_page.screenshots = StepScreenshots(app_page, "contacts", "create_contact")
    contacts_page.create_contact(contact_details)

    # The pop-up closes once Salesforce has saved the contact.
    expect(contacts_page.locator(contacts_page.save_button)).to_be_hidden(timeout=30_000)
    contacts_page.screenshot("contact_saved")


# Runs after test_create_contact and renames it (last name -> edited_last_name).
def test_edit_contact(contact_details: dict, app_page: Page):
    contacts_page = ContactsPage(app_page)
    contacts_page.edit_contact(contact_details, contact_details["edited_last_name"])

    # The pop-up closes once Salesforce has saved the change.
    expect(contacts_page.locator(contacts_page.save_button)).to_be_hidden(timeout=30_000)


# Runs after test_edit_contact and removes the edited contact.
def test_delete_contact(contact_details: dict, app_page: Page):
    contacts_page = ContactsPage(app_page)
    contacts_page.delete_contact(edited(contact_details))

    # Salesforce confirms with a 'Contact "Jane Doe1" was deleted.' toast.
    expect(contacts_page.locator(contacts_page.deleted_toast)).to_be_visible(timeout=30_000)
