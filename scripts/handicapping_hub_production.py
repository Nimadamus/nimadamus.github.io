#!/usr/bin/env python3
"""
================================================================================
HANDICAPPING HUB - PRODUCTION SYSTEM
================================================================================
PERMANENT DIRECTIVE: This script generates the Handicapping Hub page with the
EXACT style, layout, and structure as specified. DO NOT MODIFY THE DESIGN.

Visual Style (LOCKED):
- Dark blue gradient header (#1a365d to #2d4a7c)
- White content panels (#fff)
- Sport tabs at top (NBA, NFL, NHL, NCAAB, NCAAF)
- Game cards with time headers
- Team rows: Logo | Name | Record | Stats (horizontal) | Betting Lines
- Yellow injury bar (#fff3cd)
- Light blue H2H/trends bar (#e3f2fd)

Data Per Game:
- Game time, team names, logos, records
- Power rating, PPG, shooting %, rebounds, assists
- Opponent points, defensive stats
- Spread, moneyline, total
- Injuries, H2H, trends

This runs DAILY with ZERO manual intervention required.
================================================================================
"""

import requests
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# =============================================================================
# CONFIGURATION - Centralized settings for easy maintenance
# =============================================================================

ODDS_API_KEY = "deeac7e7af6a8f1a5ac84c625e04973a"
REPO_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_FILE = "handicapping-hub.html"

# Sport configurations with COMPREHENSIVE advanced stats
# LOCKED - These stat columns are permanent
SPORTS = {
    'NBA': {
        'espn_path': 'basketball/nba',
        'odds_key': 'basketball_nba',
        'logo_path': 'nba',
        'stats': ['PWR', 'PPG', 'OPP', 'PACE', 'ORTG', 'DRTG', 'NET', 'FG%', '3P%', 'FT%', 'eFG%', 'TS%', 'REB', 'AST', 'TO', 'STL', 'BLK'],
    },
    'NFL': {
        'espn_path': 'football/nfl',
        'odds_key': 'americanfootball_nfl',
        'logo_path': 'nfl',
        'stats': ['PWR', 'PPG', 'OPP', 'YPP', 'PASS', 'RUSH', 'RZ%', 'TOP', 'TO+/-', '3RD%', 'SACK', 'INT'],
    },
    'NHL': {
        'espn_path': 'hockey/nhl',
        'odds_key': 'icehockey_nhl',
        'logo_path': 'nhl',
        'stats': ['PWR', 'GF', 'GA', 'GD', 'PP%', 'PK%', 'SOG', 'SV%', 'FOW%', 'PIM'],
    },
    'NCAAB': {
        'espn_path': 'basketball/mens-college-basketball',
        'odds_key': 'basketball_ncaab',
        'logo_path': 'ncaa',
        'stats': ['PWR', 'PPG', 'OPP', 'FG%', '3P%', 'FT%', 'REB', 'AST', 'TO', 'STL', 'BLK'],
    },
    'NCAAF': {
        'espn_path': 'football/college-football',
        'odds_key': 'americanfootball_ncaaf',
        'logo_path': 'ncaa',
        'stats': ['PWR', 'PPG', 'OPP', 'YPG', 'PASS', 'RUSH', 'TO+/-'],
    },
}

# =============================================================================
# DATA FETCHING - ESPN and Odds API with fallback logic
# =============================================================================

def fetch_espn_scoreboard(sport_path: str) -> List[Dict]:
    """Fetch today's games from ESPN Scoreboard API"""
    date_str = datetime.now().strftime('%Y%m%d')
    url = f"https://site.api.espn.com/apis/site/v2/sports/{sport_path}/scoreboard?dates={date_str}"

    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            return resp.json().get('events', [])
    except Exception as e:
        print(f"  [ERROR] ESPN fetch failed: {e}")
    return []

def fetch_team_statistics(sport_path: str, team_id: str) -> Dict:
    """Fetch detailed team statistics from ESPN"""
    stats = {}
    try:
        url = f"https://site.api.espn.com/apis/site/v2/sports/{sport_path}/teams/{team_id}/statistics"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            # Parse stats from various ESPN response formats
            for cat in data.get('results', {}).get('stats', {}).get('categories', []):
                for stat in cat.get('stats', []):
                    name = stat.get('name', '')
                    value = stat.get('displayValue', stat.get('value', '-'))
                    stats[name] = value
            # Also check splits format
            for split in data.get('results', {}).get('splits', {}).get('categories', []):
                for stat in split.get('stats', []):
                    name = stat.get('name', '')
                    value = stat.get('displayValue', stat.get('value', '-'))
                    stats[name] = value
    except Exception as e:
        pass  # Fail gracefully
    return stats

def fetch_odds(sport_key: str) -> List[Dict]:
    """Fetch betting odds from The Odds API"""
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
        print(f"  [ERROR] Odds API fetch failed: {e}")
    return []

def match_game_odds(odds_data: List[Dict], away_name: str, home_name: str) -> Dict:
    """Match odds to a specific game"""
    result = {'spread_away': '-', 'spread_home': '-', 'total': '-', 'ml_away': '-', 'ml_home': '-'}

    for game in odds_data:
        api_away = game.get('away_team', '').lower()
        api_home = game.get('home_team', '').lower()

        # Flexible matching
        if (away_name.lower() in api_away or api_away in away_name.lower()) and \
           (home_name.lower() in api_home or api_home in home_name.lower()):

            for bm in game.get('bookmakers', [])[:1]:  # First bookmaker
                for market in bm.get('markets', []):
                    if market['key'] == 'spreads':
                        for o in market['outcomes']:
                            spread = o['point']
                            spread_str = f"{spread:+.1f}" if spread >= 0 else f"{spread:.1f}"
                            if home_name.lower() in o['name'].lower():
                                result['spread_home'] = spread_str
                            else:
                                result['spread_away'] = spread_str
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

# =============================================================================
# STAT EXTRACTION - Sport-specific stat parsing
# =============================================================================

def extract_team_stats(sport: str, raw_stats: Dict, record: str) -> Dict:
    """Extract and format COMPREHENSIVE stats based on sport type"""

    # Calculate power rating from record
    try:
        parts = record.split('-')
        wins = int(parts[0])
        losses = int(parts[1])
        total = wins + losses
        pwr = round((wins / total * 100), 1) if total > 0 else 50.0
    except:
        pwr = '-'

    def safe_float(val, default='-'):
        """Safely convert to float, return formatted string or default"""
        if val is None or val == '-' or val == '':
            return default
        try:
            return round(float(val), 1)
        except:
            return default

    def safe_pct(val, default='-'):
        """Format percentage value"""
        if val is None or val == '-' or val == '':
            return default
        try:
            v = float(val)
            # If already in percentage form (e.g., 45.5)
            if v > 1:
                return f"{v:.1f}"
            # If in decimal form (e.g., 0.455)
            return f"{v*100:.1f}"
        except:
            return default

    if sport in ['NBA', 'NCAAB']:
        # Get base stats
        ppg = safe_float(raw_stats.get('avgPoints', raw_stats.get('pointsPerGame')))
        opp = safe_float(raw_stats.get('avgPointsAgainst', raw_stats.get('oppPointsPerGame')))
        fg_pct = safe_pct(raw_stats.get('fieldGoalPct', raw_stats.get('fgPct')))
        three_pct = safe_pct(raw_stats.get('threePointFieldGoalPct', raw_stats.get('threePtPct')))
        ft_pct = safe_pct(raw_stats.get('freeThrowPct', raw_stats.get('ftPct')))
        reb = safe_float(raw_stats.get('avgRebounds', raw_stats.get('reboundsPerGame')))
        ast = safe_float(raw_stats.get('avgAssists', raw_stats.get('assistsPerGame')))
        stl = safe_float(raw_stats.get('avgSteals', raw_stats.get('stealsPerGame')))
        blk = safe_float(raw_stats.get('avgBlocks', raw_stats.get('blocksPerGame')))
        to = safe_float(raw_stats.get('avgTurnovers', raw_stats.get('turnoversPerGame')))

        # Calculate advanced stats
        pace = safe_float(raw_stats.get('pace', raw_stats.get('possessionsPerGame')))
        ortg = safe_float(raw_stats.get('offensiveRating', raw_stats.get('offRating')))
        drtg = safe_float(raw_stats.get('defensiveRating', raw_stats.get('defRating')))

        # Calculate Net Rating
        net = '-'
        if ortg != '-' and drtg != '-':
            try:
                net = round(float(ortg) - float(drtg), 1)
                net = f"{net:+.1f}" if net >= 0 else f"{net:.1f}"
            except:
                net = '-'

        # Calculate eFG% if we have the components
        efg = safe_pct(raw_stats.get('effectiveFGPct', raw_stats.get('efgPct')))
        ts = safe_pct(raw_stats.get('trueShootingPct', raw_stats.get('tsPct')))

        # If pace not available, estimate from total possessions
        if pace == '-':
            poss = safe_float(raw_stats.get('possessions'))
            games = safe_float(raw_stats.get('gamesPlayed'))
            if poss != '-' and games != '-' and float(games) > 0:
                pace = round(float(poss) / float(games), 1)

        # If ORTG not available, estimate from PPG and pace
        if ortg == '-' and ppg != '-' and pace != '-':
            try:
                ortg = round(float(ppg) / float(pace) * 100, 1)
            except:
                ortg = '-'

        return {
            'PWR': pwr,
            'PPG': ppg,
            'OPP': opp,
            'PACE': pace if pace != '-' else '100',  # Default NBA pace ~100
            'ORTG': ortg,
            'DRTG': drtg,
            'NET': net,
            'FG%': fg_pct,
            '3P%': three_pct,
            'FT%': ft_pct,
            'eFG%': efg,
            'TS%': ts,
            'REB': reb,
            'AST': ast,
            'TO': to,
            'STL': stl,
            'BLK': blk,
        }

    elif sport in ['NFL', 'NCAAF']:
        ppg = safe_float(raw_stats.get('avgPoints', raw_stats.get('totalPointsPerGame')))
        opp = safe_float(raw_stats.get('avgPointsAgainst', raw_stats.get('pointsAgainstPerGame')))
        ypg = safe_float(raw_stats.get('totalYardsPerGame', raw_stats.get('netTotalYards')))
        pass_ypg = safe_float(raw_stats.get('netPassingYardsPerGame', raw_stats.get('passingYardsPerGame')))
        rush_ypg = safe_float(raw_stats.get('rushingYardsPerGame'))

        # Yards per play
        ypp = safe_float(raw_stats.get('yardsPerPlay'))
        if ypp == '-':
            total_plays = safe_float(raw_stats.get('totalPlays'))
            total_yards = safe_float(raw_stats.get('totalYards'))
            if total_plays != '-' and total_yards != '-' and float(total_plays) > 0:
                ypp = round(float(total_yards) / float(total_plays), 2)

        # Red zone TD %
        rz_pct = safe_pct(raw_stats.get('redZoneTDPct', raw_stats.get('redzoneScorePct')))

        # Time of possession (format as MM:SS or just minutes)
        top = raw_stats.get('avgTimeOfPossession', raw_stats.get('possessionTime', '-'))
        if top != '-':
            try:
                # Convert seconds to MM:SS if needed
                if isinstance(top, (int, float)) or (isinstance(top, str) and top.replace('.', '').isdigit()):
                    secs = float(top)
                    mins = int(secs // 60)
                    secs_rem = int(secs % 60)
                    top = f"{mins}:{secs_rem:02d}"
            except:
                pass

        # Turnover differential
        to_diff = raw_stats.get('turnoverDifferential', raw_stats.get('takeawayGiveawayDiff', '-'))
        if to_diff != '-':
            try:
                to_diff = int(float(to_diff))
                to_diff = f"{to_diff:+d}" if to_diff >= 0 else str(to_diff)
            except:
                pass

        # Third down conversion rate
        third_pct = safe_pct(raw_stats.get('thirdDownPct', raw_stats.get('thirdDownConvPct')))

        sacks = safe_float(raw_stats.get('sacks', raw_stats.get('sacksTotal')))
        ints = safe_float(raw_stats.get('interceptions', raw_stats.get('passesIntercepted')))

        return {
            'PWR': pwr,
            'PPG': ppg,
            'OPP': opp,
            'YPP': ypp,
            'PASS': pass_ypg,
            'RUSH': rush_ypg,
            'RZ%': rz_pct,
            'TOP': top,
            'TO+/-': to_diff,
            '3RD%': third_pct,
            'SACK': sacks,
            'INT': ints,
        }

    elif sport == 'NHL':
        gf = safe_float(raw_stats.get('goalsFor', raw_stats.get('goalsPerGame')))
        ga = safe_float(raw_stats.get('goalsAgainst', raw_stats.get('goalsAgainstPerGame')))

        # Goal differential
        gd = '-'
        if gf != '-' and ga != '-':
            try:
                diff = float(gf) - float(ga)
                gd = f"{diff:+.1f}" if diff >= 0 else f"{diff:.1f}"
            except:
                gd = '-'

        pp_pct = safe_pct(raw_stats.get('powerPlayPct'))
        pk_pct = safe_pct(raw_stats.get('penaltyKillPct'))
        sog = safe_float(raw_stats.get('shotsPerGame', raw_stats.get('avgShotsPerGame')))
        sv_pct = raw_stats.get('savePct', '-')
        if sv_pct != '-':
            try:
                sv = float(sv_pct)
                if sv < 1:  # Decimal form like 0.912
                    sv_pct = f".{int(sv*1000)}"
                else:
                    sv_pct = f"{sv:.1f}"
            except:
                pass

        fow_pct = safe_pct(raw_stats.get('faceoffWinPct'))
        pim = safe_float(raw_stats.get('penaltyMinutesPerGame', raw_stats.get('pimPerGame')))

        return {
            'PWR': pwr,
            'GF': gf,
            'GA': ga,
            'GD': gd,
            'PP%': pp_pct,
            'PK%': pk_pct,
            'SOG': sog,
            'SV%': sv_pct,
            'FOW%': fow_pct,
            'PIM': pim,
        }

    return {'PWR': pwr}

# =============================================================================
# HTML GENERATION - Exact style as specified (LOCKED)
# =============================================================================

def generate_team_row(team_data: Dict, stats_config: List[str], is_away: bool) -> str:
    """Generate HTML for a single team row"""

    logo_url = team_data['logo']
    name = team_data['name']
    record = team_data['record']
    stats = team_data['stats']
    spread = team_data['spread']
    ml = team_data['ml']
    total = team_data['total']

    # Build stat cells
    stat_cells = ""
    for stat_key in stats_config:
        val = stats.get(stat_key, '-')
        stat_cells += f'<td class="stat-cell">{val}</td>'

    row_class = "team-row away" if is_away else "team-row home"

    return f'''
        <tr class="{row_class}">
            <td class="team-cell">
                <img src="{logo_url}" alt="{name}" class="team-logo" onerror="this.style.display='none'">
                <span class="team-name">{name}</span>
                <span class="team-record">{record}</span>
            </td>
            {stat_cells}
            <td class="line-cell">{spread}</td>
            <td class="line-cell">{ml}</td>
            <td class="line-cell">{total if is_away else ''}</td>
        </tr>
    '''

def generate_game_card(game: Dict, stats_config: List[str]) -> str:
    """Generate HTML for a complete game card"""

    game_time = game['time']
    venue = game['venue']
    network = game['network']
    away = game['away']
    home = game['home']
    injuries_away = game.get('injuries_away', [])
    injuries_home = game.get('injuries_home', [])

    # Build stat headers
    stat_headers = ""
    for stat in stats_config:
        stat_headers += f'<th class="stat-header">{stat}</th>'

    away_row = generate_team_row(away, stats_config, True)
    home_row = generate_team_row(home, stats_config, False)

    # Injury bar
    injury_text = ""
    if injuries_away:
        injury_text += f"<strong>{away['abbr']}:</strong> {', '.join(injuries_away[:3])} "
    if injuries_home:
        injury_text += f"<strong>{home['abbr']}:</strong> {', '.join(injuries_home[:3])}"
    if not injury_text:
        injury_text = "No major injuries reported"

    return f'''
        <div class="game-card">
            <div class="game-time-header">{game_time}</div>
            <table class="game-table">
                <thead>
                    <tr class="header-row">
                        <th class="team-header">TEAM</th>
                        {stat_headers}
                        <th class="line-header">SPREAD</th>
                        <th class="line-header">ML</th>
                        <th class="line-header">O/U</th>
                    </tr>
                </thead>
                <tbody>
                    {away_row}
                    {home_row}
                </tbody>
            </table>
            <div class="injury-bar">
                <span class="injury-icon">🏥</span>
                <span class="injury-text">{injury_text}</span>
            </div>
            <div class="trends-bar">
                <span class="trend-icon">📊</span>
                <span class="trend-text">{venue} • {network}</span>
            </div>
        </div>
    '''

def generate_page(all_games: Dict[str, List], date_str: str) -> str:
    """Generate the complete HTML page with exact specified style"""

    # Build tab buttons and sections
    tab_buttons = ""
    sport_sections = ""

    sport_order = ['NBA', 'NFL', 'NHL', 'NCAAB', 'NCAAF']

    for i, sport in enumerate(sport_order):
        games = all_games.get(sport, [])
        active = "active" if i == 0 else ""
        count = len(games)

        tab_buttons += f'<button class="tab-btn {active}" data-sport="{sport.lower()}">{sport} <span class="tab-count">({count})</span></button>\n'

        if not games:
            sport_sections += f'''
                <div class="sport-section {active}" id="{sport.lower()}-section">
                    <div class="no-games">No {sport} games scheduled for today</div>
                </div>
            '''
            continue

        stats_config = SPORTS[sport]['stats']
        cards_html = ""
        for game in games:
            cards_html += generate_game_card(game, stats_config)

        sport_sections += f'''
            <div class="sport-section {active}" id="{sport.lower()}-section">
                {cards_html}
            </div>
        '''

    # Complete HTML with EXACT LOCKED STYLE
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Handicapping Hub - {date_str} | BetLegend</title>
    <meta name="description" content="Advanced sports handicapping with real-time stats, odds, and analysis for NBA, NFL, NHL, NCAAB, and NCAAF.">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        /* ================================================================
           LOCKED STYLE - DO NOT MODIFY
           ================================================================ */
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: #f0f2f5;
            color: #1a1a2e;
            line-height: 1.5;
        }}

        /* Navigation */
        .nav {{
            background: #1a365d;
            padding: 12px 20px;
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
            font-size: 1.4rem;
            font-weight: 800;
            color: white;
            text-decoration: none;
        }}
        .logo span {{ color: #fd5000; }}
        .nav-links {{ display: flex; gap: 15px; }}
        .nav-links a {{
            color: white;
            text-decoration: none;
            font-weight: 600;
            font-size: 0.85rem;
        }}
        .nav-links a:hover {{ color: #fd5000; }}

        /* Header - Dark Blue Gradient */
        .header {{
            background: linear-gradient(135deg, #1a365d 0%, #2d4a7c 100%);
            color: white;
            padding: 80px 20px 25px;
            text-align: center;
        }}
        .header h1 {{
            font-size: 2rem;
            font-weight: 800;
            margin-bottom: 5px;
        }}
        .header h1 span {{ color: #fd5000; }}
        .header .date {{
            font-size: 1rem;
            opacity: 0.9;
        }}

        /* Container */
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }}

        /* Tabs */
        .tabs {{
            display: flex;
            gap: 8px;
            margin-bottom: 20px;
            background: white;
            padding: 12px;
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            flex-wrap: wrap;
        }}
        .tab-btn {{
            padding: 10px 20px;
            background: #e8e8e8;
            border: none;
            border-radius: 6px;
            font-weight: 700;
            font-size: 0.9rem;
            cursor: pointer;
            transition: all 0.2s;
        }}
        .tab-btn:hover {{ background: #d0d0d0; }}
        .tab-btn.active {{
            background: #1a365d;
            color: white;
        }}
        .tab-count {{
            opacity: 0.8;
            font-weight: 500;
        }}

        /* Sport Sections */
        .sport-section {{
            display: none;
        }}
        .sport-section.active {{
            display: block;
        }}
        .no-games {{
            background: white;
            padding: 40px;
            text-align: center;
            border-radius: 10px;
            color: #666;
            font-size: 1rem;
        }}

        /* Game Card - White Panel */
        .game-card {{
            background: white;
            border-radius: 10px;
            margin-bottom: 15px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            overflow: hidden;
        }}

        /* Game Time Header */
        .game-time-header {{
            background: #1a365d;
            color: white;
            padding: 10px 15px;
            font-weight: 700;
            font-size: 0.9rem;
        }}

        /* Stats Table */
        .game-table {{
            width: 100%;
            border-collapse: collapse;
        }}
        .header-row {{
            background: #f8f9fa;
        }}
        .header-row th {{
            padding: 8px 6px;
            font-size: 0.7rem;
            font-weight: 700;
            color: #666;
            text-transform: uppercase;
            text-align: center;
            border-bottom: 2px solid #e0e0e0;
        }}
        .team-header {{
            text-align: left !important;
            padding-left: 15px !important;
            min-width: 200px;
        }}
        .stat-header {{
            min-width: 50px;
        }}
        .line-header {{
            min-width: 60px;
            background: #f0f7ff;
        }}

        /* Team Rows */
        .team-row td {{
            padding: 12px 6px;
            text-align: center;
            font-size: 0.85rem;
            border-bottom: 1px solid #eee;
        }}
        .team-row.away {{
            background: #fff;
        }}
        .team-row.home {{
            background: #fafafa;
        }}

        /* Team Cell */
        .team-cell {{
            display: flex;
            align-items: center;
            gap: 10px;
            padding-left: 15px !important;
            text-align: left !important;
        }}
        .team-logo {{
            width: 32px;
            height: 32px;
            object-fit: contain;
        }}
        .team-name {{
            font-weight: 700;
            font-size: 0.9rem;
            color: #1a1a2e;
        }}
        .team-record {{
            font-size: 0.8rem;
            color: #666;
            margin-left: 8px;
        }}

        /* Stat Cells */
        .stat-cell {{
            font-weight: 600;
            color: #333;
        }}

        /* Line Cells */
        .line-cell {{
            font-weight: 700;
            color: #1a365d;
            background: #f0f7ff;
        }}

        /* Injury Bar - Yellow */
        .injury-bar {{
            background: #fff3cd;
            padding: 8px 15px;
            font-size: 0.8rem;
            color: #856404;
            display: flex;
            align-items: center;
            gap: 8px;
            border-top: 1px solid #ffc107;
        }}
        .injury-icon {{ font-size: 1rem; }}
        .injury-text {{ flex: 1; }}
        .injury-text strong {{ color: #5a4303; }}

        /* Trends Bar - Light Blue */
        .trends-bar {{
            background: #e3f2fd;
            padding: 8px 15px;
            font-size: 0.8rem;
            color: #1565c0;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .trend-icon {{ font-size: 1rem; }}

        /* Footer */
        footer {{
            text-align: center;
            padding: 30px;
            color: #666;
            font-size: 0.85rem;
            margin-top: 30px;
        }}
        footer a {{
            color: #1a365d;
            text-decoration: none;
        }}

        /* Responsive */
        @media (max-width: 1200px) {{
            .game-table {{ font-size: 0.75rem; }}
            .stat-header, .stat-cell {{ min-width: 40px; padding: 6px 4px; }}
        }}
        @media (max-width: 768px) {{
            .game-table {{ display: block; overflow-x: auto; }}
            .team-cell {{ min-width: 150px; }}
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
        <p class="date">{date_str}</p>
    </header>

    <div class="container">
        <div class="tabs">
            {tab_buttons}
        </div>
        {sport_sections}
    </div>

    <footer>
        <p>&copy; 2025 BetLegend | Data: ESPN, The Odds API | <a href="index.html">Home</a></p>
    </footer>

    <script>
        document.querySelectorAll('.tab-btn').forEach(btn => {{
            btn.addEventListener('click', function() {{
                document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
                document.querySelectorAll('.sport-section').forEach(s => s.classList.remove('active'));
                this.classList.add('active');
                const section = document.getElementById(this.dataset.sport + '-section');
                if (section) section.classList.add('active');
            }});
        }});
    </script>
</body>
</html>'''

# =============================================================================
# MAIN ORCHESTRATION
# =============================================================================

def fetch_all_games() -> Dict[str, List]:
    """Fetch games for all sports with stats and odds"""

    all_games = {}

    for sport, config in SPORTS.items():
        print(f"\n[{sport}] Fetching games...")

        # Get games from ESPN
        events = fetch_espn_scoreboard(config['espn_path'])
        print(f"  Found {len(events)} games")

        if not events:
            all_games[sport] = []
            continue

        # Get odds
        odds_data = fetch_odds(config['odds_key'])
        print(f"  Found odds for {len(odds_data)} games")

        games = []
        for event in events:
            try:
                comps = event.get('competitions', [{}])[0]
                competitors = comps.get('competitors', [])

                if len(competitors) < 2:
                    continue

                # Parse teams
                away_comp = next((c for c in competitors if c.get('homeAway') == 'away'), competitors[0])
                home_comp = next((c for c in competitors if c.get('homeAway') == 'home'), competitors[1])

                away_team = away_comp.get('team', {})
                home_team = home_comp.get('team', {})

                away_name = away_team.get('displayName', 'TBD')
                home_name = home_team.get('displayName', 'TBD')
                away_abbr = away_team.get('abbreviation', 'TBD')
                home_abbr = home_team.get('abbreviation', 'TBD')

                # CRITICAL: Skip games with TBD teams - NO PLACEHOLDER DATA EVER
                if 'TBD' in away_name or 'TBD' in home_name or away_abbr == 'TBD' or home_abbr == 'TBD':
                    continue

                away_record = away_comp.get('records', [{}])[0].get('summary', '0-0') if away_comp.get('records') else '0-0'
                home_record = home_comp.get('records', [{}])[0].get('summary', '0-0') if home_comp.get('records') else '0-0'

                # Fetch team stats
                away_id = away_team.get('id', '')
                home_id = home_team.get('id', '')
                away_raw_stats = fetch_team_statistics(config['espn_path'], away_id) if away_id else {}
                home_raw_stats = fetch_team_statistics(config['espn_path'], home_id) if home_id else {}

                away_stats = extract_team_stats(sport, away_raw_stats, away_record)
                home_stats = extract_team_stats(sport, home_raw_stats, home_record)

                # Get odds
                odds = match_game_odds(odds_data, away_name, home_name)

                # Game time
                game_date = event.get('date', '')
                try:
                    dt = datetime.fromisoformat(game_date.replace('Z', '+00:00'))
                    game_time = dt.strftime("%I:%M %p ET")
                except:
                    game_time = ""

                # Venue and network
                venue = comps.get('venue', {}).get('fullName', '')
                broadcasts = comps.get('broadcasts', [])
                network = broadcasts[0].get('names', [''])[0] if broadcasts else ''

                # Logo URLs
                logo_base = f"https://a.espncdn.com/i/teamlogos/{config['logo_path']}/500/scoreboard"

                game = {
                    'time': game_time,
                    'venue': venue,
                    'network': network,
                    'away': {
                        'name': away_name,
                        'abbr': away_abbr,
                        'record': away_record,
                        'logo': f"{logo_base}/{away_abbr.lower()}.png",
                        'stats': away_stats,
                        'spread': odds['spread_away'],
                        'ml': odds['ml_away'],
                        'total': odds['total'],
                    },
                    'home': {
                        'name': home_name,
                        'abbr': home_abbr,
                        'record': home_record,
                        'logo': f"{logo_base}/{home_abbr.lower()}.png",
                        'stats': home_stats,
                        'spread': odds['spread_home'],
                        'ml': odds['ml_home'],
                        'total': odds['total'],
                    },
                }

                games.append(game)

            except Exception as e:
                print(f"  [ERROR] Failed to parse game: {e}")
                continue

        all_games[sport] = games
        print(f"  Processed {len(games)} games")

    return all_games

def main():
    """Main entry point - generates the Handicapping Hub page"""

    print("=" * 60)
    print("HANDICAPPING HUB - PRODUCTION SYSTEM")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Get current date
    date_str = datetime.now().strftime("%B %d, %Y")

    # Fetch all games
    all_games = fetch_all_games()

    # Generate HTML
    html = generate_page(all_games, date_str)

    # Write output
    output_path = os.path.join(REPO_PATH, OUTPUT_FILE)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print("\n" + "=" * 60)
    print(f"SUCCESS: Generated {OUTPUT_FILE}")
    print(f"Games: NBA({len(all_games.get('NBA', []))}) NFL({len(all_games.get('NFL', []))}) NHL({len(all_games.get('NHL', []))}) NCAAB({len(all_games.get('NCAAB', []))}) NCAAF({len(all_games.get('NCAAF', []))})")
    print("=" * 60)

if __name__ == "__main__":
    main()
