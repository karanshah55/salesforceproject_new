from pathlib import Path

from playwright.sync_api import APIRequestContext, APIResponse, BrowserContext, Playwright

from utils.config_reader import load_selectors, load_values

CONFIG_FILE = Path(__file__).resolve().parent / "api_config.yaml"
# Connected App secrets for the OAuth Client Credentials flow (gitignored; see oauth_values.sample.json).
OAUTH_VALUES_FILE = Path(__file__).resolve().parent / "oauth_values.json"
OAUTH_PLACEHOLDER = "YOUR_CONNECTED_APP_CONSUMER_KEY"


def load_api_config() -> dict:
    return load_selectors(CONFIG_FILE, "api")


def load_oauth_values() -> dict:
    return load_values(OAUTH_VALUES_FILE)


def oauth_is_configured() -> bool:
    """True once oauth_values.json holds a real client id/secret (not the sample placeholder)."""
    if not OAUTH_VALUES_FILE.exists():
        return False
    creds = load_oauth_values()
    return bool(creds.get("client_id")) and creds.get("client_id") != OAUTH_PLACEHOLDER


def fetch_access_token(playwright: Playwright, config: dict, creds: dict) -> tuple[str, str]:
    """Get a token with the OAuth 2.0 Client Credentials flow: no browser, no passkey.

    Returns (access_token, instance_url). Raises RuntimeError with Salesforce's message on failure.
    """
    token_url = config["base_url"].rstrip("/") + config["token_path"]
    token_context = playwright.request.new_context()
    try:
        response = token_context.post(
            token_url,
            form={
                "grant_type": "client_credentials",
                "client_id": creds["client_id"],
                "client_secret": creds["client_secret"],
            },
        )
        body = response.json()
        if response.status != 200 or "access_token" not in body:
            # e.g. {"error":"invalid_client","error_description":"..."}
            error = body.get("error_description") or body.get("error") or response.text()
            raise RuntimeError(f"Salesforce OAuth token request failed ({response.status}): {error}")
        return body["access_token"], body.get("instance_url", config["base_url"])
    finally:
        token_context.dispose()


def new_api_request_oauth(playwright: Playwright) -> APIRequestContext:
    """REST API client authenticated with an OAuth Client Credentials access token."""
    config = load_api_config()
    access_token, instance_url = fetch_access_token(playwright, config, load_oauth_values())
    return playwright.request.new_context(
        base_url=instance_url, extra_http_headers={"Authorization": f"Bearer {access_token}"}
    )


def new_api_request(playwright: Playwright, browser_context: BrowserContext) -> APIRequestContext:
    """REST API client that reuses the browser's Salesforce login (its 'sid' session cookie).

    Kept as an alternative; the suite now authenticates the API with new_api_request_oauth.
    """
    base_url = load_api_config()["base_url"]
    host = base_url.split("://", 1)[1].rstrip("/")
    sid = next(
        (c["value"] for c in browser_context.cookies() if c["name"] == "sid" and c["domain"] == host),
        None,
    )
    if sid is None:
        raise RuntimeError(f"No Salesforce session for {host} - log in through the UI first")
    return playwright.request.new_context(
        base_url=base_url, extra_http_headers={"Authorization": f"Bearer {sid}"}
    )


def soql_quote(value: str) -> str:
    """Quote a value for a SOQL string literal."""
    return "'" + value.replace("\\", "\\\\").replace("'", "\\'") + "'"


class BaseApi:
    """Common helpers shared by all API objects (the API counterpart of BasePage)."""

    def __init__(self, request: APIRequestContext):
        self.request = request
        self.version = load_api_config()["version"]

    def endpoint(self, template: str, **values) -> str:
        """Fill an endpoint from the YAML, e.g. '/services/data/v{version}/sobjects/Lead/{record_id}'."""
        return template.format(version=self.version, **values)


class SObjectApi(BaseApi):
    """Generic CRUD for one Salesforce SObject over the REST API.

    Subclasses pass their endpoints file + section, which names the SObject and its paths.
    (The leads API predates this and keeps its own named methods; new objects share this base.)
    """

    def __init__(self, request: APIRequestContext, endpoints_file, section: str):
        super().__init__(request)
        endpoints = load_selectors(endpoints_file, section)
        self.name = endpoints["name"]  # SObject API name, e.g. "Account"
        self.sobject = endpoints["sobject"]
        self.record = endpoints["record"]
        self.query_endpoint = endpoints["query"]

    def create(self, fields: dict) -> APIResponse:
        """POST - 201 with {"id": ..., "success": true}."""
        return self.request.post(self.endpoint(self.sobject), data=fields)

    def get(self, record_id: str) -> APIResponse:
        """GET one record - 200 with its fields, 404 once it is deleted."""
        return self.request.get(self.endpoint(self.record, record_id=record_id))

    def query(self, soql: str) -> APIResponse:
        """GET a SOQL query - 200 with {"totalSize": ..., "records": [...]}."""
        return self.request.get(self.endpoint(self.query_endpoint), params={"q": soql})

    def find_by(self, field: str, value: str) -> APIResponse:
        """GET the records where field = value (SOQL)."""
        return self.query(f"SELECT Id FROM {self.name} WHERE {field} = {soql_quote(value)}")

    def update(self, record_id: str, fields: dict) -> APIResponse:
        """PATCH only the given fields - 204 with no body."""
        return self.request.patch(self.endpoint(self.record, record_id=record_id), data=fields)

    def delete(self, record_id: str) -> APIResponse:
        """DELETE - 204 with no body."""
        return self.request.delete(self.endpoint(self.record, record_id=record_id))
