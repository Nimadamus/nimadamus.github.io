#!/usr/bin/env python3
"""
update_sport_redirects.py - Updates sport nav links across ALL pages
=====================================================================

Instead of adding JS redirects to main sport pages (which break calendars),
this script updates the nav bar links across the ENTIRE site to point
directly to the latest keyword-rich archive page for each sport.

How it works:
1. Auto-detects the latest archive page for each sport
2. Detects the CURRENT nav link target from index.html
3. Replaces old target with new target across ALL HTML files
4. PRESERVES canonical tags, og:url tags, mainEntityOfPage, and calendar data
5. Cleans up any leftover JS redirects from main sport pages

Usage:
    python scripts/update_sport_redirects.py

    This script automatically detects the latest archive page for each sport
    by scanning the repo directory for dated sport pages.

    Or specify manually:
    python scripts/update_sport_redirects.py --nba celtics-nba-march-8-2026.html --nhl lightning-nhl-march-8-2026.html
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
        'nav_text': 'NBA',
        'patterns': [r'-nba-\w+-\d+-\d+\.html$'],
        'exclude': ['nba.html', 'nba-calendar.js', 'nba-records.html'],
    },
    'nhl': {
        'main_page': 'nhl.html',
        'nav_text': 'NHL',
        'patterns': [r'-nhl-\w+-\d+-\d+\.html$'],
        'exclude': ['nhl.html', 'nhl-calendar.js', 'nhl-records.html'],
    },
    'ncaab': {
        'main_page': 'ncaab.html',
        'nav_text': 'NCAAB',
        'patterns': [r'-ncaab-\w+-\d+-\d+\.html$', r'-college-basketball-\w+-\d+-\d+\.html$'],
        'exclude': ['ncaab.html', 'ncaab-records.html'],
    },
    'soccer': {
        'main_page': 'soccer.html',
        'nav_text': 'Soccer',
        'patterns': [r'-soccer-\w+-\d+-\d+\.html$'],
        'exclude': ['soccer.html', 'soccer-records.html'],
    },
    'mlb': {
        'main_page': 'mlb.html',
        'nav_text': 'MLB',
        'patterns': [r'-mlb-\w+-\d+-\d+\.html$'],
        'exclude': ['mlb.html', 'mlb-records.html'],
    },
    'nfl': {
        'main_page': 'nfl.html',
        'nav_text': 'NFL',
        'patterns': [r'-nfl-\w+-\d+-\d+\.html$'],
        'exclude': ['nfl.html', 'nfl-records.html'],
    },
    'ncaaf': {
        'main_page': 'ncaaf.html',
        'nav_text': 'NCAAF',
        'patterns': [r'-college-football-\w+-\d+-\d+\.html$', r'-ncaaf-\w+-\d+-\d+\.html$'],
        'exclude': ['ncaaf.html', 'ncaaf-records.html'],
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

        matched = False
        for pattern in config['patterns']:
            if re.search(pattern, filename):
                matched = True
                break

        if not matched:
            continue

        date = extract_date_from_filename(filename)
        if date:
            candidates.append((date, filename))

    if not candidates:
        return None

    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1]


def detect_current_nav_target(sport_key):
    """Detect the current nav link target for a sport from index.html."""
    config = SPORT_CONFIG[sport_key]
    nav_text = config['nav_text']
    main_page = config['main_page']

    index_path = os.path.join(REPO_DIR, 'index.html')
    if not os.path.exists(index_path):
        return main_page

    with open(index_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # Look for nav link with exact sport text
    # Pattern: href="FILENAME">SPORT_TEXT</a>
    pattern = rf'href="([^"]+)"[^>]*>{re.escape(nav_text)}</a>'
    match = re.search(pattern, content)
    if match:
        return match.group(1)

    return main_page


def remove_js_redirect(main_page_path):
    """Remove any JS redirect OR meta http-equiv refresh from a main sport page.

    Rolling Hub is retired -- sport landing pages must not redirect to
    *-previews hubs. Both the <script>window.location.replace()</script> and
    the <meta http-equiv="refresh"> forms are stripped.
    """
    with open(main_page_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    js_pattern = r"\n?<script>window\.location\.replace\('[^']+'\);</script>"
    meta_pattern = r'\n?<meta\s+http-equiv="refresh"\s+content="0;url=[^"]+"\s*/?>'
    new_content = re.sub(js_pattern, '', content)
    new_content = re.sub(meta_pattern, '', new_content)

    if new_content != content:
        with open(main_page_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    return False


def update_nav_links(old_target, new_target):
    """Replace old nav link target with new target across ALL HTML files.

    Preserves:
    - canonical tags (never touched)
    - og:url tags (never touched)
    - mainEntityOfPage in JSON-LD (never touched)
    - Calendar data entries (never touched)
    """
    total_files = 0
    total_changes = 0

    for root, dirs, files in os.walk(REPO_DIR):
        dirs[:] = [d for d in dirs if d not in ('.git', 'node_modules')]

        for f in files:
            if not (f.endswith('.html') or f.endswith('.js')):
                continue

            filepath = os.path.join(root, f)

            with open(filepath, 'r', encoding='utf-8', errors='ignore') as fh:
                content = fh.read()

            if old_target not in content:
                continue

            original = content
            lines = content.split('\n')
            new_lines = []
            changes = 0

            for line in lines:
                # SKIP canonical lines
                if 'rel="canonical"' in line:
                    new_lines.append(line)
                    continue

                # SKIP og:url lines
                if 'og:url' in line:
                    new_lines.append(line)
                    continue

                # SKIP mainEntityOfPage in JSON-LD
                if 'mainEntityOfPage' in line:
                    new_lines.append(line)
                    continue

                # SKIP calendar data entries (ARCHIVE_DATA or sport calendar JS)
                if ('page:' in line or 'page "' in line) and old_target in line:
                    # This looks like a calendar data entry - preserve it
                    if any(kw in filepath for kw in ['calendar', 'data']):
                        new_lines.append(line)
                        continue

                # Replace old target with new target
                if old_target in line:
                    new_line = line.replace(old_target, new_target)
                    changes += line.count(old_target)
                    new_lines.append(new_line)
                else:
                    new_lines.append(line)

            new_content = '\n'.join(new_lines)

            if new_content != original:
                with open(filepath, 'w', encoding='utf-8') as fh:
                    fh.write(new_content)
                total_files += 1
                total_changes += changes
                if total_files <= 20:
                    print(f"  Updated: {os.path.relpath(filepath, REPO_DIR)} ({changes} link(s))")

    if total_files > 20:
        print(f"  ... and {total_files - 20} more files")

    return total_files, total_changes


def main():
    print("=" * 60)
    print("  SPORT NAV LINK UPDATER")
    print("=" * 60)
    print()
    print("  Strategy: Update nav links across ALL pages")
    print("  (No JS redirects - calendars stay functional)")
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

    grand_total_files = 0
    grand_total_changes = 0

    for sport_key, config in SPORT_CONFIG.items():
        main_page = config['main_page']
        main_page_path = os.path.join(REPO_DIR, main_page)

        # Step 1: Clean up any JS redirect on main sport page
        if os.path.exists(main_page_path):
            if remove_js_redirect(main_page_path):
                print(f"  [CLEANUP] Removed JS redirect from {main_page}")

        # Step 2: Find latest archive page
        if sport_key in manual:
            archive_file = manual[sport_key]
        else:
            archive_file = find_latest_archive_page(sport_key)

        if not archive_file:
            print(f"  [{sport_key.upper()}] No archive page found - skipping")
            continue

        # Verify archive page exists
        archive_path = os.path.join(REPO_DIR, archive_file)
        if not os.path.exists(archive_path):
            print(f"  [{sport_key.upper()}] Archive not found: {archive_file} - skipping")
            continue

        # Step 3: Detect current nav target
        current_target = detect_current_nav_target(sport_key)

        if current_target == archive_file:
            print(f"  [{sport_key.upper()}] Already pointing to: {archive_file}")
            continue

        # Step 4: Update nav links across all pages
        print(f"\n  [{sport_key.upper()}] {current_target} -> {archive_file}")
        files_updated, changes_made = update_nav_links(current_target, archive_file)
        grand_total_files += files_updated
        grand_total_changes += changes_made
        print(f"  [{sport_key.upper()}] {files_updated} files, {changes_made} links updated")

    print()
    print("=" * 60)
    print(f"  Total files updated: {grand_total_files}")
    print(f"  Total links replaced: {grand_total_changes}")
    print("  Canonical/og:url tags: PRESERVED")
    print("  Calendar data: PRESERVED")
    print("  JS redirects: REMOVED (calendars work)")
    print("=" * 60)

    return 0


if __name__ == '__main__':
    sys.exit(main())
