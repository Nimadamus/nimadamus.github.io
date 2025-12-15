#!/usr/bin/env python3
"""
================================================================================
HANDICAPPING HUB - ULTIMATE PRODUCTION SYSTEM
================================================================================
THE BEST HANDICAPPING HUB ON THE INTERNET

Layout: 4-Section Game Cards
1. BETTING LINES - Spread, ML, Total with Opening Lines & Movement
2. OFFENSE vs DEFENSE - Side-by-side comparison
3. EFFICIENCY vs SITUATIONAL - Advanced metrics
4. TRENDS BAR - Injuries, ATS record, O/U record

Visual Style (LOCKED):
- Light gray background (#f0f2f5)
- Dark blue gradient header (#1a365d to #2d4a7c)
- White content panels (#fff)
- Orange accent (#fd5000)
- Inter font family

Sport Tabs: NBA, NFL, NHL, NCAAB, NCAAF

This runs DAILY with ZERO manual intervention required.
================================================================================
"""

import requests
import json
import os
import sys
import shutil
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

# =============================================================================
# CONFIGURATION
# =============================================================================

ODDS_API_KEY = "deeac7e7af6a8f1a5ac84c625e04973a"
REPO_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_FILE = "handicapping-hub.html"

SPORTS = {
    'NBA': {
        'espn_path': 'basketball/nba',
        'odds_key': 'basketball_nba',
        'logo_path': 'nba',
    },
    'NFL': {
        'espn_path': 'football/nfl',
        'odds_key': 'americanfootball_nfl',
        'logo_path': 'nfl',
    },
    'NHL': {
        'espn_path': 'hockey/nhl',
        'odds_key': 'icehockey_nhl',
        'logo_path': 'nhl',
    },
    'NCAAB': {
        'espn_path': 'basketball/mens-college-basketball',
        'odds_key': 'basketball_ncaab',
        'logo_path': 'ncaa',
    },
    'NCAAF': {
        'espn_path': 'football/college-football',
        'odds_key': 'americanfootball_ncaaf',
        'logo_path': 'ncaa',
    },
}

# Top 50 NCAAB teams to show (by ranking/brand)
TOP_NCAAB_TEAMS = {
    'kansas', 'duke', 'north carolina', 'kentucky', 'gonzaga', 'villanova',
    'uconn', 'connecticut', 'michigan state', 'auburn', 'tennessee', 'alabama',
    'purdue', 'houston', 'iowa state', 'baylor', 'arizona', 'marquette',
    'creighton', 'texas', 'louisville', 'indiana', 'wisconsin', 'michigan',
    'oregon', 'florida', 'ohio state', 'illinois', 'ucla', 'usc',
    'arkansas', 'cincinnati', 'memphis', 'providence', 'st. johns', 'xavier',
    'butler', 'san diego state', 'clemson', 'oklahoma', 'iowa', 'texas tech',
    'kansas state', 'mississippi state', 'ole miss', 'vanderbilt', 'lsu',
    'colorado', 'pittsburgh', 'dayton'
}

# =============================================================================
# ARCHIVE SYSTEM
# =============================================================================

def archive_current_hub():
    """
    Archive the current handicapping-hub.html before generating a new one.
    Creates a dated copy and updates the archive calendar.
    """
    today = datetime.now().strftime('%Y-%m-%d')
    hub_path = os.path.join(REPO_PATH, OUTPUT_FILE)
    archive_filename = f"handicapping-hub-{today}.html"
    archive_path = os.path.join(REPO_PATH, archive_filename)

    # Only archive if source exists and archive doesn't already exist
    if os.path.exists(hub_path) and not os.path.exists(archive_path):
        print(f"\n[ARCHIVE] Creating archive: {archive_filename}")
        shutil.copy2(hub_path, archive_path)

        # Update the archive calendar
        update_archive_calendar(today, archive_filename)
        print(f"[ARCHIVE] Archive created successfully")
    elif os.path.exists(archive_path):
        print(f"\n[ARCHIVE] Archive already exists for {today}, skipping...")
    else:
        print(f"\n[ARCHIVE] No existing hub to archive, first run")

def update_archive_calendar(date_str: str, filename: str):
    """Update the archive calendar page with the new archive entry"""
    archive_page = os.path.join(REPO_PATH, 'handicapping-hub-archive.html')

    if not os.path.exists(archive_page):
        print(f"  [ARCHIVE] Archive page not found, skipping calendar update")
        return

    try:
        with open(archive_page, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check if this date is already in the archive
        if f'"{date_str}"' in content:
            print(f"  [ARCHIVE] Date {date_str} already in calendar")
            return

        # Find the archiveData object and add the new entry
        # Pattern: Find the last entry before the closing brace
        pattern = r'("20\d{2}-\d{2}-\d{2}":\s*"[^"]+"\s*)\n(\s*\};)'
        match = re.search(pattern, content)

        if match:
            new_entry = f'{match.group(1)},\n            "{date_str}": "{filename}"\n{match.group(2)}'
            content = content[:match.start()] + new_entry + content[match.end():]

            with open(archive_page, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  [ARCHIVE] Added {date_str} to archive calendar")
    except Exception as e:
        print(f"  [ARCHIVE] Error updating calendar: {e}")

def get_archive_dates_json() -> str:
    """
    Scan for existing archive files and return a JSON object mapping dates to filenames.
    Today's date maps to handicapping-hub.html (the current page).
    """
    import glob

    archive_dict = {}
    today = datetime.now().strftime('%Y-%m-%d')

    # Scan for archive files first
    pattern = os.path.join(REPO_PATH, 'handicapping-hub-20*.html')
    for filepath in glob.glob(pattern):
        filename = os.path.basename(filepath)
        # Extract date from filename: handicapping-hub-YYYY-MM-DD.html
        match = re.match(r'handicapping-hub-(\d{4}-\d{2}-\d{2})\.html', filename)
        if match:
            date = match.group(1)
            archive_dict[date] = filename

    # Today's date always maps to current hub (overwrites archive if exists)
    archive_dict[today] = 'handicapping-hub.html'

    return json.dumps(archive_dict)

def is_game_completed(game: Dict) -> bool:
    """Check if a game has already been completed"""
    status = game.get('status', {})
    state = status.get('type', {}).get('state', '')
    return state.lower() == 'post'

def is_important_ncaab_game(game: Dict) -> bool:
    """Check if an NCAAB game involves top teams (ranked/major programs)"""
    competitors = game.get('competitions', [{}])[0].get('competitors', [])
    for team in competitors:
        team_name = team.get('team', {}).get('displayName', '').lower()
        # Check if team is ranked (has a current rank)
        if team.get('curatedRank', {}).get('current'):
            return True
        # Check if team is in our top teams list
        for top_team in TOP_NCAAB_TEAMS:
            if top_team in team_name:
                return True
    return False

def is_bowl_game(game: Dict) -> bool:
    """Check if an NCAAF game is a bowl game"""
    game_name = game.get('name', '').lower()
    short_name = game.get('shortName', '').lower()
    notes = game.get('competitions', [{}])[0].get('notes', [{}])
    headline = notes[0].get('headline', '').lower() if notes else ''

    bowl_keywords = ['bowl', 'playoff', 'championship', 'fiesta', 'rose', 'sugar',
                     'orange', 'cotton', 'peach', 'alamo', 'citrus', 'music city',
                     'liberty', 'holiday', 'sun', 'gator', 'duke', 'mayo', 'pop-tarts',
                     'tax act', 'go bowling', 'las vegas', 'fenway', 'pinstripe']

    for keyword in bowl_keywords:
        if keyword in game_name or keyword in short_name or keyword in headline:
            return True
    return False

# =============================================================================
# DATA FETCHING
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
        print(f"  [ERROR] ESPN scoreboard fetch failed: {e}")
    return []

def fetch_team_statistics(sport_path: str, team_id: str) -> Dict:
    """Fetch comprehensive team statistics from ESPN"""
    stats = {}
    try:
        url = f"https://site.api.espn.com/apis/site/v2/sports/{sport_path}/teams/{team_id}/statistics"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            # Parse all stats from ESPN response
            for cat in data.get('results', {}).get('stats', {}).get('categories', []):
                cat_name = cat.get('name', '')
                for stat in cat.get('stats', []):
                    name = stat.get('name', '')
                    value = stat.get('displayValue', stat.get('value', ''))
                    stats[name] = value
            # Also check splits format
            for split in data.get('results', {}).get('splits', {}).get('categories', []):
                for stat in split.get('stats', []):
                    name = stat.get('name', '')
                    value = stat.get('displayValue', stat.get('value', ''))
                    stats[name] = value
    except:
        pass
    return stats

def fetch_odds(sport_key: str) -> List[Dict]:
    """Fetch betting odds from The Odds API - filtered to today's games only"""
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
            all_odds = resp.json()

            # Filter to only include games happening TODAY (in Eastern Time)
            # Odds API returns UTC times, so we need to convert
            today = datetime.now()
            today_date = today.date()

            filtered = []
            for game in all_odds:
                commence = game.get('commence_time', '')
                if commence:
                    try:
                        # Parse ISO format datetime (UTC)
                        game_dt = datetime.fromisoformat(commence.replace('Z', '+00:00'))
                        # Convert UTC to Eastern (UTC - 5 hours for EST)
                        game_est = game_dt.replace(tzinfo=None) - timedelta(hours=5)
                        game_date = game_est.date()

                        # Include games from today
                        if game_date == today_date:
                            filtered.append(game)
                    except Exception as e:
                        pass

            print(f"  [ODDS] Filtered from {len(all_odds)} to {len(filtered)} today's games")
            return filtered
    except Exception as e:
        print(f"  [ERROR] Odds API fetch failed: {e}")
    return []

def fetch_team_injuries(sport_path: str, team_id: str) -> List[Dict]:
    """Fetch team injuries from ESPN"""
    injuries = []
    try:
        # Try the injuries endpoint
        url = f"https://site.api.espn.com/apis/site/v2/sports/{sport_path}/teams/{team_id}/injuries"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            for item in data.get('items', []):
                athlete = item.get('athlete', {})
                name = athlete.get('displayName', athlete.get('shortName', 'Unknown'))
                position = athlete.get('position', {}).get('abbreviation', '')
                status = item.get('status', 'Unknown')
                injury_type = item.get('type', {}).get('text', item.get('details', {}).get('type', ''))

                # Only include significant injuries (Out, Doubtful, Questionable)
                status_lower = status.lower() if status else ''
                if status_lower in ['out', 'doubtful', 'questionable', 'injured reserve', 'ir', 'day-to-day']:
                    injuries.append({
                        'name': name,
                        'position': position,
                        'status': status,
                        'type': injury_type
                    })

        # Also try the roster endpoint for injury info
        if not injuries:
            url = f"https://site.api.espn.com/apis/site/v2/sports/{sport_path}/teams/{team_id}/roster"
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                for athlete in data.get('athletes', []):
                    for player in athlete.get('items', []):
                        injury = player.get('injuries', [])
                        if injury:
                            inj = injury[0]
                            status = inj.get('status', '')
                            if status.lower() in ['out', 'doubtful', 'questionable', 'day-to-day']:
                                injuries.append({
                                    'name': player.get('displayName', 'Unknown'),
                                    'position': player.get('position', {}).get('abbreviation', ''),
                                    'status': status,
                                    'type': inj.get('type', {}).get('text', '')
                                })
    except Exception as e:
        pass  # Silently fail - injuries are supplemental

    return injuries[:5]  # Limit to top 5 injuries per team

def format_injuries_html(injuries: List[Dict], abbr: str) -> str:
    """Format injuries for display in trends bar"""
    if not injuries:
        return f"{abbr}: No reported injuries"

    injury_strs = []
    for inj in injuries[:3]:  # Show max 3 per team
        name = inj.get('name', 'Unknown')
        # Shorten name to first initial + last name
        parts = name.split()
        if len(parts) > 1:
            short_name = f"{parts[0][0]}. {parts[-1]}"
        else:
            short_name = name

        pos = inj.get('position', '')
        status = inj.get('status', '')

        # Abbreviate status
        status_abbr = status
        if status.lower() == 'questionable':
            status_abbr = 'Q'
        elif status.lower() == 'doubtful':
            status_abbr = 'D'
        elif status.lower() in ['out', 'injured reserve', 'ir']:
            status_abbr = 'OUT'
        elif status.lower() == 'day-to-day':
            status_abbr = 'DTD'

        injury_strs.append(f"{short_name} ({pos}) - {status_abbr}")

    return f"{abbr}: {', '.join(injury_strs)}"

def get_team_nickname(full_name: str) -> str:
    """Extract team nickname from full name (e.g., 'San Francisco 49ers' -> '49ers')"""
    # Handle common patterns
    full_lower = full_name.lower().strip()

    # Team nickname mappings for exact matching
    nickname_map = {
        # NFL
        '49ers': '49ers', 'niners': '49ers', 'san francisco': '49ers',
        'titans': 'titans', 'tennessee titans': 'titans',
        'colts': 'colts', 'indianapolis colts': 'colts',
        'chiefs': 'chiefs', 'kansas city chiefs': 'chiefs',
        'cowboys': 'cowboys', 'dallas cowboys': 'cowboys',
        'vikings': 'vikings', 'minnesota vikings': 'vikings',
        'bears': 'bears', 'chicago bears': 'bears',
        'browns': 'browns', 'cleveland browns': 'browns',
        'ravens': 'ravens', 'baltimore ravens': 'ravens',
        'bengals': 'bengals', 'cincinnati bengals': 'bengals',
        'chargers': 'chargers', 'los angeles chargers': 'chargers',
        'bills': 'bills', 'buffalo bills': 'bills',
        'patriots': 'patriots', 'new england patriots': 'patriots',
        'commanders': 'commanders', 'washington commanders': 'commanders',
        'giants': 'giants', 'new york giants': 'giants',
        'raiders': 'raiders', 'las vegas raiders': 'raiders',
        'eagles': 'eagles', 'philadelphia eagles': 'eagles',
        'jets': 'jets', 'new york jets': 'jets',
        'jaguars': 'jaguars', 'jacksonville jaguars': 'jaguars',
        'cardinals': 'cardinals', 'arizona cardinals': 'cardinals',
        'texans': 'texans', 'houston texans': 'texans',
        'packers': 'packers', 'green bay packers': 'packers',
        'broncos': 'broncos', 'denver broncos': 'broncos',
        'lions': 'lions', 'detroit lions': 'lions',
        'rams': 'rams', 'los angeles rams': 'rams',
        'panthers': 'panthers', 'carolina panthers': 'panthers',
        'saints': 'saints', 'new orleans saints': 'saints',
        'seahawks': 'seahawks', 'seattle seahawks': 'seahawks',
        'buccaneers': 'buccaneers', 'bucs': 'buccaneers', 'tampa bay buccaneers': 'buccaneers',
        'falcons': 'falcons', 'atlanta falcons': 'falcons',
        'dolphins': 'dolphins', 'miami dolphins': 'dolphins',
        'steelers': 'steelers', 'pittsburgh steelers': 'steelers',
        # NBA
        'lakers': 'lakers', 'los angeles lakers': 'lakers',
        'celtics': 'celtics', 'boston celtics': 'celtics',
        'warriors': 'warriors', 'golden state warriors': 'warriors',
        'cavaliers': 'cavaliers', 'cavs': 'cavaliers', 'cleveland cavaliers': 'cavaliers',
        'pacers': 'pacers', 'indiana pacers': 'pacers',
        'wizards': 'wizards', 'washington wizards': 'wizards',
        'hornets': 'hornets', 'charlotte hornets': 'hornets',
        'hawks': 'hawks', 'atlanta hawks': 'hawks',
        '76ers': '76ers', 'sixers': '76ers', 'philadelphia 76ers': '76ers',
        'heat': 'heat', 'miami heat': 'heat',
        'magic': 'magic', 'orlando magic': 'magic',
        'pistons': 'pistons', 'detroit pistons': 'pistons',
        'bulls': 'bulls', 'chicago bulls': 'bulls',
        'bucks': 'bucks', 'milwaukee bucks': 'bucks',
        'raptors': 'raptors', 'toronto raptors': 'raptors',
        'knicks': 'knicks', 'new york knicks': 'knicks',
        'nets': 'nets', 'brooklyn nets': 'nets',
        'thunder': 'thunder', 'oklahoma city thunder': 'thunder',
        'mavericks': 'mavericks', 'mavs': 'mavericks', 'dallas mavericks': 'mavericks',
        'rockets': 'rockets', 'houston rockets': 'rockets',
        'spurs': 'spurs', 'san antonio spurs': 'spurs',
        'grizzlies': 'grizzlies', 'memphis grizzlies': 'grizzlies',
        'pelicans': 'pelicans', 'new orleans pelicans': 'pelicans',
        'nuggets': 'nuggets', 'denver nuggets': 'nuggets',
        'timberwolves': 'timberwolves', 'wolves': 'timberwolves', 'minnesota timberwolves': 'timberwolves',
        'trail blazers': 'trail blazers', 'blazers': 'trail blazers', 'portland trail blazers': 'trail blazers',
        'jazz': 'jazz', 'utah jazz': 'jazz',
        'suns': 'suns', 'phoenix suns': 'suns',
        'clippers': 'clippers', 'la clippers': 'clippers', 'los angeles clippers': 'clippers',
        'kings': 'kings', 'sacramento kings': 'kings',
        # NHL
        'bruins': 'bruins', 'boston bruins': 'bruins',
        'canadiens': 'canadiens', 'habs': 'canadiens', 'montreal canadiens': 'canadiens',
        'maple leafs': 'maple leafs', 'leafs': 'maple leafs', 'toronto maple leafs': 'maple leafs',
        'senators': 'senators', 'sens': 'senators', 'ottawa senators': 'senators',
        'sabres': 'sabres', 'buffalo sabres': 'sabres',
        'red wings': 'red wings', 'detroit red wings': 'red wings',
        'lightning': 'lightning', 'bolts': 'lightning', 'tampa bay lightning': 'lightning',
        'blue jackets': 'blue jackets', 'columbus blue jackets': 'blue jackets',
        'hurricanes': 'hurricanes', 'canes': 'hurricanes', 'carolina hurricanes': 'hurricanes',
        'flyers': 'flyers', 'philadelphia flyers': 'flyers',
        'penguins': 'penguins', 'pens': 'penguins', 'pittsburgh penguins': 'penguins',
        'capitals': 'capitals', 'caps': 'capitals', 'washington capitals': 'capitals',
        'islanders': 'islanders', 'isles': 'islanders', 'new york islanders': 'islanders',
        'rangers': 'rangers', 'new york rangers': 'rangers',
        'devils': 'devils', 'new jersey devils': 'devils',
        'blackhawks': 'blackhawks', 'hawks': 'blackhawks', 'chicago blackhawks': 'blackhawks',
        'blues': 'blues', 'st. louis blues': 'blues', 'st louis blues': 'blues',
        'predators': 'predators', 'preds': 'predators', 'nashville predators': 'predators',
        'stars': 'stars', 'dallas stars': 'stars',
        'wild': 'wild', 'minnesota wild': 'wild',
        'avalanche': 'avalanche', 'avs': 'avalanche', 'colorado avalanche': 'avalanche',
        'jets': 'jets', 'winnipeg jets': 'jets',
        'coyotes': 'coyotes', 'arizona coyotes': 'coyotes', 'utah hockey club': 'utah',
        'flames': 'flames', 'calgary flames': 'flames',
        'oilers': 'oilers', 'edmonton oilers': 'oilers',
        'canucks': 'canucks', 'vancouver canucks': 'canucks',
        'kraken': 'kraken', 'seattle kraken': 'kraken',
        'sharks': 'sharks', 'san jose sharks': 'sharks',
        'ducks': 'ducks', 'anaheim ducks': 'ducks',
        'golden knights': 'golden knights', 'knights': 'golden knights', 'vegas golden knights': 'golden knights',
    }

    # Try to find nickname in the name
    for key, nickname in nickname_map.items():
        if key in full_lower:
            return nickname

    # Fallback: return last word (usually the nickname)
    parts = full_name.split()
    return parts[-1].lower() if parts else full_lower


def match_game_odds(odds_data: List[Dict], away_name: str, home_name: str) -> Dict:
    """Match odds to a specific game with strict team matching"""
    result = {
        'spread_away': '-', 'spread_home': '-',
        'ml_away': '-', 'ml_home': '-',
        'total': '-',
        'open_spread': '-', 'spread_move': '-'
    }

    # Get nicknames for matching
    away_nick = get_team_nickname(away_name)
    home_nick = get_team_nickname(home_name)

    for game in odds_data:
        api_away = game.get('away_team', '')
        api_home = game.get('home_team', '')
        api_away_nick = get_team_nickname(api_away)
        api_home_nick = get_team_nickname(api_home)

        # Strict matching: both away AND home nicknames must match
        if api_away_nick == away_nick and api_home_nick == home_nick:
            for bm in game.get('bookmakers', [])[:1]:
                for market in bm.get('markets', []):
                    if market['key'] == 'spreads':
                        for o in market['outcomes']:
                            spread = o['point']
                            spread_str = f"{spread:+.1f}" if spread >= 0 else f"{spread:.1f}"
                            outcome_nick = get_team_nickname(o['name'])
                            if outcome_nick == home_nick:
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
                            outcome_nick = get_team_nickname(o['name'])
                            if outcome_nick == home_nick:
                                result['ml_home'] = ml_str
                            else:
                                result['ml_away'] = ml_str
            break

    return result

# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================

def is_valid_value(val) -> bool:
    """Check if a value is valid (not a placeholder)"""
    if val is None:
        return False
    if isinstance(val, str):
        val_str = val.strip()
        if val_str in ['', '-', 'TBD', 'N/A', 'null', 'None']:
            return False
    return True


def has_valid_odds(odds: dict) -> bool:
    """Check if odds dictionary has all required valid values"""
    required = ['spread_away', 'spread_home', 'ml_away', 'ml_home', 'total']
    for key in required:
        if not is_valid_value(odds.get(key)):
            return False
    return True


def validate_stat(val) -> str:
    """Return validated stat or empty string (for hiding)"""
    if not is_valid_value(val):
        return ''
    return str(val)


# =============================================================================
# STAT EXTRACTION - Comprehensive stats for each sport
# =============================================================================

def safe_num(val, decimals=1):
    """Safely convert to number"""
    if val is None or val == '' or val == '-':
        return '-'
    try:
        num = float(val)
        if decimals == 0:
            return str(int(num))
        return f"{num:.{decimals}f}"
    except:
        return str(val) if val else '-'

def safe_pct(val):
    """Format percentage"""
    if val is None or val == '' or val == '-':
        return '-'
    try:
        v = float(val)
        if v <= 1:
            return f"{v*100:.1f}%"
        return f"{v:.1f}%"
    except:
        return str(val) if val else '-'

def get_power_rating(record):
    """Calculate power rating from record"""
    try:
        parts = record.replace(' ', '').split('-')
        wins = int(parts[0])
        losses = int(parts[1])
        total = wins + losses
        if total > 0:
            return f"{(wins/total)*100:.1f}"
    except:
        pass
    return '-'

def format_top(val, games_played=1):
    """Format Time of Possession - handles seconds or MM:SS string"""
    if val is None or val == '' or val == '-':
        return '-'
    # If already in MM:SS format
    if isinstance(val, str) and ':' in val:
        return val
    try:
        # If it's seconds (could be total or avg per game)
        seconds = float(val)
        # If very large, it's probably total seconds for season - convert to per-game avg
        if seconds > 3600 and games_played > 0:  # More than 1 hour means season total
            seconds = seconds / games_played
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}:{secs:02d}"
    except:
        return str(val) if val else '-'

def calculate_ts_pct(ppg, fga, fta):
    """Calculate True Shooting Percentage: TS% = PTS / (2 * (FGA + 0.44 * FTA))"""
    try:
        pts = float(ppg)
        fga_val = float(fga)
        fta_val = float(fta)
        if fga_val + fta_val > 0:
            ts = pts / (2 * (fga_val + 0.44 * fta_val)) * 100
            return f"{ts:.1f}%"
    except:
        pass
    return '-'


def calculate_efg_pct(fgm, fga, three_pm):
    """Calculate Effective FG%: eFG% = (FGM + 0.5 * 3PM) / FGA"""
    try:
        fgm_val = float(fgm)
        fga_val = float(fga)
        three_val = float(three_pm)
        if fga_val > 0:
            efg = (fgm_val + 0.5 * three_val) / fga_val * 100
            return f"{efg:.1f}%"
    except:
        pass
    return '-'


def extract_nba_stats(raw: Dict, record: str) -> Dict:
    """Extract comprehensive NBA stats"""
    # Get base stats for calculations
    ppg = raw.get('avgPoints', raw.get('pointsPerGame', 0))
    fga = raw.get('avgFieldGoalsAttempted', 0)
    fta = raw.get('avgFreeThrowsAttempted', 0)
    fgm = raw.get('avgFieldGoalsMade', 0)
    three_pm = raw.get('avgThreePointFieldGoalsMade', 0)

    return {
        # Offense
        'ppg': safe_num(ppg),
        'fg_pct': safe_pct(raw.get('fieldGoalPct')),
        'three_pct': safe_pct(raw.get('threePointPct', raw.get('threePointFieldGoalPct'))),
        'ft_pct': safe_pct(raw.get('freeThrowPct')),
        'ast': safe_num(raw.get('avgAssists', raw.get('assistsPerGame'))),
        'reb': safe_num(raw.get('avgRebounds', raw.get('reboundsPerGame'))),
        'oreb': safe_num(raw.get('avgOffensiveRebounds', raw.get('offReboundsPerGame'))),
        # Defense
        'opp_ppg': safe_num(raw.get('avgPointsAgainst', raw.get('oppPointsPerGame'))),
        'stl': safe_num(raw.get('avgSteals', raw.get('stealsPerGame'))),
        'blk': safe_num(raw.get('avgBlocks', raw.get('blocksPerGame'))),
        'dreb': safe_num(raw.get('avgDefensiveRebounds', raw.get('defReboundsPerGame'))),
        # Efficiency
        'to': safe_num(raw.get('avgTurnovers', raw.get('turnoversPerGame'))),
        'ast_to': safe_num(raw.get('assistTurnoverRatio')),
        'pf': safe_num(raw.get('avgFouls', raw.get('foulsPerGame'))),
        # Shooting - Advanced (calculated)
        'two_pct': safe_pct(raw.get('twoPointFieldGoalPct')),
        'efg': calculate_efg_pct(fgm, fga, three_pm),
        'ts': calculate_ts_pct(ppg, fga, fta),
        # Per Game
        'fgm': safe_num(raw.get('avgFieldGoalsMade')),
        'fga': safe_num(raw.get('avgFieldGoalsAttempted')),
        '3pm': safe_num(raw.get('avgThreePointFieldGoalsMade')),
        '3pa': safe_num(raw.get('avgThreePointFieldGoalsAttempted')),
        'ftm': safe_num(raw.get('avgFreeThrowsMade')),
        'fta': safe_num(raw.get('avgFreeThrowsAttempted')),
        'pwr': get_power_rating(record),
    }

def get_nfl_games_played(record: str) -> int:
    """Calculate games played from NFL record (W-L or W-L-T)"""
    try:
        parts = record.replace(' ', '').split('-')
        return sum(int(p) for p in parts if p.isdigit())
    except:
        return 1  # Avoid division by zero

def extract_nfl_stats(raw: Dict, record: str) -> Dict:
    """Extract comprehensive NFL stats"""
    # Calculate games played for per-game stats
    games = get_nfl_games_played(record)

    # Calculate yards per play if not provided
    total_yards = raw.get('totalYards', 0)
    total_plays = raw.get('totalOffensivePlays', 1)
    ypp_calc = '-'
    try:
        if total_yards and total_plays:
            ypp_calc = f"{float(total_yards) / float(total_plays):.2f}"
    except:
        pass

    # Get TOP - ESPN provides possessionTimeSeconds as season total
    top_val = raw.get('avgTimeOfPossession', raw.get('possessionTime', raw.get('possessionTimeSeconds')))

    return {
        # Offense
        'ppg': safe_num(raw.get('totalPointsPerGame', raw.get('avgPoints'))),
        'ypg': safe_num(raw.get('yardsPerGame', raw.get('totalYardsPerGame')), 0),
        'pass_ypg': safe_num(raw.get('netPassingYardsPerGame', raw.get('passingYardsPerGame')), 0),
        'rush_ypg': safe_num(raw.get('rushingYardsPerGame'), 0),
        'comp_pct': safe_pct(raw.get('completionPct')),
        'qbr': safe_num(raw.get('QBRating')),
        # Defense
        'opp_ppg': safe_num(raw.get('avgPointsAgainst', raw.get('pointsAgainstPerGame'))),
        'opp_ypg': safe_num(raw.get('yardsAllowedPerGame'), 0),
        'sacks': safe_num(raw.get('sacks'), 0),
        'ints': safe_num(raw.get('interceptions'), 0),
        'tfl': safe_num(raw.get('tacklesForLoss'), 0),
        'ff': safe_num(raw.get('fumblesForced'), 0),
        'pd': safe_num(raw.get('passesDefended'), 0),  # Passes Defended
        # Efficiency
        'ypp': safe_num(raw.get('yardsPerPlay')) if raw.get('yardsPerPlay') else ypp_calc,
        'ypa': safe_num(raw.get('yardsPerPassAttempt'), 1),
        'ypr': safe_num(raw.get('yardsPerRushAttempt'), 1),
        'ypc': safe_num(raw.get('yardsPerReception'), 1),  # Yards Per Catch
        # Situational
        'third_pct': safe_pct(raw.get('thirdDownConvPct')),
        'fourth_pct': safe_pct(raw.get('fourthDownConvPct')),
        'rz_pct': safe_pct(raw.get('redzoneTouchdownPct', raw.get('redzoneEfficiencyPct'))),
        'rz_score': safe_pct(raw.get('redzoneScoringPct')),  # RZ Scoring %
        'to_diff': raw.get('turnOverDifferential', raw.get('takeawayGiveawayDiff', '-')),
        'top': format_top(top_val, games),
        # Special Teams
        'fg_pct': safe_pct(raw.get('fieldGoalPct')),
        'punt_avg': safe_num(raw.get('grossAvgPuntYards'), 1),
        'kr_avg': safe_num(raw.get('yardsPerKickReturn'), 1),
        # First Downs
        'first_downs': safe_num(raw.get('firstDowns'), 0),
        'rush_td': safe_num(raw.get('rushingTouchdowns'), 0),
        'pass_td': safe_num(raw.get('passingTouchdowns'), 0),
        'penalties': safe_num(raw.get('totalPenalties'), 0),
        'pen_yds': safe_num(raw.get('totalPenaltyYards'), 0),
        'pwr': get_power_rating(record),
    }

def get_games_played(record: str) -> int:
    """Calculate games played from record (W-L or W-L-OTL)"""
    try:
        parts = record.replace(' ', '').split('-')
        return sum(int(p) for p in parts if p.isdigit())
    except:
        return 1  # Avoid division by zero

def extract_nhl_stats(raw: Dict, record: str) -> Dict:
    """Extract comprehensive NHL stats"""
    games = get_games_played(record)

    # Goals - ESPN returns total, convert to per-game
    gf_total = raw.get('goals', raw.get('goalsFor', 0))
    ga_total = raw.get('goalsAgainst', 0)
    try:
        gf = f"{float(gf_total) / games:.1f}" if games > 0 else '-'
    except:
        gf = safe_num(raw.get('goalsPerGame', raw.get('avgGoals')))

    try:
        ga = f"{float(ga_total) / games:.1f}" if games > 0 else '-'
    except:
        ga = safe_num(raw.get('avgGoalsAgainst', raw.get('goalsAgainstPerGame')))

    # Calculate goal differential
    gd = '-'
    try:
        gd_val = float(gf) - float(ga)
        gd = f"{gd_val:+.1f}"
    except:
        pass

    # Shots - may be total, convert to per-game
    sog_total = raw.get('shotsTotal', raw.get('shots', 0))
    try:
        sog = f"{float(sog_total) / games:.1f}" if games > 0 and sog_total else '-'
    except:
        sog = safe_num(raw.get('shotsPerGame', raw.get('avgShotsPerGame')))

    # Shots against
    sa_total = raw.get('shotsAgainst', 0)
    try:
        sa = f"{float(sa_total) / games:.1f}" if games > 0 and sa_total else '-'
    except:
        sa = safe_num(raw.get('shotsAgainstPerGame'))

    # PIM - total, convert to per-game
    pim_total = raw.get('penaltyMinutes', 0)
    try:
        pim = f"{float(pim_total) / games:.1f}" if games > 0 and pim_total else '-'
    except:
        pim = safe_num(raw.get('penaltyMinutesPerGame', raw.get('pimPerGame')))

    # Additional calculations
    points = raw.get('points', 0)
    try:
        pts_pg = f"{float(points) / games:.1f}" if games > 0 and points else '-'
    except:
        pts_pg = '-'

    return {
        # Offense
        'gf': gf,
        'sog': sog if sog != '-' else safe_num(raw.get('shotsPerGame')),
        'ppg': safe_num(raw.get('powerPlayGoals'), 0),
        'pp_pct': safe_pct(raw.get('powerPlayPct')),
        'shoot_pct': safe_pct(raw.get('shootingPct', raw.get('shootingPctg'))),  # ESPN uses shootingPct
        'fow_pct': safe_pct(raw.get('faceoffPercent', raw.get('faceoffWinPct'))),  # ESPN uses faceoffPercent
        'assists': safe_num(raw.get('assists'), 0),
        'pts_total': safe_num(raw.get('points'), 0),  # Total team points
        # Defense
        'ga': ga,
        'gd': gd,
        'pk_pct': safe_pct(raw.get('penaltyKillPct')),
        'sv_pct': safe_pct(raw.get('savePct')),
        'sa': sa if sa != '-' else safe_num(raw.get('shotsAgainstPerGame'), 0),
        'shg': safe_num(raw.get('shortHandedGoals'), 0),
        'sha': safe_num(raw.get('shortHandedAssists'), 0),
        # Situational
        'pim': pim,
        'plus_minus': raw.get('plusMinus', '-'),
        'gwg': safe_num(raw.get('gameWinningGoals'), 0),
        'otl': safe_num(raw.get('overtimeLosses', raw.get('otLosses')), 0),
        # Shootout
        'so_pct': safe_pct(raw.get('shootoutShotPct')),
        'so_sv_pct': safe_pct(raw.get('shootoutSavePct')),
        # Face-offs
        'fow': safe_num(raw.get('faceoffsWon'), 0),
        'fol': safe_num(raw.get('faceoffsLost'), 0),
        'pwr': get_power_rating(record),
    }

def extract_ncaab_stats(raw: Dict, record: str) -> Dict:
    """Extract comprehensive NCAAB stats"""
    return extract_nba_stats(raw, record)  # Same structure as NBA

def extract_ncaaf_stats(raw: Dict, record: str) -> Dict:
    """Extract comprehensive NCAAF stats"""
    return extract_nfl_stats(raw, record)  # Same structure as NFL

# =============================================================================
# HTML GENERATION - 4-Section Layout
# =============================================================================

def generate_game_card_nfl(game: Dict, sport: str = 'NFL') -> str:
    """Generate NFL/NCAAF game card with 4-section layout"""
    away = game['away']
    home = game['home']
    odds = game['odds']

    # Format injuries
    away_inj_html = format_injuries_html(away.get('injuries', []), away['abbr'])
    home_inj_html = format_injuries_html(home.get('injuries', []), home['abbr'])

    # Get correct logo URLs based on sport
    away_logo = get_logo_url(sport, away['abbr'], away.get('team_id', ''))
    home_logo = get_logo_url(sport, home['abbr'], home.get('team_id', ''))

    # Only include betting lines section if we have valid odds (NO PLACEHOLDERS)
    betting_lines_html = ''
    if has_valid_odds(odds):
        betting_lines_html = f'''
        <!-- SECTION 1: BETTING LINES -->
        <div class="section betting-lines">
            <div class="section-title">BETTING LINES</div>
            <table class="lines-table">
                <thead>
                    <tr>
                        <th class="team-col">TEAM</th>
                        <th>SPREAD</th>
                        <th>ML</th>
                        <th>O/U</th>
                    </tr>
                </thead>
                <tbody>
                    <tr class="away-row">
                        <td class="team-col">
                            <img src="{away_logo}" class="team-logo" onerror="this.style.display='none'">
                            <span class="team-name">{away['abbr']}</span>
                            <span class="team-record">{away['record']}</span>
                        </td>
                        <td class="spread">{odds['spread_away']}</td>
                        <td class="ml">{odds['ml_away']}</td>
                        <td class="total">O {odds['total']}</td>
                    </tr>
                    <tr class="home-row">
                        <td class="team-col">
                            <img src="{home_logo}" class="team-logo" onerror="this.style.display='none'">
                            <span class="team-name">{home['abbr']}</span>
                            <span class="team-record">{home['record']}</span>
                        </td>
                        <td class="spread">{odds['spread_home']}</td>
                        <td class="ml">{odds['ml_home']}</td>
                        <td class="total">U {odds['total']}</td>
                    </tr>
                </tbody>
            </table>
        </div>'''
    else:
        # Show teams info without betting lines
        betting_lines_html = f'''
        <!-- TEAMS INFO (No betting lines available) -->
        <div class="section teams-info">
            <div class="section-title">MATCHUP</div>
            <table class="lines-table">
                <thead>
                    <tr>
                        <th class="team-col">TEAM</th>
                        <th>RECORD</th>
                    </tr>
                </thead>
                <tbody>
                    <tr class="away-row">
                        <td class="team-col">
                            <img src="{away_logo}" class="team-logo" onerror="this.style.display='none'">
                            <span class="team-name">{away['abbr']}</span>
                        </td>
                        <td>{away['record']}</td>
                    </tr>
                    <tr class="home-row">
                        <td class="team-col">
                            <img src="{home_logo}" class="team-logo" onerror="this.style.display='none'">
                            <span class="team-name">{home['abbr']}</span>
                        </td>
                        <td>{home['record']}</td>
                    </tr>
                </tbody>
            </table>
        </div>'''

    return f'''
    <div class="game-card">
        <div class="game-header">
            <span class="game-time">{game['time']}</span>
            <span class="game-venue">{game['venue']}</span>
            <span class="game-network">{game['network']}</span>
        </div>
        {betting_lines_html}

        <!-- SECTION 2: OFFENSE vs DEFENSE -->
        <div class="stats-grid">
            <div class="section offense">
                <div class="section-title">OFFENSE</div>
                <table class="stats-table">
                    <thead>
                        <tr><th></th><th>PPG</th><th>YPG</th><th>PASS</th><th>RUSH</th><th>1stD</th><th>3RD%</th></tr>
                    </thead>
                    <tbody>
                        <tr><td class="team-abbr">{away['abbr']}</td><td>{away['stats']['ppg']}</td><td>{away['stats']['ypg']}</td><td>{away['stats']['pass_ypg']}</td><td>{away['stats']['rush_ypg']}</td><td>{away['stats']['first_downs']}</td><td>{away['stats']['third_pct']}</td></tr>
                        <tr><td class="team-abbr">{home['abbr']}</td><td>{home['stats']['ppg']}</td><td>{home['stats']['ypg']}</td><td>{home['stats']['pass_ypg']}</td><td>{home['stats']['rush_ypg']}</td><td>{home['stats']['first_downs']}</td><td>{home['stats']['third_pct']}</td></tr>
                    </tbody>
                </table>
            </div>
            <div class="section defense">
                <div class="section-title">DEFENSE</div>
                <table class="stats-table">
                    <thead>
                        <tr><th></th><th>SACK</th><th>INT</th><th>TFL</th><th>FF</th><th>PD</th><th>PEN</th></tr>
                    </thead>
                    <tbody>
                        <tr><td class="team-abbr">{away['abbr']}</td><td>{away['stats']['sacks']}</td><td>{away['stats']['ints']}</td><td>{away['stats']['tfl']}</td><td>{away['stats']['ff']}</td><td>{away['stats']['pd']}</td><td>{away['stats']['penalties']}</td></tr>
                        <tr><td class="team-abbr">{home['abbr']}</td><td>{home['stats']['sacks']}</td><td>{home['stats']['ints']}</td><td>{home['stats']['tfl']}</td><td>{home['stats']['ff']}</td><td>{home['stats']['pd']}</td><td>{home['stats']['penalties']}</td></tr>
                    </tbody>
                </table>
            </div>
        </div>

        <!-- SECTION 3: EFFICIENCY vs SITUATIONAL -->
        <div class="stats-grid">
            <div class="section efficiency">
                <div class="section-title">EFFICIENCY</div>
                <table class="stats-table">
                    <thead>
                        <tr><th></th><th>CMP%</th><th>YPA</th><th>YPC</th><th>YPR</th><th>QBR</th><th>FG%</th></tr>
                    </thead>
                    <tbody>
                        <tr><td class="team-abbr">{away['abbr']}</td><td>{away['stats']['comp_pct']}</td><td>{away['stats']['ypa']}</td><td>{away['stats']['ypc']}</td><td>{away['stats']['ypr']}</td><td>{away['stats']['qbr']}</td><td>{away['stats']['fg_pct']}</td></tr>
                        <tr><td class="team-abbr">{home['abbr']}</td><td>{home['stats']['comp_pct']}</td><td>{home['stats']['ypa']}</td><td>{home['stats']['ypc']}</td><td>{home['stats']['ypr']}</td><td>{home['stats']['qbr']}</td><td>{home['stats']['fg_pct']}</td></tr>
                    </tbody>
                </table>
            </div>
            <div class="section situational">
                <div class="section-title">SITUATIONAL</div>
                <table class="stats-table">
                    <thead>
                        <tr><th></th><th>RZ%</th><th>4TH%</th><th>TO+/-</th><th>TOP</th><th>FG%</th><th>PWR</th></tr>
                    </thead>
                    <tbody>
                        <tr><td class="team-abbr">{away['abbr']}</td><td>{away['stats']['rz_pct']}</td><td>{away['stats']['fourth_pct']}</td><td>{away['stats']['to_diff']}</td><td>{away['stats']['top']}</td><td>{away['stats']['fg_pct']}</td><td>{away['stats']['pwr']}</td></tr>
                        <tr><td class="team-abbr">{home['abbr']}</td><td>{home['stats']['rz_pct']}</td><td>{home['stats']['fourth_pct']}</td><td>{home['stats']['to_diff']}</td><td>{home['stats']['top']}</td><td>{home['stats']['fg_pct']}</td><td>{home['stats']['pwr']}</td></tr>
                    </tbody>
                </table>
            </div>
        </div>

        <!-- SECTION 4: TRENDS BAR -->
        <div class="trends-bar">
            <span class="trend-item">🏥 {away_inj_html} | {home_inj_html}</span>
        </div>
    </div>
    '''

def generate_game_card_nba(game: Dict, sport: str = 'NBA') -> str:
    """Generate NBA/NCAAB game card with 4-section layout"""
    away = game['away']
    home = game['home']
    odds = game['odds']

    # Format injuries
    away_inj_html = format_injuries_html(away.get('injuries', []), away['abbr'])
    home_inj_html = format_injuries_html(home.get('injuries', []), home['abbr'])

    # Get correct logo URLs based on sport
    away_logo = get_logo_url(sport, away['abbr'], away.get('team_id', ''))
    home_logo = get_logo_url(sport, home['abbr'], home.get('team_id', ''))

    # Only include betting lines section if we have valid odds (NO PLACEHOLDERS)
    betting_lines_html = ''
    if has_valid_odds(odds):
        betting_lines_html = f'''
        <!-- SECTION 1: BETTING LINES -->
        <div class="section betting-lines">
            <div class="section-title">BETTING LINES</div>
            <table class="lines-table">
                <thead>
                    <tr>
                        <th class="team-col">TEAM</th>
                        <th>SPREAD</th>
                        <th>ML</th>
                        <th>O/U</th>
                    </tr>
                </thead>
                <tbody>
                    <tr class="away-row">
                        <td class="team-col">
                            <img src="{away_logo}" class="team-logo" onerror="this.style.display='none'">
                            <span class="team-name">{away['abbr']}</span>
                            <span class="team-record">{away['record']}</span>
                        </td>
                        <td class="spread">{odds['spread_away']}</td>
                        <td class="ml">{odds['ml_away']}</td>
                        <td class="total">O {odds['total']}</td>
                    </tr>
                    <tr class="home-row">
                        <td class="team-col">
                            <img src="{home_logo}" class="team-logo" onerror="this.style.display='none'">
                            <span class="team-name">{home['abbr']}</span>
                            <span class="team-record">{home['record']}</span>
                        </td>
                        <td class="spread">{odds['spread_home']}</td>
                        <td class="ml">{odds['ml_home']}</td>
                        <td class="total">U {odds['total']}</td>
                    </tr>
                </tbody>
            </table>
        </div>'''
    else:
        # Show teams info without betting lines
        betting_lines_html = f'''
        <!-- TEAMS INFO (No betting lines available) -->
        <div class="section teams-info">
            <div class="section-title">MATCHUP</div>
            <table class="lines-table">
                <thead>
                    <tr>
                        <th class="team-col">TEAM</th>
                        <th>RECORD</th>
                    </tr>
                </thead>
                <tbody>
                    <tr class="away-row">
                        <td class="team-col">
                            <img src="{away_logo}" class="team-logo" onerror="this.style.display='none'">
                            <span class="team-name">{away['abbr']}</span>
                        </td>
                        <td>{away['record']}</td>
                    </tr>
                    <tr class="home-row">
                        <td class="team-col">
                            <img src="{home_logo}" class="team-logo" onerror="this.style.display='none'">
                            <span class="team-name">{home['abbr']}</span>
                        </td>
                        <td>{home['record']}</td>
                    </tr>
                </tbody>
            </table>
        </div>'''

    return f'''
    <div class="game-card">
        <div class="game-header">
            <span class="game-time">{game['time']}</span>
            <span class="game-venue">{game['venue']}</span>
            <span class="game-network">{game['network']}</span>
        </div>
        {betting_lines_html}

        <!-- SECTION 2: OFFENSE vs DEFENSE -->
        <div class="stats-grid">
            <div class="section offense">
                <div class="section-title">OFFENSE</div>
                <table class="stats-table">
                    <thead>
                        <tr><th></th><th>PPG</th><th>FG%</th><th>3P%</th><th>FT%</th><th>AST</th><th>REB</th></tr>
                    </thead>
                    <tbody>
                        <tr><td class="team-abbr">{away['abbr']}</td><td>{away['stats']['ppg']}</td><td>{away['stats']['fg_pct']}</td><td>{away['stats']['three_pct']}</td><td>{away['stats']['ft_pct']}</td><td>{away['stats']['ast']}</td><td>{away['stats']['reb']}</td></tr>
                        <tr><td class="team-abbr">{home['abbr']}</td><td>{home['stats']['ppg']}</td><td>{home['stats']['fg_pct']}</td><td>{home['stats']['three_pct']}</td><td>{home['stats']['ft_pct']}</td><td>{home['stats']['ast']}</td><td>{home['stats']['reb']}</td></tr>
                    </tbody>
                </table>
            </div>
            <div class="section defense">
                <div class="section-title">DEFENSE</div>
                <table class="stats-table">
                    <thead>
                        <tr><th></th><th>STL</th><th>BLK</th><th>DREB</th><th>OREB</th><th>TO</th><th>PF</th></tr>
                    </thead>
                    <tbody>
                        <tr><td class="team-abbr">{away['abbr']}</td><td>{away['stats']['stl']}</td><td>{away['stats']['blk']}</td><td>{away['stats']['dreb']}</td><td>{away['stats']['oreb']}</td><td>{away['stats']['to']}</td><td>{away['stats']['pf']}</td></tr>
                        <tr><td class="team-abbr">{home['abbr']}</td><td>{home['stats']['stl']}</td><td>{home['stats']['blk']}</td><td>{home['stats']['dreb']}</td><td>{home['stats']['oreb']}</td><td>{home['stats']['to']}</td><td>{home['stats']['pf']}</td></tr>
                    </tbody>
                </table>
            </div>
        </div>

        <!-- SECTION 3: SHOOTING vs EFFICIENCY -->
        <div class="stats-grid">
            <div class="section efficiency">
                <div class="section-title">SHOOTING</div>
                <table class="stats-table">
                    <thead>
                        <tr><th></th><th>FGM</th><th>FGA</th><th>3PM</th><th>3PA</th><th>2P%</th><th>eFG%</th></tr>
                    </thead>
                    <tbody>
                        <tr><td class="team-abbr">{away['abbr']}</td><td>{away['stats']['fgm']}</td><td>{away['stats']['fga']}</td><td>{away['stats']['3pm']}</td><td>{away['stats']['3pa']}</td><td>{away['stats']['two_pct']}</td><td>{away['stats']['efg']}</td></tr>
                        <tr><td class="team-abbr">{home['abbr']}</td><td>{home['stats']['fgm']}</td><td>{home['stats']['fga']}</td><td>{home['stats']['3pm']}</td><td>{home['stats']['3pa']}</td><td>{home['stats']['two_pct']}</td><td>{home['stats']['efg']}</td></tr>
                    </tbody>
                </table>
            </div>
            <div class="section situational">
                <div class="section-title">EFFICIENCY</div>
                <table class="stats-table">
                    <thead>
                        <tr><th></th><th>A/TO</th><th>FTM</th><th>FTA</th><th>eFG%</th><th>TS%</th><th>PWR</th></tr>
                    </thead>
                    <tbody>
                        <tr><td class="team-abbr">{away['abbr']}</td><td>{away['stats']['ast_to']}</td><td>{away['stats']['ftm']}</td><td>{away['stats']['fta']}</td><td>{away['stats']['efg']}</td><td>{away['stats']['ts']}</td><td>{away['stats']['pwr']}</td></tr>
                        <tr><td class="team-abbr">{home['abbr']}</td><td>{home['stats']['ast_to']}</td><td>{home['stats']['ftm']}</td><td>{home['stats']['fta']}</td><td>{home['stats']['efg']}</td><td>{home['stats']['ts']}</td><td>{home['stats']['pwr']}</td></tr>
                    </tbody>
                </table>
            </div>
        </div>

        <!-- SECTION 4: TRENDS BAR -->
        <div class="trends-bar">
            <span class="trend-item">🏥 {away_inj_html} | {home_inj_html}</span>
        </div>
    </div>
    '''

def generate_game_card_nhl(game: Dict) -> str:
    """Generate NHL game card with 4-section layout"""
    away = game['away']
    home = game['home']
    odds = game['odds']

    # Format injuries
    away_inj_html = format_injuries_html(away.get('injuries', []), away['abbr'])
    home_inj_html = format_injuries_html(home.get('injuries', []), home['abbr'])

    # Only include betting lines section if we have valid odds (NO PLACEHOLDERS)
    betting_lines_html = ''
    if has_valid_odds(odds):
        betting_lines_html = f'''
        <!-- SECTION 1: BETTING LINES -->
        <div class="section betting-lines">
            <div class="section-title">BETTING LINES</div>
            <table class="lines-table">
                <thead>
                    <tr>
                        <th class="team-col">TEAM</th>
                        <th>PUCK LINE</th>
                        <th>ML</th>
                        <th>O/U</th>
                    </tr>
                </thead>
                <tbody>
                    <tr class="away-row">
                        <td class="team-col">
                            <img src="https://a.espncdn.com/i/teamlogos/nhl/500/scoreboard/{away['abbr'].lower()}.png" class="team-logo" onerror="this.style.display='none'">
                            <span class="team-name">{away['abbr']}</span>
                            <span class="team-record">{away['record']}</span>
                        </td>
                        <td class="spread">{odds['spread_away']}</td>
                        <td class="ml">{odds['ml_away']}</td>
                        <td class="total">O {odds['total']}</td>
                    </tr>
                    <tr class="home-row">
                        <td class="team-col">
                            <img src="https://a.espncdn.com/i/teamlogos/nhl/500/scoreboard/{home['abbr'].lower()}.png" class="team-logo" onerror="this.style.display='none'">
                            <span class="team-name">{home['abbr']}</span>
                            <span class="team-record">{home['record']}</span>
                        </td>
                        <td class="spread">{odds['spread_home']}</td>
                        <td class="ml">{odds['ml_home']}</td>
                        <td class="total">U {odds['total']}</td>
                    </tr>
                </tbody>
            </table>
        </div>'''
    else:
        # Show teams info without betting lines
        betting_lines_html = f'''
        <!-- TEAMS INFO (No betting lines available) -->
        <div class="section teams-info">
            <div class="section-title">MATCHUP</div>
            <table class="lines-table">
                <thead>
                    <tr>
                        <th class="team-col">TEAM</th>
                        <th>RECORD</th>
                    </tr>
                </thead>
                <tbody>
                    <tr class="away-row">
                        <td class="team-col">
                            <img src="https://a.espncdn.com/i/teamlogos/nhl/500/scoreboard/{away['abbr'].lower()}.png" class="team-logo" onerror="this.style.display='none'">
                            <span class="team-name">{away['abbr']}</span>
                        </td>
                        <td>{away['record']}</td>
                    </tr>
                    <tr class="home-row">
                        <td class="team-col">
                            <img src="https://a.espncdn.com/i/teamlogos/nhl/500/scoreboard/{home['abbr'].lower()}.png" class="team-logo" onerror="this.style.display='none'">
                            <span class="team-name">{home['abbr']}</span>
                        </td>
                        <td>{home['record']}</td>
                    </tr>
                </tbody>
            </table>
        </div>'''

    return f'''
    <div class="game-card">
        <div class="game-header">
            <span class="game-time">{game['time']}</span>
            <span class="game-venue">{game['venue']}</span>
            <span class="game-network">{game['network']}</span>
        </div>
        {betting_lines_html}

        <!-- SECTION 2: OFFENSE vs DEFENSE -->
        <div class="stats-grid">
            <div class="section offense">
                <div class="section-title">OFFENSE</div>
                <table class="stats-table">
                    <thead>
                        <tr><th></th><th>GF</th><th>SOG</th><th>S%</th><th>PPG</th><th>AST</th><th>PTS</th></tr>
                    </thead>
                    <tbody>
                        <tr><td class="team-abbr">{away['abbr']}</td><td>{away['stats']['gf']}</td><td>{away['stats']['sog']}</td><td>{away['stats']['shoot_pct']}</td><td>{away['stats']['ppg']}</td><td>{away['stats']['assists']}</td><td>{away['stats']['pts_total']}</td></tr>
                        <tr><td class="team-abbr">{home['abbr']}</td><td>{home['stats']['gf']}</td><td>{home['stats']['sog']}</td><td>{home['stats']['shoot_pct']}</td><td>{home['stats']['ppg']}</td><td>{home['stats']['assists']}</td><td>{home['stats']['pts_total']}</td></tr>
                    </tbody>
                </table>
            </div>
            <div class="section defense">
                <div class="section-title">DEFENSE</div>
                <table class="stats-table">
                    <thead>
                        <tr><th></th><th>GA</th><th>SA</th><th>SV%</th><th>SHG</th><th>GD</th><th>PIM</th></tr>
                    </thead>
                    <tbody>
                        <tr><td class="team-abbr">{away['abbr']}</td><td>{away['stats']['ga']}</td><td>{away['stats']['sa']}</td><td>{away['stats']['sv_pct']}</td><td>{away['stats']['shg']}</td><td>{away['stats']['gd']}</td><td>{away['stats']['pim']}</td></tr>
                        <tr><td class="team-abbr">{home['abbr']}</td><td>{home['stats']['ga']}</td><td>{home['stats']['sa']}</td><td>{home['stats']['sv_pct']}</td><td>{home['stats']['shg']}</td><td>{home['stats']['gd']}</td><td>{home['stats']['pim']}</td></tr>
                    </tbody>
                </table>
            </div>
        </div>

        <!-- SECTION 3: SITUATIONAL -->
        <div class="stats-grid">
            <div class="section efficiency">
                <div class="section-title">FACE-OFFS & SPECIAL TEAMS</div>
                <table class="stats-table">
                    <thead>
                        <tr><th></th><th>FO%</th><th>FOW</th><th>FOL</th><th>SHA</th><th>+/-</th><th>OTL</th></tr>
                    </thead>
                    <tbody>
                        <tr><td class="team-abbr">{away['abbr']}</td><td>{away['stats']['fow_pct']}</td><td>{away['stats']['fow']}</td><td>{away['stats']['fol']}</td><td>{away['stats']['sha']}</td><td>{away['stats']['plus_minus']}</td><td>{away['stats']['otl']}</td></tr>
                        <tr><td class="team-abbr">{home['abbr']}</td><td>{home['stats']['fow_pct']}</td><td>{home['stats']['fow']}</td><td>{home['stats']['fol']}</td><td>{home['stats']['sha']}</td><td>{home['stats']['plus_minus']}</td><td>{home['stats']['otl']}</td></tr>
                    </tbody>
                </table>
            </div>
            <div class="section situational">
                <div class="section-title">CLUTCH & POWER</div>
                <table class="stats-table">
                    <thead>
                        <tr><th></th><th>GWG</th><th>PPG</th><th>SHG</th><th>PWR</th><th>REC</th></tr>
                    </thead>
                    <tbody>
                        <tr><td class="team-abbr">{away['abbr']}</td><td>{away['stats']['gwg']}</td><td>{away['stats']['ppg']}</td><td>{away['stats']['shg']}</td><td>{away['stats']['pwr']}</td><td>{away['record']}</td></tr>
                        <tr><td class="team-abbr">{home['abbr']}</td><td>{home['stats']['gwg']}</td><td>{home['stats']['ppg']}</td><td>{home['stats']['shg']}</td><td>{home['stats']['pwr']}</td><td>{home['record']}</td></tr>
                    </tbody>
                </table>
            </div>
        </div>

        <!-- SECTION 4: TRENDS BAR -->
        <div class="trends-bar">
            <span class="trend-item">🏥 {away_inj_html} | {home_inj_html}</span>
        </div>
    </div>
    '''

def get_logo_url(sport: str, abbr: str, team_id: str = '') -> str:
    """Get correct ESPN logo URL for team based on sport"""
    abbr_lower = abbr.lower()
    if sport == 'NFL':
        return f"https://a.espncdn.com/i/teamlogos/nfl/500/scoreboard/{abbr_lower}.png"
    elif sport == 'NBA':
        return f"https://a.espncdn.com/i/teamlogos/nba/500/scoreboard/{abbr_lower}.png"
    elif sport == 'NHL':
        return f"https://a.espncdn.com/i/teamlogos/nhl/500/scoreboard/{abbr_lower}.png"
    elif sport == 'NCAAF':
        # College football uses team ID for logos
        if team_id:
            return f"https://a.espncdn.com/i/teamlogos/ncaa/500/{team_id}.png"
        return f"https://a.espncdn.com/i/teamlogos/ncaa/500/{abbr_lower}.png"
    elif sport == 'NCAAB':
        # College basketball uses team ID for logos
        if team_id:
            return f"https://a.espncdn.com/i/teamlogos/ncaa/500/{team_id}.png"
        return f"https://a.espncdn.com/i/teamlogos/ncaa/500/{abbr_lower}.png"
    return ""

def generate_game_card(game: Dict, sport: str) -> str:
    """Route to sport-specific card generator"""
    if sport == 'NFL':
        return generate_game_card_nfl(game, 'NFL')
    elif sport == 'NCAAF':
        return generate_game_card_nfl(game, 'NCAAF')
    elif sport == 'NBA':
        return generate_game_card_nba(game, 'NBA')
    elif sport == 'NCAAB':
        return generate_game_card_nba(game, 'NCAAB')
    elif sport == 'NHL':
        return generate_game_card_nhl(game)
    return ''

# =============================================================================
# PAGE GENERATION
# =============================================================================

def generate_page(all_games: Dict[str, List], date_str: str) -> str:
    """Generate complete HTML page"""

    # Get archive dates for calendar
    archive_dates_json = get_archive_dates_json()

    # Build tabs and sections
    tab_buttons = ""
    sport_sections = ""
    sport_order = ['NBA', 'NFL', 'NHL', 'NCAAB', 'NCAAF']

    for i, sport in enumerate(sport_order):
        games = all_games.get(sport, [])
        active = "active" if i == 0 else ""
        count = len(games)

        tab_buttons += f'<button class="tab-btn {active}" data-sport="{sport.lower()}">{sport} <span class="count">({count})</span></button>\n'

        if not games:
            sport_sections += f'''
                <div class="sport-section {active}" id="{sport.lower()}-section">
                    <div class="no-games">No {sport} games scheduled for today</div>
                </div>
            '''
            continue

        cards_html = ""
        for game in games:
            cards_html += generate_game_card(game, sport)

        sport_sections += f'''
            <div class="sport-section {active}" id="{sport.lower()}-section">
                {cards_html}
            </div>
        '''

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Handicapping Hub - {date_str} | BetLegend</title>
    <meta name="description" content="The best handicapping hub on the internet. Advanced stats, betting lines, and analysis for NBA, NFL, NHL, NCAAB, and NCAAF.">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        body {{
            font-family: 'Inter', -apple-system, sans-serif;
            background: #f0f2f5;
            color: #1a1a2e;
            line-height: 1.4;
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

        /* Header */
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
        .header .subtitle {{ opacity: 0.9; font-size: 0.95rem; }}

        /* Container */
        .container {{
            max-width: 1200px;
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
        .tab-btn .count {{ opacity: 0.7; font-weight: 500; }}

        /* Sport Sections */
        .sport-section {{ display: none; }}
        .sport-section.active {{ display: block; }}
        .no-games {{
            background: white;
            padding: 40px;
            text-align: center;
            border-radius: 10px;
            color: #666;
        }}

        /* Game Card */
        .game-card {{
            background: white;
            border-radius: 12px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.08);
            overflow: hidden;
        }}

        .game-header {{
            background: #1a365d;
            color: white;
            padding: 12px 16px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.85rem;
            font-weight: 600;
        }}
        .game-time {{ color: #fd5000; }}
        .game-venue {{ opacity: 0.9; }}
        .game-network {{
            background: rgba(255,255,255,0.2);
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 0.75rem;
        }}

        /* Section Styling */
        .section {{
            padding: 12px 16px;
            border-bottom: 1px solid #eee;
        }}
        .section:last-child {{ border-bottom: none; }}
        .section-title {{
            font-size: 0.7rem;
            font-weight: 700;
            color: #1a365d;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 8px;
            padding-bottom: 6px;
            border-bottom: 2px solid #fd5000;
            display: inline-block;
        }}

        /* Stats Grid */
        .stats-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 0;
            border-bottom: 1px solid #eee;
        }}
        .stats-grid .section {{
            border-bottom: none;
        }}
        .stats-grid .section:first-child {{
            border-right: 1px solid #eee;
        }}

        /* Tables */
        .lines-table, .stats-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.8rem;
        }}
        .lines-table th, .stats-table th {{
            text-align: center;
            padding: 6px 4px;
            font-size: 0.65rem;
            font-weight: 700;
            color: #666;
            text-transform: uppercase;
            background: #f8f9fa;
            border-bottom: 1px solid #eee;
        }}
        .lines-table td, .stats-table td {{
            text-align: center;
            padding: 8px 4px;
            font-weight: 600;
        }}
        .lines-table .team-col, .stats-table .team-col {{
            text-align: left;
            min-width: 140px;
        }}
        .team-col {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .team-logo {{
            width: 28px;
            height: 28px;
            object-fit: contain;
        }}
        .team-name {{
            font-weight: 700;
            font-size: 0.9rem;
        }}
        .team-record {{
            font-size: 0.75rem;
            color: #666;
            font-weight: 500;
        }}
        .team-abbr {{
            font-weight: 700;
            color: #1a365d;
            text-align: left !important;
            padding-left: 8px !important;
        }}

        /* Betting Lines Colors */
        .spread {{ color: #1a365d; font-weight: 700; }}
        .ml {{ color: #2d7a2d; }}
        .total {{ color: #8b4513; }}

        .away-row {{ background: #fff; }}
        .home-row {{ background: #f8f9fa; }}

        /* Trends Bar */
        .trends-bar {{
            background: #e3f2fd;
            padding: 10px 16px;
            font-size: 0.8rem;
            color: #1565c0;
            display: flex;
            align-items: center;
            gap: 20px;
            flex-wrap: wrap;
        }}
        .trend-item {{
            display: flex;
            align-items: center;
            gap: 6px;
        }}

        /* Footer */
        footer {{
            text-align: center;
            padding: 30px;
            color: #666;
            font-size: 0.85rem;
        }}
        footer a {{ color: #1a365d; text-decoration: none; }}

        /* Responsive */
        @media (max-width: 768px) {{
            .stats-grid {{
                grid-template-columns: 1fr;
            }}
            .stats-grid .section:first-child {{
                border-right: none;
                border-bottom: 1px solid #eee;
            }}
            .game-header {{
                flex-direction: column;
                gap: 8px;
                text-align: center;
            }}
            .lines-table, .stats-table {{
                font-size: 0.7rem;
            }}
        }}

        /* Archive Calendar Dropdown */
        .archive-btn {{
            position: fixed;
            top: 70px;
            right: 20px;
            z-index: 999;
            background: linear-gradient(135deg, #fd5000, #ff7b3d);
            color: #fff;
            border: none;
            padding: 10px 16px;
            border-radius: 8px;
            font-weight: 700;
            font-size: 0.8rem;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 8px;
            box-shadow: 0 4px 15px rgba(253, 80, 0, 0.4);
        }}
        .archive-btn:hover {{ transform: scale(1.05); }}
        .archive-dropdown {{
            position: fixed;
            top: 115px;
            right: 20px;
            z-index: 998;
            background: rgba(13, 27, 42, 0.98);
            border: 2px solid #fd5000;
            border-radius: 12px;
            padding: 15px;
            width: 300px;
            display: none;
            box-shadow: 0 10px 40px rgba(0,0,0,0.5);
        }}
        .archive-dropdown.open {{ display: block; }}
        .cal-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
            padding-bottom: 10px;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }}
        .cal-title {{ color: #fff; font-weight: 700; font-size: 0.85rem; }}
        .cal-nav {{ display: flex; gap: 6px; align-items: center; }}
        .cal-nav-btn {{
            background: rgba(255,255,255,0.1);
            border: 1px solid rgba(255,255,255,0.2);
            color: #fff;
            padding: 4px 8px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.7rem;
        }}
        .cal-nav-btn:hover {{ background: #fd5000; }}
        .cal-month {{ color: #fd5000; font-weight: 700; font-size: 0.8rem; min-width: 90px; text-align: center; }}
        .cal-grid {{
            display: grid;
            grid-template-columns: repeat(7, 1fr);
            gap: 3px;
        }}
        .cal-day-hdr {{ text-align: center; color: #ffd700; font-size: 0.55rem; font-weight: 700; padding: 4px 0; }}
        .cal-day {{
            aspect-ratio: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 4px;
            color: #555;
            font-size: 0.7rem;
            font-weight: 600;
        }}
        .cal-day.has-data {{
            background: rgba(253, 80, 0, 0.25);
            border-color: rgba(253, 80, 0, 0.5);
            color: #fff;
            cursor: pointer;
        }}
        .cal-day.has-data:hover {{ background: #fd5000; transform: scale(1.1); }}
        .cal-day.today {{ background: #fd5000; color: #fff; font-weight: 800; }}
        .cal-day.other {{ opacity: 0.3; }}
        @media (max-width: 600px) {{
            .archive-btn {{ top: 60px; right: 10px; padding: 8px 12px; font-size: 0.7rem; }}
            .archive-dropdown {{ right: 10px; width: 260px; top: 100px; }}
        }}
    </style>
</head>
<body>
    <nav class="nav">
        <div class="nav-inner">
            <a href="index.html" class="logo">BET<span>LEGEND</span></a>
            <div class="nav-links">
                <a href="handicapping-hub.html">Hub</a>
                <a href="handicapping-hub-archive.html">Archive</a>
                <a href="blog-page10.html">Picks</a>
                <a href="nfl.html">NFL</a>
                <a href="nba.html">NBA</a>
                <a href="nhl.html">NHL</a>
            </div>
        </div>
    </nav>

    <header class="header">
        <h1>Handicapping <span>Hub</span></h1>
        <p class="subtitle">{date_str} | Advanced Stats & Betting Lines</p>
    </header>

    <!-- Archive Calendar Button & Dropdown -->
    <button class="archive-btn" onclick="document.getElementById('archiveCal').classList.toggle('open')">
        📅 Archive
    </button>
    <div class="archive-dropdown" id="archiveCal">
        <div class="cal-header">
            <span class="cal-title">View Past Days</span>
            <div class="cal-nav">
                <button class="cal-nav-btn" onclick="calNav(-1)">◀</button>
                <span class="cal-month" id="calMonth">Dec 2025</span>
                <button class="cal-nav-btn" onclick="calNav(1)">▶</button>
            </div>
        </div>
        <div class="cal-grid" id="calGrid"></div>
    </div>

    <div class="container">
        <div class="tabs">
            {tab_buttons}
        </div>
        {sport_sections}
    </div>

    <footer>
        <p>&copy; 2025 BetLegend | Data: ESPN, The Odds API | <a href="index.html">Home</a> | <a href="handicapping-hub-archive.html">Hub Archive</a></p>
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

        // Archive Calendar
        const archiveData = {archive_dates_json};
        let calDate = new Date();
        const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];

        function renderCal() {{
            const y = calDate.getFullYear(), m = calDate.getMonth();
            document.getElementById('calMonth').textContent = months[m] + ' ' + y;
            const first = new Date(y, m, 1).getDay();
            const days = new Date(y, m + 1, 0).getDate();
            const prev = new Date(y, m, 0).getDate();
            let h = '<div class="cal-day-hdr">S</div><div class="cal-day-hdr">M</div><div class="cal-day-hdr">T</div><div class="cal-day-hdr">W</div><div class="cal-day-hdr">T</div><div class="cal-day-hdr">F</div><div class="cal-day-hdr">S</div>';
            for (let i = first - 1; i >= 0; i--) h += '<div class="cal-day other">' + (prev - i) + '</div>';
            const today = new Date();
            for (let d = 1; d <= days; d++) {{
                const key = y + '-' + String(m + 1).padStart(2, '0') + '-' + String(d).padStart(2, '0');
                const isToday = y === today.getFullYear() && m === today.getMonth() && d === today.getDate();
                const hasData = archiveData[key];
                let cls = 'cal-day';
                if (isToday) cls += ' today';
                else if (hasData) cls += ' has-data';
                if (hasData) h += '<div class="' + cls + '" onclick="location.href=\\'' + hasData + '\\'">' + d + '</div>';
                else h += '<div class="' + cls + '">' + d + '</div>';
            }}
            const rem = (first + days) % 7;
            if (rem > 0) for (let d = 1; d <= 7 - rem; d++) h += '<div class="cal-day other">' + d + '</div>';
            document.getElementById('calGrid').innerHTML = h;
        }}
        function calNav(delta) {{ calDate.setMonth(calDate.getMonth() + delta); renderCal(); }}
        renderCal();
    </script>
</body>
</html>'''

# =============================================================================
# MAIN ORCHESTRATION
# =============================================================================

def fetch_all_games() -> Dict[str, List]:
    """Fetch games for all sports"""
    all_games = {}

    for sport, config in SPORTS.items():
        print(f"\n[{sport}] Fetching games...")

        events = fetch_espn_scoreboard(config['espn_path'])
        print(f"  Found {len(events)} games")

        if not events:
            all_games[sport] = []
            continue

        odds_data = fetch_odds(config['odds_key'])
        print(f"  Found odds for {len(odds_data)} games")

        games = []
        for event in events:
            try:
                comps = event.get('competitions', [{}])[0]
                competitors = comps.get('competitors', [])

                if len(competitors) < 2:
                    continue

                # VALIDATION: Skip completed/final games - only show scheduled/in-progress
                game_status = event.get('status', {}).get('type', {}).get('name', '')
                if game_status in ['STATUS_FINAL', 'STATUS_POSTPONED', 'STATUS_CANCELED']:
                    away_team = competitors[0].get('team', {})
                    home_team = competitors[1].get('team', {})
                    print(f"  [SKIP] Game is {game_status}: {away_team.get('abbreviation')} vs {home_team.get('abbreviation')}")
                    continue

                # NCAAB: Only show important games (ranked teams or major programs)
                if sport == 'NCAAB' and not is_important_ncaab_game(event):
                    away_team = competitors[0].get('team', {})
                    home_team = competitors[1].get('team', {})
                    print(f"  [SKIP] NCAAB not important: {away_team.get('displayName', 'TBD')} vs {home_team.get('displayName', 'TBD')}")
                    continue

                # NCAAF: Only show bowl games during bowl season (Dec-Jan)
                if sport == 'NCAAF' and not is_bowl_game(event):
                    away_team = competitors[0].get('team', {})
                    home_team = competitors[1].get('team', {})
                    print(f"  [SKIP] NCAAF not a bowl: {away_team.get('displayName', 'TBD')} vs {home_team.get('displayName', 'TBD')}")
                    continue

                away_comp = next((c for c in competitors if c.get('homeAway') == 'away'), competitors[0])
                home_comp = next((c for c in competitors if c.get('homeAway') == 'home'), competitors[1])

                away_team = away_comp.get('team', {})
                home_team = home_comp.get('team', {})

                away_name = away_team.get('displayName', 'TBD')
                home_name = home_team.get('displayName', 'TBD')
                away_abbr = away_team.get('abbreviation', 'TBD')
                home_abbr = home_team.get('abbreviation', 'TBD')

                away_record = away_comp.get('records', [{}])[0].get('summary', '0-0') if away_comp.get('records') else '0-0'
                home_record = home_comp.get('records', [{}])[0].get('summary', '0-0') if home_comp.get('records') else '0-0'

                # Fetch team stats and injuries
                away_id = away_team.get('id', '')
                home_id = home_team.get('id', '')
                away_raw = fetch_team_statistics(config['espn_path'], away_id) if away_id else {}
                home_raw = fetch_team_statistics(config['espn_path'], home_id) if home_id else {}

                # Fetch injuries
                away_injuries = fetch_team_injuries(config['espn_path'], away_id) if away_id else []
                home_injuries = fetch_team_injuries(config['espn_path'], home_id) if home_id else []

                # Extract stats based on sport
                if sport in ['NFL', 'NCAAF']:
                    away_stats = extract_nfl_stats(away_raw, away_record)
                    home_stats = extract_nfl_stats(home_raw, home_record)
                elif sport in ['NBA', 'NCAAB']:
                    away_stats = extract_nba_stats(away_raw, away_record)
                    home_stats = extract_nba_stats(home_raw, home_record)
                elif sport == 'NHL':
                    away_stats = extract_nhl_stats(away_raw, away_record)
                    home_stats = extract_nhl_stats(home_raw, home_record)
                else:
                    away_stats = {}
                    home_stats = {}

                # Get odds
                odds = match_game_odds(odds_data, away_name, home_name)

                # Game time
                game_date = event.get('date', '')
                try:
                    dt = datetime.fromisoformat(game_date.replace('Z', '+00:00'))
                    game_time = dt.strftime("%I:%M %p ET")
                except:
                    game_time = "TBD"

                venue = comps.get('venue', {}).get('fullName', 'TBD')
                broadcasts = comps.get('broadcasts', [])
                network = broadcasts[0].get('names', ['TBD'])[0] if broadcasts else 'TBD'

                # VALIDATION: Skip games with invalid/placeholder data
                # Check for TBD team names or abbreviations
                if away_abbr == 'TBD' or home_abbr == 'TBD':
                    print(f"  [SKIP] Game has TBD team: {away_abbr} vs {home_abbr}")
                    continue
                if away_name == 'TBD' or home_name == 'TBD':
                    print(f"  [SKIP] Game has TBD team name")
                    continue
                if game_time == 'TBD':
                    print(f"  [SKIP] Game has TBD time: {away_abbr} vs {home_abbr}")
                    continue

                # For college sports, verify we have real stats (not just PPG)
                if sport == 'NCAAF':
                    # NCAAF needs more robust validation - check key offensive stats
                    key_stats = ['ppg', 'ypg', 'pass_ypg', 'rush_ypg', 'comp_pct', 'ypa']
                    away_missing = sum(1 for s in key_stats if away_stats.get(s, '-') == '-')
                    home_missing = sum(1 for s in key_stats if home_stats.get(s, '-') == '-')
                    if away_missing > 2 or home_missing > 2:
                        print(f"  [SKIP] Incomplete stats ({away_missing}/{home_missing} missing): {away_abbr} vs {home_abbr}")
                        continue
                elif sport == 'NCAAB':
                    # Check if we have any real stats (at least PPG should be available)
                    away_ppg = away_stats.get('ppg', '-')
                    home_ppg = home_stats.get('ppg', '-')
                    if away_ppg == '-' or home_ppg == '-':
                        print(f"  [SKIP] Missing stats for: {away_abbr} vs {home_abbr}")
                        continue

                game = {
                    'time': game_time,
                    'venue': venue,
                    'network': network,
                    'odds': odds,
                    'away': {
                        'name': away_name,
                        'abbr': away_abbr,
                        'record': away_record,
                        'stats': away_stats,
                        'injuries': away_injuries,
                        'team_id': away_id,
                    },
                    'home': {
                        'name': home_name,
                        'abbr': home_abbr,
                        'record': home_record,
                        'stats': home_stats,
                        'injuries': home_injuries,
                        'team_id': home_id,
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
    print("=" * 60)
    print("HANDICAPPING HUB - ULTIMATE PRODUCTION SYSTEM")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Archive current hub before generating new one
    archive_current_hub()

    date_str = datetime.now().strftime("%B %d, %Y")
    all_games = fetch_all_games()
    html = generate_page(all_games, date_str)

    output_path = os.path.join(REPO_PATH, OUTPUT_FILE)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print("\n" + "=" * 60)
    print(f"SUCCESS: Generated {OUTPUT_FILE}")
    for sport in ['NBA', 'NFL', 'NHL', 'NCAAB', 'NCAAF']:
        print(f"  {sport}: {len(all_games.get(sport, []))} games")
    print("=" * 60)

if __name__ == "__main__":
    main()
