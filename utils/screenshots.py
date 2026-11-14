from datetime import datetime
from pathlib import Path

from playwright.sync_api import Page

SCREENSHOTS_DIR = Path(__file__).resolve().parent.parent / "screenshots"

# One folder per test run, so earlier runs are never overwritten.
RUN_STAMP = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


class StepScreenshots:
    """Numbered screenshots of a flow's steps.

    StepScreenshots(page, "contacts", "create_contact") saves to
    screenshots/contacts/create_contact/<run time>/01_<step>.png, 02_<step>.png, ...
    """

    def __init__(self, page: Page, *folders: str):
        self.page = page
        self.folder = SCREENSHOTS_DIR.joinpath(*folders, RUN_STAMP)
        self.count = 0

    def capture(self, step: str) -> Path:
        self.count += 1
        self.folder.mkdir(parents=True, exist_ok=True)
        path = self.folder / f"{self.count:02d}_{step}.png"
        self.page.screenshot(path=path)
        return path
