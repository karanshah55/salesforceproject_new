import json
import re
from pathlib import Path

from playwright.sync_api import BrowserContext

# Cookies Salesforce sets once you pass "Verify Your Identity". Reusing them makes
# every fresh Playwright browser look like the same, already-trusted device.
DEVICE_STATE_FILE = Path(__file__).resolve().parent.parent / ".auth" / "device_state.json"

# A persistent Chrome profile for the test run (not incognito). It keeps the Salesforce
# trusted-device and passkey state between runs, so the passkey is approved by hand only
# once; later runs reuse it. Lives under .auth/ (gitignored), separate from your own Chrome.
CHROME_PROFILE_DIR = Path(__file__).resolve().parent.parent / ".auth" / "chrome_profile"

# The cookies that hold the logged-in session. Never saved, so each run starts logged out.
SESSION_COOKIES = re.compile(r"^sid(_Client)?$")


def save_device_state(context: BrowserContext) -> None:
    state = context.storage_state()
    state["cookies"] = [c for c in state["cookies"] if not SESSION_COOKIES.match(c["name"])]
    DEVICE_STATE_FILE.parent.mkdir(exist_ok=True)
    DEVICE_STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def forget_session(context: BrowserContext) -> None:
    """Drop the session cookies but keep the trusted-device cookie."""
    context.clear_cookies(name=SESSION_COOKIES)
