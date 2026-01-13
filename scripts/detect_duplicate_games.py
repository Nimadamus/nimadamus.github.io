#!/usr/bin/env python3
"""
DUPLICATE GAME DETECTION SCRIPT
Created: January 13, 2026

This script detects when the same game/matchup appears on multiple pages.
This prevents issues like "Liverpool vs Barnsley" appearing on both Jan 12 and Jan 13.

Root Cause (Jan 13, 2026):
- When creating new soccer pages, games were copy-pasted to multiple date pages
- No script was checking for duplicate matchups across different pages
- Result: Same games appeared on both January 12 and January 13

This script should be run:
1. Before committing any sports page changes
2. As part of the pre-commit hook

Usage:
    python scripts/detect_duplicate_games.py           # Check all sports
    python scripts/detect_duplicate_games.py soccer    # Check specific sport
    python scripts/detect_duplicate_games.py --fix     # Show which page to keep
"""

import os
import re
import sys
from datetime import datetime
from collections import defaultdict

REPO_ROOT = r'C:\Users\Nima\nimadamus.github.io'

# Sports to check
SPORTS = ['nba', 'nhl', 'nfl', 'ncaab', 'ncaaf', 'mlb', 'soccer']

# Pattern to extract matchups from h2 tags inside game-preview/game-header
MATCHUP_PATTERN = re.compile(
    r'<div class="matchup-info">.*?<h2>([^<]+)</h2>',
    re.DOTALL | re.IGNORECASE
)

# Pattern to extract game time (to determine which page the game belongs on)
GAME_TIME_PATTERN = re.compile(
    r'<span class="game-time">([^<]+)</span>',
    re.IGNORECASE
)

# Pattern to extract page date from title
DATE_PATTERN = re.compile(
    r'<title>.*?(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s*(\d{4})',
    re.IGNORECASE
)

def normalize_matchup(matchup):
    """Normalize matchup string for comparison."""
    # Remove extra whitespace
    matchup = ' '.join(matchup.split())
    # Standardize separators
    matchup = matchup.replace(' @ ', ' vs ')
    matchup = matchup.replace(' at ', ' vs ')
    return matchup.strip().lower()

def extract_games_from_file(filepath):
    """Extract all game matchups from a file."""
    games = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # Get page date from title
        date_match = DATE_PATTERN.search(content)
        page_date = None
        if date_match:
            month_map = {
                'january': 1, 'february': 2, 'march': 3, 'april': 4,
                'may': 5, 'june': 6, 'july': 7, 'august': 8,
                'september': 9, 'october': 10, 'november': 11, 'december': 12
            }
            month = month_map[date_match.group(1).lower()]
            day = int(date_match.group(2))
            year = int(date_match.group(3))
            page_date = f"{year}-{month:02d}-{day:02d}"

        # Find all game articles
        # Split by game-preview to get each game section
        game_sections = re.split(r'<article class="game-preview">', content)

        for section in game_sections[1:]:  # Skip first (before any game)
            matchup_match = MATCHUP_PATTERN.search('<div class="matchup-info">' + section if 'matchup-info' in section else section)
            if not matchup_match:
                # Try alternate patterns
                h2_match = re.search(r'<h2>([^<]+vs[^<]+)</h2>', section, re.IGNORECASE)
                if h2_match:
                    matchup = h2_match.group(1)
                else:
                    continue
            else:
                matchup = matchup_match.group(1)

            # Get game time if available
            time_match = re.search(r'<span class="game-time">([^<]+)</span>', section)
            game_time = time_match.group(1) if time_match else None

            games.append({
                'matchup': normalize_matchup(matchup),
                'matchup_original': matchup.strip(),
                'game_time': game_time,
                'page_date': page_date
            })

    except Exception as e:
        print(f"  Error reading {filepath}: {e}")

    return games

def check_sport_duplicates(sport):
    """Check all pages for a sport and find duplicate games."""
    duplicates = defaultdict(list)  # matchup -> [(page, game_info), ...]
    all_games = {}  # page -> [games]

    # Find all pages for this sport
    pages = []
    for filename in os.listdir(REPO_ROOT):
        if filename.startswith(sport) and filename.endswith('.html'):
            # Skip non-content files
            if any(skip in filename for skip in ['records', 'calendar', 'archive', 'test']):
                continue
            pages.append(filename)

    # Extract games from each page
    for page in sorted(pages):
        filepath = os.path.join(REPO_ROOT, page)
        games = extract_games_from_file(filepath)
        all_games[page] = games

        for game in games:
            matchup = game['matchup']
            duplicates[matchup].append((page, game))

    # Filter to only actual duplicates
    actual_duplicates = {
        matchup: pages
        for matchup, pages in duplicates.items()
        if len(pages) > 1
    }

    return actual_duplicates, all_games

def suggest_correct_page(pages_with_game):
    """Suggest which page should keep the game based on game time."""
    # Look at game times to determine correct page
    suggestions = []

    for page, game_info in pages_with_game:
        game_time = game_info.get('game_time', '')
        page_date = game_info.get('page_date', '')

        # Try to extract day of week from game time
        day_keywords = {
            'monday': 1, 'tuesday': 2, 'wednesday': 3, 'thursday': 4,
            'friday': 5, 'saturday': 6, 'sunday': 0
        }

        game_day = None
        if game_time:
            for day, num in day_keywords.items():
                if day in game_time.lower():
                    game_day = day.capitalize()
                    break

        suggestions.append({
            'page': page,
            'page_date': page_date,
            'game_time': game_time,
            'game_day': game_day
        })

    return suggestions

def main():
    show_fix = '--fix' in sys.argv
    quiet_mode = '--quiet' in sys.argv

    # Determine which sports to check
    sports_to_check = SPORTS
    for arg in sys.argv[1:]:
        if arg in SPORTS:
            sports_to_check = [arg]
            break

    # In quiet mode, just return exit code
    if quiet_mode:
        for sport in sports_to_check:
            duplicates, _ = check_sport_duplicates(sport)
            if duplicates:
                return 1
        return 0

    print("=" * 70)
    print("DUPLICATE GAME DETECTION REPORT")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    total_duplicates = 0

    for sport in sports_to_check:
        print(f"\n{'='*25} {sport.upper()} {'='*25}")

        duplicates, all_games = check_sport_duplicates(sport)

        if duplicates:
            total_duplicates += len(duplicates)
            print(f"\n[X] DUPLICATE GAMES FOUND: {len(duplicates)}")
            print("-" * 60)

            for matchup, pages_with_game in sorted(duplicates.items()):
                # Get original matchup text from first occurrence
                original = pages_with_game[0][1]['matchup_original']
                print(f"\n  Game: {original}")
                print(f"  Found on {len(pages_with_game)} pages:")

                for page, game_info in pages_with_game:
                    page_date = game_info.get('page_date', 'unknown')
                    game_time = game_info.get('game_time', 'no time info')
                    print(f"    - {page} (page date: {page_date})")
                    if game_time:
                        print(f"      Game time: {game_time}")

                if show_fix:
                    suggestions = suggest_correct_page(pages_with_game)
                    print(f"\n  Suggested fix:")
                    for s in suggestions:
                        if s['game_day']:
                            print(f"    {s['page']}: Game is on {s['game_day']}")
        else:
            print(f"\n  [OK] No duplicate games found")
            print(f"  Pages checked: {len(all_games)}")

    print("\n" + "=" * 70)

    if total_duplicates > 0:
        print(f"[X] FOUND {total_duplicates} DUPLICATE GAME(S)")
        print("\nTo fix:")
        print("1. Determine which page the game actually belongs on (check game day/time)")
        print("2. Remove the game from the incorrect page(s)")
        print("3. Run this script again to verify")
        print("\nRun with --fix flag for suggestions: python scripts/detect_duplicate_games.py --fix")
        print("=" * 70)
        return 1
    else:
        print("[OK] NO DUPLICATE GAMES FOUND")
        print("=" * 70)
        return 0

if __name__ == '__main__':
    sys.exit(main())
