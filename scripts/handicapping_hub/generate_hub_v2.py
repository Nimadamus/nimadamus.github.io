#!/usr/bin/env python3
"""
Generate Handicapping Hub v2 - Scores and Odds Style Layout
WITH FULL ADVANCED STATS
"""
import requests
from datetime import datetime
import os

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

def get_team_stats(sport, team_id):
    """Get FULL team statistics from ESPN"""
    sport_map = {
        'NBA': 'basketball/nba',
        'NFL': 'football/nfl',
        'NHL': 'hockey/nhl',
        'NCAAB': 'basketball/mens-college-basketball'
    }
    if sport not in sport_map:
        return None

    stats = {
        'record': {},
        'offense': {},
        'defense': {},
        'advanced': {}
    }

    # Get team info and record
    try:
        url = f"https://site.api.espn.com/apis/site/v2/sports/{sport_map[sport]}/teams/{team_id}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            team = data.get('team', {})
            record = team.get('record', {})
            for item in record.get('items', []):
                item_type = item.get('type', '')
                if item_type == 'total':
                    for stat in item.get('stats', []):
                        name = stat.get('name', '')
                        value = stat.get('value', 0)
                        if name == 'wins': stats['record']['wins'] = int(value)
                        elif name == 'losses': stats['record']['losses'] = int(value)
                        elif name in ['ties', 'otLosses']: stats['record']['ties'] = int(value)
                        elif name == 'winPercent': stats['record']['pct'] = float(value)
                        elif name in ['pointsFor', 'avgPointsFor']: stats['record']['ppg'] = float(value)
                        elif name in ['pointsAgainst', 'avgPointsAgainst']: stats['record']['oppg'] = float(value)
                        elif name == 'streak': stats['record']['streak'] = stat.get('displayValue', '')
                elif item_type == 'home':
                    stats['record']['home'] = item.get('summary', '')
                elif item_type == 'road':
                    stats['record']['away'] = item.get('summary', '')
    except:
        pass

    # Get detailed statistics
    try:
        url = f"https://site.api.espn.com/apis/site/v2/sports/{sport_map[sport]}/teams/{team_id}/statistics"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            categories = data.get('results', {}).get('stats', {}).get('categories', [])

            for cat in categories:
                for stat in cat.get('stats', []):
                    name = stat.get('name', '')
                    value = stat.get('value', 0)
                    display = stat.get('displayValue', str(value))

                    # NBA stats - EXPANDED
                    if sport in ['NBA', 'NCAAB']:
                        if name == 'avgPoints': stats['offense']['PPG'] = f"{value:.1f}"
                        elif name == 'fieldGoalPct': stats['offense']['FG%'] = f"{value:.1f}%"
                        elif name == 'threePointFieldGoalPct': stats['offense']['3P%'] = f"{value:.1f}%"
                        elif name == 'freeThrowPct': stats['offense']['FT%'] = f"{value:.1f}%"
                        elif name == 'avgRebounds': stats['offense']['RPG'] = f"{value:.1f}"
                        elif name == 'avgAssists': stats['offense']['APG'] = f"{value:.1f}"
                        elif name == 'avgTurnovers': stats['defense']['TO/G'] = f"{value:.1f}"
                        elif name == 'avgSteals': stats['defense']['STL'] = f"{value:.1f}"
                        elif name == 'avgBlocks': stats['defense']['BLK'] = f"{value:.1f}"
                        elif name == 'avgPointsOpponent': stats['defense']['OPP'] = f"{value:.1f}"
                        elif name == 'avgDefensiveRebounds': stats['defense']['DREB'] = f"{value:.1f}"
                        elif name == 'avgOffensiveRebounds': stats['offense']['OREB'] = f"{value:.1f}"

                    # NFL stats - EXPANDED
                    elif sport == 'NFL':
                        if name == 'totalPointsPerGame': stats['offense']['PPG'] = f"{value:.1f}"
                        elif name == 'netPassingYardsPerGame': stats['offense']['PASS'] = f"{value:.0f}"
                        elif name == 'rushingYardsPerGame': stats['offense']['RUSH'] = f"{value:.0f}"
                        elif name == 'totalYardsPerGame': stats['offense']['YPG'] = f"{value:.0f}"
                        elif name == 'thirdDownConversionPct': stats['offense']['3RD%'] = f"{value:.1f}%"
                        elif name == 'sacks': stats['defense']['SACK'] = f"{int(value)}"
                        elif name == 'interceptions': stats['defense']['INT'] = f"{int(value)}"
                        elif name == 'fumblesRecovered': stats['defense']['FUM'] = f"{int(value)}"
                        elif name == 'avgPointsAllowed': stats['defense']['OPP'] = f"{value:.1f}"
                        elif name == 'totalYardsAllowedPerGame': stats['defense']['DYDS'] = f"{value:.0f}"
                        elif name == 'yardsAllowedPerGame': stats['defense']['DYDS'] = f"{value:.0f}"

                    # NHL stats - EXPANDED
                    elif sport == 'NHL':
                        if name == 'avgGoals': stats['offense']['GF'] = f"{value:.2f}"
                        elif name == 'avgShots': stats['offense']['SOG'] = f"{value:.1f}"
                        elif name == 'powerPlayPct': stats['offense']['PP%'] = f"{value:.1f}%"
                        elif name == 'faceoffWinPct': stats['offense']['FO%'] = f"{value:.1f}%"
                        elif name == 'avgHits': stats['offense']['HITS'] = f"{value:.1f}"
                        elif name == 'hits': stats['offense']['HITS'] = f"{value:.0f}"
                        elif name == 'avgGoalsAgainst': stats['defense']['GA'] = f"{value:.2f}"
                        elif name == 'penaltyKillPct': stats['defense']['PK%'] = f"{value:.1f}%"
                        elif name == 'savePct': stats['defense']['SV%'] = f"{value*100:.1f}%"
                        elif name == 'avgBlockedShots': stats['defense']['BLK'] = f"{value:.1f}"
                        elif name == 'blockedShots': stats['defense']['BLK'] = f"{value:.0f}"
    except:
        pass

    # Copy oppg from record to defense if not already set
    if stats['record'].get('oppg') and not stats['defense'].get('OPP'):
        games = stats['record'].get('wins', 0) + stats['record'].get('losses', 0) + stats['record'].get('ties', 0)
        oppg = stats['record']['oppg']
        # Convert to per-game if it looks like a total
        if sport in ['NBA', 'NCAAB'] and oppg > 50 and games > 0:
            oppg = oppg / games
        elif sport == 'NFL' and oppg > 50 and games > 0:
            oppg = oppg / games
        elif sport == 'NHL' and oppg > 10 and games > 0:
            oppg = oppg / games
        stats['defense']['OPP'] = f"{oppg:.1f}"

    return stats

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
            return injuries[:3]
    except:
        pass
    return []

def get_game_trends(sport, game_id):
    """Get betting trends, season series, and pickcenter from ESPN game summary"""
    sport_map = {
        'NBA': 'basketball/nba',
        'NFL': 'football/nfl',
        'NHL': 'hockey/nhl',
        'NCAAB': 'basketball/mens-college-basketball',
        'NCAAF': 'football/college-football'
    }
    trends = {
        'h2h': '',           # Head-to-head record
        'open_spread': '',   # Opening spread
        'close_spread': '',  # Closing spread
        'open_total': '',    # Opening total
        'close_total': '',   # Closing total
        'spread_home': '',   # Current home spread
        'spread_away': '',   # Current away spread
        'ml_home': '',       # Current home ML
        'ml_away': '',       # Current away ML
        'total': '',         # Current total
        'ats_away': '',      # Away team ATS record
        'ats_home': ''       # Home team ATS record
    }
    if sport not in sport_map:
        return trends
    try:
        url = f"https://site.api.espn.com/apis/site/v2/sports/{sport_map[sport]}/summary?event={game_id}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()

            # Get season series (head-to-head)
            series = data.get('seasonseries', [])
            if series:
                ser = series[0]
                trends['h2h'] = ser.get('seriesScore', '')

            # Get pickcenter (betting lines) - USE THIS FOR MAIN ODDS
            pickcenter = data.get('pickcenter', [])
            if pickcenter:
                pc = pickcenter[0]

                # Get current spread and total
                spread = pc.get('spread', 0)
                if spread:
                    trends['spread_home'] = f"{spread:+.1f}" if spread < 0 else f"{spread:+.1f}"
                    trends['spread_away'] = f"{-spread:+.1f}"

                over_under = pc.get('overUnder', 0)
                if over_under:
                    trends['total'] = f"{over_under}"

                # Get moneylines
                home_odds = pc.get('homeTeamOdds', {})
                away_odds = pc.get('awayTeamOdds', {})
                if home_odds.get('moneyLine'):
                    ml = home_odds['moneyLine']
                    trends['ml_home'] = f"{ml:+d}" if isinstance(ml, int) else str(ml)
                if away_odds.get('moneyLine'):
                    ml = away_odds['moneyLine']
                    trends['ml_away'] = f"{ml:+d}" if isinstance(ml, int) else str(ml)

                # Opening and closing lines for trends
                ps = pc.get('pointSpread', {})
                if ps:
                    home_open = ps.get('home', {}).get('open', {}).get('line', '')
                    home_close = ps.get('home', {}).get('close', {}).get('line', '')
                    trends['open_spread'] = f"Open: {home_open}" if home_open else ''
                    trends['close_spread'] = f"Close: {home_close}" if home_close else ''

                total = pc.get('total', {})
                if total:
                    over_open = total.get('over', {}).get('open', {}).get('line', '')
                    over_close = total.get('over', {}).get('close', {}).get('line', '')
                    trends['open_total'] = over_open.replace('o', 'O ') if over_open else ''
                    trends['close_total'] = over_close.replace('o', 'O ') if over_close else ''

            # Get ATS records
            ats = data.get('againstTheSpread', [])
            for team_ats in ats:
                records = team_ats.get('records', [])
                ats_rec = ''
                for rec in records:
                    if rec.get('type') == 'ats':
                        ats_rec = rec.get('summary', '')
                        break
                if ats_rec:
                    abbr = team_ats.get('team', {}).get('abbreviation', '')
                    if abbr:
                        trends[f'ats_{abbr}'] = ats_rec
    except:
        pass
    return trends

def find_odds_for_game(odds_data, away_name, home_name):
    """Find odds for a specific game"""
    result = {
        'spread_away': '-', 'spread_home': '-',
        'ml_away': '-', 'ml_home': '-',
        'total': '-'
    }
    for game in odds_data:
        game_away = game.get('away_team', '').lower()
        game_home = game.get('home_team', '').lower()
        if (away_name.lower() in game_away or game_away in away_name.lower() or
            home_name.lower() in game_home or game_home in home_name.lower()):
            for bm in game.get('bookmakers', [])[:1]:
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

def calculate_power(stats, sport):
    """Calculate power rating 0-100"""
    if not stats or not stats.get('record'):
        return 50

    rec = stats['record']
    pct = rec.get('pct', 0.5)
    ppg = rec.get('ppg', 0)
    oppg = rec.get('oppg', 0)
    games = rec.get('wins', 0) + rec.get('losses', 0) + rec.get('ties', 0)

    # Convert total to per-game if needed
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

    win_score = pct * 50
    diff = ppg - oppg
    if sport in ['NBA', 'NCAAB']:
        diff_norm = max(-15, min(15, diff)) / 15
    elif sport == 'NFL':
        diff_norm = max(-10, min(10, diff)) / 10
    elif sport == 'NHL':
        diff_norm = max(-1.5, min(1.5, diff)) / 1.5
    else:
        diff_norm = 0
    diff_score = (diff_norm + 1) * 25
    return min(100, max(0, win_score + diff_score))

def get_power_class(rating):
    if rating >= 65: return 'elite'
    elif rating >= 55: return 'good'
    elif rating >= 45: return 'avg'
    else: return 'poor'

def generate_html():
    """Generate the full HTML page with ADVANCED STATS"""
    now = datetime.now()
    date_str = now.strftime("%B %d, %Y")
    time_str = now.strftime("%I:%M %p ET")

    # Sport configurations with their stat columns - EXPANDED STATS
    sports_config = [
        {
            'name': 'NBA',
            'key': 'basketball_nba',
            'off_cols': ['PPG', 'FG%', '3P%', 'FT%', 'RPG', 'APG'],
            'def_cols': ['OPP', 'STL', 'BLK', 'TO/G', 'DREB']
        },
        {
            'name': 'NFL',
            'key': 'americanfootball_nfl',
            'off_cols': ['PPG', 'YPG', 'PASS', 'RUSH', '3RD%'],
            'def_cols': ['OPP', 'SACK', 'INT', 'FUM', 'DYDS']
        },
        {
            'name': 'NHL',
            'key': 'icehockey_nhl',
            'off_cols': ['GF', 'SOG', 'PP%', 'FO%', 'HITS'],
            'def_cols': ['GA', 'PK%', 'SV%', 'BLK']
        },
        {
            'name': 'NCAAB',
            'key': 'basketball_ncaab',
            'off_cols': ['PPG', 'FG%', '3P%', 'FT%', 'RPG', 'APG'],
            'def_cols': ['OPP', 'STL', 'BLK', 'TO/G', 'DREB']
        },
    ]

    tabs_html = ""
    sections_html = ""

    for i, sport in enumerate(sports_config):
        active_class = 'active' if i == 0 else ''
        tabs_html += f'<button class="tab {active_class}" onclick="showTab(\'{sport["name"]}\')">{sport["name"]}</button>\n'

        espn_data = get_espn_scoreboard(sport['name'])
        odds_data = get_odds(sport['key'])
        games = espn_data.get('events', []) if espn_data else []
        games_html = ""

        if not games:
            games_html = '<div class="no-games">No games scheduled today</div>'
        else:
            for game in games:
                comps = game.get('competitions', [{}])[0]
                competitors = comps.get('competitors', [])
                if len(competitors) < 2:
                    continue

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
                away_record = away.get('records', [{}])[0].get('summary', '0-0') if away.get('records') else '0-0'
                home_record = home.get('records', [{}])[0].get('summary', '0-0') if home.get('records') else '0-0'

                # Get full stats
                away_stats = get_team_stats(sport['name'], away_id)
                home_stats = get_team_stats(sport['name'], home_id)

                # Get injuries
                away_injuries = get_injuries(sport['name'], away_id)
                home_injuries = get_injuries(sport['name'], home_id)

                # Get odds
                odds = find_odds_for_game(odds_data, away_name, home_name)

                # Get game ID for trends
                game_id = game.get('id', '')
                trends = get_game_trends(sport['name'], game_id) if game_id else {}

                # Calculate power
                away_power = calculate_power(away_stats, sport['name'])
                home_power = calculate_power(home_stats, sport['name'])

                # Game time
                game_date = game.get('date', '')
                try:
                    dt = datetime.fromisoformat(game_date.replace('Z', '+00:00'))
                    game_time = dt.strftime("%I:%M %p")
                except:
                    game_time = "TBD"

                # Format injuries
                away_inj = ", ".join([f"{i['name']} ({i['status']})" for i in away_injuries[:2]]) if away_injuries else "None reported"
                home_inj = ", ".join([f"{i['name']} ({i['status']})" for i in home_injuries[:2]]) if home_injuries else "None reported"

                # Build offense stats cells
                def get_stat(stats_dict, key, section='offense'):
                    if not stats_dict:
                        return '-'
                    return stats_dict.get(section, {}).get(key, '-')

                away_off_cells = ''.join([f'<td>{get_stat(away_stats, col, "offense")}</td>' for col in sport['off_cols']])
                home_off_cells = ''.join([f'<td>{get_stat(home_stats, col, "offense")}</td>' for col in sport['off_cols']])
                away_def_cells = ''.join([f'<td>{get_stat(away_stats, col, "defense")}</td>' for col in sport['def_cols']])
                home_def_cells = ''.join([f'<td>{get_stat(home_stats, col, "defense")}</td>' for col in sport['def_cols']])

                off_headers = ''.join([f'<th>{col}</th>' for col in sport['off_cols']])
                def_headers = ''.join([f'<th>{col}</th>' for col in sport['def_cols']])

                games_html += f'''
                <div class="game-card">
                    <div class="game-header">
                        <span class="game-time">{game_time}</span>
                        <span class="matchup-text">{away_name} @ {home_name}</span>
                    </div>
                    <table class="stats-table">
                        <thead>
                            <tr>
                                <th class="team-col">TEAM</th>
                                <th>REC</th>
                                <th>PWR</th>
                                <th class="section-divider">|</th>
                                {off_headers}
                                <th class="section-divider">|</th>
                                {def_headers}
                                <th class="section-divider">|</th>
                                <th>SPREAD</th>
                                <th>ML</th>
                                <th>O/U</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr class="away-row">
                                <td class="team-col">
                                    <img src="{away_logo}" alt="{away_abbr}" class="team-logo" onerror="this.style.display='none'">
                                    <span class="abbr">{away_abbr}</span>
                                </td>
                                <td class="rec">{away_record}</td>
                                <td class="pwr {get_power_class(away_power)}">{away_power:.0f}</td>
                                <td class="section-divider">|</td>
                                {away_off_cells}
                                <td class="section-divider">|</td>
                                {away_def_cells}
                                <td class="section-divider">|</td>
                                <td class="spread">{trends.get('spread_away') or odds['spread_away']}</td>
                                <td class="ml">{trends.get('ml_away') or odds['ml_away']}</td>
                                <td class="total" rowspan="2">{trends.get('total') or odds['total']}</td>
                            </tr>
                            <tr class="home-row">
                                <td class="team-col">
                                    <img src="{home_logo}" alt="{home_abbr}" class="team-logo" onerror="this.style.display='none'">
                                    <span class="abbr">{home_abbr}</span>
                                </td>
                                <td class="rec">{home_record}</td>
                                <td class="pwr {get_power_class(home_power)}">{home_power:.0f}</td>
                                <td class="section-divider">|</td>
                                {home_off_cells}
                                <td class="section-divider">|</td>
                                {home_def_cells}
                                <td class="section-divider">|</td>
                                <td class="spread">{trends.get('spread_home') or odds['spread_home']}</td>
                                <td class="ml">{trends.get('ml_home') or odds['ml_home']}</td>
                            </tr>
                        </tbody>
                    </table>
                    <div class="info-section">
                        <div class="injury-bar">
                            <span class="inj-label">INJURIES:</span>
                            <span class="inj-team">{away_abbr}:</span> {away_inj}
                            <span class="inj-sep">|</span>
                            <span class="inj-team">{home_abbr}:</span> {home_inj}
                        </div>
                        <div class="trends-bar">
                            <span class="trend-item"><b>H2H:</b> {trends.get('h2h') or 'First meeting'}</span>
                            <span class="trend-sep">|</span>
                            <span class="trend-item"><b>Line:</b> {trends.get('open_spread') or '-'} → {trends.get('close_spread') or '-'}</span>
                            <span class="trend-sep">|</span>
                            <span class="trend-item"><b>Total:</b> {trends.get('open_total') or '-'} → {trends.get('close_total') or '-'}</span>
                        </div>
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

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Handicapping Hub - {date_str} | BetLegend</title>
    <meta name="description" content="Professional sports handicapping with advanced stats, power ratings, betting lines, and injury reports for NBA, NFL, NHL, NCAAB.">
    <link rel="canonical" href="https://www.betlegendpicks.com/handicapping-hub.html">
    <link rel="icon" href="https://www.betlegendpicks.com/newlogo.png">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            background: #f5f5f5;
            font-family: 'Inter', -apple-system, sans-serif;
            color: #1a1a1a;
            min-height: 100vh;
        }}

        .header {{
            background: linear-gradient(180deg, #1a365d 0%, #0d1b30 100%);
            padding: 20px 30px;
            border-bottom: 3px solid #fd5000;
            position: sticky;
            top: 0;
            z-index: 100;
        }}
        .header-inner {{ max-width: 1600px; margin: 0 auto; }}
        .header h1 {{ font-size: 28px; font-weight: 800; color: #fff; margin-bottom: 5px; }}
        .header h1 span {{ color: #fd5000; }}
        .timestamp {{ color: #a0aec0; font-size: 13px; margin-bottom: 15px; }}

        .tabs {{ display: flex; gap: 8px; flex-wrap: wrap; }}
        .tab {{
            background: rgba(255,255,255,0.1);
            border: 1px solid rgba(255,255,255,0.2);
            padding: 10px 24px;
            border-radius: 6px;
            color: #fff;
            cursor: pointer;
            font-weight: 600;
            font-size: 14px;
            transition: all 0.2s;
        }}
        .tab:hover {{ background: rgba(255,255,255,0.2); }}
        .tab.active {{ background: #fd5000; border-color: #fd5000; color: #fff; }}

        .container {{ max-width: 1600px; margin: 0 auto; padding: 30px; }}

        .section-header {{
            display: flex;
            align-items: center;
            gap: 15px;
            margin-bottom: 25px;
            padding-bottom: 15px;
            border-bottom: 2px solid #ddd;
        }}
        .section-header h2 {{ font-size: 22px; font-weight: 700; color: #1a365d; }}
        .game-count {{ color: #666; font-size: 14px; }}

        .game-card {{
            background: #fff;
            border: 1px solid #ddd;
            border-radius: 8px;
            margin-bottom: 20px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}

        .game-header {{
            background: linear-gradient(90deg, #1a365d, #2d4a7c);
            padding: 12px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 2px solid #fd5000;
        }}
        .game-time {{
            color: #fd5000;
            font-weight: 700;
            font-size: 14px;
        }}
        .matchup-text {{
            color: #fff;
            font-weight: 600;
            font-size: 15px;
        }}

        .stats-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }}
        .stats-table th {{
            background: #e8eef5;
            color: #1a365d;
            font-size: 10px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            padding: 10px 8px;
            text-align: center;
            border-bottom: 2px solid #ddd;
        }}
        .stats-table th.team-col {{
            text-align: left;
            padding-left: 15px;
            min-width: 100px;
        }}
        .stats-table th.section-divider {{
            color: #ccc;
            padding: 0 2px;
            width: 10px;
            background: #f0f0f0;
        }}
        .stats-table td {{
            padding: 10px 8px;
            text-align: center;
            border-bottom: 1px solid #eee;
            color: #333;
        }}
        .stats-table td.team-col {{
            text-align: left;
            padding-left: 15px;
        }}
        .stats-table td.section-divider {{
            color: #ccc;
            padding: 0;
            width: 10px;
            background: #fafafa;
        }}

        .team-logo {{
            width: 24px;
            height: 24px;
            object-fit: contain;
            vertical-align: middle;
            margin-right: 8px;
        }}
        .abbr {{
            font-weight: 700;
            color: #1a365d;
            font-size: 14px;
        }}

        .away-row {{ background: #fff; }}
        .home-row {{ background: #f8fafc; }}
        .away-row:hover, .home-row:hover {{ background: #f0f4f8; }}

        .rec {{ color: #666; font-size: 12px; font-weight: 600; }}
        .pwr {{ font-weight: 700; font-size: 14px; }}
        .pwr.elite {{ color: #059669; }}
        .pwr.good {{ color: #2563eb; }}
        .pwr.avg {{ color: #ca8a04; }}
        .pwr.poor {{ color: #dc2626; }}

        .spread, .ml {{ font-weight: 600; color: #1a1a1a; }}
        .total {{
            font-weight: 700;
            color: #fd5000;
            font-size: 15px;
            vertical-align: middle;
        }}

        .info-section {{
            border-top: 1px solid #eee;
        }}
        .injury-bar {{
            background: #fff8f0;
            padding: 8px 15px;
            font-size: 11px;
            color: #666;
            border-bottom: 1px solid #f0e8e0;
        }}
        .inj-label {{ color: #dc2626; font-weight: 700; margin-right: 8px; }}
        .inj-team {{ color: #1a365d; font-weight: 600; margin-left: 5px; }}
        .inj-sep {{ color: #ccc; margin: 0 10px; }}

        .trends-bar {{
            background: #f0f5fa;
            padding: 8px 15px;
            font-size: 11px;
            color: #333;
            display: flex;
            flex-wrap: wrap;
            gap: 5px;
        }}
        .trend-item {{ margin-right: 5px; }}
        .trend-item b {{ color: #1a365d; }}
        .trend-sep {{ color: #ccc; margin: 0 5px; }}

        .no-games {{
            text-align: center;
            padding: 60px 20px;
            color: #666;
            font-size: 16px;
            background: #fff;
            border-radius: 8px;
            border: 1px solid #ddd;
        }}

        .back-link {{
            text-align: center;
            padding: 30px;
        }}
        .back-link a {{
            color: #fd5000;
            text-decoration: none;
            font-size: 14px;
            padding: 10px 20px;
            border: 1px solid #ddd;
            border-radius: 6px;
            background: #fff;
            transition: all 0.2s;
        }}
        .back-link a:hover {{
            background: #fd5000;
            color: #fff;
            border-color: #fd5000;
        }}

        @media (max-width: 1200px) {{
            .stats-table {{ font-size: 11px; }}
            .stats-table th, .stats-table td {{ padding: 8px 4px; }}
            .team-logo {{ width: 20px; height: 20px; }}
        }}
        @media (max-width: 800px) {{
            .container {{ padding: 15px; }}
            .stats-table {{ font-size: 10px; }}
            .game-card {{ overflow-x: auto; }}
        }}
    </style>
</head>
<body>
    <header class="header">
        <div class="header-inner">
            <h1>HANDICAPPING <span>HUB</span></h1>
            <div class="timestamp">Updated: {time_str} • {date_str} • Advanced Stats & Power Ratings</div>
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
            document.querySelectorAll('.section').forEach(s => s.style.display = 'none');
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.getElementById('section-' + sport).style.display = 'block';
            event.target.classList.add('active');
        }}
    </script>
</body>
</html>'''

    return html

def main():
    print("Generating Handicapping Hub v2 WITH ADVANCED STATS...")
    html = generate_html()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(os.path.dirname(script_dir))
    output_path = os.path.join(repo_root, 'handicapping-hub.html')

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"Done! Saved to {output_path}")

if __name__ == "__main__":
    main()
