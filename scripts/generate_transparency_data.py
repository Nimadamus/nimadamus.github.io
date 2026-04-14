#!/usr/bin/env python3
"""
Generate homepage transparency widget data by reading the RECORDS PAGES directly.

The records pages are the source of truth. They contain:
  1. Embedded HTML tables with historical picks
  2. Some also fetch from Google Sheets for additional data
  3. All also fetch from the Pick Tracker for recent picks

This script mirrors that exact logic:
  1. Parse each sport's records page HTML table
  2. For sports that also use Google Sheets (NBA, MLB, NCAAB, Soccer), fetch those too
  3. Fetch the Pick Tracker for recent picks
  4. Merge all three, deduplicating by date+pick
  5. Write transparency-widget-data.js

Usage:
    python scripts/generate_transparency_data.py
"""

import csv
import io
import json
import os
import re
import urllib.request
from datetime import datetime

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Records pages with embedded HTML tables
HTML_RECORDS_PAGES = {
    "NHL": "nhl-records.html",
    "NFL": "nfl-records.html",
    "NCAAF": "ncaaf-records.html",
    "NCAAB": "ncaab-records.html",
    "MLB": "mlb-records.html",
    "NBA": "nba-records.html",
    "Soccer": "soccer-records.html",
}

# Google Sheets URLs (extracted from each records page's JS)
SHEET_URLS = {
    "NBA": "https://docs.google.com/spreadsheets/d/e/2PACX-1vSBoPl-dhj7ZAVpRIafqrFBf10r6sg3jpEKxmuymugAckdoMp-czkj1hscpDnV42GGJsIvNx5EniLVz/pub?output=csv",
    "MLB": "https://docs.google.com/spreadsheets/d/e/2PACX-1vQE9RjSNABgl0SxSA1ghp9soUs4gq7teoncN5GLmG5faXmH-sDwXgg0mrk0iQwmSEYExtx6xwFMflXv/pub?output=csv",
    "NCAAB": "https://docs.google.com/spreadsheets/d/e/2PACX-1vQrFb66HE90gCwliIBQlZ5cNBApJWtGuUV1WbS4pd12SMrs_3qlmSFZCLJ9vBmfgZKcaaGyg4G15J3Y/pub?output=csv",
    "Soccer": "https://docs.google.com/spreadsheets/d/e/2PACX-1vQy0EQskvixsVQb1zzYtCKDa4F1Wl6WU5QuAFMit32vms-c4DxlhLik-k7U_EhuYntQrpw4BI6r0rns/pub?output=csv",
}

# How each records page actually works:
# "html_then_tracker" = HTML table is primary, Pick Tracker supplements (NHL, NFL, NCAAF)
# "sheet_then_tracker" = Google Sheet is primary, Pick Tracker supplements (NBA, NCAAB, MLB)
# "sheet_only" = Google Sheet only, no tracker (Soccer)
SPORT_DATA_MODE = {
    "NHL": "html_then_tracker",
    "NFL": "html_then_tracker",
    "NCAAF": "html_then_tracker",
    "NBA": "sheet_then_tracker",
    "NCAAB": "sheet_then_tracker",
    "MLB": "sheet_then_tracker",
    "Soccer": "sheet_only",
}

PICK_TRACKER_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1izhxwiiazn99SRqcK8QpUE4pfvDRIFpgSyw5ZlMsvmY/export?format=csv&gid=0"
)

ALL_SPORTS = ["NHL", "MLB", "NFL", "NBA", "NCAAF", "NCAAB", "Soccer"]

DISPLAY_NAMES = {
    "NHL": "NHL",
    "MLB": "MLB",
    "NFL": "NFL",
    "NBA": "NBA",
    "NCAAF": "College Football",
    "NCAAB": "College Basketball",
    "Soccer": "Soccer",
}

RECORDS_LINKS = {
    "NHL": "nhl-records.html",
    "MLB": "mlb-records.html",
    "NFL": "nfl-records.html",
    "NBA": "nba-records.html",
    "NCAAF": "ncaaf-records.html",
    "NCAAB": "ncaab-records.html",
    "Soccer": "soccer-records.html",
}

TRACKER_LEAGUE_MAP = {
    "nhl": "NHL",
    "hockey": "NHL",
    "nfl": "NFL",
    "football": "NFL",
    "nba": "NBA",
    "mlb": "MLB",
    "baseball": "MLB",
    "ncaaf": "NCAAF",
    "college football": "NCAAF",
    "cfb": "NCAAF",
    "ncaa football": "NCAAF",
    "ncaab": "NCAAB",
    "college basketball": "NCAAB",
    "cbb": "NCAAB",
    "ncaa basketball": "NCAAB",
    "soccer": "Soccer",
    "mls": "Soccer",
    "epl": "Soccer",
    "la liga": "Soccer",
    "bundesliga": "Soccer",
    "serie a": "Soccer",
    "ligue 1": "Soccer",
}

SPORT_DEFAULT_STAKES = {
    "NFL": "2", "NBA": "1", "NHL": "3", "MLB": "1",
    "NCAAF": "3", "NCAAB": "3", "Soccer": "1",
}

NBA_KEYWORDS = {
    "lakers", "celtics", "warriors", "nets", "knicks", "heat", "bulls",
    "mavericks", "mavs", "spurs", "rockets", "suns", "bucks", "sixers",
    "76ers", "raptors", "thunder", "okc", "jazz", "nuggets", "blazers",
    "timberwolves", "wolves", "pelicans", "grizzlies", "kings", "clippers",
    "hawks", "hornets", "magic", "pistons", "pacers", "cavaliers", "cavs",
    "wizards",
}

NCAAB_KEYWORDS = {
    "duke", "uconn", "gonzaga", "kentucky", "kansas", "unc", "north carolina",
    "villanova", "purdue", "auburn", "tennessee", "alabama", "iowa state",
    "marquette", "baylor", "creighton", "michigan state", "florida",
    "arizona", "memphis", "houston", "texas tech", "oregon", "wisconsin",
    "illinois", "indiana", "ncaab", "cbb", "ncaa",
}


# ---- Utility functions ----

def safe_float(value, default=0.0):
    if value is None:
        return default
    text = str(value).strip().replace(",", "").replace("$", "")
    if not text:
        return default
    if text.startswith("+"):
        text = text[1:]
    try:
        return float(text)
    except (TypeError, ValueError):
        return default


def normalize_result(value):
    text = (value or "").strip().upper()
    if text.startswith("W"):
        return "W"
    if text.startswith("L"):
        return "L"
    if text.startswith("P"):
        return "P"
    return ""


def normalize_date(date_str):
    if not date_str:
        return ""
    raw = str(date_str).strip()
    for fmt in ("%m/%d/%Y", "%m/%d/%y", "%m-%d-%Y", "%Y-%m-%d", "%Y/%m/%d"):
        try:
            dt = datetime.strptime(raw, fmt)
            return f"{dt.month}/{dt.day}/{dt.year}"
        except ValueError:
            continue
    parts = raw.replace("-", "/").split("/")
    if len(parts) == 3:
        try:
            month = int(parts[0])
            day = int(parts[1])
            year_text = parts[2].strip()
            if year_text.startswith("0") and len(year_text) > 1:
                year_text = year_text.lstrip("0")
            if len(year_text) == 3 and year_text.startswith("20"):
                year_text = year_text[:2] + "2" + year_text[2:]
            year = int(year_text)
            if 2030 < year < 3000:
                year = int(f"20{str(year)[-2:]}")
            if 2020 <= year <= 2030:
                return f"{month}/{day}/{year}"
        except ValueError:
            pass
    return raw


def date_sort_key(date_str):
    normalized = normalize_date(date_str)
    for fmt in ("%m/%d/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(normalized, fmt)
        except ValueError:
            continue
    return datetime.min


def make_pick_key(date_str, pick_text):
    return f"{normalize_date(date_str)}|{(pick_text or '').strip().lower()}"


def is_cross_sport_parlay(pick_text):
    """Detect cross-sport parlays (matching the records page JS logic).
    These are excluded from single-sport records pages."""
    text = (pick_text or "").lower()
    if "teaser" in text:
        return False
    if "parlay" not in text:
        return False
    sports = set()
    if "(nfl)" in text:
        sports.add("NFL")
    if "(cfb)" in text or "(ncaaf)" in text:
        sports.add("CFB")
    if "(nba)" in text:
        sports.add("NBA")
    if "(nhl)" in text:
        sports.add("NHL")
    if "(mlb)" in text:
        sports.add("MLB")
    if "(ncaab)" in text or "(cbb)" in text:
        sports.add("NCAAB")
    if "(soccer)" in text or "(mls)" in text:
        sports.add("Soccer")
    return len(sports) > 1


def calculate_unit_result(stake_str, odds_str, result):
    stake = safe_float(stake_str)
    odds = safe_float(odds_str, default=-110.0)
    r = normalize_result(result)
    if not r:
        return 0.0
    if r == "W":
        return stake if odds < 0 else stake * (odds / 100)
    if r == "L":
        return -stake * (abs(odds) / 100) if odds < 0 else -stake
    return 0.0


def latest_date_from_keys(picks_map):
    if not picks_map:
        return ""
    latest_key = max(picks_map.keys(), key=lambda k: date_sort_key(k.split("|", 1)[0]))
    return latest_key.split("|", 1)[0]


def build_stats(picks_map):
    """Calculate stats matching how the records pages do it:
    - Filter out cross-sport parlays
    - Classify W/L/P by UNITS VALUE (positive=W, negative=L, zero=P)
    - Calculate average odds across all picks"""
    wins = losses = pushes = 0
    total_units = 0.0
    odds_values = []
    for key, entry in picks_map.items():
        # Support both (result, units) and (result, units, odds) tuples
        if len(entry) == 3:
            result, units, odds = entry
        else:
            result, units = entry
            odds = None
        # Extract pick text from key (format: "date|pick_text")
        pick_text = key.split("|", 1)[1] if "|" in key else ""
        if is_cross_sport_parlay(pick_text):
            continue
        if units > 0:
            wins += 1
        elif units < 0:
            losses += 1
        else:
            pushes += 1
        total_units += units
        if odds is not None and odds != 0:
            odds_values.append(odds)
    total_picks = wins + losses + pushes
    win_pct = round((wins / (wins + losses) * 100) if (wins + losses) else 0.0, 1)
    # Convert each American odd to implied probability, average, convert back
    if odds_values:
        probs = []
        for o in odds_values:
            if o < 0:
                probs.append(abs(o) / (abs(o) + 100))
            else:
                probs.append(100 / (o + 100))
        avg_prob = sum(probs) / len(probs)
        if avg_prob >= 0.5:
            avg_odds = round(-(avg_prob / (1 - avg_prob)) * 100)
        else:
            avg_odds = round(((1 - avg_prob) / avg_prob) * 100)
    else:
        avg_odds = -110
    return {
        "wins": wins,
        "losses": losses,
        "pushes": pushes,
        "totalPicks": total_picks,
        "totalUnits": round(total_units, 2),
        "winPct": win_pct,
        "avgOdds": avg_odds,
        "lastDate": latest_date_from_keys(picks_map),
    }


# ---- Data source parsers ----

def parse_html_table(filepath):
    """Parse the embedded HTML table in a records page. Returns a pick map."""
    if not os.path.exists(filepath):
        return {}

    with open(filepath, "r", encoding="utf-8") as f:
        html = f.read()

    picks = {}
    # Match rows like: <tr><td>4/5/2026</td><td>Pick text</td><td>-110</td><td class="result-W">W</td><td class="win">+3.00</td></tr>
    row_pattern = re.compile(
        r'<tr>\s*<td[^>]*>([^<]*)</td>'   # date
        r'\s*<td[^>]*>([^<]*)</td>'        # pick
        r'\s*<td[^>]*>([^<]*)</td>'        # line/odds
        r'\s*<td[^>]*[^>]*>([^<]*)</td>'   # result (W/L/P)
        r'\s*<td[^>]*[^>]*>([^<]*)</td>'   # units
        r'\s*</tr>',
        re.IGNORECASE
    )

    for match in row_pattern.finditer(html):
        date_str = match.group(1).strip()
        pick_text = match.group(2).strip()
        odds_str = match.group(3).strip()
        result_text = match.group(4).strip()
        units_str = match.group(5).strip()

        result = normalize_result(result_text)
        if not result:
            # Derive from units
            u = safe_float(units_str)
            if u > 0:
                result = "W"
            elif u < 0:
                result = "L"
            elif pick_text:
                result = "P"
            else:
                continue

        if not date_str or not pick_text:
            continue

        units = safe_float(units_str)
        odds = safe_float(odds_str, default=0.0)
        key = make_pick_key(date_str, pick_text)
        picks[key] = (result, units, odds)

    return picks


def fetch_csv_rows(url):
    """Fetch CSV from a URL and return list of dicts."""
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (BetLegend Transparency Widget)"},
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        csv_text = response.read().decode("utf-8-sig")
    return list(csv.DictReader(io.StringIO(csv_text)))


def sheet_rows_to_pick_map(rows):
    """Parse Google Sheet CSV rows into a pick map."""
    picks = {}
    for row in rows:
        result = normalize_result(row.get("Result") or row.get("result"))
        if not result:
            # Derive result from Units/ProfitLoss column if Result is missing
            units_val = safe_float(
                row.get("Units") or row.get("ProfitLoss")
                or row.get("Profit/Loss") or row.get("P/L")
                or row.get("UNIT_RESULT")
            )
            if units_val > 0:
                result = "W"
            elif units_val < 0:
                result = "L"
            else:
                pick_text = (row.get("Pick") or row.get("Picks") or "").strip()
                if pick_text:
                    result = "P"
                else:
                    continue
        if not result:
            continue

        date_str = row.get("Date", "")
        pick_text = row.get("Pick") or row.get("Picks") or row.get("pick") or ""
        if not date_str or not pick_text:
            continue

        units = safe_float(
            row.get("Units") or row.get("ProfitLoss")
            or row.get("Profit/Loss") or row.get("P/L")
            or row.get("UNIT_RESULT")
        )
        odds = safe_float(
            row.get("Line") or row.get("Odds") or row.get("odds") or "0"
        )
        key = make_pick_key(date_str, pick_text)
        picks[key] = (result, units, odds)
    return picks


def detect_basketball_sport(row):
    pick_text = (row.get("Pick") or row.get("Picks") or "").lower()
    if any(kw in pick_text for kw in NBA_KEYWORDS):
        return "NBA"
    if any(kw in pick_text for kw in NCAAB_KEYWORDS):
        return "NCAAB"
    return None


def detect_tracker_sport(row):
    league = (row.get("League", "") or "").strip().lower()
    sport = (row.get("Sport", "") or "").strip().lower()

    if league == "cross-sport":
        return None
    if league in TRACKER_LEAGUE_MAP:
        return TRACKER_LEAGUE_MAP[league]
    if sport == "basketball" or league == "basketball" or league == "basetball":
        return detect_basketball_sport(row)
    if sport == "football":
        return "NFL"
    if sport == "hockey":
        return "NHL"
    if sport == "baseball":
        return "MLB"
    if sport == "soccer":
        return "Soccer"
    return None


def fetch_tracker_pick_maps():
    """Fetch Pick Tracker and return per-sport pick maps."""
    sport_maps = {sport: {} for sport in ALL_SPORTS}
    skipped = 0

    try:
        rows = fetch_csv_rows(PICK_TRACKER_URL)
    except Exception as e:
        print(f"  WARNING: Could not fetch Pick Tracker: {e}")
        return sport_maps, 0

    for row in rows:
        sport = detect_tracker_sport(row)
        if not sport:
            skipped += 1
            continue

        result = normalize_result(row.get("Result"))
        if not result:
            continue

        date_str = row.get("Date", "")
        pick_text = row.get("Pick") or row.get("Picks") or ""
        if not date_str or not pick_text:
            continue

        odds_str = row.get("Line") or row.get("Odds") or "-110"
        stake = row.get("Units") or SPORT_DEFAULT_STAKES.get(sport, "1")
        units = calculate_unit_result(stake, odds_str, result)
        odds_val = safe_float(odds_str, default=0.0)
        key = make_pick_key(date_str, pick_text)
        sport_maps[sport][key] = (result, units, odds_val)

    return sport_maps, skipped


# ---- Main ----

def main():
    # Each sport's records page uses a specific data flow. We mirror it exactly.
    #
    # "html_then_tracker" (NHL, NFL, NCAAF):
    #   HTML table is primary, Pick Tracker supplements with new picks
    #
    # "sheet_then_tracker" (NBA, NCAAB, MLB):
    #   Google Sheet is primary, Pick Tracker supplements with new picks
    #   (HTML table is just a static snapshot, NOT used for calculations)
    #
    # "sheet_only" (Soccer):
    #   Google Sheet only, no Pick Tracker

    # STEP 1: Parse HTML tables (for html_then_tracker sports)
    print("Step 1: Parsing HTML tables (NHL, NFL, NCAAF)...")
    html_picks = {}
    for sport in ALL_SPORTS:
        if SPORT_DATA_MODE[sport] == "html_then_tracker":
            filepath = os.path.join(REPO_ROOT, HTML_RECORDS_PAGES[sport])
            pick_map = parse_html_table(filepath)
            html_picks[sport] = pick_map
            stats = build_stats(pick_map)
            print(
                f"  {sport:8s}: {stats['wins']}-{stats['losses']}-{stats['pushes']} | "
                f"Units: {stats['totalUnits']:+.2f} | {stats['totalPicks']} picks"
            )

    # STEP 2: Fetch Google Sheets (for sheet-based sports)
    print("\nStep 2: Fetching Google Sheets (NBA, NCAAB, MLB, Soccer)...")
    sheet_picks = {}
    for sport, url in SHEET_URLS.items():
        try:
            rows = fetch_csv_rows(url)
            pick_map = sheet_rows_to_pick_map(rows)
            sheet_picks[sport] = pick_map
            stats = build_stats(pick_map)
            print(
                f"  {sport:8s}: {stats['wins']}-{stats['losses']}-{stats['pushes']} | "
                f"Units: {stats['totalUnits']:+.2f} | {stats['totalPicks']} picks"
            )
        except Exception as e:
            print(f"  {sport:8s}: ERROR fetching sheet - {e}")
            sheet_picks[sport] = {}

    # STEP 3: Fetch Pick Tracker
    print("\nStep 3: Fetching Pick Tracker...")
    tracker_picks, skipped = fetch_tracker_pick_maps()
    if skipped:
        print(f"  Skipped {skipped} ambiguous tracker rows")
    for sport in ALL_SPORTS:
        count = len(tracker_picks.get(sport, {}))
        if count:
            print(f"  {sport:8s}: {count} picks from Tracker")

    # STEP 4: Merge per sport using the CORRECT data flow
    print("\nStep 4: Merging (matching each records page's logic)...")
    combined_data = {}
    for sport in ALL_SPORTS:
        mode = SPORT_DATA_MODE[sport]
        merged = {}

        if mode == "html_then_tracker":
            # Start with HTML table, add tracker picks not already present
            merged.update(html_picks.get(sport, {}))
            base_count = len(merged)
            for key, value in tracker_picks.get(sport, {}).items():
                if key not in merged:
                    merged[key] = value
            added = len(merged) - base_count
            source_desc = f"HTML:{base_count} +Tracker:{added}"

        elif mode == "sheet_then_tracker":
            # Start with Google Sheet, add tracker picks not already present
            merged.update(sheet_picks.get(sport, {}))
            base_count = len(merged)
            for key, value in tracker_picks.get(sport, {}).items():
                if key not in merged:
                    merged[key] = value
            added = len(merged) - base_count
            source_desc = f"Sheet:{base_count} +Tracker:{added}"

        elif mode == "sheet_only":
            # Google Sheet only
            merged.update(sheet_picks.get(sport, {}))
            source_desc = f"Sheet:{len(merged)}"

        stats = build_stats(merged)
        combined_data[sport] = {
            "displayName": DISPLAY_NAMES[sport],
            "recordsLink": RECORDS_LINKS[sport],
            **stats,
        }
        print(
            f"  {sport:8s}: {stats['wins']}-{stats['losses']}-{stats['pushes']} | "
            f"Units: {stats['totalUnits']:+.2f} | {stats['totalPicks']} total "
            f"({source_desc})"
        )

    # STEP 5: Write JS file
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    js_content = (
        f"// Auto-generated by scripts/generate_transparency_data.py\n"
        f"// Last updated: {now}\n"
        f"// Source: records page HTML tables + Google Sheets + Pick Tracker\n"
        f"// DO NOT EDIT MANUALLY - run the script to regenerate\n\n"
        f"const TRANSPARENCY_DATA = {{\n"
        f"  lastUpdated: \"{now}\",\n"
        f"  sports: {json.dumps(combined_data, indent=4)}\n"
        f"}};\n"
    )

    output_path = os.path.join(REPO_ROOT, "transparency-widget-data.js")
    with open(output_path, "w", encoding="utf-8") as handle:
        handle.write(js_content)

    print(f"\nWrote {output_path}")


if __name__ == "__main__":
    main()
