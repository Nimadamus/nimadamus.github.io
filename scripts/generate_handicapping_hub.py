#!/usr/bin/env python3
"""
Generate Handicapping Hub with FULL ADVANCED STATS displayed horizontally
- Light gray background, white cards
- Tabs for sports
- ALL stats displayed horizontally across each game card
"""
import requests
import json
from datetime import datetime
import os

ODDS_API_KEY = "deeac7e7af6a8f1a5ac84c625e04973a"
REPO_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SPORT_CONFIG = {
    'NFL': {'espn_path': 'football/nfl', 'odds_key': 'americanfootball_nfl'},
    'NBA': {'espn_path': 'basketball/nba', 'odds_key': 'basketball_nba'},
    'NHL': {'espn_path': 'hockey/nhl', 'odds_key': 'icehockey_nhl'},
    'NCAAB': {'espn_path': 'basketball/mens-college-basketball', 'odds_key': 'basketball_ncaab'},
    'NCAAF': {'espn_path': 'football/college-football', 'odds_key': 'americanfootball_ncaaf'},
}

def get_espn_games(sport_path):
    """Get today's games from ESPN with team stats"""
    date_str = datetime.now().strftime('%Y%m%d')
    url = f"https://site.api.espn.com/apis/site/v2/sports/{sport_path}/scoreboard?dates={date_str}"
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            return resp.json().get('events', [])
    except Exception as e:
        print(f"ESPN error: {e}")
    return []

def get_team_stats(sport_path, team_id):
    """Get detailed team statistics"""
    stats = {}
    try:
        url = f"https://site.api.espn.com/apis/site/v2/sports/{sport_path}/teams/{team_id}/statistics"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            for split in data.get('results', {}).get('splits', {}).get('categories', []):
                for stat in split.get('stats', []):
                    stats[stat.get('name', '')] = stat.get('displayValue', stat.get('value', '-'))
    except:
        pass
    return stats

def get_odds(sport_key):
    """Get current odds from The Odds API"""
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds"
    params = {
        'apiKey': ODDS_API_KEY,
        'regions': 'us',
        'markets': 'spreads,h2h,totals',
        'oddsFormat': 'american'
    }
    try:
        resp = requests.get(url, params=params, timeout=15)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        print(f"Odds API error: {e}")
    return []

def match_odds(odds_data, away_name, home_name):
    """Find odds for a specific game"""
    result = {'spread': '-', 'total': '-', 'ml_away': '-', 'ml_home': '-', 'spread_away': '-'}

    for game in odds_data:
        api_away = game.get('away_team', '').lower()
        api_home = game.get('home_team', '').lower()

        if (away_name.lower() in api_away or api_away in away_name.lower()) and \
           (home_name.lower() in api_home or api_home in home_name.lower()):

            for bm in game.get('bookmakers', [])[:1]:
                for market in bm.get('markets', []):
                    if market['key'] == 'spreads':
                        for o in market['outcomes']:
                            if home_name.lower() in o['name'].lower():
                                spread = o['point']
                                result['spread'] = f"{spread:+.1f}" if spread >= 0 else f"{spread:.1f}"
                            else:
                                spread = o['point']
                                result['spread_away'] = f"{spread:+.1f}" if spread >= 0 else f"{spread:.1f}"
                    elif market['key'] == 'totals':
                        for o in market['outcomes']:
                            if o['name'] == 'Over':
                                result['total'] = str(o['point'])
                    elif market['key'] == 'h2h':
                        for o in market['outcomes']:
                            ml = o['price']
                            ml_str = f"{ml:+d}" if isinstance(ml, int) else str(ml)
                            if home_name.lower() in o['name'].lower():
                                result['ml_home'] = ml_str
                            else:
                                result['ml_away'] = ml_str
            break

    return result

def generate_game_card(sport, game_data, odds):
    """Generate a game card with FULL horizontal stats"""

    away_name = game_data['away_name']
    home_name = game_data['home_name']
    away_abbr = game_data['away_abbr']
    home_abbr = game_data['home_abbr']
    away_record = game_data['away_record']
    home_record = game_data['home_record']
    game_time = game_data['game_time']
    venue = game_data['venue']
    network = game_data['network']
    away_stats = game_data.get('away_stats', {})
    home_stats = game_data.get('home_stats', {})

    # Logo URLs
    logo_base = "https://a.espncdn.com/i/teamlogos"
    if sport == 'NFL':
        away_logo = f"{logo_base}/nfl/500/scoreboard/{away_abbr.lower()}.png"
        home_logo = f"{logo_base}/nfl/500/scoreboard/{home_abbr.lower()}.png"
    elif sport == 'NBA':
        away_logo = f"{logo_base}/nba/500/scoreboard/{away_abbr.lower()}.png"
        home_logo = f"{logo_base}/nba/500/scoreboard/{home_abbr.lower()}.png"
    elif sport == 'NHL':
        away_logo = f"{logo_base}/nhl/500/scoreboard/{away_abbr.lower()}.png"
        home_logo = f"{logo_base}/nhl/500/scoreboard/{home_abbr.lower()}.png"
    else:
        away_logo = f"{logo_base}/ncaa/500/scoreboard/{away_abbr.lower()}.png"
        home_logo = f"{logo_base}/ncaa/500/scoreboard/{home_abbr.lower()}.png"

    spread = odds.get('spread', '-')
    spread_away = odds.get('spread_away', '-')
    total = odds.get('total', '-')
    ml_away = odds.get('ml_away', '-')
    ml_home = odds.get('ml_home', '-')

    # Get stats based on sport
    if sport in ['NBA', 'NCAAB']:
        away_ppg = away_stats.get('avgPoints', away_stats.get('pointsPerGame', '-'))
        home_ppg = home_stats.get('avgPoints', home_stats.get('pointsPerGame', '-'))
        away_opp_ppg = away_stats.get('avgPointsAgainst', away_stats.get('oppPointsPerGame', '-'))
        home_opp_ppg = home_stats.get('avgPointsAgainst', home_stats.get('oppPointsPerGame', '-'))
        away_rpg = away_stats.get('avgRebounds', away_stats.get('reboundsPerGame', '-'))
        home_rpg = home_stats.get('avgRebounds', home_stats.get('reboundsPerGame', '-'))
        away_apg = away_stats.get('avgAssists', away_stats.get('assistsPerGame', '-'))
        home_apg = home_stats.get('avgAssists', home_stats.get('assistsPerGame', '-'))

        stats_html = f'''
            <div class="stats-row">
                <div class="stat-box"><div class="stat-label">RECORD</div><div class="stat-values"><span>{away_record}</span><span>{home_record}</span></div></div>
                <div class="stat-box"><div class="stat-label">PPG</div><div class="stat-values"><span>{away_ppg}</span><span>{home_ppg}</span></div></div>
                <div class="stat-box"><div class="stat-label">OPP PPG</div><div class="stat-values"><span>{away_opp_ppg}</span><span>{home_opp_ppg}</span></div></div>
                <div class="stat-box"><div class="stat-label">RPG</div><div class="stat-values"><span>{away_rpg}</span><span>{home_rpg}</span></div></div>
                <div class="stat-box"><div class="stat-label">APG</div><div class="stat-values"><span>{away_apg}</span><span>{home_apg}</span></div></div>
                <div class="stat-box"><div class="stat-label">SPREAD</div><div class="stat-values"><span>{spread_away}</span><span>{spread}</span></div></div>
                <div class="stat-box"><div class="stat-label">ML</div><div class="stat-values"><span>{ml_away}</span><span>{ml_home}</span></div></div>
                <div class="stat-box"><div class="stat-label">O/U</div><div class="stat-values"><span colspan="2">{total}</span></div></div>
            </div>
        '''
    elif sport in ['NFL', 'NCAAF']:
        away_ppg = away_stats.get('avgPoints', away_stats.get('pointsPerGame', '-'))
        home_ppg = home_stats.get('avgPoints', home_stats.get('pointsPerGame', '-'))
        away_opp_ppg = away_stats.get('avgPointsAgainst', away_stats.get('oppPointsPerGame', '-'))
        home_opp_ppg = home_stats.get('avgPointsAgainst', home_stats.get('oppPointsPerGame', '-'))
        away_ypg = away_stats.get('totalYardsPerGame', away_stats.get('yardsPerGame', '-'))
        home_ypg = home_stats.get('totalYardsPerGame', home_stats.get('yardsPerGame', '-'))
        away_rush = away_stats.get('rushingYardsPerGame', '-')
        home_rush = home_stats.get('rushingYardsPerGame', '-')
        away_pass = away_stats.get('passingYardsPerGame', '-')
        home_pass = home_stats.get('passingYardsPerGame', '-')

        stats_html = f'''
            <div class="stats-row">
                <div class="stat-box"><div class="stat-label">RECORD</div><div class="stat-values"><span>{away_record}</span><span>{home_record}</span></div></div>
                <div class="stat-box"><div class="stat-label">PPG</div><div class="stat-values"><span>{away_ppg}</span><span>{home_ppg}</span></div></div>
                <div class="stat-box"><div class="stat-label">OPP PPG</div><div class="stat-values"><span>{away_opp_ppg}</span><span>{home_opp_ppg}</span></div></div>
                <div class="stat-box"><div class="stat-label">YPG</div><div class="stat-values"><span>{away_ypg}</span><span>{home_ypg}</span></div></div>
                <div class="stat-box"><div class="stat-label">RUSH YPG</div><div class="stat-values"><span>{away_rush}</span><span>{home_rush}</span></div></div>
                <div class="stat-box"><div class="stat-label">PASS YPG</div><div class="stat-values"><span>{away_pass}</span><span>{home_pass}</span></div></div>
                <div class="stat-box"><div class="stat-label">SPREAD</div><div class="stat-values"><span>{spread_away}</span><span>{spread}</span></div></div>
                <div class="stat-box"><div class="stat-label">ML</div><div class="stat-values"><span>{ml_away}</span><span>{ml_home}</span></div></div>
                <div class="stat-box"><div class="stat-label">O/U</div><div class="stat-values"><span>{total}</span></div></div>
            </div>
        '''
    else:  # NHL
        away_gpg = away_stats.get('goalsFor', away_stats.get('goalsPerGame', '-'))
        home_gpg = home_stats.get('goalsFor', home_stats.get('goalsPerGame', '-'))
        away_gapg = away_stats.get('goalsAgainst', away_stats.get('goalsAgainstPerGame', '-'))
        home_gapg = home_stats.get('goalsAgainst', home_stats.get('goalsAgainstPerGame', '-'))
        away_pp = away_stats.get('powerPlayPct', '-')
        home_pp = home_stats.get('powerPlayPct', '-')
        away_pk = away_stats.get('penaltyKillPct', '-')
        home_pk = home_stats.get('penaltyKillPct', '-')

        stats_html = f'''
            <div class="stats-row">
                <div class="stat-box"><div class="stat-label">RECORD</div><div class="stat-values"><span>{away_record}</span><span>{home_record}</span></div></div>
                <div class="stat-box"><div class="stat-label">GF/G</div><div class="stat-values"><span>{away_gpg}</span><span>{home_gpg}</span></div></div>
                <div class="stat-box"><div class="stat-label">GA/G</div><div class="stat-values"><span>{away_gapg}</span><span>{home_gapg}</span></div></div>
                <div class="stat-box"><div class="stat-label">PP%</div><div class="stat-values"><span>{away_pp}</span><span>{home_pp}</span></div></div>
                <div class="stat-box"><div class="stat-label">PK%</div><div class="stat-values"><span>{away_pk}</span><span>{home_pk}</span></div></div>
                <div class="stat-box"><div class="stat-label">SPREAD</div><div class="stat-values"><span>{spread_away}</span><span>{spread}</span></div></div>
                <div class="stat-box"><div class="stat-label">ML</div><div class="stat-values"><span>{ml_away}</span><span>{ml_home}</span></div></div>
                <div class="stat-box"><div class="stat-label">O/U</div><div class="stat-values"><span>{total}</span></div></div>
            </div>
        '''

    return f'''
        <div class="game-card">
            <div class="game-header">
                <div class="game-time">{game_time}</div>
                <div class="game-info">{venue} • {network}</div>
            </div>

            <div class="teams-header">
                <div class="team-col away">
                    <img src="{away_logo}" alt="{away_abbr}" class="team-logo" onerror="this.style.display='none'">
                    <span class="team-name">{away_name}</span>
                </div>
                <div class="vs-col">@</div>
                <div class="team-col home">
                    <img src="{home_logo}" alt="{home_abbr}" class="team-logo" onerror="this.style.display='none'">
                    <span class="team-name">{home_name}</span>
                </div>
            </div>

            {stats_html}

            <div class="line-movement">
                <span>📊 Line Movement: {spread} (current)</span>
            </div>
        </div>
'''

def generate_page():
    """Generate the full handicapping hub page"""

    today = datetime.now()
    date_str = today.strftime("%B %d, %Y")

    all_games = {}

    for sport, config in SPORT_CONFIG.items():
        print(f"Fetching {sport} games...")
        events = get_espn_games(config['espn_path'])
        odds_data = get_odds(config['odds_key'])

        games = []
        for event in events:
            comps = event.get('competitions', [{}])[0]
            competitors = comps.get('competitors', [])

            if len(competitors) < 2:
                continue

            away = [c for c in competitors if c.get('homeAway') == 'away'][0]
            home = [c for c in competitors if c.get('homeAway') == 'home'][0]

            away_team = away.get('team', {})
            home_team = home.get('team', {})

            # Get team stats
            away_id = away_team.get('id', '')
            home_id = home_team.get('id', '')
            away_stats = get_team_stats(config['espn_path'], away_id) if away_id else {}
            home_stats = get_team_stats(config['espn_path'], home_id) if home_id else {}

            # Also get stats from the event if available
            for stat in away.get('statistics', []):
                away_stats[stat.get('name', '')] = stat.get('displayValue', stat.get('value', '-'))
            for stat in home.get('statistics', []):
                home_stats[stat.get('name', '')] = stat.get('displayValue', stat.get('value', '-'))

            game_data = {
                'away_name': away_team.get('displayName', ''),
                'home_name': home_team.get('displayName', ''),
                'away_abbr': away_team.get('abbreviation', ''),
                'home_abbr': home_team.get('abbreviation', ''),
                'away_record': away.get('records', [{}])[0].get('summary', '0-0') if away.get('records') else '0-0',
                'home_record': home.get('records', [{}])[0].get('summary', '0-0') if home.get('records') else '0-0',
                'venue': comps.get('venue', {}).get('fullName', 'TBD'),
                'network': comps.get('broadcasts', [{}])[0].get('names', ['TBD'])[0] if comps.get('broadcasts') else 'TBD',
                'game_time': 'TBD',
                'away_stats': away_stats,
                'home_stats': home_stats,
            }

            game_date = event.get('date', '')
            try:
                dt = datetime.fromisoformat(game_date.replace('Z', '+00:00'))
                game_data['game_time'] = dt.strftime("%I:%M %p ET")
            except:
                pass

            odds = match_odds(odds_data, game_data['away_name'], game_data['home_name'])
            games.append((game_data, odds))

        all_games[sport] = games
        print(f"  Found {len(games)} {sport} games")

    # Generate HTML
    sport_sections = ""
    tab_buttons = ""

    for i, sport in enumerate(['NFL', 'NBA', 'NHL', 'NCAAB', 'NCAAF']):
        games = all_games.get(sport, [])
        active_class = "active" if i == 0 else ""

        tab_buttons += f'<button class="tab-btn {active_class}" data-sport="{sport.lower()}">{sport} ({len(games)})</button>\n'

        if not games:
            sport_sections += f'<div class="sport-section {active_class}" id="{sport.lower()}-section"><div class="no-games">No {sport} games today</div></div>'
            continue

        cards_html = ""
        for game_data, odds in games:
            cards_html += generate_game_card(sport, game_data, odds)

        sport_sections += f'''
        <div class="sport-section {active_class}" id="{sport.lower()}-section">
            <div class="section-header"><h2>{sport}</h2><span class="game-count">{len(games)} Games</span></div>
            <div class="games-grid">{cards_html}</div>
        </div>
        '''

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Handicapping Hub - {date_str} | BetLegend</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ background: #f5f5f5; font-family: 'Inter', sans-serif; color: #1a1a2e; }}

        .nav {{ background: #1a365d; padding: 15px 20px; position: fixed; top: 0; left: 0; right: 0; z-index: 1000; border-bottom: 3px solid #fd5000; }}
        .nav-inner {{ max-width: 1400px; margin: 0 auto; display: flex; justify-content: space-between; align-items: center; }}
        .logo {{ font-size: 1.5rem; font-weight: 800; color: white; text-decoration: none; }}
        .logo span {{ color: #fd5000; }}
        .nav-links {{ display: flex; gap: 20px; }}
        .nav-links a {{ color: white; text-decoration: none; font-weight: 600; }}

        .header {{ background: #1a365d; color: white; padding: 90px 20px 30px; text-align: center; }}
        .header h1 {{ font-size: 2rem; font-weight: 800; }}
        .header h1 span {{ color: #fd5000; }}

        .container {{ max-width: 1400px; margin: 0 auto; padding: 20px; }}

        .tabs {{ display: flex; gap: 10px; margin-bottom: 20px; background: white; padding: 15px; border-radius: 10px; flex-wrap: wrap; }}
        .tab-btn {{ padding: 12px 20px; background: #eee; border: none; border-radius: 8px; font-weight: 700; cursor: pointer; }}
        .tab-btn.active {{ background: #1a365d; color: white; }}

        .sport-section {{ display: none; }}
        .sport-section.active {{ display: block; }}
        .section-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }}
        .section-header h2 {{ color: #1a365d; }}
        .game-count {{ background: #fd5000; color: white; padding: 6px 14px; border-radius: 15px; font-weight: 700; font-size: 0.85rem; }}
        .no-games {{ background: white; padding: 40px; text-align: center; border-radius: 10px; color: #666; }}

        .games-grid {{ display: flex; flex-direction: column; gap: 15px; }}

        .game-card {{ background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}

        .game-header {{ background: #f8f9fa; padding: 10px 15px; display: flex; justify-content: space-between; border-bottom: 1px solid #eee; font-size: 0.85rem; }}
        .game-time {{ font-weight: 700; color: #1a365d; }}
        .game-info {{ color: #666; }}

        .teams-header {{ display: flex; align-items: center; justify-content: center; padding: 15px; gap: 20px; border-bottom: 1px solid #eee; }}
        .team-col {{ display: flex; align-items: center; gap: 10px; flex: 1; }}
        .team-col.away {{ justify-content: flex-end; }}
        .team-col.home {{ justify-content: flex-start; }}
        .team-logo {{ width: 50px; height: 50px; object-fit: contain; }}
        .team-name {{ font-weight: 700; font-size: 1.1rem; }}
        .vs-col {{ font-weight: 700; color: #999; font-size: 1rem; }}

        /* HORIZONTAL STATS ROW */
        .stats-row {{ display: flex; overflow-x: auto; background: #fafafa; border-bottom: 1px solid #eee; }}
        .stat-box {{ flex: 1; min-width: 80px; padding: 10px 8px; text-align: center; border-right: 1px solid #eee; }}
        .stat-box:last-child {{ border-right: none; }}
        .stat-label {{ font-size: 0.7rem; font-weight: 700; color: #666; text-transform: uppercase; margin-bottom: 5px; }}
        .stat-values {{ display: flex; flex-direction: column; gap: 3px; }}
        .stat-values span {{ font-weight: 700; font-size: 0.9rem; color: #1a1a2e; }}
        .stat-values span:first-child {{ color: #1a365d; }}
        .stat-values span:last-child {{ color: #333; }}

        .line-movement {{ background: #fff8e1; padding: 8px 15px; font-size: 0.8rem; color: #5d4e37; }}

        footer {{ text-align: center; padding: 30px; color: #666; margin-top: 30px; }}

        @media (max-width: 768px) {{
            .teams-header {{ flex-direction: column; gap: 10px; }}
            .team-col {{ justify-content: center !important; }}
            .stat-box {{ min-width: 70px; }}
        }}
    </style>
</head>
<body>
    <nav class="nav">
        <div class="nav-inner">
            <a href="index.html" class="logo">BET<span>LEGEND</span></a>
            <div class="nav-links">
                <a href="handicapping-hub.html">Hub</a>
                <a href="blog-page10.html">Picks</a>
                <a href="nfl.html">NFL</a>
                <a href="nba.html">NBA</a>
                <a href="nhl.html">NHL</a>
            </div>
        </div>
    </nav>

    <header class="header">
        <h1>Handicapping <span>Hub</span></h1>
        <p>{date_str}</p>
    </header>

    <div class="container">
        <div class="tabs">{tab_buttons}</div>
        {sport_sections}
    </div>

    <footer>
        <p>&copy; 2025 BetLegend | Data from ESPN & The Odds API</p>
    </footer>

    <script>
        document.querySelectorAll('.tab-btn').forEach(btn => {{
            btn.addEventListener('click', function() {{
                document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
                document.querySelectorAll('.sport-section').forEach(s => s.classList.remove('active'));
                this.classList.add('active');
                document.getElementById(this.dataset.sport + '-section').classList.add('active');
            }});
        }});
    </script>
</body>
</html>'''

    return html

def main():
    print("=" * 50)
    print("GENERATING HANDICAPPING HUB WITH FULL STATS")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 50)

    html = generate_page()

    output_path = os.path.join(REPO_PATH, 'handicapping-hub.html')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"\nGenerated: handicapping-hub.html")
    print("=" * 50)

if __name__ == "__main__":
    main()
