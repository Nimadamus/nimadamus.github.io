#!/usr/bin/env python3
"""
BETLEGEND DAILY SPORTS UPDATE SYSTEM
Fully automated daily content management for BetLegendPicks.com

WHAT THIS SCRIPT DOES:
1. Archives current content (moves to date-based archive)
2. Pulls today's game schedules from ESPN
3. Generates new sport pages with game cards
4. Updates archive index pages
5. Commits and pushes to GitHub

USAGE:
  python daily_sports_update.py              # Update all sports
  python daily_sports_update.py --sport NBA  # Update specific sport
  python daily_sports_update.py --dry-run    # Preview without changes

Author: BetLegend Automation System
"""

import os
import re
import json
import subprocess
from datetime import datetime, timedelta
from urllib.request import urlopen, Request
from urllib.error import URLError
import argparse

# Configuration
REPO = os.path.dirname(os.path.abspath(__file__))
TODAY = datetime.now()
DATE_STR = TODAY.strftime("%Y-%m-%d")
DATE_DISPLAY = TODAY.strftime("%A, %B %d, %Y")

# ESPN API endpoints for schedules
ESPN_ENDPOINTS = {
    'NBA': 'https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard',
    'NHL': 'https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard',
    'NFL': 'https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard',
    'NCAAB': 'https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard?limit=50',
    'NCAAF': 'https://site.api.espn.com/apis/site/v2/sports/football/college-football/scoreboard?limit=50',
    'MLB': 'https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard',
    'SOCCER': 'https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/scoreboard',  # Premier League
}

# Team logo URLs
def get_team_logo(sport, team_abbrev):
    """Get ESPN team logo URL."""
    sport_paths = {
        'NBA': 'nba/500',
        'NHL': 'nhl/500',
        'NFL': 'nfl/500',
        'NCAAB': 'ncaa/500',
        'NCAAF': 'ncaa/500',
        'MLB': 'mlb/500',
        'SOCCER': 'soccer/500'
    }
    path = sport_paths.get(sport, 'nba/500')
    return f"https://a.espncdn.com/i/teamlogos/{path}/{team_abbrev.lower()}.png"

# Standard CSS template
STANDARD_CSS = '''*{margin:0;padding:0;box-sizing:border-box}
:root{
  --bg-primary:#05070a;--bg-card:rgba(15,20,30,0.8);
  --accent-cyan:#00e5ff;--accent-gold:#ffd54f;--accent-purple:#a855f7;
  --text-primary:#ffffff;--text-secondary:#94a3b8;--text-muted:#64748b;
  --border-subtle:rgba(255,255,255,0.08);--border-glow:rgba(0,229,255,0.3);
  --gradient-card:linear-gradient(145deg,rgba(15,23,42,0.9),rgba(10,15,25,0.95));
  --gradient-accent:linear-gradient(135deg,#00e5ff,#a855f7);
  --neon-cyan:#00ffff;--neon-gold:#FFD700;
  --font-primary:'Orbitron',sans-serif;--font-secondary:'Poppins',sans-serif
}
.nav-container{position:fixed;top:0;left:0;right:0;z-index:1000;background:rgba(0,0,0,0.85);backdrop-filter:blur(10px);border-bottom:1px solid rgba(0,224,255,0.3)}
.nav-inner{max-width:1400px;margin:0 auto;display:flex;align-items:center;justify-content:center;gap:12px;padding:18px 5% 18px 280px}
.logo{position:fixed;top:15px;left:15px;z-index:1001}
.logo a{font-family:var(--font-primary);font-size:2.5rem;font-weight:900;color:#fff;text-decoration:none;text-shadow:0 0 10px rgba(255,255,255,0.8)}
.logo a span{color:var(--neon-cyan);text-shadow:0 0 15px rgba(0,255,255,1)}
.nav-links{display:flex;align-items:center;gap:15px;flex-wrap:wrap}
.nav-links>a,.dropbtn{font-family:var(--font-secondary);color:#fff;text-decoration:none;font-size:18px;font-weight:600;padding:12px 20px;border-radius:8px;background:none;border:none;cursor:pointer;text-transform:uppercase;letter-spacing:1.5px}
.nav-links>a:hover,.dropbtn:hover{color:var(--neon-gold);text-shadow:0 0 15px var(--neon-gold)}
.dropdown{position:relative}
.dropdown-content{display:none;position:absolute;top:100%;left:0;background:rgba(0,0,0,0.98);min-width:200px;border:2px solid rgba(0,224,255,0.5);border-radius:10px;padding:15px 0;margin-top:10px}
.dropdown-content a{color:var(--neon-cyan);padding:14px 20px;display:block;text-decoration:none}
.dropdown-content a:hover{background:rgba(0,224,255,0.2);color:#fff}
.dropdown:hover .dropdown-content{display:block}
body{background:var(--bg-primary);color:var(--text-primary);font-family:system-ui,sans-serif;line-height:1.7}
.hero{padding:140px 24px 60px;text-align:center}
.hero-badge{display:inline-block;background:rgba(0,229,255,0.1);border:1px solid rgba(0,229,255,0.2);padding:8px 16px;border-radius:50px;font-size:12px;color:var(--accent-cyan);text-transform:uppercase;letter-spacing:1px;margin-bottom:20px}
.hero h1{font-size:clamp(36px,6vw,56px);font-weight:700;margin-bottom:12px}
.hero h1 span{background:var(--gradient-accent);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.hero p{color:var(--text-secondary);font-size:18px}
.current-date{text-align:center;margin-bottom:40px}
.current-date h2{font-size:28px;color:var(--accent-gold)}
main{max-width:900px;margin:0 auto;padding:0 24px 80px}
.game-card{background:var(--gradient-card);border:1px solid var(--border-subtle);border-radius:20px;padding:32px;margin-bottom:24px;transition:all 0.3s}
.game-card:hover{border-color:var(--border-glow);transform:translateY(-4px);box-shadow:0 4px 24px rgba(0,0,0,0.4)}
.teams-display{display:flex;align-items:center;justify-content:center;gap:20px;margin-bottom:16px}
.team-logo{width:60px;height:60px;object-fit:contain}
.vs-badge{color:var(--text-muted);font-size:14px;font-weight:700;padding:8px 12px;background:rgba(255,255,255,0.05);border-radius:8px}
.game-title{font-size:22px;font-weight:600;margin-bottom:8px;text-align:center}
.game-meta{font-size:13px;color:var(--text-muted);margin-bottom:20px;padding-bottom:20px;border-bottom:1px solid var(--border-subtle);display:flex;flex-wrap:wrap;gap:8px;justify-content:center}
.game-meta span{background:rgba(255,255,255,0.05);padding:4px 10px;border-radius:6px}
.game-card p{color:var(--text-secondary);margin-bottom:12px;line-height:1.8}
.game-card strong{color:var(--accent-cyan)}
.archive-link{text-align:center;margin:40px 0;padding:20px}
.archive-link a{color:var(--accent-cyan);text-decoration:none;font-size:16px;padding:12px 24px;border:1px solid var(--border-subtle);border-radius:8px;transition:all 0.3s}
.archive-link a:hover{background:rgba(0,229,255,0.1);border-color:var(--accent-cyan)}
footer{text-align:center;padding:40px 24px;color:var(--text-muted);font-size:13px;border-top:1px solid var(--border-subtle)}
footer a{color:var(--accent-cyan);text-decoration:none}
@media(max-width:768px){.hero{padding:120px 20px 40px}.game-card{padding:24px}.team-logo{width:48px;height:48px}}'''

NAV_HTML = '''<nav class="nav-container">
<div class="nav-inner">
<div class="logo"><a href="index.html">BET<span>LEGEND</span></a></div>
<div class="nav-links">
<a href="blog-page9.html">Picks</a>
<div class="dropdown"><button class="dropbtn">Records</button><div class="dropdown-content"><a href="records.html">Overview</a><a href="nfl-records.html">NFL</a><a href="nba-records.html">NBA</a><a href="nhl-records.html">NHL</a><a href="ncaaf-records.html">NCAAF</a><a href="ncaab-records.html">NCAAB</a><a href="mlb-records.html">MLB</a><a href="soccer-records.html">Soccer</a></div></div>
<div class="dropdown"><button class="dropbtn">Sports</button><div class="dropdown-content"><a href="nfl.html">NFL</a><a href="nba.html">NBA</a><a href="nhl.html">NHL</a><a href="ncaaf.html">NCAAF</a><a href="ncaab.html">NCAAB</a><a href="mlb.html">MLB</a><a href="soccer.html">Soccer</a></div></div>
<div class="dropdown"><button class="dropbtn">Resources</button><div class="dropdown-content"><a href="live-odds.html">Live Odds</a><a href="howitworks.html">How It Works</a><a href="bankroll.html">Bankroll Management</a><a href="kelly-criterion.html">Kelly Criterion</a><a href="betting-calculators.html">Calculators</a><a href="bestonlinesportsbook.html">Best Sportsbook</a><a href="betting-glossary.html">Glossary</a><a href="betting-101.html">Betting 101</a></div></div>
<a href="proofofpicks.html">Proof</a>
<a href="news-page3.html">News</a>
<div class="dropdown"><button class="dropbtn">Game of Day</button><div class="dropdown-content"><a href="featured-game-of-the-day-page9.html">Featured Game</a><a href="moneyline-parlay-of-the-day.html">ML Parlay</a></div></div>
<div class="dropdown"><button class="dropbtn">Community</button><div class="dropdown-content"><a href="https://twitter.com/BetLegend2025" target="_blank">Twitter</a><a href="https://discord.gg/NbMc3wCV" target="_blank">Discord</a><a href="contact.html">Contact</a></div></div>
</div>
</div>
</nav>'''

def fetch_espn_schedule(sport):
    """Fetch today's schedule from ESPN API."""
    url = ESPN_ENDPOINTS.get(sport)
    if not url:
        return []

    try:
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())

        games = []
        events = data.get('events', [])

        for event in events:
            competition = event.get('competitions', [{}])[0]
            competitors = competition.get('competitors', [])

            if len(competitors) >= 2:
                away_team = competitors[1] if competitors[0].get('homeAway') == 'home' else competitors[0]
                home_team = competitors[0] if competitors[0].get('homeAway') == 'home' else competitors[1]

                game = {
                    'name': event.get('name', ''),
                    'date': event.get('date', ''),
                    'venue': competition.get('venue', {}).get('fullName', ''),
                    'away': {
                        'name': away_team.get('team', {}).get('displayName', ''),
                        'abbrev': away_team.get('team', {}).get('abbreviation', ''),
                        'record': away_team.get('records', [{}])[0].get('summary', '') if away_team.get('records') else '',
                        'logo': away_team.get('team', {}).get('logo', '')
                    },
                    'home': {
                        'name': home_team.get('team', {}).get('displayName', ''),
                        'abbrev': home_team.get('team', {}).get('abbreviation', ''),
                        'record': home_team.get('records', [{}])[0].get('summary', '') if home_team.get('records') else '',
                        'logo': home_team.get('team', {}).get('logo', '')
                    },
                    'odds': competition.get('odds', [{}])[0] if competition.get('odds') else {},
                    'broadcast': competition.get('broadcasts', [{}])[0].get('names', [''])[0] if competition.get('broadcasts') else ''
                }
                games.append(game)

        return games
    except Exception as e:
        print(f"  Warning: Could not fetch {sport} schedule: {e}")
        return []

def format_game_time(date_str):
    """Convert ESPN date to readable time."""
    try:
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return dt.strftime("%I:%M %p ET")
    except:
        return ""

def generate_game_card(game, sport):
    """Generate HTML for a single game card."""
    away = game['away']
    home = game['home']

    # Get odds info
    odds = game.get('odds', {})
    spread = odds.get('details', '')
    over_under = odds.get('overUnder', '')

    time_str = format_game_time(game.get('date', ''))
    venue = game.get('venue', '')
    broadcast = game.get('broadcast', '')

    # Build meta info
    meta_parts = []
    if time_str:
        meta_parts.append(f'<span>{time_str}</span>')
    if venue:
        meta_parts.append(f'<span>{venue}</span>')
    if spread:
        meta_parts.append(f'<span>{spread}</span>')
    if over_under:
        meta_parts.append(f'<span>O/U {over_under}</span>')
    if broadcast:
        meta_parts.append(f'<span>{broadcast}</span>')

    meta_html = '\n'.join(meta_parts)

    # Use ESPN logos or fallback
    away_logo = away.get('logo') or get_team_logo(sport, away['abbrev'])
    home_logo = home.get('logo') or get_team_logo(sport, home['abbrev'])

    return f'''<article class="game-card">
<div class="teams-display">
<img src="{away_logo}" alt="{away['name']}" class="team-logo">
<span class="vs-badge">VS</span>
<img src="{home_logo}" alt="{home['name']}" class="team-logo">
</div>
<h3 class="game-title">{away['name']} ({away['record']}) @ {home['name']} ({home['record']})</h3>
<div class="game-meta">
{meta_html}
</div>
<p>Game analysis will be added. Check back for picks and predictions.</p>
</article>
'''

def generate_sport_page(sport, games):
    """Generate a complete sport page with games."""
    sport_lower = sport.lower()
    sport_names = {
        'NBA': 'NBA', 'NHL': 'NHL', 'NFL': 'NFL',
        'NCAAB': 'College Basketball', 'NCAAF': 'College Football',
        'MLB': 'MLB', 'SOCCER': 'Soccer'
    }
    sport_name = sport_names.get(sport, sport)

    # Generate game cards
    if games:
        game_cards = '\n'.join([generate_game_card(g, sport) for g in games])
        game_count = len(games)
        subtitle = f"{game_count}-Game Slate - {DATE_DISPLAY}"
    else:
        game_cards = '''<article class="game-card">
<h3 class="game-title">No Games Scheduled</h3>
<p>There are no games scheduled for today. Check back tomorrow for picks and analysis.</p>
</article>'''
        subtitle = f"No games scheduled for {DATE_DISPLAY}"

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{sport_name} Picks - {DATE_DISPLAY} | BetLegend</title>
<meta name="description" content="{sport_name} betting picks and predictions for {DATE_DISPLAY}.">
<link rel="icon" href="https://www.betlegendpicks.com/newlogo.png">
<link rel="canonical" href="https://www.betlegendpicks.com/{sport_lower}.html">
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&family=Poppins:wght@300;400;600&display=swap" rel="stylesheet">
<style>
{STANDARD_CSS}
</style>
<script async src="https://www.googletagmanager.com/gtag/js?id=G-QS8L5TDNLY"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}gtag('js',new Date());gtag('config','G-QS8L5TDNLY');</script>
</head>
<body>

{NAV_HTML}

<header class="hero">
<div class="hero-badge">{sport_name} Picks</div>
<h1>{sport_name} Picks & <span>Analysis</span></h1>
<p>{subtitle}</p>
</header>

<div class="current-date"><h2>{DATE_DISPLAY}</h2></div>

<main>
{game_cards}
</main>

<div class="archive-link">
<a href="{sport_lower}-archive.html">View Archive →</a>
</div>

<footer>
<p>&copy; 2025 BetLegend | <a href="index.html">Home</a> | <a href="{sport_lower}-records.html">{sport_name} Records</a></p>
</footer>

</body>
</html>
'''

def generate_archive_page(sport):
    """Generate or update the archive index page."""
    sport_lower = sport.lower()
    archive_path = os.path.join(REPO, f"{sport_lower}-archive.html")

    # Find all archived pages for this sport
    archive_dir = os.path.join(REPO, "archives", sport_lower)
    archived_files = []

    if os.path.exists(archive_dir):
        for f in os.listdir(archive_dir):
            if f.endswith('.html'):
                # Extract date from filename (e.g., 2025-11-28.html)
                date_match = re.search(r'(\d{4}-\d{2}-\d{2})', f)
                if date_match:
                    archived_files.append({
                        'file': f'archives/{sport_lower}/{f}',
                        'date': date_match.group(1)
                    })

    # Also find old pagination pages and extract their dates
    for f in os.listdir(REPO):
        if re.match(rf'{sport_lower}-page\d+\.html', f):
            # Read the file to extract the date
            try:
                with open(os.path.join(REPO, f), 'r', encoding='utf-8') as file:
                    content = file.read()
                    # Look for date pattern in the content
                    date_match = re.search(r'(\w+day),?\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d+),?\s+(\d{4})', content)
                    if date_match:
                        month_names = {
                            'January': '01', 'February': '02', 'March': '03', 'April': '04',
                            'May': '05', 'June': '06', 'July': '07', 'August': '08',
                            'September': '09', 'October': '10', 'November': '11', 'December': '12'
                        }
                        month = month_names.get(date_match.group(2), '01')
                        day = date_match.group(3).zfill(2)
                        year = date_match.group(4)
                        display_date = f"{date_match.group(2)} {day}, {year}"
                    else:
                        display_date = f"Archive ({f})"
            except:
                display_date = f"Archive ({f})"

            archived_files.append({
                'file': f,
                'date': display_date
            })

    # Sort by date descending
    archived_files.sort(key=lambda x: x['date'], reverse=True)

    # Generate archive links
    if archived_files:
        archive_links = '\n'.join([
            f'<a href="{a["file"]}" class="archive-item">{a["date"]}</a>'
            for a in archived_files
        ])
    else:
        archive_links = '<p>No archived content yet.</p>'

    sport_names = {
        'NBA': 'NBA', 'NHL': 'NHL', 'NFL': 'NFL',
        'NCAAB': 'College Basketball', 'NCAAF': 'College Football',
        'MLB': 'MLB', 'SOCCER': 'Soccer'
    }
    sport_name = sport_names.get(sport, sport)

    archive_html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{sport_name} Archive | BetLegend</title>
<link rel="icon" href="https://www.betlegendpicks.com/newlogo.png">
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&family=Poppins:wght@300;400;600&display=swap" rel="stylesheet">
<style>
{STANDARD_CSS}
.archive-grid{{max-width:800px;margin:0 auto;padding:20px}}
.archive-item{{display:block;padding:16px 24px;margin:8px 0;background:var(--gradient-card);border:1px solid var(--border-subtle);border-radius:12px;color:var(--text-primary);text-decoration:none;transition:all 0.3s}}
.archive-item:hover{{border-color:var(--accent-cyan);transform:translateX(8px)}}
.back-link{{display:inline-block;margin:20px 0;color:var(--accent-cyan);text-decoration:none}}
</style>
</head>
<body>

{NAV_HTML}

<header class="hero">
<div class="hero-badge">Archive</div>
<h1>{sport_name} <span>Archive</span></h1>
<p>Browse past picks and analysis</p>
</header>

<main>
<a href="{sport_lower}.html" class="back-link">← Back to Today's Picks</a>
<div class="archive-grid">
{archive_links}
</div>
</main>

<footer>
<p>&copy; 2025 BetLegend | <a href="index.html">Home</a></p>
</footer>

</body>
</html>
'''

    with open(archive_path, 'w', encoding='utf-8') as f:
        f.write(archive_html)

    print(f"  Updated {sport_lower}-archive.html")

def archive_current_content(sport):
    """Archive the current sport page content."""
    sport_lower = sport.lower()
    current_page = os.path.join(REPO, f"{sport_lower}.html")

    if not os.path.exists(current_page):
        return

    # Read current content
    with open(current_page, 'r', encoding='utf-8') as f:
        content = f.read()

    # Try to extract the date from the current page
    date_match = re.search(r'(\w+day),?\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d+),?\s+(\d{4})', content)

    if date_match:
        month_names = {
            'January': '01', 'February': '02', 'March': '03', 'April': '04',
            'May': '05', 'June': '06', 'July': '07', 'August': '08',
            'September': '09', 'October': '10', 'November': '11', 'December': '12'
        }
        month = month_names.get(date_match.group(2), '01')
        day = date_match.group(3).zfill(2)
        year = date_match.group(4)
        archive_date = f"{year}-{month}-{day}"
    else:
        # Use yesterday's date as fallback
        yesterday = TODAY - timedelta(days=1)
        archive_date = yesterday.strftime("%Y-%m-%d")

    # Create archive directory
    archive_dir = os.path.join(REPO, "archives", sport_lower)
    os.makedirs(archive_dir, exist_ok=True)

    # Save to archive
    archive_file = os.path.join(archive_dir, f"{archive_date}.html")

    # Don't overwrite if already exists
    if not os.path.exists(archive_file):
        with open(archive_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  Archived {sport_lower}.html to archives/{sport_lower}/{archive_date}.html")
    else:
        print(f"  Archive already exists for {archive_date}")

def git_commit_and_push(message):
    """Commit and push changes to GitHub."""
    try:
        # Add all changes
        subprocess.run(['git', '-C', REPO, 'add', '-A'], check=True, capture_output=True)

        # Commit
        commit_msg = f"{message}\n\n🤖 Auto-generated by BetLegend Daily Update System"
        subprocess.run(['git', '-C', REPO, 'commit', '-m', commit_msg], check=True, capture_output=True)

        # Push
        result = subprocess.run(['git', '-C', REPO, 'push'], check=True, capture_output=True)
        print("  Pushed to GitHub successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  Git error: {e}")
        return False

def update_sport(sport, dry_run=False):
    """Update a single sport."""
    print(f"\n{'='*50}")
    print(f"UPDATING {sport}")
    print('='*50)

    # 1. Archive current content
    print("\n[1] Archiving current content...")
    if not dry_run:
        archive_current_content(sport)
    else:
        print("  (dry run - skipping)")

    # 2. Fetch today's schedule
    print("\n[2] Fetching schedule from ESPN...")
    games = fetch_espn_schedule(sport)
    print(f"  Found {len(games)} games")

    # 3. Generate new page
    print("\n[3] Generating new page...")
    new_content = generate_sport_page(sport, games)

    if not dry_run:
        sport_lower = sport.lower()
        page_path = os.path.join(REPO, f"{sport_lower}.html")
        with open(page_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"  Saved {sport_lower}.html")
    else:
        print("  (dry run - skipping)")

    # 4. Update archive index
    print("\n[4] Updating archive index...")
    if not dry_run:
        generate_archive_page(sport)
    else:
        print("  (dry run - skipping)")

def main():
    parser = argparse.ArgumentParser(description='BetLegend Daily Sports Update')
    parser.add_argument('--sport', type=str, help='Update specific sport (NBA, NHL, NFL, NCAAB, NCAAF, MLB, SOCCER)')
    parser.add_argument('--dry-run', action='store_true', help='Preview without making changes')
    parser.add_argument('--no-push', action='store_true', help='Skip git push')
    args = parser.parse_args()

    print("=" * 60)
    print("BETLEGEND DAILY SPORTS UPDATE")
    print(f"Date: {DATE_DISPLAY}")
    print("=" * 60)

    if args.dry_run:
        print("\n*** DRY RUN MODE - No changes will be made ***\n")

    # Determine which sports to update
    if args.sport:
        sports = [args.sport.upper()]
    else:
        # Default: update sports that are in season
        # November = NBA, NHL, NCAAB, NCAAF
        sports = ['NBA', 'NHL', 'NCAAB', 'NCAAF', 'NFL']

    # Update each sport
    for sport in sports:
        if sport in ESPN_ENDPOINTS:
            update_sport(sport, dry_run=args.dry_run)
        else:
            print(f"\nSkipping {sport} - not configured")

    # Commit and push
    if not args.dry_run and not args.no_push:
        print("\n" + "=" * 50)
        print("COMMITTING AND PUSHING TO GITHUB")
        print("=" * 50)
        git_commit_and_push(f"Daily update - {DATE_DISPLAY}")

    print("\n" + "=" * 60)
    print("UPDATE COMPLETE!")
    print("=" * 60)

if __name__ == "__main__":
    main()
