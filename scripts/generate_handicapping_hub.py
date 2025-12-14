#!/usr/bin/env python3
"""
Generate Handicapping Hub with LOCKED design:
- Light gray background (#f5f5f5) with white game cards
- Full-width horizontal game cards
- Line movement alerts UNDER each game
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

def generate_game_card(sport, away_name, home_name, away_abbr, home_abbr, away_record, home_record, game_time, venue, network, odds):
    """Generate a single game card HTML with line movement under game"""

    # Logo URL
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
    total = odds.get('total', '-')
    ml_away = odds.get('ml_away', '-')
    ml_home = odds.get('ml_home', '-')

    # Determine favorite
    try:
        spread_val = float(spread.replace('+', ''))
        if spread_val < 0:
            spread_display = f"{home_abbr} {spread}"
        else:
            spread_display = f"{away_abbr} {odds.get('spread_away', spread)}"
    except:
        spread_display = spread

    return f'''
    <div class="game-card">
        <div class="game-header">
            <span class="game-time">{game_time}</span>
            <span class="game-venue">{venue}</span>
            <span class="game-network">{network}</span>
        </div>

        <div class="matchup-row">
            <div class="team away-team">
                <img src="{away_logo}" alt="{away_name}" class="team-logo" onerror="this.style.display='none'">
                <div class="team-info">
                    <span class="team-name">{away_name}</span>
                    <span class="team-record">{away_record}</span>
                </div>
                <div class="team-odds">
                    <span class="spread">{odds.get('spread_away', '-')}</span>
                    <span class="moneyline">{ml_away}</span>
                </div>
            </div>

            <div class="vs-divider">@</div>

            <div class="team home-team">
                <img src="{home_logo}" alt="{home_name}" class="team-logo" onerror="this.style.display='none'">
                <div class="team-info">
                    <span class="team-name">{home_name}</span>
                    <span class="team-record">{home_record}</span>
                </div>
                <div class="team-odds">
                    <span class="spread">{spread}</span>
                    <span class="moneyline">{ml_home}</span>
                </div>
            </div>
        </div>

        <div class="game-total">
            <span class="total-label">Total:</span>
            <span class="total-value">O/U {total}</span>
        </div>

        <div class="line-movement-bar">
            <span class="movement-label">Line Movement:</span>
            <span class="movement-info">Opening: {spread_display} | Current: {spread_display}</span>
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

            away_name = away_team.get('displayName', '')
            home_name = home_team.get('displayName', '')
            away_abbr = away_team.get('abbreviation', '')
            home_abbr = home_team.get('abbreviation', '')

            away_record = away.get('records', [{}])[0].get('summary', '0-0') if away.get('records') else '0-0'
            home_record = home.get('records', [{}])[0].get('summary', '0-0') if home.get('records') else '0-0'

            venue = comps.get('venue', {}).get('fullName', 'TBD')
            broadcasts = comps.get('broadcasts', [{}])
            network = broadcasts[0].get('names', ['TBD'])[0] if broadcasts else 'TBD'

            game_date = event.get('date', '')
            try:
                dt = datetime.fromisoformat(game_date.replace('Z', '+00:00'))
                game_time = dt.strftime("%I:%M %p ET")
            except:
                game_time = "TBD"

            odds = match_odds(odds_data, away_name, home_name)

            games.append({
                'away_name': away_name, 'home_name': home_name,
                'away_abbr': away_abbr, 'home_abbr': home_abbr,
                'away_record': away_record, 'home_record': home_record,
                'game_time': game_time, 'venue': venue, 'network': network,
                'odds': odds
            })

        all_games[sport] = games
        print(f"  Found {len(games)} {sport} games")

    # Generate game cards HTML for each sport
    game_sections = ""

    for sport in ['NFL', 'NBA', 'NHL', 'NCAAB', 'NCAAF']:
        games = all_games.get(sport, [])
        if not games:
            continue

        cards_html = ""
        for g in games:
            cards_html += generate_game_card(
                sport, g['away_name'], g['home_name'], g['away_abbr'], g['home_abbr'],
                g['away_record'], g['home_record'], g['game_time'], g['venue'], g['network'], g['odds']
            )

        game_sections += f'''
        <div class="sport-section" id="{sport.lower()}-section">
            <div class="sport-header">
                <h2>{sport}</h2>
                <span class="game-count">{len(games)} Games</span>
            </div>
            <div class="games-container">
                {cards_html}
            </div>
        </div>
        '''

    # Build tab buttons
    tab_buttons = ""
    for sport in ['NFL', 'NBA', 'NHL', 'NCAAB', 'NCAAF']:
        count = len(all_games.get(sport, []))
        active = "active" if sport == 'NFL' else ""
        tab_buttons += f'<button class="tab-btn {active}" data-sport="{sport.lower()}">{sport} ({count})</button>'

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Handicapping Hub - {date_str} | BetLegend</title>
    <meta name="description" content="Advanced sports handicapping research center. Real-time odds, stats, and analysis for NFL, NBA, NHL, and college sports.">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        body {{
            background: #f5f5f5;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            color: #1a1a2e;
            line-height: 1.6;
        }}

        /* Header */
        .header {{
            background: #1a365d;
            color: white;
            padding: 100px 20px 30px;
            text-align: center;
        }}
        .header h1 {{
            font-size: 2.5rem;
            font-weight: 800;
            margin-bottom: 8px;
        }}
        .header h1 span {{
            color: #fd5000;
        }}
        .header p {{
            color: rgba(255,255,255,0.8);
            font-size: 1.1rem;
        }}

        /* Navigation */
        .nav-container {{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            z-index: 1000;
            background: #1a365d;
            border-bottom: 3px solid #fd5000;
            padding: 0 20px;
        }}
        .nav-inner {{
            max-width: 1400px;
            margin: 0 auto;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 12px 0;
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

        /* Main Container */
        .main-container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 30px 20px;
        }}

        /* Sport Tabs */
        .sport-tabs {{
            display: flex;
            gap: 10px;
            margin-bottom: 30px;
            flex-wrap: wrap;
        }}
        .tab-btn {{
            padding: 12px 24px;
            background: white;
            border: 2px solid #e5e5e5;
            border-radius: 8px;
            font-weight: 600;
            font-size: 0.95rem;
            cursor: pointer;
            transition: all 0.2s;
        }}
        .tab-btn:hover {{
            border-color: #1a365d;
        }}
        .tab-btn.active {{
            background: #1a365d;
            color: white;
            border-color: #1a365d;
        }}

        /* Sport Section */
        .sport-section {{
            display: none;
        }}
        .sport-section.active {{
            display: block;
        }}
        .sport-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 2px solid #1a365d;
        }}
        .sport-header h2 {{
            font-size: 1.8rem;
            color: #1a365d;
        }}
        .game-count {{
            background: #fd5000;
            color: white;
            padding: 6px 16px;
            border-radius: 20px;
            font-weight: 700;
            font-size: 0.9rem;
        }}

        /* Game Card - Full Width Horizontal */
        .game-card {{
            background: white;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            margin-bottom: 20px;
            overflow: hidden;
            width: 100%;
        }}

        .game-header {{
            background: #f8f9fa;
            padding: 12px 20px;
            display: flex;
            gap: 20px;
            font-size: 0.85rem;
            color: #666;
            border-bottom: 1px solid #eee;
        }}
        .game-time {{
            font-weight: 700;
            color: #1a365d;
        }}

        /* Matchup Row - Horizontal Layout */
        .matchup-row {{
            display: flex;
            align-items: center;
            padding: 20px;
            gap: 20px;
        }}

        .team {{
            flex: 1;
            display: flex;
            align-items: center;
            gap: 15px;
        }}
        .team.home-team {{
            flex-direction: row-reverse;
            text-align: right;
        }}
        .team.home-team .team-info {{
            align-items: flex-end;
        }}
        .team.home-team .team-odds {{
            align-items: flex-end;
        }}

        .team-logo {{
            width: 60px;
            height: 60px;
            object-fit: contain;
        }}

        .team-info {{
            display: flex;
            flex-direction: column;
        }}
        .team-name {{
            font-size: 1.1rem;
            font-weight: 700;
            color: #1a1a2e;
        }}
        .team-record {{
            font-size: 0.85rem;
            color: #666;
        }}

        .team-odds {{
            display: flex;
            flex-direction: column;
            gap: 4px;
            margin-left: auto;
        }}
        .team.home-team .team-odds {{
            margin-left: 0;
            margin-right: auto;
        }}
        .spread {{
            background: #1a365d;
            color: white;
            padding: 4px 12px;
            border-radius: 4px;
            font-weight: 700;
            font-size: 0.9rem;
        }}
        .moneyline {{
            background: #f5f5f5;
            color: #1a1a2e;
            padding: 4px 12px;
            border-radius: 4px;
            font-weight: 600;
            font-size: 0.85rem;
        }}

        .vs-divider {{
            font-size: 1.2rem;
            font-weight: 700;
            color: #999;
            padding: 0 20px;
        }}

        .game-total {{
            background: #f8f9fa;
            padding: 10px 20px;
            text-align: center;
            border-top: 1px solid #eee;
        }}
        .total-label {{
            color: #666;
            margin-right: 10px;
        }}
        .total-value {{
            font-weight: 700;
            color: #1a365d;
        }}

        /* Line Movement Bar - UNDER each game */
        .line-movement-bar {{
            background: linear-gradient(135deg, #fff3cd 0%, #ffeeba 100%);
            padding: 10px 20px;
            display: flex;
            align-items: center;
            gap: 15px;
            font-size: 0.85rem;
            border-top: 1px solid #ffc107;
        }}
        .movement-label {{
            font-weight: 700;
            color: #856404;
        }}
        .movement-info {{
            color: #856404;
        }}

        /* Footer */
        footer {{
            text-align: center;
            padding: 40px 20px;
            color: #666;
            font-size: 0.9rem;
            border-top: 1px solid #ddd;
            margin-top: 40px;
        }}
        footer a {{
            color: #1a365d;
            text-decoration: none;
        }}

        /* Responsive */
        @media (max-width: 768px) {{
            .matchup-row {{
                flex-direction: column;
                gap: 15px;
            }}
            .team, .team.home-team {{
                flex-direction: row;
                text-align: left;
                width: 100%;
            }}
            .team.home-team .team-info {{
                align-items: flex-start;
            }}
            .team-odds {{
                margin-left: auto !important;
                margin-right: 0 !important;
            }}
            .vs-divider {{
                display: none;
            }}
        }}
    </style>
</head>
<body>
    <nav class="nav-container">
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
        <p>{date_str} - Real-Time Odds & Analysis</p>
    </header>

    <div class="main-container">
        <div class="sport-tabs">
            {tab_buttons}
        </div>

        {game_sections}
    </div>

    <footer>
        <p>&copy; 2025 BetLegend. All rights reserved. | <a href="index.html">Home</a></p>
        <p style="margin-top:10px">Data sourced from ESPN and The Odds API. Lines subject to change.</p>
    </footer>

    <script>
        // Tab switching
        document.querySelectorAll('.tab-btn').forEach(btn => {{
            btn.addEventListener('click', function() {{
                // Remove active from all tabs and sections
                document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
                document.querySelectorAll('.sport-section').forEach(s => s.classList.remove('active'));

                // Add active to clicked tab and corresponding section
                this.classList.add('active');
                const sport = this.dataset.sport;
                const section = document.getElementById(sport + '-section');
                if (section) section.classList.add('active');
            }});
        }});

        // Show first sport section by default
        const firstSection = document.querySelector('.sport-section');
        if (firstSection) firstSection.classList.add('active');
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
