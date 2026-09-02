#!/usr/bin/env python3
"""
Sync Featured Games Calendar Data

ARCHITECTURE (Updated Feb 5, 2026):
- featured-games-data.js = SINGLE SOURCE OF TRUTH (defines FEATURED_GAMES array)
- scripts/featured-games-calendar.js = RENDERING ONLY (reads from FEATURED_GAMES, no embedded data)
- ALL featured game pages load BOTH files: data.js first, then calendar.js

This script now VERIFIES the setup is correct rather than syncing data between files.
The old sync behavior (copying data into calendar.js) is no longer needed because
calendar.js reads directly from FEATURED_GAMES at runtime.
"""

import os
import re
import sys

REPO_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(REPO_PATH, 'featured-games-data.js')
CALENDAR_FILE = os.path.join(REPO_PATH, 'scripts', 'featured-games-calendar.js')

def count_entries_in_data_file():
    """Count entries in featured-games-data.js"""
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    pattern = r'\{\s*date:\s*"([^"]+)",\s*page:\s*"([^"]+)",\s*title:\s*"([^"]+)"\s*\}'
    matches = re.findall(pattern, content)
    return [(d, p, t) for d, p, t in matches if d != "YYYY-MM-DD"]

def verify_calendar_reads_from_featured_games():
    """Verify calendar.js reads from FEATURED_GAMES (no embedded data)"""
    with open(CALENDAR_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    reads_from_featured_games = 'typeof FEATURED_GAMES' in content
    has_no_embedded_data = 'date: "2025-' not in content and 'date: "2026-' not in content
    has_rendering = 'renderCalendar' in content

    return reads_from_featured_games, has_no_embedded_data, has_rendering

def main():
    print("=" * 60)
    print("Featured Games Calendar - Verification")
    print("=" * 60)

    if not os.path.exists(DATA_FILE):
        print(f"[ERROR] Data file not found: {DATA_FILE}")
        return 1

    if not os.path.exists(CALENDAR_FILE):
        print(f"[ERROR] Calendar file not found: {CALENDAR_FILE}")
        return 1

    # Check data file
    entries = count_entries_in_data_file()
    print(f"\n[1] featured-games-data.js: {len(entries)} entries")
    if entries:
        newest = max(entries, key=lambda x: x[0])
        print(f"    Latest: {newest[0]} - {newest[2]}")

    # Check calendar file
    reads_fg, no_embedded, has_render = verify_calendar_reads_from_featured_games()
    print(f"\n[2] scripts/featured-games-calendar.js:")
    print(f"    Reads from FEATURED_GAMES: {'YES' if reads_fg else 'NO - PROBLEM!'}")
    print(f"    No embedded data: {'YES' if no_embedded else 'NO - PROBLEM!'}")
    print(f"    Has rendering logic: {'YES' if has_render else 'NO - PROBLEM!'}")

    if not reads_fg or not no_embedded or not has_render:
        print("\n[WARNING] Calendar file may need repair!")
        print("    calendar.js should read from FEATURED_GAMES (no embedded data)")
        return 1

    print(f"\n[OK] Architecture is correct:")
    print(f"     featured-games-data.js -> defines FEATURED_GAMES ({len(entries)} entries)")
    print(f"     scripts/featured-games-calendar.js -> reads FEATURED_GAMES, renders calendar")
    print(f"\n     No sync needed - calendar reads data at runtime.")

    print("\n" + "=" * 60)
    return 0

if __name__ == "__main__":
    sys.exit(main())
