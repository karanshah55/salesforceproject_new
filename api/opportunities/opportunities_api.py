from pathlib import Path

from playwright.sync_api import APIRequestContext

from api.base_api import SObjectApi
from utils.config_reader import load_values

OPPORTUNITIES_DIR = Path(__file__).resolve().parent
ENDPOINTS_FILE = OPPORTUNITIES_DIR / "opportunities_endpoints.yaml"
VALUES_FILE = OPPORTUNITIES_DIR / "opportunity_api_values.json"


def load_opportunity_api_values() -> dict:
    return load_values(VALUES_FILE)


class OpportunitiesApi(SObjectApi):
    """API object for Opportunity over the Salesforce REST API: create, read, query, update, delete."""

    def __init__(self, request: APIRequestContext):
        super().__init__(request, ENDPOINTS_FILE, "opportunities")
