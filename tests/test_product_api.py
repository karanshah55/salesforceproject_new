import pytest

from api.products import ProductsApi


# Product2 CRUD over the Salesforce REST API. The api_request fixture authenticates with the
# OAuth Client Credentials flow (no browser, no login), so these run on their own. Top to bottom:
# create -> get -> query -> update -> delete the same record.


@pytest.fixture(scope="module")
def created_product() -> dict:
    """Shared by the tests below: test_create stores the new record's id here."""
    return {}


def record_id(created_product: dict) -> str:
    if "id" not in created_product:
        pytest.skip("test_create_product_api did not create a record")
    return created_product["id"]


def test_create_product_api(api_request, product_api_details: dict, created_product: dict):
    response = ProductsApi(api_request).create(product_api_details["create"])

    assert response.status == 201, response.text()
    body = response.json()
    assert body["success"] is True, body
    assert body["id"].startswith("01t"), body  # 01t = Product2 record id prefix
    created_product["id"] = body["id"]


def test_get_product_api(api_request, product_api_details: dict, created_product: dict):
    response = ProductsApi(api_request).get(record_id(created_product))

    assert response.status == 200, response.text()
    record = response.json()
    for field, value in product_api_details["create"].items():
        assert record[field] == value, f"{field}: expected {value!r}, got {record[field]!r}"


def test_query_product_api(api_request, product_api_details: dict, created_product: dict):
    create = product_api_details["create"]
    response = ProductsApi(api_request).find_by("Name", create["Name"])

    assert response.status == 200, response.text()
    ids = [record["Id"] for record in response.json()["records"]]
    assert record_id(created_product) in ids, f"SOQL search returned {ids}"


def test_update_product_api(api_request, product_api_details: dict, created_product: dict):
    api = ProductsApi(api_request)
    response = api.update(record_id(created_product), product_api_details["update"])
    assert response.status == 204, response.text()

    # Read it back: the changed fields are saved.
    record = api.get(record_id(created_product)).json()
    for field, value in product_api_details["update"].items():
        assert record[field] == value, f"{field}: expected {value!r}, got {record[field]!r}"


def test_delete_product_api(api_request, created_product: dict):
    api = ProductsApi(api_request)
    response = api.delete(record_id(created_product))
    assert response.status == 204, response.text()

    # The server no longer returns it.
    response = api.get(record_id(created_product))
    assert response.status == 404, response.text()
