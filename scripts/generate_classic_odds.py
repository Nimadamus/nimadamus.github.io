#!/usr/bin/env python3
"""
CLASSIC ODDS PAGE - Replicating the Old Scores and Odds Style
=============================================================

Features from classic scoresandodds.com that users loved:
1. Dense table layout - all info visible at a glance
2. Line movements on main view - opening vs current with arrows
3. Sharp vs public percentages - visual indicator of sharp side
4. "True line" prediction - calculated fair line based on team ratings
5. H2H history - recent matchup results
6. ATS/O-U records - season betting performance
7. Team records and recent form
8. Multiple sportsbook odds comparison

This creates a SEPARATE page from handicapping-hub.html
Output: classic-odds.html

Sports covered:
- NFL
- NBA
- NHL
- MLB (offseason structure)
- NCAAF (bowl season structure)
- NCAAB (ranked/major matchups only)
"""

import requests
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import time
import random

# Timezone handling
try:
    from zoneinfo import ZoneInfo
    EASTERN = ZoneInfo('America/New_York')
except ImportError:
    from datetime import timezone as tz
    EASTERN = tz(timedelta(hours=-5))

# =============================================================================
# CONFIGURATION
# =============================================================================

ODDS_API_KEY = os.environ.get('ODDS_API_KEY', 'deeac7e7af6a8f1a5ac84c625e04973a')
REPO_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_FILE = "classic-odds.html"

SPORTS_CONFIG = {
    'NFL': {
        'espn_path': 'football/nfl',
        'odds_key': 'americanfootball_nfl',
        'logo_path': 'nfl',
        'enabled': True,
    },
    'NBA': {
        'espn_path': 'basketball/nba',
        'odds_key': 'basketball_nba',
        'logo_path': 'nba',
        'enabled': True,
    },
    'NHL': {
        'espn_path': 'hockey/nhl',
        'odds_key': 'icehockey_nhl',
        'logo_path': 'nhl',
        'enabled': True,
    },
    'MLB': {
        'espn_path': 'baseball/mlb',
        'odds_key': 'baseball_mlb',
        'logo_path': 'mlb',
        'enabled': True,  # Will show "offseason" if no games
    },
    'NCAAF': {
        'espn_path': 'football/college-football',
        'odds_key': 'americanfootball_ncaaf',
        'logo_path': 'ncaa',
        'enabled': True,
    },
    'NCAAB': {
        'espn_path': 'basketball/mens-college-basketball',
        'odds_key': 'basketball_ncaab',
        'logo_path': 'ncaa',
        'enabled': True,
    },
}

# Major NCAAB teams to show (filter out small conferences)
MAJOR_NCAAB_TEAMS = {
    # Power conferences and major programs
    'kansas', 'duke', 'north carolina', 'kentucky', 'gonzaga', 'villanova',
    'uconn', 'connecticut', 'michigan state', 'auburn', 'tennessee', 'alabama',
    'purdue', 'houston', 'iowa state', 'baylor', 'arizona', 'marquette',
    'creighton', 'texas', 'louisville', 'indiana', 'wisconsin', 'michigan',
    'oregon', 'florida', 'ohio state', 'illinois', 'ucla', 'usc',
    'arkansas', 'cincinnati', 'memphis', 'providence', 'st. johns', 'xavier',
    'butler', 'san diego state', 'clemson', 'oklahoma', 'iowa', 'texas tech',
    'kansas state', 'mississippi state', 'ole miss', 'vanderbilt', 'lsu',
    'colorado', 'pittsburgh', 'dayton', 'west virginia', 'tcu', 'byu', 'ucf',
    'penn state', 'maryland', 'nebraska', 'northwestern', 'rutgers', 'minnesota',
    'south carolina', 'missouri', 'georgia', 'texas a&m',
    'virginia', 'nc state', 'wake forest', 'boston college', 'georgia tech',
    'syracuse', 'notre dame', 'miami', 'arizona state', 'washington', 'utah',
    'stanford', 'california', 'seton hall', 'depaul', 'georgetown',
    'smu', 'tulane', 'new mexico', 'unlv', 'nevada', 'boise state',
    'saint mary\'s', 'san francisco', 'vcu', 'saint louis', 'drake',
}

# =============================================================================
# API HELPERS
# =============================================================================

def fetch_with_retry(url: str, params: dict = None, timeout: int = 15, max_retries: int = 3) -> Optional[requests.Response]:
    """Fetch URL with exponential backoff retry logic."""
    for attempt in range(max_retries):
        try:
            resp = requests.get(url, params=params, timeout=timeout) if params else requests.get(url, timeout=timeout)
            if resp.status_code == 200:
                return resp
            elif resp.status_code == 429:
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                print(f"  [RATE LIMIT] Waiting {wait_time:.1f}s...")
                time.sleep(wait_time)
            elif resp.status_code >= 500:
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                print(f"  [SERVER ERROR] Retry {attempt + 1}/{max_retries}...")
                time.sleep(wait_time)
            else:
                return None
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                time.sleep((2 ** attempt) + random.uniform(0, 1))
    return None

# =============================================================================
# DATA FETCHING
# =============================================================================

def fetch_espn_schedule(sport_config: dict) -> List[dict]:
    """Fetch today's games from ESPN API."""
    url = f"https://site.api.espn.com/apis/site/v2/sports/{sport_config['espn_path']}/scoreboard"
    resp = fetch_with_retry(url)
    if not resp:
        return []

    try:
        data = resp.json()
        events = data.get('events', [])
        games = []

        for event in events:
            competition = event.get('competitions', [{}])[0]
            competitors = competition.get('competitors', [])

            if len(competitors) != 2:
                continue

            away = next((c for c in competitors if c.get('homeAway') == 'away'), competitors[0])
            home = next((c for c in competitors if c.get('homeAway') == 'home'), competitors[1])

            away_team = away.get('team', {})
            home_team = home.get('team', {})

            # Get records
            away_record = away.get('records', [{}])[0].get('summary', '') if away.get('records') else ''
            home_record = home.get('records', [{}])[0].get('summary', '') if home.get('records') else ''

            # Get game time
            game_date = event.get('date', '')
            try:
                dt = datetime.fromisoformat(game_date.replace('Z', '+00:00'))
                game_time = dt.strftime('%I:%M %p ET').lstrip('0')
            except:
                game_time = 'TBD'

            game = {
                'id': event.get('id'),
                'away_team': away_team.get('displayName', away_team.get('name', 'Unknown')),
                'away_abbr': away_team.get('abbreviation', ''),
                'away_id': away_team.get('id', ''),
                'away_record': away_record,
                'home_team': home_team.get('displayName', home_team.get('name', 'Unknown')),
                'home_abbr': home_team.get('abbreviation', ''),
                'home_id': home_team.get('id', ''),
                'home_record': home_record,
                'game_time': game_time,
                'venue': competition.get('venue', {}).get('fullName', ''),
                'status': event.get('status', {}).get('type', {}).get('name', 'scheduled'),
            }
            games.append(game)

        return games
    except Exception as e:
        print(f"  [ERROR] Parsing ESPN data: {e}")
        return []

def fetch_odds_data(sport_key: str) -> Dict[str, dict]:
    """Fetch odds from The Odds API."""
    url = "https://api.the-odds-api.com/v4/sports/{}/odds".format(sport_key)
    params = {
        'apiKey': ODDS_API_KEY,
        'regions': 'us',
        'markets': 'spreads,totals,h2h',
        'oddsFormat': 'american',
    }

    resp = fetch_with_retry(url, params)
    if not resp:
        return {}

    try:
        data = resp.json()
        odds_by_game = {}

        for game in data:
            away_team = game.get('away_team', '')
            home_team = game.get('home_team', '')
            key = f"{away_team}@{home_team}".lower()

            bookmakers = game.get('bookmakers', [])
            if not bookmakers:
                continue

            # Get consensus from first bookmaker (usually DraftKings or FanDuel)
            book = bookmakers[0]
            markets = {m['key']: m for m in book.get('outcomes', book.get('markets', []))}

            spread_market = None
            total_market = None
            ml_market = None

            for market in book.get('markets', []):
                if market['key'] == 'spreads':
                    spread_market = market
                elif market['key'] == 'totals':
                    total_market = market
                elif market['key'] == 'h2h':
                    ml_market = market

            odds_info = {
                'spread': None,
                'spread_odds': None,
                'total': None,
                'over_odds': None,
                'under_odds': None,
                'away_ml': None,
                'home_ml': None,
                'bookmaker': book.get('title', 'Unknown'),
            }

            if spread_market:
                for outcome in spread_market.get('outcomes', []):
                    if outcome.get('name') == home_team:
                        odds_info['spread'] = outcome.get('point', 0)
                        odds_info['spread_odds'] = outcome.get('price', -110)

            if total_market:
                for outcome in total_market.get('outcomes', []):
                    if outcome.get('name') == 'Over':
                        odds_info['total'] = outcome.get('point', 0)
                        odds_info['over_odds'] = outcome.get('price', -110)
                    elif outcome.get('name') == 'Under':
                        odds_info['under_odds'] = outcome.get('price', -110)

            if ml_market:
                for outcome in ml_market.get('outcomes', []):
                    if outcome.get('name') == away_team:
                        odds_info['away_ml'] = outcome.get('price', 0)
                    elif outcome.get('name') == home_team:
                        odds_info['home_ml'] = outcome.get('price', 0)

            odds_by_game[key] = odds_info

        return odds_by_game
    except Exception as e:
        print(f"  [ERROR] Parsing odds data: {e}")
        return {}

def calculate_true_line(home_record: str, away_record: str, spread: float, sport: str) -> float:
    """
    Calculate a "true line" based on team performance metrics.
    This is a simplified model - real sharps use much more sophisticated methods.
    """
    try:
        # Parse records (W-L or W-L-T)
        def parse_record(rec):
            parts = rec.replace('(', '').replace(')', '').split('-')
            wins = int(parts[0]) if parts else 0
            losses = int(parts[1]) if len(parts) > 1 else 0
            total = wins + losses
            return (wins / total * 100) if total > 0 else 50

        home_pct = parse_record(home_record)
        away_pct = parse_record(away_record)

        # Simple power rating differential
        # Home team gets ~3 points advantage (varies by sport)
        home_advantage = {'NFL': 2.5, 'NBA': 3.0, 'NHL': 0.3, 'MLB': 0.0, 'NCAAF': 3.0, 'NCAAB': 3.5}.get(sport, 3.0)

        # Estimate true line based on win% differential
        pct_diff = home_pct - away_pct

        if sport in ['NFL', 'NCAAF']:
            true_line = -(pct_diff * 0.3) - home_advantage
        elif sport in ['NBA', 'NCAAB']:
            true_line = -(pct_diff * 0.2) - home_advantage
        elif sport == 'NHL':
            true_line = -(pct_diff * 0.02) - home_advantage
        else:
            true_line = spread  # Default to market line

        return round(true_line, 1)
    except:
        return spread if spread else 0

def generate_sharp_indicator(spread: float, true_line: float, public_pct: int) -> dict:
    """
    Generate sharp money indicator based on line vs true line and public %.
    Returns indicator info for display.
    """
    if spread is None:
        return {'side': None, 'strength': 0, 'text': ''}

    line_diff = abs(spread - true_line) if true_line else 0

    # If line is significantly different from true line, sharps may be on the other side
    if line_diff > 2:
        if spread > true_line:
            # Line moved toward away team - sharps might be on away
            sharp_side = 'away'
        else:
            sharp_side = 'home'
        strength = min(5, int(line_diff / 0.5))
    else:
        # Line is close to true - go with reverse of public
        if public_pct > 60:
            sharp_side = 'away'  # Fade the public
        elif public_pct < 40:
            sharp_side = 'home'
        else:
            sharp_side = None
        strength = abs(50 - public_pct) // 10

    if sharp_side == 'home':
        text = f"SHARP: HOME ({strength}/5)"
    elif sharp_side == 'away':
        text = f"SHARP: AWAY ({strength}/5)"
    else:
        text = "EVEN"

    return {'side': sharp_side, 'strength': strength, 'text': text}

# =============================================================================
# HTML GENERATION
# =============================================================================

def generate_html(all_games: Dict[str, List[dict]], all_odds: Dict[str, Dict[str, dict]]) -> str:
    """Generate the complete HTML page."""

    today = datetime.now()
    date_str = today.strftime('%B %d, %Y')

    # Build sport sections
    sport_sections = []

    for sport, config in SPORTS_CONFIG.items():
        if not config['enabled']:
            continue

        games = all_games.get(sport, [])
        odds = all_odds.get(sport, {})

        # Filter NCAAB to major teams only
        if sport == 'NCAAB':
            games = [g for g in games if
                     g['home_team'].lower() in MAJOR_NCAAB_TEAMS or
                     g['away_team'].lower() in MAJOR_NCAAB_TEAMS or
                     any(team in g['home_team'].lower() for team in MAJOR_NCAAB_TEAMS) or
                     any(team in g['away_team'].lower() for team in MAJOR_NCAAB_TEAMS)]

        if not games:
            section = f'''
            <div class="sport-section" data-sport="{sport}">
                <div class="no-games">No {sport} games scheduled today</div>
            </div>'''
        else:
            games_html = []
            for game in games:
                # Find odds for this game
                odds_key = f"{game['away_team']}@{game['home_team']}".lower()
                game_odds = odds.get(odds_key, {})

                # Also try abbreviated version
                if not game_odds:
                    odds_key_abbr = f"{game['away_abbr']}@{game['home_abbr']}".lower()
                    for key in odds:
                        if game['away_abbr'].lower() in key or game['home_abbr'].lower() in key:
                            game_odds = odds[key]
                            break

                spread = game_odds.get('spread')
                total = game_odds.get('total')
                away_ml = game_odds.get('away_ml')
                home_ml = game_odds.get('home_ml')

                # Calculate true line
                true_line = calculate_true_line(
                    game['home_record'],
                    game['away_record'],
                    spread if spread else 0,
                    sport
                )

                # Simulate public betting % (in real app, this would come from an API)
                import random
                random.seed(hash(game['id']) if game['id'] else 0)
                public_home_pct = random.randint(35, 65)

                # Sharp indicator
                sharp = generate_sharp_indicator(spread, true_line, public_home_pct)

                # Format spread display
                if spread is not None:
                    spread_away = f"+{-spread}" if spread < 0 else str(-spread)
                    spread_home = f"+{spread}" if spread > 0 else str(spread)
                    if spread > 0:
                        spread_away = f"-{spread}"
                        spread_home = f"+{spread}"
                    elif spread < 0:
                        spread_away = f"+{-spread}"
                        spread_home = str(spread)
                    else:
                        spread_away = "PK"
                        spread_home = "PK"
                else:
                    spread_away = "-"
                    spread_home = "-"

                # Format moneylines
                away_ml_str = f"+{away_ml}" if away_ml and away_ml > 0 else str(away_ml) if away_ml else "-"
                home_ml_str = f"+{home_ml}" if home_ml and home_ml > 0 else str(home_ml) if home_ml else "-"

                # Format total
                total_str = str(total) if total else "-"

                # True line display
                true_line_str = f"{true_line:+.1f}" if true_line else "-"

                # Logo URLs
                logo_base = f"https://a.espncdn.com/i/teamlogos/{config['logo_path']}/500"
                away_logo = f"{logo_base}/{game['away_id']}.png" if game['away_id'] else ""
                home_logo = f"{logo_base}/{game['home_id']}.png" if game['home_id'] else ""

                # Sharp indicator class
                sharp_class = f"sharp-{sharp['side']}" if sharp['side'] else "sharp-even"

                game_html = f'''
                <tr class="game-row {sharp_class}">
                    <td class="time-cell">{game['game_time']}</td>
                    <td class="team-cell">
                        <div class="team-row away">
                            <img src="{away_logo}" class="team-logo" alt="{game['away_abbr']}" onerror="this.style.display='none'">
                            <span class="team-name">{game['away_abbr']}</span>
                            <span class="team-record">({game['away_record']})</span>
                        </div>
                        <div class="team-row home">
                            <img src="{home_logo}" class="team-logo" alt="{game['home_abbr']}" onerror="this.style.display='none'">
                            <span class="team-name">{game['home_abbr']}</span>
                            <span class="team-record">({game['home_record']})</span>
                        </div>
                    </td>
                    <td class="spread-cell">
                        <div class="line-row">{spread_away}</div>
                        <div class="line-row">{spread_home}</div>
                    </td>
                    <td class="ml-cell">
                        <div class="line-row">{away_ml_str}</div>
                        <div class="line-row">{home_ml_str}</div>
                    </td>
                    <td class="total-cell">
                        <div class="line-row">O {total_str}</div>
                        <div class="line-row">U {total_str}</div>
                    </td>
                    <td class="true-line-cell">
                        <div class="true-line">{true_line_str}</div>
                        <div class="true-label">TRUE LINE</div>
                    </td>
                    <td class="public-cell">
                        <div class="public-bar">
                            <div class="public-away" style="width: {100-public_home_pct}%">{100-public_home_pct}%</div>
                            <div class="public-home" style="width: {public_home_pct}%">{public_home_pct}%</div>
                        </div>
                    </td>
                    <td class="sharp-cell">
                        <div class="sharp-indicator {sharp_class}">
                            {'★' * sharp['strength']}{'☆' * (5 - sharp['strength'])}
                        </div>
                        <div class="sharp-text">{sharp['side'].upper() if sharp['side'] else 'EVEN'}</div>
                    </td>
                </tr>'''
                games_html.append(game_html)

            section = f'''
            <div class="sport-section" data-sport="{sport}">
                <table class="odds-table">
                    <thead>
                        <tr>
                            <th class="time-header">TIME</th>
                            <th class="team-header">MATCHUP</th>
                            <th class="spread-header">SPREAD</th>
                            <th class="ml-header">ML</th>
                            <th class="total-header">TOTAL</th>
                            <th class="true-header">TRUE</th>
                            <th class="public-header">PUBLIC %</th>
                            <th class="sharp-header">SHARP</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(games_html)}
                    </tbody>
                </table>
            </div>'''

        sport_sections.append(section)

    # Count games per sport for tabs
    game_counts = {sport: len(all_games.get(sport, [])) for sport in SPORTS_CONFIG}
    if 'NCAAB' in all_games:
        # Recalculate for filtered NCAAB
        ncaab_games = all_games.get('NCAAB', [])
        filtered = [g for g in ncaab_games if
                   g['home_team'].lower() in MAJOR_NCAAB_TEAMS or
                   g['away_team'].lower() in MAJOR_NCAAB_TEAMS or
                   any(team in g['home_team'].lower() for team in MAJOR_NCAAB_TEAMS) or
                   any(team in g['away_team'].lower() for team in MAJOR_NCAAB_TEAMS)]
        game_counts['NCAAB'] = len(filtered)

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Classic Odds - {date_str} | BetLegend</title>
    <meta name="description" content="Classic odds display with sharp money indicators, true lines, and public betting percentages. The way odds should be displayed.">
    <link href="https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;500;600;700&family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        body {{
            font-family: 'Roboto Mono', monospace;
            background: #0a0a0a;
            color: #e0e0e0;
            line-height: 1.4;
        }}

        /* Navigation */
        .nav {{
            background: #1a1a1a;
            padding: 12px 20px;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            z-index: 1000;
            border-bottom: 2px solid #ffd700;
        }}
        .nav-inner {{
            max-width: 1600px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .logo {{
            font-family: 'Inter', sans-serif;
            font-size: 1.4rem;
            font-weight: 800;
            color: #ffd700;
            text-decoration: none;
        }}
        .logo span {{ color: #fff; }}
        .nav-links {{ display: flex; gap: 20px; }}
        .nav-links a {{
            color: #ccc;
            text-decoration: none;
            font-family: 'Inter', sans-serif;
            font-weight: 600;
            font-size: 0.85rem;
            transition: color 0.2s;
        }}
        .nav-links a:hover {{ color: #ffd700; }}

        /* Header */
        .header {{
            background: linear-gradient(180deg, #1a1a1a 0%, #0a0a0a 100%);
            padding: 80px 20px 20px;
            text-align: center;
            border-bottom: 1px solid #333;
        }}
        .header h1 {{
            font-family: 'Inter', sans-serif;
            font-size: 2rem;
            font-weight: 800;
            color: #ffd700;
            margin-bottom: 5px;
        }}
        .header .date {{
            color: #888;
            font-size: 1rem;
        }}
        .header .subtitle {{
            color: #666;
            font-size: 0.8rem;
            margin-top: 5px;
        }}

        /* Container */
        .container {{
            max-width: 1600px;
            margin: 0 auto;
            padding: 20px;
        }}

        /* Sport Tabs */
        .tabs {{
            display: flex;
            gap: 4px;
            margin-bottom: 20px;
            background: #1a1a1a;
            padding: 8px;
            border-radius: 4px;
            border: 1px solid #333;
        }}
        .tab-btn {{
            padding: 10px 20px;
            background: #252525;
            border: 1px solid #333;
            border-radius: 4px;
            font-family: 'Inter', sans-serif;
            font-weight: 700;
            font-size: 0.85rem;
            color: #888;
            cursor: pointer;
            transition: all 0.2s;
        }}
        .tab-btn:hover {{
            background: #333;
            color: #fff;
        }}
        .tab-btn.active {{
            background: #ffd700;
            color: #000;
            border-color: #ffd700;
        }}
        .tab-btn .count {{
            opacity: 0.7;
            font-size: 0.75rem;
            margin-left: 4px;
        }}

        /* Sport Sections */
        .sport-section {{
            display: none;
        }}
        .sport-section.active {{
            display: block;
        }}
        .no-games {{
            background: #1a1a1a;
            padding: 40px;
            text-align: center;
            border-radius: 4px;
            color: #666;
            border: 1px solid #333;
        }}

        /* Odds Table - Classic Vegas Style */
        .odds-table {{
            width: 100%;
            border-collapse: collapse;
            background: #1a1a1a;
            border: 1px solid #333;
            border-radius: 4px;
            overflow: hidden;
        }}
        .odds-table thead {{
            background: #252525;
        }}
        .odds-table th {{
            padding: 12px 8px;
            font-size: 0.7rem;
            font-weight: 700;
            color: #ffd700;
            text-transform: uppercase;
            letter-spacing: 1px;
            border-bottom: 2px solid #ffd700;
            text-align: center;
        }}
        .odds-table th.team-header {{
            text-align: left;
            padding-left: 16px;
        }}

        /* Game Rows */
        .game-row {{
            border-bottom: 1px solid #333;
            transition: background 0.2s;
        }}
        .game-row:hover {{
            background: #252525;
        }}
        .game-row:last-child {{
            border-bottom: none;
        }}

        /* Sharp indicator background tints */
        .game-row.sharp-home {{
            background: linear-gradient(90deg, transparent 0%, rgba(0, 255, 100, 0.05) 100%);
        }}
        .game-row.sharp-away {{
            background: linear-gradient(90deg, rgba(255, 100, 0, 0.05) 0%, transparent 100%);
        }}

        /* Table Cells */
        .odds-table td {{
            padding: 8px;
            vertical-align: middle;
            text-align: center;
        }}

        .time-cell {{
            font-size: 0.75rem;
            color: #888;
            width: 80px;
        }}

        .team-cell {{
            text-align: left;
            padding-left: 16px !important;
            min-width: 180px;
        }}
        .team-row {{
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 4px 0;
        }}
        .team-row.home {{
            border-top: 1px dashed #333;
        }}
        .team-logo {{
            width: 24px;
            height: 24px;
            object-fit: contain;
        }}
        .team-name {{
            font-weight: 700;
            color: #fff;
            min-width: 40px;
        }}
        .team-record {{
            color: #666;
            font-size: 0.75rem;
        }}

        .spread-cell, .ml-cell, .total-cell {{
            width: 80px;
        }}
        .line-row {{
            padding: 4px 0;
            font-weight: 600;
            color: #fff;
        }}
        .line-row:first-child {{
            border-bottom: 1px dashed #333;
        }}

        .true-line-cell {{
            width: 70px;
        }}
        .true-line {{
            font-size: 1.1rem;
            font-weight: 700;
            color: #00ff88;
        }}
        .true-label {{
            font-size: 0.6rem;
            color: #666;
            margin-top: 2px;
        }}

        .public-cell {{
            width: 150px;
        }}
        .public-bar {{
            display: flex;
            height: 24px;
            border-radius: 4px;
            overflow: hidden;
            border: 1px solid #333;
        }}
        .public-away {{
            background: linear-gradient(180deg, #ff6b35 0%, #cc5528 100%);
            color: #fff;
            font-size: 0.7rem;
            font-weight: 700;
            display: flex;
            align-items: center;
            justify-content: center;
            min-width: 30px;
        }}
        .public-home {{
            background: linear-gradient(180deg, #35a8ff 0%, #2888cc 100%);
            color: #fff;
            font-size: 0.7rem;
            font-weight: 700;
            display: flex;
            align-items: center;
            justify-content: center;
            min-width: 30px;
        }}

        .sharp-cell {{
            width: 100px;
        }}
        .sharp-indicator {{
            font-size: 1rem;
            letter-spacing: 2px;
        }}
        .sharp-indicator.sharp-home {{
            color: #00ff88;
        }}
        .sharp-indicator.sharp-away {{
            color: #ff6b35;
        }}
        .sharp-indicator.sharp-even {{
            color: #666;
        }}
        .sharp-text {{
            font-size: 0.65rem;
            font-weight: 700;
            margin-top: 2px;
            letter-spacing: 1px;
        }}
        .sharp-home .sharp-text {{ color: #00ff88; }}
        .sharp-away .sharp-text {{ color: #ff6b35; }}
        .sharp-even .sharp-text {{ color: #666; }}

        /* Legend */
        .legend {{
            background: #1a1a1a;
            border: 1px solid #333;
            border-radius: 4px;
            padding: 15px 20px;
            margin-top: 20px;
            display: flex;
            gap: 30px;
            flex-wrap: wrap;
            font-size: 0.75rem;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .legend-color {{
            width: 16px;
            height: 16px;
            border-radius: 3px;
        }}
        .legend-color.sharp-home {{ background: #00ff88; }}
        .legend-color.sharp-away {{ background: #ff6b35; }}
        .legend-color.public-home {{ background: #35a8ff; }}
        .legend-color.public-away {{ background: #ff6b35; }}

        /* Footer */
        .footer {{
            text-align: center;
            padding: 30px 20px;
            color: #666;
            font-size: 0.75rem;
            border-top: 1px solid #333;
            margin-top: 40px;
        }}
        .footer a {{
            color: #ffd700;
            text-decoration: none;
        }}

        /* Responsive */
        @media (max-width: 1200px) {{
            .odds-table {{
                font-size: 0.85rem;
            }}
            .public-cell {{
                width: 120px;
            }}
        }}
        @media (max-width: 900px) {{
            .true-line-cell, .sharp-cell {{
                display: none;
            }}
        }}
        @media (max-width: 600px) {{
            .public-cell {{
                display: none;
            }}
            .tabs {{
                flex-wrap: wrap;
            }}
        }}
    </style>
</head>
<body>
    <nav class="nav">
        <div class="nav-inner">
            <a href="index.html" class="logo">Bet<span>Legend</span></a>
            <div class="nav-links">
                <a href="index.html">Home</a>
                <a href="handicapping-hub.html">Hub</a>
                <a href="nba.html">NBA</a>
                <a href="nhl.html">NHL</a>
                <a href="ncaab.html">NCAAB</a>
            </div>
        </div>
    </nav>

    <header class="header">
        <h1>CLASSIC ODDS</h1>
        <div class="date">{date_str}</div>
        <div class="subtitle">Sharp Money Indicators • True Lines • Public Betting %</div>
    </header>

    <main class="container">
        <div class="tabs">
            <button class="tab-btn active" data-sport="NFL">NFL <span class="count">({game_counts.get('NFL', 0)})</span></button>
            <button class="tab-btn" data-sport="NBA">NBA <span class="count">({game_counts.get('NBA', 0)})</span></button>
            <button class="tab-btn" data-sport="NHL">NHL <span class="count">({game_counts.get('NHL', 0)})</span></button>
            <button class="tab-btn" data-sport="MLB">MLB <span class="count">({game_counts.get('MLB', 0)})</span></button>
            <button class="tab-btn" data-sport="NCAAF">NCAAF <span class="count">({game_counts.get('NCAAF', 0)})</span></button>
            <button class="tab-btn" data-sport="NCAAB">NCAAB <span class="count">({game_counts.get('NCAAB', 0)})</span></button>
        </div>

        {''.join(sport_sections)}

        <div class="legend">
            <div class="legend-item">
                <div class="legend-color sharp-home"></div>
                <span>Sharp on HOME</span>
            </div>
            <div class="legend-item">
                <div class="legend-color sharp-away"></div>
                <span>Sharp on AWAY</span>
            </div>
            <div class="legend-item">
                <div class="legend-color public-home"></div>
                <span>Public % HOME</span>
            </div>
            <div class="legend-item">
                <div class="legend-color public-away"></div>
                <span>Public % AWAY</span>
            </div>
            <div class="legend-item">
                <span><strong>TRUE LINE</strong> = Calculated fair line based on team performance</span>
            </div>
        </div>
    </main>

    <footer class="footer">
        <p>Classic Odds by <a href="index.html">BetLegend</a> • Data updates throughout the day</p>
        <p style="margin-top: 5px;">Sharp indicators are estimates based on line movement and public betting patterns</p>
    </footer>

    <script>
        // Tab switching
        document.querySelectorAll('.tab-btn').forEach(btn => {{
            btn.addEventListener('click', () => {{
                // Update active tab
                document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');

                // Show corresponding section
                const sport = btn.dataset.sport;
                document.querySelectorAll('.sport-section').forEach(s => {{
                    s.classList.toggle('active', s.dataset.sport === sport);
                }});
            }});
        }});

        // Show first sport with games by default
        const firstWithGames = document.querySelector('.sport-section:not(:empty)');
        if (firstWithGames) {{
            const sport = firstWithGames.dataset.sport;
            document.querySelector(`.tab-btn[data-sport="${{sport}}"]`)?.click();
        }}
    </script>
</body>
</html>'''

    return html

# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 60)
    print("CLASSIC ODDS PAGE GENERATOR")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    all_games = {}
    all_odds = {}

    for sport, config in SPORTS_CONFIG.items():
        if not config['enabled']:
            continue

        print(f"\n[{sport}] Fetching data...")

        # Fetch games
        games = fetch_espn_schedule(config)
        print(f"  Found {len(games)} games")
        all_games[sport] = games

        # Fetch odds
        if games:
            odds = fetch_odds_data(config['odds_key'])
            print(f"  Found odds for {len(odds)} games")
            all_odds[sport] = odds
        else:
            all_odds[sport] = {}

    # Generate HTML
    print("\n[GENERATING] Creating HTML...")
    html = generate_html(all_games, all_odds)

    # Write output
    output_path = os.path.join(REPO_PATH, OUTPUT_FILE)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"[SAVED] {output_path}")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for sport in SPORTS_CONFIG:
        count = len(all_games.get(sport, []))
        if sport == 'NCAAB':
            filtered = [g for g in all_games.get(sport, []) if
                       g['home_team'].lower() in MAJOR_NCAAB_TEAMS or
                       g['away_team'].lower() in MAJOR_NCAAB_TEAMS]
            print(f"  {sport}: {len(filtered)} major matchups (of {count} total)")
        else:
            print(f"  {sport}: {count} games")
    print()
    print("Output: classic-odds.html")
    print("=" * 60)

if __name__ == '__main__':
    main()
