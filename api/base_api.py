from pathlib import Path

from playwright.sync_api import APIRequestContext, BrowserContext, Playwright

from utils.config_reader import load_selectors

CONFIG_FILE = Path(__file__).resolve().parent / "api_config.yaml"


def load_api_config() -> dict:
    return load_selectors(CONFIG_FILE, "api")


def new_api_request(playwright: Playwright, browser_context: BrowserContext) -> APIRequestContext:
    """REST API client that reuses the browser's Salesforce login (its 'sid' session cookie)."""
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
