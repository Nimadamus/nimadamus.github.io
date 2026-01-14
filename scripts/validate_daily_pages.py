#!/usr/bin/env python3
"""
Validate Daily Sports Pages Script
===================================
This script ensures that daily sports content has dedicated page files,
preventing content loss when main pages are updated.

The Problem (January 12, 2026):
- Content was added to main pages (nba.html, nhl.html, etc.) without creating
  dedicated page files (nba-page47.html, etc.)
- When the next day's content was added, January 12 content was overwritten
- Result: Lost all January 12 content

The Solution:
- This script validates that every date in the main pages has a corresponding
  dedicated page file in the archive
- If content exists in nba.html for date X, there MUST be an nba-page*.html
  file with the same date in its title

Usage:
    python scripts/validate_daily_pages.py

Returns exit code 1 if validation fails (blocks commit).
"""

import os
import re
import sys
from datetime import datetime, timedelta

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Sports to check
SPORTS = ['nba', 'nhl', 'ncaab', 'soccer']

def extract_date_from_title(filepath):
    """Extract date from page title tag."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # Look for date in title tag
        title_match = re.search(r'<title>.*?(\w+\s+\d{1,2},?\s+\d{4}).*?</title>', content, re.IGNORECASE)
        if title_match:
            date_str = title_match.group(1)
            # Try parsing various formats
            for fmt in ['%B %d, %Y', '%B %d %Y', '%b %d, %Y', '%b %d %Y']:
                try:
                    return datetime.strptime(date_str.replace(',', ''), fmt.replace(',', '')).strftime('%Y-%m-%d')
                except ValueError:
                    continue

        # Fallback: look for date in meta description
        meta_match = re.search(r'(\w+\s+\d{1,2},?\s+\d{4})', content)
        if meta_match:
            date_str = meta_match.group(1)
            for fmt in ['%B %d, %Y', '%B %d %Y', '%b %d, %Y', '%b %d %Y']:
                try:
                    return datetime.strptime(date_str.replace(',', ''), fmt.replace(',', '')).strftime('%Y-%m-%d')
                except ValueError:
                    continue
    except Exception as e:
        pass

    return None

def get_page_files_dates(sport):
    """Get all dates from page files for a sport."""
    dates = {}
    pattern = re.compile(rf'^{sport}-page\d+\.html$')

    for filename in os.listdir(REPO_ROOT):
        if pattern.match(filename):
            filepath = os.path.join(REPO_ROOT, filename)
            date = extract_date_from_title(filepath)
            if date:
                dates[date] = filename

    return dates

def validate_sport(sport):
    """Validate that main page date has a corresponding page file."""
    main_page = os.path.join(REPO_ROOT, f'{sport}.html')

    if not os.path.exists(main_page):
        return True, None, None

    main_date = extract_date_from_title(main_page)
    if not main_date:
        return True, None, None

    page_dates = get_page_files_dates(sport)

    if main_date in page_dates:
        return True, main_date, page_dates[main_date]
    else:
        return False, main_date, None

def main():
    print("=" * 60)
    print("DAILY SPORTS PAGE VALIDATION")
    print("Ensuring all daily content has dedicated page files")
    print("=" * 60)
    print()

    errors = []
    warnings = []

    for sport in SPORTS:
        valid, main_date, page_file = validate_sport(sport)

        if main_date:
            if valid:
                print(f"  ✓ {sport.upper()}: {main_date} → {page_file}")
            else:
                error_msg = f"{sport.upper()}: Main page has date {main_date} but NO dedicated page file exists!"
                errors.append(error_msg)
                print(f"  ✗ {error_msg}")
                print(f"    ACTION REQUIRED: Create {sport}-page[N].html with title containing '{main_date}'")
        else:
            print(f"  ? {sport.upper()}: Could not extract date from main page")

    print()

    if errors:
        print("=" * 60)
        print("[VALIDATION FAILED] Missing dedicated page files!")
        print("=" * 60)
        print()
        print("WHAT THIS MEANS:")
        print("  Content in main pages will be LOST when the next day's")
        print("  content is added. You MUST create dedicated page files.")
        print()
        print("HOW TO FIX:")
        for sport in SPORTS:
            valid, main_date, _ = validate_sport(sport)
            if not valid and main_date:
                # Find next available page number
                existing = [f for f in os.listdir(REPO_ROOT) if f.startswith(f'{sport}-page') and f.endswith('.html')]
                numbers = []
                for f in existing:
                    match = re.search(r'page(\d+)\.html', f)
                    if match:
                        numbers.append(int(match.group(1)))
                next_num = max(numbers) + 1 if numbers else 2
                print(f"  cp {sport}.html {sport}-page{next_num}.html")
                print(f"  # Then update canonical URL in {sport}-page{next_num}.html")
        print()
        return 1

    print("[OK] All daily content has dedicated page files!")
    return 0

if __name__ == '__main__':
    sys.exit(main())
