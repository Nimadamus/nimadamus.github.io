#!/usr/bin/env python3
"""
Validate BetLegend sport calendar continuity.

This catches the failure mode where a published daily sport page exists or is
archived, but the generated calendar JS no longer exposes that date.
"""

import argparse
import json
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_DIR / "scripts"

SPORTS = {
    "nba": "nba-calendar.js",
    "nhl": "nhl-calendar.js",
    "mlb": "mlb-calendar.js",
    "soccer": "soccer-calendar.js",
    "ncaab": "ncaab-calendar.js",
    "nfl": "nfl-calendar.js",
    "ncaaf": "ncaaf-calendar.js",
}

# Locked regression dates that must always survive in each sport's calendar.
# NCAAB is intentionally absent: college basketball is OFFSEASON from mid-April
# through October, so there is no May 16 NCAAB page and demanding one keeps the
# continuity gate permanently red (false positive). Only force dates that have a
# real recovery page in REQUIRED_DATE_TARGETS (sync_calendars.py).
REQUIRED_REGRESSION_DATES = {
    "nba": {"2026-05-16"},
    "nhl": {"2026-05-16"},
    "mlb": {"2026-05-16"},
    "soccer": {"2026-05-16"},
}


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("lookback", nargs="?", type=int, default=45)
    parser.add_argument("--today", default=datetime.now().date().isoformat())
    return parser.parse_args()


def calendar_dates(js_name):
    path = SCRIPTS_DIR / js_name
    if not path.exists():
        return set()
    text = path.read_text(encoding="utf-8", errors="ignore")
    return set(re.findall(r'date:\s*"(\d{4}-\d{2}-\d{2})"', text))


def manifest_dates():
    path = SCRIPTS_DIR / "hub-archive-manifest.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def forced_page_dates_for_sport(sport):
    dates = set()
    patterns = {
        "nba": ["*-nba.html", "*-nba-*.html", "nba*.html"],
        "nhl": ["*-nhl.html", "*-nhl-*.html", "nhl*.html"],
        "mlb": ["*-mlb.html", "*-mlb-*.html", "mlb*.html"],
        "soccer": ["*-soccer.html", "*-soccer-*.html", "soccer*.html"],
        "ncaab": ["*-college-basketball.html", "*-college-basketball-*.html", "ncaab*.html"],
        "nfl": ["*-nfl.html", "*-nfl-*.html", "nfl*.html"],
        "ncaaf": ["*-college-football.html", "*-college-football-*.html", "ncaaf*.html"],
    }.get(sport, [])
    seen = set()
    for pattern in patterns:
        for path in REPO_DIR.glob(pattern):
            if path.name in seen:
                continue
            seen.add(path.name)
            text = path.read_text(encoding="utf-8", errors="ignore")
            match = re.search(r"FORCED_PAGE_DATE\s*=\s*['\"](\d{4}-\d{2}-\d{2})['\"]", text)
            if match:
                dates.add(match.group(1))
    return dates


def recent_dates(days, today_iso):
    today = datetime.fromisoformat(today_iso).date()
    return {(today - timedelta(days=i)).isoformat() for i in range(days)}


# Sport -> rolling hub page. A hub bakes in the last published article; it must
# only ever occupy a calendar cell on the SAME date as its own FORCED_PAGE_DATE.
# If a hub is dated on any other day (e.g. "today" because the date couldn't be
# read), a weeks-old baked game gets surfaced as the current board. This is the
# June 1, 2026 stale-ECF-Game-5 failure; this gate blocks it permanently.
HUB_PAGES = {
    "nba": "nba-previews.html",
    "nhl": "nhl-previews.html",
    "mlb": "mlb-previews.html",
    "soccer": "soccer-previews.html",
    "ncaab": "college-basketball-previews.html",
}


def hub_calendar_dates(js_name, hub_page):
    """Return the set of dates the hub page is listed under in the calendar JS."""
    path = SCRIPTS_DIR / js_name
    if not path.exists():
        return set()
    text = path.read_text(encoding="utf-8", errors="ignore")
    return set(
        re.findall(
            r'date:\s*"(\d{4}-\d{2}-\d{2})",\s*page:\s*"'
            + re.escape(hub_page) + r'"',
            text,
        )
    )


def hub_forced_date(hub_page):
    """Read the hub's own FORCED_PAGE_DATE (whole file)."""
    path = REPO_DIR / hub_page
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8", errors="ignore")
    match = re.search(r"FORCED_PAGE_DATE\s*=\s*['\"](\d{4}-\d{2}-\d{2})['\"]", text)
    return match.group(1) if match else None


def hub_staleness_failures():
    """A hub may only be calendar-dated on its own FORCED_PAGE_DATE."""
    problems = []
    for sport, hub_page in HUB_PAGES.items():
        js_name = SPORTS.get(sport)
        if not js_name:
            continue
        forced = hub_forced_date(hub_page)
        for dated in sorted(hub_calendar_dates(js_name, hub_page)):
            if dated != forced:
                problems.append((sport, hub_page, dated, forced))
    return problems


def main():
    args = parse_args()
    lookback = args.lookback
    manifest = manifest_dates()
    recent = recent_dates(lookback, args.today)
    failures = []

    print("=" * 64)
    print(f"BetLegend Calendar Continuity Validator ({lookback}-day lookback)")
    print("=" * 64)

    for sport, js_name in SPORTS.items():
        expected = set(manifest.get(sport, [])) | forced_page_dates_for_sport(sport)
        expected = {d for d in expected if d in recent}
        expected |= {d for d in REQUIRED_REGRESSION_DATES.get(sport, set()) if d <= args.today}
        actual = calendar_dates(js_name)
        missing = sorted(expected - actual)
        if missing:
            failures.append((sport, missing))
            print(f"[FAIL] {sport.upper()} missing: {', '.join(missing)}")
        else:
            print(f"[OK] {sport.upper()} continuity intact ({len(expected)} recent expected dates)")

    stale_hubs = hub_staleness_failures()
    for sport, hub_page, dated, forced in stale_hubs:
        forced_desc = forced or "none (no FORCED_PAGE_DATE)"
        print(f"[FAIL] {sport.upper()} hub {hub_page} is calendar-dated {dated} "
              f"but its baked FORCED_PAGE_DATE is {forced_desc} -> STALE HUB ON WRONG DAY")

    if failures or stale_hubs:
        if failures:
            print("\nCalendar continuity failed. Run sync_calendars.py and fix missing dates before publish.")
        if stale_hubs:
            print("\nStale-hub gate failed. A *-previews.html hub may only be dated on its own "
                  "FORCED_PAGE_DATE. Re-run sync_calendars.py (it now drops undated hubs) and/or "
                  "set the hub's FORCED_PAGE_DATE to match the day it represents.")
        return 1

    print("\n[PASSED] Calendar continuity intact.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
