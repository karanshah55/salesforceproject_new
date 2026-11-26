import html
import re
import shutil
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import quote

from utils.screenshots import RUN_STAMP, SCREENSHOTS_DIR

PROJECT_DIR = SCREENSHOTS_DIR.parent
REPORTS_DIR = PROJECT_DIR / "reports"
FAILURES_DIR = SCREENSHOTS_DIR / "failures" / RUN_STAMP

# A test's status is the worst of its setup / call / teardown phases.
SEVERITY = {"passed": 0, "skipped": 1, "failed": 2}
MESSAGE_LINES = 6  # lines of the error shown per failed test


@dataclass
class TestResult:
    module: str
    name: str
    status: str = "passed"
    duration: float = 0.0
    message: str = ""
    screenshot: Path | None = None


def save_failure_screenshot(item) -> Path | None:
    """Screenshot of the shared browser tab at the moment a test failed."""
    page = item.funcargs.get("app_page")
    if page is None or page.is_closed():
        return None
    file_name = re.sub(r"[^\w.-]", "_", f"{item.path.stem}-{item.name}")
    path = FAILURES_DIR / f"{file_name}.png"
    try:
        FAILURES_DIR.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=path)
    except Exception:  # a crashed browser must not hide the real failure
        return None
    return path


def _message(report) -> str:
    if report.skipped and isinstance(report.longrepr, tuple):
        return report.longrepr[2].removeprefix("Skipped: ")
    crash = getattr(report.longrepr, "reprcrash", None)
    text = crash.message if crash else str(report.longrepr)
    lines = "\n".join(text.strip().splitlines()[:MESSAGE_LINES])
    return lines if report.when == "call" else f"[failed in {report.when}] {lines}"


def _relative(path: Path) -> str:
    return path.relative_to(PROJECT_DIR).as_posix()


def _link(path: Path) -> str:
    # The report sits in reports/, so evidence is one folder up.
    return quote(f"../{_relative(path)}")


def _duration(delta: timedelta) -> str:
    minutes, seconds = divmod(round(delta.total_seconds()), 60)
    return f"{minutes}m {seconds}s" if minutes else f"{seconds}s"


class RunReport:
    """Pass/fail counts and evidence of one pytest run.

    Printed at the end of the run and saved as reports/report_<run time>.html
    (reports/latest.html is always the most recent run).
    """

    def __init__(self):
        self.started = datetime.now()
        self.results: dict[str, TestResult] = {}

    def record(self, item, report, screenshot: Path | None = None) -> None:
        result = self.results.setdefault(item.nodeid, TestResult(item.path.stem, item.name))
        result.duration += report.duration
        status = "passed" if report.passed else "skipped" if report.skipped else "failed"
        if SEVERITY[status] > SEVERITY[result.status]:
            result.status = status
            result.message = _message(report)
        result.screenshot = screenshot or result.screenshot

    def counts(self) -> Counter:
        return Counter(result.status for result in self.results.values())

    @staticmethod
    def pass_rate(counts: Counter) -> int:
        total = sum(counts.values())
        return round(100 * counts["passed"] / total) if total else 0

    @staticmethod
    def evidence_folders() -> list[Path]:
        """Screenshot folders written during this run: step screenshots and failures."""
        return sorted(folder for folder in SCREENSHOTS_DIR.rglob(RUN_STAMP) if folder.is_dir())

    def finish(self, terminal) -> None:
        if not self.results:  # e.g. --collect-only
            return
        command = " ".join(["pytest", *terminal.config.invocation_params.args])
        duration = _duration(datetime.now() - self.started)
        counts = self.counts()
        evidence = self.evidence_folders()

        REPORTS_DIR.mkdir(exist_ok=True)
        report_file = REPORTS_DIR / f"report_{RUN_STAMP}.html"
        report_file.write_text(self.render(counts, evidence, duration, command), encoding="utf-8")
        shutil.copyfile(report_file, REPORTS_DIR / "latest.html")

        self.print_summary(terminal, counts, evidence, duration, report_file)

    # --- Terminal ---------------------------------------------------------------------

    def print_summary(self, terminal, counts, evidence, duration, report_file) -> None:
        failed = [result for result in self.results.values() if result.status == "failed"]
        terminal.write_sep("=", "Run summary", bold=True)
        terminal.write_line(
            f"Total: {sum(counts.values())}   Passed: {counts['passed']}   Failed: {counts['failed']}   "
            f"Skipped: {counts['skipped']}   Pass rate: {self.pass_rate(counts)}%   Time: {duration}",
            bold=True, green=not failed, red=bool(failed),
        )
        if failed:
            terminal.write_line("")
            terminal.write_line("Failed tests:", red=True)
            for result in failed:
                reason = result.message.splitlines()[0] if result.message else ""
                terminal.write_line(f"  - {result.module}::{result.name}  ->  {reason}")

        terminal.write_line("")
        terminal.write_line("Evidence saved in:")
        for folder in evidence:
            count = len([f for f in folder.iterdir() if f.is_file()])
            terminal.write_line(f"  {_relative(folder)}  ({count} file(s))")
        if not evidence:
            terminal.write_line("  (no evidence was saved in this run)")

        terminal.write_line("")
        terminal.write_line(f"HTML report: {_relative(report_file)}  (latest run: reports/latest.html)", bold=True)

    # --- HTML -------------------------------------------------------------------------

    def render(self, counts, evidence, duration, command) -> str:
        esc = html.escape
        total = sum(counts.values())
        overall = "failed" if counts["failed"] else "passed"

        cards = "".join(
            f'<div class="card"><div class="label">{label}</div><div class="value {status if value else ""}">{value}</div></div>'
            for label, value, status in [
                ("Total", total, ""),
                ("Passed", counts["passed"], "passed"),
                ("Failed", counts["failed"], "failed"),
                ("Skipped", counts["skipped"], "skipped"),
                ("Pass rate", f"{self.pass_rate(counts)}%", ""),
            ]
        )
        bar = "".join(
            f'<span class="{status}" style="width:{100 * counts[status] / total:.2f}%"></span>'
            for status in ("passed", "failed", "skipped")
            if counts[status]
        )

        rows, module = [], None
        for result in self.results.values():  # already in run order
            if result.module != module:
                module = result.module
                rows.append(f'<tr class="module"><td colspan="3">{esc(module)}.py</td></tr>')
            detail = f'<pre class="{result.status}">{esc(result.message)}</pre>' if result.message else ""
            if result.screenshot:
                detail += (
                    f'<a href="{_link(result.screenshot)}" target="_blank">'
                    f'<img class="shot" src="{_link(result.screenshot)}" alt="Screen at failure"></a>'
                )
            rows.append(
                f'<tr><td>{esc(result.name)}{detail}</td>'
                f'<td><span class="pill {result.status}">{result.status.upper()}</span></td>'
                f'<td class="num">{result.duration:.1f}s</td></tr>'
            )

        blocks = []
        for folder in evidence:
            images = sorted(folder.glob("*.png"))
            thumbs = "".join(
                f'<figure><a href="{_link(image)}" target="_blank">'
                f'<img src="{_link(image)}" alt="{esc(image.stem)}" loading="lazy"></a>'
                f"<figcaption>{esc(image.name)}</figcaption></figure>"
                for image in images
            )
            # Non-image evidence (e.g. API request/response HTML) is listed as links.
            others = sorted(f for f in folder.iterdir() if f.is_file() and f.suffix != ".png")
            links = "".join(
                f'<li><a href="{_link(f)}" target="_blank">{esc(f.name)}</a></li>' for f in others
            )
            links_html = f'<ul class="files">{links}</ul>' if links else ""
            count = len(images) + len(others)
            blocks.append(
                f'<div class="evidence"><a class="folder" href="{_link(folder)}">{esc(_relative(folder))}</a>'
                f'<span class="meta"> &middot; {count} file(s)</span>'
                f'<div class="thumbs">{thumbs}</div>{links_html}</div>'
            )
        evidence_html = "".join(blocks) or '<p class="meta">No evidence was saved in this run.</p>'

        return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Test Run Report</title>
<style>{STYLE}</style>
</head>
<body>
<main>
  <header>
    <div>
      <h1>Test Run Report</h1>
      <div class="meta">{self.started:%d %b %Y, %H:%M:%S} &middot; {duration} &middot; <code>{esc(command)}</code></div>
    </div>
    <span class="badge {overall}">{overall.upper()}</span>
  </header>
  <section class="cards">{cards}</section>
  <div class="bar">{bar}</div>

  <h2>Results</h2>
  <div class="table-wrap">
    <table>
      <thead><tr><th>Test</th><th>Status</th><th class="num">Duration</th></tr></thead>
      <tbody>{"".join(rows)}</tbody>
    </table>
  </div>

  <h2>Evidence</h2>
  {evidence_html}
</main>
</body>
</html>
"""


STYLE = """
:root {
  --bg: #f5f6f8; --card: #ffffff; --text: #1d2330; --muted: #667085; --line: #e4e7ec; --accent: #0b5cad;
  --pass: #12805c; --pass-bg: #e3f6ee; --fail: #c4320a; --fail-bg: #fdecea; --skip: #a15c07; --skip-bg: #fef4e0;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #111418; --card: #1a1f26; --text: #e6e9ee; --muted: #98a2b3; --line: #2b323c; --accent: #6aa9ff;
    --pass: #4ad295; --pass-bg: #123326; --fail: #ff8a6b; --fail-bg: #3a1a14; --skip: #f5b84c; --skip-bg: #3a2a10;
  }
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--text); font: 14px/1.5 "Segoe UI", system-ui, sans-serif; }
main { max-width: 1100px; margin: 0 auto; padding: 32px 16px 48px; }
header { display: flex; flex-wrap: wrap; gap: 12px; align-items: center; justify-content: space-between; }
h1 { margin: 0; font-size: 24px; }
h2 { margin: 32px 0 12px; font-size: 16px; }
code { font: 12px Consolas, monospace; }
.meta { color: var(--muted); }
header .meta { margin-top: 4px; }
.badge, .pill { border-radius: 999px; font-weight: 600; letter-spacing: .04em; }
.badge { padding: 6px 16px; }
.pill { display: inline-block; padding: 2px 10px; font-size: 12px; }
.badge.passed, .pill.passed { background: var(--pass-bg); color: var(--pass); }
.badge.failed, .pill.failed { background: var(--fail-bg); color: var(--fail); }
.pill.skipped { background: var(--skip-bg); color: var(--skip); }
.cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; margin-top: 24px; }
.card { background: var(--card); border: 1px solid var(--line); border-radius: 10px; padding: 16px; }
.card .label { color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: .06em; }
.card .value { margin-top: 4px; font-size: 28px; font-weight: 600; font-variant-numeric: tabular-nums; }
.value.passed { color: var(--pass); } .value.failed { color: var(--fail); } .value.skipped { color: var(--skip); }
.bar { display: flex; height: 8px; margin-top: 16px; border-radius: 999px; overflow: hidden; background: var(--line); }
.bar .passed { background: var(--pass); } .bar .failed { background: var(--fail); } .bar .skipped { background: var(--skip); }
.table-wrap { overflow-x: auto; border: 1px solid var(--line); border-radius: 10px; }
table { width: 100%; border-collapse: collapse; background: var(--card); }
th, td { padding: 10px 14px; border-bottom: 1px solid var(--line); text-align: left; vertical-align: top; }
tbody tr:last-child td { border-bottom: 0; }
th { color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: .06em; }
tr.module td { background: var(--bg); font-weight: 600; }
.num { text-align: right; white-space: nowrap; font-variant-numeric: tabular-nums; }
pre { margin: 6px 0 0; white-space: pre-wrap; word-break: break-word; font: 12px/1.45 Consolas, monospace; }
pre.failed { color: var(--fail); } pre.skipped { color: var(--skip); }
img.shot { display: block; max-width: 320px; width: 100%; margin-top: 8px; border: 1px solid var(--line); border-radius: 6px; }
.evidence { margin-bottom: 12px; padding: 16px; background: var(--card); border: 1px solid var(--line); border-radius: 10px; }
.evidence a.folder { color: var(--accent); font: 13px Consolas, monospace; word-break: break-all; }
.thumbs { display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 10px; margin-top: 12px; }
.thumbs figure { margin: 0; }
.thumbs img { display: block; width: 100%; border: 1px solid var(--line); border-radius: 6px; }
figcaption { margin-top: 4px; color: var(--muted); font-size: 12px; word-break: break-all; }
"""
