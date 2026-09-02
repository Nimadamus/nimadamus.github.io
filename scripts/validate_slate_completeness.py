#!/usr/bin/env python3
"""
SLATE Completeness Validator
=============================
Ensures ALL active sports have dedicated pages for a given date.
Run this after every SLATE to catch missing sport pages IMMEDIATELY.

Usage:
    python scripts/validate_slate_completeness.py              # Check today
    python scripts/validate_slate_completeness.py 2026-03-05   # Check specific date
    python scripts/validate_slate_completeness.py --range 3     # Check last 3 days

Exit codes:
    0 = All active sports covered
    1 = Missing sport pages detected

Why this exists (March 6, 2026):
    Soccer pages were skipped on March 5 and 6 while NBA, NHL, and NCAAB
    pages were created. User had to discover the gap manually. This script
    ensures that can never happen again.
"""

import os
import re
import sys
import json
import subprocess
from datetime import datetime, timedelta

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Sport keywords that appear in filenames
SPORT_PATTERNS = {
    'NBA':    [r'\bnba\b'],
    'NHL':    [r'\bnhl\b'],
    'Soccer': [r'\bsoccer\b'],
    'NCAAB':  [r'\bncaab\b', r'\bcollege-basketball\b'],
    'NFL':    [r'\bnfl\b'],
    'NCAAF':  [r'\bncaaf\b', r'\bcollege-football\b'],
    'MLB':    [r'\bmlb\b'],
}

# Active months for each sport (1-indexed)
SPORT_SEASONS = {
    'NBA':    list(range(1, 7)) + [10, 11, 12],   # Oct-Jun
    'NHL':    list(range(1, 7)) + [10, 11, 12],   # Oct-Jun
    'Soccer': list(range(1, 13)),                   # Year-round
    'NCAAB':  [1, 2, 3, 11, 12],                   # Nov-Mar
    'NFL':    [1, 2, 9, 10, 11, 12],               # Sep-Feb
    'NCAAF':  [1, 8, 9, 10, 11, 12],               # Aug-Jan
    'MLB':    list(range(4, 11)),                    # Apr-Oct (regular season)
}

# Verified league off-days: dates inside a sport's season window where the
# league genuinely played NO games (e.g., gaps between playoff rounds/series).
# Every entry must be verified against the official schedule before being added
# here, so the validator never masks a real missing page.
NO_GAME_DATES = {
    'NHL': {
        '2026-04-10',  # No NHL game: confirmed off-day (schedule jumped Apr 9 -> Apr 11)
        '2026-04-17',  # No NHL game: regular season ended Apr 16, playoffs began Apr 18
        '2026-05-15',  # No NHL game: COL-MIN R2 ended May 13 (G5); MTL-BUF next game was G6 May 16
        '2026-05-17',  # No NHL game: between MTL-BUF G6 (May 16) and G7 (May 18)
        '2026-05-19',  # No NHL game: MTL-BUF G7 was May 18; conference finals began May 20
    },
    'NBA': {
        '2026-04-11',  # No NBA game: confirmed off-day (0 games; next gameday Apr 12)
    },
    'Soccer': {
        '2026-04-03',  # No major club soccer: Good Friday; top leagues played the Apr 4-5 weekend
    },
}

CALENDAR_JS = {
    'NBA': 'scripts/nba-calendar.js',
    'NHL': 'scripts/nhl-calendar.js',
    'Soccer': 'scripts/soccer-calendar.js',
    'NCAAB': 'scripts/ncaab-calendar.js',
    'NFL': 'scripts/nfl-calendar.js',
    'NCAAF': 'scripts/ncaaf-calendar.js',
    'MLB': 'scripts/mlb-calendar.js',
}

MANIFEST_SPORTS = {
    'NBA': 'nba',
    'NHL': 'nhl',
    'Soccer': 'soccer',
    'NCAAB': 'ncaab',
    'MLB': 'mlb',
}


def get_active_sports(date):
    """Return list of sports that should have pages for this date."""
    month = date.month
    active = []
    for sport, months in SPORT_SEASONS.items():
        if month in months:
            active.append(sport)
    return active


def date_to_filename_patterns(date):
    """Generate possible date patterns that appear in filenames."""
    patterns = []
    # march-5-2026, march-05-2026
    month_name = date.strftime('%B').lower()
    patterns.append(f"{month_name}-{date.day}-{date.year}")
    patterns.append(f"{month_name}-{date.day:02d}-{date.year}")
    # 2026-03-05
    patterns.append(date.strftime('%Y-%m-%d'))
    return patterns


def find_calendar_page(sport, date_iso):
    """Return a page from the sport calendar for date_iso when it exists."""
    calendar_path = os.path.join(REPO_ROOT, CALENDAR_JS[sport])
    try:
        with open(calendar_path, 'r', encoding='utf-8', errors='ignore') as f:
            calendar_data = f.read()
    except OSError:
        return None

    pattern = re.compile(
        r'\{\s*date:\s*"' + re.escape(date_iso) + r'",\s*page:\s*"([^"]+)"',
        re.I,
    )
    match = pattern.search(calendar_data)
    if not match:
        return None
    page = match.group(1)
    if page.startswith('archives/'):
        filepath = os.path.join(REPO_ROOT, *page.split('/'))
    else:
        filepath = os.path.join(REPO_ROOT, page.split('#', 1)[0])
    return page if os.path.exists(filepath) else None


def parse_calendar_entries(sport):
    """Return all generated calendar entries for a sport."""
    calendar_path = os.path.join(REPO_ROOT, CALENDAR_JS[sport])
    try:
        with open(calendar_path, 'r', encoding='utf-8', errors='ignore') as f:
            calendar_data = f.read()
    except OSError:
        return []

    pattern = re.compile(
        r'\{\s*date:\s*"([^"]+)",\s*page:\s*"([^"]+)",\s*title:\s*"([^"]*)"\s*\}',
        re.I,
    )
    return pattern.findall(calendar_data)


def page_target_exists(page):
    """Check that a calendar page target exists, including hash anchors when present."""
    path_part, _, anchor = page.partition('#')
    if path_part.startswith('archives/'):
        filepath = os.path.join(REPO_ROOT, *path_part.split('/'))
    else:
        filepath = os.path.join(REPO_ROOT, path_part)

    if not os.path.exists(filepath):
        return False, 'missing file'

    if anchor:
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except OSError:
            return False, 'unreadable file'
        if f'id="{anchor}"' not in content and f"id='{anchor}'" not in content:
            return False, 'missing anchor'

    return True, ''


def validate_calendar_integrity():
    """Validate all generated calendar entries and archived manifest dates."""
    errors = []
    calendar_dates = {}

    for sport in CALENDAR_JS:
        entries = parse_calendar_entries(sport)
        dates = set()
        seen = set()
        for date_iso, page, _title in entries:
            dates.add(date_iso)
            key = (date_iso, page)
            if key in seen:
                errors.append(f"{sport}: duplicate calendar entry {date_iso} -> {page}")
            seen.add(key)

            ok, reason = page_target_exists(page)
            if not ok:
                errors.append(f"{sport}: {date_iso} -> {page} has {reason}")

        calendar_dates[sport] = dates

    manifest_path = os.path.join(REPO_ROOT, 'scripts', 'hub-archive-manifest.json')
    if os.path.exists(manifest_path):
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"hub-archive-manifest.json is unreadable: {exc}")
            manifest = {}

        for sport, manifest_key in MANIFEST_SPORTS.items():
            for date_iso in manifest.get(manifest_key, []):
                if date_iso not in calendar_dates.get(sport, set()):
                    errors.append(f"{sport}: manifest date {date_iso} is missing from {CALENDAR_JS[sport]}")

    return errors


def validate_calendar_rendering():
    """Validate generated sport calendar scripts render complete month grids."""
    errors = []
    node_script = r"""
const fs = require('fs');
const vm = require('vm');
const calendarPath = process.argv[1];
const targetMonth = process.argv[2];
const source = fs.readFileSync(calendarPath, 'utf8');
const cells = [];
function makeEl(tag) {
  return {
    tag,
    children: [],
    className: '',
    textContent: '',
    title: '',
    style: {},
    appendChild(child) { this.children.push(child); if (this.id === 'calendar-days') cells.push(child); },
    addEventListener() {},
    remove() {},
    set innerHTML(value) { this.children = []; if (this.id === 'calendar-days') cells.length = 0; },
    get innerHTML() { return ''; }
  };
}
const elements = {
  'calendar-days': makeEl('div'),
  'month-select': makeEl('select'),
  'cal-year': makeEl('div')
};
elements['calendar-days'].id = 'calendar-days';
elements['month-select'].id = 'month-select';
elements['cal-year'].id = 'cal-year';
const context = {
  window: { location: { pathname: '/mlb-previews.html', href: '', replace() {} } },
  document: {
    readyState: 'loading',
    body: makeEl('body'),
    getElementById(id) { return elements[id] || null; },
    querySelector() { return null; },
    createElement: makeEl,
    addEventListener() {}
  },
  console,
  Date
};
context.window.FORCED_PAGE_DATE = targetMonth + '-15';
vm.createContext(context);
vm.runInContext(source, context);
if (typeof context.renderCalendar !== 'function') throw new Error('renderCalendar missing');
context.renderCalendar(targetMonth);
const days = cells.filter(c => c.className && !c.className.includes('empty')).map(c => Number(c.textContent));
const [year, month] = targetMonth.split('-').map(Number);
const expected = new Date(year, month, 0).getDate();
if (days.length !== expected) throw new Error(`${calendarPath} ${targetMonth}: expected ${expected} days, rendered ${days.length}`);
for (let i = 1; i <= expected; i++) {
  if (days[i - 1] !== i) throw new Error(`${calendarPath} ${targetMonth}: missing or misordered day ${i}`);
}
"""
    for sport, rel_path in CALENDAR_JS.items():
        calendar_path = os.path.join(REPO_ROOT, rel_path)
        if not os.path.exists(calendar_path):
            continue
        entries = parse_calendar_entries(sport)
        months = sorted({date_iso[:7] for date_iso, _page, _title in entries})
        for month in months:
            try:
                subprocess.run(
                    ['node', '-e', node_script, calendar_path, month],
                    check=True,
                    capture_output=True,
                    text=True,
                    cwd=REPO_ROOT,
                )
            except (OSError, subprocess.CalledProcessError) as exc:
                detail = getattr(exc, 'stderr', '') or getattr(exc, 'stdout', '') or str(exc)
                errors.append(f"{sport}: calendar render failed for {month}: {detail.strip()}")
    return errors


def find_sport_page(sport, date, all_files):
    """Check if a dedicated page exists for this sport on this date."""
    date_iso = date.strftime('%Y-%m-%d')
    calendar_page = find_calendar_page(sport, date_iso)
    if calendar_page:
        return calendar_page

    date_patterns = date_to_filename_patterns(date)
    sport_patterns = SPORT_PATTERNS[sport]

    for filename in all_files:
        fname_lower = filename.lower()
        # Check if filename contains the sport keyword
        has_sport = any(re.search(p, fname_lower) for p in sport_patterns)
        if not has_sport:
            continue
        # Check if filename contains the date
        has_date = any(dp in fname_lower for dp in date_patterns)
        if not has_date:
            continue
        # Skip redirect stubs (they're tiny <15 lines)
        filepath = os.path.join(REPO_ROOT, filename)
        try:
            size = os.path.getsize(filepath)
            if size < 1000:  # Redirect stubs are tiny
                continue
        except OSError:
            continue
        return filename
    return None


def check_date(date, all_files):
    """Check all active sports for a given date. Returns (missing, found) lists."""
    active = get_active_sports(date)
    missing = []
    found = []
    calendar_missing = []
    date_iso = date.strftime('%Y-%m-%d')

    for sport in active:
        if date_iso in NO_GAME_DATES.get(sport, set()):
            # Verified league off-day: no game scheduled, so no page is owed.
            continue
        page = find_sport_page(sport, date, all_files)
        if page:
            found.append((sport, page))
        else:
            missing.append(sport)
            continue

        calendar_path = os.path.join(REPO_ROOT, CALENDAR_JS[sport])
        try:
            with open(calendar_path, 'r', encoding='utf-8', errors='ignore') as f:
                calendar_data = f.read()
            if f'date: "{date_iso}"' not in calendar_data:
                calendar_missing.append((sport, CALENDAR_JS[sport]))
        except OSError:
            calendar_missing.append((sport, CALENDAR_JS[sport]))

    return missing, found, calendar_missing


def main():
    # Parse args
    dates_to_check = []
    today_date = datetime.now().date()
    if len(sys.argv) > 1:
        if sys.argv[1] == '--range':
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 3
            today = datetime.now()
            for i in range(days):
                dates_to_check.append(today - timedelta(days=i))
        else:
            try:
                dates_to_check.append(datetime.strptime(sys.argv[1], '%Y-%m-%d'))
            except ValueError:
                print(f"Invalid date format: {sys.argv[1]}. Use YYYY-MM-DD.")
                return 1
    else:
        dates_to_check.append(datetime.now())

    # Get all HTML files in repo root
    all_files = [f for f in os.listdir(REPO_ROOT) if f.endswith('.html')]

    has_errors = False

    print("=" * 65)
    print("  SLATE COMPLETENESS VALIDATOR")
    print("  Checking that ALL active sports have pages")
    print("=" * 65)

    integrity_errors = validate_calendar_integrity()
    if integrity_errors:
        has_errors = True
        print("\n  Calendar integrity errors:")
        for error in integrity_errors:
            print(f"  [X]  {error}")

    render_errors = validate_calendar_rendering()
    if render_errors:
        has_errors = True
        print("\n  Calendar rendering errors:")
        for error in render_errors:
            print(f"  [X]  {error}")

    for date in dates_to_check:
        date_str = date.strftime('%A, %B %d, %Y')
        print(f"\n  Date: {date_str}")
        print(f"  {'-' * 55}")

        if date.date() == today_date:
            print("  [SKIP] Current-day slate pages may not be published yet.")
            print("  Historical completeness checks start with past dates only.")
            continue

        missing, found, calendar_missing = check_date(date, all_files)

        for sport, page in found:
            print(f"  [OK] {sport:8s} -> {page}")

        for sport in missing:
            print(f"  [X]  {sport:8s} -> MISSING! No page found for this date.")
            has_errors = True

        for sport, calendar_path in calendar_missing:
            print(f"  [X]  {sport:8s} -> PAGE EXISTS BUT CALENDAR IS MISSING {date.strftime('%Y-%m-%d')} in {calendar_path}.")
            has_errors = True

        if not missing and not calendar_missing:
            print(f"  All {len(found)} active sports covered and present in calendars.")
        else:
            print(f"\n  WARNING: slate/calendar coverage failed.")
            if missing:
                print(f"  Missing pages: {', '.join(missing)}")
            if calendar_missing:
                print(f"  Missing calendar dates: {', '.join(s for s, _ in calendar_missing)}")

    print()
    if has_errors:
        print("=" * 65)
        print("  [FAILED] SLATE IS INCOMPLETE")
        print("  Create missing pages and run scripts/sync_calendars.py before pushing.")
        print("=" * 65)
        return 1
    else:
        print("=" * 65)
        print("  [PASSED] All active sports have pages.")
        print("=" * 65)
        return 0


if __name__ == '__main__':
    sys.exit(main())
