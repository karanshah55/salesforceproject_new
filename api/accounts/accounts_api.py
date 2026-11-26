from pathlib import Path

from playwright.sync_api import APIRequestContext

from api.base_api import SObjectApi
from utils.config_reader import load_values

ACCOUNTS_DIR = Path(__file__).resolve().parent
ENDPOINTS_FILE = ACCOUNTS_DIR / "accounts_endpoints.yaml"
VALUES_FILE = ACCOUNTS_DIR / "account_api_values.json"


def load_account_api_values() -> dict:
    return load_values(VALUES_FILE)


class AccountsApi(SObjectApi):
    """API object for Account over the Salesforce REST API: create, read, query, update, delete."""

    def __init__(self, request: APIRequestContext):
        super().__init__(request, ENDPOINTS_FILE, "accounts")
