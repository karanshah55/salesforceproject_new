import pytest

from api.case import CasesApi


# Case CRUD over the Salesforce REST API. The api_request fixture authenticates with the
# OAuth Client Credentials flow (no browser, no login), so these run on their own. Top to bottom:
# create -> get -> query -> update -> delete the same record.


@pytest.fixture(scope="module")
def created_case() -> dict:
    """Shared by the tests below: test_create stores the new record's id here."""
    return {}


def record_id(created_case: dict) -> str:
    if "id" not in created_case:
        pytest.skip("test_create_case_api did not create a record")
    return created_case["id"]


def test_create_case_api(api_request, case_api_details: dict, created_case: dict):
    response = CasesApi(api_request).create(case_api_details["create"])

    assert response.status == 201, response.text()
    body = response.json()
    assert body["success"] is True, body
    assert body["id"].startswith("500"), body  # 500 = Case record id prefix
    created_case["id"] = body["id"]


def test_get_case_api(api_request, case_api_details: dict, created_case: dict):
    response = CasesApi(api_request).get(record_id(created_case))

    assert response.status == 200, response.text()
    record = response.json()
    for field, value in case_api_details["create"].items():
        assert record[field] == value, f"{field}: expected {value!r}, got {record[field]!r}"


def test_query_case_api(api_request, case_api_details: dict, created_case: dict):
    create = case_api_details["create"]
    response = CasesApi(api_request).find_by("Subject", create["Subject"])

    assert response.status == 200, response.text()
    ids = [record["Id"] for record in response.json()["records"]]
    assert record_id(created_case) in ids, f"SOQL search returned {ids}"


def test_update_case_api(api_request, case_api_details: dict, created_case: dict):
    api = CasesApi(api_request)
    response = api.update(record_id(created_case), case_api_details["update"])
    assert response.status == 204, response.text()

    # Read it back: the changed fields are saved.
    record = api.get(record_id(created_case)).json()
    for field, value in case_api_details["update"].items():
        assert record[field] == value, f"{field}: expected {value!r}, got {record[field]!r}"


def test_delete_case_api(api_request, created_case: dict):
    api = CasesApi(api_request)
    response = api.delete(record_id(created_case))
    assert response.status == 204, response.text()

    # The server no longer returns it.
    response = api.get(record_id(created_case))
    assert response.status == 404, response.text()
