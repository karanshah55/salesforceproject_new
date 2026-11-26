import pytest

from api.opportunities import OpportunitiesApi


# Opportunity CRUD over the Salesforce REST API. The api_request fixture authenticates with the
# OAuth Client Credentials flow (no browser, no login), so these run on their own. Top to bottom:
# create -> get -> query -> update -> delete the same record.


@pytest.fixture(scope="module")
def created_opportunity() -> dict:
    """Shared by the tests below: test_create stores the new record's id here."""
    return {}


def record_id(created_opportunity: dict) -> str:
    if "id" not in created_opportunity:
        pytest.skip("test_create_opportunity_api did not create a record")
    return created_opportunity["id"]


def test_create_opportunity_api(api_request, opportunity_api_details: dict, created_opportunity: dict):
    response = OpportunitiesApi(api_request).create(opportunity_api_details["create"])

    assert response.status == 201, response.text()
    body = response.json()
    assert body["success"] is True, body
    assert body["id"].startswith("006"), body  # 006 = Opportunity record id prefix
    created_opportunity["id"] = body["id"]


def test_get_opportunity_api(api_request, opportunity_api_details: dict, created_opportunity: dict):
    response = OpportunitiesApi(api_request).get(record_id(created_opportunity))

    assert response.status == 200, response.text()
    record = response.json()
    for field, value in opportunity_api_details["create"].items():
        assert record[field] == value, f"{field}: expected {value!r}, got {record[field]!r}"


def test_query_opportunity_api(api_request, opportunity_api_details: dict, created_opportunity: dict):
    create = opportunity_api_details["create"]
    response = OpportunitiesApi(api_request).find_by("Name", create["Name"])

    assert response.status == 200, response.text()
    ids = [record["Id"] for record in response.json()["records"]]
    assert record_id(created_opportunity) in ids, f"SOQL search returned {ids}"


def test_update_opportunity_api(api_request, opportunity_api_details: dict, created_opportunity: dict):
    api = OpportunitiesApi(api_request)
    response = api.update(record_id(created_opportunity), opportunity_api_details["update"])
    assert response.status == 204, response.text()

    # Read it back: the changed fields are saved.
    record = api.get(record_id(created_opportunity)).json()
    for field, value in opportunity_api_details["update"].items():
        assert record[field] == value, f"{field}: expected {value!r}, got {record[field]!r}"


def test_delete_opportunity_api(api_request, created_opportunity: dict):
    api = OpportunitiesApi(api_request)
    response = api.delete(record_id(created_opportunity))
    assert response.status == 204, response.text()

    # The server no longer returns it.
    response = api.get(record_id(created_opportunity))
    assert response.status == 404, response.text()
