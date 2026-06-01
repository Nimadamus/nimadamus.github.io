#!/usr/bin/env python3
"""
Calendar / archive integrity guard (Nima, June 1 2026).

Prevents the class of bug where stale old articles surface under the wrong date
or via stale nav. Run before publishing; non-zero exit = a real problem.

Checks:
  1. featured-games-data.js: every referenced page exists on disk, and when a
     dated featured page declares window.FORCED_PAGE_DATE it MUST equal the
     calendar entry's date (article date == calendar date).
  2. Sport <sport>-calendar.js ARCHIVE_DATA: every referenced concrete page
     (no '#', no external) exists on disk.
  3. No article date/calendar date mismatch in any sport calendar either.
  4. The permanent hub featured-game-of-the-day.html is a REDIRECTOR
     (location.replace present) and carries no frozen <article> board.
  5. Every "Featured Game" nav link across the site points at the stable hub
     /featured-game-of-the-day.html (never a dated page that goes stale).
  6. Each sport calendar JS still contains the stale-hub redirect guard.
"""
import os
import re
import sys
import glob

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STABLE_HUB = 'featured-game-of-the-day.html'
errors = []
warnings = []

ENTRY_RE = re.compile(r'\{\s*date:\s*"([0-9]{4}-[0-9]{2}-[0-9]{2})"\s*,\s*page:\s*"([^"]+)"')
FORCED_RE = re.compile(r"FORCED_PAGE_DATE\s*=\s*'([0-9]{4}-[0-9]{2}-[0-9]{2})'")
NAV_RE = re.compile(r'<a\b[^>]*?href="([^"]*)"[^>]*>\s*Featured Game<')


def page_path(page):
    return os.path.join(REPO, page.split('#')[0])


def forced_date(page):
    p = page_path(page)
    if not os.path.exists(p):
        return None
    with open(p, 'r', encoding='utf-8', errors='ignore') as f:
        m = FORCED_RE.search(f.read())
    return m.group(1) if m else None


def check_data_file(js_path, label):
    if not os.path.exists(js_path):
        warnings.append(f"{label}: file not found ({js_path})")
        return
    with open(js_path, 'r', encoding='utf-8', errors='ignore') as f:
        text = f.read()
    for date, page in ENTRY_RE.findall(text):
        if page.endswith('.html') and '#' not in page and not page.startswith('http'):
            if not os.path.exists(page_path(page)):
                errors.append(f"{label}: entry {date} -> {page} but file is MISSING")
                continue
            # Hub/landing pages legitimately differ (redirectors); skip them.
            if page in (STABLE_HUB,) or page.endswith('-previews.html'):
                continue
            fd = forced_date(page)
            if fd and fd != date:
                errors.append(f"{label}: DATE MISMATCH {page} listed {date} but FORCED_PAGE_DATE={fd}")


def main():
    # 1 + 3: featured + each sport calendar
    check_data_file(os.path.join(REPO, 'featured-games-data.js'), 'featured-games-data.js')
    for js in glob.glob(os.path.join(REPO, 'scripts', '*-calendar.js')):
        name = os.path.basename(js)
        check_data_file(js, name)
        # 6: stale-hub guard present in sport calendars. Sport hubs use the
        # clean-state guard renderPreviewHub(); the featured engine uses its own
        # redirectFeaturedHub(). Either is a valid hub stale-guard.
        if name != 'featured-games-calendar.js':
            with open(js, 'r', encoding='utf-8', errors='ignore') as f:
                if 'renderPreviewHub' not in f.read():
                    errors.append(f"{name}: hub stale-guard (renderPreviewHub) MISSING")

    # 4: hub is a redirector
    hub = os.path.join(REPO, STABLE_HUB)
    if os.path.exists(hub):
        with open(hub, 'r', encoding='utf-8', errors='ignore') as f:
            hub_txt = f.read()
        if 'location.replace' not in hub_txt:
            errors.append(f"{STABLE_HUB}: must be a redirector (location.replace missing)")
        if 'class="game-preview"' in hub_txt:
            errors.append(f"{STABLE_HUB}: still contains a frozen <article class=game-preview> board")
    else:
        errors.append(f"{STABLE_HUB}: missing")

    # 5: all Featured Game nav links point at the stable hub
    bad_nav = 0
    for fp in glob.glob(os.path.join(REPO, '**', '*.html'), recursive=True):
        if os.sep + '.git' + os.sep in fp:
            continue
        with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        for href in NAV_RE.findall(content):
            target = href.rstrip('/').split('/')[-1]
            if target != STABLE_HUB:
                bad_nav += 1
                if bad_nav <= 15:
                    errors.append(f"{os.path.relpath(fp, REPO)}: Featured Game nav -> '{href}' (must be /{STABLE_HUB})")
    if bad_nav > 15:
        errors.append(f"... and {bad_nav - 15} more stale Featured Game nav links")

    print("=" * 60)
    print("  CALENDAR / ARCHIVE INTEGRITY CHECK")
    print("=" * 60)
    for w in warnings:
        print("  [WARN]", w)
    if errors:
        for e in errors:
            print("  [FAIL]", e)
        print(f"\n  {len(errors)} problem(s) found. [FAILED]")
        return 1
    print("  No date/nav/archive mismatches found. [PASSED]")
    return 0


if __name__ == '__main__':
    sys.exit(main())
