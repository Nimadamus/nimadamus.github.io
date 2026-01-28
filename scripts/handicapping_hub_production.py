#!/usr/bin/env python3
"""
HANDICAPPING HUB - PRODUCTION SCRIPT
Generates the Handicapping Hub with:
- ScoresAndOdds-style betting table (Team, Line, ML, O/U, SU, ATS, O/U Rec, PPG, OPP, PWR)
- Offense vs Defense stat grids
- ATS and O/U records from Covers.com
- Head-to-head data when available
- Injury reports
- Dark futuristic theme with neon accents
"""

import requests
import json
import os
import sys
import shutil
import re
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple
from bs4 import BeautifulSoup

# Timezone handling
try:
    from zoneinfo import ZoneInfo
    EASTERN = ZoneInfo('America/New_York')
except ImportError:
    from datetime import timezone as tz
    EASTERN = tz(timedelta(hours=-5))

import time
import random

def fetch_with_retry(url: str, params: dict = None, timeout: int = 15, max_retries: int = 3) -> Optional[requests.Response]:
    """Fetch URL with exponential backoff retry logic."""
    for attempt in range(max_retries):
        try:
            if params:
                resp = requests.get(url, params=params, timeout=timeout)
            else:
                resp = requests.get(url, timeout=timeout)
            if resp.status_code == 200:
                return resp
            elif resp.status_code == 429:
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                print(f"  [RATE LIMIT] Waiting {wait_time:.1f}s before retry...")
                time.sleep(wait_time)
            elif resp.status_code >= 500:
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                print(f"  [SERVER ERROR {resp.status_code}] Retry {attempt + 1}/{max_retries}...")
                time.sleep(wait_time)
            else:
                return None
        except requests.exceptions.Timeout:
            wait_time = (2 ** attempt) + random.uniform(0, 1)
            print(f"  [TIMEOUT] Retry {attempt + 1}/{max_retries} after {wait_time:.1f}s...")
            time.sleep(wait_time)
        except requests.exceptions.RequestException as e:
            print(f"  [REQUEST ERROR] {e}")
            if attempt < max_retries - 1:
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                time.sleep(wait_time)
    return None

# =============================================================================
# CONFIGURATION
# =============================================================================

ODDS_API_KEY = os.environ.get('ODDS_API_KEY', 'deeac7e7af6a8f1a5ac84c625e04973a')
REPO_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_FILE = "handicapping-hub.html"  # Production file

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

TOP_NCAAB_TEAMS = {
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
    'virginia', 'nc state', 'wake forest', 'boston college', 'georgia tech', 'syracuse', 'notre dame', 'miami',
    'arizona state', 'washington', 'utah', 'stanford', 'california', 'cal',
    'seton hall', 'depaul', 'georgetown',
    'smu', 'tulane', 'uab', 'temple', 'east carolina', 'charlotte', 'wichita state',
    'new mexico', 'unlv', 'nevada', 'boise state', 'colorado state', 'fresno state', 'wyoming', 'air force',
    'saint mary\'s', 'san francisco', 'santa clara', 'loyola marymount', 'pepperdine',
    'vcu', 'saint louis', 'george mason', 'richmond', 'la salle', 'fordham', 'umass',
    'drake', 'bradley', 'southern illinois', 'indiana state', 'missouri state',
}

# =============================================================================
# PERMANENT SAFEGUARDS - DO NOT REMOVE
# =============================================================================

def block_line_movements(html_content: str) -> str:
    """
    PERMANENT SAFEGUARD: Remove ANY line movement content that might slip through.
    This function is called before saving the HTML file.
    Added January 24, 2026 - NEVER REMOVE THIS FUNCTION.
    """
    import re
    # Patterns to remove
    banned_patterns = [
        r'<div[^>]*class="[^"]*alerts-banner[^"]*"[^>]*>.*?</div>',
        r'LINE MOVEMENTS? DETECTED',
        r'line.?movement',
        r'<div[^>]*class="[^"]*line-movement[^"]*"[^>]*>.*?</div>',
    ]
    for pattern in banned_patterns:
        html_content = re.sub(pattern, '', html_content, flags=re.IGNORECASE | re.DOTALL)
    return html_content

def clean_stat_display(val) -> str:
    """
    PERMANENT SAFEGUARD: Clean stats for display.
    - Returns 'N/A' for missing/invalid data (styled nicely in CSS)
    - Never shows raw '-', '0', or '0.0' for missing stats
    Added January 24, 2026 - NEVER REMOVE THIS FUNCTION.
    """
    if val is None or val == '' or val == '-':
        return '<span class="stat-na">—</span>'
    try:
        num = float(str(val).replace('%', ''))
        if num == 0:
            # Check if this is a legitimate 0 or missing data
            # For most stats, 0 is suspicious - use context
            return '<span class="stat-na">—</span>'
        return str(val)
    except (ValueError, TypeError):
        if str(val).strip() in ['-', '0', '0.0', 'N/A', 'n/a', '']:
            return '<span class="stat-na">—</span>'
        return str(val)

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def safe_num(val, decimals=1):
    """Safely format a number with specified decimals"""
    if val is None or val == '':
        return '-'
    try:
        num = float(val)
        if num == 0:
            return '-'  # Return dash for zero values
        if decimals == 0:
            return str(int(num))
        return f"{num:.{decimals}f}"
    except (ValueError, TypeError):
        return str(val) if val else '-'

def safe_float(val) -> float:
    """Safely convert to float, return 0 if fails"""
    try:
        return float(val) if val else 0
    except (ValueError, TypeError):
        return 0

def safe_pct(val):
    """Format percentage value"""
    if val is None or val == '':
        return '-'
    try:
        num = float(val)
        if num > 1:
            return f"{num:.1f}%"
        return f"{num * 100:.1f}%"
    except (ValueError, TypeError):
        return str(val) if val else '-'

def get_power_rating(record: str) -> str:
    """Calculate simple power rating from record"""
    try:
        parts = record.replace(' ', '').split('-')
        wins = int(parts[0])
        total = sum(int(p) for p in parts if p.isdigit())
        if total == 0:
            return '-'
        pct = wins / total
        return f"{pct * 100:.0f}"
    except (ValueError, IndexError, ZeroDivisionError):
        return '-'

def calculate_efg_pct(fgm, fga, three_pm) -> str:
    """Calculate effective field goal percentage"""
    try:
        fgm = float(fgm) if fgm else 0
        fga = float(fga) if fga else 0
        three_pm = float(three_pm) if three_pm else 0
        if fga == 0:
            return '-'
        efg = ((fgm + 0.5 * three_pm) / fga) * 100
        return f"{efg:.1f}%"
    except (ValueError, TypeError, ZeroDivisionError):
        return '-'

def calculate_ts_pct(ppg, fga, fta) -> str:
    """Calculate true shooting percentage"""
    try:
        ppg = float(ppg) if ppg else 0
        fga = float(fga) if fga else 0
        fta = float(fta) if fta else 0
        tsa = fga + 0.44 * fta
        if tsa == 0:
            return '-'
        ts = (ppg / (2 * tsa)) * 100
        return f"{ts:.1f}%"
    except (ValueError, TypeError, ZeroDivisionError):
        return '-'

def format_top(val, games: int) -> str:
    """Format time of possession"""
    if val is None or val == '' or val == '-':
        return '-'
    try:
        if isinstance(val, (int, float)):
            if val > 1000:
                secs_per_game = val / games if games > 0 else val
                mins = int(secs_per_game // 60)
                secs = int(secs_per_game % 60)
                return f"{mins}:{secs:02d}"
            return f"{int(val)}:00"
        return str(val)
    except (ValueError, TypeError):
        return str(val) if val else '-'

# =============================================================================
# NEW: COVERS.COM ATS/O/U BETTING RECORDS SCRAPER
# =============================================================================

# Cache for betting records to avoid repeated scraping
_COVERS_CACHE = {}

def fetch_covers_betting_records(sport: str) -> Dict[str, Dict]:
    """
    Fetch ATS and O/U records from Covers.com standings page.
    Returns dict mapping team abbreviation to {'ats': 'W-L-P', 'ou': 'O-U-P'}
    """
    global _COVERS_CACHE

    # Check cache first
    if sport.lower() in _COVERS_CACHE:
        return _COVERS_CACHE[sport.lower()]

    urls = {
        'nba': 'https://www.covers.com/sport/basketball/nba/standings',
        'nhl': 'https://www.covers.com/sport/hockey/nhl/standings',
        'nfl': 'https://www.covers.com/sport/football/nfl/standings',
        'ncaab': 'https://www.covers.com/sport/basketball/ncaab/standings',
        'ncaaf': 'https://www.covers.com/sport/football/ncaaf/standings',
    }

    url = urls.get(sport.lower())
    if not url:
        return {}

    print(f"  [COVERS] Fetching {sport.upper()} ATS/O/U records from Covers.com...")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"  [COVERS] Failed to fetch: HTTP {response.status_code}")
            return {}

        soup = BeautifulSoup(response.text, 'html.parser')
        records = {}

        # Valid team abbreviations for validation
        valid_nba = {'ATL','BOS','BKN','CHA','CHI','CLE','DAL','DEN','DET','GS','GSW','HOU','IND','LAC','LAL','MEM','MIA','MIL','MIN','NO','NOP','NY','NYK','OKC','ORL','PHI','PHX','POR','SAC','SA','SAS','TOR','UTA','WAS'}
        valid_nhl = {'ANA','ARI','BOS','BUF','CAR','CBJ','CGY','CHI','COL','DAL','DET','EDM','FLA','LA','LAK','MIN','MTL','NJ','NJD','NSH','NYI','NYR','OTT','PHI','PIT','SEA','SJ','SJS','STL','TB','TBL','TOR','UTA','VAN','VGK','WPG','WSH'}
        valid_nfl = {'ARI','ATL','BAL','BUF','CAR','CHI','CIN','CLE','DAL','DEN','DET','GB','HOU','IND','JAC','JAX','KC','LAC','LAR','LV','MIA','MIN','NE','NO','NYG','NYJ','PHI','PIT','SEA','SF','TB','TEN','WAS'}

        if sport.lower() == 'nba':
            valid_teams = valid_nba
        elif sport.lower() == 'nhl':
            valid_teams = valid_nhl
        elif sport.lower() == 'nfl':
            valid_teams = valid_nfl
        else:
            valid_teams = set()  # For college, we'll be more lenient

        # Find tables with ATS column
        for table in soup.find_all('table'):
            headers = [th.get_text(strip=True).upper() for th in table.find_all('th')]

            if 'ATS' not in headers:
                continue

            ats_idx = headers.index('ATS')
            ou_idx = headers.index('O/U') if 'O/U' in headers else -1

            for row in table.find_all('tr')[1:]:  # Skip header row
                cells = row.find_all(['td', 'th'])
                if len(cells) <= ats_idx:
                    continue

                # Extract team abbreviation from first cell
                team_cell = cells[0]
                team_text = team_cell.get_text(strip=True)

                # Look for abbreviation pattern (2-3 uppercase letters)
                match = re.search(r'([A-Z]{2,3})', team_text)
                if match:
                    team_abbr = match.group(1)

                    # Validate team abbreviation if we have a list
                    if valid_teams and team_abbr not in valid_teams:
                        continue

                    # Get ATS record
                    ats_text = cells[ats_idx].get_text(strip=True) if len(cells) > ats_idx else '-'

                    # Get O/U record
                    ou_text = '-'
                    if ou_idx >= 0 and len(cells) > ou_idx:
                        ou_text = cells[ou_idx].get_text(strip=True)

                    # Validate format (should be like "25-17-1" or "25-17")
                    if re.match(r'\d+-\d+', ats_text):
                        records[team_abbr] = {
                            'ats': ats_text,
                            'ou': ou_text if re.match(r'\d+-\d+', ou_text) else '-'
                        }

        # Normalize abbreviations
        normalized = {}
        abbr_map = {
            'GS': 'GSW', 'NO': 'NOP', 'NY': 'NYK', 'SA': 'SAS',
            'LA': 'LAK', 'NJ': 'NJD', 'TB': 'TBL', 'SJ': 'SJS',
            'JAC': 'JAX', 'LAR': 'LA'
        }

        for abbr, data in records.items():
            # Store under both the original and normalized abbreviation
            normalized[abbr] = data
            if abbr in abbr_map:
                normalized[abbr_map[abbr]] = data
            # Also check reverse mapping
            for orig, norm in abbr_map.items():
                if abbr == norm:
                    normalized[orig] = data

        print(f"  [COVERS] Found ATS/O/U records for {len(records)} teams")

        # Cache the results
        _COVERS_CACHE[sport.lower()] = normalized

        return normalized

    except requests.exceptions.RequestException as e:
        print(f"  [COVERS] Error fetching data: {e}")
        return {}
    except Exception as e:
        print(f"  [COVERS] Error parsing data: {e}")
        return {}


# =============================================================================
# NEW: HEAD-TO-HEAD DATA FROM COVERS.COM
# =============================================================================

# H2H cache to avoid repeated scraping
_H2H_CACHE = {}

def fetch_h2h_data(sport: str, team1_abbr: str, team2_abbr: str) -> Optional[Dict]:
    """
    Fetch head-to-head data from Covers.com matchup page.
    Returns dict with H2H record, ATS record, O/U trend for last 5 meetings.
    """
    global _H2H_CACHE

    # Create cache key
    cache_key = f"{sport.lower()}_{min(team1_abbr, team2_abbr)}_{max(team1_abbr, team2_abbr)}"
    if cache_key in _H2H_CACHE:
        return _H2H_CACHE[cache_key]

    sport_urls = {
        'nba': 'https://www.covers.com/sports/nba/matchups',
        'nhl': 'https://www.covers.com/sports/nhl/matchups',
        'nfl': 'https://www.covers.com/sports/nfl/matchups',
        'ncaab': 'https://www.covers.com/sports/ncaab/matchups',
        'ncaaf': 'https://www.covers.com/sports/ncaaf/matchups',
    }

    sport_paths = {
        'nba': 'basketball/nba',
        'nhl': 'hockey/nhl',
        'nfl': 'football/nfl',
        'ncaab': 'basketball/ncaab',
        'ncaaf': 'football/ncaaf',
    }

    base_url = sport_urls.get(sport.lower())
    sport_path = sport_paths.get(sport.lower())

    if not base_url:
        return None

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

    try:
        # First get the matchups page to find game IDs
        r = requests.get(base_url, headers=headers, timeout=15)
        if r.status_code != 200:
            return None

        soup = BeautifulSoup(r.text, 'html.parser')

        # Find game ID for this matchup
        pattern = rf'/sport/{sport_path}/matchup/(\d+)'

        t1 = team1_abbr.lower()
        t2 = team2_abbr.lower()

        # Team name mappings for matching
        team_names = {
            'okc': 'thunder', 'mil': 'bucks', 'lal': 'lakers',
            'bos': 'celtics', 'gsw': 'warriors', 'phx': 'suns',
            'den': 'nuggets', 'cle': 'cavaliers', 'phi': '76ers',
            'tor': 'raptors', 'sac': 'kings', 'ana': 'ducks',
            'col': 'avalanche', 'sea': 'kraken', 'pit': 'penguins',
            'wsh': 'capitals', 'van': 'canucks', 'cgy': 'flames',
            'nyi': 'islanders', 'uta': 'jazz', 'chi': 'bulls',
            'mia': 'heat', 'nyk': 'knicks', 'bkn': 'nets',
            'atl': 'hawks', 'det': 'pistons', 'ind': 'pacers',
            'orl': 'magic', 'was': 'wizards', 'cha': 'hornets',
            'mem': 'grizzlies', 'min': 'timberwolves', 'nop': 'pelicans',
            'hou': 'rockets', 'dal': 'mavericks', 'sas': 'spurs',
            'por': 'blazers', 'lac': 'clippers',
            # NHL
            'vgk': 'golden knights', 'wpg': 'jets', 'edm': 'oilers',
            'buf': 'sabres', 'car': 'hurricanes', 'cbj': 'blue jackets',
            'fla': 'panthers', 'mtl': 'canadiens', 'njd': 'devils',
            'nyr': 'rangers', 'ott': 'senators', 'tbl': 'lightning',
            'stl': 'blues', 'nsh': 'predators', 'ari': 'coyotes',
        }

        # Get all game IDs
        game_ids = []
        for link in soup.find_all('a', href=re.compile(pattern)):
            match = re.search(pattern, link.get('href', ''))
            if match and match.group(1) not in game_ids:
                game_ids.append(match.group(1))

        game_id = None
        # Try each game ID to find our matchup
        for test_id in game_ids[:15]:
            test_url = f'https://www.covers.com/sport/{sport_path}/matchup/{test_id}'
            test_r = requests.get(test_url, headers=headers, timeout=10)
            if test_r.status_code == 200:
                test_soup = BeautifulSoup(test_r.text, 'html.parser')
                title = test_soup.find('title')
                if title:
                    title_text = title.get_text().lower()
                    # Check if both team abbreviations appear in title
                    if t1 in title_text and t2 in title_text:
                        game_id = test_id
                        soup = test_soup
                        break
                    # Also check common team name mappings
                    t1_name = team_names.get(t1, t1)
                    t2_name = team_names.get(t2, t2)
                    if t1_name in title_text and t2_name in title_text:
                        game_id = test_id
                        soup = test_soup
                        break

        if not game_id:
            print(f'  [H2H] Could not find matchup for {t1.upper()} vs {t2.upper()}')
            return None

        # Find the H2H table
        h2h_table = None
        for table in soup.find_all('table'):
            headers_list = [th.get_text(strip=True) for th in table.find_all('th')]
            if 'Date' in headers_list and 'Result' in headers_list and 'Home' in headers_list:
                h2h_table = table
                break

        if not h2h_table:
            print(f'  [H2H] No H2H table found')
            return None

        # Extract last 5 meetings
        meetings = []
        t1_wins = 0
        t2_wins = 0
        t1_ats = 0
        t2_ats = 0
        overs = 0
        unders = 0

        rows = h2h_table.find_all('tr')[1:]  # Skip header
        for row in rows[:5]:
            cells = [td.get_text(strip=True) for td in row.find_all('td')]
            if len(cells) >= 5:
                date, home, result, ats, ou = cells[0], cells[1], cells[2], cells[3], cells[4]
                meetings.append({
                    'date': date,
                    'home': home,
                    'result': result,
                    'ats': ats,
                    'ou': ou
                })

                # Parse ATS - format like 'OKC-5.5' or 'MIL5.0'
                ats_team = re.match(r'([A-Z]+)', ats)
                if ats_team:
                    ats_abbr = ats_team.group(1).upper()
                    if ats_abbr == t1.upper():
                        t1_ats += 1
                    elif ats_abbr == t2.upper():
                        t2_ats += 1

                # Parse O/U - format like 'o233.5' or 'u233.5'
                if ou.lower().startswith('o'):
                    overs += 1
                elif ou.lower().startswith('u'):
                    unders += 1

                # Parse winner from result
                scores = re.findall(r'(\d+)', result)
                if len(scores) >= 2:
                    home_score = int(scores[0])
                    away_score = int(scores[1])
                    home_abbr = home.upper()

                    if home_score > away_score:
                        if home_abbr == t1.upper():
                            t1_wins += 1
                        else:
                            t2_wins += 1
                    else:
                        if home_abbr == t1.upper():
                            t2_wins += 1
                        else:
                            t1_wins += 1

        total_games = len(meetings)

        result = {
            'meetings': meetings,
            'h2h_su': f'{team1_abbr.upper()} {t1_wins}-{t2_wins}',
            'h2h_ats': f'{t1_ats}-{t2_ats} ATS',
            'h2h_ou': f'{overs}O-{unders}U',
            'total_games': total_games,
            'team1_abbr': team1_abbr.upper(),
            'team2_abbr': team2_abbr.upper(),
        }

        _H2H_CACHE[cache_key] = result
        return result

    except Exception as e:
        print(f'  [H2H] Error fetching H2H: {e}')
        return None


# =============================================================================
# NEW: ADVANCED STATS FETCHING
# =============================================================================

def fetch_team_standings_details(sport_path: str, team_id: str) -> Dict:
    """
    Fetch team standings details including home/away record and streak.
    Returns dict with: home_rec, away_rec, streak, div_rec
    """
    result = {
        'home_rec': '-',
        'away_rec': '-',
        'streak': '-',
        'div_rec': '-',
        'conf_rec': '-',
    }

    url = f"https://site.api.espn.com/apis/site/v2/sports/{sport_path}/teams/{team_id}"
    resp = fetch_with_retry(url, timeout=10, max_retries=2)

    if resp:
        try:
            data = resp.json()
            team = data.get('team', {})
            record = team.get('record', {})
            items = record.get('items', [])

            for item in items:
                rec_type = item.get('type', '').lower()
                summary = item.get('summary', '-')

                if rec_type == 'home':
                    result['home_rec'] = summary
                elif rec_type == 'road' or rec_type == 'away':
                    result['away_rec'] = summary
                elif rec_type == 'vsDiv' or rec_type == 'vsdiv':
                    result['div_rec'] = summary
                elif rec_type == 'vsConf' or rec_type == 'vsconf':
                    result['conf_rec'] = summary

            # Get streak from standingSummary or other sources
            standing = team.get('standingSummary', '')
            if standing:
                # Try to extract streak info (e.g., "1st in Southeast - Won 3")
                streak_match = re.search(r'(Won|Lost|W|L)\s*(\d+)', standing, re.I)
                if streak_match:
                    direction = 'W' if streak_match.group(1).lower().startswith('w') else 'L'
                    count = streak_match.group(2)
                    result['streak'] = f"{direction}{count}"

            # Also check for streak in record items
            for item in items:
                if 'streak' in item.get('type', '').lower():
                    result['streak'] = item.get('summary', '-')

        except json.JSONDecodeError:
            pass

    return result

def fetch_team_l5_record(sport_path: str, team_id: str) -> str:
    """
    Calculate last 5 games record from team schedule.
    Returns string like "3-2" or "-" if unavailable.
    """
    url = f"https://site.api.espn.com/apis/site/v2/sports/{sport_path}/teams/{team_id}/schedule"
    resp = fetch_with_retry(url, timeout=10, max_retries=2)

    if resp:
        try:
            data = resp.json()
            events = data.get('events', [])

            # Filter to completed games
            completed = []
            for event in events:
                status = event.get('competitions', [{}])[0].get('status', {})
                state = status.get('type', {}).get('state', '')
                if state.lower() == 'post':
                    completed.append(event)

            # Sort by date descending and take last 5
            completed.sort(key=lambda x: x.get('date', ''), reverse=True)
            last_5 = completed[:5]

            if not last_5:
                return '-'

            wins = 0
            losses = 0

            for game in last_5:
                competitions = game.get('competitions', [{}])
                if competitions:
                    comp = competitions[0]
                    competitors = comp.get('competitors', [])

                    for team in competitors:
                        if str(team.get('id', '')) == str(team_id):
                            winner = team.get('winner', False)
                            if winner:
                                wins += 1
                            else:
                                losses += 1
                            break

            if wins + losses > 0:
                return f"{wins}-{losses}"

        except (json.JSONDecodeError, KeyError, IndexError):
            pass

    return '-'

# =============================================================================
# DATA FETCHING (from production)
# =============================================================================

def fetch_espn_scoreboard(sport_path: str) -> List[Dict]:
    """Fetch today's games from ESPN Scoreboard API"""
    date_str = datetime.now().strftime('%Y%m%d')
    url = f"https://site.api.espn.com/apis/site/v2/sports/{sport_path}/scoreboard?dates={date_str}"
    resp = fetch_with_retry(url, timeout=15, max_retries=3)
    if resp:
        return resp.json().get('events', [])
    return []

def fetch_team_statistics(sport_path: str, team_id: str) -> Dict:
    """Fetch team statistics from ESPN"""
    stats = {}
    url = f"https://site.api.espn.com/apis/site/v2/sports/{sport_path}/teams/{team_id}/statistics"
    resp = fetch_with_retry(url, timeout=10, max_retries=2)
    if resp:
        try:
            data = resp.json()
            for cat in data.get('results', {}).get('stats', {}).get('categories', []):
                for stat in cat.get('stats', []):
                    name = stat.get('name', '')
                    value = stat.get('displayValue', stat.get('value', ''))
                    stats[name] = value
            for split in data.get('results', {}).get('splits', {}).get('categories', []):
                for stat in split.get('stats', []):
                    name = stat.get('name', '')
                    value = stat.get('displayValue', stat.get('value', ''))
                    stats[name] = value
        except json.JSONDecodeError:
            pass
    return stats

def fetch_team_record(sport_path: str, team_id: str) -> str:
    """Fetch team win-loss record"""
    url = f"https://site.api.espn.com/apis/site/v2/sports/{sport_path}/teams/{team_id}"
    resp = fetch_with_retry(url, timeout=10, max_retries=2)
    if resp:
        try:
            data = resp.json()
            team = data.get('team', {})
            record = team.get('record', {})
            items = record.get('items', [])
            if items:
                return items[0].get('summary', '0-0')
        except json.JSONDecodeError:
            pass
    return '0-0'

def fetch_defensive_stats(sport_path: str, team_id: str) -> Dict:
    """
    Fetch defensive stats (opponent PPG, etc.) from ESPN team summary.
    Returns dict with opp_ppg, opp_fg_pct, opp_3pt_pct
    """
    result = {'opp_ppg': 0, 'opp_fg_pct': '-', 'opp_3pt_pct': '-'}

    # Try the team summary endpoint which often has points against
    url = f"https://site.api.espn.com/apis/site/v2/sports/{sport_path}/teams/{team_id}"
    resp = fetch_with_retry(url, timeout=10, max_retries=2)

    if resp:
        try:
            data = resp.json()
            team = data.get('team', {})

            # Check record stats for points against
            record = team.get('record', {})
            for item in record.get('items', []):
                stats = item.get('stats', [])
                for stat in stats:
                    name = stat.get('name', '').lower()
                    value = stat.get('value', stat.get('displayValue', 0))
                    if 'pointsagainst' in name or 'avgpointsagainst' in name or name == 'papg':
                        try:
                            result['opp_ppg'] = float(value)
                        except (ValueError, TypeError):
                            pass

            # Also check nextEvent for defensive stats
            next_event = team.get('nextEvent', [])
            for event in next_event:
                for comp in event.get('competitions', []):
                    for competitor in comp.get('competitors', []):
                        if str(competitor.get('id', '')) == str(team_id):
                            for stat in competitor.get('statistics', []):
                                name = stat.get('name', '').lower()
                                value = stat.get('displayValue', stat.get('value', ''))
                                if 'against' in name or 'opp' in name:
                                    try:
                                        result['opp_ppg'] = float(value)
                                    except (ValueError, TypeError):
                                        pass

        except (json.JSONDecodeError, KeyError):
            pass

    # Fallback: Fetch from statistics endpoint with defensive category
    url2 = f"https://site.api.espn.com/apis/site/v2/sports/{sport_path}/teams/{team_id}/statistics"
    resp2 = fetch_with_retry(url2, timeout=10, max_retries=2)

    if resp2:
        try:
            data = resp2.json()
            # Look through all categories for defensive stats
            for split in data.get('results', {}).get('splits', {}).get('categories', []):
                cat_name = split.get('name', '').lower()
                if 'defense' in cat_name or 'opponent' in cat_name:
                    for stat in split.get('stats', []):
                        name = stat.get('name', '').lower()
                        value = stat.get('value', stat.get('displayValue', ''))
                        if 'pointsagainst' in name or name == 'avgpointsagainst' or name == 'oppointspergame':
                            try:
                                result['opp_ppg'] = float(value)
                            except (ValueError, TypeError):
                                pass
                        elif 'oppfieldgoalpct' in name or 'oppfg' in name:
                            result['opp_fg_pct'] = safe_pct(value)
                        elif 'oppthreepointpct' in name or 'opp3pt' in name:
                            result['opp_3pt_pct'] = safe_pct(value)
        except (json.JSONDecodeError, KeyError):
            pass

    return result

def fetch_odds(sport_key: str) -> List[Dict]:
    """Fetch betting odds from The Odds API"""
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds"
    params = {
        'apiKey': ODDS_API_KEY,
        'regions': 'us',
        'markets': 'spreads,h2h,totals',
        'oddsFormat': 'american'
    }
    resp = fetch_with_retry(url, params=params, timeout=15, max_retries=3)
    if resp:
        try:
            all_odds = resp.json()
            if EASTERN:
                now_eastern = datetime.now(EASTERN)
            else:
                now_eastern = datetime.now() - timedelta(hours=5)
            today_date = now_eastern.date() if hasattr(now_eastern, 'date') else now_eastern

            filtered = []
            for game in all_odds:
                commence = game.get('commence_time', '')
                if commence:
                    try:
                        game_dt = datetime.fromisoformat(commence.replace('Z', '+00:00'))
                        if EASTERN:
                            game_eastern = game_dt.astimezone(EASTERN)
                            game_date = game_eastern.date()
                        else:
                            game_date = (game_dt.replace(tzinfo=None) - timedelta(hours=5)).date()

                        if game_date == today_date:
                            filtered.append(game)
                    except Exception:
                        pass
            return filtered
        except json.JSONDecodeError:
            pass
    return []

def fetch_team_injuries(sport_path: str, team_id: str) -> List[Dict]:
    """Fetch team injuries"""
    injuries = []
    url = f"https://site.api.espn.com/apis/site/v2/sports/{sport_path}/teams/{team_id}/injuries"
    resp = fetch_with_retry(url, timeout=10, max_retries=2)
    if resp:
        try:
            data = resp.json()
            for item in data.get('items', []):
                athlete = item.get('athlete', {})
                name = athlete.get('displayName', athlete.get('shortName', 'Unknown'))
                position = athlete.get('position', {}).get('abbreviation', '')
                status = item.get('status', 'Unknown')
                injury_type = item.get('type', {}).get('text', item.get('details', {}).get('type', ''))
                status_lower = status.lower() if status else ''
                if status_lower in ['out', 'doubtful', 'questionable', 'injured reserve', 'ir', 'day-to-day']:
                    injuries.append({
                        'name': name,
                        'position': position,
                        'status': status,
                        'type': injury_type
                    })
        except json.JSONDecodeError:
            pass
    return injuries[:5]

def format_injuries_html(injuries: List[Dict], abbr: str) -> str:
    """Format injuries for display"""
    if not injuries:
        return f"{abbr}: No reported injuries"

    injury_strs = []
    for inj in injuries[:3]:
        name = inj.get('name', 'Unknown')
        parts = name.split()
        if len(parts) > 1:
            short_name = f"{parts[0][0]}. {parts[-1]}"
        else:
            short_name = name
        pos = inj.get('position', '')
        status = inj.get('status', '')
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

# =============================================================================
# STAT EXTRACTION (Enhanced with situational stats)
# =============================================================================

def extract_nba_stats(raw: Dict, record: str, standings: Dict = None, l5: str = '-', betting_rec: Dict = None) -> Dict:
    """Extract comprehensive NBA stats including situational and ATS/O/U"""
    ppg = raw.get('avgPoints', raw.get('pointsPerGame', 0))
    fga = raw.get('avgFieldGoalsAttempted', 0)
    fta = raw.get('avgFreeThrowsAttempted', 0)
    fgm = raw.get('avgFieldGoalsMade', 0)
    three_pm = raw.get('avgThreePointFieldGoalsMade', 0)

    # Calculate games played from record (e.g., "25-20" = 45 games)
    games_played = 1
    try:
        parts = record.replace(' ', '').split('-')
        games_played = sum(int(p) for p in parts if p.isdigit()) or 1
    except (ValueError, AttributeError):
        games_played = 1

    # Get opponent PPG from merged defensive stats or fallback to other keys
    opp_ppg_raw = raw.get('opp_ppg', raw.get('avgPointsAgainst', raw.get('oppPointsPerGame', 0)))

    # If opp_ppg looks like a season total (>200), convert to per-game average
    # VALIDATION: For basketball, OPP PPG should be between 50-150 (reasonable range)
    # If the value is outside this range, it's clearly wrong data and should be hidden
    opp_ppg = 0
    try:
        opp_val = float(opp_ppg_raw)
        if opp_val > 200:  # This is a season total, convert to average
            converted = opp_val / games_played
            # Validate the converted value is reasonable (50-150 for basketball)
            if 50 <= converted <= 150:
                opp_ppg = converted
            else:
                opp_ppg = 0  # Converted value is still invalid
        elif 50 <= opp_val <= 150:  # Reasonable per-game value for basketball
            opp_ppg = opp_val
        else:
            # Value is suspicious (too low like 13.3 or too high) - treat as invalid
            opp_ppg = 0
    except (ValueError, TypeError):
        opp_ppg = 0

    # Calculate Net Rating proxy (PPG - OPP_PPG)
    net_rtg = '-'
    try:
        if ppg and opp_ppg and float(opp_ppg) > 0:
            net_val = float(ppg) - float(opp_ppg)
            net_rtg = f"{net_val:+.1f}"
    except (ValueError, TypeError):
        pass

    standings = standings or {}
    betting_rec = betting_rec or {}

    # Opponent shooting percentages (from merged defensive stats or fallback)
    opp_fg_pct_val = raw.get('opp_fg_pct', raw.get('oppFieldGoalPct', raw.get('avgPointsAgainstPerFieldGoalAttempt')))
    opp_3pt_pct_val = raw.get('opp_3pt_pct', raw.get('oppThreePointPct', raw.get('oppThreePointFieldGoalPct')))
    opp_fg_pct = safe_pct(opp_fg_pct_val) if opp_fg_pct_val and opp_fg_pct_val != '-' else '-'
    opp_3pt_pct = safe_pct(opp_3pt_pct_val) if opp_3pt_pct_val and opp_3pt_pct_val != '-' else '-'

    return {
        # Offense
        'ppg': safe_num(ppg),
        'fg_pct': safe_pct(raw.get('fieldGoalPct')),
        'three_pct': safe_pct(raw.get('threePointPct', raw.get('threePointFieldGoalPct'))),
        'ft_pct': safe_pct(raw.get('freeThrowPct')),
        'ast': safe_num(raw.get('avgAssists', raw.get('assistsPerGame'))),
        'reb': safe_num(raw.get('avgRebounds', raw.get('reboundsPerGame'))),
        'oreb': safe_num(raw.get('avgOffensiveRebounds', raw.get('offReboundsPerGame'))),
        # Defense - Enhanced with opponent shooting
        'opp_ppg': safe_num(opp_ppg),
        'opp_fg_pct': opp_fg_pct if opp_fg_pct != '-' else '-',
        'opp_3pt_pct': opp_3pt_pct if opp_3pt_pct != '-' else '-',
        'stl': safe_num(raw.get('avgSteals', raw.get('stealsPerGame'))),
        'blk': safe_num(raw.get('avgBlocks', raw.get('blocksPerGame'))),
        'dreb': safe_num(raw.get('avgDefensiveRebounds', raw.get('defReboundsPerGame'))),
        # Efficiency
        'to': safe_num(raw.get('avgTurnovers', raw.get('turnoversPerGame'))),
        'ast_to': safe_num(raw.get('assistTurnoverRatio')),
        'pf': safe_num(raw.get('avgFouls', raw.get('foulsPerGame'))),
        # Shooting
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
        # NEW: Advanced/Situational
        'net_rtg': net_rtg,
        'home_rec': standings.get('home_rec', '-'),
        'away_rec': standings.get('away_rec', '-'),
        'streak': standings.get('streak', '-'),
        'l5': l5,
        # NEW: ATS/O/U from Covers.com
        'ats': betting_rec.get('ats', '-'),
        'ou': betting_rec.get('ou', '-'),
    }

def get_nfl_games_played(record: str) -> int:
    """Calculate games played from NFL record"""
    try:
        parts = record.replace(' ', '').split('-')
        return sum(int(p) for p in parts if p.isdigit())
    except (ValueError, AttributeError):
        return 1

def extract_nfl_stats(raw: Dict, record: str, standings: Dict = None, l5: str = '-', betting_rec: Dict = None) -> Dict:
    """Extract comprehensive NFL stats including ATS/O/U"""
    games = get_nfl_games_played(record)
    total_yards = raw.get('totalYards', 0)
    total_plays = raw.get('totalOffensivePlays', 1)
    ypp_calc = '-'
    try:
        if total_yards and total_plays:
            ypp_calc = f"{float(total_yards) / float(total_plays):.2f}"
    except (ValueError, TypeError, ZeroDivisionError):
        pass

    top_val = raw.get('avgTimeOfPossession', raw.get('possessionTime', raw.get('possessionTimeSeconds')))
    standings = standings or {}
    betting_rec = betting_rec or {}

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
        'sacks': f"{safe_float(raw.get('sacks')) / games:.1f}" if games > 0 and raw.get('sacks') and safe_float(raw.get('sacks')) > 10 else safe_num(raw.get('sacks'), 0),
        'ints': f"{safe_float(raw.get('interceptions')) / games:.1f}" if games > 0 and raw.get('interceptions') and safe_float(raw.get('interceptions')) > 8 else safe_num(raw.get('interceptions'), 0),
        'tfl': f"{safe_float(raw.get('tacklesForLoss')) / games:.1f}" if games > 0 and raw.get('tacklesForLoss') and safe_float(raw.get('tacklesForLoss')) > 15 else safe_num(raw.get('tacklesForLoss'), 0),
        'ff': f"{safe_float(raw.get('fumblesForced')) / games:.1f}" if games > 0 and raw.get('fumblesForced') and safe_float(raw.get('fumblesForced')) > 5 else safe_num(raw.get('fumblesForced'), 0),
        'pd': f"{safe_float(raw.get('passesDefended')) / games:.1f}" if games > 0 and raw.get('passesDefended') and safe_float(raw.get('passesDefended')) > 20 else safe_num(raw.get('passesDefended'), 0),
        # Efficiency
        'ypp': safe_num(raw.get('yardsPerPlay')) if raw.get('yardsPerPlay') else ypp_calc,
        'ypa': safe_num(raw.get('yardsPerPassAttempt'), 1),
        'ypr': safe_num(raw.get('yardsPerRushAttempt'), 1),
        'ypc': safe_num(raw.get('yardsPerReception'), 1),
        # Situational
        'third_pct': safe_pct(raw.get('thirdDownConvPct')),
        'fourth_pct': safe_pct(raw.get('fourthDownConvPct')),
        'rz_pct': safe_pct(raw.get('redzoneTouchdownPct', raw.get('redzoneEfficiencyPct'))),
        'rz_score': safe_pct(raw.get('redzoneScoringPct')),
        'to_diff': raw.get('turnOverDifferential', raw.get('takeawayGiveawayDiff', '-')),
        'top': format_top(top_val, games),
        # Special Teams
        'fg_pct': safe_pct(raw.get('fieldGoalPct')),
        'punt_avg': safe_num(raw.get('grossAvgPuntYards'), 1),
        'kr_avg': safe_num(raw.get('yardsPerKickReturn'), 1),
        # Additional
        'first_downs': f"{safe_float(raw.get('firstDowns')) / games:.1f}" if games > 0 and raw.get('firstDowns') and safe_float(raw.get('firstDowns')) > 50 else safe_num(raw.get('firstDowns'), 0),
        'rush_td': f"{safe_float(raw.get('rushingTouchdowns')) / games:.1f}" if games > 0 and raw.get('rushingTouchdowns') and safe_float(raw.get('rushingTouchdowns')) > 5 else safe_num(raw.get('rushingTouchdowns'), 0),
        'pass_td': f"{safe_float(raw.get('passingTouchdowns')) / games:.1f}" if games > 0 and raw.get('passingTouchdowns') and safe_float(raw.get('passingTouchdowns')) > 8 else safe_num(raw.get('passingTouchdowns'), 0),
        'penalties': f"{safe_float(raw.get('totalPenalties')) / games:.1f}" if games > 0 and raw.get('totalPenalties') and safe_float(raw.get('totalPenalties')) > 20 else safe_num(raw.get('totalPenalties'), 0),
        'pen_yds': f"{safe_float(raw.get('totalPenaltyYards')) / games:.1f}" if games > 0 and raw.get('totalPenaltyYards') and safe_float(raw.get('totalPenaltyYards')) > 150 else safe_num(raw.get('totalPenaltyYards'), 0),
        'pwr': get_power_rating(record),
        # NEW: Situational
        'home_rec': standings.get('home_rec', '-'),
        'away_rec': standings.get('away_rec', '-'),
        'streak': standings.get('streak', '-'),
        'l5': l5,
        # NEW: ATS/O/U from Covers.com
        'ats': betting_rec.get('ats', '-'),
        'ou': betting_rec.get('ou', '-'),
    }

def get_games_played(record: str) -> int:
    """Calculate games played from record"""
    try:
        parts = record.replace(' ', '').split('-')
        return sum(int(p) for p in parts if p.isdigit())
    except (ValueError, AttributeError):
        return 1

def extract_nhl_stats(raw: Dict, record: str, standings: Dict = None, l5: str = '-', betting_rec: Dict = None) -> Dict:
    """Extract comprehensive NHL stats including ATS/O/U"""
    games = get_games_played(record)
    gf_total = raw.get('goals', raw.get('goalsFor', 0))
    ga_total = raw.get('goalsAgainst', 0)

    try:
        gf = f"{float(gf_total) / games:.1f}" if games > 0 else '-'
    except (ValueError, TypeError, ZeroDivisionError):
        gf = safe_num(raw.get('goalsPerGame', raw.get('avgGoals')))

    try:
        ga = f"{float(ga_total) / games:.1f}" if games > 0 else '-'
    except (ValueError, TypeError, ZeroDivisionError):
        ga = safe_num(raw.get('avgGoalsAgainst', raw.get('goalsAgainstPerGame')))

    gd = '-'
    try:
        gd_val = float(gf) - float(ga)
        gd = f"{gd_val:+.1f}"
    except (ValueError, TypeError):
        pass

    sog_total = raw.get('shotsTotal', raw.get('shots', 0))
    try:
        sog = f"{float(sog_total) / games:.1f}" if games > 0 and sog_total else '-'
    except (ValueError, TypeError, ZeroDivisionError):
        sog = safe_num(raw.get('shotsPerGame', raw.get('avgShotsPerGame')))

    sa_total = raw.get('shotsAgainst', 0)
    try:
        sa = f"{float(sa_total) / games:.1f}" if games > 0 and sa_total else '-'
    except (ValueError, TypeError, ZeroDivisionError):
        sa = safe_num(raw.get('shotsAgainstPerGame'))

    pim_total = raw.get('penaltyMinutes', 0)
    try:
        pim = f"{float(pim_total) / games:.1f}" if games > 0 and pim_total else '-'
    except (ValueError, TypeError, ZeroDivisionError):
        pim = safe_num(raw.get('penaltyMinutesPerGame', raw.get('pimPerGame')))

    standings = standings or {}
    betting_rec = betting_rec or {}

    return {
        # Offense
        'gf': gf,
        'sog': sog if sog != '-' else safe_num(raw.get('shotsPerGame')),
        'ppg': safe_num(raw.get('powerPlayGoals'), 0),
        'pp_pct': safe_pct(raw.get('powerPlayPct')),
        'shoot_pct': safe_pct(raw.get('shootingPct', raw.get('shootingPctg'))),
        'fow_pct': safe_pct(raw.get('faceoffPercent', raw.get('faceoffWinPct'))),
        'assists': safe_num(raw.get('assists'), 0),
        'pts_total': safe_num(raw.get('points'), 0),
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
        # NEW: Situational
        'home_rec': standings.get('home_rec', '-'),
        'away_rec': standings.get('away_rec', '-'),
        'streak': standings.get('streak', '-'),
        'l5': l5,
        # NEW: ATS/O/U from Covers.com
        'ats': betting_rec.get('ats', '-'),
        'ou': betting_rec.get('ou', '-'),
    }

def extract_ncaab_stats(raw: Dict, record: str, standings: Dict = None, l5: str = '-', betting_rec: Dict = None) -> Dict:
    return extract_nba_stats(raw, record, standings, l5, betting_rec)

def extract_ncaaf_stats(raw: Dict, record: str, standings: Dict = None, l5: str = '-', betting_rec: Dict = None) -> Dict:
    return extract_nfl_stats(raw, record, standings, l5, betting_rec)

# =============================================================================
# ODDS MATCHING
# =============================================================================

def has_valid_odds(odds: Dict) -> bool:
    """Check if odds data has real values (not placeholders)"""
    if not odds:
        return False
    spread = odds.get('spread_away', '-')
    ml = odds.get('ml_away', '-')
    total = odds.get('total', '-')
    if spread == '-' or ml == '-' or total == '-':
        return False
    return True

def match_game_odds(espn_game: Dict, odds_data: List[Dict]) -> Dict:
    """Match ESPN game with odds data"""
    result = {
        'spread_away': '-',
        'spread_home': '-',
        'ml_away': '-',
        'ml_home': '-',
        'total': '-',
    }

    comp = espn_game.get('competitions', [{}])[0]
    competitors = comp.get('competitors', [])

    away_team = None
    home_team = None
    for team in competitors:
        if team.get('homeAway') == 'away':
            away_team = team.get('team', {}).get('displayName', '').lower()
        else:
            home_team = team.get('team', {}).get('displayName', '').lower()

    if not away_team or not home_team:
        return result

    for odds_game in odds_data:
        odds_away = odds_game.get('away_team', '').lower()
        odds_home = odds_game.get('home_team', '').lower()

        def teams_match(t1, t2):
            t1_words = set(t1.split())
            t2_words = set(t2.split())
            return bool(t1_words & t2_words)

        if teams_match(away_team, odds_away) and teams_match(home_team, odds_home):
            bookmakers = odds_game.get('bookmakers', [])
            for book in bookmakers:
                if book.get('key') in ['fanduel', 'draftkings', 'betmgm', 'caesars', 'bovada', 'pinnacle']:
                    markets = book.get('markets', [])
                    for market in markets:
                        if market.get('key') == 'spreads':
                            for outcome in market.get('outcomes', []):
                                if outcome.get('name', '').lower() == odds_away:
                                    point = outcome.get('point', 0)
                                    result['spread_away'] = f"{point:+.1f}" if point else '-'
                                    result['spread_home'] = f"{-point:+.1f}" if point else '-'
                        elif market.get('key') == 'h2h':
                            for outcome in market.get('outcomes', []):
                                price = outcome.get('price', 0)
                                price_str = f"{price:+d}" if price else '-'
                                if outcome.get('name', '').lower() == odds_away:
                                    result['ml_away'] = price_str
                                else:
                                    result['ml_home'] = price_str
                        elif market.get('key') == 'totals':
                            for outcome in market.get('outcomes', []):
                                if outcome.get('name', '').lower() == 'over':
                                    result['total'] = outcome.get('point', '-')
                    break
            break

    return result

# =============================================================================
# GAME PROCESSING
# =============================================================================

def is_game_completed(game: Dict) -> bool:
    status = game.get('status', {})
    state = status.get('type', {}).get('state', '')
    return state.lower() == 'post'

def is_important_ncaab_game(game: Dict, has_odds: bool = False) -> bool:
    if has_odds:
        return True
    competitors = game.get('competitions', [{}])[0].get('competitors', [])
    for team in competitors:
        team_name = team.get('team', {}).get('displayName', '').lower()
        if team.get('curatedRank', {}).get('current'):
            return True
        for top_team in TOP_NCAAB_TEAMS:
            if top_team in team_name:
                return True
    return False

def is_bowl_game(game: Dict) -> bool:
    game_name = game.get('name', '').lower()
    short_name = game.get('shortName', '').lower()
    notes = game.get('competitions', [{}])[0].get('notes', [{}])
    headline = notes[0].get('headline', '').lower() if notes else ''
    bowl_keywords = ['bowl', 'playoff', 'championship', 'fiesta', 'rose', 'sugar',
                     'orange', 'cotton', 'peach', 'alamo', 'citrus', 'music city',
                     'liberty', 'holiday', 'sun', 'gator', 'duke', 'mayo', 'pop-tarts']
    for keyword in bowl_keywords:
        if keyword in game_name or keyword in short_name or keyword in headline:
            return True
    return False

def process_game(espn_game: Dict, sport: str, sport_path: str, odds_data: List[Dict], betting_records: Dict = None) -> Optional[Dict]:
    """Process a single game with all data including new situational stats and ATS/O/U"""
    if is_game_completed(espn_game):
        return None

    comp = espn_game.get('competitions', [{}])[0]
    competitors = comp.get('competitors', [])

    away_data = None
    home_data = None
    for team in competitors:
        if team.get('homeAway') == 'away':
            away_data = team
        else:
            home_data = team

    if not away_data or not home_data:
        return None

    # Get basic info
    away_info = away_data.get('team', {})
    home_info = home_data.get('team', {})
    away_id = away_info.get('id', '')
    home_id = home_info.get('id', '')
    away_abbr = away_info.get('abbreviation', 'UNK')
    home_abbr = home_info.get('abbreviation', 'UNK')

    # Fetch all data including new situational stats
    print(f"  Fetching stats for {away_abbr} @ {home_abbr}...")

    away_stats_raw = fetch_team_statistics(sport_path, away_id)
    home_stats_raw = fetch_team_statistics(sport_path, home_id)
    away_record = fetch_team_record(sport_path, away_id)
    home_record = fetch_team_record(sport_path, home_id)
    away_injuries = fetch_team_injuries(sport_path, away_id)
    home_injuries = fetch_team_injuries(sport_path, home_id)

    # NEW: Fetch defensive stats (opp_ppg, etc.)
    away_def_stats = fetch_defensive_stats(sport_path, away_id)
    home_def_stats = fetch_defensive_stats(sport_path, home_id)

    # Merge defensive stats into raw stats
    away_stats_raw.update(away_def_stats)
    home_stats_raw.update(home_def_stats)

    # NEW: Fetch situational data
    away_standings = fetch_team_standings_details(sport_path, away_id)
    home_standings = fetch_team_standings_details(sport_path, home_id)
    away_l5 = fetch_team_l5_record(sport_path, away_id)
    home_l5 = fetch_team_l5_record(sport_path, home_id)

    # NEW: Get ATS/O/U betting records from Covers.com
    betting_records = betting_records or {}
    away_betting = betting_records.get(away_abbr, {})
    home_betting = betting_records.get(home_abbr, {})

    # NEW: Fetch Head-to-Head data from Covers.com
    h2h_data = None
    if sport in ['NBA', 'NHL', 'NFL', 'NCAAB', 'NCAAF']:  # All sports with Covers.com H2H
        print(f"  [H2H] Fetching H2H for {away_abbr} @ {home_abbr}...")
        h2h_data = fetch_h2h_data(sport, away_abbr, home_abbr)
        if h2h_data:
            print(f"  [H2H] Found {h2h_data['total_games']} meetings: {h2h_data['h2h_su']} | {h2h_data['h2h_ats']} | {h2h_data['h2h_ou']}")

    # Extract stats based on sport
    if sport in ['NBA', 'NCAAB']:
        away_stats = extract_nba_stats(away_stats_raw, away_record, away_standings, away_l5, away_betting)
        home_stats = extract_nba_stats(home_stats_raw, home_record, home_standings, home_l5, home_betting)
    elif sport in ['NFL', 'NCAAF']:
        away_stats = extract_nfl_stats(away_stats_raw, away_record, away_standings, away_l5, away_betting)
        home_stats = extract_nfl_stats(home_stats_raw, home_record, home_standings, home_l5, home_betting)
    else:  # NHL
        away_stats = extract_nhl_stats(away_stats_raw, away_record, away_standings, away_l5, away_betting)
        home_stats = extract_nhl_stats(home_stats_raw, home_record, home_standings, home_l5, home_betting)

    # Match odds
    odds = match_game_odds(espn_game, odds_data)

    # Get game info
    venue = comp.get('venue', {}).get('fullName', 'TBD')
    broadcasts = comp.get('broadcasts', [])
    network = broadcasts[0].get('names', [''])[0] if broadcasts else ''

    # Format time
    game_date_str = espn_game.get('date', '')
    try:
        game_dt = datetime.fromisoformat(game_date_str.replace('Z', '+00:00'))
        if EASTERN:
            game_eastern = game_dt.astimezone(EASTERN)
            game_time = game_eastern.strftime('%I:%M %p ET')
        else:
            game_eastern = game_dt.replace(tzinfo=None) - timedelta(hours=5)
            game_time = game_eastern.strftime('%I:%M %p ET')
    except Exception:
        game_time = 'TBD'

    return {
        'event_id': espn_game.get('id', ''),
        'away': {
            'name': away_info.get('displayName', 'Unknown'),
            'abbr': away_info.get('abbreviation', 'UNK'),
            'record': away_record,
            'team_id': away_id,
            'stats': away_stats,
            'injuries': away_injuries,
        },
        'home': {
            'name': home_info.get('displayName', 'Unknown'),
            'abbr': home_info.get('abbreviation', 'UNK'),
            'record': home_record,
            'team_id': home_id,
            'stats': home_stats,
            'injuries': home_injuries,
        },
        'odds': odds,
        'time': game_time,
        'venue': venue,
        'network': network,
        'h2h': h2h_data,  # Head-to-head data from Covers.com
    }

# =============================================================================
# HTML GENERATION - ENHANCED TEMPLATES
# =============================================================================

def get_logo_url(sport: str, abbr: str, team_id: str = '') -> str:
    abbr_lower = abbr.lower()
    if sport == 'NFL':
        return f"https://a.espncdn.com/i/teamlogos/nfl/500/scoreboard/{abbr_lower}.png"
    elif sport == 'NBA':
        return f"https://a.espncdn.com/i/teamlogos/nba/500/scoreboard/{abbr_lower}.png"
    elif sport == 'NHL':
        return f"https://a.espncdn.com/i/teamlogos/nhl/500/scoreboard/{abbr_lower}.png"
    elif sport == 'NCAAF':
        if team_id:
            return f"https://a.espncdn.com/i/teamlogos/ncaa/500/{team_id}.png"
        return f"https://a.espncdn.com/i/teamlogos/ncaa/500/{abbr_lower}.png"
    elif sport == 'NCAAB':
        if team_id:
            return f"https://a.espncdn.com/i/teamlogos/ncaa/500/{team_id}.png"
        return f"https://a.espncdn.com/i/teamlogos/ncaa/500/{abbr_lower}.png"
    return ""

def generate_game_card_nba(game: Dict, sport: str = 'NBA') -> str:
    """Generate NBA/NCAAB game card with ENHANCED Section 3 + H2H"""
    away = game['away']
    home = game['home']
    odds = game['odds']
    h2h = game.get('h2h')  # Head-to-head data

    away_inj_html = format_injuries_html(away.get('injuries', []), away['abbr'])
    home_inj_html = format_injuries_html(home.get('injuries', []), home['abbr'])
    away_logo = get_logo_url(sport, away['abbr'], away.get('team_id', ''))
    home_logo = get_logo_url(sport, home['abbr'], home.get('team_id', ''))

    # Generate H2H section HTML if data available
    h2h_html = ''
    if h2h and h2h.get('total_games', 0) > 0:
        import re as re_h2h
        meetings_html = ''
        for m in h2h.get('meetings', [])[:5]:
            # Parse who won from result (home score first, away score second)
            scores = re_h2h.findall(r'(\d+)', m['result'])
            home_team = m['home'].upper()
            if len(scores) >= 2:
                home_score = int(scores[0])
                away_score = int(scores[1])
                if home_score > away_score:
                    winner = home_team
                    winner_class = 'winner-home'
                else:
                    # Away team won - figure out who that is
                    winner = away['abbr'] if home_team == home['abbr'] else home['abbr']
                    winner_class = 'winner-away'
                score_display = f"{home_score}-{away_score}"
            else:
                winner = "—"
                winner_class = ''
                score_display = m['result']

            # Parse who covered from ATS (format like "OKC-5.5" or "MIL+3.0")
            ats_match = re_h2h.match(r'([A-Z]+)', m['ats'])
            covered_team = ats_match.group(1) if ats_match else "—"

            # Parse O/U (format like "o233.5" or "u233.5")
            ou_val = m['ou'].lower()
            if ou_val.startswith('o'):
                ou_display = '<span class="over">OVER</span>'
            elif ou_val.startswith('u'):
                ou_display = '<span class="under">UNDER</span>'
            else:
                ou_display = m['ou']

            meetings_html += f'''<tr>
                <td>{m["date"]}</td>
                <td class="{winner_class}"><strong>{winner}</strong></td>
                <td class="score">{score_display}</td>
                <td class="h2h-ats"><strong>{covered_team}</strong></td>
                <td class="h2h-ou">{ou_display}</td>
            </tr>'''

        # Parse clearer H2H display
        su_parts = h2h['h2h_su'].split()  # "OKC 3-2" -> ["OKC", "3-2"]
        t1_abbr = away['abbr']
        t2_abbr = home['abbr']
        su_record = su_parts[1] if len(su_parts) > 1 else "0-0"
        su_wins = su_record.split('-')
        t1_wins = su_wins[0] if len(su_wins) > 0 else "0"
        t2_wins = su_wins[1] if len(su_wins) > 1 else "0"

        ats_parts = h2h['h2h_ats'].replace(' ATS', '').split('-')
        ats_t1 = ats_parts[0] if len(ats_parts) > 0 else "0"
        ats_t2 = ats_parts[1] if len(ats_parts) > 1 else "0"

        ou_parts = h2h['h2h_ou']  # "1O-4U"
        overs = ou_parts.split('O')[0] if 'O' in ou_parts else "0"
        unders = ou_parts.split('-')[1].replace('U', '') if '-' in ou_parts else "0"

        h2h_html = f'''
        <!-- SECTION 5: HEAD-TO-HEAD -->
        <div class="h2h-section">
            <div class="section-title">HEAD-TO-HEAD (Last {h2h['total_games']} Meetings)</div>
            <div class="h2h-summary">
                <div class="h2h-stat h2h-su">
                    <span class="h2h-stat-label">STRAIGHT UP</span>
                    <span class="h2h-stat-value">{t1_abbr} {t1_wins} - {t2_wins} {t2_abbr}</span>
                </div>
                <div class="h2h-stat h2h-ats-summary">
                    <span class="h2h-stat-label">ATS RECORD</span>
                    <span class="h2h-stat-value">{t1_abbr} {ats_t1} - {ats_t2} {t2_abbr}</span>
                </div>
                <div class="h2h-stat h2h-ou-summary">
                    <span class="h2h-stat-label">OVER / UNDER</span>
                    <span class="h2h-stat-value">{overs} OVER - {unders} UNDER</span>
                </div>
            </div>
            <table class="h2h-table">
                <thead><tr><th>DATE</th><th>WINNER</th><th>SCORE</th><th>COVERED</th><th>O/U</th></tr></thead>
                <tbody>{meetings_html}</tbody>
            </table>
        </div>'''

    betting_lines_html = ''
    if has_valid_odds(odds):
        betting_lines_html = f'''
        <div class="section betting-lines-full">
            <div class="section-title">MATCHUP & BETTING (ScoresAndOdds Style)</div>
            <table class="lines-table-full">
                <thead>
                    <tr><th class="team-col">TEAM</th><th>LINE</th><th>ML</th><th>O/U</th><th>SU</th><th>ATS</th><th>O/U REC</th><th>PPG</th><th>OPP</th><th>PWR</th></tr>
                </thead>
                <tbody>
                    <tr class="away-row">
                        <td class="team-col">
                            <img src="{away_logo}" class="team-logo" onerror="this.style.display='none'">
                            <span class="team-name">{away['abbr']}</span>
                        </td>
                        <td class="spread">{odds['spread_away']}</td>
                        <td class="ml">{odds['ml_away']}</td>
                        <td class="total">O {odds['total']}</td>
                        <td class="su-record">{away['record']}</td>
                        <td class="ats-record">{away['stats']['ats']}</td>
                        <td class="ou-record">{away['stats']['ou']}</td>
                        <td class="ppg">{away['stats']['ppg']}</td>
                        <td class="opp-ppg">{away['stats']['opp_ppg']}</td>
                        <td class="pwr">{away['stats']['pwr']}</td>
                    </tr>
                    <tr class="home-row">
                        <td class="team-col">
                            <img src="{home_logo}" class="team-logo" onerror="this.style.display='none'">
                            <span class="team-name">{home['abbr']}</span>
                        </td>
                        <td class="spread">{odds['spread_home']}</td>
                        <td class="ml">{odds['ml_home']}</td>
                        <td class="total">U {odds['total']}</td>
                        <td class="su-record">{home['record']}</td>
                        <td class="ats-record">{home['stats']['ats']}</td>
                        <td class="ou-record">{home['stats']['ou']}</td>
                        <td class="ppg">{home['stats']['ppg']}</td>
                        <td class="opp-ppg">{home['stats']['opp_ppg']}</td>
                        <td class="pwr">{home['stats']['pwr']}</td>
                    </tr>
                </tbody>
            </table>
        </div>'''
    else:
        betting_lines_html = f'''
        <div class="section betting-lines-full">
            <div class="section-title">MATCHUP (No Odds Available)</div>
            <table class="lines-table-full">
                <thead><tr><th class="team-col">TEAM</th><th>SU</th><th>ATS</th><th>O/U REC</th><th>PPG</th><th>OPP</th><th>PWR</th></tr></thead>
                <tbody>
                    <tr class="away-row">
                        <td class="team-col">
                            <img src="{away_logo}" class="team-logo" onerror="this.style.display='none'">
                            <span class="team-name">{away['abbr']}</span>
                        </td>
                        <td class="su-record">{away['record']}</td>
                        <td class="ats-record">{away['stats']['ats']}</td>
                        <td class="ou-record">{away['stats']['ou']}</td>
                        <td class="ppg">{away['stats']['ppg']}</td>
                        <td class="opp-ppg">{away['stats']['opp_ppg']}</td>
                        <td class="pwr">{away['stats']['pwr']}</td>
                    </tr>
                    <tr class="home-row">
                        <td class="team-col">
                            <img src="{home_logo}" class="team-logo" onerror="this.style.display='none'">
                            <span class="team-name">{home['abbr']}</span>
                        </td>
                        <td class="su-record">{home['record']}</td>
                        <td class="ats-record">{home['stats']['ats']}</td>
                        <td class="ou-record">{home['stats']['ou']}</td>
                        <td class="ppg">{home['stats']['ppg']}</td>
                        <td class="opp-ppg">{home['stats']['opp_ppg']}</td>
                        <td class="pwr">{home['stats']['pwr']}</td>
                    </tr>
                </tbody>
            </table>
        </div>'''

    # Format injuries section cleanly
    injuries_html = ''
    if away_inj_html != 'No reported injuries' or home_inj_html != 'No reported injuries':
        injuries_html = f'''
        <div class="section injuries-section">
            <div class="section-title">INJURIES</div>
            <div class="injuries-content">
                <div class="team-injuries"><strong>{away['abbr']}:</strong> {away_inj_html}</div>
                <div class="team-injuries"><strong>{home['abbr']}:</strong> {home_inj_html}</div>
            </div>
        </div>'''

    return f'''
    <div class="game-card" data-event-id="{game.get('event_id', '')}" data-sport="{sport.lower()}">
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
                    <thead><tr><th></th><th>PPG</th><th>FG%</th><th>3P%</th><th>FT%</th><th>AST</th><th>REB</th></tr></thead>
                    <tbody>
                        <tr><td class="team-abbr">{away['abbr']}</td><td>{away['stats']['ppg']}</td><td>{away['stats']['fg_pct']}</td><td>{away['stats']['three_pct']}</td><td>{away['stats']['ft_pct']}</td><td>{away['stats']['ast']}</td><td>{away['stats']['reb']}</td></tr>
                        <tr><td class="team-abbr">{home['abbr']}</td><td>{home['stats']['ppg']}</td><td>{home['stats']['fg_pct']}</td><td>{home['stats']['three_pct']}</td><td>{home['stats']['ft_pct']}</td><td>{home['stats']['ast']}</td><td>{home['stats']['reb']}</td></tr>
                    </tbody>
                </table>
            </div>
            <div class="section defense">
                <div class="section-title">DEFENSE</div>
                <table class="stats-table">
                    <thead><tr><th></th><th>OPP PPG</th><th>STL</th><th>BLK</th><th>DREB</th></tr></thead>
                    <tbody>
                        <tr><td class="team-abbr">{away['abbr']}</td><td>{away['stats']['opp_ppg']}</td><td>{away['stats']['stl']}</td><td>{away['stats']['blk']}</td><td>{away['stats']['dreb']}</td></tr>
                        <tr><td class="team-abbr">{home['abbr']}</td><td>{home['stats']['opp_ppg']}</td><td>{home['stats']['stl']}</td><td>{home['stats']['blk']}</td><td>{home['stats']['dreb']}</td></tr>
                    </tbody>
                </table>
            </div>
        </div>

        {injuries_html}
        {h2h_html}
    </div>
    '''

def generate_game_card_nfl(game: Dict, sport: str = 'NFL') -> str:
    """Generate NFL/NCAAF game card with ENHANCED Section 3 + H2H"""
    away = game['away']
    home = game['home']
    odds = game['odds']
    h2h = game.get('h2h')  # Head-to-head data

    away_inj_html = format_injuries_html(away.get('injuries', []), away['abbr'])
    home_inj_html = format_injuries_html(home.get('injuries', []), home['abbr'])
    away_logo = get_logo_url(sport, away['abbr'], away.get('team_id', ''))
    home_logo = get_logo_url(sport, home['abbr'], home.get('team_id', ''))

    # Generate H2H section HTML if data available
    h2h_html = ''
    if h2h and h2h.get('total_games', 0) > 0:
        import re as re_h2h
        meetings_html = ''
        for m in h2h.get('meetings', [])[:5]:
            # Parse who won from result (home score first, away score second)
            scores = re_h2h.findall(r'(\d+)', m['result'])
            home_team = m['home'].upper()
            if len(scores) >= 2:
                home_score = int(scores[0])
                away_score = int(scores[1])
                if home_score > away_score:
                    winner = home_team
                    winner_class = 'winner-home'
                else:
                    winner = away['abbr'] if home_team == home['abbr'] else home['abbr']
                    winner_class = 'winner-away'
                score_display = f"{home_score}-{away_score}"
            else:
                winner = "—"
                winner_class = ''
                score_display = m['result']

            ats_match = re_h2h.match(r'([A-Z]+)', m['ats'])
            covered_team = ats_match.group(1) if ats_match else "—"

            ou_val = m['ou'].lower()
            if ou_val.startswith('o'):
                ou_display = '<span class="over">OVER</span>'
            elif ou_val.startswith('u'):
                ou_display = '<span class="under">UNDER</span>'
            else:
                ou_display = m['ou']

            meetings_html += f'''<tr>
                <td>{m["date"]}</td>
                <td class="{winner_class}"><strong>{winner}</strong></td>
                <td class="score">{score_display}</td>
                <td class="h2h-ats"><strong>{covered_team}</strong></td>
                <td class="h2h-ou">{ou_display}</td>
            </tr>'''

        # Parse clearer H2H display
        su_parts = h2h['h2h_su'].split()
        t1_abbr = away['abbr']
        t2_abbr = home['abbr']
        su_record = su_parts[1] if len(su_parts) > 1 else "0-0"
        su_wins = su_record.split('-')
        t1_wins = su_wins[0] if len(su_wins) > 0 else "0"
        t2_wins = su_wins[1] if len(su_wins) > 1 else "0"

        ats_parts = h2h['h2h_ats'].replace(' ATS', '').split('-')
        ats_t1 = ats_parts[0] if len(ats_parts) > 0 else "0"
        ats_t2 = ats_parts[1] if len(ats_parts) > 1 else "0"

        ou_parts = h2h['h2h_ou']
        overs = ou_parts.split('O')[0] if 'O' in ou_parts else "0"
        unders = ou_parts.split('-')[1].replace('U', '') if '-' in ou_parts else "0"

        h2h_html = f'''
        <!-- SECTION 5: HEAD-TO-HEAD -->
        <div class="h2h-section">
            <div class="section-title">HEAD-TO-HEAD (Last {h2h['total_games']} Meetings)</div>
            <div class="h2h-summary">
                <div class="h2h-stat h2h-su">
                    <span class="h2h-stat-label">STRAIGHT UP</span>
                    <span class="h2h-stat-value">{t1_abbr} {t1_wins} - {t2_wins} {t2_abbr}</span>
                </div>
                <div class="h2h-stat h2h-ats-summary">
                    <span class="h2h-stat-label">ATS RECORD</span>
                    <span class="h2h-stat-value">{t1_abbr} {ats_t1} - {ats_t2} {t2_abbr}</span>
                </div>
                <div class="h2h-stat h2h-ou-summary">
                    <span class="h2h-stat-label">OVER / UNDER</span>
                    <span class="h2h-stat-value">{overs} OVER - {unders} UNDER</span>
                </div>
            </div>
            <table class="h2h-table">
                <thead><tr><th>DATE</th><th>WINNER</th><th>SCORE</th><th>COVERED</th><th>O/U</th></tr></thead>
                <tbody>{meetings_html}</tbody>
            </table>
        </div>'''

    betting_lines_html = ''
    if has_valid_odds(odds):
        betting_lines_html = f'''
        <div class="section betting-lines">
            <div class="section-title">BETTING LINES</div>
            <table class="lines-table">
                <thead><tr><th class="team-col">TEAM</th><th>SPREAD</th><th>ML</th><th>O/U</th></tr></thead>
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
        betting_lines_html = f'''
        <div class="section teams-info">
            <div class="section-title">MATCHUP</div>
            <table class="lines-table">
                <thead><tr><th class="team-col">TEAM</th><th>RECORD</th></tr></thead>
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

    # Format injuries section cleanly
    injuries_html = ''
    if away_inj_html != 'No reported injuries' or home_inj_html != 'No reported injuries':
        injuries_html = f'''
        <div class="section injuries-section">
            <div class="section-title">INJURIES</div>
            <div class="injuries-content">
                <div class="team-injuries"><strong>{away['abbr']}:</strong> {away_inj_html}</div>
                <div class="team-injuries"><strong>{home['abbr']}:</strong> {home_inj_html}</div>
            </div>
        </div>'''

    return f'''
    <div class="game-card" data-event-id="{game.get('event_id', '')}" data-sport="{sport.lower()}">
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
                    <thead><tr><th></th><th>PPG</th><th>YPG</th><th>PASS</th><th>RUSH</th><th>3RD%</th></tr></thead>
                    <tbody>
                        <tr><td class="team-abbr">{away['abbr']}</td><td>{away['stats']['ppg']}</td><td>{away['stats']['ypg']}</td><td>{away['stats']['pass_ypg']}</td><td>{away['stats']['rush_ypg']}</td><td>{away['stats']['third_pct']}</td></tr>
                        <tr><td class="team-abbr">{home['abbr']}</td><td>{home['stats']['ppg']}</td><td>{home['stats']['ypg']}</td><td>{home['stats']['pass_ypg']}</td><td>{home['stats']['rush_ypg']}</td><td>{home['stats']['third_pct']}</td></tr>
                    </tbody>
                </table>
            </div>
            <div class="section defense">
                <div class="section-title">DEFENSE</div>
                <table class="stats-table">
                    <thead><tr><th></th><th>SACK</th><th>INT</th><th>TFL</th><th>FF</th><th>TO+/-</th></tr></thead>
                    <tbody>
                        <tr><td class="team-abbr">{away['abbr']}</td><td>{away['stats']['sacks']}</td><td>{away['stats']['ints']}</td><td>{away['stats']['tfl']}</td><td>{away['stats']['ff']}</td><td>{away['stats']['to_diff']}</td></tr>
                        <tr><td class="team-abbr">{home['abbr']}</td><td>{home['stats']['sacks']}</td><td>{home['stats']['ints']}</td><td>{home['stats']['tfl']}</td><td>{home['stats']['ff']}</td><td>{home['stats']['to_diff']}</td></tr>
                    </tbody>
                </table>
            </div>
        </div>

        {injuries_html}
        {h2h_html}
    </div>
    '''

def generate_game_card_nhl(game: Dict) -> str:
    """Generate NHL game card with ENHANCED Section 3 (PP%/PK% prominent) + H2H"""
    away = game['away']
    home = game['home']
    odds = game['odds']
    h2h = game.get('h2h')  # Head-to-head data

    away_inj_html = format_injuries_html(away.get('injuries', []), away['abbr'])
    home_inj_html = format_injuries_html(home.get('injuries', []), home['abbr'])

    # Generate H2H section HTML if data available
    h2h_html = ''
    if h2h and h2h.get('total_games', 0) > 0:
        import re as re_h2h
        meetings_html = ''
        for m in h2h.get('meetings', [])[:5]:
            # Parse who won from result (home score first, away score second)
            scores = re_h2h.findall(r'(\d+)', m['result'])
            home_team = m['home'].upper()
            if len(scores) >= 2:
                home_score = int(scores[0])
                away_score = int(scores[1])
                if home_score > away_score:
                    winner = home_team
                    winner_class = 'winner-home'
                else:
                    winner = away['abbr'] if home_team == home['abbr'] else home['abbr']
                    winner_class = 'winner-away'
                score_display = f"{home_score}-{away_score}"
            else:
                winner = "—"
                winner_class = ''
                score_display = m['result']

            ats_match = re_h2h.match(r'([A-Z]+)', m['ats'])
            covered_team = ats_match.group(1) if ats_match else "—"

            ou_val = m['ou'].lower()
            if ou_val.startswith('o'):
                ou_display = '<span class="over">OVER</span>'
            elif ou_val.startswith('u'):
                ou_display = '<span class="under">UNDER</span>'
            else:
                ou_display = m['ou']

            meetings_html += f'''<tr>
                <td>{m["date"]}</td>
                <td class="{winner_class}"><strong>{winner}</strong></td>
                <td class="score">{score_display}</td>
                <td class="h2h-ats"><strong>{covered_team}</strong></td>
                <td class="h2h-ou">{ou_display}</td>
            </tr>'''

        # Parse clearer H2H display with team abbreviations
        t1_abbr = away['abbr']
        t2_abbr = home['abbr']

        # Parse straight up record - format: "TEAM X-Y"
        su_parts = h2h['h2h_su'].split()
        su_record = su_parts[1] if len(su_parts) > 1 else "0-0"
        su_wins = su_record.split('-')
        t1_wins = su_wins[0] if len(su_wins) > 0 else "0"
        t2_wins = su_wins[1] if len(su_wins) > 1 else "0"

        # Parse ATS record - format: "X-Y ATS"
        ats_parts = h2h['h2h_ats'].split()
        ats_record = ats_parts[0] if len(ats_parts) > 0 else "0-0"
        ats_wins = ats_record.split('-')
        ats_t1 = ats_wins[0] if len(ats_wins) > 0 else "0"
        ats_t2 = ats_wins[1] if len(ats_wins) > 1 else "0"

        # Parse O/U record - format: "XO-YU"
        ou_str = h2h['h2h_ou']
        ou_match = re_h2h.match(r'(\d+)O-(\d+)U', ou_str)
        if ou_match:
            overs = ou_match.group(1)
            unders = ou_match.group(2)
        else:
            overs = "0"
            unders = "0"

        h2h_html = f'''
        <!-- SECTION 5: HEAD-TO-HEAD -->
        <div class="h2h-section">
            <div class="section-title">HEAD-TO-HEAD (Last {h2h['total_games']} Meetings)</div>
            <div class="h2h-summary">
                <div class="h2h-stat h2h-su">
                    <span class="h2h-stat-label">STRAIGHT UP</span>
                    <span class="h2h-stat-value">{t1_abbr} {t1_wins} - {t2_wins} {t2_abbr}</span>
                </div>
                <div class="h2h-stat h2h-ats-summary">
                    <span class="h2h-stat-label">ATS RECORD</span>
                    <span class="h2h-stat-value">{t1_abbr} {ats_t1} - {ats_t2} {t2_abbr}</span>
                </div>
                <div class="h2h-stat h2h-ou-summary">
                    <span class="h2h-stat-label">OVER / UNDER</span>
                    <span class="h2h-stat-value">{overs} OVER - {unders} UNDER</span>
                </div>
            </div>
            <table class="h2h-table">
                <thead><tr><th>DATE</th><th>WINNER</th><th>SCORE</th><th>COVERED</th><th>O/U</th></tr></thead>
                <tbody>{meetings_html}</tbody>
            </table>
        </div>'''

    away_logo = f"https://a.espncdn.com/i/teamlogos/nhl/500/scoreboard/{away['abbr'].lower()}.png"
    home_logo = f"https://a.espncdn.com/i/teamlogos/nhl/500/scoreboard/{home['abbr'].lower()}.png"

    betting_lines_html = ''
    if has_valid_odds(odds):
        betting_lines_html = f'''
        <div class="section betting-lines-full">
            <div class="section-title">MATCHUP & BETTING (ScoresAndOdds Style)</div>
            <table class="lines-table-full">
                <thead>
                    <tr><th class="team-col">TEAM</th><th>LINE</th><th>ML</th><th>O/U</th><th>SU</th><th>ATS</th><th>O/U REC</th><th>GPG</th><th>GA</th><th>PWR</th></tr>
                </thead>
                <tbody>
                    <tr class="away-row">
                        <td class="team-col">
                            <img src="{away_logo}" class="team-logo" onerror="this.style.display='none'">
                            <span class="team-name">{away['abbr']}</span>
                        </td>
                        <td class="spread">{odds['spread_away']}</td>
                        <td class="ml">{odds['ml_away']}</td>
                        <td class="total">O {odds['total']}</td>
                        <td class="su-record">{away['record']}</td>
                        <td class="ats-record">{away['stats']['ats']}</td>
                        <td class="ou-record">{away['stats']['ou']}</td>
                        <td class="ppg">{away['stats']['gf']}</td>
                        <td class="opp-ppg">{away['stats']['ga']}</td>
                        <td class="pwr">{away['stats']['pwr']}</td>
                    </tr>
                    <tr class="home-row">
                        <td class="team-col">
                            <img src="{home_logo}" class="team-logo" onerror="this.style.display='none'">
                            <span class="team-name">{home['abbr']}</span>
                        </td>
                        <td class="spread">{odds['spread_home']}</td>
                        <td class="ml">{odds['ml_home']}</td>
                        <td class="total">U {odds['total']}</td>
                        <td class="su-record">{home['record']}</td>
                        <td class="ats-record">{home['stats']['ats']}</td>
                        <td class="ou-record">{home['stats']['ou']}</td>
                        <td class="ppg">{home['stats']['gf']}</td>
                        <td class="opp-ppg">{home['stats']['ga']}</td>
                        <td class="pwr">{home['stats']['pwr']}</td>
                    </tr>
                </tbody>
            </table>
        </div>'''
    else:
        betting_lines_html = f'''
        <div class="section betting-lines-full">
            <div class="section-title">MATCHUP (No Odds Available)</div>
            <table class="lines-table-full">
                <thead><tr><th class="team-col">TEAM</th><th>SU</th><th>ATS</th><th>O/U REC</th><th>GPG</th><th>GA</th><th>PWR</th></tr></thead>
                <tbody>
                    <tr class="away-row">
                        <td class="team-col">
                            <img src="{away_logo}" class="team-logo" onerror="this.style.display='none'">
                            <span class="team-name">{away['abbr']}</span>
                        </td>
                        <td class="su-record">{away['record']}</td>
                        <td class="ats-record">{away['stats']['ats']}</td>
                        <td class="ou-record">{away['stats']['ou']}</td>
                        <td class="ppg">{away['stats']['gf']}</td>
                        <td class="opp-ppg">{away['stats']['ga']}</td>
                        <td class="pwr">{away['stats']['pwr']}</td>
                    </tr>
                    <tr class="home-row">
                        <td class="team-col">
                            <img src="{home_logo}" class="team-logo" onerror="this.style.display='none'">
                            <span class="team-name">{home['abbr']}</span>
                        </td>
                        <td class="su-record">{home['record']}</td>
                        <td class="ats-record">{home['stats']['ats']}</td>
                        <td class="ou-record">{home['stats']['ou']}</td>
                        <td class="ppg">{home['stats']['gf']}</td>
                        <td class="opp-ppg">{home['stats']['ga']}</td>
                        <td class="pwr">{home['stats']['pwr']}</td>
                    </tr>
                </tbody>
            </table>
        </div>'''

    # Format injuries section cleanly
    injuries_html = ''
    if away_inj_html != 'No reported injuries' or home_inj_html != 'No reported injuries':
        injuries_html = f'''
        <div class="section injuries-section">
            <div class="section-title">INJURIES</div>
            <div class="injuries-content">
                <div class="team-injuries"><strong>{away['abbr']}:</strong> {away_inj_html}</div>
                <div class="team-injuries"><strong>{home['abbr']}:</strong> {home_inj_html}</div>
            </div>
        </div>'''

    return f'''
    <div class="game-card" data-event-id="{game.get('event_id', '')}" data-sport="nhl">
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
                    <thead><tr><th></th><th>GF</th><th>SOG</th><th>S%</th><th>PP%</th><th>FO%</th></tr></thead>
                    <tbody>
                        <tr><td class="team-abbr">{away['abbr']}</td><td>{away['stats']['gf']}</td><td>{away['stats']['sog']}</td><td>{away['stats']['shoot_pct']}</td><td>{away['stats']['pp_pct']}</td><td>{away['stats']['fow_pct']}</td></tr>
                        <tr><td class="team-abbr">{home['abbr']}</td><td>{home['stats']['gf']}</td><td>{home['stats']['sog']}</td><td>{home['stats']['shoot_pct']}</td><td>{home['stats']['pp_pct']}</td><td>{home['stats']['fow_pct']}</td></tr>
                    </tbody>
                </table>
            </div>
            <div class="section defense">
                <div class="section-title">DEFENSE</div>
                <table class="stats-table">
                    <thead><tr><th></th><th>GA</th><th>SA</th><th>SV%</th><th>PK%</th><th>GD</th></tr></thead>
                    <tbody>
                        <tr><td class="team-abbr">{away['abbr']}</td><td>{away['stats']['ga']}</td><td>{away['stats']['sa']}</td><td>{away['stats']['sv_pct']}</td><td>{away['stats']['pk_pct']}</td><td>{away['stats']['gd']}</td></tr>
                        <tr><td class="team-abbr">{home['abbr']}</td><td>{home['stats']['ga']}</td><td>{home['stats']['sa']}</td><td>{home['stats']['sv_pct']}</td><td>{home['stats']['pk_pct']}</td><td>{home['stats']['gd']}</td></tr>
                    </tbody>
                </table>
            </div>
        </div>

        {injuries_html}
        {h2h_html}
    </div>
    '''

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

    # Scan archive folder for available dates
    archive_dir = os.path.join(REPO_PATH, 'handicapping-hub-archive')
    archive_dates = []
    if os.path.exists(archive_dir):
        for f in os.listdir(archive_dir):
            if f.startswith('hub-') and f.endswith('.html'):
                date_part = f[4:-5]  # Extract 2026-01-15 from hub-2026-01-15.html
                if re.match(r'\d{4}-\d{2}-\d{2}', date_part):
                    archive_dates.append(date_part)
    archive_dates_json = json.dumps(sorted(archive_dates))

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

    # Simplified page without full CSS (for brevity, using production CSS)
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Handicapping Hub PREVIEW - {date_str} | BetLegend</title>
    <meta name="description" content="PREVIEW VERSION - Enhanced with advanced stats and situational data">
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&family=Rajdhani:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        /* === FUTURISTIC DARK THEME === */
        body {{
            font-family: 'Rajdhani', sans-serif;
            background: linear-gradient(135deg, #0a0a1a 0%, #1a1a3a 50%, #0d0d2b 100%);
            color: #e0e0e0;
            line-height: 1.5;
            min-height: 100vh;
        }}


        .nav {{
            background: linear-gradient(180deg, rgba(10, 10, 30, 0.98) 0%, rgba(20, 20, 50, 0.95) 100%);
            padding: 15px 25px;
            position: fixed;
            top: 0; left: 0; right: 0;
            z-index: 1000;
            border-bottom: 2px solid #00f5ff;
            box-shadow: 0 4px 30px rgba(0, 245, 255, 0.2);
        }}
        .nav-inner {{ max-width: 1400px; margin: 0 auto; display: flex; justify-content: space-between; align-items: center; }}
        .logo {{
            font-family: 'Orbitron', sans-serif;
            font-size: 1.8rem;
            font-weight: 900;
            color: #00f5ff;
            text-decoration: none;
            text-shadow: 0 0 20px rgba(0, 245, 255, 0.5);
            letter-spacing: 3px;
        }}
        .logo span {{ color: #ff6b35; text-shadow: 0 0 20px rgba(255, 107, 53, 0.5); }}

        .header {{
            background: linear-gradient(135deg, #0d0d2b 0%, #1a1a4a 50%, #0a0a2a 100%);
            color: white;
            padding: 90px 20px 35px;
            text-align: center;
            border-bottom: 3px solid #00f5ff;
            position: relative;
            overflow: hidden;
        }}
        .header::before {{
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0; bottom: 0;
            background: radial-gradient(ellipse at center, rgba(0, 245, 255, 0.1) 0%, transparent 70%);
        }}
        .header h1 {{
            font-family: 'Orbitron', sans-serif;
            font-size: 3rem;
            font-weight: 900;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 5px;
            text-shadow: 0 0 30px rgba(0, 245, 255, 0.5);
            position: relative;
        }}
        .header h1 span {{ color: #ff6b35; text-shadow: 0 0 30px rgba(255, 107, 53, 0.5); }}
        .header .subtitle {{
            opacity: 0.9;
            font-size: 1.2rem;
            color: #00f5ff;
            font-weight: 600;
            letter-spacing: 2px;
            position: relative;
        }}

        /* Calendar Sidebar */
        .calendar-sidebar {{
            position: fixed;
            left: 20px;
            top: 160px;
            width: 260px;
            z-index: 100;
        }}
        .calendar-box {{
            background: linear-gradient(135deg, rgba(20, 20, 50, 0.95) 0%, rgba(30, 30, 70, 0.95) 100%);
            border: 1px solid rgba(0, 245, 255, 0.3);
            border-radius: 16px;
            padding: 20px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
        }}
        .calendar-title {{
            font-size: 14px;
            color: #ff6b35;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            margin-bottom: 16px;
            text-align: center;
            font-weight: 700;
        }}
        .calendar-weekdays {{
            display: grid;
            grid-template-columns: repeat(7, 1fr);
            gap: 2px;
            margin-bottom: 8px;
        }}
        .calendar-weekdays span {{
            text-align: center;
            font-size: 11px;
            color: #00f5ff;
            font-weight: 600;
        }}
        .calendar-days {{
            display: grid;
            grid-template-columns: repeat(7, 1fr);
            gap: 2px;
        }}
        .calendar-day {{
            aspect-ratio: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            color: #666;
            border-radius: 6px;
        }}
        .calendar-day.has-content {{
            background: rgba(0, 245, 255, 0.1);
            color: #00f5ff;
            cursor: pointer;
            transition: all 0.2s;
        }}
        .calendar-day.has-content:hover {{
            background: rgba(0, 245, 255, 0.3);
            transform: scale(1.1);
        }}
        .calendar-day.today {{
            background: rgba(255, 107, 53, 0.3);
            color: #ff6b35;
            font-weight: bold;
        }}
        .month-nav {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        }}
        .month-nav button {{
            background: rgba(0, 245, 255, 0.1);
            border: 1px solid rgba(0, 245, 255, 0.3);
            color: #00f5ff;
            padding: 4px 10px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
        }}
        .month-nav button:hover {{ background: rgba(0, 245, 255, 0.2); }}
        .month-name {{
            color: #fff;
            font-weight: 600;
            font-size: 14px;
        }}
        @media (max-width: 1400px) {{ .calendar-sidebar {{ display: none; }} }}

        .container {{ max-width: 1300px; margin: 0 auto; padding: 30px; margin-left: 300px; }}
        @media (max-width: 1400px) {{ .container {{ margin-left: auto; }} }}

        .tabs {{
            display: flex;
            gap: 12px;
            margin-bottom: 30px;
            background: linear-gradient(135deg, rgba(20, 20, 50, 0.9) 0%, rgba(30, 30, 70, 0.9) 100%);
            padding: 18px;
            border-radius: 15px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255,255,255,0.1);
            flex-wrap: wrap;
            border: 1px solid rgba(0, 245, 255, 0.2);
        }}
        .tab-btn {{
            padding: 14px 28px;
            background: rgba(255,255,255,0.05);
            border: 2px solid rgba(0, 245, 255, 0.3);
            border-radius: 10px;
            font-family: 'Orbitron', sans-serif;
            font-weight: 700;
            font-size: 1rem;
            cursor: pointer;
            color: #a0a0a0;
            transition: all 0.3s ease;
            text-transform: uppercase;
            letter-spacing: 2px;
        }}
        .tab-btn:hover {{
            background: rgba(0, 245, 255, 0.1);
            border-color: #00f5ff;
            color: #00f5ff;
            box-shadow: 0 0 20px rgba(0, 245, 255, 0.3);
        }}
        .tab-btn.active {{
            background: linear-gradient(135deg, #00f5ff 0%, #00c4cc 100%);
            color: #0a0a1a;
            border-color: #00f5ff;
            box-shadow: 0 0 30px rgba(0, 245, 255, 0.5);
        }}

        .sport-section {{ display: none; }}
        .sport-section.active {{ display: block; }}
        .no-games {{
            background: rgba(30, 30, 60, 0.8);
            padding: 60px;
            text-align: center;
            border-radius: 15px;
            color: #888;
            font-size: 1.2rem;
            border: 1px solid rgba(0, 245, 255, 0.2);
        }}

        /* === GAME CARDS === */
        .game-card {{
            background: linear-gradient(135deg, rgba(20, 20, 50, 0.95) 0%, rgba(30, 30, 70, 0.95) 100%);
            border-radius: 20px;
            margin-bottom: 30px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(0, 245, 255, 0.1);
            overflow: hidden;
            border: 1px solid rgba(0, 245, 255, 0.2);
            transition: all 0.3s ease;
        }}
        .game-card:hover {{
            box-shadow: 0 15px 50px rgba(0, 0, 0, 0.6), 0 0 30px rgba(0, 245, 255, 0.2);
            transform: translateY(-3px);
        }}

        .game-header {{
            background: linear-gradient(135deg, #0d0d2b 0%, #1a1a4a 100%);
            color: white;
            padding: 18px 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 1rem;
            font-weight: 700;
            border-bottom: 2px solid #00f5ff;
        }}
        .game-time {{
            color: #00f5ff;
            font-family: 'Orbitron', sans-serif;
            font-size: 1.1rem;
            text-shadow: 0 0 10px rgba(0, 245, 255, 0.5);
        }}
        .game-venue {{ color: #a0a0a0; font-size: 0.95rem; }}
        .game-network {{
            background: linear-gradient(135deg, #ff6b35 0%, #ff8c42 100%);
            padding: 6px 14px;
            border-radius: 6px;
            font-size: 0.85rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        .section {{ padding: 18px 24px; border-bottom: 1px solid rgba(0, 245, 255, 0.1); }}
        .section-title {{
            font-family: 'Orbitron', sans-serif;
            font-size: 0.9rem;
            font-weight: 700;
            color: #00f5ff;
            text-transform: uppercase;
            letter-spacing: 3px;
            margin-bottom: 14px;
            padding-bottom: 10px;
            border-bottom: 2px solid #ff6b35;
            display: inline-block;
            text-shadow: 0 0 10px rgba(0, 245, 255, 0.3);
        }}

        .stats-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 0; border-bottom: 1px solid rgba(0, 245, 255, 0.1); }}
        .stats-grid .section {{ border-bottom: none; }}
        .stats-grid .section:first-child {{ border-right: 1px solid rgba(0, 245, 255, 0.1); }}

        .lines-table, .stats-table {{ width: 100%; border-collapse: collapse; font-size: 1rem; }}
        .lines-table th, .stats-table th {{
            text-align: center;
            padding: 12px 8px;
            font-family: 'Orbitron', sans-serif;
            font-size: 0.75rem;
            font-weight: 700;
            color: #00f5ff;
            text-transform: uppercase;
            letter-spacing: 1px;
            background: rgba(0, 245, 255, 0.1);
            border-bottom: 1px solid rgba(0, 245, 255, 0.2);
        }}
        .lines-table td, .stats-table td {{
            text-align: center;
            padding: 14px 8px;
            font-weight: 700;
            font-size: 1.05rem;
            color: #e0e0e0;
        }}

        .team-col {{ text-align: left !important; min-width: 160px; display: flex; align-items: center; gap: 12px; }}
        .team-logo {{ width: 40px; height: 40px; object-fit: contain; filter: drop-shadow(0 0 8px rgba(255,255,255,0.3)); }}
        .team-name {{ font-weight: 800; font-size: 1.1rem; color: #fff; }}
        .team-record {{ font-size: 0.9rem; color: #888; font-weight: 600; }}
        .team-abbr {{
            font-weight: 800;
            color: #00f5ff;
            text-align: left !important;
            padding-left: 12px !important;
            font-size: 1.1rem;
            text-shadow: 0 0 10px rgba(0, 245, 255, 0.3);
        }}

        .spread {{ color: #ffd700; font-weight: 800; font-size: 1.15rem; text-shadow: 0 0 10px rgba(255, 215, 0, 0.3); }}
        .ml {{ color: #00ff88; font-weight: 800; font-size: 1.15rem; }}
        .total {{ color: #ff6b35; font-weight: 700; }}
        .away-row {{ background: rgba(0, 0, 0, 0.2); }}
        .home-row {{ background: rgba(0, 245, 255, 0.05); }}

        /* ScoresAndOdds-style full width table */
        .betting-lines-full {{ margin-bottom: 20px; }}
        .lines-table-full {{ width: 100%; border-collapse: collapse; font-size: 0.95rem; }}
        .lines-table-full th {{
            text-align: center;
            padding: 10px 6px;
            font-family: 'Orbitron', sans-serif;
            font-size: 0.7rem;
            font-weight: 700;
            color: #ffd700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            background: linear-gradient(135deg, rgba(255, 215, 0, 0.2) 0%, rgba(255, 107, 53, 0.1) 100%);
            border-bottom: 2px solid #ffd700;
        }}
        .lines-table-full td {{
            text-align: center;
            padding: 12px 6px;
            font-weight: 700;
            font-size: 1rem;
            color: #e0e0e0;
            border-bottom: 1px solid rgba(255, 215, 0, 0.1);
        }}
        .lines-table-full .team-col {{ text-align: left !important; min-width: 100px; }}
        .su-record {{ color: #fff; }}
        .ats-record {{ color: #00ff88; font-weight: 800; }}
        .ou-record {{ color: #00c4ff; font-weight: 800; }}
        .ppg {{ color: #ff6b35; font-weight: 800; }}
        .opp-ppg {{ color: #ff4757; }}
        .pwr {{ color: #ffd700; font-weight: 800; }}

        .ats-record {{
            color: #00ff88;
            font-weight: 800;
            font-size: 1.1rem;
            background: rgba(0, 255, 136, 0.15);
            padding: 8px 12px !important;
            border-radius: 8px;
            border: 1px solid rgba(0, 255, 136, 0.3);
            text-shadow: 0 0 10px rgba(0, 255, 136, 0.3);
        }}
        .ou-record {{
            color: #00c4ff;
            font-weight: 800;
            font-size: 1.1rem;
            background: rgba(0, 196, 255, 0.15);
            padding: 8px 12px !important;
            border-radius: 8px;
            border: 1px solid rgba(0, 196, 255, 0.3);
            text-shadow: 0 0 10px rgba(0, 196, 255, 0.3);
        }}

        /* === INJURIES SECTION === */
        .injuries-section {{
            padding: 16px 24px;
            border-top: 1px solid rgba(255, 107, 53, 0.3);
        }}
        .injuries-section .section-title {{
            color: #ff6b35;
            font-size: 0.85rem;
            margin-bottom: 12px;
        }}
        .injuries-content {{
            display: flex;
            flex-direction: column;
            gap: 8px;
        }}
        .team-injuries {{
            font-size: 0.9rem;
            color: #ccc;
            line-height: 1.5;
        }}
        .team-injuries strong {{
            color: #00f5ff;
        }}

        /* === H2H SECTION - PROFESSIONAL ESPN-STYLE === */
        .h2h-section {{
            background: #f8f9fa;
            padding: 20px 24px;
            border-radius: 0 0 16px 16px;
            border-top: 4px solid #1a365d;
        }}
        .h2h-section .section-title {{
            font-family: 'Inter', sans-serif;
            color: #1a365d;
            font-size: 0.85rem;
            font-weight: 700;
            margin-bottom: 16px;
            padding-bottom: 8px;
            border-bottom: 2px solid #e2e8f0;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .h2h-summary {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
            margin-bottom: 16px;
        }}
        .h2h-stat {{
            background: #fff;
            padding: 16px 12px;
            border-radius: 8px;
            text-align: center;
            border: 1px solid #e2e8f0;
            box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        }}
        .h2h-stat-label {{
            font-size: 0.65rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: #64748b;
            font-weight: 600;
            margin-bottom: 6px;
            display: block;
        }}
        .h2h-stat-value {{
            font-size: 1rem;
            font-weight: 700;
            color: #1e293b;
        }}
        .h2h-su {{ border-left: 3px solid #1a365d; }}
        .h2h-ats-summary {{ border-left: 3px solid #059669; }}
        .h2h-ou-summary {{ border-left: 3px solid #0284c7; }}
        .h2h-su .h2h-stat-value {{ color: #1a365d; }}
        .h2h-ats-summary .h2h-stat-value {{ color: #059669; }}
        .h2h-ou-summary .h2h-stat-value {{ color: #0284c7; }}
        .h2h-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.85rem;
            background: #fff;
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid #e2e8f0;
        }}
        .h2h-table th {{
            background: #1a365d;
            color: #fff;
            padding: 10px 8px;
            text-align: center;
            font-weight: 600;
            font-size: 0.7rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .h2h-table td {{
            padding: 10px 8px;
            text-align: center;
            border-bottom: 1px solid #f1f5f9;
            font-weight: 500;
            font-size: 0.85rem;
            color: #334155;
        }}
        .h2h-table tr:nth-child(even) {{ background: #f8fafc; }}
        .h2h-table tr:hover {{ background: #f1f5f9; }}
        .h2h-ats {{ color: #059669; font-weight: 600; }}
        .h2h-ou {{ color: #0284c7; font-weight: 600; }}
        .winner-home {{ color: #059669; font-weight: 600; }}
        .winner-away {{ color: #1a365d; font-weight: 600; }}
        .score {{ color: #1e293b; font-weight: 600; }}
        .over {{ color: #ff6b35; font-weight: 700; }}
        .under {{ color: #00c4ff; font-weight: 700; }}

        /* PERMANENT STYLING: Missing/unavailable data - Added Jan 24, 2026 */
        .stat-na {{
            color: #94a3b8;
            font-style: normal;
            font-weight: 400;
        }}
        .stat-zero {{
            color: #94a3b8;
            font-style: normal;
        }}

        footer {{
            text-align: center;
            padding: 40px;
            color: #666;
            font-size: 1rem;
            background: rgba(0,0,0,0.3);
            margin-top: 40px;
            border-top: 1px solid rgba(0, 245, 255, 0.1);
        }}
        footer strong {{ color: #00f5ff; }}

        @media (max-width: 768px) {{
            .stats-grid {{ grid-template-columns: 1fr; }}
            .stats-grid .section:first-child {{ border-right: none; border-bottom: 1px solid rgba(0, 245, 255, 0.1); }}
            .header h1 {{ font-size: 2rem; }}
            .h2h-summary {{ flex-direction: column; align-items: center; }}
        }}
    </style>
</head>
<body>
    <nav class="nav">
        <div class="nav-inner">
            <a href="index.html" class="logo">BET<span>LEGEND</span></a>
        </div>
    </nav>
    <header class="header">
        <h1>Handicapping <span>Hub</span></h1>
        <p class="subtitle">{date_str} | Real-Time Odds, Stats & Betting Trends</p>
    </header>
    <aside class="calendar-sidebar">
        <div class="calendar-box">
            <div class="calendar-title">Hub Archive</div>
            <div class="month-nav">
                <button id="prev-month">&lt;</button>
                <span class="month-name" id="month-name"></span>
                <button id="next-month">&gt;</button>
            </div>
            <div class="calendar-weekdays"><span>Su</span><span>Mo</span><span>Tu</span><span>We</span><span>Th</span><span>Fr</span><span>Sa</span></div>
            <div class="calendar-days" id="calendar-days"></div>
        </div>
    </aside>
    <div class="container">
        <div class="tabs">
            {tab_buttons}
        </div>
        {sport_sections}
    </div>
    <footer>
        <p>Data from ESPN & The Odds API | Updated Daily</p>
    </footer>
    <script>
        document.querySelectorAll('.tab-btn').forEach(btn => {{
            btn.addEventListener('click', () => {{
                document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
                document.querySelectorAll('.sport-section').forEach(s => s.classList.remove('active'));
                btn.classList.add('active');
                document.getElementById(btn.dataset.sport + '-section').classList.add('active');
            }});
        }});
        // Calendar
        const archiveDates = {archive_dates_json};
        let currentMonth = new Date().getMonth();
        let currentYear = new Date().getFullYear();
        function renderCalendar() {{
            const monthNames = ['January','February','March','April','May','June','July','August','September','October','November','December'];
            document.getElementById('month-name').textContent = monthNames[currentMonth] + ' ' + currentYear;
            const firstDay = new Date(currentYear, currentMonth, 1).getDay();
            const daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate();
            const today = new Date();
            let html = '';
            for (let i = 0; i < firstDay; i++) html += '<div class="calendar-day"></div>';
            for (let d = 1; d <= daysInMonth; d++) {{
                const dateStr = currentYear + '-' + String(currentMonth + 1).padStart(2, '0') + '-' + String(d).padStart(2, '0');
                const hasContent = archiveDates.includes(dateStr);
                const isToday = today.getFullYear() === currentYear && today.getMonth() === currentMonth && today.getDate() === d;
                let cls = 'calendar-day';
                if (hasContent) cls += ' has-content';
                if (isToday) cls += ' today';
                if (hasContent) {{
                    html += '<a href="handicapping-hub-archive/hub-' + dateStr + '.html" class="' + cls + '">' + d + '</a>';
                }} else {{
                    html += '<div class="' + cls + '">' + d + '</div>';
                }}
            }}
            document.getElementById('calendar-days').innerHTML = html;
        }}
        document.getElementById('prev-month').onclick = () => {{ currentMonth--; if (currentMonth < 0) {{ currentMonth = 11; currentYear--; }} renderCalendar(); }};
        document.getElementById('next-month').onclick = () => {{ currentMonth++; if (currentMonth > 11) {{ currentMonth = 0; currentYear++; }} renderCalendar(); }};
        renderCalendar();
    </script>
</body>
</html>'''

# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    print("=" * 60)
    print("HANDICAPPING HUB - PREVIEW WITH ADVANCED STATS")
    print("=" * 60)

    # Get today's date
    if EASTERN:
        now = datetime.now(EASTERN)
    else:
        now = datetime.now() - timedelta(hours=5)
    date_str = now.strftime('%B %d, %Y')

    print(f"\nGenerating PREVIEW for: {date_str}")
    print("NEW FEATURES: ATS Records, O/U Trends, L5 Record, Home/Away, Streak, Net Rating")

    all_games = {}

    for sport, config in SPORTS.items():
        print(f"\n[{sport}] Processing...")

        # Fetch scoreboard
        games = fetch_espn_scoreboard(config['espn_path'])
        print(f"  Found {len(games)} games on ESPN")

        if not games:
            all_games[sport] = []
            continue

        # Fetch odds
        odds_data = fetch_odds(config['odds_key'])
        print(f"  Found {len(odds_data)} games with odds")

        # NEW: Fetch ATS/O/U betting records from Covers.com
        betting_records = fetch_covers_betting_records(sport)

        # Process games
        processed = []
        for game in games:
            # NCAAB/NCAAF filtering
            if sport == 'NCAAB':
                odds_match = match_game_odds(game, odds_data)
                if not is_important_ncaab_game(game, has_valid_odds(odds_match)):
                    continue
            elif sport == 'NCAAF':
                if not is_bowl_game(game):
                    continue

            result = process_game(game, sport, config['espn_path'], odds_data, betting_records)
            if result:
                processed.append(result)

        all_games[sport] = processed
        print(f"  Processed {len(processed)} games")

    # Generate HTML
    print("\n[HTML] Generating preview page...")
    html = generate_page(all_games, date_str)

    # PERMANENT SAFEGUARD: Remove any line movement content that might slip through
    html = block_line_movements(html)

    # PERMANENT SAFEGUARD: Replace ugly dashes with styled em-dashes for missing data
    # This catches any "-" that wasn't handled elsewhere
    html = html.replace('<td>-</td>', '<td class="stat-na">—</td>')
    html = html.replace('<td class="ats-record">-</td>', '<td class="ats-record stat-na">—</td>')
    html = html.replace('<td class="ou-record">-</td>', '<td class="ou-record stat-na">—</td>')
    html = html.replace('>0.0<', ' class="stat-zero">0.0<')

    # Write to preview file
    output_path = os.path.join(REPO_PATH, OUTPUT_FILE)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"\n[SUCCESS] PREVIEW saved to: {output_path}")
    print("\n" + "=" * 60)
    print("NEXT STEPS:")
    print("1. Open handicapping-hub-preview.html in browser")
    print("2. Review the new SITUATIONAL section in each game card")
    print("3. Check L5, Home/Away, Streak data")
    print("4. If approved, update production script")
    print("=" * 60)

if __name__ == '__main__':
    main()
