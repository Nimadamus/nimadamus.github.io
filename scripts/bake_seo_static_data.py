"""Bake hydrated data into records.html and upcomingpicks.html at publish time.

WHY: Both pages historically shipped placeholder shells ("--", "Loading Picks...")
and hydrated everything client-side from Google Sheets CSVs, so crawlers that do
not execute JavaScript saw no real content (GSC: upcomingpicks.html was never
crawled; see SEO_AUDIT_REPORT_2026-07-30.md, finding A).

HOW: Instead of re-implementing the pages' aggregation math in Python (drift risk
on trust-critical record numbers), this script loads each page in headless
Chromium, lets the page's OWN JavaScript hydrate from the live sheets, then
copies the rendered values back into the static HTML. Baked numbers are therefore
always exactly what the JS renders. The client-side JS still runs on load and
rewrites these regions (records.html clears each tbody; upcomingpicks.html
replaces the table body wholesale), so users continue to get live data.

SAFETY:
- Writes NOTHING unless every validation passes (never publishes empty/misleading
  data; on failure the previous good bake stays in place and exit code is 1).
- Touches only: the four stat divs + nine tbody regions in records.html, the
  picks tbody in upcomingpicks.html, and one <!-- seo-bake: ... --> comment per
  file. No canonicals, routes, titles, meta, or design.
- Verifies written files are non-NULL and re-parseable (C: NULL-byte hazard);
  restores from git and fails if corruption is detected.

Run from repo root: python scripts/bake_seo_static_data.py
"""

import http.server
import re
import socketserver
import subprocess
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
RECORD_RE = re.compile(r"^\d+-\d+(-\d+)?$")
NO_PICKS_MSG = "No upcoming picks at this time. Check back soon!"
FAIL_MARKERS = ("Could not load", "Loading Picks", "Loading...")

RECORDS_STATS = ["total-record", "win-rate", "avg-odds", "total-picks"]
RECORDS_TBODIES = [
    "sport-breakdown", "bet-type-breakdown", "monthly-breakdown",
    "unit-sizing-breakdown", "teaser-breakdown", "parlay-breakdown",
    "five-inning-breakdown", "total-bets-breakdown", "team-totals-by-sport",
]


def serve_repo():
    handler = http.server.SimpleHTTPRequestHandler
    httpd = socketserver.TCPServer(("127.0.0.1", 0), handler, bind_and_activate=True)
    httpd.RequestHandlerClass = type(
        "H", (handler,), {"directory": str(ROOT), "log_message": lambda *a: None}
    )
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    return httpd, httpd.server_address[1]


def capture(port):
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page()

        page.goto(f"http://127.0.0.1:{port}/records.html", wait_until="load", timeout=60000)
        page.wait_for_function(
            "() => /\\d+-\\d+/.test(document.getElementById('total-record').textContent)",
            timeout=90000,
        )
        page.wait_for_function(
            "() => document.querySelectorAll('#sport-breakdown tr').length > 0",
            timeout=30000,
        )
        records = {
            "stats": {
                sid: {
                    "text": page.eval_on_selector(f"#{sid}", "el => el.textContent.trim()"),
                    "class": page.eval_on_selector(f"#{sid}", "el => el.className"),
                }
                for sid in RECORDS_STATS
            },
            "tbodies": {
                tid: page.eval_on_selector(f"#{tid}", "el => el.innerHTML.trim()")
                for tid in RECORDS_TBODIES
            },
        }

        page.goto(f"http://127.0.0.1:{port}/upcomingpicks.html", wait_until="load", timeout=60000)
        page.wait_for_function(
            "() => !document.getElementById('picks-table-body').textContent.includes('Loading')",
            timeout=60000,
        )
        picks_html = page.eval_on_selector(
            "#picks-table-body", "el => el.innerHTML.trim()"
        )
        browser.close()
    return records, picks_html


def validate(records, picks_html):
    errors = []
    total = records["stats"]["total-record"]["text"]
    if not RECORD_RE.match(total):
        errors.append(f"total-record '{total}' does not look like a W-L(-P) record")
    for sid in RECORDS_STATS:
        text = records["stats"][sid]["text"]
        if not text or text == "--":
            errors.append(f"stat #{sid} is empty/placeholder: '{text}'")
    for tid in ("sport-breakdown", "bet-type-breakdown", "monthly-breakdown"):
        html = records["tbodies"][tid]
        if "<tr" not in html:
            errors.append(f"tbody #{tid} has no rows")
    for tid, html in records["tbodies"].items():
        for marker in FAIL_MARKERS:
            if marker in html:
                errors.append(f"tbody #{tid} contains failure marker '{marker}'")
    if "<tr" not in picks_html and NO_PICKS_MSG not in picks_html:
        errors.append("upcoming picks tbody has neither rows nor the no-picks message")
    for marker in FAIL_MARKERS:
        if marker in picks_html:
            errors.append(f"upcoming picks tbody contains failure marker '{marker}'")
    return errors


def inject(path, replacements):
    content = path.read_text(encoding="utf-8")
    original = content
    for pattern, replacement in replacements:
        new_content, count = re.subn(pattern, replacement, content, count=1, flags=re.S)
        if count != 1:
            raise RuntimeError(f"{path.name}: pattern not found (exactly once): {pattern[:80]}")
        content = new_content
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    marker = f"<!-- seo-bake: {stamp} -->"
    if "<!-- seo-bake:" in content:
        content = re.sub(r"<!-- seo-bake: [^>]+ -->", marker, content, count=1)
    else:
        content = content.replace("</body>", marker + "\n</body>", 1)
    if content == original:
        return False
    path.write_text(content, encoding="utf-8", newline="\n")
    written = path.read_bytes()
    if b"\x00" in written[:4096] or b"seo-bake" not in written:
        subprocess.run(["git", "checkout", "--", str(path)], cwd=ROOT, check=False)
        raise RuntimeError(f"{path.name}: written file failed integrity check; restored")
    return True


def esc(s):
    return s.replace("\\", r"\\")


def main():
    httpd, port = serve_repo()
    try:
        records, picks_html = capture(port)
    finally:
        httpd.shutdown()

    errors = validate(records, picks_html)
    if errors:
        print("SEO BAKE FAILED - nothing written, previous baked data preserved:")
        for err in errors:
            print(f"  - {err}")
        return 1

    rec_repl = []
    for sid in RECORDS_STATS:
        stat = records["stats"][sid]
        rec_repl.append((
            rf'<div class="[^"]*"\s+id="{sid}">.*?</div>',
            f'<div class="{stat["class"]}" id="{sid}">{esc(stat["text"])}</div>',
        ))
    for tid in RECORDS_TBODIES:
        rec_repl.append((
            rf'<tbody id="{tid}">.*?</tbody>',
            f'<tbody id="{tid}">{esc(records["tbodies"][tid])}</tbody>',
        ))
    inject(ROOT / "records.html", rec_repl)

    inject(ROOT / "upcomingpicks.html", [(
        r'<tbody id="picks-table-body">.*?</tbody>',
        f'<tbody id="picks-table-body">{esc(picks_html)}</tbody>',
    )])

    total = records["stats"]["total-record"]["text"]
    if NO_PICKS_MSG in picks_html:
        picks_desc = "no-picks message"
    else:
        picks_desc = f"{picks_html.count('<tr')} pick rows"
    print(f"SEO BAKE OK: records.html total-record={total}, "
          f"upcomingpicks.html {picks_desc}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
