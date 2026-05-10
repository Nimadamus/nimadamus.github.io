#!/usr/bin/env python3
"""
AVG ODDS Validation Script
Fetches data from Google Sheets and validates the AVG ODDS calculation
"""

import csv
import re
from urllib.request import urlopen
from io import StringIO

# Google Sheets CSV URLs
SHEET_URLS = {
    'NFL': 'https://docs.google.com/spreadsheets/d/e/2PACX-1vQgB4WcyyEpMBp_XI_ya6hC7Y8kRaHzrOvuLMq9voGF0nzfqi4lkmAWVb92nDkxUhLVhzr4RTWtZRxq/pub?output=csv',
    'NBA': 'https://docs.google.com/spreadsheets/d/e/2PACX-1vSBoPl-dhj7ZAVpRIafqrFBf10r6sg3jpEKxmuymugAckdoMp-czkj1hscpDnV42GGJsIvNx5EniLVz/pub?output=csv',
}

def extract_odds(line):
    """Extract American odds from line string (e.g., '-110', '+150')"""
    if not line:
        return None

    # Match all +/- numbers, take the last one (usually the odds)
    matches = re.findall(r'([+-]\d+)', line)
    if not matches:
        return None

    return int(matches[-1])

def calculate_avg_odds(sport, url):
    """Calculate AVG ODDS for a sport using corrected logic"""
    print(f"\n{'='*60}")
    print(f"🏈 {sport} - AVG ODDS Calculation")
    print(f"{'='*60}")

    # Fetch CSV data
    response = urlopen(url)
    csv_text = response.read().decode('utf-8')
    reader = csv.DictReader(StringIO(csv_text))

    odds_sum = 0
    odds_count = 0
    total_bets = 0
    excluded_pushes = 0
    excluded_parlays = 0
    excluded_teasers = 0
    sample_odds = []

    for row in reader:
        result = row.get('Result', row.get('result', '')).upper()
        line = row.get('Line', row.get('line', ''))
        pick = row.get('Pick', row.get('pick', '')).lower()
        bet_type = row.get('Bet Type', row.get('bet type', '')).lower()

        # Skip pending or empty
        if not result or result == 'PENDING':
            continue

        total_bets += 1

        # Exclude pushes
        if result in ('P', 'PUSH'):
            excluded_pushes += 1
            continue

        # Exclude parlays
        search_text = pick + ' ' + bet_type
        if 'parlay' in search_text:
            excluded_parlays += 1
            continue

        # Exclude teasers
        if 'teaser' in search_text:
            excluded_teasers += 1
            continue

        # Include in average
        odds = extract_odds(line)
        if odds:
            odds_sum += odds
            odds_count += 1
            if len(sample_odds) < 5:
                sample_odds.append((odds, pick[:30], result))

    # Calculate average
    avg_odds = round(odds_sum / odds_count) if odds_count > 0 else -110

    # Print results
    print(f"\n📊 Summary:")
    print(f"  Total bets with results: {total_bets}")
    print(f"  Excluded (pushes):       {excluded_pushes}")
    print(f"  Excluded (parlays):      {excluded_parlays}")
    print(f"  Excluded (teasers):      {excluded_teasers}")
    print(f"  Included in average:     {odds_count}")

    print(f"\n🧮 Calculation:")
    print(f"  Sum of odds:             {odds_sum:,}")
    print(f"  Count of bets:           {odds_count}")
    print(f"  Average (rounded):       {avg_odds}")
    print(f"  Formula:                 {odds_sum} ÷ {odds_count} = {avg_odds}")

    print(f"\n📋 Sample Included Bets:")
    for odds, pick, result in sample_odds:
        print(f"  {odds:>5} | {pick:<30} | {result}")

    print(f"\n✅ AVG ODDS for {sport}: {avg_odds}")

    return {
        'sport': sport,
        'avg_odds': avg_odds,
        'total_bets': total_bets,
        'included': odds_count,
        'excluded_pushes': excluded_pushes,
        'excluded_parlays': excluded_parlays,
        'excluded_teasers': excluded_teasers,
    }

def main():
    print("🧪 AVG ODDS Validation Script")
    print("=" * 60)
    print("This script validates the AVG ODDS calculation by:")
    print("  ✓ Using posted American odds from Line column")
    print("  ✓ Excluding pushes")
    print("  ✓ Excluding parlays and teasers")
    print("  ✓ Including all straight bets")
    print("  ✓ Computing arithmetic mean")

    results = []

    for sport, url in SHEET_URLS.items():
        try:
            result = calculate_avg_odds(sport, url)
            results.append(result)
        except Exception as e:
            print(f"\n❌ Error processing {sport}: {e}")

    # Summary table
    print("\n" + "=" * 60)
    print("📊 FINAL SUMMARY")
    print("=" * 60)
    print(f"{'Sport':<10} {'AVG ODDS':<12} {'Total':<8} {'Included':<10} {'Excluded'}")
    print("-" * 60)

    for r in results:
        excluded_total = r['excluded_pushes'] + r['excluded_parlays'] + r['excluded_teasers']
        print(f"{r['sport']:<10} {r['avg_odds']:<12} {r['total_bets']:<8} {r['included']:<10} {excluded_total}")

    print("\n✅ Validation complete! Compare these values with records.html")
    print("   Open the browser console on records.html to see the same breakdown.")

if __name__ == '__main__':
    main()
