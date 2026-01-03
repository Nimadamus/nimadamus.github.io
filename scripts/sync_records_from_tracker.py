#!/usr/bin/env python3
"""
Sync Records from Pick Tracker

This script fetches graded picks from the BetLegend Pick Tracker Google Sheet
and updates ALL sport-specific records pages (NHL, NBA, NFL, NCAAF, NCAAB, MLB, Soccer).

Run this after grading picks to update the records pages.

Usage:
    python scripts/sync_records_from_tracker.py
"""

import csv
import io
import os
import re
import urllib.request
from datetime import datetime

# Pick Tracker URL (the master sheet with all graded picks)
PICK_TRACKER_URL = 'https://docs.google.com/spreadsheets/d/1izhxwiiazn99SRqcK8QpUE4pfvDRIFpgSyw5ZlMsvmY/export?format=csv&gid=0'

# Repo path
REPO_PATH = r'C:\Users\Nima\nimadamus.github.io'

# Sport mapping - how to identify picks for each sport from the tracker
SPORT_CONFIG = {
    'nhl': {
        'file': 'nhl-records.html',
        'leagues': ['nhl', 'hockey'],
        'sports': ['hockey', 'nhl']
    },
    'nba': {
        'file': 'nba-records.html',
        'leagues': ['nba', 'basketball'],
        'sports': ['basketball', 'nba']
    },
    'nfl': {
        'file': 'nfl-records.html',
        'leagues': ['nfl', 'football'],
        'sports': ['football', 'nfl']
    },
    'ncaaf': {
        'file': 'ncaaf-records.html',
        'leagues': ['ncaaf', 'college football', 'cfb', 'ncaa football'],
        'sports': ['college football', 'ncaaf', 'cfb']
    },
    'ncaab': {
        'file': 'ncaab-records.html',
        'leagues': ['ncaab', 'college basketball', 'cbb', 'ncaa basketball'],
        'sports': ['college basketball', 'ncaab', 'cbb']
    },
    'mlb': {
        'file': 'mlb-records.html',
        'leagues': ['mlb', 'baseball'],
        'sports': ['baseball', 'mlb']
    },
    'soccer': {
        'file': 'soccer-records.html',
        'leagues': ['soccer', 'football', 'mls', 'epl', 'la liga', 'bundesliga', 'serie a', 'ligue 1'],
        'sports': ['soccer']
    }
}


def fetch_pick_tracker():
    """Fetch all data from the Pick Tracker Google Sheet."""
    print(f"Fetching from Pick Tracker...")
    try:
        req = urllib.request.Request(PICK_TRACKER_URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=30) as response:
            csv_data = response.read().decode('utf-8')

        reader = csv.DictReader(io.StringIO(csv_data))
        records = list(reader)
        print(f"  Found {len(records)} total records in tracker")
        return records
    except Exception as e:
        print(f"  ERROR fetching Pick Tracker: {e}")
        return []


def is_sport_pick(row, sport_key):
    """Check if a pick belongs to a specific sport."""
    config = SPORT_CONFIG[sport_key]
    league = (row.get('League', '') or '').lower().strip()
    sport = (row.get('Sport', '') or '').lower().strip()

    # Skip cross-sport parlays for individual sport pages
    if 'cross-sport' in league or 'parlay' in league.lower():
        return False

    # Check if league or sport matches
    if any(l in league for l in config['leagues']):
        return True
    if any(s in sport for s in config['sports']):
        return True

    return False


def calculate_unit_result(units_stake, odds, result):
    """
    Calculate unit profit/loss using the CORRECT formula from CLAUDE.md.

    Units column = what you're trying to WIN, not what you're risking.

    WINS:
    - Favorite (negative odds): You WIN exactly the units listed
    - Underdog (positive odds): You WIN units × (odds/100)

    LOSSES:
    - Favorite (negative odds): You LOSE units × (|odds|/100)
    - Underdog (positive odds): You LOSE exactly the units listed
    """
    try:
        stake = float(units_stake) if units_stake else 3.0
        odds_num = float(str(odds).replace('+', '').replace(',', '')) if odds else -110
        result_upper = (result or '').upper().strip()
    except (ValueError, TypeError):
        return 0.0

    if result_upper.startswith('W'):
        # WIN
        if odds_num < 0:
            # Favorite win: you win exactly what you were trying to win
            return stake
        else:
            # Underdog win: you win stake × (odds/100)
            return stake * (odds_num / 100)
    elif result_upper.startswith('L'):
        # LOSS
        if odds_num < 0:
            # Favorite loss: you lose stake × (|odds|/100)
            return -stake * (abs(odds_num) / 100)
        else:
            # Underdog loss: you lose exactly what you risked
            return -stake
    else:
        # Push or unknown
        return 0.0


def format_date(date_str):
    """Format date to M/D/YYYY format."""
    if not date_str:
        return ''

    # Try various date formats
    for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%m-%d-%Y', '%m/%d/%y', '%d/%m/%Y']:
        try:
            dt = datetime.strptime(date_str.strip(), fmt)
            return dt.strftime('%-m/%-d/%Y') if os.name != 'nt' else dt.strftime('%#m/%#d/%Y')
        except ValueError:
            continue

    # Return as-is if can't parse
    return date_str


def get_existing_picks(html_content):
    """Extract existing picks from the records page table."""
    existing = set()

    # Find all table rows and extract Date + Pick combinations
    pattern = r'<tr>\s*<td>([^<]+)</td>\s*<td>([^<]+)</td>'
    matches = re.findall(pattern, html_content, re.IGNORECASE)

    for date, pick in matches:
        key = f"{date.strip().lower()}|{pick.strip().lower()}"
        existing.add(key)

    return existing


def create_table_row(pick):
    """Create an HTML table row for a pick."""
    date = pick['Date']
    pick_text = pick['Pick']
    odds = pick['Line']
    result = pick['Result'].upper()[0] if pick['Result'] else ''
    units = pick['Units']

    # Determine CSS classes
    result_class = f"result-{result}" if result in ['W', 'L', 'P'] else ''

    if units > 0:
        units_class = 'win'
        units_text = f"+{units:.2f}"
    elif units < 0:
        units_class = 'loss'
        units_text = f"{units:.2f}"
    else:
        units_class = 'result-P'
        units_text = "0.00"

    return f'                    <tr><td>{date}</td><td>{pick_text}</td><td>{odds}</td><td class="{result_class}">{result}</td><td class="{units_class}">{units_text}</td></tr>'


def update_records_page(sport_key, picks):
    """Update a records page with new picks from the tracker."""
    config = SPORT_CONFIG[sport_key]
    file_path = os.path.join(REPO_PATH, config['file'])

    if not os.path.exists(file_path):
        print(f"  WARNING: {config['file']} not found, skipping")
        return 0

    # Read current file
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        html = f.read()

    # Get existing picks
    existing = get_existing_picks(html)

    # Find new picks that aren't already in the page
    new_picks = []
    for pick in picks:
        key = f"{pick['Date'].strip().lower()}|{pick['Pick'].strip().lower()}"
        if key not in existing and pick['Result']:  # Only graded picks
            new_picks.append(pick)

    if not new_picks:
        print(f"  {sport_key.upper()}: No new picks to add")
        return 0

    # Sort new picks by date (newest first)
    new_picks.sort(key=lambda x: x['Date'], reverse=True)

    # Create new rows
    new_rows = '\n'.join([create_table_row(p) for p in new_picks])

    # Find the table body and insert new rows at the top
    tbody_pattern = r'(<tbody id="picks-table-body">)\s*(\n\s*<!--[^>]*-->)?'
    match = re.search(tbody_pattern, html)

    if match:
        insert_pos = match.end()
        # Find the position after any comments but before first <tr>
        remaining = html[insert_pos:]
        first_tr = remaining.find('<tr>')
        if first_tr > 0:
            insert_pos += first_tr

        new_html = html[:insert_pos] + '\n' + new_rows + '\n' + html[insert_pos:]

        # Write updated file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_html)

        print(f"  {sport_key.upper()}: Added {len(new_picks)} new picks")
        return len(new_picks)
    else:
        print(f"  {sport_key.upper()}: Could not find table body, skipping")
        return 0


def main():
    print("=" * 60)
    print("SYNC RECORDS FROM PICK TRACKER")
    print("=" * 60)
    print()

    # Fetch all data from Pick Tracker
    all_records = fetch_pick_tracker()
    if not all_records:
        print("No records found or error fetching. Exiting.")
        return

    print()
    print("Processing sport-specific records pages...")
    print()

    total_added = 0

    for sport_key in SPORT_CONFIG.keys():
        # Filter picks for this sport
        sport_picks = []
        for row in all_records:
            if is_sport_pick(row, sport_key):
                result = row.get('Result', '').strip()
                if result and result.upper() in ['W', 'WIN', 'L', 'LOSS', 'P', 'PUSH']:
                    pick_data = {
                        'Date': format_date(row.get('Date', '')),
                        'Pick': row.get('Pick', '') or row.get('Picks', ''),
                        'Line': row.get('Odds', '') or row.get('Line', '') or '-110',
                        'Result': result[0].upper(),
                        'Units': calculate_unit_result(
                            row.get('Units', '3'),
                            row.get('Odds', '') or row.get('Line', ''),
                            result
                        )
                    }
                    if pick_data['Pick']:  # Only add if there's a pick
                        sport_picks.append(pick_data)

        # Update the records page
        added = update_records_page(sport_key, sport_picks)
        total_added += added

    print()
    print("=" * 60)
    print(f"COMPLETE: Added {total_added} total new picks across all sports")
    print("=" * 60)
    print()
    print("Next steps:")
    print("  1. Review the changes: git diff")
    print("  2. Commit: git add -A && git commit -m 'Sync records from tracker'")
    print("  3. Push: git push")


if __name__ == '__main__':
    main()
