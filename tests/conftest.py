import pytest
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from api.accounts import load_account_api_values
from api.base_api import new_api_request_oauth, oauth_is_configured
from api.case import load_case_api_values
from api.opportunities import load_opportunity_api_values
from api.products import load_product_api_values
from api.leads import load_lead_api_values
from pages.accounts import load_account_values
from pages.case import load_case_values
from pages.common import OrgStatus, Popups
from pages.contacts import load_contact_values
from pages.leads import load_lead_values
from pages.login import load_login_values
from pages.opportunities import load_opportunity_values
from pages.products import load_product_values
from pages.setup import load_setup_values
from utils.api_evidence import ApiEvidence, LoggingApiRequest
from utils.device_state import CHROME_PROFILE_DIR, forget_session
from utils.run_report import RunReport, save_failure_screenshot

# Every test covers one page object and they run as one user journey in a shared browser,
# in this order. Running a test on its own pulls in its prerequisites and runs them first.
TEST_ORDER = [
    "test_login",
    "test_leads",
    "test_leads_api",
    "test_account_api",
    "test_case_api",
    "test_opportunity_api",
    "test_product_api",
    "test_contacts",
    "test_accounts",
    "test_opportunities",
    "test_products",
    "test_setup",
    "test_case",  # switches to the Service app, so it runs after the other app tests
    "test_logout",
]
PREREQUISITES = {
    "test_leads": ["test_login"],
    "test_contacts": ["test_login"],
    "test_accounts": ["test_login"],
    "test_opportunities": ["test_login"],
    "test_products": ["test_login"],
    "test_setup": ["test_login"],
    "test_case": ["test_login"],
    "test_logout": ["test_login"],
}
# Whenever a run logs in, it also ends by logging out (TEST_ORDER puts it last).
CLOSING_TESTS = {"test_login": ["test_logout"]}

# Tests that add, edit or delete records. Skipped when the org is read-only (trial ended).
WRITE_TEST_PREFIXES = ("test_create_", "test_edit_", "test_update_", "test_delete_")
READ_ONLY_REASON = "org is read-only (Salesforce trial has ended): add, edit and delete are blocked"
_org_read_only: bool | None = None  # checked once per run, on the first write test

_failed_modules: set[str] = set()
# Counts and evidence of this run, printed and saved to reports/ when the run ends.
_run_report = RunReport()


def pytest_collection_modifyitems(session, config, items):
    collected = {item.path.stem for item in items}
    missing = {
        prerequisite
        for item in items
        for prerequisite in PREREQUISITES.get(item.path.stem, [])
        if prerequisite not in collected
    }
    running = collected | missing
    missing |= {
        closing
        for name in running
        for closing in CLOSING_TESTS.get(name, [])
        if closing not in running
    }
    if missing:
        # Collect under the same tests package so its conftest fixtures stay visible.
        package = items[0].getparent(pytest.Module).parent
        for name in missing:
            module = pytest.Module.from_parent(package, path=package.path / f"{name}.py")
            items.extend(session.genitems(module))

    def position(item):
        stem = item.path.stem
        return TEST_ORDER.index(stem) if stem in TEST_ORDER else len(TEST_ORDER)

    items.sort(key=position)


@pytest.hookimpl(wrapper=True)
def pytest_runtest_makereport(item, call):
    report = yield
    setattr(item, f"rep_{report.when}", report)  # lets fixtures see whether the test failed
    screenshot = None
    if report.failed:
        _failed_modules.add(item.path.stem)
        if report.when == "call":
            screenshot = save_failure_screenshot(item)
    _run_report.record(item, report, screenshot)
    return report


def pytest_terminal_summary(terminalreporter):
    _run_report.finish(terminalreporter)


def pytest_runtest_setup(item):
    failed = [p for p in PREREQUISITES.get(item.path.stem, []) if p in _failed_modules]
    if failed:
        pytest.skip(f"prerequisite failed: {', '.join(failed)}")


@pytest.fixture(scope="session")
def app_page(playwright):
    """One shared tab for the whole run, in the real Google Chrome with a saved profile.

    A persistent profile (not incognito) keeps Salesforce's trusted-device and passkey state
    between runs, so you approve the passkey by hand only once and later runs skip it. The
    profile lives in .auth/chrome_profile (gitignored), separate from your everyday Chrome.
    """
    CHROME_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    context = playwright.chromium.launch_persistent_context(
        user_data_dir=str(CHROME_PROFILE_DIR),
        channel="chrome",   # the real Google Chrome, where your passkey works - not bundled Chromium
        headless=False,     # a passkey / identity check needs you to approve it in the window
        no_viewport=True,
        args=["--start-maximized"],
    )
    forget_session(context)  # drop the session cookie so each run starts at the login form
    page = context.pages[0] if context.pages else context.new_page()
    # Close pop-ups such as "Your trial has ended" whenever they appear, in every test.
    Popups(page).auto_close()
    yield page
    context.close()


def org_is_read_only(page) -> bool:
    global _org_read_only
    if _org_read_only is None:
        status = OrgStatus(page)
        try:
            status.wait_for_visible(status.read_only_banner, timeout=5_000)
            _org_read_only = True
        except PlaywrightTimeoutError:
            _org_read_only = False
    return _org_read_only


@pytest.fixture(autouse=True)
def org_guard(request):
    """Runs around every test.

    Before: skip UI tests that add/edit/delete when the org is read-only, instead of letting
    each one time out. After a failed test: cancel any New/Edit pop-up it left open, so the
    next test does not start blocked.

    Only touches the browser for tests that already use it (app_page in their fixtures), so API
    tests - which authenticate over OAuth and never open a browser - are left alone.
    """
    uses_browser = "app_page" in request.fixturenames
    if uses_browser and request.node.name.startswith(WRITE_TEST_PREFIXES):
        if org_is_read_only(request.getfixturevalue("app_page")):
            pytest.skip(READ_ONLY_REASON)
    yield
    report = getattr(request.node, "rep_call", None)
    if report is not None and report.failed and "app_page" in request.fixturenames:
        try:
            Popups(request.getfixturevalue("app_page")).close_open_form()
        except Exception:
            pass  # clean-up is best effort; the test failure itself is already reported


@pytest.fixture(scope="session")
def api_request(playwright):
    """Salesforce REST API client, authenticated with the OAuth Client Credentials flow.

    Server-to-server: no browser, no passkey, no UI login. Needs a Connected App's client id and
    secret in api/oauth_values.json (see api/oauth_values.sample.json). If those are missing, the
    API tests skip with setup instructions instead of failing.
    """
    if not oauth_is_configured():
        pytest.skip(
            "OAuth not configured: copy api/oauth_values.sample.json to api/oauth_values.json and "
            "fill in your Connected App's client id and secret (Client Credentials flow)."
        )
    request = LoggingApiRequest(new_api_request_oauth(playwright))
    yield request
    request.dispose()


@pytest.fixture(autouse=True)
def api_evidence(request):
    """For every API test, save each HTTP request/response as evidence under
    screenshots/api/<module>/<run time>/. Does nothing for tests that don't use the API."""
    if "api_request" not in request.fixturenames:
        yield
        return
    client = request.getfixturevalue("api_request")
    client.recorder = ApiEvidence("api", request.node.path.stem, prefix=request.node.name)
    yield
    client.recorder = None


@pytest.fixture(scope="session")
def credentials() -> dict:
    return load_login_values()


@pytest.fixture(scope="session")
def lead_details() -> dict:
    return load_lead_values()


@pytest.fixture(scope="session")
def lead_api_details() -> dict:
    return load_lead_api_values()


@pytest.fixture(scope="session")
def contact_details() -> dict:
    return load_contact_values()


@pytest.fixture(scope="session")
def account_details() -> dict:
    return load_account_values()


@pytest.fixture(scope="session")
def opportunity_details() -> dict:
    return load_opportunity_values()


@pytest.fixture(scope="session")
def product_details() -> dict:
    return load_product_values()


@pytest.fixture(scope="session")
def setup_details() -> dict:
    return load_setup_values()


@pytest.fixture(scope="session")
def case_details() -> dict:
    return load_case_values()


@pytest.fixture(scope="session")
def account_api_details() -> dict:
    return load_account_api_values()


@pytest.fixture(scope="session")
def case_api_details() -> dict:
    return load_case_api_values()


@pytest.fixture(scope="session")
def opportunity_api_details() -> dict:
    return load_opportunity_api_values()


@pytest.fixture(scope="session")
def product_api_details() -> dict:
    return load_product_api_values()
