"""
Generate test pages matching the EXACT BetLegend style
"""

import os
import re
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scrapers import get_scraper, SCRAPERS
from generators.content_generator import ContentGenerator
from config import SPORTS

DESKTOP = r"C:\Users\Nima\Desktop"
OUTPUT_DIR = os.path.join(DESKTOP, "AutoContent_Test_Dec4")
os.makedirs(OUTPUT_DIR, exist_ok=True)

generator = ContentGenerator()

def generate_test_page(sport: str):
    """Generate a test page matching BetLegend's actual style."""
    config = SPORTS.get(sport)
    if not config:
        print(f"Unknown sport: {sport}")
        return

    sport_name = config['name']
    print(f"\n{'='*60}")
    print(f"Generating {sport_name} content...")
    print('='*60)

    scraper = get_scraper(sport)
    games_data = scraper.get_full_game_data()

    if not games_data:
        print(f"No {sport_name} games today")
        return

    print(f"Found {len(games_data)} games")

    game_cards = []
    for i, game_data in enumerate(games_data):
        formatted = scraper.format_for_article(game_data)
        matchup = formatted.get('matchup', f'Game {i+1}')
        print(f"  [{i+1}/{len(games_data)}] {matchup}")

        try:
            home = formatted.get('home', {})
            away = formatted.get('away', {})
            odds = formatted.get('odds', {})

            # Generate article
            article = generator.generate_game_article(formatted, sport)

            # Split into paragraphs and convert markdown bold to HTML
            paragraphs = article.split('\n\n')
            article_html = ''
            for p in paragraphs:
                if p.strip():
                    # Convert **text** to <strong>text</strong>
                    converted = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', p.strip())
                    article_html += f'<p>{converted}</p>\n'

            # Build game card matching EXACT BetLegend structure
            game_html = f'''<article class="game-card">
<div class="teams-display">
<img alt="{away.get('name', 'Away')}" class="team-logo" onerror="this.style.display='none'" src="https://a.espncdn.com/i/teamlogos/{sport}/500/scoreboard/{away.get('abbrev', '').lower()}.png"/>
<span class="vs-badge">@</span>
<img alt="{home.get('name', 'Home')}" class="team-logo" onerror="this.style.display='none'" src="https://a.espncdn.com/i/teamlogos/{sport}/500/scoreboard/{home.get('abbrev', '').lower()}.png"/>
</div>
<h3 class="game-title">{away.get('name', 'Away')} ({away.get('record', '?')}) @ {home.get('name', 'Home')} ({home.get('record', '?')})</h3>
<div class="game-meta">
<span>{formatted.get('game_time', 'TBD')}</span>
<span>{formatted.get('venue', 'TBD')}</span>
<span>{formatted.get('broadcast', 'TBD')}</span>
<span>Line: {odds.get('spread', 'N/A')}</span>
<span>Total: {odds.get('total', 'N/A')}</span>
</div>
<div class="stat-grid">
<div class="stat-row">
<div class="stat-item">
<div class="value">{home.get('record', 'N/A')}</div>
<div class="label">{home.get('abbrev', 'HOME')}</div>
</div>
<div class="stat-item">
<div class="value">{away.get('record', 'N/A')}</div>
<div class="label">{away.get('abbrev', 'AWAY')}</div>
</div>
<div class="stat-item">
<div class="value">{home.get('l10', 'N/A')}</div>
<div class="label">L10</div>
</div>
<div class="stat-item">
<div class="value">{away.get('l10', 'N/A')}</div>
<div class="label">L10</div>
</div>
</div>
</div>
{article_html}
<div class="data-source">Sources: ESPN, Team Stats, Official League Data</div>
</article>'''
            game_cards.append(game_html)

        except Exception as e:
            print(f"    Error: {e}")

    date_str = datetime.now().strftime("%B %d, %Y")

    # Use EXACT BetLegend CSS
    html_page = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<title>{sport_name} Test - {date_str} | BetLegend</title>
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&amp;family=Poppins:wght@300;400;600&amp;display=swap" rel="stylesheet"/>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
:root{{
  --bg-primary:#05070a;--bg-card:rgba(15,20,30,0.8);
  --accent-cyan:#00e5ff;--accent-gold:#ffd54f;--accent-purple:#a855f7;
  --text-primary:#ffffff;--text-secondary:#94a3b8;--text-muted:#64748b;
  --border-subtle:rgba(255,255,255,0.08);--border-glow:rgba(0,229,255,0.3);
  --gradient-card:linear-gradient(145deg,rgba(15,23,42,0.9),rgba(10,15,25,0.95));
  --gradient-accent:linear-gradient(135deg,#00e5ff,#a855f7);
  --neon-cyan:#00ffff;--neon-gold:#FFD700;
  --font-primary:'Orbitron',sans-serif;--font-secondary:'Poppins',sans-serif
}}
body{{background:var(--bg-primary);color:var(--text-primary);font-family:var(--font-secondary);line-height:1.7}}
.hero{{padding:60px 24px;text-align:center}}
.hero-badge{{display:inline-block;background:rgba(0,229,255,0.1);border:1px solid rgba(0,229,255,0.2);padding:8px 16px;border-radius:50px;font-size:12px;color:var(--accent-cyan);text-transform:uppercase;letter-spacing:1px;margin-bottom:20px}}
.hero h1{{font-family:var(--font-primary);font-size:clamp(36px,6vw,56px);font-weight:700;margin-bottom:12px}}
.hero h1 span{{background:var(--gradient-accent);-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
.hero p{{color:var(--text-secondary);font-size:18px}}
.current-date{{text-align:center;margin-bottom:40px}}
.current-date h2{{font-size:28px;color:var(--accent-gold)}}
main{{max-width:900px;margin:0 auto;padding:0 24px 80px}}
.game-card{{background:var(--gradient-card);border:1px solid var(--border-subtle);border-radius:20px;padding:32px;margin-bottom:24px;transition:all 0.3s}}
.game-card:hover{{border-color:var(--border-glow);transform:translateY(-4px);box-shadow:0 4px 24px rgba(0,0,0,0.4)}}
.teams-display{{display:flex;align-items:center;justify-content:center;gap:20px;margin-bottom:16px}}
.team-logo{{width:60px;height:60px;object-fit:contain}}
.vs-badge{{color:var(--text-muted);font-size:14px;font-weight:700;padding:8px 12px;background:rgba(255,255,255,0.05);border-radius:8px}}
.game-title{{font-size:22px;font-weight:600;margin-bottom:8px;text-align:center}}
.game-meta{{font-size:13px;color:var(--text-muted);margin-bottom:20px;padding-bottom:20px;border-bottom:1px solid var(--border-subtle);display:flex;flex-wrap:wrap;gap:8px;justify-content:center}}
.game-meta span{{background:rgba(255,255,255,0.05);padding:4px 10px;border-radius:6px}}
.game-card p{{color:var(--text-secondary);margin-bottom:12px;line-height:1.8}}
.game-card strong{{color:var(--accent-cyan);font-weight:700}}
.game-card p:last-of-type strong{{display:block;background:linear-gradient(135deg,rgba(0,229,255,0.15),rgba(168,85,247,0.15));padding:12px 16px;border-radius:8px;border-left:3px solid var(--accent-cyan);margin-top:8px;font-size:1.1rem;text-shadow:0 0 10px rgba(0,229,255,0.3)}}
.stat-row{{display:flex;flex-wrap:wrap;gap:12px;margin:16px 0;padding:16px;background:rgba(0,0,0,0.3);border-radius:12px;border:1px solid var(--border-subtle)}}
.stat-item{{flex:1;min-width:100px;text-align:center;padding:8px}}
.stat-item .value{{font-family:var(--font-primary);font-size:1.3rem;font-weight:700;color:var(--accent-gold)}}
.stat-item .label{{font-size:0.7rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.5px}}
.data-source{{font-size:11px;color:var(--text-muted);text-align:center;margin-top:8px;padding-top:12px;border-top:1px solid var(--border-subtle)}}
.test-banner{{background:linear-gradient(135deg,#ff6b00,#ff8c00);color:#fff;text-align:center;padding:15px;font-weight:600;font-size:14px;letter-spacing:1px}}
@media(max-width:768px){{.game-card{{padding:24px}}.team-logo{{width:48px;height:48px}}.stat-row{{flex-direction:column}}}}
</style>
</head>
<body>
<div class="test-banner">TEST PAGE - FOR REVIEW ONLY - NOT LIVE</div>
<header class="hero">
<div class="hero-badge">Statistical Analysis</div>
<h1>{sport_name} <span>Analysis</span></h1>
<p>{len(game_cards)}-Game Slate | Advanced Stats &amp; Betting Trends</p>
</header>
<div class="current-date"><h2>{date_str}</h2></div>
<main>
{''.join(game_cards)}
</main>
</body>
</html>'''

    output_path = os.path.join(OUTPUT_DIR, f"{sport}_test.html")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_page)

    print(f"\nSaved: {output_path}")
    return len(game_cards)


if __name__ == "__main__":
    print("\n" + "="*60)
    print("AUTO-CONTENT TEST GENERATION")
    print(f"Date: {datetime.now().strftime('%B %d, %Y')}")
    print(f"Output: {OUTPUT_DIR}")
    print("="*60)

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
