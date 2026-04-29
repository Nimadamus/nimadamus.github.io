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


def find_sport_page(sport, date, all_files):
    """Check if a dedicated page exists for this sport on this date.

    Updated April 29, 2026: URLs no longer contain dates (Nima rule). When the
    filename has no date pattern but matches the sport, fall back to scanning
    FORCED_PAGE_DATE / dateModified inside the file. This keeps the validator
    working under the new no-dates-in-URLs convention.
    """
    date_patterns = date_to_filename_patterns(date)
    sport_patterns = SPORT_PATTERNS[sport]
    iso_date = date.strftime('%Y-%m-%d')

    for filename in all_files:
        fname_lower = filename.lower()
        # Check if filename contains the sport keyword
        has_sport = any(re.search(p, fname_lower) for p in sport_patterns)
        if not has_sport:
            continue
        # Skip redirect stubs (they're tiny <15 lines)
        filepath = os.path.join(REPO_ROOT, filename)
        try:
            size = os.path.getsize(filepath)
            if size < 1000:  # Redirect stubs are tiny
                continue
        except OSError:
            continue
        # Path 1: filename contains the date
        if any(dp in fname_lower for dp in date_patterns):
            return filename
        # Path 2: filename has no date — fall back to file content
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(8000)  # head is enough; FORCED_PAGE_DATE lives in <head>
        except OSError:
            continue
        if f"FORCED_PAGE_DATE = '{iso_date}'" in content or \
           f'FORCED_PAGE_DATE = "{iso_date}"' in content or \
           f'"datePublished":"{iso_date}' in content or \
           f'"datePublished": "{iso_date}' in content:
            return filename
    return None


def check_date(date, all_files):
    """Check all active sports for a given date. Returns (missing, found) lists."""
    active = get_active_sports(date)
    missing = []
    found = []

    for sport in active:
        page = find_sport_page(sport, date, all_files)
        if page:
            found.append((sport, page))
        else:
            missing.append(sport)

    return missing, found


def main():
    # Parse args
    dates_to_check = []
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

    for date in dates_to_check:
        date_str = date.strftime('%A, %B %d, %Y')
        print(f"\n  Date: {date_str}")
        print(f"  {'-' * 55}")

        missing, found = check_date(date, all_files)

        for sport, page in found:
            print(f"  [OK] {sport:8s} -> {page}")

        for sport in missing:
            print(f"  [X]  {sport:8s} -> MISSING! No page found for this date.")
            has_errors = True

        if not missing:
            print(f"  All {len(found)} active sports covered.")
        else:
            print(f"\n  WARNING: {len(missing)} sport(s) MISSING pages!")
            print(f"  Missing: {', '.join(missing)}")

    print()
    if has_errors:
        print("=" * 65)
        print("  [FAILED] SLATE IS INCOMPLETE")
        print("  Create pages for the missing sports before pushing.")
        print("=" * 65)
        return 1
    else:
        print("=" * 65)
        print("  [PASSED] All active sports have pages.")
        print("=" * 65)
        return 0


if __name__ == '__main__':
    sys.exit(main())
