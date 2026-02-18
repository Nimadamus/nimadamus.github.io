#!/usr/bin/env python3
"""
Enhanced Content Validator with Live ESPN Data Verification
===========================================================

Validates BetLegend HTML content against live ESPN scoreboard data.

Checks:
  1. Player-team associations (existing check - preserved)
  2. Injury information (existing check - preserved)
  3. Placeholder content (existing check - preserved)
  4. Betting lines vs ESPN data (NEW - live verification)
  5. Team records vs ESPN data (NEW - live verification)
  6. Quote detection (NEW - flags unverifiable quotes)

ESPN Scoreboard API (free, no auth required):
  https://site.api.espn.com/apis/site/v2/sports/{sport}/{league}/scoreboard?dates=YYYYMMDD

Usage:
  python scripts/live_content_validator.py              # reads changed_files.txt
  python scripts/live_content_validator.py file1.html   # validate specific file(s)

Exit codes:
  0 = PASSED (may have warnings)
  1 = ERRORS found - should block push
"""

import os
import re
import sys
import io
import json
from datetime import datetime

# Fix Windows console encoding
if sys.platform == 'win32':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass

# ASCII-safe status symbols
OK = "[OK]"
WARN = "[!!]"
FAIL = "[XX]"

# Try to import requests; if unavailable, live checks are skipped
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# =============================================================================
# CONFIGURATION
# =============================================================================

# ESPN API endpoints by sport keyword
ESPN_ENDPOINTS = {
    "nba": "basketball/nba",
    "nhl": "hockey/nhl",
    "nfl": "football/nfl",
    "ncaab": "basketball/mens-college-basketball",
    "college-basketball": "basketball/mens-college-basketball",
    "ncaaf": "football/college-football",
    "college-football": "football/college-football",
    "mlb": "baseball/mlb",
    "soccer": "soccer/eng.1",
}

# Sport detection patterns in filenames
SPORT_PATTERNS = [
    (r'\b(?:nba)\b', "nba"),
    (r'\b(?:nhl)\b', "nhl"),
    (r'\b(?:nfl)\b', "nfl"),
    (r'\b(?:ncaab|college-basketball)\b', "ncaab"),
    (r'\b(?:ncaaf|college-football)\b', "ncaaf"),
    (r'\b(?:mlb)\b', "mlb"),
    (r'\b(?:soccer)\b', "soccer"),
]

# Month name to number mapping
MONTH_MAP = {
    "january": "01", "february": "02", "march": "03", "april": "04",
    "may": "05", "june": "06", "july": "07", "august": "08",
    "september": "09", "october": "10", "november": "11", "december": "12",
}

# Thresholds for comparing values
THRESHOLDS = {
    "spread_warn": 1.5,
    "spread_error": 3.0,
    "moneyline_warn": 50,
    "moneyline_error": 100,
    "total_warn": 2.5,
    "total_error": 5.0,
    "record_wins_warn": 2,
    "record_wins_error": 3,
}

# =============================================================================
# EXISTING CHECKS (preserved from original validator)
# =============================================================================

WRONG_ASSOCIATIONS = [
    ("de'aaron fox", "kings", "De'Aaron Fox is on the SPURS, not Kings"),
    ("de'aaron fox", "heat", "De'Aaron Fox is on the SPURS - he was NEVER on the Heat"),
    ("deaaron fox", "kings", "De'Aaron Fox is on the SPURS, not Kings"),
    ("deaaron fox", "heat", "De'Aaron Fox is on the SPURS - he was NEVER on the Heat"),
    ("bregman", "astros", "Alex Bregman signed with the CUBS in January 2026"),
    ("bregman", "houston", "Alex Bregman signed with the CUBS in January 2026"),
    ("tucker", "astros", "Kyle Tucker was traded to the DODGERS"),
    ("alonso", "mets", "Pete Alonso signed with the ORIOLES"),
    ("durant", "suns", "Kevin Durant was traded to the ROCKETS"),
    ("durant", "phoenix", "Kevin Durant was traded to the ROCKETS"),
    ("marner", "maple leafs", "Mitch Marner was traded to the GOLDEN KNIGHTS"),
    ("marner", "leafs", "Mitch Marner was traded to the GOLDEN KNIGHTS"),
    ("marner", "toronto", "Mitch Marner was traded to the GOLDEN KNIGHTS"),
    ("lavine", "bulls", "Zach LaVine was traded to the KINGS"),
    ("butler", "heat", "Jimmy Butler was traded to the WARRIORS"),
    ("ingram", "pelicans", "Brandon Ingram was traded to the RAPTORS"),
]

INJURY_FACTS = {
    "tatum": {"correct": "achilles", "wrong": "acl",
              "message": "Jayson Tatum has ACHILLES injury, NOT ACL"},
}

PLACEHOLDER_PATTERNS = [r'\bcoming soon\b', r'\bTBD\b', r'\bTBA\b']

TRADE_CONTEXT_WORDS = [
    'traded', 'former', 'ex-', 'left', 'was with', 'from the',
    'trade from', 'no longer', 'previously', 'acquired from', 'came from',
    'from toronto', 'from chicago', 'from houston', 'from phoenix', 'from miami',
]


# =============================================================================
# ESPN API
# =============================================================================

def fetch_espn_scoreboard(sport_key, date_str):
    """
    Fetch ESPN scoreboard data for a sport and date.
    Returns list of game dicts or None on failure.
    date_str format: YYYYMMDD
    """
    if not HAS_REQUESTS:
        return None

    endpoint = ESPN_ENDPOINTS.get(sport_key)
    if not endpoint:
        return None

    url = f"https://site.api.espn.com/apis/site/v2/sports/{endpoint}/scoreboard?dates={date_str}"

    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"  [WARN] ESPN API unavailable for {sport_key}: {e}")
        return None

    games = []
    for event in data.get("events", []):
        game = parse_espn_event(event)
        if game:
            games.append(game)

    return games


def parse_espn_event(event):
    """Parse a single ESPN event into a structured dict."""
    competition = event.get("competitions", [{}])[0]
    competitors = competition.get("competitors", [])

    if len(competitors) < 2:
        return None

    game = {"raw_event": event}

    for comp in competitors:
        side = "home" if comp.get("homeAway") == "home" else "away"
        team = comp.get("team", {})

        game[f"{side}_name"] = team.get("displayName", "")
        game[f"{side}_short"] = team.get("shortDisplayName", "")
        game[f"{side}_abbrev"] = team.get("abbreviation", "").upper()
        game[f"{side}_id"] = team.get("id", "")
        game[f"{side}_location"] = team.get("location", "")
        game[f"{side}_nickname"] = team.get("name", "")

        # Extract record
        records = comp.get("records", [])
        if records:
            overall = records[0].get("summary", "")
            game[f"{side}_record"] = overall  # e.g. "19-6"
        else:
            game[f"{side}_record"] = ""

    # Extract odds if available
    odds_list = competition.get("odds", [])
    if odds_list:
        odds = odds_list[0]
        game["spread"] = odds.get("details", "")  # e.g. "BAMA -4.5"
        game["overUnder"] = odds.get("overUnder", None)

        # Extract spread value and favorite
        spread_detail = odds.get("details", "")
        spread_match = re.search(r'([A-Z]+)\s+([+-]?\d+\.?\d*)', spread_detail)
        if spread_match:
            game["spread_fav_abbrev"] = spread_match.group(1)
            game["spread_value"] = float(spread_match.group(2))

        # Home/away moneylines from homeTeamOdds / awayTeamOdds
        home_odds = odds.get("homeTeamOdds", {})
        away_odds = odds.get("awayTeamOdds", {})
        game["home_ml"] = home_odds.get("moneyLine", None)
        game["away_ml"] = away_odds.get("moneyLine", None)
    else:
        game["spread"] = ""
        game["overUnder"] = None
        game["home_ml"] = None
        game["away_ml"] = None

    return game


# =============================================================================
# FILENAME PARSING
# =============================================================================

def detect_sport_from_file(filepath, content):
    """Detect sport from filename or content. Returns sport key or None."""
    filename = os.path.basename(filepath).lower()

    # Try filename patterns first
    for pattern, sport in SPORT_PATTERNS:
        if re.search(pattern, filename):
            return sport

    # For featured game pages (team-vs-team), detect from content
    if "prediction-picks" in filename or "vs" in filename:
        content_lower = content.lower()
        # Check for sport-specific markers in content
        if "ncaab" in content_lower or "college basketball" in content_lower or "sec " in content_lower:
            return "ncaab"
        if "nba" in content_lower and "nba" not in filename:
            return "nba"
        if "nhl" in content_lower or "puck line" in content_lower:
            return "nhl"
        if "nfl" in content_lower:
            return "nfl"
        if "mlb" in content_lower or "baseball" in content_lower:
            return "mlb"
        if "soccer" in content_lower or "premier league" in content_lower:
            return "soccer"
        if "ncaaf" in content_lower or "college football" in content_lower:
            return "ncaaf"

        # Check for college team logos (ncaa/500/)
        if "teamlogos/ncaa" in content_lower:
            # Could be NCAAB or NCAAF - check for basketball indicators
            if any(w in content_lower for w in ["basketball", "ncaab", "kenpom", "big east",
                                                  "big 12", "sec basketball", "acc basketball"]):
                return "ncaab"
            elif any(w in content_lower for w in ["football", "ncaaf", "cfp", "bowl"]):
                return "ncaaf"
            # Default to NCAAB during basketball season (Nov-Mar)
            return "ncaab"

    return None


def extract_date_from_file(filepath, content):
    """
    Extract the target date from filename or content.
    Returns YYYYMMDD string or None.
    """
    filename = os.path.basename(filepath).lower()

    # Try filename: ...february-18-2026.html
    date_match = re.search(
        r'(january|february|march|april|may|june|july|august|september|october|november|december)'
        r'-(\d{1,2})-(\d{4})',
        filename
    )
    if date_match:
        month = MONTH_MAP[date_match.group(1)]
        day = date_match.group(2).zfill(2)
        year = date_match.group(3)
        return f"{year}{month}{day}"

    # Try FORCED_PAGE_DATE in content
    forced_match = re.search(r"FORCED_PAGE_DATE\s*=\s*['\"](\d{4})-(\d{2})-(\d{2})['\"]", content)
    if forced_match:
        return forced_match.group(1) + forced_match.group(2) + forced_match.group(3)

    # Try title tag date
    title_match = re.search(
        r'(January|February|March|April|May|June|July|August|September|October|November|December)'
        r'\s+(\d{1,2}),?\s+(\d{4})',
        content
    )
    if title_match:
        month = MONTH_MAP[title_match.group(1).lower()]
        day = title_match.group(2).zfill(2)
        year = title_match.group(3)
        return f"{year}{month}{day}"

    return None


# =============================================================================
# HTML CONTENT EXTRACTION
# =============================================================================

def extract_betting_lines_from_html(content):
    """
    Extract all betting lines from HTML content.
    Returns list of dicts with keys: team_abbrev, spread, moneyline, total, context
    """
    lines = []

    # Pattern 1: bet-value divs (sports pages)
    # <div class="bet-value">UCONN -17.5</div>
    # <div class="bet-value">UCONN -2500 / CREI +900</div>
    # <div class="bet-value">O/U 143.5</div>

    # Find groups of 3 consecutive bet-box divs (Spread, Moneyline, Total)
    spread_pattern = r'<div[^>]*class="bet-label"[^>]*>Spread</div>\s*<div[^>]*class="bet-value"[^>]*>([^<]+)</div>'
    ml_pattern = r'<div[^>]*class="bet-label"[^>]*>Moneyline</div>\s*<div[^>]*class="bet-value"[^>]*>([^<]+)</div>'
    total_pattern = r'<div[^>]*class="bet-label"[^>]*>Total</div>\s*<div[^>]*class="bet-value"[^>]*>([^<]+)</div>'

    spreads = re.findall(spread_pattern, content, re.IGNORECASE)
    moneylines = re.findall(ml_pattern, content, re.IGNORECASE)
    totals = re.findall(total_pattern, content, re.IGNORECASE)

    for i, spread_text in enumerate(spreads):
        entry = {"source": "bet-value"}

        # Parse spread: "UCONN -17.5" or "BAMA -4.5"
        sp_match = re.match(r'([A-Z]+)\s+([+-]?\d+\.?\d*)', spread_text.strip())
        if sp_match:
            entry["spread_team"] = sp_match.group(1)
            entry["spread_value"] = float(sp_match.group(2))

        # Parse moneyline if available
        if i < len(moneylines):
            ml_text = moneylines[i].strip()
            # "UCONN -2500 / CREI +900" or "BAMA -200 / ARK +165"
            ml_match = re.match(
                r'([A-Z]+)\s+([+-]?\d+)\s*/\s*([A-Z]+)\s+([+-]?\d+)',
                ml_text
            )
            if ml_match:
                entry["ml_team1"] = ml_match.group(1)
                entry["ml_value1"] = int(ml_match.group(2))
                entry["ml_team2"] = ml_match.group(3)
                entry["ml_value2"] = int(ml_match.group(4))

        # Parse total if available
        if i < len(totals):
            total_text = totals[i].strip()
            # "O/U 143.5"
            t_match = re.search(r'(\d+\.?\d*)', total_text)
            if t_match:
                entry["total"] = float(t_match.group(1))

        lines.append(entry)

    # Pattern 2: line-value divs (featured game pages)
    # <div class="line-label">Spread</div><div class="line-value">BAMA -4.5</div>
    # <div class="line-label">Total (O/U)</div><div class="line-value">182.5</div>
    lv_spread = re.findall(
        r'<div[^>]*class="line-label"[^>]*>Spread</div>\s*<div[^>]*class="line-value"[^>]*>([^<]+)</div>',
        content, re.IGNORECASE
    )
    lv_total = re.findall(
        r'<div[^>]*class="line-label"[^>]*>Total[^<]*</div>\s*<div[^>]*class="line-value"[^>]*>([^<]+)</div>',
        content, re.IGNORECASE
    )

    for i, spread_text in enumerate(lv_spread):
        entry = {"source": "line-value"}
        sp_match = re.match(r'([A-Z]+)\s+([+-]?\d+\.?\d*)', spread_text.strip())
        if sp_match:
            entry["spread_team"] = sp_match.group(1)
            entry["spread_value"] = float(sp_match.group(2))
        if i < len(lv_total):
            t_match = re.search(r'(\d+\.?\d*)', lv_total[i].strip())
            if t_match:
                entry["total"] = float(t_match.group(1))
        # Only add if not already captured by bet-value pattern
        if entry not in lines and "spread_team" in entry:
            lines.append(entry)

    return lines


def extract_team_records_from_html(content):
    """
    Extract team records mentioned in the HTML.
    Returns list of dicts: {team_name, wins, losses, context}
    """
    records = []

    # Pattern: "Team Name (19-6)" or "#20 Arkansas (19-6)"
    rec_pattern = r'(?:#\d+\s+)?([A-Z][a-zA-Z\s.\'&]+?)\s*\((\d{1,2})-(\d{1,2})(?:,\s*[\d-]+\s*\w+)?\)'
    for match in re.finditer(rec_pattern, content):
        team_name = match.group(1).strip()
        wins = int(match.group(2))
        losses = int(match.group(3))

        # Skip if in style/script/url context
        start = max(0, match.start() - 100)
        context = content[start:match.start()].lower()
        if any(tag in context for tag in ['<style', '<script', 'href=', 'src=']):
            continue

        records.append({
            "team_name": team_name,
            "wins": wins,
            "losses": losses,
            "raw": match.group(0),
        })

    return records


def extract_quotes_from_html(content):
    """
    Detect attributed quotes in the HTML.
    Returns list of quote strings for WARNING flagging.
    """
    quotes = []

    # Strip HTML tags for text analysis
    text = re.sub(r'<[^>]+>', ' ', content)
    text = re.sub(r'\s+', ' ', text)

    # Pattern: "quote text" said/according to Name
    q_patterns = [
        r'["\u201c]([^"\u201d]{20,200})["\u201d]\s*(?:said|says|stated|noted|explained|added)\s+([A-Z][a-z]+ [A-Z][a-z]+)',
        r'([A-Z][a-z]+ [A-Z][a-z]+)\s+(?:said|says|stated|noted)\s*[,:]?\s*["\u201c]([^"\u201d]{20,200})["\u201d]',
    ]

    for pattern in q_patterns:
        for match in re.finditer(pattern, text):
            quotes.append(match.group(0)[:120])

    return quotes


# =============================================================================
# MATCHING & COMPARISON
# =============================================================================

def normalize_team_name(name):
    """Normalize team name for matching."""
    return re.sub(r'[^a-z]', '', name.lower().strip())


def match_game_to_espn(html_team_abbrev, espn_games):
    """
    Try to match an HTML team abbreviation to an ESPN game.
    Returns the matched ESPN game dict or None.
    """
    abbrev = html_team_abbrev.upper().strip()

    # Common abbreviation aliases
    abbrev_aliases = {
        "UCONN": ["CONN", "UCONN"],
        "CREI": ["CREIGHTON", "CREI"],
        "BAMA": ["BAMA", "ALA", "ALB"],
        "ARK": ["ARK", "ARKANSAS"],
        "TENN": ["TENN", "TEN"],
        "OKLA": ["OKLA", "OU"],
        "CLEM": ["CLEM"],
        "WAKE": ["WAKE", "WF"],
        "ARIZ": ["ARIZ", "ARIZONA", "ARI"],
        "BYU": ["BYU"],
        "KU": ["KU", "KAN", "KANSAS"],
        "OKST": ["OKST", "OSU"],
        "SJU": ["SJU", "STJOHNS"],
        "MARQ": ["MARQ"],
        "UVA": ["UVA", "VA"],
        "GT": ["GT", "GATECH"],
        "MIZZ": ["MIZZ", "MIZ", "MIZZOU"],
        "TENN": ["TENN", "TEN"],
        "CLEM": ["CLEM"],
        "VAN": ["VAN", "VANDY"],
        "ILL": ["ILL"],
        "USC": ["USC"],
        "GONZ": ["GONZ", "GONZAGA"],
        "SF": ["SF", "USF"],
        # NBA/NHL/NFL/MLB common abbreviations
        "LAL": ["LAL", "LAKERS"],
        "BOS": ["BOS", "CELTICS"],
        "GSW": ["GSW", "GS", "WARRIORS"],
        "PHI": ["PHI", "SIXERS", "76ERS"],
        "MIL": ["MIL", "BUCKS"],
        "DEN": ["DEN", "NUGGETS"],
        "MIN": ["MIN", "WOLVES", "TIMBERWOLVES"],
        "OKC": ["OKC", "THUNDER"],
        "CLE": ["CLE", "CAVS", "CAVALIERS"],
        "NYK": ["NYK", "KNICKS"],
        "HOU": ["HOU", "ROCKETS"],
        "SAC": ["SAC", "KINGS"],
        "MIA": ["MIA", "HEAT"],
        "ATL": ["ATL", "HAWKS"],
        "DAL": ["DAL", "MAVS", "MAVERICKS"],
        "CHI": ["CHI", "BULLS"],
        "POR": ["POR", "BLAZERS"],
        "SAS": ["SAS", "SA", "SPURS"],
    }

    # Get possible aliases
    search_abbrevs = {abbrev}
    for key, aliases in abbrev_aliases.items():
        if abbrev in aliases or abbrev == key:
            search_abbrevs.update(aliases)
            search_abbrevs.add(key)

    for game in espn_games:
        for side in ["home", "away"]:
            espn_abbrev = game.get(f"{side}_abbrev", "").upper()
            espn_name = normalize_team_name(game.get(f"{side}_name", ""))
            espn_short = normalize_team_name(game.get(f"{side}_short", ""))
            espn_nick = normalize_team_name(game.get(f"{side}_nickname", ""))
            espn_loc = normalize_team_name(game.get(f"{side}_location", ""))

            # Direct abbreviation match
            if espn_abbrev in search_abbrevs:
                return game, side

            # Normalized name match - EXACT only to avoid false positives
            # (e.g. "kansas" is a substring of "arkansas", must not match)
            for sa in search_abbrevs:
                sa_norm = normalize_team_name(sa)
                if sa_norm and len(sa_norm) >= 4:
                    if (sa_norm == espn_short or sa_norm == espn_nick or
                        sa_norm == espn_loc or sa_norm == espn_name):
                        return game, side

    return None, None


def match_record_to_espn(record_entry, espn_games):
    """
    Try to match an HTML record entry to an ESPN game.
    Returns (espn_game, side, espn_record_str) or (None, None, None).
    """
    team_name = normalize_team_name(record_entry["team_name"])

    for game in espn_games:
        for side in ["home", "away"]:
            espn_name = normalize_team_name(game.get(f"{side}_name", ""))
            espn_short = normalize_team_name(game.get(f"{side}_short", ""))
            espn_nick = normalize_team_name(game.get(f"{side}_nickname", ""))
            espn_loc = normalize_team_name(game.get(f"{side}_location", ""))

            if (team_name and len(team_name) >= 4 and
                (team_name == espn_loc or team_name == espn_nick or
                 team_name == espn_short or team_name == espn_name)):
                record_str = game.get(f"{side}_record", "")
                return game, side, record_str

    return None, None, None


def compare_spread(html_value, espn_game):
    """Compare HTML spread to ESPN spread. Returns (status, message)."""
    espn_spread = espn_game.get("spread_value")
    if espn_spread is None:
        return "skip", "No ESPN spread available"

    diff = abs(html_value - espn_spread)
    if diff < 0.1:
        return "ok", f"Spread verified: {html_value}"
    elif diff <= THRESHOLDS["spread_warn"]:
        return "warn", f"Spread close but off: HTML={html_value}, ESPN={espn_spread} (diff {diff})"
    elif diff <= THRESHOLDS["spread_error"]:
        return "warn", f"Spread mismatch: HTML={html_value}, ESPN={espn_spread} (diff {diff})"
    else:
        return "error", f"Spread significantly wrong: HTML={html_value}, ESPN={espn_spread} (off by {diff})"


def compare_total(html_value, espn_game):
    """Compare HTML total to ESPN O/U. Returns (status, message)."""
    espn_total = espn_game.get("overUnder")
    if espn_total is None:
        return "skip", "No ESPN total available"

    espn_total = float(espn_total)
    diff = abs(html_value - espn_total)
    if diff < 0.1:
        return "ok", f"Total verified: {html_value}"
    elif diff <= THRESHOLDS["total_warn"]:
        return "warn", f"Total close but off: HTML={html_value}, ESPN={espn_total} (diff {diff})"
    elif diff <= THRESHOLDS["total_error"]:
        return "warn", f"Total mismatch: HTML={html_value}, ESPN={espn_total} (diff {diff})"
    else:
        return "error", f"Total significantly wrong: HTML={html_value}, ESPN={espn_total} (off by {diff})"


def compare_moneyline(html_ml, espn_game, side):
    """Compare HTML moneyline to ESPN. Returns (status, message)."""
    if side == "home":
        espn_ml = espn_game.get("home_ml")
    else:
        espn_ml = espn_game.get("away_ml")

    if espn_ml is None:
        return "skip", "No ESPN moneyline available"

    diff = abs(html_ml - int(espn_ml))
    if diff == 0:
        return "ok", f"Moneyline verified: {html_ml}"
    elif diff <= THRESHOLDS["moneyline_warn"]:
        return "warn", f"Moneyline close: HTML={html_ml}, ESPN={espn_ml} (diff {diff})"
    elif diff <= THRESHOLDS["moneyline_error"]:
        return "warn", f"Moneyline mismatch: HTML={html_ml}, ESPN={espn_ml} (diff {diff})"
    else:
        return "error", f"Moneyline significantly wrong: HTML={html_ml}, ESPN={espn_ml} (off by {diff})"


def compare_record(html_wins, html_losses, espn_record_str):
    """Compare HTML record to ESPN record. Returns (status, message)."""
    if not espn_record_str:
        return "skip", "No ESPN record available"

    rec_match = re.match(r'(\d+)-(\d+)', espn_record_str)
    if not rec_match:
        return "skip", f"Cannot parse ESPN record: {espn_record_str}"

    espn_wins = int(rec_match.group(1))
    espn_losses = int(rec_match.group(2))

    win_diff = abs(html_wins - espn_wins)
    loss_diff = abs(html_losses - espn_losses)

    if win_diff == 0 and loss_diff == 0:
        return "ok", f"Record verified: {html_wins}-{html_losses}"
    elif win_diff <= THRESHOLDS["record_wins_warn"] and loss_diff <= THRESHOLDS["record_wins_warn"]:
        return "warn", f"Record close: HTML={html_wins}-{html_losses}, ESPN={espn_wins}-{espn_losses}"
    else:
        return "error", f"Record wrong: HTML={html_wins}-{html_losses}, ESPN={espn_wins}-{espn_losses}"


# =============================================================================
# EXISTING CHECKS (from original inline validator)
# =============================================================================

def check_player_teams(content, filename):
    """Check for incorrect player-team associations."""
    issues = []
    content_lower = content.lower()

    for player, wrong_team, error_msg in WRONG_ASSOCIATIONS:
        for match in re.finditer(rf'\b{re.escape(player)}\b', content_lower):
            pos = match.start()
            sent_start = max(
                content_lower.rfind('.', 0, pos) + 1,
                content_lower.rfind('\n', 0, pos) + 1,
                0
            )
            sent_end = min(
                content_lower.find('.', pos) if content_lower.find('.', pos) != -1 else len(content_lower),
                content_lower.find('\n', pos) if content_lower.find('\n', pos) != -1 else len(content_lower)
            )
            sentence = content_lower[sent_start:sent_end]
            if re.search(rf'\b{re.escape(wrong_team)}\b', sentence):
                if not any(tw in sentence for tw in TRADE_CONTEXT_WORDS):
                    issues.append(("error", f"ROSTER ERROR: {error_msg}"))

    return issues


def check_injuries(content, filename):
    """Check for incorrect injury information."""
    issues = []
    content_lower = content.lower()

    for player, injury_info in INJURY_FACTS.items():
        if player in content_lower:
            for match in re.finditer(rf'\b{re.escape(player)}\b', content_lower):
                pos = match.start()
                context = content_lower[max(0, pos - 100):pos + 100]
                if injury_info["wrong"] in context and injury_info["correct"] not in context:
                    issues.append(("error", f"WRONG INJURY: {injury_info['message']}"))

    return issues


def check_placeholders(content, filename):
    """Check for placeholder content."""
    issues = []

    for pattern in PLACEHOLDER_PATTERNS:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            ctx = content[max(0, match.start() - 100):match.start()]
            if '<style' not in ctx.lower() and '<script' not in ctx.lower():
                issues.append(("error", f"PLACEHOLDER: Found '{match.group()}' - incomplete content"))

    return issues


def check_quotes(content, filename):
    """Flag any attributed quotes for manual verification."""
    quotes = extract_quotes_from_html(content)
    issues = []
    for q in quotes:
        issues.append(("warn", f"QUOTE DETECTED (unverifiable): {q}"))
    return issues


# =============================================================================
# FILE VALIDATION
# =============================================================================

def validate_file(filepath):
    """
    Run all validation checks on a single HTML file.
    Returns (errors, warnings, info_messages).
    """
    errors = []
    warnings = []
    info = []

    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except Exception as e:
        errors.append(f"Cannot read file: {e}")
        return errors, warnings, info

    filename = os.path.basename(filepath)

    # Skip non-content files
    if any(skip in filename for skip in ['calendar', 'script', 'style', 'template',
                                          'mobile-optimize', 'sitemap']):
        info.append(f"Skipped non-content file: {filename}")
        return errors, warnings, info

    print(f"\n[{filename}]")

    # --- Existing checks ---
    for severity, msg in check_player_teams(content, filename):
        if severity == "error":
            errors.append(msg)
        else:
            warnings.append(msg)

    for severity, msg in check_injuries(content, filename):
        if severity == "error":
            errors.append(msg)
        else:
            warnings.append(msg)

    for severity, msg in check_placeholders(content, filename):
        if severity == "error":
            errors.append(msg)
        else:
            warnings.append(msg)

    for severity, msg in check_quotes(content, filename):
        warnings.append(msg)

    # --- Live ESPN verification ---
    sport = detect_sport_from_file(filepath, content)
    date_str = extract_date_from_file(filepath, content)

    if not sport:
        info.append("Could not detect sport - skipping live data verification")
    elif not date_str:
        info.append("Could not detect date - skipping live data verification")
    elif not HAS_REQUESTS:
        info.append("requests library not installed - skipping live data verification")
    else:
        print(f"  Sport: {sport.upper()} | Date: {date_str[:4]}-{date_str[4:6]}-{date_str[6:]}")

        espn_games = fetch_espn_scoreboard(sport, date_str)

        if espn_games is None:
            warnings.append("ESPN API unavailable - skipping live data verification")
        elif len(espn_games) == 0:
            info.append(f"ESPN returned 0 games for {sport.upper()} on {date_str}")
        else:
            print(f"  ESPN data: {len(espn_games)} games found for this date")

            # Compare betting lines
            html_lines = extract_betting_lines_from_html(content)
            matched_count = 0
            unmatched = []

            for line_entry in html_lines:
                spread_team = line_entry.get("spread_team", "")
                if not spread_team:
                    continue

                matched_game, matched_side = match_game_to_espn(spread_team, espn_games)

                if matched_game:
                    matched_count += 1
                    home_name = matched_game.get("home_short", matched_game.get("home_abbrev", ""))
                    away_name = matched_game.get("away_short", matched_game.get("away_abbrev", ""))
                    print(f"  Matched: {away_name} at {home_name}")

                    # Compare spread
                    if "spread_value" in line_entry:
                        status, msg = compare_spread(line_entry["spread_value"], matched_game)
                        if status == "ok":
                            print(f"    Spread: HTML={line_entry['spread_value']}, "
                                  f"ESPN={matched_game.get('spread_value', 'N/A')} {OK}")
                        elif status == "warn":
                            warnings.append(f"[{spread_team}] {msg}")
                            print(f"    Spread: {msg} {WARN}")
                        elif status == "error":
                            errors.append(f"[{spread_team}] {msg}")
                            print(f"    Spread: {msg} {FAIL}")

                    # Compare total
                    if "total" in line_entry:
                        status, msg = compare_total(line_entry["total"], matched_game)
                        if status == "ok":
                            print(f"    O/U: HTML={line_entry['total']}, "
                                  f"ESPN={matched_game.get('overUnder', 'N/A')} {OK}")
                        elif status == "warn":
                            warnings.append(f"[{spread_team}] {msg}")
                            print(f"    O/U: {msg} {WARN}")
                        elif status == "error":
                            errors.append(f"[{spread_team}] {msg}")
                            print(f"    O/U: {msg} {FAIL}")

                    # Compare moneylines
                    if "ml_value1" in line_entry:
                        team1 = line_entry["ml_team1"]
                        game1, side1 = match_game_to_espn(team1, espn_games)
                        if game1 and side1:
                            status, msg = compare_moneyline(line_entry["ml_value1"], game1, side1)
                            if status == "error":
                                errors.append(f"[{team1}] {msg}")
                                print(f"    ML {team1}: {msg} {FAIL}")
                            elif status == "warn":
                                warnings.append(f"[{team1}] {msg}")
                            elif status == "ok":
                                print(f"    ML {team1}: {line_entry['ml_value1']} {OK}")

                    if "ml_value2" in line_entry:
                        team2 = line_entry["ml_team2"]
                        game2, side2 = match_game_to_espn(team2, espn_games)
                        if game2 and side2:
                            status, msg = compare_moneyline(line_entry["ml_value2"], game2, side2)
                            if status == "error":
                                errors.append(f"[{team2}] {msg}")
                                print(f"    ML {team2}: {msg} {FAIL}")
                            elif status == "warn":
                                warnings.append(f"[{team2}] {msg}")
                            elif status == "ok":
                                print(f"    ML {team2}: {line_entry['ml_value2']} {OK}")

                else:
                    unmatched.append(spread_team)

            if html_lines:
                print(f"  {matched_count} of {len(html_lines)} betting lines matched to ESPN data")
            if unmatched:
                info.append(f"Unmatched teams (not in ESPN data): {', '.join(unmatched)}")

            # Compare team records
            html_records = extract_team_records_from_html(content)
            for rec in html_records:
                game, side, espn_rec = match_record_to_espn(rec, espn_games)
                if game and espn_rec:
                    status, msg = compare_record(rec["wins"], rec["losses"], espn_rec)
                    team_display = rec["team_name"]
                    if status == "ok":
                        print(f"    {team_display} record: {rec['wins']}-{rec['losses']} {OK}")
                    elif status == "warn":
                        warnings.append(f"[{team_display}] {msg}")
                        print(f"    {team_display} record: {msg} {WARN}")
                    elif status == "error":
                        errors.append(f"[{team_display}] {msg}")
                        print(f"    {team_display} record: {msg} {FAIL}")

    return errors, warnings, info


# =============================================================================
# MAIN
# =============================================================================

def main():
    # Determine files to validate
    files = []

    if len(sys.argv) > 1:
        # Files passed as arguments
        files = [f for f in sys.argv[1:] if f.endswith('.html')]
    elif os.path.exists('changed_files.txt'):
        # Read from changed_files.txt (GitHub Actions workflow)
        with open('changed_files.txt') as f:
            files = [line.strip() for line in f if line.strip()]
    else:
        print("[OK] No files to validate")
        sys.exit(0)

    if not files:
        print("[OK] No HTML files to validate")
        sys.exit(0)

    print(f"Validating {len(files)} changed file(s)...")

    if not HAS_REQUESTS:
        print("[WARN] 'requests' library not installed - live ESPN verification disabled")
        print("       Install with: pip install requests")

    total_errors = []
    total_warnings = []

    for filepath in files:
        if not os.path.exists(filepath):
            print(f"\n[{filepath}] File not found - skipping")
            continue

        file_errors, file_warnings, file_info = validate_file(filepath)

        for msg in file_info:
            print(f"  [INFO] {msg}")

        total_errors.extend([(filepath, e) for e in file_errors])
        total_warnings.extend([(filepath, w) for w in file_warnings])

    # --- Summary ---
    print("\n" + "=" * 70)

    error_count = len(total_errors)
    warn_count = len(total_warnings)

    # Deduplicate
    total_errors = list(set(total_errors))
    total_warnings = list(set(total_warnings))
    error_count = len(total_errors)
    warn_count = len(total_warnings)

    if error_count > 0:
        print("  ERRORS FOUND")
        print("  " + "-" * 66)
        for filepath, msg in total_errors:
            fname = os.path.basename(filepath)
            print(f"  [ERROR] [{fname}] {msg}")
        print()

    if warn_count > 0:
        print("  WARNINGS")
        print("  " + "-" * 66)
        for filepath, msg in total_warnings:
            fname = os.path.basename(filepath)
            print(f"  [WARN]  [{fname}] {msg}")
        print()

    print(f"RESULTS: {error_count} error(s), {warn_count} warning(s)")
    print("=" * 70)

    if error_count > 0:
        print("\n[FAIL] Fix errors before pushing.")
        sys.exit(1)
    elif warn_count > 0:
        print("\n[OK] Passed with warnings - review recommended.")
        sys.exit(0)
    else:
        print(f"\n[OK] All {len(files)} file(s) validated - no issues found.")
        sys.exit(0)


if __name__ == "__main__":
    main()
