#!/usr/bin/env python3
"""
Generate homepage transparency widget data from the same live sources that power
the records pages.

The homepage widget must stay in sync with:
  - the sport-specific records pages
  - the all-records dashboard

To do that, this script mirrors the records-page data model:
  1. pull each sport's historical/current Google Sheet
  2. pull the master Pick Tracker sheet for recent picks
  3. classify tracker picks conservatively, especially basketball
  4. deduplicate by normalized date + pick text
  5. write transparency-widget-data.js

Usage:
    python scripts/generate_transparency_data.py
"""

import csv
import io
import json
import os
import urllib.request
from datetime import datetime

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SHEET_URLS = {
    "NFL": "https://docs.google.com/spreadsheets/d/e/2PACX-1vQgB4WcyyEpMBp_XI_ya6hC7Y8kRaHzrOvuLMq9voGF0nzfqi4lkmAWVb92nDkxUhLVhzr4RTWtZRxq/pub?output=csv",
    "NBA": "https://docs.google.com/spreadsheets/d/e/2PACX-1vSBoPl-dhj7ZAVpRIafqrFBf10r6sg3jpEKxmuymugAckdoMp-czkj1hscpDnV42GGJsIvNx5EniLVz/pub?output=csv",
    "NHL": "https://docs.google.com/spreadsheets/d/e/2PACX-1vRaRwsGOmbXrqAX0xqrDc9XwRCSaAOkuW68TArz3XQp7SMmLirKbdYqU5-zSM_A-MDNKG6sbdwZac6I/pub?output=csv",
    "MLB": "https://docs.google.com/spreadsheets/d/e/2PACX-1vQE9RjSNABgl0SxSA1ghp9soUs4gq7teoncN5GLmG5faXmH-sDwXgg0mrk0iQwmSEYExtx6xwFMflXv/pub?output=csv",
    "NCAAF": "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ9c45xiuXWNe-fAXYMoNb00kCBHfMf4Yn-Xr2LUqdCIiuoiXXDgrDa5mq1PZqxjg8hx-5KnS0L4uVU/pub?output=csv",
    "NCAAB": "https://docs.google.com/spreadsheets/d/e/2PACX-1vQrFb66HE90gCwliIBQlZ5cNBApJWtGuUV1WbS4pd12SMrs_3qlmSFZCLJ9vBmfgZKcaaGyg4G15J3Y/pub?output=csv",
    "Soccer": "https://docs.google.com/spreadsheets/d/e/2PACX-1vQy0EQskvixsVQb1zzYtCKDa4F1Wl6WU5QuAFMit32vms-c4DxlhLik-k7U_EhuYntQrpw4BI6r0rns/pub?output=csv",
}

PICK_TRACKER_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1izhxwiiazn99SRqcK8QpUE4pfvDRIFpgSyw5ZlMsvmY/export?format=csv&gid=0"
)

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
    "NFL": "2",
    "NBA": "1",
    "NHL": "3",
    "MLB": "1",
    "NCAAF": "3",
    "NCAAB": "3",
    "Soccer": "1",
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
    "marquette", "baylor", "creighton", "michigan state", "florida state",
    "florida", "arizona", "st. john", "st john", "xavier", "memphis",
    "houston cougars", "houston", "texas tech", "oregon", "wisconsin",
    "illinois", "indiana", "cincinnati", "california", "cal", "nc state",
    "virginia", "wake forest", "syracuse", "louisville", "pitt", "maryland",
    "rutgers", "nebraska", "ucla", "usc", "utah", "notre dame", "ole miss",
    "byu", "ucf", "ncaab", "cbb", "ncaa",
}


def fetch_csv_rows(url):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (BetLegend Transparency Widget)"},
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        csv_text = response.read().decode("utf-8-sig")
    return list(csv.DictReader(io.StringIO(csv_text)))


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


def calculate_unit_result(stake_str, odds_str, result):
    stake = safe_float(stake_str)
    odds = safe_float(odds_str, default=-110.0)
    normalized_result = normalize_result(result)
    if not normalized_result:
        return 0.0
    if normalized_result == "W":
        return stake if odds < 0 else stake * (odds / 100)
    if normalized_result == "L":
        return -stake * (abs(odds) / 100) if odds < 0 else -stake
    return 0.0


def latest_date_from_keys(picks_map):
    if not picks_map:
        return ""
    latest_key = max(picks_map.keys(), key=lambda key: date_sort_key(key.split("|", 1)[0]))
    return latest_key.split("|", 1)[0]


def build_stats(picks_map):
    wins = losses = pushes = 0
    total_units = 0.0
    for result, units in picks_map.values():
        if result == "W":
            wins += 1
        elif result == "L":
            losses += 1
        elif result == "P":
            pushes += 1
        total_units += units
    total_picks = wins + losses + pushes
    win_pct = round((wins / (wins + losses) * 100) if (wins + losses) else 0.0, 1)
    return {
        "wins": wins,
        "losses": losses,
        "pushes": pushes,
        "totalPicks": total_picks,
        "totalUnits": round(total_units, 2),
        "winPct": win_pct,
        "lastDate": latest_date_from_keys(picks_map),
    }


def rows_to_pick_map(rows, units_field="Units"):
    picks = {}
    for row in rows:
        result = normalize_result(row.get("Result") or row.get("result"))
        if not result:
            continue
        date_str = row.get("Date", "")
        pick_text = row.get("Pick") or row.get("Picks") or row.get("pick") or ""
        if not date_str or not pick_text:
            continue
        key = make_pick_key(date_str, pick_text)
        units = safe_float(
            row.get(units_field)
            or row.get("ProfitLoss")
            or row.get("Profit/Loss")
            or row.get("P/L")
            or row.get("UNIT_RESULT")
        )
        picks[key] = (result, units)
    return picks


def detect_basketball_sport(row):
    pick_text = (row.get("Pick") or row.get("Picks") or "").lower()
    if any(keyword in pick_text for keyword in NBA_KEYWORDS):
        return "NBA"
    if any(keyword in pick_text for keyword in NCAAB_KEYWORDS):
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


def tracker_rows_to_pick_maps(rows):
    sport_maps = {sport: {} for sport in SHEET_URLS}
    skipped_ambiguous = 0

    for row in rows:
        sport = detect_tracker_sport(row)
        if not sport:
            skipped_ambiguous += 1
            continue

        result = normalize_result(row.get("Result"))
        if not result:
            continue

        date_str = row.get("Date", "")
        pick_text = row.get("Pick") or row.get("Picks") or ""
        if not date_str or not pick_text:
            continue

        odds = row.get("Line") or row.get("Odds") or "-110"
        stake = row.get("Units") or SPORT_DEFAULT_STAKES.get(sport, "1")
        units = calculate_unit_result(stake, odds, result)
        key = make_pick_key(date_str, pick_text)
        sport_maps[sport][key] = (result, units)

    return sport_maps, skipped_ambiguous


def main():
    print("Fetching sport sheets...")
    sheet_pick_maps = {}
    for sport, url in SHEET_URLS.items():
        rows = fetch_csv_rows(url)
        pick_map = rows_to_pick_map(rows)
        sheet_pick_maps[sport] = pick_map
        stats = build_stats(pick_map)
        print(
            f"  {sport}: {stats['wins']}-{stats['losses']}-{stats['pushes']} | "
            f"Units: {stats['totalUnits']:+.2f} | Picks: {stats['totalPicks']}"
        )

    print("Fetching Pick Tracker...")
    tracker_rows = fetch_csv_rows(PICK_TRACKER_URL)
    tracker_maps, skipped_ambiguous = tracker_rows_to_pick_maps(tracker_rows)
    if skipped_ambiguous:
        print(f"  Skipped {skipped_ambiguous} ambiguous tracker rows")

    combined_data = {}
    for sport in SHEET_URLS:
        combined = dict(sheet_pick_maps.get(sport, {}))
        for key, value in tracker_maps.get(sport, {}).items():
            combined[key] = value
        stats = build_stats(combined)
        combined_data[sport] = {
            "displayName": DISPLAY_NAMES[sport],
            "recordsLink": RECORDS_LINKS[sport],
            **stats,
        }
        tracker_added = max(0, len(combined) - len(sheet_pick_maps.get(sport, {})))
        print(
            f"  {sport} merged: {stats['wins']}-{stats['losses']}-{stats['pushes']} | "
            f"Units: {stats['totalUnits']:+.2f} | Picks: {stats['totalPicks']} | "
            f"Tracker additions: {tracker_added}"
        )

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    js_content = (
        f"// Auto-generated by scripts/generate_transparency_data.py\n"
        f"// Last updated: {now}\n"
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
