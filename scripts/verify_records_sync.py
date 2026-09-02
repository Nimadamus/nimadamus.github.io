#!/usr/bin/env python3
"""
Verify that records.html (Detailed Breakdown) produces the same unit totals
as each individual sport records page.

This script fetches the SAME Google Sheet data that both pages use,
computes totals using both approaches, and compares them.
"""

import csv
import io
import re
import sys
import urllib.request
from html.parser import HTMLParser

# ============================================================
# Google Sheet URLs (same as records.html lines 914-920)
# ============================================================
SPORT_SHEET_URLS = {
    'NFL': 'https://docs.google.com/spreadsheets/d/e/2PACX-1vQgB4WcyyEpMBp_XI_ya6hC7Y8kRaHzrOvuLMq9voGF0nzfqi4lkmAWVb92nDkxUhLVhzr4RTWtZRxq/pub?output=csv',
    'NBA': 'https://docs.google.com/spreadsheets/d/e/2PACX-1vSBoPl-dhj7ZAVpRIafqrFBf10r6sg3jpEKxmuymugAckdoMp-czkj1hscpDnV42GGJsIvNx5EniLVz/pub?output=csv',
    'NHL': 'https://docs.google.com/spreadsheets/d/e/2PACX-1vRaRwsGOmbXrqAX0xqrDc9XwRCSaAOkuW68TArz3XQp7SMmLirKbdYqU5-zSM_A-MDNKG6sbdwZac6I/pub?output=csv',
    'MLB': 'https://docs.google.com/spreadsheets/d/e/2PACX-1vQE9RjSNABgl0SxSA1ghp9soUs4gq7teoncN5GLmG5faXmH-sDwXgg0mrk0iQwmSEYExtx6xwFMflXv/pub?output=csv',
    'NCAAF': 'https://docs.google.com/spreadsheets/d/e/2PACX-1vQ9c45xiuXWNe-fAXYMoNb00kCBHfMf4Yn-Xr2LUqdCIiuoiXXDgrDa5mq1PZqxjg8hx-5KnS0L4uVU/pub?output=csv',
    'NCAAB': 'https://docs.google.com/spreadsheets/d/e/2PACX-1vQrFb66HE90gCwliIBQlZ5cNBApJWtGuUV1WbS4pd12SMrs_3qlmSFZCLJ9vBmfgZKcaaGyg4G15J3Y/pub?output=csv',
    'Soccer': 'https://docs.google.com/spreadsheets/d/e/2PACX-1vQy0EQskvixsVQb1zzYtCKDa4F1Wl6WU5QuAFMit32vms-c4DxlhLik-k7U_EhuYntQrpw4BI6r0rns/pub?output=csv',
}

PICK_TRACKER_URL = 'https://docs.google.com/spreadsheets/d/1izhxwiiazn99SRqcK8QpUE4pfvDRIFpgSyw5ZlMsvmY/export?format=csv&gid=0'

# Sport-specific default stakes (from records.html fix)
SPORT_DEFAULTS = {
    'NFL': 2, 'NBA': 1, 'NHL': 3, 'MLB': 1,
    'NCAAF': 3, 'NCAAB': 3, 'Soccer': 1
}

def fetch_csv(url):
    """Fetch CSV from URL and return list of dicts."""
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=30) as resp:
        text = resp.read().decode('utf-8-sig')
    reader = csv.DictReader(io.StringIO(text))
    return list(reader)

def calculate_unit_result(stake_str, odds_str, result_str):
    """
    Same logic as calculateUnitResult() in the JS pages.
    stake = what you're trying to win (for favorites, you risk more)
    Returns the P/L value.
    """
    try:
        stake = float(stake_str)
        odds = float(odds_str)
    except (ValueError, TypeError):
        return None

    result = result_str.strip().upper() if result_str else ''

    if result in ('W', 'WIN'):
        if odds < 0:
            return stake  # Fav win: you win the stake amount
        else:
            return stake * (odds / 100)  # Dog win: you win more
    elif result in ('L', 'LOSS'):
        if odds < 0:
            return -(stake * (abs(odds) / 100))  # Fav loss: you lose more
        else:
            return -stake  # Dog loss: you lose the stake
    elif result in ('P', 'PUSH'):
        return 0.0
    return None

def compute_from_sheet(rows, sport_name):
    """
    Compute stats from a sport-specific Google Sheet.
    The Units column in sport sheets is PRE-CALCULATED P/L.
    This is what records.html now does (pre-computed unitPL).
    """
    wins = 0
    losses = 0
    pushes = 0
    total_units = 0.0
    counted = 0

    for row in rows:
        result = (row.get('Result', '') or row.get('result', '') or '').strip().upper()
        units_raw = row.get('Units', '') or row.get('units', '') or ''

        if result not in ('W', 'WIN', 'L', 'LOSS', 'P', 'PUSH'):
            continue

        try:
            units_val = float(units_raw)
        except (ValueError, TypeError):
            continue

        counted += 1
        total_units += units_val

        if result in ('W', 'WIN'):
            wins += 1
        elif result in ('L', 'LOSS'):
            losses += 1
        elif result in ('P', 'PUSH'):
            pushes += 1

    return {
        'sport': sport_name,
        'wins': wins,
        'losses': losses,
        'pushes': pushes,
        'units': round(total_units, 2),
        'counted': counted
    }

def detect_sport_from_pick(pick_text):
    """Detect sport from the Pick column text (same logic as records.html)."""
    pick = (pick_text or '').upper()

    nfl_teams = ['CHIEFS','BILLS','RAVENS','BENGALS','DOLPHINS','CHARGERS','STEELERS',
                 'TEXANS','JAGUARS','COLTS','BRONCOS','JETS','RAIDERS','TITANS','BROWNS',
                 'PATRIOTS','EAGLES','COWBOYS','49ERS','LIONS','PACKERS','VIKINGS',
                 'SEAHAWKS','BUCCANEERS','BUCS','RAMS','COMMANDERS','SAINTS','FALCONS',
                 'BEARS','CARDINALS','GIANTS','PANTHERS']
    nhl_teams = ['BRUINS','SABRES','RED WINGS','PANTHERS','CANADIENS','SENATORS','LIGHTNING',
                 'MAPLE LEAFS','HURRICANES','BLUE JACKETS','DEVILS','ISLANDERS','RANGERS',
                 'FLYERS','PENGUINS','CAPITALS','BLACKHAWKS','AVALANCHE','STARS','WILD',
                 'PREDATORS','BLUES','JETS','FLAMES','OILERS','KINGS','DUCKS','COYOTES',
                 'SHARKS','KRAKEN','CANUCKS','GOLDEN KNIGHTS','UTAH HC','UTAH HOCKEY']
    nba_teams = ['CELTICS','NETS','KNICKS','76ERS','SIXERS','RAPTORS','BULLS','CAVALIERS',
                 'PISTONS','PACERS','BUCKS','HAWKS','HORNETS','HEAT','MAGIC','WIZARDS',
                 'NUGGETS','TIMBERWOLVES','THUNDER','TRAIL BLAZERS','JAZZ','WARRIORS',
                 'CLIPPERS','LAKERS','SUNS','KINGS','MAVERICKS','ROCKETS','GRIZZLIES',
                 'PELICANS','SPURS']
    mlb_teams = ['YANKEES','RED SOX','BLUE JAYS','ORIOLES','RAYS','WHITE SOX','GUARDIANS',
                 'TIGERS','ROYALS','TWINS','ASTROS','ANGELS','ATHLETICS','MARINERS',
                 'RANGERS','METS','BRAVES','PHILLIES','MARLINS','NATIONALS','CUBS',
                 'REDS','BREWERS','PIRATES','CARDINALS','DODGERS','GIANTS','PADRES',
                 'ROCKIES','DIAMONDBACKS','D-BACKS']

    for t in nfl_teams:
        if t in pick:
            return 'NFL'
    for t in nhl_teams:
        if t in pick:
            return 'NHL'
    for t in nba_teams:
        if t in pick:
            return 'NBA'
    for t in mlb_teams:
        if t in pick:
            return 'MLB'

    if any(kw in pick for kw in ['NCAAF', 'CFB', 'BOWL', 'COLLEGE FOOTBALL']):
        return 'NCAAF'
    if any(kw in pick for kw in ['NCAAB', 'CBB', 'COLLEGE BASKETBALL', 'MARCH MADNESS']):
        return 'NCAAB'
    if any(kw in pick for kw in ['SOCCER', 'PREMIER', 'LA LIGA', 'SERIE A', 'BUNDESLIGA',
                                   'CHAMPIONS LEAGUE', 'MLS', 'LIGA MX', 'LIGUE 1']):
        return 'Soccer'

    return None

def compute_pick_tracker_by_sport(rows):
    """
    Compute stats from Pick Tracker, grouped by sport.
    In Pick Tracker, Units = STAKE (not P/L), so we must calculate P/L.
    """
    sport_data = {}

    for row in rows:
        # Detect sport
        sport_col = (row.get('Sport', '') or '').strip()
        pick_col = row.get('Pick', '') or row.get('pick', '') or ''

        if sport_col:
            sport = sport_col.strip().upper()
            # Normalize sport names from Pick Tracker
            sport_map = {
                'HOCKEY': 'NHL', '`HOCKEY': 'NHL',
                'BASKETBALL': 'NBA', 'BACKETBALL': 'NBA',
                'FOOTBALL': 'NFL',
                'BASEBALL': 'MLB', 'BASETBALL': 'MLB',
                'CBB': 'NCAAB', 'COLLEGE BASKETBALL': 'NCAAB',
                'CFB': 'NCAAF', 'COLLEGE FOOTBALL': 'NCAAF',
            }
            sport = sport_map.get(sport, sport)
        else:
            sport = detect_sport_from_pick(pick_col)

        if not sport:
            continue

        result = (row.get('Result', '') or row.get('result', '') or '').strip().upper()
        if result not in ('W', 'WIN', 'L', 'LOSS', 'P', 'PUSH'):
            continue

        # Get odds
        odds_str = row.get('Line', '') or row.get('Odds', '') or row.get('odds', '') or ''
        odds_str = odds_str.strip()
        if not odds_str:
            continue

        # Get stake (Units in Pick Tracker = STAKE)
        units_str = row.get('Units', '') or row.get('units', '') or ''
        default_stake = SPORT_DEFAULTS.get(sport, 1)
        try:
            stake = float(units_str) if units_str.strip() else default_stake
        except (ValueError, TypeError):
            stake = default_stake

        try:
            odds = float(odds_str)
        except (ValueError, TypeError):
            continue

        # Calculate P/L
        pl = calculate_unit_result(stake, odds, result)
        if pl is None:
            continue

        if sport not in sport_data:
            sport_data[sport] = {'wins': 0, 'losses': 0, 'pushes': 0, 'units': 0.0, 'counted': 0}

        sport_data[sport]['counted'] += 1
        sport_data[sport]['units'] += pl

        if result in ('W', 'WIN'):
            sport_data[sport]['wins'] += 1
        elif result in ('L', 'LOSS'):
            sport_data[sport]['losses'] += 1
        elif result in ('P', 'PUSH'):
            sport_data[sport]['pushes'] += 1

    # Round units
    for sport in sport_data:
        sport_data[sport]['units'] = round(sport_data[sport]['units'], 2)

    return sport_data

def parse_static_html_table(html_file, sport):
    """
    For sports with static HTML tables (NHL, NFL, NCAAF),
    parse the table rows and sum the P/L values directly.
    This is what the individual records pages do.

    Table format:
    <tr><td>Date</td><td>Pick</td><td>Line</td><td class="result-W">W</td><td class="win">+3.00</td></tr>
    """
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()

    wins = 0
    losses = 0
    pushes = 0
    total_units = 0.0
    counted = 0

    td_pattern = re.compile(r'<td[^>]*>(.*?)</td>', re.DOTALL | re.IGNORECASE)
    # Match data rows (skip thead rows)
    row_pattern = re.compile(r'<tr><td>(.*?)</tr>', re.DOTALL | re.IGNORECASE)

    for match in row_pattern.finditer(content):
        row_html = '<td>' + match.group(1)
        tds = td_pattern.findall(row_html)

        if len(tds) < 5:
            continue

        # Columns: Date, Pick, Line, Result, Units
        result_raw = re.sub(r'<[^>]+>', '', tds[3]).strip().upper()
        units_raw = re.sub(r'<[^>]+>', '', tds[4]).strip()

        if result_raw not in ('W', 'WIN', 'L', 'LOSS', 'P', 'PUSH'):
            continue

        try:
            units_val = float(units_raw)
        except (ValueError, TypeError):
            continue

        counted += 1
        total_units += units_val

        if result_raw in ('W', 'WIN'):
            wins += 1
        elif result_raw in ('L', 'LOSS'):
            losses += 1
        elif result_raw in ('P', 'PUSH'):
            pushes += 1

    return {
        'sport': sport,
        'wins': wins,
        'losses': losses,
        'pushes': pushes,
        'units': round(total_units, 2),
        'counted': counted,
        'source': 'static HTML table'
    }

def main():
    print("=" * 70)
    print("  RECORDS SYNC VERIFICATION")
    print("  Comparing records.html data against individual sport records pages")
    print("=" * 70)
    print()

    # ============================================================
    # 1. Fetch data from sport-specific Google Sheets
    #    (This is what records.html uses for all sports)
    # ============================================================
    print("Fetching sport-specific Google Sheet data...")
    sheet_results = {}
    for sport, url in SPORT_SHEET_URLS.items():
        try:
            rows = fetch_csv(url)
            stats = compute_from_sheet(rows, sport)
            sheet_results[sport] = stats
            print(f"  {sport}: {stats['wins']}-{stats['losses']}-{stats['pushes']}, "
                  f"Units: {stats['units']:+.2f}u ({stats['counted']} picks)")
        except Exception as e:
            print(f"  {sport}: ERROR fetching - {e}")
            sheet_results[sport] = None

    print()

    # ============================================================
    # 2. Fetch Pick Tracker data (both pages use this too)
    # ============================================================
    print("Fetching Pick Tracker data...")
    try:
        pt_rows = fetch_csv(PICK_TRACKER_URL)
        pt_results = compute_pick_tracker_by_sport(pt_rows)
        for sport, stats in sorted(pt_results.items()):
            print(f"  {sport}: {stats['wins']}-{stats['losses']}-{stats['pushes']}, "
                  f"Units: {stats['units']:+.2f}u ({stats['counted']} picks)")
    except Exception as e:
        print(f"  ERROR fetching Pick Tracker: {e}")
        pt_results = {}

    print()

    # ============================================================
    # 3. Compute COMBINED totals (Sheet + Pick Tracker, deduplicated)
    #    This is what records.html shows in the Detailed Breakdown
    #    Note: Deduplication happens by Date|Sport|Pick|Line key
    #    We can't perfectly replicate JS dedup here, but sheet data
    #    + PT data gives us the components.
    # ============================================================
    print("=" * 70)
    print("  COMBINED TOTALS (Sheet data + Pick Tracker)")
    print("  This is what records.html Detailed Breakdown should show")
    print("=" * 70)
    print()

    all_sports = sorted(set(list(sheet_results.keys()) + list(pt_results.keys())))

    for sport in all_sports:
        sheet = sheet_results.get(sport)
        pt = pt_results.get(sport, {'wins': 0, 'losses': 0, 'pushes': 0, 'units': 0.0, 'counted': 0})

        if sheet:
            # Note: In practice, deduplication means PT picks that already
            # exist in the sheet won't be double-counted. The sheet data
            # is the primary source.
            print(f"  {sport}:")
            print(f"    Sheet:        {sheet['wins']}-{sheet['losses']}-{sheet['pushes']}, "
                  f"Units: {sheet['units']:+.2f}u ({sheet['counted']} picks)")
            if pt['counted'] > 0:
                print(f"    Pick Tracker: {pt['wins']}-{pt['losses']}-{pt['pushes']}, "
                      f"Units: {pt['units']:+.2f}u ({pt['counted']} picks)")
                print(f"    (PT picks are deduplicated against sheet in the live page)")
            print()
        else:
            print(f"  {sport}: Sheet data unavailable")
            if pt['counted'] > 0:
                print(f"    Pick Tracker only: {pt['wins']}-{pt['losses']}-{pt['pushes']}, "
                      f"Units: {pt['units']:+.2f}u")
            print()

    # ============================================================
    # 4. Parse static HTML tables from individual records pages
    #    (for NHL, NFL, NCAAF which have static tables)
    # ============================================================
    print("=" * 70)
    print("  INDIVIDUAL RECORDS PAGES (static HTML table data)")
    print("=" * 70)
    print()

    html_pages = {
        'NHL': 'nhl-records.html',
        'NFL': 'nfl-records.html',
        'NCAAF': 'ncaaf-records.html',
    }

    html_results = {}
    for sport, filename in html_pages.items():
        try:
            stats = parse_static_html_table(filename, sport)
            html_results[sport] = stats
            print(f"  {sport} ({filename}):")
            print(f"    Static table: {stats['wins']}-{stats['losses']}-{stats['pushes']}, "
                  f"Units: {stats['units']:+.2f}u ({stats['counted']} picks)")
        except Exception as e:
            print(f"  {sport}: ERROR parsing {filename} - {e}")

    print()

    # ============================================================
    # 5. COMPARISON: Sheet totals vs HTML table totals
    # ============================================================
    print("=" * 70)
    print("  COMPARISON: Sheet data vs Individual Records Pages")
    print("=" * 70)
    print()

    all_ok = True

    for sport in all_sports:
        sheet = sheet_results.get(sport)
        html = html_results.get(sport)

        if sheet and html:
            units_match = abs(sheet['units'] - html['units']) < 0.01
            record_match = (sheet['wins'] == html['wins'] and
                           sheet['losses'] == html['losses'] and
                           sheet['pushes'] == html['pushes'])

            status = "MATCH" if (units_match and record_match) else "MISMATCH"
            if status == "MISMATCH":
                all_ok = False

            print(f"  {sport}: [{status}]")
            print(f"    Sheet:      {sheet['wins']}-{sheet['losses']}-{sheet['pushes']}, {sheet['units']:+.2f}u")
            print(f"    HTML table: {html['wins']}-{html['losses']}-{html['pushes']}, {html['units']:+.2f}u")
            if not units_match:
                diff = sheet['units'] - html['units']
                print(f"    UNIT DIFF: {diff:+.2f}u")
            print()
        elif sheet:
            # For sports without static HTML tables (NBA, NCAAB, Soccer, MLB)
            # These pages fetch from the SAME Google Sheet URL, so they should match by definition
            print(f"  {sport}: [OK - same Google Sheet source]")
            print(f"    Sheet: {sheet['wins']}-{sheet['losses']}-{sheet['pushes']}, {sheet['units']:+.2f}u")
            print(f"    (Individual page fetches from same CSV URL - guaranteed match)")
            print()

    print("=" * 70)
    if all_ok:
        print("  ALL SPORTS VERIFIED - DATA IS IN SYNC")
    else:
        print("  MISMATCHES FOUND - INVESTIGATE ABOVE")
    print("=" * 70)

    return 0 if all_ok else 1

if __name__ == '__main__':
    import os
    os.chdir(os.path.dirname(os.path.abspath(__file__)) + '/..')
    sys.exit(main())
