import pytest

from api.leads import LeadsApi


# Lead CRUD over the Salesforce REST API. They run after test_login (see conftest), reusing its
# session, top to bottom: create -> get -> query -> update -> delete the same lead.


@pytest.fixture(scope="module")
def created_lead() -> dict:
    """Shared by the tests below: test_create_lead_api stores the new lead's id here."""
    return {}


def lead_id(created_lead: dict) -> str:
    if "id" not in created_lead:
        pytest.skip("test_create_lead_api did not create a lead")
    return created_lead["id"]


def test_create_lead_api(api_request, lead_api_details: dict, created_lead: dict):
    response = LeadsApi(api_request).create_lead(lead_api_details["create"])

    assert response.status == 201, response.text()
    body = response.json()
    assert body["success"] is True, body
    assert body["id"].startswith("00Q"), body  # 00Q = Lead record id prefix
    created_lead["id"] = body["id"]


def test_get_lead_api(api_request, lead_api_details: dict, created_lead: dict):
    response = LeadsApi(api_request).get_lead(lead_id(created_lead))

    assert response.status == 200, response.text()
    lead = response.json()
    for field, value in lead_api_details["create"].items():
        assert lead[field] == value, f"{field}: expected {value!r}, got {lead[field]!r}"


def test_query_lead_api(api_request, lead_api_details: dict, created_lead: dict):
    create = lead_api_details["create"]
    response = LeadsApi(api_request).find_leads_by_name(create["FirstName"], create["LastName"])

    assert response.status == 200, response.text()
    ids = [record["Id"] for record in response.json()["records"]]
    assert lead_id(created_lead) in ids, f"SOQL search returned {ids}"


def test_update_lead_api(api_request, lead_api_details: dict, created_lead: dict):
    leads_api = LeadsApi(api_request)
    response = leads_api.update_lead(lead_id(created_lead), lead_api_details["update"])
    assert response.status == 204, response.text()

    # Read it back: the changed fields are saved.
    lead = leads_api.get_lead(lead_id(created_lead)).json()
    for field, value in lead_api_details["update"].items():
        assert lead[field] == value, f"{field}: expected {value!r}, got {lead[field]!r}"


def test_delete_lead_api(api_request, created_lead: dict):
    leads_api = LeadsApi(api_request)
    response = leads_api.delete_lead(lead_id(created_lead))
    assert response.status == 204, response.text()

    # The server no longer returns it.
    response = leads_api.get_lead(lead_id(created_lead))
    assert response.status == 404, response.text()
