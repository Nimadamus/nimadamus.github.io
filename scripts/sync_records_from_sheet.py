#!/usr/bin/env python3
"""
sync_records_from_sheet.py - Syncs graded picks from the Pick Tracker Google Sheet
into the static HTML of each sport's records page.

Run after grading picks to ensure records pages always have fresh data
without relying solely on client-side JS merging.

Usage:
    python scripts/sync_records_from_sheet.py          # Sync all sports
    python scripts/sync_records_from_sheet.py NHL      # Sync one sport
    python scripts/sync_records_from_sheet.py --dry-run # Preview without writing
"""

import csv
import io
import os
import re
import sys
import urllib.request

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = os.path.dirname(SCRIPT_DIR)

PICK_TRACKER_URL = 'https://docs.google.com/spreadsheets/d/1izhxwiiazn99SRqcK8QpUE4pfvDRIFpgSyw5ZlMsvmY/export?format=csv&gid=0'

SPORT_CONFIG = {
    'NHL': {
        'file': 'nhl-records.html',
        'leagues': ['nhl', 'hockey'],
        'sports': ['hockey', 'nhl'],
    },
    'NBA': {
        'file': 'nba-records.html',
        'leagues': ['nba', 'basketball'],
        'sports': ['basketball', 'nba'],
    },
    'NFL': {
        'file': 'nfl-records.html',
        'leagues': ['nfl'],
        'sports': ['football', 'nfl'],
    },
    'NCAAF': {
        'file': 'ncaaf-records.html',
        'leagues': ['ncaaf', 'college football'],
        'sports': ['college football', 'ncaaf'],
    },
    'NCAAB': {
        'file': 'ncaab-records.html',
        'leagues': ['ncaab', 'college basketball'],
        'sports': ['college basketball', 'ncaab'],
    },
    'MLB': {
        'file': 'mlb-records.html',
        'leagues': ['mlb', 'baseball'],
        'sports': ['baseball', 'mlb'],
    },
}


def normalize_date(date_str):
    """Normalize date to M/D/YYYY canonical form."""
    if not date_str:
        return ''
    date_str = date_str.strip()
    parts = re.split(r'[-/]', date_str)
    if len(parts) == 3:
        try:
            m, d, y_str = int(parts[0]), int(parts[1]), parts[2].strip()
            y = int(y_str)
            # Fix leading-zero typos: 0206 -> 206
            if re.match(r'^0\d+$', y_str):
                y_str = y_str.lstrip('0')
                y = int(y_str)
            # Fix 3-digit: 206 -> 2026
            if re.match(r'^\d{3}$', y_str) and y_str.startswith('20'):
                y = int(y_str[:2] + '2' + y_str[2:])
            # Fix 4-digit beyond 2030: 2926 -> 2026
            if y > 2030 and y < 3000:
                y = int('20' + str(y)[-2:])
            if 2020 <= y <= 2030:
                return f'{m}/{d}/{y}'
        except (ValueError, IndexError):
            pass
    return date_str


def calculate_units(stake, odds, result):
    """Calculate unit result using the correct formula from CLAUDE.md."""
    try:
        stake = float(stake)
        odds = float(odds)
    except (ValueError, TypeError):
        return 0.0

    result = (result or '').upper().strip()
    if result.startswith('W'):
        return stake if odds < 0 else round(stake * (odds / 100), 2)
    elif result.startswith('L'):
        return round(-stake * (abs(odds) / 100), 2) if odds < 0 else -stake
    elif result.startswith('P'):
        return 0.0
    return 0.0


def fetch_sheet():
    """Download the Pick Tracker CSV."""
    print('Fetching Pick Tracker sheet...')
    req = urllib.request.Request(PICK_TRACKER_URL, headers={'Cache-Control': 'no-cache'})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = resp.read().decode('utf-8')
    reader = csv.DictReader(io.StringIO(data))
    rows = list(reader)
    print(f'  Downloaded {len(rows)} rows')
    return rows


def get_sport_picks(all_rows, config):
    """Filter sheet rows for a specific sport."""
    picks = []
    for r in all_rows:
        league = (r.get('League', '') or '').strip().lower()
        sport = (r.get('Sport', '') or '').strip().lower()
        if league == 'cross-sport':
            continue
        if league not in config['leagues'] and sport not in config['sports']:
            continue
        result = (r.get('Result', '') or '').strip()
        if not result:
            continue
        picks.append(r)
    return picks


def get_existing_html_keys(filepath):
    """Extract normalized date|pick keys from the static HTML table."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    start = content.find('<tbody id="picks-table-body">')
    if start == -1:
        return set(), content
    end = content.find('</tbody>', start)
    tbody = content[start:end]

    keys = set()
    rows = re.findall(
        r'<tr><td>(.*?)</td><td>(.*?)</td><td>(.*?)</td><td.*?>(.*?)</td><td.*?>(.*?)</td></tr>',
        tbody
    )
    for date, pick, odds, result, units in rows:
        key = normalize_date(date) + '|' + pick.strip().lower()
        keys.add(key)

    return keys, content


def build_row_html(date, pick, odds, result, units_val):
    """Build a single <tr> HTML string."""
    result_upper = result.upper().strip()
    if result_upper.startswith('W'):
        result_class = 'result-W'
        result_text = 'W'
        units_class = 'win'
    elif result_upper.startswith('L'):
        result_class = 'result-L'
        result_text = 'L'
        units_class = 'loss'
    else:
        result_class = 'result-P'
        result_text = 'P'
        units_class = 'result-P'

    units_text = f'{units_val:+.2f}' if units_val != 0 else '0.00'
    display_date = normalize_date(date)

    return (
        f'                    <tr><td>{display_date}</td>'
        f'<td>{pick}</td>'
        f'<td>{odds}</td>'
        f'<td class="{result_class}">{result_text}</td>'
        f'<td class="{units_class}">{units_text}</td></tr>'
    )


def sync_sport(sport_name, config, all_rows, dry_run=False):
    """Sync a single sport's records page with sheet data."""
    filepath = os.path.join(REPO_DIR, config['file'])
    if not os.path.exists(filepath):
        print(f'  {sport_name}: File not found: {config["file"]}')
        return 0

    sheet_picks = get_sport_picks(all_rows, config)
    existing_keys, content = get_existing_html_keys(filepath)

    # Find picks in sheet but not in static HTML
    new_picks = []
    for r in sheet_picks:
        date = (r.get('Date', '') or '').strip()
        pick = (r.get('Pick', '') or r.get('Picks', '')).strip()
        odds = (r.get('Odds', '') or r.get('Line', '') or '-110').strip()
        result = (r.get('Result', '') or '').strip()
        units_stake = (r.get('Units', '') or '3').strip()

        key = normalize_date(date) + '|' + pick.lower()
        if key not in existing_keys:
            units_val = calculate_units(units_stake, odds, result)
            new_picks.append({
                'date': date,
                'pick': pick,
                'odds': odds,
                'result': result,
                'units': units_val,
                'norm_date': normalize_date(date),
            })
            existing_keys.add(key)  # Prevent duplicates within sheet

    if not new_picks:
        print(f'  {sport_name}: Already synced ({len(sheet_picks)} sheet picks, all in HTML)')
        return 0

    # Sort new picks by date descending
    from datetime import datetime
    def parse_date(d):
        try:
            parts = d.split('/')
            return datetime(int(parts[2]), int(parts[0]), int(parts[1]))
        except:
            return datetime(2020, 1, 1)

    new_picks.sort(key=lambda p: parse_date(p['norm_date']), reverse=True)

    # Build HTML rows
    new_rows_html = '\n'.join(
        build_row_html(p['date'], p['pick'], p['odds'], p['result'], p['units'])
        for p in new_picks
    )

    # Insert after <tbody id="picks-table-body">
    insert_marker = '<tbody id="picks-table-body">'
    insert_pos = content.find(insert_marker)
    if insert_pos == -1:
        print(f'  {sport_name}: ERROR - Cannot find picks-table-body')
        return 0

    insert_pos += len(insert_marker)

    new_content = content[:insert_pos] + '\n' + new_rows_html + content[insert_pos:]

    if dry_run:
        print(f'  {sport_name}: Would add {len(new_picks)} picks (dry run)')
        for p in new_picks[:5]:
            print(f'    {p["norm_date"]} | {p["pick"]} | {p["result"]} | {p["units"]:+.2f}u')
        if len(new_picks) > 5:
            print(f'    ... and {len(new_picks) - 5} more')
    else:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f'  {sport_name}: Added {len(new_picks)} new picks to {config["file"]}')

    return len(new_picks)


def verify_math(sport_name, config):
    """Verify year totals sum to all-time total for a sport."""
    filepath = os.path.join(REPO_DIR, config['file'])
    if not os.path.exists(filepath):
        return True

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    start = content.find('<tbody id="picks-table-body">')
    if start == -1:
        return True
    end = content.find('</tbody>', start)
    tbody = content[start:end]

    rows = re.findall(
        r'<tr><td>(.*?)</td><td>(.*?)</td><td>(.*?)</td><td.*?>(.*?)</td><td.*?>(.*?)</td></tr>',
        tbody
    )

    years = {}
    total_w, total_l, total_p, total_u = 0, 0, 0, 0.0

    for date, pick, odds, result, units_str in rows:
        units_val = float(units_str.replace('+', '').replace(',', ''))
        if units_val > 0: total_w += 1
        elif units_val < 0: total_l += 1
        else: total_p += 1
        total_u += units_val

        nd = normalize_date(date)
        parts = nd.split('/')
        if len(parts) == 3:
            try:
                yr = int(parts[2])
                if 2020 <= yr <= 2030:
                    if yr not in years:
                        years[yr] = {'w': 0, 'l': 0, 'p': 0, 'u': 0.0}
                    if units_val > 0: years[yr]['w'] += 1
                    elif units_val < 0: years[yr]['l'] += 1
                    else: years[yr]['p'] += 1
                    years[yr]['u'] += units_val
            except ValueError:
                pass

    sum_w = sum(y['w'] for y in years.values())
    sum_l = sum(y['l'] for y in years.values())
    sum_p = sum(y['p'] for y in years.values())
    sum_u = sum(y['u'] for y in years.values())

    ok = (sum_w == total_w and sum_l == total_l and sum_p == total_p and abs(sum_u - total_u) < 0.01)

    if ok:
        for yr in sorted(years):
            y = years[yr]
            wp = y['w'] / (y['w'] + y['l']) * 100 if (y['w'] + y['l']) > 0 else 0
            print(f'    {yr}: {y["w"]}-{y["l"]}-{y["p"]} | {y["u"]:+.2f}u | {wp:.1f}%')
        print(f'    All Time: {total_w}-{total_l}-{total_p} | {total_u:+.2f}u')
        print(f'    MATH CHECK: PASS')
    else:
        print(f'    All Time: {total_w}-{total_l}-{total_p} | {total_u:+.2f}u')
        print(f'    Sum years: {sum_w}-{sum_l}-{sum_p} | {sum_u:+.2f}u')
        print(f'    MATH CHECK: FAIL - MISMATCH!')

    return ok


def main():
    args = sys.argv[1:]
    dry_run = '--dry-run' in args
    args = [a for a in args if a != '--dry-run']

    # Filter to specific sport if provided
    target_sport = args[0].upper() if args else None
    if target_sport and target_sport not in SPORT_CONFIG:
        print(f'Unknown sport: {target_sport}')
        print(f'Available: {", ".join(SPORT_CONFIG.keys())}')
        sys.exit(1)

    all_rows = fetch_sheet()

    total_added = 0
    sports_to_sync = {target_sport: SPORT_CONFIG[target_sport]} if target_sport else SPORT_CONFIG

    print(f'\n{"=" * 50}')
    print(f'SYNCING RECORDS FROM PICK TRACKER')
    print(f'{"=" * 50}')

    for sport_name, config in sports_to_sync.items():
        added = sync_sport(sport_name, config, all_rows, dry_run)
        total_added += added

    # Verify math for all synced sports
    print(f'\n{"=" * 50}')
    print(f'MATH VERIFICATION')
    print(f'{"=" * 50}')

    all_pass = True
    for sport_name, config in sports_to_sync.items():
        print(f'\n  {sport_name}:')
        if not verify_math(sport_name, config):
            all_pass = False

    print(f'\n{"=" * 50}')
    if dry_run:
        print(f'DRY RUN: Would add {total_added} picks total')
    else:
        print(f'SYNC COMPLETE: Added {total_added} new picks')
    if all_pass:
        print(f'ALL MATH CHECKS: PASS')
    else:
        print(f'MATH CHECKS: SOME FAILED - investigate!')
        sys.exit(1)
    print(f'{"=" * 50}')


if __name__ == '__main__':
    main()
