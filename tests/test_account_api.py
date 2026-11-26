import pytest

from api.accounts import AccountsApi


# Account CRUD over the Salesforce REST API. The api_request fixture authenticates with the
# OAuth Client Credentials flow (no browser, no login), so these run on their own. Top to bottom:
# create -> get -> query -> update -> delete the same record.


@pytest.fixture(scope="module")
def created_account() -> dict:
    """Shared by the tests below: test_create stores the new record's id here."""
    return {}


def record_id(created_account: dict) -> str:
    if "id" not in created_account:
        pytest.skip("test_create_account_api did not create a record")
    return created_account["id"]


def test_create_account_api(api_request, account_api_details: dict, created_account: dict):
    response = AccountsApi(api_request).create(account_api_details["create"])

    assert response.status == 201, response.text()
    body = response.json()
    assert body["success"] is True, body
    assert body["id"].startswith("001"), body  # 001 = Account record id prefix
    created_account["id"] = body["id"]


def test_get_account_api(api_request, account_api_details: dict, created_account: dict):
    response = AccountsApi(api_request).get(record_id(created_account))

    assert response.status == 200, response.text()
    record = response.json()
    for field, value in account_api_details["create"].items():
        assert record[field] == value, f"{field}: expected {value!r}, got {record[field]!r}"


def test_query_account_api(api_request, account_api_details: dict, created_account: dict):
    create = account_api_details["create"]
    response = AccountsApi(api_request).find_by("Name", create["Name"])

    assert response.status == 200, response.text()
    ids = [record["Id"] for record in response.json()["records"]]
    assert record_id(created_account) in ids, f"SOQL search returned {ids}"


def test_update_account_api(api_request, account_api_details: dict, created_account: dict):
    api = AccountsApi(api_request)
    response = api.update(record_id(created_account), account_api_details["update"])
    assert response.status == 204, response.text()

    # Read it back: the changed fields are saved.
    record = api.get(record_id(created_account)).json()
    for field, value in account_api_details["update"].items():
        assert record[field] == value, f"{field}: expected {value!r}, got {record[field]!r}"


def test_delete_account_api(api_request, created_account: dict):
    api = AccountsApi(api_request)
    response = api.delete(record_id(created_account))
    assert response.status == 204, response.text()

    # The server no longer returns it.
    response = api.get(record_id(created_account))
    assert response.status == 404, response.text()
