import html
import json
from pathlib import Path

from playwright.sync_api import APIResponse

from utils.screenshots import RUN_STAMP, SCREENSHOTS_DIR


def _pretty(text: str) -> str:
    """Pretty-print a JSON body; leave anything else (e.g. an empty 204) as-is."""
    try:
        return json.dumps(json.loads(text), indent=2)
    except (ValueError, TypeError):
        return text or "(no body)"


class ApiEvidence:
    """Request/response evidence for API tests - the API counterpart of StepScreenshots.

    ApiEvidence("api", "test_opportunity_api", prefix="test_create_opportunity_api") saves to
    screenshots/api/test_opportunity_api/<run time>/<prefix>_01_POST_201.html, ... one file per call.
    """

    def __init__(self, *folders: str, prefix: str):
        self.folder = SCREENSHOTS_DIR.joinpath(*folders, RUN_STAMP)
        self.prefix = prefix
        self.count = 0

    def capture(self, method: str, url: str, payload, response: APIResponse) -> Path:
        self.count += 1
        self.folder.mkdir(parents=True, exist_ok=True)
        path = self.folder / f"{self.prefix}_{self.count:02d}_{method}_{response.status}.html"
        path.write_text(self._render(method, url, payload, response), encoding="utf-8")
        return path

    def _render(self, method: str, url: str, payload, response: APIResponse) -> str:
        esc = html.escape
        ok = response.ok
        request_body = _pretty(json.dumps(payload)) if payload is not None else "(no request body)"
        response_body = _pretty(response.text())
        colour = "#1a7f37" if ok else "#cf222e"
        return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>{esc(method)} {response.status}</title>
<style>
 body{{font-family:system-ui,Segoe UI,Arial,sans-serif;margin:2rem;color:#1f2328;background:#fff}}
 h1{{font-size:1.1rem}} .status{{color:{colour};font-weight:700}}
 .u{{color:#57606a;word-break:break-all}} h2{{font-size:.85rem;text-transform:uppercase;color:#57606a;margin:1.3rem 0 .3rem}}
 pre{{background:#f6f8fa;border:1px solid #d0d7de;border-radius:6px;padding:.8rem;overflow:auto;white-space:pre-wrap}}
</style></head><body>
 <h1>{esc(method)} &rarr; <span class="status">{response.status} {esc(response.status_text)}</span></h1>
 <div class="u">{esc(url)}</div>
 <h2>Request body</h2><pre>{esc(request_body)}</pre>
 <h2>Response body</h2><pre>{esc(response_body)}</pre>
</body></html>"""


class LoggingApiRequest:
    """Wraps a Playwright APIRequestContext so each call is recorded as evidence.

    Delegates everything to the real context; when `recorder` is set (per test), every
    get/post/patch/delete is saved. API objects use it exactly like the real context.
    """

    def __init__(self, inner):
        self._inner = inner
        self.recorder: ApiEvidence | None = None

    def _call(self, method: str, name: str, url: str, kwargs):
        response = getattr(self._inner, name)(url, **kwargs)
        if self.recorder is not None:
            payload = kwargs.get("data", kwargs.get("params"))
            self.recorder.capture(method, url, payload, response)
        return response

    def post(self, url, **kwargs):
        return self._call("POST", "post", url, kwargs)

    def get(self, url, **kwargs):
        return self._call("GET", "get", url, kwargs)

    def patch(self, url, **kwargs):
        return self._call("PATCH", "patch", url, kwargs)

    def delete(self, url, **kwargs):
        return self._call("DELETE", "delete", url, kwargs)

    def __getattr__(self, name):
        # Anything else (e.g. dispose) passes straight through to the real context.
        return getattr(self._inner, name)
