"""
Generate test pages for desktop review
"""

import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scrapers import get_scraper, SCRAPERS
from generators.content_generator import ContentGenerator
from config import SPORTS

# Output directory
DESKTOP = r"C:\Users\Nima\Desktop"
OUTPUT_DIR = os.path.join(DESKTOP, "AutoContent_Test_Dec4")

# Create output directory
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Initialize content generator
generator = ContentGenerator()

def generate_test_page(sport: str):
    """Generate a test HTML page for a sport."""
    config = SPORTS.get(sport)
    if not config:
        print(f"Unknown sport: {sport}")
        return

    sport_name = config['name']
    print(f"\n{'='*60}")
    print(f"Generating {sport_name} content...")
    print('='*60)

    # Get scraper and fetch games
    scraper = get_scraper(sport)
    games_data = scraper.get_full_game_data()

    if not games_data:
        print(f"No {sport_name} games today")
        return

    print(f"Found {len(games_data)} games")

    # Generate content for each game
    game_sections = []
    for i, game_data in enumerate(games_data):
        formatted = scraper.format_for_article(game_data)
        matchup = formatted.get('matchup', f'Game {i+1}')
        print(f"  [{i+1}/{len(games_data)}] {matchup}")

        try:
            # Generate stat grid
            stat_grid = generator.generate_stat_grid_html(formatted, sport)

            # Generate article
            article = generator.generate_game_article(formatted, sport)

            # Build game section HTML
            home = formatted.get('home', {})
            away = formatted.get('away', {})
            odds = formatted.get('odds', {})

            game_html = f"""
<article class="game-card">
    <h3 class="game-title">{away.get('name', 'Away')} ({away.get('record', '')}) @ {home.get('name', 'Home')} ({home.get('record', '')})</h3>
    <div class="game-meta">
        <span>Time: {formatted.get('game_time', 'TBD')}</span>
        <span>Venue: {formatted.get('venue', 'TBD')}</span>
        <span>TV: {formatted.get('broadcast', 'TBD')}</span>
        <span>Line: {odds.get('spread', 'N/A')}</span>
        <span>Total: {odds.get('total', 'N/A')}</span>
    </div>

    {stat_grid}

    <div class="analysis">
        <p>{article}</p>
    </div>
</article>
"""
            game_sections.append(game_html)

        except Exception as e:
            print(f"    Error: {e}")

    # Build full test page
    date_str = datetime.now().strftime("%B %d, %Y")

    html_page = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{sport_name} Test - {date_str}</title>
    <style>
        :root {{
            --bg-dark: #0a0a0f;
            --bg-card: #12121a;
            --text-primary: #ffffff;
            --text-secondary: #a0a0b0;
            --accent-cyan: #00e5ff;
            --accent-gold: #ffd700;
            --border-subtle: #2a2a3a;
        }}

        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: var(--bg-dark);
            color: var(--text-primary);
            line-height: 1.6;
            padding: 20px;
        }}

        header {{
            text-align: center;
            padding: 30px;
            background: linear-gradient(135deg, #1a1a2e 0%, #0a0a0f 100%);
            border-radius: 12px;
            margin-bottom: 30px;
            border: 1px solid var(--border-subtle);
        }}

        header h1 {{
            color: var(--accent-cyan);
            font-size: 2.5rem;
            margin-bottom: 10px;
        }}

        header p {{
            color: var(--text-secondary);
            font-size: 1.1rem;
        }}

        .game-card {{
            background: var(--bg-card);
            border: 1px solid var(--border-subtle);
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 25px;
        }}

        .game-card:hover {{
            border-color: var(--accent-cyan);
        }}

        .game-title {{
            color: var(--accent-gold);
            font-size: 1.4rem;
            margin-bottom: 15px;
        }}

        .game-meta {{
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            margin-bottom: 20px;
            font-size: 0.9rem;
            color: var(--text-secondary);
        }}

        .game-meta span {{
            background: rgba(0, 229, 255, 0.1);
            padding: 5px 12px;
            border-radius: 20px;
            border: 1px solid var(--border-subtle);
        }}

        .stat-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin: 20px 0;
            padding: 20px;
            background: rgba(0, 0, 0, 0.3);
            border-radius: 8px;
        }}

        .stat-row {{
            display: flex;
            justify-content: space-around;
            gap: 20px;
        }}

        .stat-item {{
            text-align: center;
            padding: 10px;
        }}

        .stat-value {{
            font-size: 1.3rem;
            font-weight: bold;
            color: var(--accent-cyan);
        }}

        .stat-label {{
            font-size: 0.8rem;
            color: var(--text-secondary);
            margin-top: 5px;
        }}

        .analysis {{
            margin-top: 20px;
            padding: 20px;
            background: rgba(255, 215, 0, 0.05);
            border-left: 3px solid var(--accent-gold);
            border-radius: 0 8px 8px 0;
        }}

        .analysis p {{
            color: var(--text-primary);
            font-size: 1rem;
            line-height: 1.8;
        }}

        .summary {{
            text-align: center;
            padding: 20px;
            margin-top: 30px;
            background: var(--bg-card);
            border-radius: 12px;
            border: 1px solid var(--accent-cyan);
        }}

        .summary h2 {{
            color: var(--accent-cyan);
            margin-bottom: 10px;
        }}
    </style>
</head>
<body>
    <header>
        <h1>{sport_name} Daily Analysis</h1>
        <p>{date_str} - {len(game_sections)} Games</p>
        <p style="color: var(--accent-gold); margin-top: 10px;">TEST PAGE - FOR REVIEW ONLY</p>
    </header>

    <main>
        {''.join(game_sections)}
    </main>

    <div class="summary">
        <h2>Generation Complete</h2>
        <p>Generated {len(game_sections)} game articles using Claude AI</p>
    </div>
</body>
</html>
"""

    # Save to desktop
    output_path = os.path.join(OUTPUT_DIR, f"{sport}_test.html")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_page)

    print(f"\nSaved: {output_path}")
    return len(game_sections)


if __name__ == "__main__":
    print("\n" + "="*60)
    print("AUTO-CONTENT TEST GENERATION")
    print(f"Date: {datetime.now().strftime('%B %d, %Y')}")
    print(f"Output: {OUTPUT_DIR}")
    print("="*60)

    # Sports to test
    sports_to_test = ['nba', 'nhl', 'ncaab', 'soccer']

    total_games = 0
    for sport in sports_to_test:
        try:
            count = generate_test_page(sport)
            if count:
                total_games += count
        except Exception as e:
            print(f"Error with {sport}: {e}")

    print("\n" + "="*60)
    print("TEST GENERATION COMPLETE")
    print(f"Total games processed: {total_games}")
    print(f"Files saved to: {OUTPUT_DIR}")
    print("="*60)
