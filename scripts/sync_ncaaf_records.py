#!/usr/bin/env python3
"""
Sync NCAAF Records from Pick Tracker Google Sheet to ncaaf-records.html

This script:
1. Fetches all NCAAF picks from the Pick Tracker spreadsheet
2. MERGES new picks with existing hardcoded data (doesn't replace historical data)
3. Avoids duplicates by checking date + pick text

Run this after grading new NCAAF picks to keep the records page in sync.
"""

import requests
import csv
import io
import re
import os
from datetime import datetime
from html.parser import HTMLParser

# Configuration
PICK_TRACKER_URL = 'https://docs.google.com/spreadsheets/d/1izhxwiiazn99SRqcK8QpUE4pfvDRIFpgSyw5ZlMsvmY/export?format=csv&gid=0'
RECORDS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'ncaaf-records.html')


class TableParser(HTMLParser):
    """Parse existing picks from the HTML table."""
    def __init__(self):
        super().__init__()
        self.in_tbody = False
        self.in_td = False
        self.current_row = []
        self.rows = []
        self.td_count = 0

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag == 'tbody' and attrs_dict.get('id') == 'picks-table-body':
            self.in_tbody = True
        elif tag == 'tr' and self.in_tbody:
            self.current_row = []
            self.td_count = 0
        elif tag == 'td' and self.in_tbody:
            self.in_td = True
            self.td_count += 1

    def handle_endtag(self, tag):
        if tag == 'tbody':
            self.in_tbody = False
        elif tag == 'tr' and self.in_tbody and len(self.current_row) >= 5:
            self.rows.append(self.current_row[:5])
        elif tag == 'td':
            self.in_td = False

    def handle_data(self, data):
        if self.in_td and self.in_tbody:
            self.current_row.append(data.strip())


def fetch_pick_tracker():
    """Fetch CSV data from the Pick Tracker Google Sheet."""
    print("Fetching Pick Tracker data...")
    response = requests.get(PICK_TRACKER_URL, allow_redirects=True)
    response.raise_for_status()
    return response.text


def parse_csv(csv_text):
    """Parse CSV text into list of dictionaries."""
    reader = csv.DictReader(io.StringIO(csv_text))
    return list(reader)


def is_ncaaf_pick(row):
    """Check if a row is an NCAAF pick."""
    league = (row.get('League') or '').strip().lower()
    sport = (row.get('Sport') or '').strip().lower()

    if league == 'cross-sport':
        return False
    if league in ('ncaaf', 'cfb', 'college football'):
        return True
    if sport in ('ncaaf', 'cfb', 'college football'):
        return True
    return False


def calculate_unit_result(units_stake, odds, result):
    """
    Calculate unit profit/loss using CLAUDE.md formula.
    """
    try:
        stake = float(units_stake)
        odds_num = float(str(odds).replace('+', ''))
        result_upper = (result or '').strip().upper()

        if result_upper.startswith('W'):
            if odds_num < 0:
                return stake
            else:
                return stake * (odds_num / 100)
        elif result_upper.startswith('L'):
            if odds_num < 0:
                return -stake * (abs(odds_num) / 100)
            else:
                return -stake
        elif result_upper.startswith('P'):
            return 0
        return 0
    except (ValueError, TypeError):
        return 0


def format_odds(odds):
    """Format odds with + sign for positive odds."""
    try:
        odds_num = float(str(odds).replace('+', ''))
        if odds_num > 0:
            return f"+{int(odds_num)}"
        return str(int(odds_num))
    except:
        return str(odds)


def normalize_pick_key(date, pick_text):
    """Create a normalized key for deduplication."""
    # Normalize date to M/D/YYYY format
    date_clean = date.replace('-', '/').strip()
    # Normalize pick text
    pick_clean = pick_text.lower().strip()
    # Remove extra spaces
    pick_clean = ' '.join(pick_clean.split())
    return f"{date_clean}|{pick_clean}"


def parse_date(date_str):
    """Parse date string to datetime for sorting."""
    try:
        parts = date_str.replace('-', '/').split('/')
        if len(parts) == 3:
            month, day, year = int(parts[0]), int(parts[1]), int(parts[2])
            return datetime(year, month, day)
    except:
        pass
    return datetime.min


def get_existing_picks(html_content):
    """Extract existing picks from the HTML file."""
    parser = TableParser()
    parser.feed(html_content)

    existing = {}
    for row in parser.rows:
        if len(row) >= 5:
            date, pick, odds, result, units = row[:5]
            key = normalize_pick_key(date, pick)
            existing[key] = {
                'date': date,
                'pick': pick,
                'odds': odds,
                'result': result,
                'units': units
            }
    return existing


def process_pick_tracker_picks(all_picks):
    """Process picks from the Pick Tracker."""
    ncaaf_picks = {}

    for row in all_picks:
        if not is_ncaaf_pick(row):
            continue

        date = (row.get('Date') or '').strip()
        pick_text = (row.get('Pick') or '').strip()
        odds = (row.get('Odds') or '-110').strip()
        result = (row.get('Result') or '').strip().upper()
        units_stake = (row.get('Units') or '3').strip()

        # Skip ungraded picks
        if not result or result[0] not in ('W', 'L', 'P'):
            continue

        # Calculate unit result
        unit_result = calculate_unit_result(units_stake, odds, result)

        # Format units text
        if unit_result > 0:
            units_text = f"+{unit_result:.2f}"
        elif unit_result < 0:
            units_text = f"{unit_result:.2f}"
        else:
            units_text = "0.00"

        key = normalize_pick_key(date, pick_text)
        ncaaf_picks[key] = {
            'date': date,
            'pick': pick_text,
            'odds': format_odds(odds),
            'result': result[0],
            'units': units_text
        }

    return ncaaf_picks


def generate_table_row(pick_data):
    """Generate HTML table row from pick data."""
    date = pick_data['date']
    pick = pick_data['pick']
    odds = pick_data['odds']
    result = pick_data['result']
    units = pick_data['units']

    result_class = f"result-{result}"

    # Determine units class
    try:
        units_val = float(units.replace('+', ''))
        if units_val > 0:
            units_class = "win"
        elif units_val < 0:
            units_class = "loss"
        else:
            units_class = "result-P"
    except:
        units_class = "result-P"

    return f'                    <tr><td>{date}</td><td>{pick}</td><td>{odds}</td><td class="{result_class}">{result}</td><td class="{units_class}">{units}</td></tr>'


def update_records_file(merged_picks):
    """Update the ncaaf-records.html file with merged picks."""
    print(f"Reading {RECORDS_FILE}...")
    with open(RECORDS_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    # Sort picks by date descending
    sorted_picks = sorted(merged_picks.values(), key=lambda x: parse_date(x['date']), reverse=True)

    # Generate new tbody content
    rows = [generate_table_row(p) for p in sorted_picks]
    new_tbody = '<tbody id="picks-table-body">\n' + '\n'.join(rows) + '\n                </tbody>'

    # Replace existing tbody
    pattern = r'<tbody id="picks-table-body">.*?</tbody>'
    new_content = re.sub(pattern, new_tbody, content, flags=re.DOTALL)

    if new_content == content:
        print("WARNING: Could not find tbody to replace!")
        return False

    print(f"Writing updated {RECORDS_FILE}...")
    with open(RECORDS_FILE, 'w', encoding='utf-8') as f:
        f.write(new_content)

    return True


def main():
    print("=" * 60)
    print("NCAAF Records Sync Script (MERGE MODE)")
    print("=" * 60)

    # Read existing HTML file
    with open(RECORDS_FILE, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # Get existing picks from HTML
    existing_picks = get_existing_picks(html_content)
    print(f"Found {len(existing_picks)} existing picks in HTML file")

    # Fetch and parse Pick Tracker data
    csv_text = fetch_pick_tracker()
    all_picks = parse_csv(csv_text)

    # Get NCAAF picks from Pick Tracker
    tracker_picks = process_pick_tracker_picks(all_picks)
    print(f"Found {len(tracker_picks)} NCAAF picks in Pick Tracker")

    # Merge: Pick Tracker takes precedence for duplicates
    merged_picks = existing_picks.copy()
    new_picks_count = 0

    for key, pick_data in tracker_picks.items():
        if key not in merged_picks:
            new_picks_count += 1
            print(f"  NEW: {pick_data['date']} - {pick_data['pick']} ({pick_data['result']})")
        merged_picks[key] = pick_data  # Pick Tracker data overwrites existing

    print(f"Added {new_picks_count} new picks from Pick Tracker")
    print(f"Total picks after merge: {len(merged_picks)}")

    # Update the HTML file
    if update_records_file(merged_picks):
        print("=" * 60)
        print("SUCCESS: ncaaf-records.html updated!")
        print("Don't forget to commit and push the changes.")
        print("=" * 60)
    else:
        print("ERROR: Failed to update file")
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
