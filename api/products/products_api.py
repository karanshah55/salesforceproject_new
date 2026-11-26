from pathlib import Path

from playwright.sync_api import APIRequestContext

from api.base_api import SObjectApi
from utils.config_reader import load_values

PRODUCTS_DIR = Path(__file__).resolve().parent
ENDPOINTS_FILE = PRODUCTS_DIR / "products_endpoints.yaml"
VALUES_FILE = PRODUCTS_DIR / "product_api_values.json"


def load_product_api_values() -> dict:
    return load_values(VALUES_FILE)


class ProductsApi(SObjectApi):
    """API object for Product2 over the Salesforce REST API: create, read, query, update, delete."""

    def __init__(self, request: APIRequestContext):
        super().__init__(request, ENDPOINTS_FILE, "products")
