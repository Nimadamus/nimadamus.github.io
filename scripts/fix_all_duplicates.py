#!/usr/bin/env python3
"""
Fix ALL duplicate games across all sports
Created: January 13, 2026

Strategy: For each duplicate game, keep it on the LOWEST page number
and remove from all other pages. This ensures no content is lost,
just deduplicated.

This is a comprehensive one-time cleanup script.
"""

import os
import re
from collections import defaultdict

REPO_ROOT = r'C:\Users\Nima\nimadamus.github.io'
SPORTS = ['nba', 'nhl', 'nfl', 'ncaab', 'ncaaf', 'mlb', 'soccer']

def normalize_matchup(text):
    """Normalize matchup for comparison."""
    text = ' '.join(text.split()).lower()
    text = text.replace(' @ ', ' vs ')
    text = text.replace(' at ', ' vs ')
    return text

def get_page_number(filename):
    """Extract page number from filename for sorting."""
    # soccer.html -> 0, soccer-page2.html -> 2, etc.
    if '-page' in filename:
        match = re.search(r'-page(\d+)', filename)
        if match:
            return int(match.group(1))
    return 0  # Main page (e.g., nba.html) gets 0

def extract_games_from_file(filepath):
    """Extract all game matchups from a file."""
    games = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # Split by game-preview articles
        article_pattern = r'<article class="game-preview">(.*?)</article>'
        for match in re.finditer(article_pattern, content, re.DOTALL):
            article = match.group(0)

            # Extract matchup from h2
            h2_match = re.search(r'<h2>([^<]+)</h2>', article)
            if h2_match:
                matchup = h2_match.group(1).strip()
                games.append({
                    'matchup': normalize_matchup(matchup),
                    'matchup_original': matchup,
                    'article_html': article
                })
    except Exception as e:
        print(f"  Error reading {filepath}: {e}")

    return games

def remove_game_from_file(filepath, matchup_normalized):
    """Remove a game article from an HTML file."""
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    article_pattern = r'<article class="game-preview">.*?</article>'

    original_content = content

    for match in re.finditer(article_pattern, content, re.DOTALL):
        article = match.group(0)
        h2_match = re.search(r'<h2>([^<]+)</h2>', article)
        if h2_match:
            article_matchup = normalize_matchup(h2_match.group(1))
            if article_matchup == matchup_normalized:
                # Remove this article
                content = content.replace(article + '\n\n', '')
                content = content.replace(article + '\n', '')
                content = content.replace(article, '')
                break

    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def fix_sport_duplicates(sport):
    """Fix all duplicates for a sport."""
    print(f"\n{'='*20} {sport.upper()} {'='*20}")

    # Collect all pages and their games
    pages = []
    for filename in sorted(os.listdir(REPO_ROOT)):
        if filename.startswith(sport) and filename.endswith('.html'):
            if any(skip in filename for skip in ['records', 'calendar', 'archive', 'test']):
                continue
            pages.append(filename)

    # Sort by page number (lower = keep, higher = remove duplicates)
    pages.sort(key=get_page_number)

    # Build map of matchup -> list of pages it appears on
    matchup_pages = defaultdict(list)

    for page in pages:
        filepath = os.path.join(REPO_ROOT, page)
        games = extract_games_from_file(filepath)
        for game in games:
            matchup_pages[game['matchup']].append({
                'page': page,
                'original': game['matchup_original']
            })

    # Find duplicates and remove from higher page numbers
    removed = 0

    for matchup, occurrences in matchup_pages.items():
        if len(occurrences) > 1:
            # Sort by page number - keep on lowest
            occurrences.sort(key=lambda x: get_page_number(x['page']))

            keep_page = occurrences[0]['page']
            original_name = occurrences[0]['original']

            # Remove from all pages except the first one
            for occ in occurrences[1:]:
                remove_page = occ['page']
                filepath = os.path.join(REPO_ROOT, remove_page)

                if remove_game_from_file(filepath, matchup):
                    print(f"  Removed '{original_name}' from {remove_page} (kept on {keep_page})")
                    removed += 1

    print(f"  Total removed from {sport}: {removed}")
    return removed

def main():
    print("=" * 60)
    print("COMPREHENSIVE DUPLICATE CLEANUP - ALL SPORTS")
    print("=" * 60)
    print("\nStrategy: Keep games on LOWEST page number, remove from others")

    total_removed = 0

    for sport in SPORTS:
        total_removed += fix_sport_duplicates(sport)

    print("\n" + "=" * 60)
    print(f"TOTAL GAMES REMOVED: {total_removed}")
    print("=" * 60)

    print("\nVerify with: python scripts/detect_duplicate_games.py")

if __name__ == '__main__':
    main()
