#!/usr/bin/env python3
"""
Sync Featured Games Calendar Data

This script reads from featured-games-data.js (the master source) and updates
scripts/featured-games-calendar.js (used by the calendar sidebar).

This ensures both files stay in sync automatically.

Run this after adding new featured game entries to featured-games-data.js.
"""

import os
import re
import json
from datetime import datetime

REPO_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(REPO_PATH, 'featured-games-data.js')
CALENDAR_FILE = os.path.join(REPO_PATH, 'scripts', 'featured-games-calendar.js')

def parse_featured_games_data():
    """Parse entries from featured-games-data.js"""
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract entries using regex
    pattern = r'\{\s*date:\s*"([^"]+)",\s*page:\s*"([^"]+)",\s*title:\s*"([^"]+)"\s*\}'
    matches = re.findall(pattern, content)

    entries = []
    for date, page, title in matches:
        # Skip template/placeholder entries from comments
        if date == "YYYY-MM-DD" or page == "filename.html":
            continue
        entries.append({'date': date, 'page': page, 'title': title})

    # Sort by date descending (newest first)
    entries.sort(key=lambda x: x['date'], reverse=True)

    return entries

def update_calendar_file(entries):
    """Update the calendar JS file with new entries"""

    today = datetime.now().strftime("%B %d, %Y")

    # Build the ARCHIVE_DATA array
    archive_lines = []
    for entry in entries:
        archive_lines.append(f'    {{ date: "{entry["date"]}", page: "{entry["page"]}", title: "{entry["title"]}" }}')

    archive_data = ',\n'.join(archive_lines)

    # Read existing file to preserve the calendar logic
    with open(CALENDAR_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    # Replace the ARCHIVE_DATA section
    # Find the pattern: const ARCHIVE_DATA = [ ... ];
    pattern = r'(// Featured Games Archive Data.*?Last updated:)[^\n]*(\n\nconst ARCHIVE_DATA = \[)\n.*?(\];)'

    replacement = f'\\g<1> {today}\\g<2>\n{archive_data}\n\\3'

    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

    if new_content != content:
        with open(CALENDAR_FILE, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"[OK] Updated {CALENDAR_FILE}")
        print(f"     Added/updated {len(entries)} entries")
        return True
    else:
        print(f"[OK] {CALENDAR_FILE} is already up to date")
        return False

def main():
    print("=" * 60)
    print("Syncing Featured Games Calendar Data")
    print("=" * 60)

    # Check files exist
    if not os.path.exists(DATA_FILE):
        print(f"[ERROR] Data file not found: {DATA_FILE}")
        return 1

    if not os.path.exists(CALENDAR_FILE):
        print(f"[ERROR] Calendar file not found: {CALENDAR_FILE}")
        return 1

    # Parse master data
    print(f"\n[1] Reading from: featured-games-data.js")
    entries = parse_featured_games_data()
    print(f"    Found {len(entries)} featured game entries")

    if entries:
        print(f"    Latest: {entries[0]['date']} - {entries[0]['title']}")

    # Update calendar file
    print(f"\n[2] Updating: scripts/featured-games-calendar.js")
    update_calendar_file(entries)

    print("\n" + "=" * 60)
    print("Done! Don't forget to commit and push the changes.")
    print("=" * 60)

    return 0

if __name__ == "__main__":
    exit(main())
