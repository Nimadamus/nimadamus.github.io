#!/usr/bin/env python3
"""
!!! DEPRECATED - DO NOT USE FOR SPORTS PAGES !!!

This script generates game-card format with stats which is WRONG for sports pages.
Sports pages (nba.html, nfl.html, etc.) should have WRITTEN ARTICLES using
the game-preview format, not auto-generated stats.

Use this ONLY for:
- Handicapping Hub updates (which use stats)
- Testing/development

For sports pages, write proper articles manually with game-preview class.

See: html_updater.py generate_game_card_html() for the correct format.
"""
import requests
import json
import random
from datetime import datetime
import os
import sys

ODDS_API_KEY = "deeac7e7af6a8f1a5ac84c625e04973a"
REPO_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SPORT_CONFIG = {
    'NFL': {
        'espn_path': 'football/nfl',
        'odds_key': 'americanfootball_nfl',
        'output': 'nfl.html'
    },
    'NBA': {
        'espn_path': 'basketball/nba',
        'odds_key': 'basketball_nba',
        'output': 'nba.html'
    },
    'NHL': {
        'espn_path': 'hockey/nhl',
        'odds_key': 'icehockey_nhl',
        'output': 'nhl.html'
    },
    'NCAAB': {
        'espn_path': 'basketball/mens-college-basketball',
        'odds_key': 'basketball_ncaab',
        'output': 'ncaab.html'
    },
    'NCAAF': {
        'espn_path': 'football/college-football',
        'odds_key': 'americanfootball_ncaaf',
        'output': 'ncaaf.html'
    }
}

# ============================================
# ANALYSIS GENERATION - Natural Language Articles
# ============================================

OPENINGS = [
    "This one has all the makings of a competitive battle.",
    "Circle this matchup on your calendar.",
    "Here's a game that deserves your attention.",
    "Don't sleep on this one.",
    "This game could be more interesting than the spread suggests.",
    "Let's break down what makes this matchup tick.",
    "Both teams come into this with something to prove.",
    "Two teams heading in different directions meet here.",
    "The numbers tell an interesting story in this one.",
    "Sharp money has been moving on this game, and there's a reason why.",
]

TREND_PHRASES = {
    'hot': ['rolling', 'on fire', 'clicking on all cylinders', 'playing their best ball', 'surging'],
    'cold': ['struggling', 'in a slump', 'searching for answers', 'trying to find their footing', 'ice cold'],
    'mixed': ['inconsistent', 'up and down', 'hard to read', 'unpredictable', 'a mixed bag'],
}

def parse_record(record_str):
    """Parse W-L record string into wins, losses"""
    try:
        parts = record_str.replace(' ', '').split('-')
        return int(parts[0]), int(parts[1])
    except:
        return 0, 0

def get_team_trend(record):
    """Determine team trend based on record"""
    wins, losses = parse_record(record)
    total = wins + losses
    if total == 0:
        return 'mixed'
    pct = wins / total
    if pct >= 0.6:
        return 'hot'
    elif pct <= 0.4:
        return 'cold'
    return 'mixed'

def generate_game_analysis(sport, away_name, home_name, away_record, home_record, odds, venue):
    """Generate human-sounding analysis article for a game"""

    away_trend = get_team_trend(away_record)
    home_trend = get_team_trend(home_record)

    sections = []

    # Opening paragraph
    opening = random.choice(OPENINGS)
    away_desc = random.choice(TREND_PHRASES.get(away_trend, TREND_PHRASES['mixed']))
    home_desc = random.choice(TREND_PHRASES.get(home_trend, TREND_PHRASES['mixed']))

    if away_trend == 'hot' and home_trend == 'cold':
        context = f"The {away_name} come in {away_desc} at {away_record}, while the {home_name} ({home_record}) have been {home_desc}. That disparity in form is the headline here."
    elif home_trend == 'hot' and away_trend == 'cold':
        context = f"Home cooking could be the difference as the {home_name} ({home_record}) have been {home_desc}, facing a {away_name} team ({away_record}) that's been {away_desc} lately."
    elif away_trend == 'hot' and home_trend == 'hot':
        context = f"Both teams enter this one playing well. The {away_name} ({away_record}) take on the {home_name} ({home_record}) in what promises to be a competitive matchup."
    else:
        context = f"The {away_name} ({away_record}) visit the {home_name} ({home_record}) at {venue}."

    sections.append(f'<div class="analysis-section"><h4>The Matchup</h4><p>{opening} {context}</p></div>')

    # Betting lines analysis
    spread = odds.get('spread', '-')
    total = odds.get('total', '-')
    ml_away = odds.get('ml_away', '-')
    ml_home = odds.get('ml_home', '-')

    if spread != '-' and total != '-':
        try:
            spread_val = float(spread.replace('+', ''))
            total_val = float(total)

            if spread_val <= -10:
                line_analysis = f"The {home_name} are heavy favorites laying {abs(spread_val)} points. That's a lot of chalk, but the market clearly expects a blowout."
            elif spread_val >= 10:
                line_analysis = f"The {away_name} are substantial favorites getting {abs(spread_val)} points on the road. That kind of line movement suggests sharp confidence."
            elif abs(spread_val) <= 3:
                line_analysis = f"This is essentially a pick'em with the spread at {spread}. Vegas sees these teams as evenly matched."
            else:
                fav = home_name if spread_val < 0 else away_name
                dog = away_name if spread_val < 0 else home_name
                line_analysis = f"The {fav} are laying {abs(spread_val)} points here. The {dog} will need to keep this close or pull the upset outright."

            total_analysis = f"The total sits at {total}. "
            if total_val > 230 and sport == 'NBA':
                total_analysis += "That's a high number, suggesting an up-tempo game with limited defensive stops."
            elif total_val < 210 and sport == 'NBA':
                total_analysis += "That's a relatively low total, indicating expectations of a defensive battle."
            elif total_val > 48 and sport == 'NFL':
                total_analysis += "Vegas expects points in this one."
            elif total_val < 40 and sport == 'NFL':
                total_analysis += "A low total suggests a grind-it-out affair."
            elif total_val > 6 and sport == 'NHL':
                total_analysis += "That's on the higher side for hockey, pointing to potential offensive fireworks."

            sections.append(f'<div class="analysis-section"><h4>The Lines</h4><p>{line_analysis} {total_analysis}</p></div>')
        except:
            pass

    # Moneyline analysis
    if ml_away != '-' and ml_home != '-':
        try:
            ml_away_val = int(ml_away.replace('+', ''))
            ml_home_val = int(ml_home.replace('+', ''))

            if ml_away_val > 200:
                ml_analysis = f"The {away_name} are substantial underdogs at {ml_away}. There could be value if you believe in an upset."
            elif ml_home_val > 200:
                ml_analysis = f"The {home_name} sit as significant underdogs at {ml_home}. Road favorites this heavy don't always deliver."
            elif abs(ml_away_val) < 130 and abs(ml_home_val) < 130:
                ml_analysis = f"The moneylines ({away_name} {ml_away}, {home_name} {ml_home}) reflect how close this game is expected to be."
            else:
                ml_analysis = f"Moneyline: {away_name} {ml_away}, {home_name} {ml_home}."

            sections.append(f'<div class="analysis-section"><h4>Moneyline Angle</h4><p>{ml_analysis}</p></div>')
        except:
            pass

    # Closing angle
    closers = [
        "Line movement closer to game time could reveal additional value.",
        "This matchup has trap game written all over it - proceed with caution.",
        "Sharp bettors are paying attention to this one for a reason.",
        "The value might not be where the public thinks.",
        "Sometimes the obvious play is the right one. Sometimes it isn't.",
        "This game deserves a deeper look before making any decisions.",
    ]

    sections.append(f'<div class="analysis-section"><h4>The Angle</h4><p>{random.choice(closers)}</p></div>')

    return '\n'.join(sections)

# ============================================
# ESPN & ODDS API FUNCTIONS
# ============================================

def get_espn_scoreboard(sport_path, date_str=None):
    """Get today's games from ESPN"""
    if date_str is None:
        date_str = datetime.now().strftime('%Y%m%d')
    url = f"https://site.api.espn.com/apis/site/v2/sports/{sport_path}/scoreboard?dates={date_str}"
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        print(f"ESPN error: {e}")
    return None

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

def get_team_statistics(sport_path, team_id):
    """Fetch team statistics from ESPN API"""
    stats = {}
    try:
        url = f"https://site.api.espn.com/apis/site/v2/sports/{sport_path}/teams/{team_id}/statistics"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            # Parse stats from ESPN response
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

def format_stat(val, default='-'):
    """Format a stat value safely"""
    if val is None or val == '' or val == '-':
        return default
    try:
        return round(float(val), 1)
    except:
        return val

def get_nfl_team_stats(raw_stats, record):
    """Extract NFL offensive and defensive stats"""
    wins, losses = parse_record(record)
    total = wins + losses
    pwr = round((wins / total * 100), 1) if total > 0 else 50.0

    return {
        'pwr': pwr,
        'ppg': format_stat(raw_stats.get('avgPoints', raw_stats.get('totalPointsPerGame'))),
        'ypg': format_stat(raw_stats.get('totalYardsPerGame')),
        'pass_ypg': format_stat(raw_stats.get('netPassingYardsPerGame')),
        'rush_ypg': format_stat(raw_stats.get('rushingYardsPerGame')),
        'opp_ppg': format_stat(raw_stats.get('avgPointsAgainst', raw_stats.get('pointsAgainstPerGame'))),
        'opp_ypg': format_stat(raw_stats.get('yardsAllowedPerGame')),
        'to_diff': raw_stats.get('turnoverDifferential', '-'),
        'sacks': format_stat(raw_stats.get('sacks')),
        'ints': format_stat(raw_stats.get('interceptions')),
    }

def get_nba_team_stats(raw_stats, record):
    """Extract NBA offensive and defensive stats"""
    wins, losses = parse_record(record)
    total = wins + losses
    pwr = round((wins / total * 100), 1) if total > 0 else 50.0

    return {
        'pwr': pwr,
        'ppg': format_stat(raw_stats.get('avgPoints', raw_stats.get('pointsPerGame'))),
        'opp_ppg': format_stat(raw_stats.get('avgPointsAgainst', raw_stats.get('oppPointsPerGame'))),
        'fg_pct': format_stat(raw_stats.get('fieldGoalPct')),
        'three_pct': format_stat(raw_stats.get('threePointFieldGoalPct')),
        'reb': format_stat(raw_stats.get('avgRebounds')),
        'ast': format_stat(raw_stats.get('avgAssists')),
        'to': format_stat(raw_stats.get('avgTurnovers')),
        'stl': format_stat(raw_stats.get('avgSteals')),
        'blk': format_stat(raw_stats.get('avgBlocks')),
    }

def get_nhl_team_stats(raw_stats, record):
    """Extract NHL offensive and defensive stats"""
    wins, losses = parse_record(record)
    total = wins + losses
    pwr = round((wins / total * 100), 1) if total > 0 else 50.0

    gf = format_stat(raw_stats.get('goalsFor', raw_stats.get('goalsPerGame')))
    ga = format_stat(raw_stats.get('goalsAgainst', raw_stats.get('goalsAgainstPerGame')))

    return {
        'pwr': pwr,
        'gf': gf,
        'ga': ga,
        'pp_pct': format_stat(raw_stats.get('powerPlayPct')),
        'pk_pct': format_stat(raw_stats.get('penaltyKillPct')),
        'sog': format_stat(raw_stats.get('shotsPerGame')),
        'sv_pct': raw_stats.get('savePct', '-'),
        'fow_pct': format_stat(raw_stats.get('faceoffWinPct')),
    }

def match_odds_to_game(odds_data, away_name, home_name):
    """Find odds for a specific game"""
    result = {'spread': '-', 'total': '-', 'ml_away': '-', 'ml_home': '-'}

    for game in odds_data:
        api_away = game.get('away_team', '').lower()
        api_home = game.get('home_team', '').lower()

        # Match by partial name
        if (away_name.lower() in api_away or api_away in away_name.lower()) and \
           (home_name.lower() in api_home or api_home in home_name.lower()):

            for bm in game.get('bookmakers', [])[:1]:
                for market in bm.get('markets', []):
                    if market['key'] == 'spreads':
                        for o in market['outcomes']:
                            if home_name.lower() in o['name'].lower():
                                spread = o['point']
                                result['spread'] = f"{spread:+.1f}" if spread >= 0 else f"{spread:.1f}"
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

# ============================================
# HTML GENERATION
# ============================================

def generate_team_stats_html(team_name, team_abbr, stats, sport, logo_sport, is_away=True):
    """Generate HTML for a team's stats row with logo"""

    if sport in ['NFL', 'NCAAF']:
        stats_html = f'''
        <div class="stat-item"><span class="value">{stats.get('pwr', '-')}</span><span class="label">PWR</span></div>
        <div class="stat-item"><span class="value">{stats.get('ppg', '-')}</span><span class="label">PPG</span></div>
        <div class="stat-item"><span class="value">{stats.get('ypg', '-')}</span><span class="label">YPG</span></div>
        <div class="stat-item"><span class="value">{stats.get('pass_ypg', '-')}</span><span class="label">PASS</span></div>
        <div class="stat-item"><span class="value">{stats.get('rush_ypg', '-')}</span><span class="label">RUSH</span></div>
        <div class="stat-item off"><span class="value">{stats.get('opp_ppg', '-')}</span><span class="label">OPP PPG</span></div>
        <div class="stat-item off"><span class="value">{stats.get('opp_ypg', '-')}</span><span class="label">OPP YPG</span></div>
        <div class="stat-item off"><span class="value">{stats.get('to_diff', '-')}</span><span class="label">TO+/-</span></div>
        <div class="stat-item off"><span class="value">{stats.get('sacks', '-')}</span><span class="label">SACKS</span></div>
        <div class="stat-item off"><span class="value">{stats.get('ints', '-')}</span><span class="label">INT</span></div>
        '''
    elif sport in ['NBA', 'NCAAB']:
        stats_html = f'''
        <div class="stat-item"><span class="value">{stats.get('pwr', '-')}</span><span class="label">PWR</span></div>
        <div class="stat-item"><span class="value">{stats.get('ppg', '-')}</span><span class="label">PPG</span></div>
        <div class="stat-item"><span class="value">{stats.get('fg_pct', '-')}</span><span class="label">FG%</span></div>
        <div class="stat-item"><span class="value">{stats.get('three_pct', '-')}</span><span class="label">3P%</span></div>
        <div class="stat-item"><span class="value">{stats.get('reb', '-')}</span><span class="label">REB</span></div>
        <div class="stat-item"><span class="value">{stats.get('ast', '-')}</span><span class="label">AST</span></div>
        <div class="stat-item off"><span class="value">{stats.get('opp_ppg', '-')}</span><span class="label">OPP PPG</span></div>
        <div class="stat-item off"><span class="value">{stats.get('stl', '-')}</span><span class="label">STL</span></div>
        <div class="stat-item off"><span class="value">{stats.get('blk', '-')}</span><span class="label">BLK</span></div>
        <div class="stat-item off"><span class="value">{stats.get('to', '-')}</span><span class="label">TO</span></div>
        '''
    elif sport == 'NHL':
        stats_html = f'''
        <div class="stat-item"><span class="value">{stats.get('pwr', '-')}</span><span class="label">PWR</span></div>
        <div class="stat-item"><span class="value">{stats.get('gf', '-')}</span><span class="label">GF</span></div>
        <div class="stat-item"><span class="value">{stats.get('ga', '-')}</span><span class="label">GA</span></div>
        <div class="stat-item"><span class="value">{stats.get('pp_pct', '-')}</span><span class="label">PP%</span></div>
        <div class="stat-item off"><span class="value">{stats.get('pk_pct', '-')}</span><span class="label">PK%</span></div>
        <div class="stat-item off"><span class="value">{stats.get('sog', '-')}</span><span class="label">SOG</span></div>
        <div class="stat-item off"><span class="value">{stats.get('sv_pct', '-')}</span><span class="label">SV%</span></div>
        <div class="stat-item off"><span class="value">{stats.get('fow_pct', '-')}</span><span class="label">FOW%</span></div>
        '''
    else:
        stats_html = '<div class="stat-item"><span class="value">-</span><span class="label">-</span></div>'

    label = "AWAY" if is_away else "HOME"

    return f'''
<div class="team-stats-row">
    <div class="team-info">
        <img alt="{team_name}" class="team-logo-small" onerror="this.style.display='none'" src="https://a.espncdn.com/i/teamlogos/{logo_sport}/500/scoreboard/{team_abbr.lower()}.png"/>
        <span class="team-abbr">{team_abbr}</span>
        <span class="team-label">{label}</span>
    </div>
    <div class="team-stats-grid">
        {stats_html}
    </div>
</div>
'''

def generate_game_card(away_name, home_name, away_abbr, home_abbr, away_record, home_record,
                       game_time, venue, network, odds, sport, away_stats=None, home_stats=None):
    """Generate HTML for a single game card with analysis article and team stats"""

    # Determine spread display
    try:
        spread_val = float(odds['spread'].replace('+', ''))
        if spread_val < 0:
            spread_display = f"{home_abbr} {odds['spread']}"
        else:
            spread_display = f"{away_abbr} {-spread_val:+.1f}"
    except:
        spread_display = odds['spread']

    # Generate analysis article for this game
    analysis_html = generate_game_analysis(sport, away_name, home_name, away_record, home_record, odds, venue)

    # Fix logo path for college sports and soccer
    logo_sport = sport.lower()
    if sport == 'NCAAB':
        logo_sport = 'ncaab'
    elif sport == 'NCAAF':
        logo_sport = 'ncaa'
    elif sport.upper() == 'SOCCER':
        logo_sport = 'soccer'  # Soccer uses team IDs, handled separately below

    # Generate team stats rows if available
    if away_stats is None:
        away_stats = {'pwr': '-'}
    if home_stats is None:
        home_stats = {'pwr': '-'}

    away_stats_html = generate_team_stats_html(away_name, away_abbr, away_stats, sport, logo_sport, is_away=True)
    home_stats_html = generate_team_stats_html(home_name, home_abbr, home_stats, sport, logo_sport, is_away=False)

    return f'''
<article class="game-card">
<div class="teams-display">
<img alt="{away_name}" class="team-logo" onerror="this.style.display='none'" src="https://a.espncdn.com/i/teamlogos/{logo_sport}/500/scoreboard/{away_abbr.lower()}.png"/>
<span class="vs-badge">@</span>
<img alt="{home_name}" class="team-logo" onerror="this.style.display='none'" src="https://a.espncdn.com/i/teamlogos/{logo_sport}/500/scoreboard/{home_abbr.lower()}.png"/>
</div>
<h3 class="game-title">{away_name} @ {home_name}</h3>
<div class="game-meta">
<span>{game_time}</span>
<span>{away_record} vs {home_record}</span>
<span>{venue}</span>
<span>{network}</span>
</div>
<div class="lines-row">
<div class="stat-item"><span class="value">{spread_display}</span><span class="label">Spread</span></div>
<div class="stat-item"><span class="value">{odds['total']}</span><span class="label">O/U</span></div>
<div class="stat-item"><span class="value">{odds['ml_away']}</span><span class="label">{away_abbr} ML</span></div>
<div class="stat-item"><span class="value">{odds['ml_home']}</span><span class="label">{home_abbr} ML</span></div>
</div>
<div class="team-stats-section">
<div class="stats-header">TEAM STATISTICS</div>
{away_stats_html}
{home_stats_html}
</div>
<div class="game-analysis">
{analysis_html}
</div>
<p class="data-source">Data: ESPN, The Odds API | Lines subject to change</p>
</article>
'''

def update_sport_page(sport):
    """Update a sport page with current accurate data"""
    config = SPORT_CONFIG[sport]

    print(f"\n=== Updating {sport} ===")

    # Get today's games
    espn_data = get_espn_scoreboard(config['espn_path'])
    if not espn_data:
        print(f"Failed to get ESPN data for {sport}")
        return False

    events = espn_data.get('events', [])
    print(f"Found {len(events)} games")

    if not events:
        print("No games today")
        return True

    # Get odds
    odds_data = get_odds(config['odds_key'])
    print(f"Found odds for {len(odds_data)} games")

    # Generate game cards
    game_cards = []
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

        # Fetch team statistics
        away_id = away_team.get('id', '')
        home_id = home_team.get('id', '')

        away_raw_stats = get_team_statistics(config['espn_path'], away_id) if away_id else {}
        home_raw_stats = get_team_statistics(config['espn_path'], home_id) if home_id else {}

        away_record = away.get('records', [{}])[0].get('summary', '0-0') if away.get('records') else '0-0'
        home_record = home.get('records', [{}])[0].get('summary', '0-0') if home.get('records') else '0-0'

        # Extract formatted stats based on sport
        if sport in ['NFL', 'NCAAF']:
            away_stats = get_nfl_team_stats(away_raw_stats, away_record)
            home_stats = get_nfl_team_stats(home_raw_stats, home_record)
        elif sport in ['NBA', 'NCAAB']:
            away_stats = get_nba_team_stats(away_raw_stats, away_record)
            home_stats = get_nba_team_stats(home_raw_stats, home_record)
        elif sport == 'NHL':
            away_stats = get_nhl_team_stats(away_raw_stats, away_record)
            home_stats = get_nhl_team_stats(home_raw_stats, home_record)
        else:
            away_stats = {'pwr': '-'}
            home_stats = {'pwr': '-'}

        # Game details - use empty strings, NEVER TBD
        venue = comps.get('venue', {}).get('fullName', '')
        broadcasts = comps.get('broadcasts', [{}])
        network = broadcasts[0].get('names', [''])[0] if broadcasts else ''

        game_date = event.get('date', '')
        try:
            dt = datetime.fromisoformat(game_date.replace('Z', '+00:00'))
            game_time = dt.strftime("%I:%M %p ET")
        except:
            game_time = ""

        # Get odds for this game
        odds = match_odds_to_game(odds_data, away_name, home_name)

        card = generate_game_card(
            away_name, home_name, away_abbr, home_abbr,
            away_record, home_record, game_time, venue, network,
            odds, sport, away_stats, home_stats
        )
        game_cards.append(card)
        print(f"  {away_name} @ {home_name}: Spread {odds['spread']}, O/U {odds['total']}")

    # Generate full page HTML
    today = datetime.now()
    date_str = today.strftime("%B %d, %Y")

    html = generate_page_html(sport, date_str, len(events), ''.join(game_cards))

    # Write to file
    output_path = os.path.join(REPO_PATH, config['output'])
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"Updated {config['output']}")
    return True

def generate_page_html(sport, date_str, game_count, game_cards):
    """Generate full page HTML with analysis styling"""
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<title>{sport} Analysis - {date_str} | BetLegend</title>
<meta content="{sport} statistical analysis for {date_str}. Advanced stats and betting lines for all {game_count} games." name="description"/>
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
.stat-row,.lines-row{{display:flex;flex-wrap:wrap;gap:12px;margin:16px 0;padding:16px;background:rgba(0,0,0,0.3);border-radius:12px;border:1px solid var(--border-subtle)}}
.stat-item{{flex:1;min-width:80px;text-align:center;padding:8px}}
.stat-item .value{{font-family:var(--font-primary);font-size:1.1rem;font-weight:700;color:var(--accent-gold)}}
.stat-item .label{{font-size:0.65rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.5px}}
.stat-item.off .value{{color:var(--accent-cyan)}}
/* Team Stats Section */
.team-stats-section{{margin:20px 0;padding:20px;background:rgba(0,20,40,0.5);border-radius:12px;border:1px solid rgba(0,229,255,0.2)}}
.stats-header{{font-family:var(--font-primary);font-size:0.75rem;color:var(--accent-cyan);text-transform:uppercase;letter-spacing:2px;margin-bottom:15px;padding-bottom:10px;border-bottom:1px solid var(--border-subtle);text-align:center}}
.team-stats-row{{display:flex;align-items:center;gap:15px;padding:12px;margin-bottom:8px;background:rgba(0,0,0,0.3);border-radius:10px;border:1px solid var(--border-subtle)}}
.team-stats-row:last-child{{margin-bottom:0}}
.team-info{{display:flex;align-items:center;gap:10px;min-width:120px}}
.team-logo-small{{width:36px;height:36px;object-fit:contain}}
.team-abbr{{font-family:var(--font-primary);font-size:1rem;font-weight:700;color:#fff}}
.team-label{{font-size:0.6rem;color:var(--text-muted);text-transform:uppercase;padding:2px 6px;background:rgba(255,255,255,0.1);border-radius:4px}}
.team-stats-grid{{display:flex;flex-wrap:wrap;flex:1;gap:8px;justify-content:space-around}}
/* Analysis Section Styles */
.game-analysis{{margin-top:20px;padding-top:20px;border-top:1px solid var(--border-subtle)}}
.analysis-section{{margin-bottom:16px}}
.analysis-section h4{{font-family:var(--font-primary);font-size:0.85rem;color:var(--accent-cyan);text-transform:uppercase;letter-spacing:1px;margin-bottom:8px}}
.analysis-section p{{color:var(--text-secondary);font-size:0.95rem;line-height:1.7}}
footer{{text-align:center;padding:40px 24px;color:var(--text-muted);font-size:13px;border-top:1px solid var(--border-subtle)}}
footer a{{color:var(--accent-cyan);text-decoration:none}}
.data-source{{font-size:11px;color:var(--text-muted);text-align:center;margin-top:8px;padding-top:12px;border-top:1px solid var(--border-subtle)}}
@media(max-width:768px){{.hero{{padding:160px 20px 40px}}.game-card{{padding:24px}}.team-logo{{width:48px;height:48px}}.stat-row{{flex-direction:column}}}}
</style>
</head>
<body>
<nav class="nav-container">
<div class="nav-inner">
<div class="logo"><a href="index.html">BET<span>LEGEND</span></a></div>
<div class="nav-links">
<a href="handicapping-hub.html" style="background:linear-gradient(135deg,#ff6b00,#ff8c00);color:#fff;border-radius:8px;">Handicapping Hub</a>
<a href="blog-page10.html">Picks</a>
<div class="dropdown"><button class="dropbtn">Records</button><div class="dropdown-content"><a href="records.html">Overview</a><a href="nfl-records.html">NFL</a><a href="nba-records.html">NBA</a><a href="nhl-records.html">NHL</a><a href="ncaaf-records.html">NCAAF</a><a href="ncaab-records.html">NCAAB</a><a href="mlb-records.html">MLB</a></div></div>
<div class="dropdown"><button class="dropbtn">Sports</button><div class="dropdown-content"><a href="nfl.html">NFL</a><a href="nba.html">NBA</a><a href="nhl.html">NHL</a><a href="ncaaf.html">NCAAF</a><a href="ncaab.html">NCAAB</a><a href="mlb.html">MLB</a></div></div>
<a href="proofofpicks.html">Proof</a>
</div>
</div>
</nav>
<header class="hero">
<div class="hero-badge">{sport}</div>
<h1>{sport} <span>Analysis</span></h1>
<p>{game_count}-Game Slate | Real-Time Odds & Stats</p>
</header>
<div class="current-date"><h2>{date_str}</h2></div>
<main>
{game_cards}
</main>
<footer>
<p>&copy; 2025 BetLegend. All rights reserved. | <a href="index.html">Home</a></p>
<p style="margin-top:10px">Data sourced from ESPN and The Odds API. Lines subject to change.</p>
</footer>
</body>
</html>'''

def main():
    print("=" * 50)
    print("SPORTS PAGE UPDATER WITH ANALYSIS")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 50)

    # Update each sport that has games today
    for sport in ['NFL', 'NBA', 'NHL', 'NCAAB', 'NCAAF']:
        update_sport_page(sport)

    print("\n" + "=" * 50)
    print("UPDATE COMPLETE - All pages now include analysis articles")
    print("=" * 50)

if __name__ == "__main__":
    main()
