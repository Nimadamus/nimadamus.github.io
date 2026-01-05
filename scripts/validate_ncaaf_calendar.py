#!/usr/bin/env python3
"""
NCAAF Calendar Validation Script
Validates that:
1. All NCAAF pages have date mappings
2. Main page (ncaaf.html) date matches title
3. Archive pages are properly mapped
4. No placeholder content exists

Run this script to check for calendar issues before they go live.
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

SCRIPTS_DIR = REPO_DIR / 'scripts'

def extract_date_from_title(content):
    """Extract date from page title."""
    title_match = re.search(r'<title>([^<]+)</title>', content, re.I)
    if title_match:
        title = title_match.group(1)
        # Look for date patterns
        patterns = [
            r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s*(\d{4})',
            r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2}),?\s*(\d{4})'
        ]
        for pattern in patterns:
            match = re.search(pattern, title, re.I)
            if match:
                month_map = {
                    'january': '01', 'february': '02', 'march': '03', 'april': '04',
                    'may': '05', 'june': '06', 'july': '07', 'august': '08',
                    'september': '09', 'october': '10', 'november': '11', 'december': '12',
                    'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
                    'jun': '06', 'jul': '07', 'aug': '08', 'sep': '09',
                    'oct': '10', 'nov': '11', 'dec': '12'
                }
                month = month_map.get(match.group(1).lower())
                day = match.group(2).zfill(2)
                year = match.group(3)
                if month:
                    return f"{year}-{month}-{day}"
    return None

def load_calendar_data():
    """Load the ARCHIVE_DATA from ncaaf-calendar.js."""
    js_path = SCRIPTS_DIR / 'ncaaf-calendar.js'
    if not js_path.exists():
        return {}

    with open(js_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract entries
    entries = {}
    pattern = r'\{\s*date:\s*"([^"]+)",\s*page:\s*"([^"]+)",\s*title:\s*"([^"]+)"\s*\}'
    for match in re.finditer(pattern, content):
        date, page, title = match.groups()
        entries[page] = {'date': date, 'title': title}

    return entries

def validate():
    """Run all validations."""
    errors = []
    warnings = []

    print("=" * 60)
    print("NCAAF CALENDAR VALIDATION")
    print("=" * 60)

    # Load calendar data
    calendar_data = load_calendar_data()
    if not calendar_data:
        errors.append("Could not load ncaaf-calendar.js data")
        return errors, warnings

    print(f"\nLoaded {len(calendar_data)} entries from ncaaf-calendar.js")

    # 1. Check main ncaaf.html
    print("\n[1] Checking ncaaf.html...")
    main_page = REPO_DIR / 'ncaaf.html'
    if main_page.exists():
        with open(main_page, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        title_date = extract_date_from_title(content)
        calendar_entry = calendar_data.get('ncaaf.html')

        if not calendar_entry:
            errors.append("ncaaf.html is NOT in calendar data!")
        elif title_date and calendar_entry['date'] != title_date:
            errors.append(f"ncaaf.html date MISMATCH: title says {title_date}, calendar has {calendar_entry['date']}")
        elif not title_date:
            warnings.append("ncaaf.html title doesn't have a parseable date")
        else:
            print(f"  OK: ncaaf.html mapped to {calendar_entry['date']}")
    else:
        errors.append("ncaaf.html does not exist!")

    # 2. Check all ncaaf-page*.html files
    print("\n[2] Checking ncaaf-page*.html files...")
    page_files = list(REPO_DIR.glob('ncaaf-page*.html'))
    missing_from_calendar = []

    for pf in sorted(page_files):
        filename = pf.name
        if filename not in calendar_data:
            missing_from_calendar.append(filename)

    if missing_from_calendar:
        errors.append(f"Pages missing from calendar: {', '.join(missing_from_calendar)}")
    else:
        print(f"  OK: All {len(page_files)} page files are in calendar")

    # 3. Check archive pages
    print("\n[3] Checking archive pages...")
    archive_dir = REPO_DIR / 'archives' / 'ncaaf'
    if archive_dir.exists():
        archive_files = list(archive_dir.glob('*.html'))
        for af in archive_files:
            relative_path = f'archives/ncaaf/{af.name}'
            if relative_path not in calendar_data:
                errors.append(f"Archive page {relative_path} not in calendar!")
            else:
                print(f"  OK: {relative_path} is in calendar")

    # 4. Check for placeholder content in main page
    print("\n[4] Checking for placeholder content...")
    # Patterns that should match as whole words (use regex word boundaries)
    placeholder_patterns = [
        r'\bcoming soon\b', r'\banalysis coming\b', r'\bmatchup analysis\b',
        r'\bpreview coming\b', r'\bTBD\b', r'\bTBA\b', r'\bN/A\b'
    ]

    main_page = REPO_DIR / 'ncaaf.html'
    if main_page.exists():
        with open(main_page, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        found_placeholders = []
        for pattern in placeholder_patterns:
            if re.search(pattern, content, re.I):
                found_placeholders.append(pattern.replace(r'\b', ''))

        if found_placeholders:
            errors.append(f"ncaaf.html has placeholder content: {', '.join(found_placeholders)}")
        else:
            print("  OK: No placeholder content in ncaaf.html")

    # 5. Check calendar JS has archive page detection
    print("\n[5] Checking calendar JS for archive page support...")
    js_path = SCRIPTS_DIR / 'ncaaf-calendar.js'
    with open(js_path, 'r', encoding='utf-8') as f:
        js_content = f.read()

    if "pathname.includes('/archives/')" not in js_content:
        errors.append("ncaaf-calendar.js missing archive page detection code!")
    else:
        print("  OK: Archive page detection is present")

    # Summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)

    if errors:
        print(f"\n[X] {len(errors)} ERROR(S) FOUND:")
        for e in errors:
            print(f"    - {e}")

    if warnings:
        print(f"\n[!] {len(warnings)} WARNING(S):")
        for w in warnings:
            print(f"    - {w}")

    if not errors and not warnings:
        print("\n[OK] All validations passed!")

    print()
    return errors, warnings

if __name__ == '__main__':
    errors, warnings = validate()
    sys.exit(1 if errors else 0)
