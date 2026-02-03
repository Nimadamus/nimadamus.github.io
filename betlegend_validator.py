#!/usr/bin/env python3
"""
BetLegend Content Validator & Pre-Publish Filter
=================================================
Scans HTML files for roster errors, statistical errors, structural issues,
and content problems BEFORE they go live on betlegendpicks.com.

Usage:
    python betlegend_validator.py [path_to_html_files_or_single_file]
    python betlegend_validator.py C:/Users/Nima/nimadamus.github.io
    python betlegend_validator.py C:/Users/Nima/nimadamus.github.io/blog-page12.html

Run this AFTER Claude Code makes changes and BEFORE committing/pushing.
"""

import os
import sys
import re
import json
import time
import codecs
import fnmatch
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

# Force UTF-8 output on Windows
if sys.platform == 'win32':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, errors='replace')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, errors='replace')

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    print("[WARNING] 'requests' not installed. Roster validation disabled.")
    print("  Install with: pip install requests")

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False
    print("[WARNING] 'beautifulsoup4' not installed. HTML parsing limited.")
    print("  Install with: pip install beautifulsoup4")


# =============================================================================
# CONFIGURATION
# =============================================================================

class Config:
    """All configurable thresholds and settings."""
    
    # MLB Stats API (free, no key needed)
    MLB_API_BASE = "https://statsapi.mlb.com/api/v1"
    
    # Cache roster data for this many hours to avoid hammering the API
    ROSTER_CACHE_HOURS = 6
    ROSTER_CACHE_FILE = os.path.join(os.path.expanduser("~"), ".betlegend_roster_cache.json")
    
    # File patterns to scan
    HTML_EXTENSIONS = {'.html', '.htm'}
    
    # Files/dirs to skip
    SKIP_DIRS = {'.git', 'node_modules', '.claude', '__pycache__', 'assets', 'images', 'css', 'js'}
    SKIP_FILES = {'404.html', 'template.html', 'test_article.html', 'input.html'}
    # Glob patterns for files to skip (e.g., google verification files)
    SKIP_FILE_PATTERNS = ['google*.html']
    
    # Stat range validation (min, max, typical_min, typical_max)
    # Values outside min/max = ERROR, outside typical = WARNING
    MLB_STAT_RANGES = {
        'batting_average': {
            'pattern': r'(?:batting\s*average|AVG|BA)[:\s]*(?:of\s*)?\.(\d{3})',
            'min': 0, 'max': 500, 'typical_min': 150, 'typical_max': 400,
            'display': 'Batting Average', 'format': '.{}'
        },
        'era': {
            'pattern': r'(?:ERA)[:\s]*(?:of\s*)?(\d{1,2}\.\d{2})',
            'min': 0.00, 'max': 20.00, 'typical_min': 1.50, 'typical_max': 7.00,
            'display': 'ERA', 'format': '{}'
        },
        'whip': {
            'pattern': r'(?:WHIP)[:\s]*(?:of\s*)?(\d\.\d{2,3})',
            'min': 0.00, 'max': 3.50, 'typical_min': 0.70, 'typical_max': 2.00,
            'display': 'WHIP', 'format': '{}'
        },
        'ops': {
            'pattern': r'(?:OPS)[:\s]*(?:of\s*)?\.?(\d{3,4})',
            'min': 0, 'max': 2000, 'typical_min': 400, 'typical_max': 1200,
            'display': 'OPS', 'format': '{}'
        },
        'home_runs_season': {
            'pattern': r'(\d{1,3})\s*(?:home\s*runs|HRs?|homers?)(?:\s*(?:this|on the)\s*(?:season|year))?',
            'min': 0, 'max': 80, 'typical_min': 0, 'typical_max': 62,
            'display': 'Home Runs', 'format': '{}'
        },
        'rbi_season': {
            'pattern': r'(\d{1,3})\s*(?:RBIs?|runs?\s*batted\s*in)',
            'min': 0, 'max': 200, 'typical_min': 0, 'typical_max': 165,
            'display': 'RBI', 'format': '{}'
        },
        'wins_pitcher': {
            # Only match explicit W-L or win-loss notation (not generic "record" which catches team records)
            'pattern': r'(\d{1,2})-\d{1,2}\s*(?:W-L|win-loss|wins?\s*and\s*\d+\s*loss)',
            'min': 0, 'max': 30, 'typical_min': 0, 'typical_max': 25,
            'display': 'Pitcher Wins', 'format': '{}'
        },
        'strikeouts_pitcher': {
            'pattern': r'(\d{1,3})\s*(?:strikeouts|Ks|punch\s*outs)',
            'min': 0, 'max': 400, 'typical_min': 0, 'typical_max': 350,
            'display': 'Strikeouts', 'format': '{}'
        },
    }
    
    # Betting line validation
    MONEYLINE_RANGE = (-1000, 1000)  # Reasonable ML range
    OVER_UNDER_RANGE = {
        'MLB': (5.0, 15.0),
        'NFL': (30.0, 65.0),
        'NBA': (190.0, 260.0),
        'NHL': (4.0, 8.5),
        'NCAAB': (110.0, 180.0),
        'Soccer': (1.0, 5.5),
    }
    SPREAD_RANGE = {
        'MLB': (-3.5, 3.5),
        'NFL': (-20.5, 20.5),
        'NBA': (-20.5, 20.5),
        'NHL': (-3.5, 3.5),
    }


# =============================================================================
# MLB TEAM DATA
# =============================================================================

# Complete MLB teams with all common name variations
MLB_TEAMS = {
    108: {'name': 'Los Angeles Angels', 'abbr': 'LAA', 'aliases': ['Angels', 'LA Angels', 'Anaheim Angels', 'Halos']},
    109: {'name': 'Arizona Diamondbacks', 'abbr': 'ARI', 'aliases': ['Diamondbacks', 'D-backs', 'D-Backs', 'DBacks', 'Arizona']},
    110: {'name': 'Baltimore Orioles', 'abbr': 'BAL', 'aliases': ['Orioles', 'O\'s', 'Baltimore']},
    111: {'name': 'Boston Red Sox', 'abbr': 'BOS', 'aliases': ['Red Sox', 'BoSox', 'Boston']},
    112: {'name': 'Chicago Cubs', 'abbr': 'CHC', 'aliases': ['Cubs', 'Chicago Cubs', 'Cubbies']},
    113: {'name': 'Cincinnati Reds', 'abbr': 'CIN', 'aliases': ['Reds', 'Cincinnati', 'Cincy']},
    114: {'name': 'Cleveland Guardians', 'abbr': 'CLE', 'aliases': ['Guardians', 'Cleveland', 'Guards']},
    115: {'name': 'Colorado Rockies', 'abbr': 'COL', 'aliases': ['Rockies', 'Colorado', 'Rox']},
    116: {'name': 'Detroit Tigers', 'abbr': 'DET', 'aliases': ['Tigers', 'Detroit']},
    117: {'name': 'Houston Astros', 'abbr': 'HOU', 'aliases': ['Astros', 'Houston', 'Stros']},
    118: {'name': 'Kansas City Royals', 'abbr': 'KC', 'aliases': ['Royals', 'Kansas City', 'KC']},
    119: {'name': 'Los Angeles Dodgers', 'abbr': 'LAD', 'aliases': ['Dodgers', 'LA Dodgers', 'Los Angeles']},
    120: {'name': 'Washington Nationals', 'abbr': 'WSH', 'aliases': ['Nationals', 'Nats', 'Washington']},
    121: {'name': 'New York Mets', 'abbr': 'NYM', 'aliases': ['Mets', 'NY Mets']},
    133: {'name': 'Oakland Athletics', 'abbr': 'OAK', 'aliases': ['Athletics', 'A\'s', 'Oakland', 'As']},
    134: {'name': 'Pittsburgh Pirates', 'abbr': 'PIT', 'aliases': ['Pirates', 'Pittsburgh', 'Bucs', 'Buccos']},
    135: {'name': 'San Diego Padres', 'abbr': 'SD', 'aliases': ['Padres', 'San Diego', 'Friars']},
    136: {'name': 'Seattle Mariners', 'abbr': 'SEA', 'aliases': ['Mariners', 'Seattle', 'M\'s']},
    137: {'name': 'San Francisco Giants', 'abbr': 'SF', 'aliases': ['Giants', 'San Francisco', 'SF Giants']},
    138: {'name': 'St. Louis Cardinals', 'abbr': 'STL', 'aliases': ['Cardinals', 'Cards', 'St. Louis', 'St Louis']},
    139: {'name': 'Tampa Bay Rays', 'abbr': 'TB', 'aliases': ['Rays', 'Tampa Bay', 'Tampa']},
    140: {'name': 'Texas Rangers', 'abbr': 'TEX', 'aliases': ['Rangers', 'Texas']},
    141: {'name': 'Toronto Blue Jays', 'abbr': 'TOR', 'aliases': ['Blue Jays', 'Toronto', 'Jays']},
    142: {'name': 'Minnesota Twins', 'abbr': 'MIN', 'aliases': ['Twins', 'Minnesota']},
    143: {'name': 'Philadelphia Phillies', 'abbr': 'PHI', 'aliases': ['Phillies', 'Philadelphia', 'Phils']},
    144: {'name': 'Atlanta Braves', 'abbr': 'ATL', 'aliases': ['Braves', 'Atlanta']},
    145: {'name': 'Chicago White Sox', 'abbr': 'CWS', 'aliases': ['White Sox', 'ChiSox', 'Sox']},
    146: {'name': 'Miami Marlins', 'abbr': 'MIA', 'aliases': ['Marlins', 'Miami', 'Fish']},
    147: {'name': 'New York Yankees', 'abbr': 'NYY', 'aliases': ['Yankees', 'NY Yankees', 'Yanks', 'Bombers']},
    158: {'name': 'Milwaukee Brewers', 'abbr': 'MIL', 'aliases': ['Brewers', 'Milwaukee', 'Brew Crew']},
}

# Build reverse lookup: name/alias -> team_id
TEAM_LOOKUP = {}
for team_id, info in MLB_TEAMS.items():
    TEAM_LOOKUP[info['name'].lower()] = team_id
    TEAM_LOOKUP[info['abbr'].lower()] = team_id
    for alias in info['aliases']:
        TEAM_LOOKUP[alias.lower()] = team_id


# =============================================================================
# KNOWN FACTS DATABASE - MANDATORY CHECKS
# =============================================================================
# These are VERIFIED facts that override any claims in content.
# Last updated: February 2026

# Players on WRONG teams - these associations trigger ERRORS
WRONG_PLAYER_TEAM_ASSOCIATIONS = [
    # NBA 2025 Trades
    ("luka doncic", "mavericks", "Luka Doncic was traded to the LAKERS in February 2025"),
    ("luka doncic", "dallas", "Luka Doncic was traded to the LAKERS in February 2025"),
    ("luka", "mavericks", "Luka Doncic was traded to the LAKERS in February 2025"),
    ("luka", "dallas", "Luka Doncic was traded to the LAKERS in February 2025"),
    ("doncic", "mavericks", "Luka Doncic was traded to the LAKERS in February 2025"),
    ("doncic", "dallas", "Luka Doncic was traded to the LAKERS in February 2025"),
    ("de'aaron fox", "kings", "De'Aaron Fox was traded to the SPURS in February 2025"),
    ("deaaron fox", "kings", "De'Aaron Fox was traded to the SPURS in February 2025"),
    ("fox", "kings", "De'Aaron Fox was traded to the SPURS in February 2025"),
    ("fox", "sacramento", "De'Aaron Fox was traded to the SPURS in February 2025"),
    ("de'aaron fox", "heat", "De'Aaron Fox is on the SPURS - he was NEVER on the Heat (fabricated)"),
    ("fox", "heat", "De'Aaron Fox is on the SPURS - he was NEVER on the Heat (fabricated)"),
    ("fox", "miami heat", "De'Aaron Fox is on the SPURS - he was NEVER on Miami Heat (fabricated)"),
    ("kevin durant", "suns", "Kevin Durant was traded to the ROCKETS in July 2025"),
    ("kevin durant", "phoenix", "Kevin Durant was traded to the ROCKETS in July 2025"),
    ("durant", "suns", "Kevin Durant was traded to the ROCKETS in July 2025"),
    ("durant", "phoenix", "Kevin Durant was traded to the ROCKETS in July 2025"),
    ("jimmy butler", "heat", "Jimmy Butler was traded to the WARRIORS in February 2025"),
    ("butler", "heat", "Jimmy Butler was traded to the WARRIORS in February 2025"),
    ("butler", "miami", "Jimmy Butler was traded to the WARRIORS in February 2025"),
    ("brandon ingram", "pelicans", "Brandon Ingram was traded to the RAPTORS in February 2025"),
    ("ingram", "pelicans", "Brandon Ingram was traded to the RAPTORS in February 2025"),
    ("ingram", "new orleans", "Brandon Ingram was traded to the RAPTORS in February 2025"),
    ("zach lavine", "bulls", "Zach LaVine was traded to the KINGS in February 2025"),
    ("lavine", "bulls", "Zach LaVine was traded to the KINGS in February 2025"),
    ("lavine", "chicago", "Zach LaVine was traded to the KINGS in February 2025"),

    # NHL 2025 Trades
    ("mitch marner", "maple leafs", "Mitch Marner was traded to the GOLDEN KNIGHTS in July 2025"),
    ("mitch marner", "leafs", "Mitch Marner was traded to the GOLDEN KNIGHTS in July 2025"),
    ("mitch marner", "toronto", "Mitch Marner was traded to the GOLDEN KNIGHTS in July 2025"),
    ("marner", "maple leafs", "Mitch Marner was traded to the GOLDEN KNIGHTS in July 2025"),
    ("marner", "leafs", "Mitch Marner was traded to the GOLDEN KNIGHTS in July 2025"),
    ("marner", "toronto", "Mitch Marner was traded to the GOLDEN KNIGHTS in July 2025"),

    # MLB 2025-26 Signings
    ("alex bregman", "astros", "Alex Bregman signed with the CUBS in January 2026"),
    ("alex bregman", "houston", "Alex Bregman signed with the CUBS in January 2026"),
    ("bregman", "astros", "Alex Bregman signed with the CUBS in January 2026"),
    ("bregman", "houston", "Alex Bregman signed with the CUBS in January 2026"),
    ("kyle tucker", "astros", "Kyle Tucker was traded to the DODGERS in January 2026"),
    ("kyle tucker", "houston", "Kyle Tucker was traded to the DODGERS in January 2026"),
    ("tucker", "astros", "Kyle Tucker was traded to the DODGERS in January 2026"),
    ("pete alonso", "mets", "Pete Alonso signed with the ORIOLES in December 2025"),
    ("pete alonso", "new york mets", "Pete Alonso signed with the ORIOLES in December 2025"),
    ("alonso", "mets", "Pete Alonso signed with the ORIOLES in December 2025"),
    ("dylan cease", "padres", "Dylan Cease signed with the BLUE JAYS in December 2025"),
    ("dylan cease", "san diego", "Dylan Cease signed with the BLUE JAYS in December 2025"),
    ("cease", "padres", "Dylan Cease signed with the BLUE JAYS in December 2025"),
]

# Wrong injury types - trigger ERRORS
WRONG_INJURY_CLAIMS = [
    ("tatum", "acl", "achilles", "Jayson Tatum has an ACHILLES injury, NOT ACL"),
    ("jayson tatum", "acl", "achilles", "Jayson Tatum has an ACHILLES injury, NOT ACL"),
]

# Placeholder patterns - trigger ERRORS
PLACEHOLDER_PATTERNS = [
    (r'\bcoming soon\b', "Placeholder 'coming soon' found - incomplete content"),
    (r'\banalysis coming\b', "Placeholder 'analysis coming' found - incomplete content"),
    (r'\bpreview coming\b', "Placeholder 'preview coming' found - incomplete content"),
    (r'\bmatchup analysis coming\b', "Placeholder text found - incomplete content"),
    (r'\bTBD\b', "Placeholder 'TBD' found - incomplete content"),
    (r'\bTBA\b', "Placeholder 'TBA' found - incomplete content"),
    (r'\bN/A\b', "Placeholder 'N/A' found - incomplete content"),
    (r'\{[a-zA-Z_]+\}', "Template variable found - incomplete content"),
]

# Banned content patterns - trigger ERRORS
# Note: Line movement ban applies only to picks/analysis, NOT educational content
BANNED_CONTENT_PATTERNS = [
    (r'Sources?:\s*(?:ESPN|Yahoo|NFL\.com|NBA\.com|NHL\.com)', "Source citations are BANNED in articles - write as the authority"),
]

# Line movement patterns - checked separately to exclude educational files
LINE_MOVEMENT_PATTERNS = [
    r'line (?:opened|moved|has moved)',
    r'sharp money (?:is |has )(?:coming|moved)',
    r'the line has (?:ticked|shifted)',
]

# Files where line movement discussion is allowed (educational content)
LINE_MOVEMENT_ALLOWED_FILES = [
    'betting-101', 'how-to', 'calculator', 'explained', 'guide', 'glossary', 'tutorial'
]

# Unsigned claims that are now wrong - trigger ERRORS
WRONG_UNSIGNED_CLAIMS = [
    (r'bregman\s+(?:is\s+)?(?:still\s+)?unsigned', "Alex Bregman signed with Cubs on January 14, 2026"),
    (r'alonso\s+(?:is\s+)?(?:still\s+)?unsigned', "Pete Alonso signed with Orioles in December 2025"),
    (r'tucker\s+(?:is\s+)?(?:still\s+)?unsigned', "Kyle Tucker was traded to Dodgers in January 2026"),
]

# Impossible statistics - trigger ERRORS
IMPOSSIBLE_STATS = [
    (r'(\d{3,})\s*%', 100, "Percentage over 100% is impossible"),
    (r'(\d+\.?\d*)\s*PPG', 55, "PPG over 55 is virtually impossible in NBA"),
    (r'batting\s+(?:average|avg)[:\s]+\.?([4-9]\d{2})', 400, "Batting average over .400 is extremely rare"),
    (r'ERA[:\s]+(\d+\.\d+)', 0, "Negative ERA is impossible"),  # Will check for negative
]

# Suspicious round betting lines - trigger WARNINGS
SUSPICIOUS_ROUND_LINES = [
    (r'spread[:\s]+([+-]?\d+)(?:\.0)?(?!\.\d)', "Round spread without .5 is suspicious - verify this is accurate"),
    (r'moneyline[:\s]+([+-]\d{2}0)(?!\d)', "Round moneyline ending in 0 is suspicious - verify this is accurate"),
]

# =============================================================================
# NFL / NBA / NHL TEAM DATA (basic validation)
# =============================================================================

NFL_TEAMS = {
    'Arizona Cardinals', 'Atlanta Falcons', 'Baltimore Ravens', 'Buffalo Bills',
    'Carolina Panthers', 'Chicago Bears', 'Cincinnati Bengals', 'Cleveland Browns',
    'Dallas Cowboys', 'Denver Broncos', 'Detroit Lions', 'Green Bay Packers',
    'Houston Texans', 'Indianapolis Colts', 'Jacksonville Jaguars', 'Kansas City Chiefs',
    'Las Vegas Raiders', 'Los Angeles Chargers', 'Los Angeles Rams', 'Miami Dolphins',
    'Minnesota Vikings', 'New England Patriots', 'New Orleans Saints', 'New York Giants',
    'New York Jets', 'Philadelphia Eagles', 'Pittsburgh Steelers', 'San Francisco 49ers',
    'Seattle Seahawks', 'Tampa Bay Buccaneers', 'Tennessee Titans', 'Washington Commanders',
}

NBA_TEAMS = {
    'Atlanta Hawks', 'Boston Celtics', 'Brooklyn Nets', 'Charlotte Hornets',
    'Chicago Bulls', 'Cleveland Cavaliers', 'Dallas Mavericks', 'Denver Nuggets',
    'Detroit Pistons', 'Golden State Warriors', 'Houston Rockets', 'Indiana Pacers',
    'Los Angeles Clippers', 'Los Angeles Lakers', 'Memphis Grizzlies', 'Miami Heat',
    'Milwaukee Bucks', 'Minnesota Timberwolves', 'New Orleans Pelicans', 'New York Knicks',
    'Oklahoma City Thunder', 'Orlando Magic', 'Philadelphia 76ers', 'Phoenix Suns',
    'Portland Trail Blazers', 'Sacramento Kings', 'San Antonio Spurs', 'Toronto Raptors',
    'Utah Jazz', 'Washington Wizards',
}

NHL_TEAMS = {
    'Anaheim Ducks', 'Arizona Coyotes', 'Boston Bruins', 'Buffalo Sabres',
    'Calgary Flames', 'Carolina Hurricanes', 'Chicago Blackhawks', 'Colorado Avalanche',
    'Columbus Blue Jackets', 'Dallas Stars', 'Detroit Red Wings', 'Edmonton Oilers',
    'Florida Panthers', 'Los Angeles Kings', 'Minnesota Wild', 'Montreal Canadiens',
    'Nashville Predators', 'New Jersey Devils', 'New York Islanders', 'New York Rangers',
    'Ottawa Senators', 'Philadelphia Flyers', 'Pittsburgh Penguins', 'San Jose Sharks',
    'Seattle Kraken', 'St. Louis Blues', 'Tampa Bay Lightning', 'Toronto Maple Leafs',
    'Utah Hockey Club', 'Vancouver Canucks', 'Vegas Golden Knights', 'Washington Capitals',
    'Winnipeg Jets',
}


# =============================================================================
# ROSTER CACHE & API
# =============================================================================

class RosterManager:
    """Fetches and caches MLB roster data from the Stats API."""
    
    def __init__(self):
        self.rosters = {}  # team_id -> set of player last names
        self.full_rosters = {}  # team_id -> list of full player dicts
        self.loaded = False
    
    def load_rosters(self):
        """Load rosters from cache or API."""
        if not HAS_REQUESTS:
            print("  [SKIP] Cannot load rosters - 'requests' not installed")
            return False
        
        # Check cache first
        if self._load_cache():
            self.loaded = True
            return True
        
        # Fetch fresh from API
        print("  Fetching current MLB rosters from API...")
        try:
            for team_id, team_info in MLB_TEAMS.items():
                url = f"{Config.MLB_API_BASE}/teams/{team_id}/roster?rosterType=active"
                resp = requests.get(url, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    players = set()
                    full_players = []
                    for entry in data.get('roster', []):
                        person = entry.get('person', {})
                        full_name = person.get('fullName', '')
                        if full_name:
                            # Store last name for fuzzy matching
                            parts = full_name.split()
                            if parts:
                                players.add(parts[-1].lower())
                                players.add(full_name.lower())
                                full_players.append({
                                    'name': full_name,
                                    'position': entry.get('position', {}).get('abbreviation', ''),
                                    'jersey': entry.get('jerseyNumber', ''),
                                })
                    self.rosters[team_id] = players
                    self.full_rosters[team_id] = full_players
                time.sleep(0.1)  # Be nice to the API
            
            self._save_cache()
            self.loaded = True
            total_players = sum(len(p) for p in self.full_rosters.values())
            print(f"  Loaded {total_players} players across {len(self.rosters)} teams")
            return True
            
        except Exception as e:
            print(f"  [WARNING] Could not fetch rosters: {e}")
            return False
    
    def _load_cache(self):
        """Load roster data from local cache if fresh enough."""
        try:
            if not os.path.exists(Config.ROSTER_CACHE_FILE):
                return False
            
            with open(Config.ROSTER_CACHE_FILE, 'r') as f:
                cache = json.load(f)
            
            cached_time = datetime.fromisoformat(cache.get('timestamp', '2000-01-01'))
            if datetime.now() - cached_time > timedelta(hours=Config.ROSTER_CACHE_HOURS):
                print("  Roster cache expired, fetching fresh data...")
                return False
            
            # Restore rosters (convert string keys back to int)
            for team_id_str, players in cache.get('rosters', {}).items():
                self.rosters[int(team_id_str)] = set(players)
            for team_id_str, players in cache.get('full_rosters', {}).items():
                self.full_rosters[int(team_id_str)] = players
            
            total_players = sum(len(p) for p in self.full_rosters.values())
            print(f"  Loaded {total_players} players from cache (expires in {Config.ROSTER_CACHE_HOURS}h)")
            return True
            
        except Exception:
            return False
    
    def _save_cache(self):
        """Save roster data to local cache."""
        try:
            cache = {
                'timestamp': datetime.now().isoformat(),
                'rosters': {str(k): list(v) for k, v in self.rosters.items()},
                'full_rosters': {str(k): v for k, v in self.full_rosters.items()},
            }
            with open(Config.ROSTER_CACHE_FILE, 'w') as f:
                json.dump(cache, f)
        except Exception as e:
            print(f"  [WARNING] Could not save roster cache: {e}")
    
    def find_player_team(self, player_name):
        """Find which team(s) a player is on. Returns list of (team_id, team_name)."""
        if not self.loaded:
            return []
        
        name_lower = player_name.lower().strip()
        last_name = name_lower.split()[-1] if name_lower.split() else name_lower
        
        found = []
        for team_id, players in self.rosters.items():
            if name_lower in players or last_name in players:
                found.append((team_id, MLB_TEAMS[team_id]['name']))
        return found
    
    def verify_player_on_team(self, player_name, team_ref):
        """Check if a player is actually on the referenced team."""
        if not self.loaded:
            return None  # Can't verify
        
        team_ref_lower = team_ref.lower().strip()
        expected_team_id = TEAM_LOOKUP.get(team_ref_lower)
        
        if expected_team_id is None:
            return None  # Unknown team reference
        
        actual_teams = self.find_player_team(player_name)
        
        if not actual_teams:
            return 'NOT_FOUND'  # Player not on any active roster
        
        for team_id, team_name in actual_teams:
            if team_id == expected_team_id:
                return 'CORRECT'
        
        return ('WRONG_TEAM', actual_teams)


# =============================================================================
# CONTENT EXTRACTORS
# =============================================================================

class ContentExtractor:
    """Extracts player references, stats, and betting lines from HTML content."""
    
    # Common patterns for player-team associations in sports writing
    PLAYER_TEAM_PATTERNS = [
        # "Player Name (Team)" or "Player Name (TEX)"
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\s*\(([A-Z]{2,3})\)',
        # "Team's Player Name" e.g. "Yankees' Aaron Judge"
        r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'s\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",
        # "Player Name of the Team"
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\s+of\s+the\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        # "Player Name, Team pitcher/starter/closer/etc"
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+),\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:pitcher|starter|closer|reliever|outfielder|infielder|catcher|shortstop|first baseman|second baseman|third baseman)',
    ]
    
    # Betting line patterns
    # Moneyline pattern requires context - look for ML/moneyline keywords nearby
    # This prevents matching team records (9-10), spreads (-12.5), years (2025-26)
    MONEYLINE_PATTERN = r'(?:ML|moneyline|money\s*line|odds|to\s*win|favorite|underdog|juice)[:\s]*([+-]\d{3,4})|([+-]\d{3,4})\s*(?:ML|moneyline|odds)'
    OVER_UNDER_PATTERN = r'(?:O/U|over/under|total)[:\s]*(\d+\.?\d?)'
    SPREAD_PATTERN = r'(?:spread|line)[:\s]*([+-]\d+\.?\d?)'

    # Patterns to EXCLUDE from moneyline detection (false positives)
    EXCLUDE_PATTERNS = [
        r'\(\d{1,2}-\d{1,2}(?:-\d{1,2})?\)',  # Team records like (9-10) or (11-10-5)
        r'\d{4}-\d{2,4}',  # Years like 2025-26 or 1971-72
        r'[+-]\d+\.\d',  # Decimals like -12.5 (spreads, not moneylines)
    ]
    
    @staticmethod
    def extract_text_from_html(html_content):
        """Get clean text from HTML."""
        if HAS_BS4:
            soup = BeautifulSoup(html_content, 'html.parser')
            # Remove script/style elements
            for tag in soup(['script', 'style', 'nav', 'header', 'footer']):
                tag.decompose()
            # Get article/main content if available
            main = soup.find('main') or soup.find('article') or soup.find(class_=re.compile(r'content|article|post|blog'))
            if main:
                return main.get_text(' ', strip=True)
            return soup.get_text(' ', strip=True)
        else:
            # Fallback: strip tags with regex
            text = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r'<[^>]+>', ' ', text)
            return text
    
    @staticmethod
    def extract_player_team_refs(text):
        """Extract player-team associations from text."""
        refs = []
        for pattern in ContentExtractor.PLAYER_TEAM_PATTERNS:
            matches = re.finditer(pattern, text)
            for m in matches:
                refs.append({
                    'player': m.group(1) if '\'s' not in pattern else m.group(2),
                    'team': m.group(2) if '\'s' not in pattern else m.group(1),
                    'context': text[max(0, m.start()-30):m.end()+30].strip()
                })
        return refs
    
    @staticmethod
    def extract_stats(text):
        """Extract statistical references from text."""
        stats = []
        for stat_key, stat_info in Config.MLB_STAT_RANGES.items():
            matches = re.finditer(stat_info['pattern'], text, re.IGNORECASE)
            for m in matches:
                try:
                    value = float(m.group(1))
                    stats.append({
                        'stat': stat_key,
                        'display': stat_info['display'],
                        'value': value,
                        'raw': m.group(0),
                        'context': text[max(0, m.start()-40):m.end()+40].strip(),
                        'range': stat_info,
                    })
                except ValueError:
                    pass
        return stats
    
    @staticmethod
    def extract_betting_lines(text):
        """Extract betting lines from text."""
        lines = []

        # Moneylines - only extract when in proper betting context
        for m in re.finditer(ContentExtractor.MONEYLINE_PATTERN, text, re.IGNORECASE):
            # Get the matched value (could be group 1 or 2 depending on pattern)
            value_str = m.group(1) or m.group(2)
            if not value_str:
                continue
            value = int(value_str)

            # Skip values that are clearly not moneylines (too small)
            # Real moneylines are typically -500 to +500, never between -100 and +100
            if -100 < value < 100:
                continue

            lines.append({
                'type': 'moneyline',
                'value': value,
                'raw': m.group(0),
                'context': text[max(0, m.start()-30):m.end()+30].strip(),
            })
        
        # Over/under
        for m in re.finditer(ContentExtractor.OVER_UNDER_PATTERN, text, re.IGNORECASE):
            value = float(m.group(1))
            lines.append({
                'type': 'over_under',
                'value': value,
                'raw': m.group(0),
                'context': text[max(0, m.start()-30):m.end()+30].strip(),
            })
        
        # Spreads
        for m in re.finditer(ContentExtractor.SPREAD_PATTERN, text, re.IGNORECASE):
            value = float(m.group(1))
            lines.append({
                'type': 'spread',
                'value': value,
                'raw': m.group(0),
                'context': text[max(0, m.start()-30):m.end()+30].strip(),
            })
        
        return lines


# =============================================================================
# HTML STRUCTURE VALIDATOR
# =============================================================================

class StructureValidator:
    """Validates HTML structure and navigation consistency."""
    
    # Required nav links that should appear on every page
    # Each entry can be a string or list of alternatives
    EXPECTED_NAV_LINKS = [
        'index.html',
        'handicapping-hub.html',
        ['blog.html', 'blog-page'],  # Accept either blog.html or blog-pageXX.html
    ]

    @staticmethod
    def validate_html(filepath, html_content):
        """Run all structural checks on an HTML file."""
        issues = []

        if not HAS_BS4:
            return issues

        soup = BeautifulSoup(html_content, 'html.parser')

        # Check for basic HTML structure
        if not soup.find('html'):
            issues.append(('ERROR', 'Missing <html> tag'))
        if not soup.find('head'):
            issues.append(('ERROR', 'Missing <head> tag'))
        if not soup.find('body'):
            issues.append(('ERROR', 'Missing <body> tag'))
        if not soup.find('title'):
            issues.append(('WARNING', 'Missing <title> tag'))

        # Check navigation exists
        nav = soup.find('nav') or soup.find(class_=re.compile(r'nav'))
        if not nav:
            issues.append(('WARNING', 'No <nav> element found'))
        else:
            # Check for expected nav links
            nav_links = [a.get('href', '') for a in nav.find_all('a')]
            for expected in StructureValidator.EXPECTED_NAV_LINKS:
                # Handle list of alternatives
                if isinstance(expected, list):
                    if not any(any(alt in link for link in nav_links) for alt in expected):
                        issues.append(('WARNING', f'Expected nav link missing: {expected[0]}'))
                else:
                    if not any(expected in link for link in nav_links):
                        issues.append(('WARNING', f'Expected nav link missing: {expected}'))
        
        # Check for empty elements that shouldn't be empty
        for tag_name in ['h1', 'h2', 'h3', 'p', 'a', 'li']:
            for tag in soup.find_all(tag_name):
                if tag.get_text(strip=True) == '' and not tag.find('img'):
                    issues.append(('WARNING', f'Empty <{tag_name}> element found'))
                    break  # Only report once per tag type
        
        # Check for broken internal links
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            if href.startswith(('http://', 'https://', 'mailto:', 'tel:', '#', 'javascript:')):
                continue
            # Internal link - check if the file might exist
            if href.endswith('.html') or href.endswith('.htm'):
                linked_file = os.path.join(os.path.dirname(filepath), href.split('?')[0].split('#')[0])
                if not os.path.exists(linked_file):
                    issues.append(('WARNING', f'Possibly broken internal link: {href}'))
        
        # Check for duplicate IDs
        ids_seen = {}
        for tag in soup.find_all(id=True):
            tag_id = tag['id']
            if tag_id in ids_seen:
                issues.append(('WARNING', f'Duplicate ID found: #{tag_id}'))
            ids_seen[tag_id] = True
        
        return issues


# =============================================================================
# CONTENT VALIDATORS
# =============================================================================

class ContentValidator:
    """Validates sports content accuracy."""
    
    @staticmethod
    def validate_stats(stats):
        """Check if statistics are within valid ranges."""
        issues = []
        for stat in stats:
            value = stat['value']
            info = stat['range']
            
            if value < info['min'] or value > info['max']:
                issues.append((
                    'ERROR',
                    f"IMPOSSIBLE {info['display']}: {value} "
                    f"(valid range: {info['min']}-{info['max']})",
                    stat['context']
                ))
            elif value < info['typical_min'] or value > info['typical_max']:
                issues.append((
                    'WARNING',
                    f"UNUSUAL {info['display']}: {value} "
                    f"(typical range: {info['typical_min']}-{info['typical_max']})",
                    stat['context']
                ))
        
        return issues
    
    @staticmethod
    def validate_betting_lines(lines):
        """Check if betting lines are reasonable."""
        issues = []
        for line in lines:
            if line['type'] == 'moneyline':
                ml = line['value']
                context = line['context'].lower()

                # Skip if this looks like a year (e.g., 2025, 2026)
                if abs(ml) >= 1900 and abs(ml) <= 2100:
                    # Check if context suggests it's a year
                    if any(word in context for word in ['season', 'year', 'january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december', '20' + str(abs(ml) % 100)]):
                        continue

                min_ml, max_ml = Config.MONEYLINE_RANGE
                if ml < min_ml or ml > max_ml:
                    issues.append((
                        'WARNING',
                        f"Extreme moneyline: {ml} (typical range: {min_ml} to +{max_ml})",
                        line['context']
                    ))
                # Check for invalid moneylines (between -100 and +100 exclusive)
                # Note: With the new extraction logic, these should not appear anymore
                if -100 < ml < 100 and ml != 0:
                    issues.append((
                        'ERROR',
                        f"Invalid moneyline: {ml} (moneylines can't be between -100 and +100)",
                        line['context']
                    ))
            
            elif line['type'] == 'over_under':
                ou = line['value']
                # Try to detect which sport
                for sport, (min_ou, max_ou) in Config.OVER_UNDER_RANGE.items():
                    if min_ou - 2 <= ou <= max_ou + 2:
                        break
                else:
                    issues.append((
                        'WARNING',
                        f"Unusual over/under: {ou} (doesn't match typical ranges for any sport)",
                        line['context']
                    ))
        
        return issues
    
    @staticmethod
    def validate_roster(player_team_refs, roster_manager):
        """Check player-team associations against active rosters."""
        issues = []
        
        if not roster_manager.loaded:
            return issues
        
        for ref in player_team_refs:
            result = roster_manager.verify_player_on_team(ref['player'], ref['team'])
            
            if result == 'CORRECT':
                continue
            elif result == 'NOT_FOUND':
                issues.append((
                    'WARNING',
                    f"Player '{ref['player']}' not found on any active MLB roster "
                    f"(referenced with {ref['team']})",
                    ref['context']
                ))
            elif isinstance(result, tuple) and result[0] == 'WRONG_TEAM':
                actual_teams = ', '.join([t[1] for t in result[1]])
                issues.append((
                    'ERROR',
                    f"ROSTER ERROR: '{ref['player']}' referenced with {ref['team']} "
                    f"but is actually on: {actual_teams}",
                    ref['context']
                ))
        
        return issues
    
    @staticmethod
    def check_known_facts(text):
        """Check for known false information based on CURRENT_FACTS database."""
        issues = []
        text_lower = text.lower()

        # Check wrong player-team associations
        for player, wrong_team, error_msg in WRONG_PLAYER_TEAM_ASSOCIATIONS:
            # Find all occurrences of the player name
            player_pattern = re.compile(r'\b' + re.escape(player) + r'\b', re.IGNORECASE)
            for match in player_pattern.finditer(text_lower):
                pos = match.start()
                # Get surrounding context (sentence-ish)
                start = max(0, text_lower.rfind('.', 0, pos) + 1, text_lower.rfind('\n', 0, pos) + 1)
                end = min(len(text_lower),
                         text_lower.find('.', pos) if text_lower.find('.', pos) != -1 else len(text_lower),
                         text_lower.find('\n', pos) if text_lower.find('\n', pos) != -1 else len(text_lower))
                sentence = text_lower[start:end]

                # Check if wrong team is mentioned in same sentence
                if re.search(r'\b' + re.escape(wrong_team) + r'\b', sentence):
                    # Allow if discussing trade history or the player leaving
                    trade_words = ['traded', 'former', 'ex-', 'left', 'was with', 'from the', 'no longer',
                                  'previously', 'used to', 'acquired from', 'sent to', 'deal with',
                                  'blockbuster', 'trade from', 'arriving from', 'came from']
                    if not any(tw in sentence for tw in trade_words):
                        context = text[max(0, pos-50):min(len(text), pos+100)]
                        issues.append((
                            'ERROR',
                            f"FALSE INFO: {error_msg}",
                            context.strip()
                        ))

        # Check wrong injury claims
        for player, wrong_injury, correct_injury, error_msg in WRONG_INJURY_CLAIMS:
            player_pattern = re.compile(r'\b' + re.escape(player) + r'\b', re.IGNORECASE)
            for match in player_pattern.finditer(text_lower):
                pos = match.start()
                context_start = max(0, pos - 100)
                context_end = min(len(text_lower), pos + 100)
                context = text_lower[context_start:context_end]

                if wrong_injury in context and correct_injury not in context:
                    issues.append((
                        'ERROR',
                        f"WRONG INJURY: {error_msg}",
                        text[context_start:context_end].strip()
                    ))

        return issues

    @staticmethod
    def check_placeholder_content(text, html_content):
        """Check for placeholder content that should not be published."""
        issues = []

        for pattern, error_msg in PLACEHOLDER_PATTERNS:
            matches = list(re.finditer(pattern, text, re.IGNORECASE))
            for match in matches:
                # Skip if inside script or style tags
                pos = match.start()
                before = html_content[:pos].lower() if pos < len(html_content) else ""
                if '<script' in before[max(0, len(before)-500):] and '</script>' not in before[max(0, len(before)-500):]:
                    continue
                if '<style' in before[max(0, len(before)-500):] and '</style>' not in before[max(0, len(before)-500):]:
                    continue

                context = text[max(0, pos-30):min(len(text), pos+50)]
                issues.append((
                    'ERROR',
                    f"PLACEHOLDER: {error_msg}",
                    context.strip()
                ))

        return issues

    @staticmethod
    def check_banned_content(text, filepath=""):
        """Check for content that is explicitly banned."""
        issues = []

        for pattern, error_msg in BANNED_CONTENT_PATTERNS:
            matches = list(re.finditer(pattern, text, re.IGNORECASE))
            for match in matches:
                context = text[max(0, match.start()-30):min(len(text), match.end()+50)]
                issues.append((
                    'ERROR',
                    f"BANNED CONTENT: {error_msg}",
                    context.strip()
                ))

        # Check line movement patterns (but allow in educational content)
        filepath_lower = filepath.lower()
        is_educational = any(allowed in filepath_lower for allowed in LINE_MOVEMENT_ALLOWED_FILES)

        if not is_educational:
            for pattern in LINE_MOVEMENT_PATTERNS:
                matches = list(re.finditer(pattern, text, re.IGNORECASE))
                for match in matches:
                    context = text[max(0, match.start()-30):min(len(text), match.end()+50)]
                    issues.append((
                        'ERROR',
                        f"BANNED CONTENT: Line movement discussions are BANNED per January 24, 2026 rule",
                        context.strip()
                    ))

        return issues

    @staticmethod
    def check_wrong_unsigned_claims(text):
        """Check for claims that players are unsigned when they have signed."""
        issues = []

        for pattern, error_msg in WRONG_UNSIGNED_CLAIMS:
            matches = list(re.finditer(pattern, text, re.IGNORECASE))
            for match in matches:
                context = text[max(0, match.start()-30):min(len(text), match.end()+50)]
                issues.append((
                    'ERROR',
                    f"STALE INFO: {error_msg}",
                    context.strip()
                ))

        return issues

    @staticmethod
    def check_impossible_statistics(text):
        """Check for obviously impossible statistics."""
        issues = []

        # Check for percentages over 100 (but exclude marketing bonuses, vig explanations)
        pct_pattern = r'(\d+(?:\.\d+)?)\s*%'
        for match in re.finditer(pct_pattern, text):
            try:
                value = float(match.group(1))
                if value > 100:
                    context = text[max(0, match.start()-50):min(len(text), match.end()+50)]
                    context_lower = context.lower()
                    # Skip marketing/bonus percentages
                    if any(word in context_lower for word in ['bonus', 'promo', 'welcome', 'deposit', 'match', 'vig', 'juice', 'implied', 'totaling', 'extra']):
                        continue
                    issues.append((
                        'ERROR',
                        f"IMPOSSIBLE STAT: {value}% - percentages cannot exceed 100%",
                        context.strip()
                    ))
            except ValueError:
                pass

        # Check for impossible PLAYER PPG (NBA) - must be clearly player-specific
        # Only flag if pattern clearly indicates individual player stats
        player_ppg_pattern = r'(?:he\s+is\s+averaging|(?:is\s+)?averaging\s+(?:a\s+)?career|player\s+averaging)\s+(\d+(?:\.\d+)?)\s*(?:PPG|points)'
        for match in re.finditer(player_ppg_pattern, text, re.IGNORECASE):
            try:
                value = float(match.group(1))
                if value > 55:  # Wilt's record is 50.4
                    context = text[max(0, match.start()-30):min(len(text), match.end()+30)]
                    issues.append((
                        'ERROR',
                        f"IMPOSSIBLE STAT: {value} PPG - no NBA player has averaged over 55 PPG",
                        context.strip()
                    ))
            except ValueError:
                pass

        # Check for impossible batting averages
        ba_pattern = r'(?:batting average|avg|BA)[:\s]+\.?([5-9]\d{2}|\d{4,})'
        for match in re.finditer(ba_pattern, text, re.IGNORECASE):
            context = text[max(0, match.start()-30):min(len(text), match.end()+30)]
            issues.append((
                'ERROR',
                f"IMPOSSIBLE STAT: Batting average .{match.group(1)} is impossible",
                context.strip()
            ))

        return issues

    @staticmethod
    def check_suspicious_betting_lines(text):
        """Check for betting lines that look made up (round numbers)."""
        issues = []

        # Check for round spreads (no .5) - these are suspicious
        spread_pattern = r'(?:spread|line)[:\s]*([+-]?\d+)(?:\.0)?(?!\.\d)'
        for match in re.finditer(spread_pattern, text, re.IGNORECASE):
            try:
                spread = int(match.group(1))
                # Round spreads are unusual (except 0)
                if spread != 0 and abs(spread) <= 20:
                    context = text[max(0, match.start()-30):min(len(text), match.end()+50)]
                    issues.append((
                        'WARNING',
                        f"SUSPICIOUS LINE: Spread {spread} is a round number - most spreads end in .5",
                        context.strip()
                    ))
            except ValueError:
                pass

        return issues

    @staticmethod
    def check_date_references(text):
        """Check for obviously wrong date references."""
        issues = []
        today = datetime.now()
        
        # Look for date patterns like "January 15, 2024"
        date_pattern = r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(\d{4})'
        for m in re.finditer(date_pattern, text):
            try:
                month_str, day, year = m.group(1), int(m.group(2)), int(m.group(3))
                months = {'January': 1, 'February': 2, 'March': 3, 'April': 4,
                         'May': 5, 'June': 6, 'July': 7, 'August': 8,
                         'September': 9, 'October': 10, 'November': 11, 'December': 12}
                month = months.get(month_str, 0)
                
                ref_date = datetime(year, month, day)
                
                # Flag dates more than 2 days in the future
                if ref_date > today + timedelta(days=2):
                    issues.append((
                        'WARNING',
                        f"Future date reference: {m.group(0)} (today is {today.strftime('%B %d, %Y')})",
                        text[max(0, m.start()-30):m.end()+30].strip()
                    ))
                
                # Flag dates more than a year old in context that seems current
                if ref_date < today - timedelta(days=365):
                    context = text[max(0, m.start()-50):m.end()+50].lower()
                    if any(word in context for word in ['today', 'tonight', 'this week', 'upcoming']):
                        issues.append((
                            'ERROR',
                            f"Stale date with current language: {m.group(0)}",
                            text[max(0, m.start()-40):m.end()+40].strip()
                        ))
            except (ValueError, KeyError):
                pass
        
        return issues


# =============================================================================
# MAIN VALIDATOR
# =============================================================================

class BetLegendValidator:
    """Main validator that orchestrates all checks."""
    
    def __init__(self, target_path):
        self.target_path = target_path
        self.roster_manager = RosterManager()
        self.results = defaultdict(list)  # filepath -> list of issues
        self.summary = {'errors': 0, 'warnings': 0, 'files_scanned': 0, 'files_with_issues': 0}
    
    def run(self):
        """Run the full validation suite."""
        print("=" * 70)
        print("  BETLEGEND CONTENT VALIDATOR & PRE-PUBLISH FILTER")
        print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        print()
        
        # Load rosters
        print("[1/4] Loading MLB roster data...")
        self.roster_manager.load_rosters()
        print()
        
        # Find files to scan
        print("[2/4] Finding HTML files to scan...")
        files = self._find_files()
        print(f"  Found {len(files)} HTML files")
        print()
        
        if not files:
            print("  No HTML files found. Check your path.")
            return
        
        # Scan files
        print("[3/4] Scanning content...")
        for i, filepath in enumerate(files):
            self._validate_file(filepath)
            # Progress indicator
            if (i + 1) % 50 == 0 or (i + 1) == len(files):
                print(f"  Scanned {i+1}/{len(files)} files...")
        print()
        
        # Report
        print("[4/4] Generating report...")
        self._print_report()
    
    def _find_files(self):
        """Find all HTML files to scan."""
        target = Path(self.target_path)
        
        if target.is_file():
            return [str(target)]
        
        files = []
        for root, dirs, filenames in os.walk(target):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in Config.SKIP_DIRS]
            
            for fname in filenames:
                if Path(fname).suffix.lower() in Config.HTML_EXTENSIONS:
                    if fname not in Config.SKIP_FILES:
                        # Also check glob patterns
                        skip = False
                        for pattern in Config.SKIP_FILE_PATTERNS:
                            if fnmatch.fnmatch(fname, pattern):
                                skip = True
                                break
                        if not skip:
                            files.append(os.path.join(root, fname))
        
        return sorted(files)
    
    def _validate_file(self, filepath):
        """Run all validations on a single file."""
        self.summary['files_scanned'] += 1
        issues = []
        
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                html_content = f.read()
        except Exception as e:
            issues.append(('ERROR', f'Could not read file: {e}', ''))
            self.results[filepath] = issues
            return
        
        # Extract text content
        text = ContentExtractor.extract_text_from_html(html_content)
        
        # 1. HTML structure validation
        struct_issues = StructureValidator.validate_html(filepath, html_content)
        for severity, msg in struct_issues:
            issues.append((severity, msg, ''))
        
        # 2. Statistical validation
        stats = ContentExtractor.extract_stats(text)
        stat_issues = ContentValidator.validate_stats(stats)
        issues.extend(stat_issues)
        
        # 3. Betting line validation
        betting_lines = ContentExtractor.extract_betting_lines(text)
        line_issues = ContentValidator.validate_betting_lines(betting_lines)
        issues.extend(line_issues)
        
        # 4. Roster validation
        player_refs = ContentExtractor.extract_player_team_refs(text)
        roster_issues = ContentValidator.validate_roster(player_refs, self.roster_manager)
        issues.extend(roster_issues)
        
        # 5. Date validation
        date_issues = ContentValidator.check_date_references(text)
        issues.extend(date_issues)

        # 6. Known facts validation (CRITICAL - catches player trades, injuries, etc.)
        known_facts_issues = ContentValidator.check_known_facts(text)
        issues.extend(known_facts_issues)

        # 7. Placeholder content check
        placeholder_issues = ContentValidator.check_placeholder_content(text, html_content)
        issues.extend(placeholder_issues)

        # 8. Banned content check (source citations, line movements)
        banned_issues = ContentValidator.check_banned_content(text, filepath)
        issues.extend(banned_issues)

        # 9. Wrong unsigned claims check
        unsigned_issues = ContentValidator.check_wrong_unsigned_claims(text)
        issues.extend(unsigned_issues)

        # 10. Impossible statistics check
        impossible_stats_issues = ContentValidator.check_impossible_statistics(text)
        issues.extend(impossible_stats_issues)

        # 11. Suspicious betting lines check
        suspicious_lines_issues = ContentValidator.check_suspicious_betting_lines(text)
        issues.extend(suspicious_lines_issues)

        # Store results
        if issues:
            self.results[filepath] = issues
            self.summary['files_with_issues'] += 1
            for severity, _, _ in issues:
                if severity == 'ERROR':
                    self.summary['errors'] += 1
                elif severity == 'WARNING':
                    self.summary['warnings'] += 1
    
    def _print_report(self):
        """Print the validation report."""
        print()
        print("=" * 70)
        print("  VALIDATION REPORT")
        print("=" * 70)
        print()
        print(f"  Files scanned:      {self.summary['files_scanned']}")
        print(f"  Files with issues:  {self.summary['files_with_issues']}")
        print(f"  Total ERRORS:       {self.summary['errors']}")
        print(f"  Total WARNINGS:     {self.summary['warnings']}")
        print()
        
        if not self.results:
            print("  [PASS] ALL CLEAR - No issues found!")
            print()
            return
        
        # Print errors first, then warnings
        for filepath, issues in sorted(self.results.items()):
            errors = [(s, m, c) for s, m, c in issues if s == 'ERROR']
            warnings = [(s, m, c) for s, m, c in issues if s == 'WARNING']
            
            if errors:
                rel_path = os.path.relpath(filepath, self.target_path) if os.path.isdir(self.target_path) else os.path.basename(filepath)
                print(f"  [ERROR] {rel_path}")
                for severity, msg, context in errors:
                    print(f"     [{severity}] {msg}")
                    if context:
                        print(f"     Context: ...{context}...")
                print()
        
        # Warnings section
        warning_files = {fp: issues for fp, issues in self.results.items()
                        if any(s == 'WARNING' for s, _, _ in issues)}
        
        if warning_files:
            print("-" * 70)
            print("  WARNINGS (review recommended):")
            print("-" * 70)
            print()
            for filepath, issues in sorted(warning_files.items()):
                warnings = [(s, m, c) for s, m, c in issues if s == 'WARNING']
                if warnings:
                    rel_path = os.path.relpath(filepath, self.target_path) if os.path.isdir(self.target_path) else os.path.basename(filepath)
                    print(f"  [WARN] {rel_path}")
                    for severity, msg, context in warnings:
                        print(f"     [{severity}] {msg}")
                        if context:
                            print(f"     Context: ...{context}...")
                    print()
        
        # Final verdict
        print("=" * 70)
        if self.summary['errors'] > 0:
            print(f"  [BLOCKED] HOLD - {self.summary['errors']} error(s) found. Fix before publishing!")
        elif self.summary['warnings'] > 0:
            print(f"  [WARNING] REVIEW - {self.summary['warnings']} warning(s). Check before publishing.")
        else:
            print("  [PASS] ALL CLEAR")
        print("=" * 70)
        print()


# =============================================================================
# GIT INTEGRATION HOOK
# =============================================================================

def install_git_hook(repo_path):
    """Install as a git pre-commit hook."""
    hook_path = os.path.join(repo_path, '.git', 'hooks', 'pre-commit')
    script_path = os.path.abspath(__file__)
    
    hook_content = f"""#!/bin/sh
# BetLegend Content Validator - Pre-commit hook
echo "Running BetLegend content validator..."
python "{script_path}" "{repo_path}"
if [ $? -ne 0 ]; then
    echo ""
    echo "Commit blocked by validator. Fix errors above before committing."
    exit 1
fi
"""
    
    try:
        with open(hook_path, 'w') as f:
            f.write(hook_content)
        os.chmod(hook_path, 0o755)
        print(f"  Git pre-commit hook installed at: {hook_path}")
        print("  The validator will now run automatically before every commit.")
        return True
    except Exception as e:
        print(f"  Could not install git hook: {e}")
        return False


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage:")
        print(f"  python {sys.argv[0]} <path_to_scan>")
        print(f"  python {sys.argv[0]} <path_to_scan> --install-hook")
        print()
        print("Examples:")
        print(f"  python {sys.argv[0]} C:/Users/Nima/nimadamus.github.io")
        print(f"  python {sys.argv[0]} C:/Users/Nima/nimadamus.github.io/blog-page12.html")
        print(f"  python {sys.argv[0]} C:/Users/Nima/nimadamus.github.io --install-hook")
        sys.exit(1)
    
    target = sys.argv[1]
    
    if not os.path.exists(target):
        print(f"Error: Path does not exist: {target}")
        sys.exit(1)
    
    # Install git hook if requested
    if '--install-hook' in sys.argv:
        print("Installing git pre-commit hook...")
        install_git_hook(target)
        print()
    
    # Run validation
    validator = BetLegendValidator(target)
    validator.run()
    
    # Exit with error code if errors found (useful for git hooks)
    sys.exit(1 if validator.summary['errors'] > 0 else 0)
