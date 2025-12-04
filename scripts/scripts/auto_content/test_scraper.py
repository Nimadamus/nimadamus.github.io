"""Quick test to see sample game data"""
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scrapers import get_scraper

scraper = get_scraper('nba')
games = scraper.get_full_game_data()

print(f"Found {len(games)} games\n")

# Show first 2 games formatted
for game in games[:2]:
    formatted = scraper.format_for_article(game)
    print(json.dumps(formatted, indent=2))
    print("-" * 60)
