"""
Auto-Content Generation System Configuration
BetLegend Picks - Daily Sports Content Automation
"""

import os
from datetime import datetime

# =============================================================================
# API CONFIGURATION
# =============================================================================

# Claude API - Priority: api_keys.py > environment variable > empty
# Create api_keys.py with ANTHROPIC_API_KEY = "your-key-here" (not committed to git)
try:
    from api_keys import ANTHROPIC_API_KEY as _secret_key
    ANTHROPIC_API_KEY = _secret_key
except ImportError:
    ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')

# Model to use for content generation
CLAUDE_MODEL = "claude-sonnet-4-20250514"

# =============================================================================
# PATHS
# =============================================================================

# Base repository path - dynamically determine based on script location
# This works on both Windows (local) and Linux (GitHub Actions)
_script_dir = os.path.dirname(os.path.abspath(__file__))
REPO_PATH = os.path.dirname(os.path.dirname(_script_dir))  # Go up from scripts/auto_content to repo root

# Scripts path
SCRIPTS_PATH = os.path.join(REPO_PATH, "scripts", "auto_content")

# Templates path
TEMPLATES_PATH = os.path.join(SCRIPTS_PATH, "templates")

# =============================================================================
# SPORT CONFIGURATIONS
# =============================================================================

SPORTS = {
    "nba": {
        "name": "NBA",
        "full_name": "National Basketball Association",
        "main_page": "nba.html",
        "page_prefix": "nba-page",
        "total_pages": 9,
        "espn_sport": "basketball",
        "espn_league": "nba",
        "season_months": [10, 11, 12, 1, 2, 3, 4, 5, 6],  # Oct-June
        "emoji": "🏀",
        "active": True
    },
    "nhl": {
        "name": "NHL",
        "full_name": "National Hockey League",
        "main_page": "nhl.html",
        "page_prefix": "nhl-page",
        "total_pages": 19,
        "espn_sport": "hockey",
        "espn_league": "nhl",
        "season_months": [10, 11, 12, 1, 2, 3, 4, 5, 6],  # Oct-June
        "emoji": "🏒",
        "active": True
    },
    "nfl": {
        "name": "NFL",
        "full_name": "National Football League",
        "main_page": "nfl.html",
        "page_prefix": "nfl-page",
        "total_pages": 14,
        "espn_sport": "football",
        "espn_league": "nfl",
        "season_months": [9, 10, 11, 12, 1, 2],  # Sep-Feb
        "emoji": "🏈",
        "active": True
    },
    "ncaab": {
        "name": "NCAAB",
        "full_name": "NCAA Men's Basketball",
        "main_page": "ncaab.html",
        "page_prefix": "ncaab-page",
        "total_pages": 5,
        "espn_sport": "basketball",
        "espn_league": "mens-college-basketball",
        "season_months": [11, 12, 1, 2, 3, 4],  # Nov-April
        "emoji": "🏀",
        "active": True
    },
    "ncaaf": {
        "name": "NCAAF",
        "full_name": "NCAA Football",
        "main_page": "ncaaf.html",
        "page_prefix": "ncaaf-page",
        "total_pages": 7,
        "espn_sport": "football",
        "espn_league": "college-football",
        "season_months": [8, 9, 10, 11, 12, 1],  # Aug-Jan
        "emoji": "🏈",
        "active": True
    },
    "mlb": {
        "name": "MLB",
        "full_name": "Major League Baseball",
        "main_page": "mlb.html",
        "page_prefix": "mlb-page",
        "total_pages": 2,
        "espn_sport": "baseball",
        "espn_league": "mlb",
        "season_months": [3, 4, 5, 6, 7, 8, 9, 10, 11],  # Mar-Nov
        "emoji": "⚾",
        "active": True
    },
    "soccer": {
        "name": "Soccer",
        "full_name": "Soccer (Multiple Leagues)",
        "main_page": "soccer.html",
        "page_prefix": "soccer-page",
        "total_pages": 3,
        "espn_sport": "soccer",
        "espn_league": "eng.1",  # Premier League default
        "leagues": ["eng.1", "esp.1", "ger.1", "ita.1", "fra.1", "usa.1", "mex.1"],
        "season_months": list(range(1, 13)),  # Year-round
        "emoji": "⚽",
        "active": True
    }
}

# =============================================================================
# ESPN API ENDPOINTS
# =============================================================================

ESPN_BASE_URL = "https://site.api.espn.com/apis/site/v2/sports"

def get_espn_scoreboard_url(sport, league, date=None):
    """Get ESPN scoreboard URL for a sport/league."""
    if date is None:
        date = datetime.now().strftime("%Y%m%d")
    return f"{ESPN_BASE_URL}/{sport}/{league}/scoreboard?dates={date}"

def get_espn_teams_url(sport, league):
    """Get ESPN teams URL for a sport/league."""
    return f"{ESPN_BASE_URL}/{sport}/{league}/teams"

def get_espn_standings_url(sport, league):
    """Get ESPN standings URL for a sport/league."""
    return f"{ESPN_BASE_URL}/{sport}/{league}/standings"

def get_espn_team_url(sport, league, team_id):
    """Get ESPN team detail URL."""
    return f"{ESPN_BASE_URL}/{sport}/{league}/teams/{team_id}"

# =============================================================================
# CONTENT SETTINGS
# =============================================================================

# Maximum games to cover per sport per day
MAX_GAMES_PER_SPORT = 15

# Article style settings
ARTICLE_STYLE = {
    "tone": "conversational but analytical",
    "length": "200-350 words per game",
    "include_stats": True,
    "include_trends": True,
    "include_injuries": True,
    "betting_focus": True
}

# =============================================================================
# ARCHIVE SETTINGS
# =============================================================================

# How many posts to keep on main page before archiving
POSTS_PER_PAGE = 3

# Date format for posts
DATE_FORMAT = "%B %d, %Y"
TIME_FORMAT = "%I:%M %p PT"

# =============================================================================
# GIT SETTINGS
# =============================================================================

GIT_AUTO_COMMIT = True
GIT_AUTO_PUSH = True
GIT_COMMIT_MESSAGE_TEMPLATE = "Auto-update {sport} content for {date}"
