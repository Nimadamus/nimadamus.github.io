#!/usr/bin/env python3
"""
Fix all soccer page duplicates - One-time cleanup script
Created: January 13, 2026

This script removes duplicate games from soccer pages where they appear on
multiple dates. The rule is: keep the game on ONE page only.

For pages with the same date (e.g., page6 and page7 both Dec 27):
- Keep games on the LOWER page number, remove from higher

For pages with different dates:
- Check game time to determine correct page
- Remove from wrong page
"""

import os
import re

REPO_ROOT = r'C:\Users\Nima\nimadamus.github.io'

# Define which pages to CLEAR of duplicate content
# Format: {page_to_clean: [list of matchups to remove]}

CLEANUP_RULES = {
    # Dec 27: page6 and page7 both dated Dec 27 - keep on page6, remove from page7
    'soccer-page7.html': [
        'Albion @ Arsenal',
        'Bournemouth @ Brentford',
        'Cagliari @ Torino',
        'City @ Forest',
        'Como @ Lecce',
        'Everton @ Burnley',
        'Fiorentina @ Parma',
        'Fulham @ United',
        'Juventus @ Pisa',
        'Lazio @ Udinese',
        'Villa @ Chelsea',
        'Wanderers @ Liverpool',
    ],

    # Dec 28: page8 and page9 both dated Dec 28 - keep on page8, remove from page9
    'soccer-page9.html': [
        'Hotspur @ Palace',
        'Internazionale @ Atalanta',
        'Napoli @ Cremonese',
        'Sassuolo @ Bologna',
        'United @ Sunderland',
        'Verona @ Milan',
    ],

    # Jan 10/11: FA Cup games on Saturday (Jan 10) - remove from Jan 11 page (page20)
    'soccer-page20.html': [
        'Arsenal vs Manchester United',
        'Charlton Athletic vs Chelsea',
        'Liverpool vs Accrington Stanley',
        'Macclesfield FC vs Crystal Palace',
        'Manchester City vs Exeter City',
        'Newcastle vs Bromley',
        'Tottenham vs Aston Villa',
        'West Ham vs Aston Villa',
    ],

    # Jan 4/9: Game "Brentford @ Everton" with Sunday Jan 4 game time - keep on page15 (Jan 4)
    'soccer-page14.html': [
        'Brentford @ Everton',  # Listed as "Sunday, January 4" - belongs on Jan 4 page
    ],

    # Liverpool @ Fulham - appears on both page14 (Jan 9) and page15 (Jan 4)
    # Game time shows Jan 4 - keep on page15, remove from page14
    'soccer-page14.html': [
        'Brentford @ Everton',
        'Liverpool @ Fulham',
    ],
}

def normalize_matchup(text):
    """Normalize matchup for comparison."""
    text = ' '.join(text.split()).lower()
    text = text.replace(' @ ', ' vs ')
    text = text.replace(' at ', ' vs ')
    return text

def remove_game_from_file(filepath, matchup_to_remove):
    """Remove a game article from an HTML file."""
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # Find and remove the article containing this matchup
    # Pattern to find article blocks
    article_pattern = r'<article class="game-preview">.*?</article>'

    def should_remove(article_html):
        # Extract h2 content
        h2_match = re.search(r'<h2>([^<]+)</h2>', article_html)
        if h2_match:
            h2_text = h2_match.group(1)
            return normalize_matchup(h2_text) == normalize_matchup(matchup_to_remove)
        return False

    original_content = content

    # Find all articles and filter out the one to remove
    for match in re.finditer(article_pattern, content, re.DOTALL):
        article = match.group(0)
        if should_remove(article):
            # Remove this article (and any trailing newlines)
            content = content.replace(article + '\n\n', '')
            content = content.replace(article + '\n', '')
            content = content.replace(article, '')
            print(f"  Removed: {matchup_to_remove}")
            break

    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def main():
    print("=" * 60)
    print("SOCCER DUPLICATE CLEANUP")
    print("=" * 60)

    total_removed = 0

    for page, matchups in CLEANUP_RULES.items():
        filepath = os.path.join(REPO_ROOT, page)
        if not os.path.exists(filepath):
            print(f"\n[!] File not found: {page}")
            continue

        print(f"\nProcessing {page}:")

        for matchup in matchups:
            if remove_game_from_file(filepath, matchup):
                total_removed += 1

    print("\n" + "=" * 60)
    print(f"Total games removed: {total_removed}")
    print("=" * 60)

    print("\nRun duplicate detection to verify:")
    print("  python scripts/detect_duplicate_games.py soccer")

if __name__ == '__main__':
    main()
