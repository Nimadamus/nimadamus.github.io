#!/usr/bin/env python3
"""
update_sport_redirects.py - Updates JS redirects on main sport pages

After each SLATE run, the main sport pages (nba.html, nhl.html, etc.) need
their JavaScript redirects updated to point to the newest keyword-rich archive page.

This ensures users who click "NBA" in the nav see the keyword-rich URL in their browser.

Usage:
    python scripts/update_sport_redirects.py

    This script automatically detects the latest archive page for each sport
    by scanning the repo directory for dated sport pages.

    Or specify manually:
    python scripts/update_sport_redirects.py --nba celtics-depleted-nba-march-8-2026.html --nhl lightning-nhl-march-8-2026.html
"""

import os
import re
import sys
import glob
from datetime import datetime

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Sport config: main page -> pattern to find archive pages
SPORT_CONFIG = {
    'nba': {
        'main_page': 'nba.html',
        'patterns': [r'-nba-\w+-\d+-\d+\.html$'],
        'exclude': ['nba.html', 'nba-calendar.js'],
    },
    'nhl': {
        'main_page': 'nhl.html',
        'patterns': [r'-nhl-\w+-\d+-\d+\.html$'],
        'exclude': ['nhl.html', 'nhl-calendar.js'],
    },
    'ncaab': {
        'main_page': 'ncaab.html',
        'patterns': [r'-ncaab-\w+-\d+-\d+\.html$', r'-college-basketball-\w+-\d+-\d+\.html$'],
        'exclude': ['ncaab.html'],
    },
    'soccer': {
        'main_page': 'soccer.html',
        'patterns': [r'-soccer-\w+-\d+-\d+\.html$'],
        'exclude': ['soccer.html'],
    },
    'mlb': {
        'main_page': 'mlb.html',
        'patterns': [r'-mlb-\w+-\d+-\d+\.html$'],
        'exclude': ['mlb.html'],
    },
    'nfl': {
        'main_page': 'nfl.html',
        'patterns': [r'-nfl-\w+-\d+-\d+\.html$'],
        'exclude': ['nfl.html'],
    },
    'ncaaf': {
        'main_page': 'ncaaf.html',
        'patterns': [r'-college-football-\w+-\d+-\d+\.html$', r'-ncaaf-\w+-\d+-\d+\.html$'],
        'exclude': ['ncaaf.html'],
    },
}

# Month name to number mapping
MONTH_MAP = {
    'january': 1, 'february': 2, 'march': 3, 'april': 4,
    'may': 5, 'june': 6, 'july': 7, 'august': 8,
    'september': 9, 'october': 10, 'november': 11, 'december': 12
}


def extract_date_from_filename(filename):
    """Extract date from a keyword-rich filename like xxx-nba-march-8-2026.html"""
    # Match pattern: month-day-year at end of filename (before .html)
    match = re.search(r'(\w+)-(\d{1,2})-(\d{4})\.html$', filename)
    if match:
        month_str = match.group(1).lower()
        day = int(match.group(2))
        year = int(match.group(3))
        month = MONTH_MAP.get(month_str)
        if month:
            try:
                return datetime(year, month, day)
            except ValueError:
                pass
    return None


def find_latest_archive_page(sport_key):
    """Find the most recent archive page for a given sport."""
    config = SPORT_CONFIG[sport_key]
    all_html = glob.glob(os.path.join(REPO_DIR, '*.html'))

    candidates = []
    for filepath in all_html:
        filename = os.path.basename(filepath)
        if filename in config['exclude']:
            continue

        # Check if filename matches any of the sport's patterns
        matched = False
        for pattern in config['patterns']:
            if re.search(pattern, filename):
                matched = True
                break

        if not matched:
            continue

        # Extract date from filename
        date = extract_date_from_filename(filename)
        if date:
            candidates.append((date, filename))

    if not candidates:
        return None

    # Sort by date descending, return newest
    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1]


def update_redirect(main_page_path, archive_filename):
    """Add or update the JS redirect in a main sport page."""
    with open(main_page_path, 'r', encoding='utf-8') as f:
        content = f.read()

    redirect_line = f"<script>window.location.replace('{archive_filename}');</script>"

    # Check if redirect already exists
    redirect_pattern = r"<script>window\.location\.replace\('[^']+'\);</script>"
    if re.search(redirect_pattern, content):
        # Update existing redirect
        new_content = re.sub(redirect_pattern, redirect_line, content)
    else:
        # Insert redirect after canonical tag
        canonical_end = content.find('rel="canonical"/>')
        if canonical_end != -1:
            insert_pos = canonical_end + len('rel="canonical"/>')
            new_content = content[:insert_pos] + '\n' + redirect_line + content[insert_pos:]
        else:
            # Fallback: insert after <meta charset="utf-8"/>
            charset_end = content.find('<meta charset="utf-8"/>')
            if charset_end != -1:
                insert_pos = charset_end + len('<meta charset="utf-8"/>')
                new_content = content[:insert_pos] + '\n' + redirect_line + content[insert_pos:]
            else:
                print(f"  [ERROR] Could not find insertion point in {main_page_path}")
                return False

    if new_content != content:
        with open(main_page_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    return False


def main():
    print("=" * 60)
    print("  SPORT PAGE REDIRECT UPDATER")
    print("=" * 60)
    print()

    # Parse manual overrides from command line
    manual = {}
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i].startswith('--'):
            sport = args[i][2:]
            if i + 1 < len(args) and sport in SPORT_CONFIG:
                manual[sport] = args[i + 1]
                i += 2
                continue
        i += 1

    updated = 0
    skipped = 0

    for sport_key, config in SPORT_CONFIG.items():
        main_page = config['main_page']
        main_page_path = os.path.join(REPO_DIR, main_page)

        if not os.path.exists(main_page_path):
            continue

        # Use manual override or auto-detect
        if sport_key in manual:
            archive_file = manual[sport_key]
        else:
            archive_file = find_latest_archive_page(sport_key)

        if not archive_file:
            print(f"  [{main_page}] No archive page found - skipping")
            skipped += 1
            continue

        # Verify archive page exists
        archive_path = os.path.join(REPO_DIR, archive_file)
        if not os.path.exists(archive_path):
            print(f"  [{main_page}] Archive page not found: {archive_file} - skipping")
            skipped += 1
            continue

        # Update redirect
        changed = update_redirect(main_page_path, archive_file)
        if changed:
            print(f"  [OK] {main_page} -> {archive_file}")
            updated += 1
        else:
            print(f"  [--] {main_page} already points to {archive_file}")
            skipped += 1

    print()
    print(f"  Updated: {updated} | Already correct: {skipped}")
    print("=" * 60)

    return 0


if __name__ == '__main__':
    sys.exit(main())
