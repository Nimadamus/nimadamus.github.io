#!/usr/bin/env python3
"""
Generate Handicapping Hub v2 - Scores and Odds Style Layout
Clean horizontal table format with stats in columns
"""
import requests
from datetime import datetime
import json

# API endpoints
ODDS_API_KEY = "deeac7e7af6a8f1a5ac84c625e04973a"
ODDS_API_BASE = "https://api.the-odds-api.com/v4"

def get_odds(sport_key):
    """Get odds from the-odds-api.com"""
    try:
        url = f"{ODDS_API_BASE}/sports/{sport_key}/odds/"
        params = {
            'apiKey': ODDS_API_KEY,
            'regions': 'us',
            'markets': 'spreads,h2h,totals',
            'oddsFormat': 'american'
        }
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Error getting odds for {sport_key}: {e}")
    return []

def get_espn_scoreboard(sport):
    """Get scoreboard data from ESPN"""
    sport_map = {
        'NBA': 'basketball/nba',
        'NFL': 'football/nfl',
        'NHL': 'hockey/nhl',
        'NCAAB': 'basketball/mens-college-basketball',
        'NCAAF': 'football/college-football',
        'MLB': 'baseball/mlb'
    }

    try:
        url = f"https://site.api.espn.com/apis/site/v2/sports/{sport_map.get(sport, '')}/scoreboard"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Error getting ESPN data for {sport}: {e}")
    return None

def get_team_record_and_stats(sport, team_id):
    """Get team record and basic stats"""
    sport_map = {
        'NBA': 'basketball/nba',
        'NFL': 'football/nfl',
        'NHL': 'hockey/nhl',
        'NCAAB': 'basketball/mens-college-basketball'
    }

    if sport not in sport_map:
        return None

    try:
        url = f"https://site.api.espn.com/apis/site/v2/sports/{sport_map[sport]}/teams/{team_id}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            team = data.get('team', {})
            record = team.get('record', {})
            items = record.get('items', [])

            result = {
                'wins': 0, 'losses': 0, 'ties': 0,
                'ppg': 0, 'oppg': 0, 'pct': 0.5,
                'home_record': '', 'away_record': '', 'streak': ''
            }

            for item in items:
                item_type = item.get('type', '')
                stats = item.get('stats', [])

                if item_type == 'total':
                    for stat in stats:
                        name = stat.get('name', '')
                        value = stat.get('value', 0)
                        if name == 'wins': result['wins'] = int(value)
                        elif name == 'losses': result['losses'] = int(value)
                        elif name == 'ties' or name == 'otLosses': result['ties'] = int(value)
                        elif name == 'winPercent': result['pct'] = float(value)
                        elif name in ['pointsFor', 'avgPointsFor']: result['ppg'] = float(value)
                        elif name in ['pointsAgainst', 'avgPointsAgainst']: result['oppg'] = float(value)
                        elif name == 'streak': result['streak'] = stat.get('displayValue', '')
                elif item_type == 'home':
                    result['home_record'] = item.get('summary', '')
                elif item_type == 'road':
                    result['away_record'] = item.get('summary', '')

            return result
    except:
        pass
    return None

def get_injuries(sport, team_id):
    """Get team injuries"""
    sport_map = {
        'NBA': 'basketball/nba',
        'NFL': 'football/nfl',
        'NHL': 'hockey/nhl'
    }

    if sport not in sport_map:
        return []

    try:
        url = f"https://site.api.espn.com/apis/site/v2/sports/{sport_map[sport]}/teams/{team_id}/injuries"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            injuries = []
            for item in data.get('items', []):
                athlete = item.get('athlete', {})
                name = athlete.get('displayName', 'Unknown')
                status = item.get('status', 'Unknown')
                injuries.append({'name': name, 'status': status})
            return injuries[:3]  # Top 3 injuries
    except:
        pass
    return []

def find_odds_for_game(odds_data, away_name, home_name):
    """Find odds for a specific game"""
    result = {
        'spread_away': 'N/A', 'spread_home': 'N/A',
        'ml_away': 'N/A', 'ml_home': 'N/A',
        'total': 'N/A'
    }

    for game in odds_data:
        game_away = game.get('away_team', '').lower()
        game_home = game.get('home_team', '').lower()

        # Match by checking if team names are similar
        if (away_name.lower() in game_away or game_away in away_name.lower() or
            home_name.lower() in game_home or game_home in home_name.lower()):

            for bm in game.get('bookmakers', [])[:1]:  # First bookmaker
                for market in bm.get('markets', []):
                    if market['key'] == 'spreads':
                        for outcome in market['outcomes']:
                            if outcome['name'] == game['away_team']:
                                result['spread_away'] = f"{outcome['point']:+.1f}"
                            else:
                                result['spread_home'] = f"{outcome['point']:+.1f}"
                    elif market['key'] == 'h2h':
                        for outcome in market['outcomes']:
                            if outcome['name'] == game['away_team']:
                                result['ml_away'] = f"{outcome['price']:+d}"
                            else:
                                result['ml_home'] = f"{outcome['price']:+d}"
                    elif market['key'] == 'totals':
                        result['total'] = f"{market['outcomes'][0]['point']}"
            break

    return result

def calculate_power(record_data, sport):
    """Calculate power rating 0-100"""
    if not record_data:
        return 50

    pct = record_data.get('pct', 0.5)
    ppg = record_data.get('ppg', 0)
    oppg = record_data.get('oppg', 0)
    games = record_data.get('wins', 0) + record_data.get('losses', 0) + record_data.get('ties', 0)

    # Convert total points to per-game if needed
    if games > 0:
        if sport in ['NBA', 'NCAAB'] and ppg > 50:
            ppg = ppg / games
            oppg = oppg / games
        elif sport == 'NFL' and ppg > 50:
            ppg = ppg / games
            oppg = oppg / games
        elif sport == 'NHL' and ppg > 10:
            ppg = ppg / games
            oppg = oppg / games

    # Win % = 50% weight
    win_score = pct * 50

    # Point differential = 50% weight
    diff = ppg - oppg
    if sport in ['NBA', 'NCAAB']:
        diff_norm = max(-15, min(15, diff)) / 15
    elif sport == 'NFL':
        diff_norm = max(-10, min(10, diff)) / 10
    elif sport == 'NHL':
        diff_norm = max(-1.5, min(1.5, diff)) / 1.5
    else:
        diff_norm = 0

    diff_score = (diff_norm + 1) * 25  # 0-50

    return min(100, max(0, win_score + diff_score))

def get_power_class(rating):
    """Get CSS class for power rating"""
    if rating >= 65: return 'elite'
    elif rating >= 55: return 'good'
    elif rating >= 45: return 'avg'
    else: return 'poor'

def generate_html():
    """Generate the full HTML page"""

    now = datetime.now()
    date_str = now.strftime("%B %d, %Y")
    time_str = now.strftime("%I:%M %p ET")

    # Sport configurations
    sports_config = [
        {'name': 'NBA', 'key': 'basketball_nba', 'cols': ['PPG', 'OPP', 'HOME', 'AWAY', 'STK']},
        {'name': 'NFL', 'key': 'americanfootball_nfl', 'cols': ['PPG', 'OPP', 'HOME', 'AWAY', 'STK']},
        {'name': 'NHL', 'key': 'icehockey_nhl', 'cols': ['GF/G', 'GA/G', 'HOME', 'AWAY', 'STK']},
        {'name': 'NCAAB', 'key': 'basketball_ncaab', 'cols': ['PPG', 'OPP', 'HOME', 'AWAY', 'STK']},
    ]

    # Generate tabs HTML
    tabs_html = ""
    sections_html = ""

    for i, sport in enumerate(sports_config):
        active_class = 'active' if i == 0 else ''
        tabs_html += f'<button class="tab {active_class}" onclick="showTab(\'{sport["name"]}\')">{sport["name"]}</button>\n'

        # Get data
        espn_data = get_espn_scoreboard(sport['name'])
        odds_data = get_odds(sport['key'])

        games = espn_data.get('events', []) if espn_data else []

        # Generate games HTML
        games_html = ""

        if not games:
            games_html = '<div class="no-games">No games scheduled today</div>'
        else:
            for game in games:
                comps = game.get('competitions', [{}])[0]
                competitors = comps.get('competitors', [])

                if len(competitors) < 2:
                    continue

                # Away is index 1, Home is index 0
                away = competitors[1]
                home = competitors[0]

                away_team = away.get('team', {})
                home_team = home.get('team', {})

                away_name = away_team.get('displayName', 'Away')
                home_name = home_team.get('displayName', 'Home')
                away_abbr = away_team.get('abbreviation', 'AWY')
                home_abbr = home_team.get('abbreviation', 'HME')
                away_logo = away_team.get('logo', '')
                home_logo = home_team.get('logo', '')
                away_id = away_team.get('id', '')
                home_id = home_team.get('id', '')

                away_record_str = away.get('records', [{}])[0].get('summary', '0-0') if away.get('records') else '0-0'
                home_record_str = home.get('records', [{}])[0].get('summary', '0-0') if home.get('records') else '0-0'

                # Get detailed stats
                away_stats = get_team_record_and_stats(sport['name'], away_id)
                home_stats = get_team_record_and_stats(sport['name'], home_id)

                # Get injuries
                away_injuries = get_injuries(sport['name'], away_id)
                home_injuries = get_injuries(sport['name'], home_id)

                # Get odds
                odds = find_odds_for_game(odds_data, away_name, home_name)

                # Calculate power ratings
                away_power = calculate_power(away_stats, sport['name'])
                home_power = calculate_power(home_stats, sport['name'])

                # Format stats - calculate per-game averages
                if away_stats:
                    away_games = away_stats['wins'] + away_stats['losses'] + away_stats.get('ties', 0)
                    if away_games > 0 and away_stats['ppg'] > 50:  # If it's total points, divide
                        away_ppg = f"{away_stats['ppg'] / away_games:.1f}"
                        away_opp = f"{away_stats['oppg'] / away_games:.1f}"
                    else:
                        away_ppg = f"{away_stats['ppg']:.1f}" if away_stats['ppg'] else '-'
                        away_opp = f"{away_stats['oppg']:.1f}" if away_stats['oppg'] else '-'
                    away_home = away_stats.get('home_record', '-') or '-'
                    away_away = away_stats.get('away_record', '-') or '-'
                    away_stk = away_stats.get('streak', '-') or '-'
                else:
                    away_ppg = away_opp = away_home = away_away = away_stk = '-'

                if home_stats:
                    home_games = home_stats['wins'] + home_stats['losses'] + home_stats.get('ties', 0)
                    if home_games > 0 and home_stats['ppg'] > 50:  # If it's total points, divide
                        home_ppg = f"{home_stats['ppg'] / home_games:.1f}"
                        home_opp = f"{home_stats['oppg'] / home_games:.1f}"
                    else:
                        home_ppg = f"{home_stats['ppg']:.1f}" if home_stats['ppg'] else '-'
                        home_opp = f"{home_stats['oppg']:.1f}" if home_stats['oppg'] else '-'
                    home_home = home_stats.get('home_record', '-') or '-'
                    home_away = home_stats.get('away_record', '-') or '-'
                    home_stk = home_stats.get('streak', '-') or '-'
                else:
                    home_ppg = home_opp = home_home = home_away = home_stk = '-'

                # Game time
                game_date = game.get('date', '')
                try:
                    dt = datetime.fromisoformat(game_date.replace('Z', '+00:00'))
                    game_time = dt.strftime("%I:%M %p")
                except:
                    game_time = "TBD"

                # Format injuries
                away_inj_str = ", ".join([f"{i['name']} ({i['status']})" for i in away_injuries[:2]]) if away_injuries else "None"
                home_inj_str = ", ".join([f"{i['name']} ({i['status']})" for i in home_injuries[:2]]) if home_injuries else "None"

                games_html += f'''
                <div class="game-table">
                    <table>
                        <thead>
                            <tr>
                                <th class="team-col">TEAM</th>
                                <th>REC</th>
                                <th>PWR</th>
                                <th>{sport['cols'][0]}</th>
                                <th>{sport['cols'][1]}</th>
                                <th>HOME</th>
                                <th>AWAY</th>
                                <th>STK</th>
                                <th>SPREAD</th>
                                <th>ML</th>
                                <th>O/U</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr class="away-row">
                                <td class="team-col">
                                    <img src="{away_logo}" alt="{away_abbr}" class="team-logo" onerror="this.style.display='none'">
                                    <span class="team-name">{away_abbr}</span>
                                    <span class="team-full">{away_name}</span>
                                </td>
                                <td>{away_record_str}</td>
                                <td class="pwr {get_power_class(away_power)}">{away_power:.0f}</td>
                                <td>{away_ppg}</td>
                                <td>{away_opp}</td>
                                <td>{away_home}</td>
                                <td>{away_away}</td>
                                <td class="streak">{away_stk}</td>
                                <td class="spread">{odds['spread_away']}</td>
                                <td class="ml">{odds['ml_away']}</td>
                                <td class="total" rowspan="2">{odds['total']}</td>
                            </tr>
                            <tr class="home-row">
                                <td class="team-col">
                                    <img src="{home_logo}" alt="{home_abbr}" class="team-logo" onerror="this.style.display='none'">
                                    <span class="team-name">{home_abbr}</span>
                                    <span class="team-full">{home_name}</span>
                                </td>
                                <td>{home_record_str}</td>
                                <td class="pwr {get_power_class(home_power)}">{home_power:.0f}</td>
                                <td>{home_ppg}</td>
                                <td>{home_opp}</td>
                                <td>{home_home}</td>
                                <td>{home_away}</td>
                                <td class="streak">{home_stk}</td>
                                <td class="spread">{odds['spread_home']}</td>
                                <td class="ml">{odds['ml_home']}</td>
                            </tr>
                        </tbody>
                    </table>
                    <div class="injury-bar">
                        <span class="inj-label">INJURIES:</span>
                        <span class="inj-team">{away_abbr}:</span> {away_inj_str}
                        <span class="inj-sep">|</span>
                        <span class="inj-team">{home_abbr}:</span> {home_inj_str}
                    </div>
                </div>
                '''

        display = 'block' if i == 0 else 'none'
        sections_html += f'''
        <div id="section-{sport['name']}" class="section" style="display: {display};">
            <div class="section-header">
                <h2>{sport['name']} Games</h2>
                <span class="game-count">{len(games)} games today</span>
            </div>
            {games_html}
        </div>
        '''

    # Full HTML
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Handicapping Hub - {date_str} | BetLegend</title>
    <meta name="description" content="Professional sports betting analysis with stats, odds, injuries, and power ratings for NBA, NFL, NHL, NCAAB.">
    <link rel="canonical" href="https://www.betlegendpicks.com/handicapping-hub.html">
    <link rel="icon" href="https://www.betlegendpicks.com/newlogo.png">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            background: #0a0a0a;
            font-family: 'Inter', -apple-system, sans-serif;
            color: #e0e0e0;
            min-height: 100vh;
        }}

        /* Header */
        .header {{
            background: linear-gradient(180deg, #111 0%, #0a0a0a 100%);
            padding: 20px 30px;
            border-bottom: 1px solid #222;
            position: sticky;
            top: 0;
            z-index: 100;
        }}
        .header-inner {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        .header h1 {{
            font-size: 28px;
            font-weight: 800;
            color: #fff;
            margin-bottom: 5px;
        }}
        .header h1 span {{ color: #fd5000; }}
        .timestamp {{
            color: #666;
            font-size: 13px;
            margin-bottom: 15px;
        }}

        /* Tabs */
        .tabs {{
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }}
        .tab {{
            background: #1a1a1a;
            border: 1px solid #333;
            padding: 10px 24px;
            border-radius: 6px;
            color: #888;
            cursor: pointer;
            font-weight: 600;
            font-size: 14px;
            transition: all 0.2s;
        }}
        .tab:hover {{
            background: #252525;
            color: #fff;
            border-color: #444;
        }}
        .tab.active {{
            background: #fd5000;
            border-color: #fd5000;
            color: #fff;
        }}

        /* Container */
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 30px;
        }}

        /* Section */
        .section-header {{
            display: flex;
            align-items: center;
            gap: 15px;
            margin-bottom: 25px;
            padding-bottom: 15px;
            border-bottom: 2px solid #222;
        }}
        .section-header h2 {{
            font-size: 22px;
            font-weight: 700;
            color: #fff;
        }}
        .game-count {{
            color: #666;
            font-size: 14px;
        }}

        /* Game Table - Scores and Odds Style */
        .game-table {{
            background: #111;
            border: 1px solid #222;
            border-radius: 8px;
            margin-bottom: 20px;
            overflow: hidden;
        }}
        .game-table table {{
            width: 100%;
            border-collapse: collapse;
        }}
        .game-table th {{
            background: #1a1a1a;
            color: #888;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            padding: 12px 10px;
            text-align: center;
            border-bottom: 1px solid #222;
        }}
        .game-table th.team-col {{
            text-align: left;
            padding-left: 15px;
            width: 200px;
        }}
        .game-table td {{
            padding: 12px 10px;
            text-align: center;
            font-size: 14px;
            border-bottom: 1px solid #1a1a1a;
        }}
        .game-table td.team-col {{
            text-align: left;
            padding-left: 15px;
        }}

        /* Team column */
        .team-logo {{
            width: 28px;
            height: 28px;
            object-fit: contain;
            vertical-align: middle;
            margin-right: 10px;
        }}
        .team-name {{
            font-weight: 700;
            color: #fff;
            font-size: 15px;
        }}
        .team-full {{
            color: #666;
            font-size: 12px;
            margin-left: 8px;
        }}

        /* Row styling */
        .away-row {{
            background: #0d0d0d;
        }}
        .home-row {{
            background: #111;
        }}
        .away-row:hover, .home-row:hover {{
            background: #151515;
        }}

        /* Power ratings */
        .pwr {{
            font-weight: 700;
            font-size: 15px;
        }}
        .pwr.elite {{ color: #22c55e; }}
        .pwr.good {{ color: #3b82f6; }}
        .pwr.avg {{ color: #eab308; }}
        .pwr.poor {{ color: #ef4444; }}

        /* Betting columns */
        .spread, .ml {{
            font-weight: 600;
            color: #fff;
        }}
        .total {{
            font-weight: 700;
            color: #fd5000;
            font-size: 16px;
            vertical-align: middle;
        }}

        /* Streak */
        .streak {{
            font-size: 12px;
            color: #888;
        }}

        /* Injury bar */
        .injury-bar {{
            background: #0a0a0a;
            padding: 10px 15px;
            font-size: 12px;
            color: #666;
            border-top: 1px solid #1a1a1a;
        }}
        .inj-label {{
            color: #ef4444;
            font-weight: 600;
            margin-right: 10px;
        }}
        .inj-team {{
            color: #888;
            font-weight: 600;
            margin-left: 5px;
        }}
        .inj-sep {{
            color: #333;
            margin: 0 10px;
        }}

        /* No games */
        .no-games {{
            text-align: center;
            padding: 60px 20px;
            color: #666;
            font-size: 16px;
            background: #111;
            border-radius: 8px;
            border: 1px solid #222;
        }}

        /* Back to site link */
        .back-link {{
            text-align: center;
            padding: 30px;
        }}
        .back-link a {{
            color: #fd5000;
            text-decoration: none;
            font-size: 14px;
            padding: 10px 20px;
            border: 1px solid #333;
            border-radius: 6px;
            transition: all 0.2s;
        }}
        .back-link a:hover {{
            background: #fd5000;
            color: #fff;
            border-color: #fd5000;
        }}

        /* Mobile responsive */
        @media (max-width: 900px) {{
            .team-full {{ display: none; }}
            .game-table th, .game-table td {{ padding: 8px 5px; font-size: 12px; }}
            .game-table th.team-col, .game-table td.team-col {{ width: 120px; }}
            .team-logo {{ width: 22px; height: 22px; margin-right: 6px; }}
        }}
        @media (max-width: 600px) {{
            .container {{ padding: 15px; }}
            .tabs {{ gap: 5px; }}
            .tab {{ padding: 8px 12px; font-size: 12px; }}
        }}
    </style>
</head>
<body>
    <header class="header">
        <div class="header-inner">
            <h1>HANDICAPPING <span>HUB</span></h1>
            <div class="timestamp">Updated: {time_str} • {date_str}</div>
            <div class="tabs">
                {tabs_html}
            </div>
        </div>
    </header>

    <main class="container">
        {sections_html}
    </main>

    <div class="back-link">
        <a href="index.html">← Back to BetLegend</a>
    </div>

    <script>
        function showTab(sport) {{
            // Hide all sections
            document.querySelectorAll('.section').forEach(s => s.style.display = 'none');
            // Remove active from all tabs
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            // Show selected section
            document.getElementById('section-' + sport).style.display = 'block';
            // Activate tab
            event.target.classList.add('active');
        }}
    </script>
</body>
</html>'''

    return html

def main():
    print("Generating Handicapping Hub v2 (Scores & Odds Style)...")
    html = generate_html()

    # Works both locally and in GitHub Actions
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(os.path.dirname(script_dir))
    output_path = os.path.join(repo_root, 'handicapping-hub.html')

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"Done! Saved to {output_path}")

if __name__ == "__main__":
    main()
