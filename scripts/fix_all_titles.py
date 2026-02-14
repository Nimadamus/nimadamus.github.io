#!/usr/bin/env python3
"""
Fix all page titles to include dates.
This ensures the calendar sync works correctly.
"""

import os
import re

# Mapping of pages to their correct dates (from sync_calendars.py output)
page_dates = {
    'nba-picks-analysis-against-the-spread-december-20-2025-part-4.html': '2025-12-20',
    'nba-picks-analysis-against-the-spread-december-21-2025-part-3.html': '2025-12-21',
    'nba-picks-analysis-against-the-spread-december-18-2025.html': '2025-12-18',
    'nba-picks-analysis-against-the-spread-december-19-2025.html': '2025-12-19',
    'nba-picks-analysis-against-the-spread-december-21-2025.html': '2025-12-21',
    'nba-picks-analysis-against-the-spread-december-22-2025.html': '2025-12-22',
    'nba-picks-analysis-against-the-spread-december-22-2025-part-2.html': '2025-12-22',
    'nba-picks-analysis-against-the-spread-december-22-2025-part-3.html': '2025-12-22',
    'nba-picks-analysis-against-the-spread-december-23-2025.html': '2025-12-23',
    'nba-picks-analysis-against-the-spread-december-26-2025.html': '2025-12-26',
    'nba-picks-analysis-against-the-spread-december-25-2025.html': '2025-12-25',
    'nba-picks-analysis-against-the-spread-december-21-2025-part-2.html': '2025-12-21',
    'nba-picks-analysis-against-the-spread-december-27-2025.html': '2025-12-27',
    'nba-picks-analysis-against-the-spread-december-28-2025.html': '2025-12-28',
    'nba-picks-analysis-against-the-spread-december-28-2025-part-2.html': '2025-12-28',
    'nba-picks-analysis-against-the-spread-december-28-2025-part-3.html': '2025-12-28',
    'nba-picks-analysis-against-the-spread-december-28-2025-part-4.html': '2025-12-28',
    'nba-picks-analysis-against-the-spread-december-20-2025.html': '2025-12-20',
    'nba-picks-analysis-against-the-spread-december-31-2025.html': '2025-12-31',
    'nba-picks-analysis-against-the-spread-december-20-2025-part-2.html': '2025-12-20',
    'nba-picks-analysis-against-the-spread-january-01-2026-part-2.html': '2026-01-01',
    'nba-picks-analysis-against-the-spread-january-03-2026.html': '2026-01-03',
    'nba-picks-analysis-against-the-spread-december-20-2025-part-3.html': '2025-12-20',
    'nba-picks-analysis-against-the-spread-january-03-2026-part-2.html': '2026-01-03',
    'nba-picks-analysis-against-the-spread-january-06-2026.html': '2026-01-06',
    'nba-picks-analysis-against-the-spread-january-08-2026.html': '2026-01-08',
    'nhl-predictions-best-bets-tonight-december-16-2025.html': '2025-12-16',
    'nhl-predictions-best-bets-tonight-december-17-2025-part-3.html': '2025-12-17',
    'nhl-predictions-best-bets-tonight-december-18-2025-part-3.html': '2025-12-18',
    'nhl-predictions-best-bets-tonight-december-09-2025.html': '2025-12-09',
    'nhl-predictions-best-bets-tonight-december-19-2025.html': '2025-12-19',
    'nhl-predictions-best-bets-tonight-december-20-2025.html': '2025-12-20',
    'nhl-predictions-best-bets-tonight-december-17-2025.html': '2025-12-17',
    'nhl-predictions-best-bets-tonight-december-18-2025.html': '2025-12-18',
    'nhl-predictions-best-bets-tonight-december-19-2025-part-2.html': '2025-12-19',
    'nhl-predictions-best-bets-tonight-december-20-2025-part-2.html': '2025-12-20',
    'nhl-predictions-best-bets-tonight-december-21-2025.html': '2025-12-21',
    'nhl-predictions-best-bets-tonight-december-22-2025.html': '2025-12-22',
    'nhl-predictions-best-bets-tonight-december-23-2025.html': '2025-12-23',
    'nhl-predictions-best-bets-tonight-december-23-2025-part-2.html': '2025-12-23',
    'nhl-predictions-best-bets-tonight-december-29-2025.html': '2025-12-29',
    'nhl-predictions-best-bets-tonight-december-31-2025.html': '2025-12-31',
    'nhl-predictions-best-bets-tonight-january-01-2026-part-2.html': '2026-01-01',
    'nhl-predictions-best-bets-tonight-january-01-2026-part-3.html': '2026-01-01',
    'nhl-predictions-best-bets-tonight-december-20-2025-part-3.html': '2025-12-20',
    'nhl-predictions-best-bets-tonight-january-03-2026-part-2.html': '2026-01-03',
    'nhl-predictions-best-bets-tonight-january-06-2026.html': '2026-01-06',
    'nhl-predictions-best-bets-tonight-january-08-2026.html': '2026-01-08',
    'college-basketball-picks-predictions-best-bets-december-04-2025.html': '2025-12-04',
    'college-basketball-picks-predictions-best-bets-december-05-2025-part-2.html': '2025-12-05',
    'college-basketball-picks-predictions-best-bets-december-07-2025-part-2.html': '2025-12-07',
    'college-basketball-picks-predictions-best-bets-december-08-2025.html': '2025-12-08',
    'college-basketball-picks-predictions-best-bets-december-09-2025-part-2.html': '2025-12-09',
    'college-basketball-picks-predictions-best-bets-december-20-2025.html': '2025-12-20',
    'college-basketball-picks-predictions-best-bets-december-09-2025.html': '2025-12-09',
    'college-basketball-picks-predictions-best-bets-december-07-2025.html': '2025-12-07',
    'college-basketball-picks-predictions-best-bets-december-05-2025.html': '2025-12-05',
    'college-basketball-picks-predictions-best-bets-december-03-2025.html': '2025-12-03',
    'college-basketball-picks-predictions-best-bets-december-16-2025.html': '2025-12-16',
    'college-basketball-picks-predictions-best-bets-december-17-2025.html': '2025-12-17',
    'college-basketball-picks-predictions-best-bets-december-18-2025.html': '2025-12-18',
    'college-basketball-picks-predictions-best-bets-december-19-2025-part-2.html': '2025-12-19',
    'college-basketball-picks-predictions-best-bets-december-20-2025-part-2.html': '2025-12-20',
    'college-basketball-picks-predictions-best-bets-december-21-2025.html': '2025-12-21',
    'college-basketball-picks-predictions-best-bets-december-22-2025.html': '2025-12-22',
    'college-basketball-picks-predictions-best-bets-december-23-2025.html': '2025-12-23',
    'college-basketball-picks-predictions-best-bets-december-27-2025.html': '2025-12-27',
    'college-basketball-picks-predictions-best-bets-december-27-2025-part-2.html': '2025-12-27',
    'college-basketball-picks-predictions-best-bets-december-28-2025.html': '2025-12-28',
    'college-basketball-picks-predictions-best-bets-december-28-2025-part-2.html': '2025-12-28',
    'college-basketball-picks-predictions-best-bets-december-20-2025-part-3.html': '2025-12-20',
    'college-basketball-picks-predictions-best-bets-december-31-2025.html': '2025-12-31',
    'college-basketball-picks-predictions-best-bets-december-20-2025-part-4.html': '2025-12-20',
    'college-basketball-picks-predictions-best-bets-january-01-2026-part-2.html': '2026-01-01',
    'college-basketball-picks-predictions-best-bets-january-03-2026.html': '2026-01-03',
    'college-basketball-picks-predictions-best-bets-december-20-2025-part-5.html': '2025-12-20',
    'college-basketball-picks-predictions-best-bets-january-04-2026-part-2.html': '2026-01-04',
    'college-basketball-picks-predictions-best-bets-january-06-2026.html': '2026-01-06',
    'college-basketball-picks-predictions-best-bets-january-08-2026.html': '2026-01-08',
    'nfl-dec19.html': '2025-12-18',
    'nfl-picks-predictions-against-the-spread-november-23-2025.html': '2025-11-23',
    'nfl-picks-predictions-against-the-spread-november-16-2025.html': '2025-11-16',
    'nfl-picks-predictions-against-the-spread-november-01-2025.html': '2025-11-01',
    'nfl-picks-predictions-against-the-spread-october-30-2025.html': '2025-10-30',
    'nfl-picks-predictions-against-the-spread-october-28-2025.html': '2025-10-28',
    'nfl-picks-predictions-against-the-spread-october-26-2025.html': '2025-10-26',
    'nfl-picks-predictions-against-the-spread-september-10-2025.html': '2025-09-10',
    'nfl-picks-predictions-against-the-spread-november-28-2025.html': '2025-11-28',
    'nfl-picks-predictions-against-the-spread-december-21-2025.html': '2025-12-21',
    'nfl-picks-predictions-against-the-spread-december-19-2025.html': '2025-12-19',
    'nfl-picks-predictions-against-the-spread-december-20-2025.html': '2025-12-20',
    'nfl-picks-predictions-against-the-spread-december-21-2025-part-2.html': '2025-12-21',
    'nfl-picks-predictions-against-the-spread-december-21-2025-part-3.html': '2025-12-21',
    'nfl-picks-predictions-against-the-spread-december-21-2025-part-4.html': '2025-12-21',
    'nfl-picks-predictions-against-the-spread-december-21-2025-part-5.html': '2025-12-21',
    'nfl-picks-predictions-against-the-spread-december-21-2025-part-7.html': '2025-12-21',
    'nfl-picks-predictions-against-the-spread-december-25-2025.html': '2025-12-25',
    'nfl-picks-predictions-against-the-spread-december-26-2025.html': '2025-12-26',
    'nfl-picks-predictions-against-the-spread-december-21-2025-part-8.html': '2025-12-21',
    'nfl-picks-predictions-against-the-spread-december-21-2025-part-9.html': '2025-12-21',
    'nfl-picks-predictions-against-the-spread-december-28-2025.html': '2025-12-28',
    'nfl-picks-predictions-against-the-spread-december-29-2025.html': '2025-12-29',
    'nfl-picks-predictions-against-the-spread-january-03-2026.html': '2026-01-03',
    'nfl-picks-predictions-against-the-spread-december-21-2025-saturday.html': '2025-12-21',
    'soccer-predictions-picks-best-bets-november-28-2025.html': '2025-11-28',
    'soccer-predictions-picks-best-bets-january-03-2026.html': '2025-12-22',
    'soccer-predictions-picks-best-bets-december-26-2025.html': '2025-12-26',
    'soccer-predictions-picks-best-bets-december-27-2025.html': '2025-12-27',
    'soccer-page7.html': '2025-12-27',
    'soccer-predictions-picks-best-bets-december-28-2025.html': '2025-12-28',
    'soccer-predictions-picks-best-bets-january-25-2026.html': '2025-12-28',
    'soccer-predictions-picks-best-bets-january-05-2026.html': '2025-12-22',
    'soccer-predictions-picks-best-bets-january-01-2026.html': '2026-01-01',
    'soccer-predictions-picks-best-bets-january-01-2026-part-2.html': '2026-01-01',
    'soccer-predictions-picks-best-bets-january-02-2026.html': '2026-01-02',
    'soccer-predictions-picks-best-bets-january-09-2026.html': '2025-12-22',
    'soccer-predictions-picks-best-bets-january-04-2026.html': '2026-01-04',
    'soccer-predictions-picks-best-bets-january-06-2026.html': '2026-01-06',
    'soccer-predictions-picks-best-bets-january-07-2026.html': '2026-01-07',
    'soccer-predictions-picks-best-bets-january-21-2026.html': '2025-12-21',
    'soccer-predictions-picks-best-bets-january-22-2026.html': '2025-12-22',
    'mlb-page2.html': '2026-01-08',
}

month_names = {
    1: 'January', 2: 'February', 3: 'March', 4: 'April',
    5: 'May', 6: 'June', 7: 'July', 8: 'August',
    9: 'September', 10: 'October', 11: 'November', 12: 'December'
}

def format_date(date_str):
    parts = date_str.split('-')
    year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
    return f'{month_names[month]} {day:02d}, {year}'

def main():
    # Change to repo directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_dir = os.path.dirname(script_dir)
    os.chdir(repo_dir)

    fixed = 0
    for page, date in page_dates.items():
        if not os.path.exists(page):
            print(f'SKIP: {page} does not exist')
            continue

        with open(page, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # Check if already has date in title
        title_match = re.search(r'<title>([^<]+)</title>', content)
        if title_match:
            title = title_match.group(1)
            if any(m in title for m in month_names.values()):
                continue  # Already has date

        # Get sport prefix from filename
        sport = page.split('-')[0].upper()
        formatted_date = format_date(date)
        new_title = f'{sport} Analysis - {formatted_date} | BetLegend'

        # Replace title
        new_content = re.sub(r'<title>[^<]+</title>', f'<title>{new_title}</title>', content)

        if new_content != content:
            with open(page, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f'FIXED: {page} -> {new_title}')
            fixed += 1

    print(f'\nTotal fixed: {fixed} pages')

if __name__ == '__main__':
    main()
