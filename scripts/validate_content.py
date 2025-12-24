#!/usr/bin/env python3
"""
BETLEGEND CONTENT VALIDATOR
===========================
Run this BEFORE committing ANY changes.
This script checks for ALL known issues and BLOCKS bad content.

Usage: python scripts/validate_content.py
"""

import os
import re
import sys
from pathlib import Path

# Auto-detect repo directory
if sys.platform == 'win32':
    REPO_DIR = Path(r'C:\Users\Nima\nimadamus.github.io')
else:
    REPO_DIR = Path(__file__).parent.parent

ERRORS = []
WARNINGS = []

# ============================================================
# CHECK 1: PLACEHOLDER CONTENT
# ============================================================
PLACEHOLDER_PATTERNS = [
    r'coming soon',
    r'Matchup analysis coming',
    r'Analysis coming',
    r'Preview coming',
    r'\bTBD\b',
    r'\bTBA\b',
    r'\bN/A\b',
]

def check_placeholders():
    """Check for placeholder content in HTML files."""
    print("Checking for placeholder content...")

    sports_files = ['nba.html', 'nhl.html', 'ncaaf.html', 'ncaab.html', 'nfl.html', 'mlb.html']

    for filename in sports_files:
        filepath = REPO_DIR / filename
        if not filepath.exists():
            continue

        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        for pattern in PLACEHOLDER_PATTERNS:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                ERRORS.append(f"PLACEHOLDER in {filename}: Found '{matches[0]}'")

# ============================================================
# CHECK 2: COLLEGE LOGOS (must use numeric IDs)
# ============================================================
def check_college_logos():
    """Check that college logos use numeric ESPN IDs, not abbreviations."""
    print("Checking college logo URLs...")

    # Pattern for non-numeric college logo URLs
    bad_pattern = r'teamlogos/ncaa/500/([a-zA-Z][a-zA-Z0-9&;-]+)\.png'

    for filepath in REPO_DIR.glob('*.html'):
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        matches = re.findall(bad_pattern, content)
        for match in matches:
            # Skip if it's already numeric
            if match.isdigit():
                continue
            # Skip scoreboard paths (those are fine)
            if 'scoreboard' in match:
                continue
            ERRORS.append(f"BAD LOGO in {filepath.name}: Using '{match}' instead of numeric ID")

# ============================================================
# CHECK 3: CALENDAR SYNC
# ============================================================
def check_calendars():
    """Check that all sport pages are in their calendar JS files."""
    print("Checking calendar completeness...")

    sports = {
        'nba': 'nba-calendar.js',
        'nhl': 'nhl-calendar.js',
        'ncaab': 'ncaab-calendar.js',
        'ncaaf': 'ncaaf-calendar.js',
        'nfl': 'nfl-calendar.js',
        'mlb': 'mlb-calendar.js',
    }

    exclude_patterns = ['calendar', 'archive', 'records', 'index']

    for sport, calendar_file in sports.items():
        calendar_path = REPO_DIR / 'scripts' / calendar_file
        if not calendar_path.exists():
            WARNINGS.append(f"Calendar file missing: {calendar_file}")
            continue

        with open(calendar_path, 'r', encoding='utf-8') as f:
            calendar_content = f.read()

        # Find all sport pages
        for filepath in REPO_DIR.glob(f'{sport}*.html'):
            filename = filepath.name

            # Skip utility pages
            skip = any(p in filename.lower() for p in exclude_patterns)
            if skip:
                continue

            # Check if page is in calendar
            if filename not in calendar_content:
                WARNINGS.append(f"MISSING from calendar: {filename} not in {calendar_file}")

# ============================================================
# CHECK 4: NAV CONSISTENCY
# ============================================================
def check_nav_text():
    """Check for incorrect nav text like 'Overview' instead of 'Detailed Breakdown'."""
    print("Checking navigation text...")

    bad_patterns = [
        (r'>Overview<', 'Should be "Detailed Breakdown"'),
    ]

    for filepath in REPO_DIR.glob('*.html'):
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        for pattern, message in bad_patterns:
            if re.search(pattern, content):
                ERRORS.append(f"BAD NAV TEXT in {filepath.name}: {message}")

# ============================================================
# CHECK 5: FEATURED GAME LINKS
# ============================================================
def check_featured_game_links():
    """Check that featured game links are up to date."""
    print("Checking featured game links...")

    # Find the highest featured game page number
    featured_pages = list(REPO_DIR.glob('featured-game-of-the-day-page*.html'))
    if not featured_pages:
        return

    # Extract page numbers
    page_nums = []
    for fp in featured_pages:
        match = re.search(r'page(\d+)', fp.name)
        if match:
            page_nums.append(int(match.group(1)))

    if not page_nums:
        return

    latest_page = max(page_nums)
    latest_filename = f'featured-game-of-the-day-page{latest_page}.html'

    # Check a sample of files to ensure they link to the latest
    sample_files = ['index.html', 'nba.html', 'nfl.html']
    for filename in sample_files:
        filepath = REPO_DIR / filename
        if not filepath.exists():
            continue

        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # Find featured game links
        links = re.findall(r'featured-game-of-the-day-page(\d+)\.html', content)
        for link_num in links:
            if int(link_num) < latest_page - 1:  # Allow 1 page behind
                WARNINGS.append(f"OUTDATED LINK in {filename}: Links to page{link_num}, latest is page{latest_page}")

# ============================================================
# MAIN
# ============================================================
def main():
    print("=" * 60)
    print("BETLEGEND CONTENT VALIDATOR")
    print("=" * 60)
    print()

    check_placeholders()
    check_college_logos()
    check_calendars()
    check_nav_text()
    check_featured_game_links()

    print()
    print("=" * 60)

    if ERRORS:
        print(f"[X] ERRORS FOUND: {len(ERRORS)}")
        print("-" * 60)
        for error in ERRORS:
            print(f"  [X] {error}")
        print()

    if WARNINGS:
        print(f"[!] WARNINGS: {len(WARNINGS)}")
        print("-" * 60)
        for warning in WARNINGS:
            print(f"  [!] {warning}")
        print()

    if not ERRORS and not WARNINGS:
        print("[OK] ALL CHECKS PASSED!")
        print()
        return 0

    if ERRORS:
        print("=" * 60)
        print("[X] VALIDATION FAILED - FIX ERRORS BEFORE COMMITTING")
        print("=" * 60)
        return 1

    print("=" * 60)
    print("[!] WARNINGS FOUND - Review before committing")
    print("=" * 60)
    return 0

if __name__ == '__main__':
    sys.exit(main())
