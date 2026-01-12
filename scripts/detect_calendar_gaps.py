#!/usr/bin/env python3
"""
CALENDAR GAP DETECTION SCRIPT
Created: January 11, 2026

This script detects:
1. Pages with generic "Archive - Page X" titles (BLOCKED by pre-commit)
2. Missing dates in the calendar (gaps between oldest and newest)
3. Duplicate dates (multiple pages for same date)

Run this BEFORE committing to catch issues early.
"""

import os
import re
from datetime import datetime, timedelta
from collections import defaultdict

REPO_ROOT = r'C:\Users\Nima\nimadamus.github.io'

SPORTS = ['nba', 'nhl', 'nfl', 'ncaab', 'ncaaf', 'mlb', 'soccer']

# Regex to extract date from title
DATE_PATTERN = re.compile(
    r'<title>.*?(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s*(\d{4})',
    re.IGNORECASE
)

# Regex to detect generic titles
GENERIC_PATTERN = re.compile(r'<title>.*Archive\s*-\s*Page\s*\d+', re.IGNORECASE)

def parse_date_from_title(title_match):
    """Convert month name + day + year to datetime."""
    month_name, day, year = title_match.groups()
    month_map = {
        'january': 1, 'february': 2, 'march': 3, 'april': 4,
        'may': 5, 'june': 6, 'july': 7, 'august': 8,
        'september': 9, 'october': 10, 'november': 11, 'december': 12
    }
    month = month_map[month_name.lower()]
    return datetime(int(year), month, int(day))

def check_sport(sport):
    """Check all pages for a sport and return issues found."""
    issues = {
        'generic_titles': [],
        'missing_dates': [],
        'duplicate_dates': [],
        'dates_found': {}
    }

    # Find all pages for this sport
    pages = []
    for filename in os.listdir(REPO_ROOT):
        if filename.startswith(sport) and filename.endswith('.html'):
            # Skip records and calendar files
            if 'records' in filename or 'calendar' in filename or 'archive' in filename:
                continue
            pages.append(filename)

    # Check each page
    date_to_pages = defaultdict(list)

    for page in pages:
        filepath = os.path.join(REPO_ROOT, page)
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Check for generic title
            if GENERIC_PATTERN.search(content):
                issues['generic_titles'].append(page)
                continue

            # Extract date from title
            match = DATE_PATTERN.search(content)
            if match:
                date = parse_date_from_title(match)
                date_str = date.strftime('%Y-%m-%d')
                date_to_pages[date_str].append(page)
                issues['dates_found'][page] = date_str
            else:
                # No date found in title
                issues['generic_titles'].append(f"{page} (no date in title)")

        except Exception as e:
            print(f"  Error reading {page}: {e}")

    # Find duplicates
    for date_str, page_list in date_to_pages.items():
        if len(page_list) > 1:
            issues['duplicate_dates'].append((date_str, page_list))

    # Find gaps (only if we have at least 2 dates)
    if len(date_to_pages) >= 2:
        dates = sorted([datetime.strptime(d, '%Y-%m-%d') for d in date_to_pages.keys()])
        oldest = dates[0]
        newest = dates[-1]

        current = oldest
        while current <= newest:
            date_str = current.strftime('%Y-%m-%d')
            if date_str not in date_to_pages:
                issues['missing_dates'].append(date_str)
            current += timedelta(days=1)

    return issues

def main():
    print("=" * 60)
    print("CALENDAR GAP DETECTION REPORT")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    all_clear = True

    for sport in SPORTS:
        print(f"\n{'='*20} {sport.upper()} {'='*20}")
        issues = check_sport(sport)

        # Report generic titles (CRITICAL)
        if issues['generic_titles']:
            all_clear = False
            print(f"\n[X] CRITICAL - Generic/Missing Date Titles:")
            for page in issues['generic_titles']:
                print(f"    - {page}")

        # Report duplicates (WARNING)
        if issues['duplicate_dates']:
            all_clear = False
            print(f"\n[!] WARNING - Duplicate Dates:")
            for date_str, page_list in issues['duplicate_dates']:
                print(f"    - {date_str}: {', '.join(page_list)}")

        # Report gaps (INFO - some gaps are expected for days with no games)
        if issues['missing_dates']:
            # Only show recent gaps (last 14 days)
            today = datetime.now()
            recent_gaps = [d for d in issues['missing_dates']
                          if (today - datetime.strptime(d, '%Y-%m-%d')).days <= 14]
            if recent_gaps:
                print(f"\n[?] Recent Gaps (last 14 days) - may be intentional:")
                for date_str in recent_gaps[-10:]:  # Show last 10
                    print(f"    - {date_str}")

        # Summary
        page_count = len(issues['dates_found'])
        if page_count > 0:
            dates = sorted(issues['dates_found'].values())
            print(f"\n  Pages found: {page_count}")
            print(f"  Date range: {dates[0]} to {dates[-1]}")

        if not issues['generic_titles'] and not issues['duplicate_dates']:
            print(f"\n  [OK] No critical issues found")

    print("\n" + "=" * 60)
    if all_clear:
        print("[OK] ALL SPORTS CALENDARS ARE HEALTHY")
    else:
        print("[X] ISSUES FOUND - SEE ABOVE FOR DETAILS")
        print("\nTo fix generic titles, edit each file's <title> tag to include the date:")
        print("  <title>NBA Analysis - January 12, 2026 | BetLegend</title>")
    print("=" * 60)

    return 0 if all_clear else 1

if __name__ == '__main__':
    exit(main())
