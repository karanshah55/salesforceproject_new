import random

from playwright.sync_api import Locator, Page

from utils.screenshots import StepScreenshots


class BasePage:
    """Common actions shared by all page objects."""

    DEFAULT_TIMEOUT = 30_000  # ms

    # Human-like pacing (ms). Tweak these to make the run faster/slower.
    THINK_DELAY = (600, 1500)      # pause before each action
    KEYSTROKE_DELAY = (80, 200)    # pause between typed characters

    def __init__(self, page: Page):
        self.page = page
        # Set by a test to save step screenshots; None means screenshot() does nothing.
        self.screenshots: StepScreenshots | None = None

    def screenshot(self, step: str) -> None:
        """Save a numbered step screenshot when the test turned screenshots on."""
        if self.screenshots:
            self.screenshots.capture(step)

    def pause(self, delay_range: tuple[int, int] = THINK_DELAY) -> None:
        self.page.wait_for_timeout(random.randint(*delay_range))

    def open(self, url: str) -> None:
        self.page.goto(url, wait_until="domcontentloaded")
        self.pause()

    def locator(self, selector: str) -> Locator:
        # Selectors in the YAML are XPath; prefix so Playwright never guesses wrong.
        if selector.startswith("//") and not selector.startswith("xpath="):
            selector = f"xpath={selector}"
        return self.page.locator(selector)

    def wait_for_visible(self, selector: str, timeout: int = DEFAULT_TIMEOUT) -> Locator:
        element = self.locator(selector)
        element.wait_for(state="visible", timeout=timeout)
        return element

    def fill(self, selector: str, value: str) -> None:
        """Click into the field and type one key at a time, like a person would."""
        element = self.wait_for_visible(selector)
        self.pause()
        element.click()
        element.clear()
        for char in value:
            element.press_sequentially(char)
            self.pause(self.KEYSTROKE_DELAY)

    def click_if_enabled(self, selector: str, timeout: int = DEFAULT_TIMEOUT) -> None:
        element = self.wait_for_visible(selector, timeout)
        if not element.is_enabled():
            raise AssertionError(f"Element '{selector}' is visible but not enabled")
        self.pause()
        element.hover()
        self.pause((200, 500))
        element.click()
