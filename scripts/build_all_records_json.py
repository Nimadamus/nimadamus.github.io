#!/usr/bin/env python3
"""
Build all-records.json by merging every per-sport *-records.json file.

Output is deduped on (Sport, Date, Picks, Odds) and sorted newest-first so
betlegend-verified-records.html shows an accurate, current all-sports log.

Run standalone, or call from another script:
    python scripts/build_all_records_json.py
"""

import json
import os
import re
from datetime import datetime

REPO_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SOURCE_FILES = [
    'mlb-records.json',
    'nhl-records.json',
    'nfl-records.json',
    'nba-records.json',
    'ncaab-records.json',
    'ncaaf-records.json',
    'soccer-records.json',
]

OUTPUT_FILE = 'all-records.json'


def parse_date(date_str):
    if not date_str:
        return datetime.min
    for fmt in ('%m-%d-%Y', '%m/%d/%Y', '%Y-%m-%d', '%m-%d-%y', '%m/%d/%y'):
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    m = re.search(r'(\d{1,2})[-/](\d{1,2})[-/](\d{2,4})', date_str)
    if m:
        mo, d, y = m.groups()
        y = int(y)
        if y < 100:
            y += 2000
        try:
            return datetime(y, int(mo), int(d))
        except ValueError:
            pass
    return datetime.min


def main():
    merged = []
    seen = set()
    per_sport_counts = {}

    for fname in SOURCE_FILES:
        path = os.path.join(REPO_PATH, fname)
        if not os.path.exists(path):
            print(f"  SKIP {fname} (missing)")
            continue
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        added = 0
        for row in data:
            key = (
                (row.get('Sport') or '').strip().lower(),
                (row.get('Date') or '').strip(),
                (row.get('Picks') or row.get('Pick') or '').strip().lower(),
                (row.get('Odds') or row.get('Line') or '').strip(),
            )
            if key in seen:
                continue
            seen.add(key)
            merged.append(row)
            added += 1
        per_sport_counts[fname] = added
        print(f"  {fname}: {added} unique records")

    merged.sort(key=lambda r: parse_date(r.get('Date', '')), reverse=True)

    out_path = os.path.join(REPO_PATH, OUTPUT_FILE)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(merged, f, indent=2)

    total_units = 0.0
    wins = losses = pushes = 0
    year_counts = {}
    for r in merged:
        try:
            total_units += float(r.get('ProfitLoss', '') or 0)
        except ValueError:
            pass
        res = (r.get('Result', '') or '').upper().strip()
        if res.startswith('W'):
            wins += 1
        elif res.startswith('L'):
            losses += 1
        elif res.startswith('P'):
            pushes += 1
        m = re.search(r'(20\d\d)', r.get('Date', '') or '')
        if m:
            y = m.group(1)
            year_counts[y] = year_counts.get(y, 0) + 1

    print()
    print(f"Wrote {out_path}")
    print(f"  Total records: {len(merged)}")
    print(f"  Record: {wins}-{losses}-{pushes}")
    print(f"  Total units: {total_units:+.2f}")
    print(f"  By year: {dict(sorted(year_counts.items()))}")


if __name__ == '__main__':
    main()
