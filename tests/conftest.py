import pytest

from api.base_api import new_api_request
from api.leads import load_lead_api_values
from pages.accounts import load_account_values
from pages.case import load_case_values
from pages.contacts import load_contact_values
from pages.leads import load_lead_values
from pages.login import load_login_values
from pages.opportunities import load_opportunity_values
from pages.products import load_product_values
from pages.setup import load_setup_values
from utils.device_state import DEVICE_STATE_FILE, forget_session
from utils.run_report import RunReport, save_failure_screenshot

# Every test covers one page object and they run as one user journey in a shared browser,
# in this order. Running a test on its own pulls in its prerequisites and runs them first.
TEST_ORDER = [
    "test_login",
    "test_leads",
    "test_leads_api",
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
    "test_leads_api": ["test_login"],  # reuses the UI login's session as the API token
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
def browser_context_args(browser_context_args) -> dict:
    # Load the remembered device so Salesforce skips the email verification code.
    if DEVICE_STATE_FILE.exists():
        return {**browser_context_args, "storage_state": str(DEVICE_STATE_FILE)}
    return browser_context_args


@pytest.fixture(scope="session")
def app_page(browser, browser_context_args):
    """One browser tab shared by all tests, so each continues where the previous one stopped."""
    context = browser.new_context(**browser_context_args)
    forget_session(context)  # always start at the login form
    page = context.new_page()
    yield page
    context.close()


@pytest.fixture(scope="session")
def api_request(playwright, app_page):
    """Salesforce REST API client, authenticated with the session test_login created."""
    request = new_api_request(playwright, app_page.context)
    yield request
    request.dispose()


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
