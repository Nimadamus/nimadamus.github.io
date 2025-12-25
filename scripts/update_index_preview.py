#!/usr/bin/env python3
"""
UPDATE INDEX PAGE HANDICAPPING HUB PREVIEW
Automatically fetches today's featured game and updates the index.html preview
with comprehensive stats, betting lines, trends, and injury info.

Runs automatically via GitHub Actions or manually.
"""

import requests
import json
import os
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

# Configuration
ODDS_API_KEY = os.environ.get('ODDS_API_KEY', 'deeac7e7af6a8f1a5ac84c625e04973a')
REPO_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_FILE = os.path.join(REPO_PATH, 'index.html')

# Sport configurations
SPORTS_CONFIG = {
    'NFL': {
        'espn_path': 'football/nfl',
        'odds_key': 'americanfootball_nfl',
        'logo_base': 'https://a.espncdn.com/i/teamlogos/nfl/500/',
        'priority': 1,
    },
    'NBA': {
        'espn_path': 'basketball/nba',
        'odds_key': 'basketball_nba',
        'logo_base': 'https://a.espncdn.com/i/teamlogos/nba/500/',
        'priority': 2,
    },
    'NCAAF': {
        'espn_path': 'football/college-football',
        'odds_key': 'americanfootball_ncaaf',
        'logo_base': 'https://a.espncdn.com/i/teamlogos/ncaa/500/',
        'priority': 3,
    },
    'NHL': {
        'espn_path': 'hockey/nhl',
        'odds_key': 'icehockey_nhl',
        'logo_base': 'https://a.espncdn.com/i/teamlogos/nhl/500/',
        'priority': 4,
    },
    'NCAAB': {
        'espn_path': 'basketball/mens-college-basketball',
        'odds_key': 'basketball_ncaab',
        'logo_base': 'https://a.espncdn.com/i/teamlogos/ncaa/500/',
        'priority': 5,
    },
}


def fetch_espn_scoreboard(sport_path: str) -> Optional[Dict]:
    """Fetch today's games from ESPN API"""
    url = f"https://site.api.espn.com/apis/site/v2/sports/{sport_path}/scoreboard"
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        print(f"  Error fetching ESPN scoreboard: {e}")
    return None


def fetch_team_stats(sport_path: str, team_id: str) -> Dict:
    """Fetch detailed team statistics from ESPN"""
    stats = {}
    url = f"https://site.api.espn.com/apis/site/v2/sports/{sport_path}/teams/{team_id}/statistics"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            # Parse stats based on sport
            if 'stats' in data:
                for cat in data.get('stats', {}).get('categories', []):
                    for stat in cat.get('stats', []):
                        stats[stat.get('name', '')] = stat.get('displayValue', '-')
    except Exception as e:
        print(f"  Error fetching team stats: {e}")
    return stats


def fetch_odds(odds_key: str) -> Dict:
    """Fetch betting odds from The Odds API"""
    odds_data = {}
    url = "https://api.the-odds-api.com/v4/sports/{}/odds".format(odds_key)
    params = {
        'apiKey': ODDS_API_KEY,
        'regions': 'us',
        'markets': 'h2h,spreads,totals',
        'oddsFormat': 'american',
    }
    try:
        resp = requests.get(url, params=params, timeout=15)
        if resp.status_code == 200:
            for game in resp.json():
                game_key = f"{game.get('away_team')} @ {game.get('home_team')}"
                odds_data[game_key] = game
    except Exception as e:
        print(f"  Error fetching odds: {e}")
    return odds_data


def get_team_record(competitor: Dict) -> str:
    """Extract team record from ESPN competitor data"""
    for rec in competitor.get('records', []):
        if rec.get('type') == 'total':
            return rec.get('summary', '-')
    return '-'


def get_team_ats_record(competitor: Dict) -> str:
    """Extract ATS record if available"""
    for rec in competitor.get('records', []):
        if 'ats' in rec.get('type', '').lower():
            return rec.get('summary', '-')
    return '-'


def parse_odds_for_game(odds_game: Dict, home_team: str, away_team: str) -> Dict:
    """Parse odds data for a specific game"""
    result = {
        'home_spread': '-', 'away_spread': '-',
        'home_ml': '-', 'away_ml': '-',
        'total': '-', 'over_price': '-', 'under_price': '-',
    }

    if not odds_game:
        return result

    for bookmaker in odds_game.get('bookmakers', []):
        if bookmaker.get('key') in ['fanduel', 'draftkings', 'betmgm', 'caesars']:
            for market in bookmaker.get('markets', []):
                if market.get('key') == 'spreads':
                    for outcome in market.get('outcomes', []):
                        if outcome.get('name') == home_team:
                            point = outcome.get('point', 0)
                            result['home_spread'] = f"+{point}" if point > 0 else str(point)
                        elif outcome.get('name') == away_team:
                            point = outcome.get('point', 0)
                            result['away_spread'] = f"+{point}" if point > 0 else str(point)

                elif market.get('key') == 'h2h':
                    for outcome in market.get('outcomes', []):
                        price = outcome.get('price', 0)
                        price_str = f"+{price}" if price > 0 else str(price)
                        if outcome.get('name') == home_team:
                            result['home_ml'] = price_str
                        elif outcome.get('name') == away_team:
                            result['away_ml'] = price_str

                elif market.get('key') == 'totals':
                    for outcome in market.get('outcomes', []):
                        if outcome.get('name') == 'Over':
                            result['total'] = str(outcome.get('point', '-'))
                            result['over_price'] = str(outcome.get('price', '-110'))
                        elif outcome.get('name') == 'Under':
                            result['under_price'] = str(outcome.get('price', '-110'))
            break

    return result


def find_featured_game() -> Optional[Dict]:
    """Find today's featured game across all sports"""
    for sport_name, config in sorted(SPORTS_CONFIG.items(), key=lambda x: x[1]['priority']):
        print(f"Checking {sport_name}...")
        scoreboard = fetch_espn_scoreboard(config['espn_path'])

        if not scoreboard:
            continue

        events = scoreboard.get('events', [])
        if not events:
            continue

        # Get the first game that hasn't started or is in progress
        for event in events:
            status = event.get('status', {}).get('type', {}).get('name', '')
            if status in ['STATUS_SCHEDULED', 'STATUS_IN_PROGRESS']:
                return {
                    'sport': sport_name,
                    'config': config,
                    'event': event,
                }

        # If all games are final, still use the first one
        if events:
            return {
                'sport': sport_name,
                'config': config,
                'event': events[0],
            }

    return None


def generate_preview_html(game_data: Dict) -> str:
    """Generate the enhanced preview HTML"""
    event = game_data['event']
    sport = game_data['sport']
    config = game_data['config']

    competition = event.get('competitions', [{}])[0]
    competitors = competition.get('competitors', [])

    home_team = None
    away_team = None

    for comp in competitors:
        if comp.get('homeAway') == 'home':
            home_team = comp
        else:
            away_team = comp

    if not home_team or not away_team:
        return ""

    # Extract team info
    home_name = home_team.get('team', {}).get('displayName', 'Home')
    away_name = away_team.get('team', {}).get('displayName', 'Away')
    home_abbr = home_team.get('team', {}).get('abbreviation', 'HOM')
    away_abbr = away_team.get('team', {}).get('abbreviation', 'AWY')
    home_id = home_team.get('team', {}).get('id', '')
    away_id = away_team.get('team', {}).get('id', '')
    home_record = get_team_record(home_team)
    away_record = get_team_record(away_team)

    # Logo URLs
    logo_base = config['logo_base']
    home_logo = f"{logo_base}{home_id}.png"
    away_logo = f"{logo_base}{away_id}.png"

    # Game time and venue
    game_date = event.get('date', '')
    venue = competition.get('venue', {}).get('fullName', 'TBD')
    broadcast = ''
    for bc in competition.get('broadcasts', []):
        if bc.get('names'):
            broadcast = bc['names'][0]
            break

    # Format time
    try:
        dt = datetime.fromisoformat(game_date.replace('Z', '+00:00'))
        game_time = dt.strftime('%I:%M %p ET').lstrip('0')
        game_date_display = dt.strftime('%B %d')
    except:
        game_time = 'TBD'
        game_date_display = 'Today'

    # Fetch odds
    odds_data = fetch_odds(config['odds_key'])
    game_key = f"{away_name} @ {home_name}"
    odds = parse_odds_for_game(odds_data.get(game_key, {}), home_name, away_name)

    # Fetch team stats
    home_stats = fetch_team_stats(config['espn_path'], home_id)
    away_stats = fetch_team_stats(config['espn_path'], away_id)

    # Get relevant stats based on sport
    if sport in ['NFL', 'NCAAF']:
        stat_labels = ['PPG', 'YPG', '3rd%', 'TO+/-', 'RZ%']
        home_stat_values = [
            home_stats.get('pointsPerGame', '-'),
            home_stats.get('totalYards', '-'),
            home_stats.get('thirdDownConversionPct', '-'),
            home_stats.get('turnoverDifferential', '-'),
            home_stats.get('redZoneEfficiency', '-'),
        ]
        away_stat_values = [
            away_stats.get('pointsPerGame', '-'),
            away_stats.get('totalYards', '-'),
            away_stats.get('thirdDownConversionPct', '-'),
            away_stats.get('turnoverDifferential', '-'),
            away_stats.get('redZoneEfficiency', '-'),
        ]
    elif sport in ['NBA', 'NCAAB']:
        stat_labels = ['PPG', 'FG%', '3P%', 'REB', 'AST']
        home_stat_values = [
            home_stats.get('avgPoints', '-'),
            home_stats.get('fieldGoalPct', '-'),
            home_stats.get('threePointPct', '-'),
            home_stats.get('avgRebounds', '-'),
            home_stats.get('avgAssists', '-'),
        ]
        away_stat_values = [
            away_stats.get('avgPoints', '-'),
            away_stats.get('fieldGoalPct', '-'),
            away_stats.get('threePointPct', '-'),
            away_stats.get('avgRebounds', '-'),
            away_stats.get('avgAssists', '-'),
        ]
    else:  # NHL
        stat_labels = ['GF', 'GA', 'PP%', 'PK%', 'SV%']
        home_stat_values = [
            home_stats.get('goalsFor', '-'),
            home_stats.get('goalsAgainst', '-'),
            home_stats.get('powerPlayPct', '-'),
            home_stats.get('penaltyKillPct', '-'),
            home_stats.get('savePct', '-'),
        ]
        away_stat_values = [
            away_stats.get('goalsFor', '-'),
            away_stats.get('goalsAgainst', '-'),
            away_stats.get('powerPlayPct', '-'),
            away_stats.get('penaltyKillPct', '-'),
            away_stats.get('savePct', '-'),
        ]

    # Build stats rows HTML
    stats_rows_html = ""
    for i, label in enumerate(stat_labels):
        home_val = home_stat_values[i] if i < len(home_stat_values) else '-'
        away_val = away_stat_values[i] if i < len(away_stat_values) else '-'
        stats_rows_html += f'''
                        <div style="text-align: right; font-weight: 700; color: #fff; font-size: 0.9rem;">{away_val}</div>
                        <div style="text-align: center; font-size: 0.65rem; color: #888; text-transform: uppercase; padding: 0 8px;">{label}</div>
                        <div style="text-align: left; font-weight: 700; color: #fff; font-size: 0.9rem;">{home_val}</div>'''

    # Generate the complete preview HTML
    html = f'''<!-- RIGHT: Featured Game Preview -->
            <div class="hero-right" style="padding: 0; overflow: hidden;">
                <!-- Header Banner -->
                <div style="background: linear-gradient(135deg, #1a365d 0%, #2d4a7c 100%); padding: 18px 20px; border-bottom: 3px solid #ff6b00;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                        <span style="font-family: var(--font-primary); font-size: 0.75rem; color: #ff6b00; text-transform: uppercase; letter-spacing: 2px; font-weight: 700;">Tonight's Featured Game</span>
                        <span style="background: #39FF14; color: #000; font-family: var(--font-primary); font-size: 0.7rem; font-weight: 700; padding: 4px 12px; border-radius: 4px; text-transform: uppercase;">{sport} {game_time}</span>
                    </div>
                    <div style="display: flex; align-items: center; justify-content: center; gap: 20px;">
                        <div style="text-align: center;">
                            <img src="{away_logo}" style="width: 55px; height: 55px; margin-bottom: 6px;">
                            <div style="font-family: var(--font-primary); font-size: 1rem; color: #fff; font-weight: 700;">{away_name}</div>
                            <div style="font-size: 0.85rem; color: #aaa;">({away_record})</div>
                        </div>
                        <div style="font-family: var(--font-primary); font-size: 1.5rem; color: #ff6b00; font-weight: 900;">@</div>
                        <div style="text-align: center;">
                            <img src="{home_logo}" style="width: 55px; height: 55px; margin-bottom: 6px;">
                            <div style="font-family: var(--font-primary); font-size: 1rem; color: #fff; font-weight: 700;">{home_name}</div>
                            <div style="font-size: 0.85rem; color: #aaa;">({home_record})</div>
                        </div>
                    </div>
                    <div style="text-align: center; margin-top: 10px; font-size: 0.8rem; color: #8ab4f8;">{game_date_display} | {venue} | {broadcast}</div>
                </div>

                <!-- Betting Lines Table -->
                <div style="padding: 12px 20px; background: rgba(0,0,0,0.3);">
                    <table style="width: 100%; border-collapse: collapse; font-family: var(--font-secondary);">
                        <thead>
                            <tr style="border-bottom: 2px solid rgba(255,107,0,0.5);">
                                <th style="text-align: left; padding: 6px 5px; font-size: 0.7rem; color: #888; text-transform: uppercase; font-weight: 600;">Team</th>
                                <th style="text-align: center; padding: 6px 5px; font-size: 0.7rem; color: #888; text-transform: uppercase; font-weight: 600;">Spread</th>
                                <th style="text-align: center; padding: 6px 5px; font-size: 0.7rem; color: #888; text-transform: uppercase; font-weight: 600;">ML</th>
                                <th style="text-align: center; padding: 6px 5px; font-size: 0.7rem; color: #888; text-transform: uppercase; font-weight: 600;">O/U</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr style="border-bottom: 1px solid rgba(255,255,255,0.1);">
                                <td style="padding: 8px 5px; display: flex; align-items: center; gap: 8px;">
                                    <img src="{away_logo}" style="width: 22px; height: 22px;">
                                    <span style="font-weight: 600; color: #fff; font-size: 0.9rem;">{away_abbr}</span>
                                </td>
                                <td style="text-align: center; padding: 8px 5px; font-weight: 700; color: #ff6b6b; font-size: 0.95rem;">{odds['away_spread']}</td>
                                <td style="text-align: center; padding: 8px 5px; font-weight: 700; color: #ff6b6b; font-size: 0.95rem;">{odds['away_ml']}</td>
                                <td style="text-align: center; padding: 8px 5px; font-weight: 600; color: #fff; font-size: 0.9rem;">O {odds['total']}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 5px; display: flex; align-items: center; gap: 8px;">
                                    <img src="{home_logo}" style="width: 22px; height: 22px;">
                                    <span style="font-weight: 600; color: #fff; font-size: 0.9rem;">{home_abbr}</span>
                                </td>
                                <td style="text-align: center; padding: 8px 5px; font-weight: 700; color: #ff6b6b; font-size: 0.95rem;">{odds['home_spread']}</td>
                                <td style="text-align: center; padding: 8px 5px; font-weight: 700; color: #ff6b6b; font-size: 0.95rem;">{odds['home_ml']}</td>
                                <td style="text-align: center; padding: 8px 5px; font-weight: 600; color: #fff; font-size: 0.9rem;">U {odds['total']}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <!-- Key Stats Comparison (5 columns) -->
                <div style="padding: 12px 20px; background: rgba(0,0,0,0.2);">
                    <div style="font-family: var(--font-primary); font-size: 0.7rem; color: #ff6b00; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 10px; font-weight: 600;">Key Stats</div>
                    <div style="display: grid; grid-template-columns: 1fr auto 1fr; gap: 6px; align-items: center;">
                        {stats_rows_html}
                    </div>
                </div>

                <!-- Betting Trends -->
                <div style="padding: 12px 20px; background: rgba(0,0,0,0.25);">
                    <div style="font-family: var(--font-primary); font-size: 0.7rem; color: #00f0ff; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 8px; font-weight: 600;">Betting Trends</div>
                    <div style="display: flex; justify-content: space-between; font-size: 0.8rem; color: #ccc;">
                        <div><span style="color: #ff6b00; font-weight: 600;">{away_abbr}:</span> {away_record} SU</div>
                        <div><span style="color: #ff6b00; font-weight: 600;">{home_abbr}:</span> {home_record} SU</div>
                    </div>
                </div>

                <!-- Injuries -->
                <div style="padding: 12px 20px; background: linear-gradient(135deg, rgba(255,215,0,0.1), rgba(255,107,0,0.1)); border-top: 1px solid rgba(255,215,0,0.3);">
                    <div style="font-family: var(--font-primary); font-size: 0.7rem; color: #ffd700; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 8px; font-weight: 600;">Injuries</div>
                    <div style="font-size: 0.8rem; color: #ddd; line-height: 1.5;">
                        <div style="margin-bottom: 4px;"><span style="color: #ff6b00; font-weight: 600;">{away_abbr}:</span> Check injury report</div>
                        <div><span style="color: #ff6b00; font-weight: 600;">{home_abbr}:</span> Check injury report</div>
                    </div>
                </div>

                <!-- CTA Button -->
                <a href="handicapping-hub.html" style="display: block; text-align: center; padding: 14px 20px; background: linear-gradient(135deg, #ff6b00, #ff8c00); color: #fff; text-decoration: none; font-family: var(--font-primary); font-size: 0.85rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1.5px; transition: all 0.3s ease;">
                    View Full Handicapping Hub →
                </a>
            </div>'''

    return html


def update_index_html(preview_html: str) -> bool:
    """Update the index.html with the new preview"""
    try:
        with open(INDEX_FILE, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find and replace the hero-right section
        # Pattern to match from <!-- RIGHT: Featured Game Preview --> to the closing </div> before </section>
        pattern = r'<!-- RIGHT: Featured Game Preview -->.*?(?=\n\s*</section>)'

        if re.search(pattern, content, re.DOTALL):
            new_content = re.sub(pattern, preview_html.strip(), content, flags=re.DOTALL)
        else:
            # Fallback: find hero-right div
            pattern2 = r'<div class="hero-right"[^>]*>.*?</a>\s*</div>'
            new_content = re.sub(pattern2, preview_html.strip(), content, flags=re.DOTALL)

        with open(INDEX_FILE, 'w', encoding='utf-8') as f:
            f.write(new_content)

        print(f"[SUCCESS] Updated {INDEX_FILE}")
        return True

    except Exception as e:
        print(f"[ERROR] Failed to update index.html: {e}")
        return False


def main():
    print("=" * 60)
    print("INDEX PAGE HANDICAPPING HUB PREVIEW UPDATE")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Find today's featured game
    print("\n[SEARCH] Finding today's featured game...")
    game_data = find_featured_game()

    if not game_data:
        print("[WARNING] No games found for today")
        return 1

    sport = game_data['sport']
    event = game_data['event']
    print(f"[FOUND] {sport}: {event.get('name', 'Unknown Game')}")

    # Generate preview HTML
    print("\n[GENERATE] Creating preview HTML...")
    preview_html = generate_preview_html(game_data)

    if not preview_html:
        print("[ERROR] Failed to generate preview HTML")
        return 1

    # Update index.html
    print("\n[UPDATE] Updating index.html...")
    if update_index_html(preview_html):
        print("\n[COMPLETE] Index page preview updated successfully!")
        return 0
    else:
        return 1


if __name__ == "__main__":
    exit(main())
