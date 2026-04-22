#!/usr/bin/env python3
"""
Build all-records.json by merging EVERY available source of per-sport picks.

Why both sources: the per-sport *-records.html tables are the source of
truth for picks graded after Nov 2025 (sync_records_from_tracker.py writes
into those tables). But MLB's HTML table has been truncated to recent
picks only - the full MLB history lives in mlb-records.json. Neither
source alone is complete, so we merge both, HTML wins on conflict because
it's fresher.

Output is deduped on (Sport, Date, Pick, Odds), sorted newest-first, and
written to all-records.json for betlegend-verified-records.html.

Run standalone, or from sync_records_from_tracker.py:
    python scripts/build_all_records_json.py
"""

import json
import os
import re
from datetime import datetime

REPO_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SPORTS = [
    ('MLB',    'mlb-records.html',    'mlb-records.json'),
    ('NHL',    'nhl-records.html',    'nhl-records.json'),
    ('NFL',    'nfl-records.html',    'nfl-records.json'),
    ('NBA',    'nba-records.html',    'nba-records.json'),
    ('NCAAF',  'ncaaf-records.html',  'ncaaf-records.json'),
    ('NCAAB',  'ncaab-records.html',  'ncaab-records.json'),
    ('Soccer', 'soccer-records.html', 'soccer-records.json'),
]

OUTPUT_FILE = 'all-records.json'

ROW_RE = re.compile(
    r'<tr>\s*'
    r'<td>([^<]+)</td>\s*'       # Date
    r'<td>([^<]+)</td>\s*'       # Pick
    r'<td>([^<]*)</td>\s*'       # Line / Odds
    r'<td[^>]*>([^<]*)</td>\s*'  # Result
    r'<td[^>]*>([^<]*)</td>\s*'  # Units (profit/loss)
    r'</tr>',
    re.IGNORECASE,
)

TBODY_RE = re.compile(
    r'<tbody id="picks-table-body">(.*?)</tbody>',
    re.IGNORECASE | re.DOTALL,
)


def normalize_date(s):
    s = (s or '').strip()
    for fmt in ('%m-%d-%Y', '%m/%d/%Y', '%Y-%m-%d', '%m-%d-%y', '%m/%d/%y'):
        try:
            dt = datetime.strptime(s, fmt)
            return dt.strftime('%#m/%#d/%Y') if os.name == 'nt' else dt.strftime('%-m/%-d/%Y')
        except ValueError:
            continue
    return s


def parse_date_sort_key(s):
    s = (s or '').strip()
    for fmt in ('%m/%d/%Y', '%m-%d-%Y', '%Y-%m-%d', '%m/%d/%y', '%m-%d-%y'):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return datetime.min


def pick_key(row):
    return (
        (row.get('Sport') or '').strip().lower(),
        normalize_date(row.get('Date') or ''),
        (row.get('Picks') or row.get('Pick') or '').strip().lower(),
        (row.get('Odds') or row.get('Line') or '').strip(),
    )


def extract_html_rows(html, sport):
    m = TBODY_RE.search(html)
    if not m:
        return []
    body = m.group(1)
    out = []
    for date, pick, odds, result, units in ROW_RE.findall(body):
        result = (result or '').strip().upper()
        if result and result[0] in ('W', 'L', 'P'):
            result = result[0]
        else:
            result = ''
        units = (units or '').replace('+', '').strip()
        out.append({
            'Sport': sport,
            'League': '',
            'Date': normalize_date(date),
            'Picks': pick.strip(),
            'Odds': odds.strip(),
            'Units': '',
            'Result': result,
            'ProfitLoss': units,
            'GradedAt': '',
        })
    return out


def load_json_rows(path, sport):
    if not os.path.exists(path):
        return []
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    out = []
    for r in data:
        row = {
            'Sport': r.get('Sport') or sport,
            'League': r.get('League', ''),
            'Date': normalize_date(r.get('Date', '')),
            'Picks': (r.get('Picks') or r.get('Pick') or '').strip(),
            'Odds': (r.get('Odds') or r.get('Line') or '').strip(),
            'Units': r.get('Units', ''),
            'Result': (r.get('Result') or '').strip().upper()[:1],
            'ProfitLoss': (r.get('ProfitLoss') or '').replace('+', '').strip(),
            'GradedAt': r.get('GradedAt', ''),
        }
        if row['Result'] not in ('W', 'L', 'P'):
            row['Result'] = ''
        out.append(row)
    return out


def main():
    merged = {}  # key -> row. HTML loaded last so it wins conflicts.

    json_total = 0
    html_total = 0

    for sport, html_file, json_file in SPORTS:
        j = load_json_rows(os.path.join(REPO_PATH, json_file), sport)
        json_added = 0
        for row in j:
            k = pick_key(row)
            if k not in merged:
                merged[k] = row
                json_added += 1
        json_total += json_added

        html_path = os.path.join(REPO_PATH, html_file)
        html_rows = []
        if os.path.exists(html_path):
            with open(html_path, 'r', encoding='utf-8', errors='ignore') as f:
                html_rows = extract_html_rows(f.read(), sport)
        html_added = 0
        html_overwritten = 0
        for row in html_rows:
            k = pick_key(row)
            if k in merged:
                html_overwritten += 1
            else:
                html_added += 1
            merged[k] = row  # HTML wins
        html_total += html_added

        print(f"  {sport:6s} | JSON +{json_added:4d} | HTML +{html_added:4d} new, "
              f"{html_overwritten:4d} overwrote")

    rows = sorted(merged.values(),
                  key=lambda r: parse_date_sort_key(r['Date']), reverse=True)

    out_path = os.path.join(REPO_PATH, OUTPUT_FILE)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(rows, f, indent=2)

    wins = losses = pushes = 0
    total_units = 0.0
    year_units = {}
    year_cnt = {}
    for r in rows:
        res = r['Result']
        if res == 'W': wins += 1
        elif res == 'L': losses += 1
        elif res == 'P': pushes += 1
        try:
            pl = float(r['ProfitLoss']) if r['ProfitLoss'] else 0.0
        except ValueError:
            pl = 0.0
        total_units += pl
        m = re.search(r'(20\d\d)', r['Date'])
        if m:
            y = m.group(1)
            year_units[y] = year_units.get(y, 0.0) + pl
            year_cnt[y] = year_cnt.get(y, 0) + 1

    print()
    print(f"Wrote {out_path}")
    print(f"  Total: {len(rows)} picks | {wins}-{losses}-{pushes} | {total_units:+.2f}u")
    for y in sorted(year_cnt):
        print(f"  {y}: {year_cnt[y]:4d} picks | {year_units[y]:+.2f}u")


if __name__ == '__main__':
    main()
