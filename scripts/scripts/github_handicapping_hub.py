#!/usr/bin/env python3
"""
BETLEGEND HANDICAPPING HUB UPDATE - GitHub Actions Version
===========================================================
Scrapes ESPN for team stats, injuries, and game schedules.
Optionally uses the-odds-api.com for betting lines.

Runs daily at 8:00 AM PST via GitHub Actions.
"""

import os
import re
import json
from datetime import datetime, timedelta
from collections import defaultdict
import time

import requests
from bs4 import BeautifulSoup

# Configuration
REPO = os.getcwd()
TODAY = datetime.now()
DATE_STR = TODAY.strftime("%Y-%m-%d")
DATE_DISPLAY = TODAY.strftime("%B %d, %Y")
TIME_DISPLAY = TODAY.strftime("%I:%M %p")

# Optional: The Odds API key (set as GitHub secret)
ODDS_API_KEY = os.environ.get('ODDS_API_KEY', '')

# ESPN API endpoints
ESPN_API = {
    'NBA': {
        'scoreboard': 'https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard',
        'teams': 'https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams',
        'injuries': 'https://sports.core.api.espn.com/v2/sports/basketball/leagues/nba/teams/{team_id}/injuries',
    },
    'NHL': {
        'scoreboard': 'https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard',
        'teams': 'https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/teams',
        'injuries': 'https://sports.core.api.espn.com/v2/sports/hockey/leagues/nhl/teams/{team_id}/injuries',
    },
    'NFL': {
        'scoreboard': 'https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard',
        'teams': 'https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams',
        'injuries': 'https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/teams/{team_id}/injuries',
    },
    'NCAAB': {
        'scoreboard': 'https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard?groups=50',
        'teams': 'https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/teams',
    },
    'NCAAF': {
        'scoreboard': 'https://site.api.espn.com/apis/site/v2/sports/football/college-football/scoreboard?groups=80',
        'teams': 'https://site.api.espn.com/apis/site/v2/sports/football/college-football/teams',
    },
}

# Odds API sport keys
ODDS_SPORT_KEYS = {
    'NBA': 'basketball_nba',
    'NHL': 'icehockey_nhl',
    'NFL': 'americanfootball_nfl',
    'NCAAB': 'basketball_ncaab',
    'NCAAF': 'americanfootball_ncaaf',
}


class ESPNScraper:
    """Scrape ESPN for team stats, injuries, and schedules"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        })
        self.team_cache = {}

    def get_todays_games(self, sport):
        """Get today's games for a sport"""
        try:
            url = ESPN_API[sport]['scoreboard']
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            data = response.json()

            games = []
            for event in data.get('events', []):
                competition = event.get('competitions', [{}])[0]
                competitors = competition.get('competitors', [])

                if len(competitors) < 2:
                    continue

                home_team = None
                away_team = None

                for comp in competitors:
                    team_data = {
                        'id': comp.get('team', {}).get('id'),
                        'name': comp.get('team', {}).get('displayName', ''),
                        'abbreviation': comp.get('team', {}).get('abbreviation', ''),
                        'logo': comp.get('team', {}).get('logo', ''),
                        'record': comp.get('records', [{}])[0].get('summary', '') if comp.get('records') else '',
                        'home_record': '',
                        'away_record': '',
                    }

                    # Get home/away records
                    for rec in comp.get('records', []):
                        if rec.get('type') == 'home':
                            team_data['home_record'] = rec.get('summary', '')
                        elif rec.get('type') == 'road':
                            team_data['away_record'] = rec.get('summary', '')

                    if comp.get('homeAway') == 'home':
                        home_team = team_data
                    else:
                        away_team = team_data

                if home_team and away_team:
                    games.append({
                        'id': event.get('id'),
                        'name': event.get('name'),
                        'date': event.get('date'),
                        'status': event.get('status', {}).get('type', {}).get('description', ''),
                        'home': home_team,
                        'away': away_team,
                    })

            print(f"  {sport}: Found {len(games)} games")
            return games

        except Exception as e:
            print(f"  {sport}: Error fetching games - {e}")
            return []

    def get_team_stats(self, sport, team_id):
        """Get team statistics"""
        try:
            if sport in ['NCAAB', 'NCAAF']:
                # College sports use different URL structure
                if sport == 'NCAAB':
                    url = f'https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/teams/{team_id}/statistics'
                else:
                    url = f'https://site.api.espn.com/apis/site/v2/sports/football/college-football/teams/{team_id}/statistics'
            else:
                url = f'https://site.api.espn.com/apis/site/v2/sports/{self._get_sport_path(sport)}/teams/{team_id}/statistics'

            response = self.session.get(url, timeout=15)
            if response.status_code != 200:
                return self._get_default_stats(sport)

            data = response.json()
            stats = {}

            for stat_group in data.get('splits', {}).get('categories', []):
                for stat in stat_group.get('stats', []):
                    stats[stat.get('name', '')] = stat.get('displayValue', stat.get('value', ''))

            return stats

        except Exception as e:
            return self._get_default_stats(sport)

    def get_team_injuries(self, sport, team_id):
        """Get team injury report"""
        try:
            if sport in ['NCAAB', 'NCAAF']:
                return []  # College sports don't have injury data in ESPN API

            url = ESPN_API[sport]['injuries'].format(team_id=team_id)
            response = self.session.get(url, timeout=15)
            if response.status_code != 200:
                return []

            data = response.json()
            injuries = []

            for item in data.get('items', []):
                try:
                    # Fetch player details
                    player_ref = item.get('athlete', {}).get('$ref', '')
                    if player_ref:
                        player_resp = self.session.get(player_ref, timeout=10)
                        if player_resp.status_code == 200:
                            player_data = player_resp.json()

                            injuries.append({
                                'name': player_data.get('displayName', 'Unknown'),
                                'position': player_data.get('position', {}).get('abbreviation', ''),
                                'injury': item.get('type', {}).get('description', item.get('details', {}).get('type', 'Unknown')),
                                'status': item.get('status', 'Unknown'),
                            })
                except:
                    continue

            return injuries[:8]  # Limit to 8 injuries per team

        except Exception as e:
            return []

    def _get_sport_path(self, sport):
        """Get ESPN API sport path"""
        paths = {
            'NBA': 'basketball/nba',
            'NHL': 'hockey/nhl',
            'NFL': 'football/nfl',
        }
        return paths.get(sport, 'basketball/nba')

    def _get_default_stats(self, sport):
        """Return default stats structure"""
        if sport in ['NBA', 'NCAAB']:
            return {
                'avgPoints': 'N/A',
                'avgFieldGoalPct': 'N/A',
                'avgThreePointPct': 'N/A',
                'avgFreeThrowPct': 'N/A',
                'avgRebounds': 'N/A',
                'avgAssists': 'N/A',
                'avgSteals': 'N/A',
                'avgBlocks': 'N/A',
            }
        elif sport == 'NHL':
            return {
                'goalsFor': 'N/A',
                'goalsAgainst': 'N/A',
                'powerPlayPct': 'N/A',
                'penaltyKillPct': 'N/A',
            }
        else:
            return {}


class OddsAPIClient:
    """Get betting odds from the-odds-api.com"""

    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = 'https://api.the-odds-api.com/v4/sports'

    def get_odds(self, sport):
        """Get odds for a sport"""
        if not self.api_key:
            return {}

        try:
            sport_key = ODDS_SPORT_KEYS.get(sport)
            if not sport_key:
                return {}

            url = f'{self.base_url}/{sport_key}/odds'
            params = {
                'apiKey': self.api_key,
                'regions': 'us',
                'markets': 'spreads,totals,h2h',
                'oddsFormat': 'american',
            }

            response = requests.get(url, params=params, timeout=15)
            if response.status_code != 200:
                return {}

            data = response.json()
            odds_by_game = {}

            for game in data:
                home_team = game.get('home_team', '')
                away_team = game.get('away_team', '')
                key = f"{away_team} @ {home_team}"

                odds_data = {
                    'spread_home': None,
                    'spread_away': None,
                    'total': None,
                    'ml_home': None,
                    'ml_away': None,
                }

                for bookmaker in game.get('bookmakers', []):
                    for market in bookmaker.get('markets', []):
                        if market.get('key') == 'spreads':
                            for outcome in market.get('outcomes', []):
                                if outcome.get('name') == home_team:
                                    odds_data['spread_home'] = outcome.get('point')
                                elif outcome.get('name') == away_team:
                                    odds_data['spread_away'] = outcome.get('point')
                        elif market.get('key') == 'totals':
                            for outcome in market.get('outcomes', []):
                                if outcome.get('name') == 'Over':
                                    odds_data['total'] = outcome.get('point')
                        elif market.get('key') == 'h2h':
                            for outcome in market.get('outcomes', []):
                                if outcome.get('name') == home_team:
                                    odds_data['ml_home'] = outcome.get('price')
                                elif outcome.get('name') == away_team:
                                    odds_data['ml_away'] = outcome.get('price')
                    break  # Only use first bookmaker

                odds_by_game[key] = odds_data

            return odds_by_game

        except Exception as e:
            print(f"  Error fetching odds for {sport}: {e}")
            return {}


def get_injury_status_class(status):
    """Get CSS class for injury status"""
    status_lower = status.lower()
    if 'out' in status_lower:
        return 'out'
    elif 'doubtful' in status_lower:
        return 'doubtful'
    elif 'questionable' in status_lower:
        return 'questionable'
    elif 'day' in status_lower:
        return 'day-to-day'
    elif 'probable' in status_lower:
        return 'probable'
    return 'questionable'


def generate_game_card_html(game, sport, away_stats, home_stats, away_injuries, home_injuries, odds=None):
    """Generate HTML for a single game card"""

    away = game['away']
    home = game['home']

    # Default odds display
    spread_home = odds.get('spread_home', 'N/A') if odds else 'N/A'
    spread_away = odds.get('spread_away', 'N/A') if odds else 'N/A'
    total = odds.get('total', 'N/A') if odds else 'N/A'
    ml_home = odds.get('ml_home', 'N/A') if odds else 'N/A'
    ml_away = odds.get('ml_away', 'N/A') if odds else 'N/A'

    # Format spread display
    if spread_home and spread_home != 'N/A':
        spread_home = f"+{spread_home}" if spread_home > 0 else str(spread_home)
    if spread_away and spread_away != 'N/A':
        spread_away = f"+{spread_away}" if spread_away > 0 else str(spread_away)
    if ml_home and ml_home != 'N/A':
        ml_home = f"+{ml_home}" if ml_home > 0 else str(ml_home)
    if ml_away and ml_away != 'N/A':
        ml_away = f"+{ml_away}" if ml_away > 0 else str(ml_away)

    # Generate injury HTML
    def generate_injury_list(injuries, team_name):
        if not injuries:
            return f'<span class="no-injuries">No injuries reported</span>'

        html = '<ul class="injury-list">'
        for inj in injuries[:5]:
            status_class = get_injury_status_class(inj.get('status', ''))
            html += f'''
                <li>
                    <div class="player-info">
                        <span class="player-name">{inj['name']} ({inj.get('position', 'N/A')})</span>
                        <span class="injury-type">{inj.get('injury', 'Unknown')}</span>
                    </div>
                    <span class="status {status_class}">{inj.get('status', 'Unknown')}</span>
                </li>'''
        html += '</ul>'
        return html

    # Generate stats HTML based on sport
    def generate_stats_html(stats, sport):
        if sport in ['NBA', 'NCAAB']:
            return f'''
                <div class="stats-column">
                    <div class="stats-column-title">Offensive</div>
                    <div class="stat-item"><span class="label">PPG</span><span class="value">{stats.get('avgPoints', 'N/A')}</span></div>
                    <div class="stat-item"><span class="label">FG%</span><span class="value">{stats.get('avgFieldGoalPct', 'N/A')}</span></div>
                    <div class="stat-item"><span class="label">3PT%</span><span class="value">{stats.get('avgThreePointPct', 'N/A')}</span></div>
                    <div class="stat-item"><span class="label">FT%</span><span class="value">{stats.get('avgFreeThrowPct', 'N/A')}</span></div>
                    <div class="stat-item"><span class="label">RPG</span><span class="value">{stats.get('avgRebounds', 'N/A')}</span></div>
                    <div class="stat-item"><span class="label">APG</span><span class="value">{stats.get('avgAssists', 'N/A')}</span></div>
                </div>
                <div class="stats-column">
                    <div class="stats-column-title">Defensive</div>
                    <div class="stat-item"><span class="label">STL/G</span><span class="value">{stats.get('avgSteals', 'N/A')}</span></div>
                    <div class="stat-item"><span class="label">BLK/G</span><span class="value">{stats.get('avgBlocks', 'N/A')}</span></div>
                    <div class="stat-item"><span class="label">TO/G</span><span class="value">{stats.get('avgTurnovers', 'N/A')}</span></div>
                </div>'''
        elif sport == 'NHL':
            return f'''
                <div class="stats-column">
                    <div class="stats-column-title">Offensive</div>
                    <div class="stat-item"><span class="label">GF/G</span><span class="value">{stats.get('goalsFor', 'N/A')}</span></div>
                    <div class="stat-item"><span class="label">PP%</span><span class="value">{stats.get('powerPlayPct', 'N/A')}</span></div>
                    <div class="stat-item"><span class="label">SOG/G</span><span class="value">{stats.get('shotsPerGame', 'N/A')}</span></div>
                </div>
                <div class="stats-column">
                    <div class="stats-column-title">Defensive</div>
                    <div class="stat-item"><span class="label">GA/G</span><span class="value">{stats.get('goalsAgainst', 'N/A')}</span></div>
                    <div class="stat-item"><span class="label">PK%</span><span class="value">{stats.get('penaltyKillPct', 'N/A')}</span></div>
                    <div class="stat-item"><span class="label">SV%</span><span class="value">{stats.get('savePct', 'N/A')}</span></div>
                </div>'''
        else:
            return '<div class="stats-column"><div class="stat-item">Stats not available</div></div>'

    # Get logo URL
    away_logo = away.get('logo', f"https://a.espncdn.com/i/teamlogos/{sport.lower()}/500/scoreboard/{away['abbreviation'].lower()}.png")
    home_logo = home.get('logo', f"https://a.espncdn.com/i/teamlogos/{sport.lower()}/500/scoreboard/{home['abbreviation'].lower()}.png")

    card_html = f'''
            <div class="game-card">
                <div class="matchup-header">
                    <div class="team-box away">
                        <img src="{away_logo}" alt="{away['name']}" class="team-logo" onerror="this.style.display='none'">
                        <div class="team-details">
                            <h3>{away['name']}</h3>
                            <div class="team-records">
                                <span class="overall">{away.get('record', 'N/A')}</span>
                                <br>Away: {away.get('away_record', 'N/A')}
                            </div>
                        </div>
                    </div>
                    <div class="vs-badge">VS</div>
                    <div class="team-box home">
                        <img src="{home_logo}" alt="{home['name']}" class="team-logo" onerror="this.style.display='none'">
                        <div class="team-details">
                            <h3>{home['name']}</h3>
                            <div class="team-records">
                                <span class="overall">{home.get('record', 'N/A')}</span>
                                <br>Home: {home.get('home_record', 'N/A')}
                            </div>
                        </div>
                    </div>
                </div>
                <div class="teams-layout">
                <div class="team-section away" data-team="{away['name']}">
                    <div class="team-section-header">
                        <img src="{away_logo}" alt="{away['name']}" class="team-section-logo" onerror="this.style.display='none'">
                        <div class="team-section-info">
                            <h4>{away['name']}</h4>
                            <div class="record">{away.get('record', 'N/A')}</div>
                        </div>
                    </div>
                    <div class="team-stats-grid">
                        {generate_stats_html(away_stats, sport)}
                    </div>
                </div>
                <div class="team-section home" data-team="{home['name']}">
                    <div class="team-section-header">
                        <img src="{home_logo}" alt="{home['name']}" class="team-section-logo" onerror="this.style.display='none'">
                        <div class="team-section-info">
                            <h4>{home['name']}</h4>
                            <div class="record">{home.get('record', 'N/A')}</div>
                        </div>
                    </div>
                    <div class="team-stats-grid">
                        {generate_stats_html(home_stats, sport)}
                    </div>
                </div>
                <div class="middle-section">
                    <div class="middle-section-title">Injury Report</div>
                    <div class="injury-grid">
                        <div class="injury-column">
                            <h5>{away['name']}</h5>
                            {generate_injury_list(away_injuries, away['name'])}
                        </div>
                        <div class="injury-column">
                            <h5>{home['name']}</h5>
                            {generate_injury_list(home_injuries, home['name'])}
                        </div>
                    </div>
                </div>
                </div>
                <div class="bottom-section">
                    <div class="lines-section" style="grid-column: span 2;">
                        <div class="lines-title">Betting Lines</div>
                        <div class="betting-lines">
                            <div class="line-box">
                                <div class="type">Spread</div>
                                <div class="values">
                                    <span class="value">{away['abbreviation']} {spread_away}</span>
                                    <span class="value">{home['abbreviation']} {spread_home}</span>
                                </div>
                            </div>
                            <div class="line-box">
                                <div class="type">Total</div>
                                <div class="values">
                                    <span class="value">O/U {total}</span>
                                </div>
                            </div>
                            <div class="line-box">
                                <div class="type">Moneyline</div>
                                <div class="values">
                                    <span class="value">{away['abbreviation']} {ml_away}</span>
                                    <span class="value">{home['abbreviation']} {ml_home}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>'''

    return card_html


def update_handicapping_hub(sports_data):
    """Update the handicapping-hub.html file"""
    main_file = os.path.join(REPO, "handicapping-hub.html")

    if not os.path.exists(main_file):
        print(f"  [ERROR] handicapping-hub.html not found")
        return False

    with open(main_file, 'r', encoding='utf-8') as f:
        html = f.read()

    # Update timestamp
    html = re.sub(
        r'Last updated: [^&]+',
        f'Last updated: {DATE_DISPLAY} at {TIME_DISPLAY}',
        html
    )

    # Update tab counts
    for sport, data in sports_data.items():
        game_count = len(data.get('games', []))
        pattern = rf'onclick="showSection\(\'{sport}\'\)">[^<]+</button>'
        replacement = f'onclick="showSection(\'{sport}\')">{sport} ({game_count})</button>'
        html = re.sub(pattern, replacement, html)

    # Generate section content for each sport
    for sport, data in sports_data.items():
        games = data.get('games', [])
        odds_data = data.get('odds', {})

        section_start = html.find(f'id="{sport}"')
        if section_start == -1:
            continue

        # Find the section boundaries
        section_tag_start = html.rfind('<div', 0, section_start)
        next_section = html.find('<div id=', section_start + 10)
        if next_section == -1:
            next_section = html.find('</div>\n    </div>\n\n    <script>', section_start)

        if section_tag_start == -1:
            continue

        # Generate game cards
        game_cards = []
        for game in games:
            away_stats = data.get('stats', {}).get(game['away']['id'], {})
            home_stats = data.get('stats', {}).get(game['home']['id'], {})
            away_injuries = data.get('injuries', {}).get(game['away']['id'], [])
            home_injuries = data.get('injuries', {}).get(game['home']['id'], [])

            # Match odds to game
            game_key = f"{game['away']['name']} @ {game['home']['name']}"
            game_odds = odds_data.get(game_key, {})

            card = generate_game_card_html(
                game, sport,
                away_stats, home_stats,
                away_injuries, home_injuries,
                game_odds
            )
            game_cards.append(card)

        # Create new section content
        active_class = 'active' if sport == 'NBA' else ''
        if games:
            section_content = f'''<div id="{sport}" class="section {active_class}">
            <div class="section-header">
                <h2>{sport} Games</h2><span class="count">{len(games)} games today</span>
            </div>
{''.join(game_cards)}
        </div>'''
        else:
            section_content = f'''<div id="{sport}" class="section {active_class}">
            <div class="section-header">
                <h2>{sport} Games</h2><span class="count">0 games today</span>
            </div>
            <div class="no-games">
                <p>No {sport} games scheduled for today</p>
            </div>
        </div>'''

        # Replace section
        # Find the exact section boundaries
        pattern = rf'<div id="{sport}" class="section[^"]*">[\s\S]*?(?=<div id="|</div>\s*</div>\s*<script>)'
        html = re.sub(pattern, section_content + '\n        ', html, count=1)

    # Save updated file
    with open(main_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"  Updated handicapping-hub.html")

    # Create dated archive
    archive_file = os.path.join(REPO, f"handicapping-hub-{DATE_STR}.html")
    with open(archive_file, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"  Created archive: handicapping-hub-{DATE_STR}.html")

    return True


def main():
    print("=" * 60)
    print("BETLEGEND HANDICAPPING HUB UPDATE")
    print(f"Date: {DATE_DISPLAY}")
    print(f"Running from: {REPO}")
    print("=" * 60)

    espn = ESPNScraper()
    odds_client = OddsAPIClient(ODDS_API_KEY) if ODDS_API_KEY else None

    if ODDS_API_KEY:
        print("\n[INFO] Odds API key found - will fetch betting lines")
    else:
        print("\n[INFO] No Odds API key - betting lines will show N/A")

    sports_data = {}

    # Fetch data for each sport
    for sport in ['NBA', 'NHL', 'NFL', 'NCAAB', 'NCAAF']:
        print(f"\n[{sport}]")

        games = espn.get_todays_games(sport)

        if not games:
            sports_data[sport] = {'games': [], 'stats': {}, 'injuries': {}, 'odds': {}}
            continue

        # Get stats and injuries for each team
        stats = {}
        injuries = {}

        for game in games[:10]:  # Limit to 10 games per sport
            for team_type in ['away', 'home']:
                team = game[team_type]
                team_id = team['id']

                if team_id and team_id not in stats:
                    stats[team_id] = espn.get_team_stats(sport, team_id)
                    if sport not in ['NCAAB', 'NCAAF']:
                        injuries[team_id] = espn.get_team_injuries(sport, team_id)
                    time.sleep(0.2)  # Rate limiting

        # Get odds if API key available
        odds = {}
        if odds_client:
            odds = odds_client.get_odds(sport)
            print(f"    Fetched odds for {len(odds)} games")

        sports_data[sport] = {
            'games': games[:10],
            'stats': stats,
            'injuries': injuries,
            'odds': odds,
        }

    # Update the HTML file
    print("\n[UPDATE]")
    if not update_handicapping_hub(sports_data):
        return 1

    total_games = sum(len(d['games']) for d in sports_data.values())
    print("\n" + "=" * 60)
    print("HANDICAPPING HUB UPDATE COMPLETE!")
    print(f"  - {total_games} total games across all sports")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    exit(main())
