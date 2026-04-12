#!/usr/bin/env python3
"""
Generate transparency widget data from the records pages.

Reads the HTML tables in each sport's records page, calculates
total units, win percentage, and total picks, then writes
transparency-widget-data.js for the homepage widget to consume.

IMPORTANT: This script filters to the CURRENT YEAR (matching the
records pages' default filterByYear view) so the homepage widget
and records pages always show the same numbers.

For MLB: fetches data from the Google Sheets CSV endpoint since the
MLB records page loads data dynamically via JavaScript.

Usage:
    python scripts/generate_transparency_data.py
"""

import os
import re
import csv
import json
import io
import urllib.request
from datetime import datetime

# Year filter: must match the records pages' default filterByYear() call
# and the WIDGET_YEAR_FILTER in index.html. Change when the year rolls over.
YEAR_FILTER = "2026"

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Records pages with embedded HTML tables (sport key -> filename)
HTML_RECORDS_PAGES = {
    "NHL": "nhl-records.html",
    "NFL": "nfl-records.html",
    "NCAAF": "ncaaf-records.html",
    "NCAAB": "ncaab-records.html",
    "MLB": "mlb-records.html",
}

# MLB uses Google Sheets - CSV endpoint
MLB_SHEETS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQE9RjSNABgl0SxSA1ghp9soUs4gq7teoncN5GLmG5faXmH-sDwXgg0mrk0iQwmSEYExtx6xwFMflXv/pub?output=csv"

# Pick Tracker Google Sheet (supplements HTML tables with recent picks)
PICK_TRACKER_URL = "https://docs.google.com/spreadsheets/d/1izhxwiiazn99SRqcK8QpUE4pfvDRIFpgSyw5ZlMsvmY/export?format=csv&gid=0"

# Map Pick Tracker League values to our sport keys
LEAGUE_MAP = {
    "nhl": "NHL",
    "hockey": "NHL",
    "nfl": "NFL",
    "ncaaf": "NCAAF",
    "college football": "NCAAF",
    "cfb": "NCAAF",
    "ncaab": "NCAAB",
    "college basketball": "NCAAB",
    "cbb": "NCAAB",
    "mlb": "MLB",
    "baseball": "MLB",
    "football": "NFL",
    "basetball": "NCAAB",
}

# Display names for the widget
DISPLAY_NAMES = {
    "NHL": "NHL",
    "MLB": "MLB",
    "NFL": "NFL",
    "NCAAF": "College Football",
    "NCAAB": "College Basketball",
}

# Links to full records pages
RECORDS_LINKS = {
    "NHL": "nhl-records.html",
    "MLB": "mlb-records.html",
    "NFL": "nfl-records.html",
    "NCAAF": "ncaaf-records.html",
    "NCAAB": "ncaab-records.html",
}


def normalize_date(date_str):
    """Normalize date to M/D/YYYY format. Matches JS normalizeDate() in records pages."""
    if not date_str:
        return ""
    date_str = date_str.strip()
    parts = re.split(r"[-/]", date_str)
    if len(parts) == 3:
        try:
            m = int(parts[0])
            d = int(parts[1])
            y_str = parts[2].strip()
            # Strip leading zeros from year: 0206 -> 206
            if re.match(r"^0\d+$", y_str):
                y_str = y_str.lstrip("0")
            y = int(y_str)
            # Fix 3-digit year: 206 -> 2026
            if re.match(r"^\d{3}$", y_str) and y_str.startswith("20"):
                y = int(y_str[:2] + "2" + y_str[2:])
            # Fix 4-digit year beyond 2030: 2926 -> 2026
            if 2030 < y < 3000:
                y = int("20" + str(y)[-2:])
            if 2020 <= y <= 2030:
                return f"{m}/{d}/{y}"
        except (ValueError, IndexError):
            pass
    return date_str


def extract_year(date_str):
    """Extract the 4-digit year from a date string like '4/5/2026' or '12-31-2025'.
    Returns the year as a string, or None if not parseable."""
    if not date_str:
        return None
    normalized = normalize_date(date_str)
    parts = re.split(r"[-/]", normalized)
    if len(parts) == 3:
        try:
            y = int(parts[2])
            if 2020 <= y <= 2030:
                return str(y)
        except ValueError:
            pass
    m = re.search(r"20\d{2}", date_str)
    return m.group(0) if m else None


def calculate_unit_result(stake_str, odds_str, result):
    """Calculate unit profit/loss using the correct formula from CLAUDE.md."""
    try:
        stake = float(stake_str) if stake_str else 3.0
        odds = float(odds_str) if odds_str else -110.0
    except (ValueError, TypeError):
        return 0.0
    r = (result or "").upper().strip()
    if r.startswith("W"):
        return stake if odds < 0 else stake * (odds / 100)
    elif r.startswith("L"):
        return -stake * (abs(odds) / 100) if odds < 0 else -stake
    return 0.0


def fetch_pick_tracker_picks():
    """Fetch graded picks from the Pick Tracker Google Sheet.

    Returns a dict keyed by sport: { "NHL": { "date|pick": (result, units), ... }, ... }
    """
    try:
        req = urllib.request.Request(PICK_TRACKER_URL, headers={
            "User-Agent": "Mozilla/5.0 (BetLegend Transparency Widget)"
        })
        with urllib.request.urlopen(req, timeout=15) as response:
            csv_text = response.read().decode("utf-8")
    except Exception as e:
        print(f"WARNING: Could not fetch Pick Tracker: {e}")
        return {}

    reader = csv.DictReader(io.StringIO(csv_text))
    sport_picks = {}  # sport_key -> { "date|pick": (result, units) }

    for row in reader:
        league = (row.get("League", "") or "").lower().strip()
        if league == "cross-sport":
            continue
        sport_key = LEAGUE_MAP.get(league)
        if not sport_key:
            # Try Sport column
            sport_val = (row.get("Sport", "") or "").lower().strip()
            sport_key = LEAGUE_MAP.get(sport_val)
        if not sport_key:
            continue

        result = (row.get("Result", "") or "").strip().upper()
        if not result:
            continue

        date = normalize_date((row.get("Date", "") or "").strip())

        # Year filter: skip picks not matching the target year
        if YEAR_FILTER and extract_year(date) != YEAR_FILTER:
            continue

        pick = (row.get("Pick", "") or row.get("Picks", "") or "").strip().lower()
        stake = row.get("Units", "") or "3"
        odds = row.get("Line", "") or row.get("Odds", "") or "-110"
        units = calculate_unit_result(stake, odds, result)

        key = date + "|" + pick
        if sport_key not in sport_picks:
            sport_picks[sport_key] = {}
        sport_picks[sport_key][key] = (result[0], units)

    return sport_picks


def parse_html_records_page(filepath, tracker_picks=None):
    """Parse an HTML records page, merge with Pick Tracker data, and extract stats.

    Args:
        filepath: Path to the HTML records page.
        tracker_picks: Optional dict of { "date|pick": (result, units) } from Pick Tracker.
            These supplement the HTML table (adding picks not in the static HTML).
    """
    with open(filepath, "r", encoding="utf-8") as f:
        html = f.read()

    # Find all table rows in picks-table-body
    row_pattern = re.compile(
        r'<tr>\s*<td[^>]*>([^<]*)</td>'   # date
        r'\s*<td[^>]*>([^<]*)</td>'        # pick
        r'\s*<td[^>]*>([^<]*)</td>'        # line/odds
        r'\s*<td[^>]*class="result-([WLP])"[^>]*>[^<]*</td>'  # result
        r'\s*<td[^>]*class="(?:win|loss|result-P)"[^>]*>([^<]*)</td>'  # units
        r'\s*</tr>',
        re.IGNORECASE
    )

    # Build merged picks dict: key = "date|pick_lower" -> (result, units)
    merged = {}
    last_date = None

    for match in row_pattern.finditer(html):
        date_str = normalize_date(match.group(1).strip())
        pick_str = match.group(2).strip().lower()
        result = match.group(4).upper()
        units_str = match.group(5).strip()

        # Year filter: skip rows not matching the target year
        if YEAR_FILTER and extract_year(date_str) != YEAR_FILTER:
            continue

        try:
            units_val = float(units_str.replace("+", ""))
        except ValueError:
            units_val = 0.0

        key = date_str + "|" + pick_str
        merged[key] = (result, units_val)

        if last_date is None and date_str:
            last_date = date_str

    # Merge Pick Tracker picks: only ADD picks not already in the static HTML.
    # This matches the JS behavior in the records pages (which skip duplicates
    # rather than overwriting), so the widget and records page stay in sync.
    if tracker_picks:
        new_count = 0
        for key, (result, units) in tracker_picks.items():
            if key not in merged:
                merged[key] = (result, units)
                new_count += 1
                tracker_date = key.split("|")[0]
                if tracker_date and (last_date is None):
                    last_date = tracker_date
        if new_count:
            print(f"  Merged {new_count} new picks from Pick Tracker")

    # Calculate totals from merged data.
    # IMPORTANT: classify W/L/P by units value (matches the JS logic in the
    # records pages: units > 0 = W, units < 0 = L, units == 0 = P). Using
    # the result column can diverge from units and cause the widget and
    # records page to show different records.
    wins = 0
    losses = 0
    pushes = 0
    total_units = 0.0

    for key, (result, units) in merged.items():
        if units > 0:
            wins += 1
        elif units < 0:
            losses += 1
        else:
            pushes += 1
        total_units += units

    total_picks = wins + losses + pushes
    win_pct = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0.0

    return {
        "wins": wins,
        "losses": losses,
        "pushes": pushes,
        "totalPicks": total_picks,
        "totalUnits": round(total_units, 2),
        "winPct": round(win_pct, 1),
        "lastDate": last_date or "",
    }


def fetch_mlb_from_sheets():
    """Fetch MLB records from Google Sheets CSV and calculate stats."""
    try:
        req = urllib.request.Request(MLB_SHEETS_URL, headers={
            "User-Agent": "Mozilla/5.0 (BetLegend Transparency Widget)"
        })
        with urllib.request.urlopen(req, timeout=15) as response:
            csv_text = response.read().decode("utf-8")
    except Exception as e:
        print(f"WARNING: Could not fetch MLB Google Sheet: {e}")
        return None

    reader = csv.DictReader(io.StringIO(csv_text))

    wins = 0
    losses = 0
    pushes = 0
    total_units = 0.0
    last_date = None

    for row in reader:
        # Try to find result column (varies by sheet format)
        result = ""
        for key in ["Result", "result", ""]:
            if key in row and row[key]:
                result = row[key].strip().upper()
                break

        # If no result found, scan all values for W/L/P
        if not result:
            for val in row.values():
                v = (val or "").strip().upper()
                if v in ("W", "L", "P"):
                    result = v
                    break

        if not result:
            continue

        # Year filter: skip picks not matching the target year
        date_str = row.get("Date", "").strip()
        if YEAR_FILTER and extract_year(date_str) != YEAR_FILTER:
            continue

        if result.startswith("W"):
            wins += 1
        elif result.startswith("L"):
            losses += 1
        elif result.startswith("P"):
            pushes += 1
        else:
            continue

        # Try to get units
        units_str = ""
        for key in ["ProfitLoss", "Profit/Loss", "Units", "units", "P/L"]:
            if key in row and row[key]:
                units_str = row[key].strip()
                break

        try:
            units_val = float(units_str.replace("+", "").replace("$", ""))
            total_units += units_val
        except (ValueError, TypeError):
            pass

        # Track most recent date
        if last_date is None and date_str:
            last_date = date_str

    total_picks = wins + losses + pushes
    win_pct = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0.0

    return {
        "wins": wins,
        "losses": losses,
        "pushes": pushes,
        "totalPicks": total_picks,
        "totalUnits": round(total_units, 2),
        "winPct": round(win_pct, 1),
        "lastDate": last_date or "",
    }


def main():
    data = {}

    # Fetch Pick Tracker picks (supplements HTML tables with recent picks)
    print("Fetching Pick Tracker data from Google Sheets...")
    tracker_picks = fetch_pick_tracker_picks()
    for sk, picks in tracker_picks.items():
        print(f"  Pick Tracker {sk}: {len(picks)} graded picks")

    # Parse HTML-based records pages and merge with tracker
    for sport_key, filename in HTML_RECORDS_PAGES.items():
        filepath = os.path.join(REPO_ROOT, filename)
        if not os.path.exists(filepath):
            print(f"WARNING: {filepath} not found, skipping {sport_key}")
            continue

        stats = parse_html_records_page(filepath, tracker_picks.get(sport_key, {}))
        data[sport_key] = {
            "displayName": DISPLAY_NAMES[sport_key],
            "recordsLink": RECORDS_LINKS[sport_key],
            **stats,
        }
        print(f"{sport_key}: {stats['wins']}-{stats['losses']}-{stats['pushes']} | "
              f"Units: {stats['totalUnits']:+.2f} | Win%: {stats['winPct']}% | "
              f"Picks: {stats['totalPicks']}")

    # MLB: Fetch Google Sheets data (all historical MLB data lives here).
    # The mlb-records.html table is empty (loads via JavaScript), so the HTML
    # parse above only gets Pick Tracker picks. We also fetch the sheets data
    # and merge with tracker data (both filtered to YEAR_FILTER).
    print(f"Fetching MLB data from Google Sheets (filtered to {YEAR_FILTER})...")
    mlb_sheets_stats = fetch_mlb_from_sheets()
    if mlb_sheets_stats:
        existing_mlb = data.get("MLB")
        if existing_mlb and existing_mlb["totalPicks"] > 0:
            # Combine sheets data with Pick Tracker data (both already year-filtered)
            combined_wins = mlb_sheets_stats["wins"] + existing_mlb["wins"]
            combined_losses = mlb_sheets_stats["losses"] + existing_mlb["losses"]
            combined_pushes = mlb_sheets_stats["pushes"] + existing_mlb["pushes"]
            combined_units = round(mlb_sheets_stats["totalUnits"] + existing_mlb["totalUnits"], 2)
            combined_picks = combined_wins + combined_losses + combined_pushes
            combined_win_pct = round((combined_wins / (combined_wins + combined_losses) * 100) if (combined_wins + combined_losses) > 0 else 0.0, 1)
            last_date = existing_mlb["lastDate"] or mlb_sheets_stats["lastDate"]
            data["MLB"] = {
                "displayName": DISPLAY_NAMES["MLB"],
                "recordsLink": RECORDS_LINKS["MLB"],
                "wins": combined_wins,
                "losses": combined_losses,
                "pushes": combined_pushes,
                "totalPicks": combined_picks,
                "totalUnits": combined_units,
                "winPct": combined_win_pct,
                "lastDate": last_date,
            }
            print(f"MLB (sheets {YEAR_FILTER}): {mlb_sheets_stats['wins']}-{mlb_sheets_stats['losses']}-{mlb_sheets_stats['pushes']} | Units: {mlb_sheets_stats['totalUnits']:+.2f}")
            print(f"MLB (tracker {YEAR_FILTER}): {existing_mlb['wins']}-{existing_mlb['losses']}-{existing_mlb['pushes']} | Units: {existing_mlb['totalUnits']:+.2f}")
            print(f"MLB ({YEAR_FILTER}): {combined_wins}-{combined_losses}-{combined_pushes} | Units: {combined_units:+.2f} | Win%: {combined_win_pct}%")
        else:
            # No tracker data for this year, just use sheets
            data["MLB"] = {
                "displayName": DISPLAY_NAMES["MLB"],
                "recordsLink": RECORDS_LINKS["MLB"],
                **mlb_sheets_stats,
            }
            print(f"MLB ({YEAR_FILTER}): {mlb_sheets_stats['wins']}-{mlb_sheets_stats['losses']}-{mlb_sheets_stats['pushes']} | "
                  f"Units: {mlb_sheets_stats['totalUnits']:+.2f} | Win%: {mlb_sheets_stats['winPct']}%")
    else:
        print("WARNING: MLB Google Sheets data unavailable")
        if "MLB" not in data:
            print("WARNING: MLB data completely unavailable, will be excluded from widget")

    # Generate the JS data file
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    js_content = f"""// Auto-generated by scripts/generate_transparency_data.py
// Last updated: {now}
// DO NOT EDIT MANUALLY - run the script to regenerate

const TRANSPARENCY_DATA = {{
  lastUpdated: "{now}",
  sports: {json.dumps(data, indent=4)}
}};
"""

    output_path = os.path.join(REPO_ROOT, "transparency-widget-data.js")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(js_content)

    print(f"\nData written to: {output_path}")
    print(f"Last updated: {now}")


if __name__ == "__main__":
    main()
