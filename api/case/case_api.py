from pathlib import Path

from playwright.sync_api import APIRequestContext

from api.base_api import SObjectApi
from utils.config_reader import load_values

CASE_DIR = Path(__file__).resolve().parent
ENDPOINTS_FILE = CASE_DIR / "case_endpoints.yaml"
VALUES_FILE = CASE_DIR / "case_api_values.json"


def load_case_api_values() -> dict:
    return load_values(VALUES_FILE)


class CasesApi(SObjectApi):
    """API object for Case over the Salesforce REST API: create, read, query, update, delete."""

    def __init__(self, request: APIRequestContext):
        super().__init__(request, ENDPOINTS_FILE, "case")
