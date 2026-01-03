"""
BETLEGEND DAILY UPDATE SYSTEM
Master script that runs all daily updates:
1. Handicapping Hub (with injuries)
2. Sports pages (NBA, NHL, NFL, NCAAF, NCAAB)
3. Index page featured game
4. Archive rotation for old content

Run this script daily to update the entire site.
"""

import os
import sys
import re
import shutil
from datetime import datetime
from typing import Dict, List

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import existing modules
from handicapping_hub.main import main as run_handicapping_hub, fetch_all_sports_data
from handicapping_hub.injury_scraper import InjuryScraper
from handicapping_hub.featured_game_updater import update_featured_game
from handicapping_hub.game_analysis_generator import GameAnalysisGenerator

# Configuration
REPO_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TODAY = datetime.now()
DATE_STR = TODAY.strftime("%Y-%m-%d")
DATE_DISPLAY = TODAY.strftime("%B %d, %Y")

# ESPN logo URLs by sport
LOGO_URLS = {
    'NBA': 'https://a.espncdn.com/i/teamlogos/nba/500/scoreboard/{abbrev}.png',
    'NHL': 'https://a.espncdn.com/i/teamlogos/nhl/500/scoreboard/{abbrev}.png',
    'NFL': 'https://a.espncdn.com/i/teamlogos/nfl/500/scoreboard/{abbrev}.png',
    'NCAAF': 'https://a.espncdn.com/i/teamlogos/ncaa/500/{id}.png',
    'NCAAB': 'https://a.espncdn.com/i/teamlogos/ncaa/500/{id}.png',
    'MLB': 'https://a.espncdn.com/i/teamlogos/mlb/500/scoreboard/{abbrev}.png',
}

# Team abbreviation mappings for logos
TEAM_ABBREVS = {
    # NBA
    'Golden State Warriors': 'gs', 'Los Angeles Lakers': 'lal', 'Boston Celtics': 'bos',
    'Philadelphia 76ers': 'phi', 'Brooklyn Nets': 'bkn', 'New York Knicks': 'ny',
    'Toronto Raptors': 'tor', 'Chicago Bulls': 'chi', 'Miami Heat': 'mia',
    'Milwaukee Bucks': 'mil', 'Cleveland Cavaliers': 'cle', 'Denver Nuggets': 'den',
    'Phoenix Suns': 'phx', 'Dallas Mavericks': 'dal', 'Houston Rockets': 'hou',
    'San Antonio Spurs': 'sa', 'Memphis Grizzlies': 'mem', 'New Orleans Pelicans': 'no',
    'Minnesota Timberwolves': 'min', 'Oklahoma City Thunder': 'okc', 'Portland Trail Blazers': 'por',
    'Utah Jazz': 'utah', 'Sacramento Kings': 'sac', 'Los Angeles Clippers': 'lac',
    'Indiana Pacers': 'ind', 'Detroit Pistons': 'det', 'Atlanta Hawks': 'atl',
    'Charlotte Hornets': 'cha', 'Washington Wizards': 'wsh', 'Orlando Magic': 'orl',
    # NHL
    'Boston Bruins': 'bos', 'Toronto Maple Leafs': 'tor', 'Florida Panthers': 'fla',
    'Tampa Bay Lightning': 'tb', 'New York Rangers': 'nyr', 'Carolina Hurricanes': 'car',
    'New Jersey Devils': 'nj', 'New York Islanders': 'nyi', 'Pittsburgh Penguins': 'pit',
    'Washington Capitals': 'wsh', 'Philadelphia Flyers': 'phi', 'Columbus Blue Jackets': 'cbj',
    'Detroit Red Wings': 'det', 'Ottawa Senators': 'ott', 'Buffalo Sabres': 'buf',
    'Montreal Canadiens': 'mtl', 'Colorado Avalanche': 'col', 'Dallas Stars': 'dal',
    'Winnipeg Jets': 'wpg', 'Minnesota Wild': 'min', 'St. Louis Blues': 'stl',
    'Nashville Predators': 'nsh', 'Chicago Blackhawks': 'chi', 'Arizona Coyotes': 'ari',
    'Vegas Golden Knights': 'vgk', 'Edmonton Oilers': 'edm', 'Calgary Flames': 'cgy',
    'Vancouver Canucks': 'van', 'Seattle Kraken': 'sea', 'Los Angeles Kings': 'la',
    'Anaheim Ducks': 'ana', 'San Jose Sharks': 'sj',
    # NFL
    'Kansas City Chiefs': 'kc', 'Buffalo Bills': 'buf', 'Miami Dolphins': 'mia',
    'New England Patriots': 'ne', 'New York Jets': 'nyj', 'Baltimore Ravens': 'bal',
    'Pittsburgh Steelers': 'pit', 'Cleveland Browns': 'cle', 'Cincinnati Bengals': 'cin',
    'Houston Texans': 'hou', 'Indianapolis Colts': 'ind', 'Jacksonville Jaguars': 'jax',
    'Tennessee Titans': 'ten', 'Denver Broncos': 'den', 'Las Vegas Raiders': 'lv',
    'Los Angeles Chargers': 'lac', 'Dallas Cowboys': 'dal', 'Philadelphia Eagles': 'phi',
    'New York Giants': 'nyg', 'Washington Commanders': 'wsh', 'Chicago Bears': 'chi',
    'Detroit Lions': 'det', 'Green Bay Packers': 'gb', 'Minnesota Vikings': 'min',
    'Atlanta Falcons': 'atl', 'Carolina Panthers': 'car', 'New Orleans Saints': 'no',
    'Tampa Bay Buccaneers': 'tb', 'Arizona Cardinals': 'ari', 'Los Angeles Rams': 'lar',
    'San Francisco 49ers': 'sf', 'Seattle Seahawks': 'sea',
}


def is_valid_record(record: str) -> bool:
    """Check if a record is valid (not 0-0, not empty, has real values)"""
    if not record or record in ('', '-', 'N/A', '0-0', None):
        return False
    try:
        parts = str(record).split('-')
        if len(parts) >= 2:
            wins = int(parts[0])
            losses = int(parts[1])
            # A valid season record should have some games played
            return (wins + losses) >= 1
    except:
        pass
    return False


def has_real_data(sport: str, away_stats: dict, home_stats: dict) -> bool:
    """
    Check if stats contain real data vs placeholder defaults.
    Returns False if data appears to be fake/placeholder.
    """
    # Check records first - most important indicator
    away_record = away_stats.get('record', '')
    home_record = home_stats.get('record', '')

    if not is_valid_record(away_record) or not is_valid_record(home_record):
        return False

    # Check for identical PPG (a sign of defaults being used)
    away_ppg = away_stats.get('ppg', 0)
    home_ppg = home_stats.get('ppg', 0)

    # If both teams have exactly the same PPG, likely defaults
    if away_ppg and home_ppg:
        try:
            if float(away_ppg) == float(home_ppg) and float(away_ppg) in [72.0, 110.0, 22.0, 28.0, 3.0]:
                return False
        except:
            pass

    return True


class SportsPageGenerator:
    """Generates daily sports pages with comprehensive game analysis"""

    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.injury_scraper = InjuryScraper()
        self.analysis_generator = GameAnalysisGenerator()

    def get_team_logo_url(self, sport: str, team: Dict) -> str:
        """Get the logo URL for a team"""
        name = team.get('displayName', team.get('name', ''))
        abbrev = team.get('abbreviation', '').lower()
        team_id = team.get('id', '')

        # For college sports, use team ID
        if sport in ['NCAAF', 'NCAAB']:
            if team_id:
                return LOGO_URLS[sport].format(id=team_id)
            return ''

        # For pro sports, use abbreviation mapping
        if name in TEAM_ABBREVS:
            abbrev = TEAM_ABBREVS[name]

        return LOGO_URLS.get(sport, '').format(abbrev=abbrev)

    def generate_game_card(self, sport: str, game_data: Dict, injuries: Dict) -> str:
        """Generate HTML for a single game card"""
        game = game_data.get('game', {})
        away = game.get('away', {})
        home = game.get('home', {})

        away_name = away.get('displayName', away.get('name', 'Away'))
        home_name = home.get('displayName', home.get('name', 'Home'))
        away_abbrev = away.get('abbreviation', 'AWY')
        home_abbrev = home.get('abbreviation', 'HME')

        # Get logos
        away_logo = self.get_team_logo_url(sport, away)
        home_logo = self.get_team_logo_url(sport, home)

        # Get game time
        game_time = game.get('date', '')
        if game_time:
            try:
                dt = datetime.fromisoformat(game_time.replace('Z', '+00:00'))
                game_time = dt.strftime('%I:%M %p ET')
            except:
                game_time = ''

        # Get venue
        venue = game.get('venue', {})
        venue_name = venue.get('fullName', '') if isinstance(venue, dict) else str(venue)

        # Get odds - NEVER use placeholders, use empty string if no data
        odds = game_data.get('odds', {})
        spread = odds.get('spread', '')
        total = odds.get('total', '')
        away_ml = odds.get('away_ml', '')
        home_ml = odds.get('home_ml', '')

        # Get team stats
        away_stats = game_data.get('away_stats', {})
        home_stats = game_data.get('home_stats', {})
        away_record = away_stats.get('record', away.get('record', ''))
        home_record = home_stats.get('record', home.get('record', ''))

        # CRITICAL: Validate data is real before displaying
        if not is_valid_record(away_record):
            away_record = ''  # Show nothing instead of fake 0-0
        if not is_valid_record(home_record):
            home_record = ''

        # Get injuries
        away_injuries = injuries.get(away_name, [])
        home_injuries = injuries.get(home_name, [])

        injury_html = self._format_injuries(away_injuries, home_injuries, away_abbrev, home_abbrev)

        # CRITICAL: Only generate analysis if we have REAL data
        # Skip games entirely if data is fake/placeholder - NO PLACEHOLDERS EVER
        if has_real_data(sport, away_stats, home_stats):
            analysis_html = self.analysis_generator.generate_analysis(sport, game_data)
        else:
            # SKIP THIS GAME - return empty string to exclude from output
            print(f"    [SKIP GAME] {away_name} @ {home_name} - insufficient real data, NOT including in output")
            return ''  # Return empty string to skip this game entirely

        return f'''<article class="game-card">
<div class="teams-display">
<img alt="{away_name}" class="team-logo" onerror="this.style.display='none'" src="{away_logo}"/>
<span class="vs-badge">@</span>
<img alt="{home_name}" class="team-logo" onerror="this.style.display='none'" src="{home_logo}"/>
</div>
<h3 class="game-title">{away_name} @ {home_name}</h3>
<div class="game-meta">
<span>{game_time}</span>
{f'<span>{away_record} vs {home_record}</span>' if away_record and home_record else ''}
{f'<span>{venue_name}</span>' if venue_name else ''}
</div>
<div class="stat-row">
<div class="stat-item"><span class="value">{spread}</span><span class="label">Spread</span></div>
<div class="stat-item"><span class="value">{total}</span><span class="label">O/U</span></div>
<div class="stat-item"><span class="value">{away_ml}</span><span class="label">{away_abbrev} ML</span></div>
<div class="stat-item"><span class="value">{home_ml}</span><span class="label">{home_abbrev} ML</span></div>
</div>
{injury_html}
<div class="deep-analysis">
{analysis_html}
</div>
<p class="data-source">Data: ESPN, The Odds API | Lines subject to change</p>
</article>
'''

    def _format_injuries(self, away_injuries: List, home_injuries: List, away_abbrev: str, home_abbrev: str) -> str:
        """Format injuries for display"""
        def format_team(injuries: List, abbrev: str) -> str:
            if not injuries:
                return f"<strong>{abbrev}:</strong> No key injuries"
            out = [i for i in injuries if 'out' in i.get('status', '').lower()]
            q = [i for i in injuries if 'questionable' in i.get('status', '').lower()]
            parts = []
            if out:
                names = [f"{i.get('player', '')} ({i.get('position', '')})" for i in out[:3]]
                parts.append(f"<strong>{abbrev} OUT:</strong> {', '.join(names)}")
            if q and len(out) < 2:
                names = [f"{i.get('player', '')} ({i.get('position', '')})" for i in q[:2]]
                parts.append(f"<strong>Q:</strong> {', '.join(names)}")
            return ' | '.join(parts) if parts else f"<strong>{abbrev}:</strong> No key injuries"

        if not away_injuries and not home_injuries:
            return ''

        return f'''<div class="injury-section" style="background:rgba(255,50,50,0.1);border:1px solid rgba(255,50,50,0.2);border-radius:10px;padding:12px;margin:12px 0;">
<p style="font-size:0.75rem;color:#ff6b6b;margin-bottom:6px;font-weight:600;">INJURIES</p>
<p style="font-size:0.8rem;color:#ccc;margin:4px 0;">{format_team(away_injuries, away_abbrev)}</p>
<p style="font-size:0.8rem;color:#ccc;margin:4px 0;">{format_team(home_injuries, home_abbrev)}</p>
</div>'''

    def generate_sport_page(self, sport: str, games: List[Dict], injuries: Dict) -> str:
        """Generate the full HTML for a sports page"""
        game_count = len(games)

        # Generate all game cards
        cards_html = ''
        for game_data in games:
            cards_html += self.generate_game_card(sport, game_data, injuries)

        return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<title>{sport} Analysis - {DATE_DISPLAY} | BetLegend</title>
<meta content="{sport} statistical analysis for {DATE_DISPLAY}. Advanced stats, efficiency ratings, and betting trends." name="description"/>
<link href="https://www.betlegendpicks.com/newlogo.png" rel="icon"/>
<link href="https://www.betlegendpicks.com/{sport.lower()}.html" rel="canonical"/>
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
.nav-container{{position:fixed;top:0;left:0;right:0;z-index:1000;background:rgba(0,0,0,0.85);backdrop-filter:blur(10px);border-bottom:1px solid rgba(0,224,255,0.3)}}
.nav-inner{{max-width:1400px;margin:0 auto;display:flex;align-items:center;justify-content:center;gap:12px;padding:18px 5% 18px 280px}}
.logo{{position:fixed;top:15px;left:15px;z-index:1001}}
.logo a{{font-family:var(--font-primary);font-size:2.5rem;font-weight:900;color:#fff;text-decoration:none;text-shadow:0 0 10px rgba(255,255,255,0.8)}}
.logo a span{{color:var(--neon-cyan);text-shadow:0 0 15px rgba(0,255,255,1)}}
.nav-links{{display:flex;align-items:center;gap:15px;flex-wrap:wrap}}
.nav-links>a,.dropbtn{{font-family:var(--font-secondary);color:#fff;text-decoration:none;font-size:18px;font-weight:600;padding:12px 20px;border-radius:8px;background:none;border:none;cursor:pointer;text-transform:uppercase;letter-spacing:1.5px}}
.nav-links>a:hover,.dropbtn:hover{{color:var(--neon-gold);text-shadow:0 0 15px var(--neon-gold)}}
.dropdown{{position:relative}}
.dropdown-content{{display:none;position:absolute;top:100%;left:0;background:rgba(0,0,0,0.98);min-width:200px;border:2px solid rgba(0,224,255,0.5);border-radius:10px;padding:15px 0;margin-top:10px}}
.dropdown-content a{{color:var(--neon-cyan);padding:14px 20px;display:block;text-decoration:none}}
.dropdown-content a:hover{{background:rgba(0,224,255,0.2);color:#fff}}
.dropdown:hover .dropdown-content{{display:block}}
body{{background:var(--bg-primary);color:var(--text-primary);font-family:system-ui,sans-serif;line-height:1.7}}
.hero{{padding:160px 24px 60px;text-align:center}}
.hero-badge{{display:inline-block;background:rgba(0,229,255,0.1);border:1px solid rgba(0,229,255,0.2);padding:8px 16px;border-radius:50px;font-size:12px;color:var(--accent-cyan);text-transform:uppercase;letter-spacing:1px;margin-bottom:20px}}
.hero h1{{font-size:clamp(36px,6vw,56px);font-weight:700;margin-bottom:12px}}
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
.game-card strong{{color:var(--accent-cyan)}}
.stat-row{{display:flex;flex-wrap:wrap;gap:12px;margin:16px 0;padding:16px;background:rgba(0,0,0,0.3);border-radius:12px;border:1px solid var(--border-subtle)}}
.stat-item{{flex:1;min-width:100px;text-align:center;padding:8px}}
.stat-item .value{{font-family:var(--font-primary);font-size:1.3rem;font-weight:700;color:var(--accent-gold)}}
.stat-item .label{{font-size:0.7rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.5px}}
footer{{text-align:center;padding:40px 24px;color:var(--text-muted);font-size:13px;border-top:1px solid var(--border-subtle)}}
footer a{{color:var(--accent-cyan);text-decoration:none}}
.data-source{{font-size:11px;color:var(--text-muted);text-align:center;margin-top:8px;padding-top:12px;border-top:1px solid var(--border-subtle)}}
.deep-analysis{{margin:20px 0;padding:20px;background:rgba(0,0,0,0.2);border-radius:12px;border-left:3px solid var(--accent-cyan)}}
.analysis-section{{margin-bottom:16px;padding-bottom:16px;border-bottom:1px solid rgba(255,255,255,0.05)}}
.analysis-section:last-child{{border-bottom:none;margin-bottom:0;padding-bottom:0}}
.analysis-section h4{{color:var(--accent-gold);font-size:0.9rem;text-transform:uppercase;letter-spacing:1px;margin-bottom:10px;font-family:var(--font-primary)}}
.analysis-section p{{font-size:0.85rem;color:var(--text-secondary);margin:6px 0;line-height:1.6}}
.analysis-section ul{{margin:8px 0;padding-left:20px}}
.analysis-section li{{font-size:0.85rem;color:var(--text-secondary);margin:4px 0}}
.stats-comparison{{display:grid;gap:8px}}
.stat-compare-row{{display:flex;justify-content:space-between;padding:6px 10px;background:rgba(255,255,255,0.03);border-radius:6px}}
.stat-compare-row .stat-label{{color:var(--text-muted);font-size:0.8rem}}
.stat-compare-row .stat-away,.stat-compare-row .stat-home{{font-size:0.85rem;font-weight:600}}
.stat-compare-row .stat-away{{color:var(--accent-cyan)}}
.stat-compare-row .stat-home{{color:var(--accent-gold)}}
@media(max-width:768px){{.hero{{padding:160px 20px 40px}}.game-card{{padding:24px}}.team-logo{{width:48px;height:48px}}.stat-row{{flex-direction:column}}.deep-analysis{{padding:15px}}}}
</style>
<script async="" src="https://www.googletagmanager.com/gtag/js?id=G-QS8L5TDNLY"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}gtag('js',new Date());gtag('config','G-QS8L5TDNLY');</script>
</head>
<body>
<nav class="nav-container">
<div class="nav-inner">
<div class="logo"><a href="index.html">BET<span>LEGEND</span></a></div>
<div class="nav-links">
<a href="handicapping-hub.html" style="background:linear-gradient(135deg,#ff6b00,#ff8c00);color:#fff;border-radius:8px;">Handicapping Hub</a>
<a href="blog-page10.html">Picks</a>
<div class="dropdown"><button class="dropbtn">Records</button><div class="dropdown-content"><a href="records.html">Overview</a><a href="nfl-records.html">NFL</a><a href="nba-records.html">NBA</a><a href="nhl-records.html">NHL</a><a href="ncaaf-records.html">NCAAF</a><a href="ncaab-records.html">NCAAB</a><a href="mlb-records.html">MLB</a><a href="soccer-records.html">Soccer</a></div></div>
<div class="dropdown"><button class="dropbtn">Sports</button><div class="dropdown-content"><a href="nfl.html">NFL</a><a href="nba.html">NBA</a><a href="nhl.html">NHL</a><a href="ncaaf.html">NCAAF</a><a href="ncaab.html">NCAAB</a><a href="mlb.html">MLB</a><a href="soccer.html">Soccer</a></div></div>
<div class="dropdown"><button class="dropbtn">Resources</button><div class="dropdown-content"><a href="live-odds.html">Live Odds</a><a href="howitworks.html">How It Works</a><a href="bankroll.html">Bankroll</a><a href="kelly-criterion.html">Kelly Criterion</a><a href="betting-calculators.html">Calculators</a><a href="bestonlinesportsbook.html">Best Sportsbook</a><a href="betting-glossary.html">Glossary</a><a href="betting-101.html">Betting 101</a></div></div>
<a href="proofofpicks.html">Proof</a>
<a href="news-page3.html">News</a>
<div class="dropdown"><button class="dropbtn">Game of Day</button><div class="dropdown-content"><a href="featured-game-of-the-day-page12.html">Featured Game</a><a href="moneyline-parlay-of-the-day.html">ML Parlay</a></div></div>
</div>
</div>
</nav>
<header class="hero">
<div class="hero-badge">Statistical Analysis</div>
<h1>{sport} <span>Analysis</span></h1>
<p>{game_count}-Game Slate | Advanced Stats &amp; Betting Trends</p>
</header>
<div class="current-date"><h2>{DATE_DISPLAY}</h2></div>
<main>
{cards_html}
</main>
<footer>
<p>© 2025 BetLegend. For entertainment purposes only.</p>
<p><a href="index.html">Home</a> | <a href="howitworks.html">How It Works</a></p>
</footer>
</body>
</html>'''

    def rotate_archives(self, sport: str, max_pages: int = 30):
        """Rotate archive pages - move old content to numbered pages"""
        sport_lower = sport.lower()
        main_page = os.path.join(self.repo_path, f'{sport_lower}.html')

        if not os.path.exists(main_page):
            return

        # Find the highest existing page number
        highest_page = 1
        for i in range(2, max_pages + 1):
            page_path = os.path.join(self.repo_path, f'{sport_lower}-page{i}.html')
            if os.path.exists(page_path):
                highest_page = i
            else:
                break

        # Rotate pages: move page N-1 to page N, N-2 to N-1, etc.
        for i in range(highest_page, 1, -1):
            old_path = os.path.join(self.repo_path, f'{sport_lower}-page{i}.html')
            new_path = os.path.join(self.repo_path, f'{sport_lower}-page{i+1}.html')
            if os.path.exists(old_path):
                shutil.copy(old_path, new_path)
                print(f"    Rotated {sport_lower}-page{i}.html -> page{i+1}.html")

        # Move main page to page2
        page2_path = os.path.join(self.repo_path, f'{sport_lower}-page2.html')
        shutil.copy(main_page, page2_path)
        print(f"    Archived {sport_lower}.html -> page2.html")


class DailyUpdater:
    """Main class that orchestrates all daily updates"""

    def __init__(self, repo_path: str = None):
        self.repo_path = repo_path or REPO_PATH
        self.page_generator = SportsPageGenerator(self.repo_path)
        self.injury_scraper = InjuryScraper()

    def run(self):
        """Run all daily updates"""
        print("\n" + "=" * 70)
        print("  BETLEGEND DAILY UPDATE SYSTEM")
        print("  Automated Site-Wide Update")
        print("=" * 70)
        print(f"\nDate: {DATE_DISPLAY}")
        print(f"Repository: {self.repo_path}")

        # Step 1: Fetch all sports data
        print("\n[STEP 1] Fetching sports data...")
        all_data = fetch_all_sports_data()

        # Step 2: Fetch injuries
        print("\n[STEP 2] Fetching injuries...")
        injuries_by_sport = {}
        for sport in ['NBA', 'NHL', 'NFL', 'MLB']:
            injuries = self.injury_scraper.get_all_injuries(sport)
            if injuries:
                injuries_by_sport[sport] = injuries
                print(f"    {sport}: {len(injuries)} teams with injuries")

        # Step 3: DISABLED - Sports pages should have WRITTEN ARTICLES not auto-generated stats
        # The Handicapping Hub is for stats. Sports pages are for articles.
        # DO NOT auto-update sports pages with game-card content!
        print("\n[STEP 3] Sports pages - SKIPPED (manual update with written articles)")
        # DISABLED - DO NOT ENABLE THIS CODE
        # for sport in ['NBA', 'NHL', 'NFL', 'NCAAF', 'NCAAB']:
        #     sport_data = all_data.get(sport, {})
        #     games = sport_data.get('games', [])
        #
        #     if not games:
        #         print(f"    {sport}: No games today, skipping")
        #         continue
        #
        #     print(f"    {sport}: {len(games)} games")
        #
        #     # Rotate archives first
        #     self.page_generator.rotate_archives(sport)
        #
        #     # Generate new page
        #     injuries = injuries_by_sport.get(sport, {})
        #     html_content = self.page_generator.generate_sport_page(sport, games, injuries)
        #
        #     # Save to file
        #     page_path = os.path.join(self.repo_path, f'{sport.lower()}.html')
        #     with open(page_path, 'w', encoding='utf-8') as f:
        #         f.write(html_content)
        #     print(f"    Saved {sport.lower()}.html")

        # Step 4: Update handicapping hub
        print("\n[STEP 4] Updating handicapping hub...")
        try:
            run_handicapping_hub()
        except Exception as e:
            print(f"    [WARN] Handicapping hub update failed: {e}")

        # Step 5: Update index featured game
        print("\n[STEP 5] Updating index featured game...")
        try:
            update_featured_game(all_data)
        except Exception as e:
            print(f"    [WARN] Featured game update failed: {e}")

        # Summary
        print("\n" + "=" * 70)
        print("  DAILY UPDATE COMPLETE!")
        print("=" * 70)

        total_games = sum(len(d.get('games', [])) for d in all_data.values())
        print(f"\n  Total Games Updated: {total_games}")
        print("\n  Files Updated:")
        print("    - handicapping-hub.html")
        print("    - index.html (featured game)")
        for sport in ['NBA', 'NHL', 'NFL', 'NCAAF', 'NCAAB']:
            games = all_data.get(sport, {}).get('games', [])
            if games:
                print(f"    - {sport.lower()}.html ({len(games)} games)")

        print("\n" + "=" * 70)
        return 0


def main():
    """Entry point"""
    updater = DailyUpdater()
    return updater.run()


if __name__ == '__main__':
    sys.exit(main())
