from pathlib import Path

from playwright.sync_api import APIRequestContext, APIResponse

from api.base_api import BaseApi, soql_quote
from utils.config_reader import load_selectors, load_values

LEADS_DIR = Path(__file__).resolve().parent
ENDPOINTS_FILE = LEADS_DIR / "leads_endpoints.yaml"
VALUES_FILE = LEADS_DIR / "lead_api_values.json"


def load_lead_api_values() -> dict:
    return load_values(VALUES_FILE)


class LeadsApi(BaseApi):
    """API object for Leads over the Salesforce REST API: create, read, update and delete."""

    def __init__(self, request: APIRequestContext):
        super().__init__(request)
        endpoints = load_selectors(ENDPOINTS_FILE, "leads")
        self.sobject = endpoints["sobject"]
        self.record = endpoints["record"]
        self.query = endpoints["query"]

    # --- Create ---------------------------------------------------------------------

    def create_lead(self, fields: dict) -> APIResponse:
        """POST - 201 with {"id": ..., "success": true}."""
        return self.request.post(self.endpoint(self.sobject), data=fields)

    # --- Read -----------------------------------------------------------------------

    def get_lead(self, lead_id: str) -> APIResponse:
        """GET one lead - 200 with its fields, 404 once it is deleted."""
        return self.request.get(self.endpoint(self.record, record_id=lead_id))

    def query_leads(self, soql: str) -> APIResponse:
        """GET a SOQL query - 200 with {"totalSize": ..., "records": [...]}."""
        return self.request.get(self.endpoint(self.query), params={"q": soql})

    def find_leads_by_name(self, first_name: str, last_name: str) -> APIResponse:
        return self.query_leads(
            "SELECT Id, Name FROM Lead "
            f"WHERE FirstName = {soql_quote(first_name)} AND LastName = {soql_quote(last_name)}"
        )

    # --- Update ---------------------------------------------------------------------

    def update_lead(self, lead_id: str, fields: dict) -> APIResponse:
        """PATCH only the given fields - 204 with no body."""
        return self.request.patch(self.endpoint(self.record, record_id=lead_id), data=fields)

    # --- Delete ---------------------------------------------------------------------

    def delete_lead(self, lead_id: str) -> APIResponse:
        """DELETE - 204 with no body."""
        return self.request.delete(self.endpoint(self.record, record_id=lead_id))
