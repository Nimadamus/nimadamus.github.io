#!/usr/bin/env python3
"""
sync_nhl_data.py - Single source of truth for all NHL data pages.

Pulls from NHL API (api-web.nhle.com), updates nhl-standings-data.json,
then regenerates all NHL data page HTML tables from that JSON.

Pages updated:
  - nhl-home-away-splits.html
  - nhl-totals-trends.html
  - nhl-team-trends.html
  - nhl-betting-hub.html (date reference only)

Usage:
  python scripts/sync_nhl_data.py
"""

import json
import os
import re
import sys
import urllib.request
from datetime import datetime

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JSON_PATH = os.path.join(REPO_ROOT, "nhl-standings-data.json")
API_URL = "https://api-web.nhle.com/v1/standings/now"

TEAM_NAME_MAP = {
    "Utah Hockey Club": "Utah Mammoth",
    "Arizona Coyotes": "Utah Mammoth",
}


def fetch_api():
    """Fetch standings from NHL API. Returns parsed JSON or None on failure."""
    try:
        req = urllib.request.Request(API_URL, headers={"User-Agent": "BetLegend-Sync/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        if "standings" not in data or len(data["standings"]) < 32:
            print(f"ERROR: API returned {len(data.get('standings', []))} teams, expected 32")
            return None
        return data
    except Exception as e:
        print(f"ERROR: NHL API fetch failed: {e}")
        return None


def parse_standings(api_data):
    """Parse API response into our standardized team list."""
    teams = []
    for s in api_data["standings"]:
        name = s.get("teamName", {})
        if isinstance(name, dict):
            full_name = name.get("default", "")
        else:
            full_name = str(name)
        team_common = s.get("teamCommonName", {})
        if isinstance(team_common, dict):
            common = team_common.get("default", "")
        else:
            common = str(team_common)
        place = s.get("placeName", {})
        if isinstance(place, dict):
            place_name = place.get("default", "")
        else:
            place_name = str(place)

        display_name = f"{place_name} {common}".strip()
        display_name = TEAM_NAME_MAP.get(display_name, display_name)

        abbrev = s.get("teamAbbrev", {})
        if isinstance(abbrev, dict):
            abbrev = abbrev.get("default", "")

        div = s.get("divisionName", "")
        conf = s.get("conferenceName", "")

        teams.append({
            "name": display_name,
            "abbrev": abbrev,
            "division": div,
            "conference": conf,
            "gp": s.get("gamesPlayed", 0),
            "w": s.get("wins", 0),
            "l": s.get("losses", 0),
            "otl": s.get("otLosses", 0),
            "pts": s.get("points", 0),
            "hw": s.get("homeWins", 0),
            "hl": s.get("homeLosses", 0),
            "hotl": s.get("homeOtLosses", 0),
            "rw": s.get("roadWins", 0),
            "rl": s.get("roadLosses", 0),
            "rotl": s.get("roadOtLosses", 0),
            "gf": s.get("goalFor", 0),
            "ga": s.get("goalAgainst", 0),
        })

    if len(teams) != 32:
        print(f"WARNING: Parsed {len(teams)} teams, expected 32")
        return None
    return teams


def compute_league_summary(teams):
    """Compute league-wide aggregates from team data."""
    total_hw = sum(t["hw"] for t in teams)
    total_home_gp = sum(t["hw"] + t["hl"] + t["hotl"] for t in teams)
    total_rw = sum(t["rw"] for t in teams)
    total_road_gp = sum(t["rw"] + t["rl"] + t["rotl"] for t in teams)
    total_gf = sum(t["gf"] for t in teams)
    total_gp = sum(t["gp"] for t in teams)
    total_games = total_home_gp  # each game = 1 home GP + 1 road GP

    return {
        "total_home_wins": total_hw,
        "total_home_gp": total_home_gp,
        "home_win_pct": f"{total_hw / total_home_gp * 100:.1f}%",
        "total_road_wins": total_rw,
        "total_road_gp": total_road_gp,
        "road_win_pct": f"{total_rw / total_road_gp * 100:.1f}%",
        "avg_gf_per_team": round(total_gf / total_gp, 2),
        "avg_combined_goals": round(total_gf / total_games, 2),
    }


def save_json(teams, summary, date_str):
    """Write the canonical JSON data file."""
    data = {
        "last_updated": date_str,
        "source": "NHL API (api-web.nhle.com/v1/standings/now)",
        "season": "2025-26",
        "league_summary": summary,
        "teams": teams,
    }
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"Updated {JSON_PATH}")


def fmt_pct(numerator, denominator):
    """Format percentage to 1 decimal place."""
    if denominator == 0:
        return "0.0%"
    return f"{numerator / denominator * 100:.1f}%"


def update_splits_page(teams, summary, date_str):
    """Update nhl-home-away-splits.html from JSON data."""
    path = os.path.join(REPO_ROOT, "nhl-home-away-splits.html")
    with open(path, "r", encoding="utf-8") as f:
        html = f.read()

    # Update league-wide summary cards
    html = re.sub(
        r'(<h3>Home Win Rate</h3>\s*<div class="value">)[^<]+(</div>)',
        rf'\g<1>{summary["home_win_pct"]}\2', html)
    html = re.sub(
        r'(<h3>Road Win Rate</h3>\s*<div class="value">)[^<]+(</div>)',
        rf'\g<1>{summary["road_win_pct"]}\2', html)

    # Find best/worst home records
    best_home = max(teams, key=lambda t: t["hw"] / max(t["hw"] + t["hl"] + t["hotl"], 1))
    worst_home = min(teams, key=lambda t: t["hw"] / max(t["hw"] + t["hl"] + t["hotl"], 1))
    best_h_rec = f'{best_home["abbrev"]} {best_home["hw"]}-{best_home["hl"]}-{best_home["hotl"]}'
    best_h_pct = fmt_pct(best_home["hw"], best_home["hw"] + best_home["hl"] + best_home["hotl"])
    worst_h_rec = f'{worst_home["abbrev"]} {worst_home["hw"]}-{worst_home["hl"]}-{worst_home["hotl"]}'
    worst_h_pct = fmt_pct(worst_home["hw"], worst_home["hw"] + worst_home["hl"] + worst_home["hotl"])

    html = re.sub(
        r'(<h3>Best Home Record</h3>\s*<div class="value">)[^<]+(</div>\s*<div class="sub">)[^<]+(</div>)',
        rf'\g<1>{best_h_rec}\g<2>{best_h_pct} win rate\3', html)
    html = re.sub(
        r'(<h3>Worst Home Record</h3>\s*<div class="value">)[^<]+(</div>\s*<div class="sub">)[^<]+(</div>)',
        rf'\g<1>{worst_h_rec}\g<2>{worst_h_pct} win rate\3', html)

    # Update date references
    html = re.sub(
        r'as of March \d+, 2026',
        f'as of {date_str}', html)
    html = re.sub(
        r'Last updated: [^.]+\.',
        f'Last updated: {date_str}.', html)

    # Rebuild division tables
    for div_name in ["Atlantic", "Metropolitan", "Central", "Pacific"]:
        div_teams = [t for t in teams if t["division"] == div_name]
        div_teams.sort(key=lambda t: t["pts"], reverse=True)
        rows = []
        for t in div_teams:
            hgp = t["hw"] + t["hl"] + t["hotl"]
            agp = t["rw"] + t["rl"] + t["rotl"]
            h_wpct = fmt_pct(t["hw"], hgp)
            h_ptspct = fmt_pct(t["hw"] * 2 + t["hotl"], hgp * 2)
            a_wpct = fmt_pct(t["rw"], agp)
            a_ptspct = fmt_pct(t["rw"] * 2 + t["rotl"], agp * 2)
            overall = f'{t["w"]}-{t["l"]}-{t["otl"]}'
            home = f'{t["hw"]}-{t["hl"]}-{t["hotl"]}'
            away = f'{t["rw"]}-{t["rl"]}-{t["rotl"]}'

            hw_ratio = t["hw"] / max(hgp, 1)
            aw_ratio = t["rw"] / max(agp, 1)

            # CSS class logic
            h_cls = ' class="high-green"' if hw_ratio >= 0.62 else (' class="low-red"' if hw_ratio <= 0.30 else '')
            hwpct_cls = h_cls
            hptspct_cls = ' class="high-green"' if h_ptspct.replace('%', '') and float(h_ptspct.replace('%', '')) >= 75.0 else ''
            a_cls = ' class="high-green"' if aw_ratio >= 0.60 else (' class="low-red"' if aw_ratio <= 0.36 else '')
            awpct_cls = a_cls

            row = f' <tr><td>{t["name"]}</td><td>{overall}</td>'
            row += f'<td{h_cls}>{home}</td><td{hwpct_cls}>{h_wpct}</td><td{hptspct_cls}>{h_ptspct}</td>'
            row += f'<td{a_cls}>{away}</td><td{awpct_cls}>{a_wpct}</td><td>{a_ptspct}</td></tr>'
            rows.append(row)

        tbody_html = "\n".join(rows)
        pattern = rf'(division-label">{div_name} Division</div>.*?<tbody>\n)(.*?)(</tbody>)'
        html = re.sub(pattern, rf'\g<1>{tbody_html}\n \3', html, flags=re.DOTALL)

    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Updated {path}")


def update_totals_page(teams, summary, date_str):
    """Update nhl-totals-trends.html - summary cards and date only.
    O/U records come from Action Network, not NHL API, so we only update
    GF/GP, GA/GP, Combined, and league summary values."""
    path = os.path.join(REPO_ROOT, "nhl-totals-trends.html")
    with open(path, "r", encoding="utf-8") as f:
        html = f.read()

    html = re.sub(
        r'(<h3>Avg Goals / Game</h3>\s*<div class="value">)[^<]+(</div>)',
        rf'\g<1>{summary["avg_combined_goals"]}\2', html)
    html = re.sub(
        r'(<h3>Avg GF / Team</h3>\s*<div class="value">)[^<]+(</div>)',
        rf'\g<1>{summary["avg_gf_per_team"]}\2', html)

    # Update highest/lowest scoring
    team_combined = [(t, round((t["gf"] + t["ga"]) / t["gp"], 2)) for t in teams]
    highest = max(team_combined, key=lambda x: x[1])
    lowest = min(team_combined, key=lambda x: x[1])

    html = re.sub(
        r'(<h3>Highest Scoring</h3>\s*<div class="value">)[^<]+(</div>)',
        rf'\g<1>{highest[0]["abbrev"]} {highest[1]:.2f}\2', html)
    html = re.sub(
        r'(<h3>Lowest Scoring</h3>\s*<div class="value">)[^<]+(</div>)',
        rf'\g<1>{lowest[0]["abbrev"]} {lowest[1]:.2f}\2', html)

    # Update per-team GF/GP, GA/GP, Combined in the table
    for t in teams:
        gfgp = round(t["gf"] / t["gp"], 2)
        gagp = round(t["ga"] / t["gp"], 2)
        combined = round((t["gf"] + t["ga"]) / t["gp"], 2)
        # Find the row for this team and update GF/GP, GA/GP, Combined columns
        pattern = rf'(<td>{re.escape(t["name"])}</td>.*?<td>\d+\.\d+%</td><td>)\d+\.\d+(</td><td>)\d+\.\d+(</td><td>)\d+\.\d+(</td>)'
        replacement = rf'\g<1>{gfgp:.2f}\g<2>{gagp:.2f}\g<3>{combined:.2f}\4'
        html = re.sub(pattern, replacement, html)

    html = re.sub(r'as of March \d+, 2026', f'as of {date_str}', html)
    html = re.sub(r'Last updated: [^.]+\.', f'Last updated: {date_str}.', html)

    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Updated {path}")


def update_trends_page(teams, date_str):
    """Update nhl-team-trends.html - overall records only (ATS data from Action Network)."""
    path = os.path.join(REPO_ROOT, "nhl-team-trends.html")
    with open(path, "r", encoding="utf-8") as f:
        html = f.read()

    # Update each team's overall record in the table
    for t in teams:
        overall = f'{t["w"]}-{t["l"]}-{t["otl"]}'
        pattern = rf'(<td>{re.escape(t["name"])}</td><td>)\d+-\d+-\d+(</td>)'
        html = re.sub(pattern, rf'\g<1>{overall}\2', html)

    html = re.sub(r'as of March \d+, 2026', f'as of {date_str}', html)
    html = re.sub(r'Last updated: [^.]+\.', f'Last updated: {date_str}.', html)

    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Updated {path}")


def update_hub_page(date_str):
    """Update nhl-betting-hub.html date reference."""
    path = os.path.join(REPO_ROOT, "nhl-betting-hub.html")
    with open(path, "r", encoding="utf-8") as f:
        html = f.read()

    html = re.sub(r'Last updated: [^.]+\.', f'Last updated: {date_str}.', html)

    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Updated {path}")


def validate(teams):
    """Validate internal consistency of parsed data."""
    errors = []
    for t in teams:
        hgp = t["hw"] + t["hl"] + t["hotl"]
        agp = t["rw"] + t["rl"] + t["rotl"]
        if hgp + agp != t["gp"]:
            errors.append(f'{t["name"]}: home GP ({hgp}) + away GP ({agp}) != total GP ({t["gp"]})')
        if t["hw"] + t["rw"] != t["w"]:
            errors.append(f'{t["name"]}: home W ({t["hw"]}) + road W ({t["rw"]}) != total W ({t["w"]})')
        if t["hl"] + t["rl"] != t["l"]:
            errors.append(f'{t["name"]}: home L ({t["hl"]}) + road L ({t["rl"]}) != total L ({t["l"]})')
        if t["hotl"] + t["rotl"] != t["otl"]:
            errors.append(f'{t["name"]}: home OTL ({t["hotl"]}) + road OTL ({t["rotl"]}) != total OTL ({t["otl"]})')
    return errors


def post_write_validate():
    """Re-read the written JSON and verify integrity. Returns list of errors."""
    errors = []
    try:
        with open(JSON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        return [f"Cannot read JSON after write: {e}"]

    teams = data.get("teams", [])

    # Check 1: Exactly 32 teams
    if len(teams) != 32:
        errors.append(f"Team count is {len(teams)}, expected 32")

    required_fields = ["name", "gp", "w", "l", "otl", "hw", "hl", "hotl", "rw", "rl", "rotl", "gf", "ga"]

    for t in teams:
        # Check 2: No null or missing values
        for field in required_fields:
            val = t.get(field)
            if val is None or val == "":
                errors.append(f'{t.get("name", "UNKNOWN")}: field "{field}" is null or missing')

        # Check 3: Home + Away = Overall
        hgp = t.get("hw", 0) + t.get("hl", 0) + t.get("hotl", 0)
        agp = t.get("rw", 0) + t.get("rl", 0) + t.get("rotl", 0)
        if hgp + agp != t.get("gp", 0):
            errors.append(f'{t["name"]}: home GP ({hgp}) + away GP ({agp}) != total GP ({t["gp"]})')
        if t.get("hw", 0) + t.get("rw", 0) != t.get("w", 0):
            errors.append(f'{t["name"]}: home W + road W != total W')
        if t.get("hl", 0) + t.get("rl", 0) != t.get("l", 0):
            errors.append(f'{t["name"]}: home L + road L != total L')
        if t.get("hotl", 0) + t.get("rotl", 0) != t.get("otl", 0):
            errors.append(f'{t["name"]}: home OTL + road OTL != total OTL')

    if errors:
        print(f"POST-WRITE VALIDATION: {len(errors)} error(s)")
    else:
        print("POST-WRITE VALIDATION: PASS (32 teams, no nulls, all records consistent)")

    return errors


def main():
    print("=" * 60)
    print("NHL Data Sync - Pulling from NHL API")
    print("=" * 60)

    # Step 1: Fetch from API
    api_data = fetch_api()
    if api_data is None:
        print("SAFEGUARD: API fetch failed. Existing data preserved. No changes made.")
        sys.exit(1)

    # Step 2: Parse
    teams = parse_standings(api_data)
    if teams is None:
        print("SAFEGUARD: Parsing failed. Existing data preserved. No changes made.")
        sys.exit(1)

    # Step 3: Validate
    errors = validate(teams)
    if errors:
        print("SAFEGUARD: Validation errors detected. No changes made.")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)

    # Step 4: Compute league summary
    summary = compute_league_summary(teams)
    date_str = datetime.now().strftime("%B %d, %Y").replace(" 0", " ")

    print(f"\nDate: {date_str}")
    print(f"Teams: {len(teams)}")
    print(f"Home Win %: {summary['home_win_pct']}")
    print(f"Road Win %: {summary['road_win_pct']}")
    print(f"Avg Combined Goals: {summary['avg_combined_goals']}")

    # Step 5: Save JSON (single source of truth)
    save_json(teams, summary, date_str)

    # Step 5b: Backup current JSON before overwriting
    backup_path = JSON_PATH + ".bak"
    if os.path.exists(JSON_PATH):
        with open(JSON_PATH, "r", encoding="utf-8") as f:
            backup_content = f.read()
        with open(backup_path, "w", encoding="utf-8") as f:
            f.write(backup_content)

    # Step 6: Save JSON and update all HTML pages
    save_json(teams, summary, date_str)
    update_splits_page(teams, summary, date_str)
    update_totals_page(teams, summary, date_str)
    update_trends_page(teams, date_str)
    update_hub_page(date_str)

    # Step 7: Post-write validation
    post_errors = post_write_validate()
    if post_errors:
        print("\nPOST-WRITE VALIDATION FAILED. Rolling back to previous data.")
        for e in post_errors:
            print(f"  - {e}")
        # Restore backup
        if os.path.exists(backup_path):
            with open(backup_path, "r", encoding="utf-8") as f:
                restored = f.read()
            with open(JSON_PATH, "w", encoding="utf-8") as f:
                f.write(restored)
            print("Restored previous JSON from backup.")
        sys.exit(1)

    # Clean up backup
    if os.path.exists(backup_path):
        os.remove(backup_path)

    print("\n" + "=" * 60)
    print("ALL NHL DATA PAGES SYNCED AND POST-VALIDATED SUCCESSFULLY")
    print("=" * 60)


if __name__ == "__main__":
    main()
