#!/usr/bin/env python3
"""
Generate Handicapping Hub with:
- Light gray background (#f5f5f5) with white game cards
- Tabs for sport switching
- Full stats displayed horizontally (left to right)
- Real data from ESPN and Odds API
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
    """Get today's games from ESPN"""
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
    """Get team statistics from ESPN"""
    try:
        url = f"https://site.api.espn.com/apis/site/v2/sports/{sport_path}/teams/{team_id}/statistics"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            stats = {}
            for cat in data.get('results', {}).get('stats', {}).get('categories', []):
                for stat in cat.get('stats', []):
                    stats[stat.get('name', '')] = stat.get('value', 0)
            return stats
    except:
        pass
    return {}

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
    """Generate a game card with full stats displayed horizontally"""

    away_name = game_data['away_name']
    home_name = game_data['home_name']
    away_abbr = game_data['away_abbr']
    home_abbr = game_data['home_abbr']
    away_record = game_data['away_record']
    home_record = game_data['home_record']
    game_time = game_data['game_time']
    venue = game_data['venue']
    network = game_data['network']

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

    return f'''
        <div class="game-card">
            <div class="game-header">
                <div class="game-time">{game_time}</div>
                <div class="game-info">{venue} • {network}</div>
            </div>

            <div class="teams-container">
                <div class="team-row away">
                    <img src="{away_logo}" alt="{away_abbr}" class="team-logo" onerror="this.style.display='none'">
                    <div class="team-name">{away_name}</div>
                    <div class="team-record">{away_record}</div>
                </div>
                <div class="team-row home">
                    <img src="{home_logo}" alt="{home_abbr}" class="team-logo" onerror="this.style.display='none'">
                    <div class="team-name">{home_name}</div>
                    <div class="team-record">{home_record}</div>
                </div>
            </div>

            <div class="stats-table">
                <div class="stats-header">
                    <div class="stat-col">SPREAD</div>
                    <div class="stat-col">MONEYLINE</div>
                    <div class="stat-col">TOTAL</div>
                </div>
                <div class="stats-row away-stats">
                    <div class="stat-col"><span class="stat-value">{spread_away}</span></div>
                    <div class="stat-col"><span class="stat-value">{ml_away}</span></div>
                    <div class="stat-col"><span class="stat-value">O {total}</span></div>
                </div>
                <div class="stats-row home-stats">
                    <div class="stat-col"><span class="stat-value">{spread}</span></div>
                    <div class="stat-col"><span class="stat-value">{ml_home}</span></div>
                    <div class="stat-col"><span class="stat-value">U {total}</span></div>
                </div>
            </div>

            <div class="line-movement">
                <span class="movement-icon">📊</span>
                <span class="movement-text">Line Movement: Opening {spread} → Current {spread}</span>
            </div>
        </div>
'''

def generate_page():
    """Generate the full handicapping hub page"""

    today = datetime.now()
    date_str = today.strftime("%B %d, %Y")

    # Collect all games by sport
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

            game_data = {
                'away_name': away_team.get('displayName', ''),
                'home_name': home_team.get('displayName', ''),
                'away_abbr': away_team.get('abbreviation', ''),
                'home_abbr': home_team.get('abbreviation', ''),
                'away_record': away.get('records', [{}])[0].get('summary', '0-0') if away.get('records') else '0-0',
                'home_record': home.get('records', [{}])[0].get('summary', '0-0') if home.get('records') else '0-0',
                'venue': comps.get('venue', {}).get('fullName', 'TBD'),
                'network': comps.get('broadcasts', [{}])[0].get('names', ['TBD'])[0] if comps.get('broadcasts') else 'TBD',
                'game_time': 'TBD'
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

    # Generate HTML for each sport section
    sport_sections = ""
    tab_buttons = ""

    for i, sport in enumerate(['NFL', 'NBA', 'NHL', 'NCAAB', 'NCAAF']):
        games = all_games.get(sport, [])
        active_class = "active" if i == 0 else ""

        # Tab button
        tab_buttons += f'<button class="tab-btn {active_class}" data-sport="{sport.lower()}">{sport} <span class="count">({len(games)})</span></button>\n'

        if not games:
            sport_sections += f'''
            <div class="sport-section {active_class}" id="{sport.lower()}-section">
                <div class="no-games">No {sport} games scheduled for today</div>
            </div>
            '''
            continue

        # Generate game cards
        cards_html = ""
        for game_data, odds in games:
            cards_html += generate_game_card(sport, game_data, odds)

        sport_sections += f'''
        <div class="sport-section {active_class}" id="{sport.lower()}-section">
            <div class="section-header">
                <h2>{sport} Games</h2>
                <span class="game-count">{len(games)} Games Today</span>
            </div>
            <div class="games-grid">
                {cards_html}
            </div>
        </div>
        '''

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Handicapping Hub - {date_str} | BetLegend</title>
    <meta name="description" content="Advanced sports handicapping with real-time odds, spreads, and betting lines for NFL, NBA, NHL, NCAAB, and NCAAF.">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        body {{
            background: #f5f5f5;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            color: #1a1a2e;
            line-height: 1.5;
        }}

        /* Navigation */
        .nav {{
            background: #1a365d;
            padding: 15px 20px;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            z-index: 1000;
            border-bottom: 3px solid #fd5000;
        }}
        .nav-inner {{
            max-width: 1400px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .logo {{
            font-size: 1.5rem;
            font-weight: 800;
            color: white;
            text-decoration: none;
        }}
        .logo span {{ color: #fd5000; }}
        .nav-links {{
            display: flex;
            gap: 20px;
        }}
        .nav-links a {{
            color: white;
            text-decoration: none;
            font-weight: 600;
            font-size: 0.9rem;
        }}
        .nav-links a:hover {{ color: #fd5000; }}

        /* Header */
        .header {{
            background: linear-gradient(135deg, #1a365d 0%, #2d4a7c 100%);
            color: white;
            padding: 100px 20px 40px;
            text-align: center;
        }}
        .header h1 {{
            font-size: 2.5rem;
            font-weight: 800;
            margin-bottom: 10px;
        }}
        .header h1 span {{ color: #fd5000; }}
        .header .date {{
            font-size: 1.1rem;
            opacity: 0.9;
        }}

        /* Main Container */
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 30px 20px;
        }}

        /* Sport Tabs */
        .tabs {{
            display: flex;
            gap: 10px;
            margin-bottom: 30px;
            flex-wrap: wrap;
            background: white;
            padding: 15px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }}
        .tab-btn {{
            padding: 12px 24px;
            background: #f0f0f0;
            border: none;
            border-radius: 8px;
            font-weight: 700;
            font-size: 0.95rem;
            cursor: pointer;
            transition: all 0.2s;
            color: #333;
        }}
        .tab-btn:hover {{
            background: #e0e0e0;
        }}
        .tab-btn.active {{
            background: #1a365d;
            color: white;
        }}
        .tab-btn .count {{
            opacity: 0.7;
            font-weight: 500;
        }}

        /* Sport Section */
        .sport-section {{
            display: none;
        }}
        .sport-section.active {{
            display: block;
        }}
        .section-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }}
        .section-header h2 {{
            font-size: 1.5rem;
            color: #1a365d;
        }}
        .game-count {{
            background: #fd5000;
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: 700;
            font-size: 0.85rem;
        }}
        .no-games {{
            background: white;
            padding: 40px;
            text-align: center;
            border-radius: 12px;
            color: #666;
            font-size: 1.1rem;
        }}

        /* Games Grid */
        .games-grid {{
            display: grid;
            gap: 20px;
        }}

        /* Game Card - Full Width */
        .game-card {{
            background: white;
            border-radius: 12px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.08);
            overflow: hidden;
            width: 100%;
        }}

        .game-header {{
            background: #f8f9fa;
            padding: 12px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #eee;
        }}
        .game-time {{
            font-weight: 700;
            color: #1a365d;
            font-size: 0.95rem;
        }}
        .game-info {{
            color: #666;
            font-size: 0.85rem;
        }}

        /* Teams Container */
        .teams-container {{
            padding: 15px 20px;
        }}
        .team-row {{
            display: flex;
            align-items: center;
            gap: 15px;
            padding: 10px 0;
        }}
        .team-row.away {{
            border-bottom: 1px solid #eee;
        }}
        .team-logo {{
            width: 40px;
            height: 40px;
            object-fit: contain;
        }}
        .team-name {{
            font-weight: 700;
            font-size: 1rem;
            flex: 1;
        }}
        .team-record {{
            color: #666;
            font-size: 0.9rem;
            font-weight: 500;
        }}

        /* Stats Table - Horizontal Layout */
        .stats-table {{
            background: #f8f9fa;
            border-top: 1px solid #eee;
        }}
        .stats-header {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            background: #1a365d;
            color: white;
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .stats-header .stat-col {{
            padding: 10px;
            text-align: center;
        }}
        .stats-row {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            border-bottom: 1px solid #eee;
        }}
        .stats-row:last-child {{
            border-bottom: none;
        }}
        .stats-row .stat-col {{
            padding: 12px 10px;
            text-align: center;
        }}
        .stat-value {{
            font-weight: 700;
            font-size: 1rem;
            color: #1a1a2e;
        }}
        .away-stats {{
            background: #fff;
        }}
        .home-stats {{
            background: #fafafa;
        }}

        /* Line Movement */
        .line-movement {{
            background: linear-gradient(135deg, #fff8e1 0%, #ffecb3 100%);
            padding: 10px 20px;
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 0.85rem;
            color: #5d4e37;
            border-top: 1px solid #ffe082;
        }}
        .movement-icon {{
            font-size: 1rem;
        }}
        .movement-text {{
            font-weight: 500;
        }}

        /* Footer */
        footer {{
            text-align: center;
            padding: 40px 20px;
            color: #666;
            font-size: 0.9rem;
            margin-top: 40px;
            border-top: 1px solid #ddd;
        }}
        footer a {{
            color: #1a365d;
            text-decoration: none;
        }}

        /* Responsive */
        @media (max-width: 768px) {{
            .header h1 {{ font-size: 1.8rem; }}
            .tabs {{ gap: 8px; }}
            .tab-btn {{ padding: 10px 16px; font-size: 0.85rem; }}
            .game-header {{ flex-direction: column; gap: 5px; text-align: center; }}
            .team-name {{ font-size: 0.9rem; }}
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
                <a href="records.html">Records</a>
            </div>
        </div>
    </nav>

    <header class="header">
        <h1>Handicapping <span>Hub</span></h1>
        <p class="date">{date_str} • Real-Time Odds & Stats</p>
    </header>

    <div class="container">
        <div class="tabs">
            {tab_buttons}
        </div>

        {sport_sections}
    </div>

    <footer>
        <p>&copy; 2025 BetLegend. All rights reserved. | <a href="index.html">Home</a></p>
        <p style="margin-top:10px">Data sourced from ESPN and The Odds API. Lines subject to change.</p>
    </footer>

    <script>
        // Tab switching
        document.querySelectorAll('.tab-btn').forEach(btn => {{
            btn.addEventListener('click', function() {{
                document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
                document.querySelectorAll('.sport-section').forEach(s => s.classList.remove('active'));

                this.classList.add('active');
                const sport = this.dataset.sport;
                const section = document.getElementById(sport + '-section');
                if (section) section.classList.add('active');
            }});
        }});
    </script>
</body>
</html>'''

    return html

def main():
    print("=" * 50)
    print("GENERATING HANDICAPPING HUB")
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
