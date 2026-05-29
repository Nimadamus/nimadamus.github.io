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

    if failures:
        print("\nCalendar continuity failed. Run sync_calendars.py and fix missing dates before publish.")
        return 1

    print("\n[PASSED] Calendar continuity intact.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
