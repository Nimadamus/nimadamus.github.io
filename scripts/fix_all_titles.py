#!/usr/bin/env python3
"""
Fix all page titles to include dates.
This ensures the calendar sync works correctly.
"""

import os
import re

# Mapping of pages to their correct dates (from sync_calendars.py output)
page_dates = {
    'nba-page4.html': '2025-12-20',
    'nba-page5.html': '2025-12-21',
    'nba-page8.html': '2025-12-18',
    'nba-page9.html': '2025-12-19',
    'nba-page15.html': '2025-12-21',
    'nba-page16.html': '2025-12-22',
    'nba-page17.html': '2025-12-22',
    'nba-page18.html': '2025-12-22',
    'nba-page19.html': '2025-12-23',
    'nba-page20.html': '2025-12-26',
    'nba-page21.html': '2025-12-25',
    'nba-page22.html': '2025-12-21',
    'nba-page23.html': '2025-12-27',
    'nba-page24.html': '2025-12-28',
    'nba-page25.html': '2025-12-28',
    'nba-page26.html': '2025-12-28',
    'nba-page27.html': '2025-12-28',
    'nba-page28.html': '2025-12-20',
    'nba-page29.html': '2025-12-31',
    'nba-page32.html': '2025-12-20',
    'nba-page33.html': '2026-01-01',
    'nba-page34.html': '2026-01-03',
    'nba-page36.html': '2025-12-20',
    'nba-page37.html': '2026-01-03',
    'nba-page38.html': '2026-01-06',
    'nba-page41.html': '2026-01-08',
    'nhl-page4.html': '2025-12-16',
    'nhl-page7.html': '2025-12-17',
    'nhl-page8.html': '2025-12-18',
    'nhl-page9.html': '2025-12-09',
    'nhl-page11.html': '2025-12-19',
    'nhl-page12.html': '2025-12-20',
    'nhl-page17.html': '2025-12-17',
    'nhl-page18.html': '2025-12-18',
    'nhl-page19.html': '2025-12-19',
    'nhl-page20.html': '2025-12-20',
    'nhl-page21.html': '2025-12-21',
    'nhl-page22.html': '2025-12-22',
    'nhl-page23.html': '2025-12-23',
    'nhl-page24.html': '2025-12-23',
    'nhl-page29.html': '2025-12-29',
    'nhl-page30.html': '2025-12-31',
    'nhl-page33.html': '2026-01-01',
    'nhl-page34.html': '2026-01-01',
    'nhl-page37.html': '2025-12-20',
    'nhl-page38.html': '2026-01-03',
    'nhl-page39.html': '2026-01-06',
    'nhl-page42.html': '2026-01-08',
    'ncaab-page4.html': '2025-12-04',
    'ncaab-page5.html': '2025-12-05',
    'ncaab-page7.html': '2025-12-07',
    'ncaab-page8.html': '2025-12-08',
    'ncaab-page9.html': '2025-12-09',
    'ncaab-page11.html': '2025-12-20',
    'ncaab-page12.html': '2025-12-09',
    'ncaab-page13.html': '2025-12-07',
    'ncaab-page14.html': '2025-12-05',
    'ncaab-page15.html': '2025-12-03',
    'ncaab-page16.html': '2025-12-16',
    'ncaab-page17.html': '2025-12-17',
    'ncaab-page18.html': '2025-12-18',
    'ncaab-page19.html': '2025-12-19',
    'ncaab-page20.html': '2025-12-20',
    'ncaab-page21.html': '2025-12-21',
    'ncaab-page22.html': '2025-12-22',
    'ncaab-page23.html': '2025-12-23',
    'ncaab-page24.html': '2025-12-27',
    'ncaab-page25.html': '2025-12-27',
    'ncaab-page26.html': '2025-12-28',
    'ncaab-page27.html': '2025-12-28',
    'ncaab-page28.html': '2025-12-20',
    'ncaab-page29.html': '2025-12-31',
    'ncaab-page32.html': '2025-12-20',
    'ncaab-page33.html': '2026-01-01',
    'ncaab-page34.html': '2026-01-03',
    'ncaab-page36.html': '2025-12-20',
    'ncaab-page37.html': '2026-01-04',
    'ncaab-page38.html': '2026-01-06',
    'ncaab-page40.html': '2026-01-08',
    'nfl-dec19.html': '2025-12-18',
    'nfl-page3.html': '2025-11-23',
    'nfl-page4.html': '2025-11-16',
    'nfl-page5.html': '2025-11-01',
    'nfl-page6.html': '2025-10-30',
    'nfl-page7.html': '2025-10-28',
    'nfl-page8.html': '2025-10-26',
    'nfl-page9.html': '2025-09-10',
    'nfl-page10.html': '2025-11-28',
    'nfl-page11.html': '2025-12-21',
    'nfl-page12.html': '2025-12-19',
    'nfl-page15.html': '2025-12-20',
    'nfl-page16.html': '2025-12-21',
    'nfl-page17.html': '2025-12-21',
    'nfl-page18.html': '2025-12-21',
    'nfl-page19.html': '2025-12-21',
    'nfl-page20.html': '2025-12-21',
    'nfl-page21.html': '2025-12-25',
    'nfl-page22.html': '2025-12-26',
    'nfl-page23.html': '2025-12-21',
    'nfl-page24.html': '2025-12-21',
    'nfl-page25.html': '2025-12-28',
    'nfl-page26.html': '2025-12-29',
    'nfl-page27.html': '2026-01-03',
    'nfl-page29.html': '2025-12-21',
    'soccer-page3.html': '2025-11-28',
    'soccer-page4.html': '2025-12-22',
    'soccer-page5.html': '2025-12-26',
    'soccer-page6.html': '2025-12-27',
    'soccer-page7.html': '2025-12-27',
    'soccer-page8.html': '2025-12-28',
    'soccer-page9.html': '2025-12-28',
    'soccer-page10.html': '2025-12-22',
    'soccer-page11.html': '2026-01-01',
    'soccer-page12.html': '2026-01-01',
    'soccer-page13.html': '2026-01-02',
    'soccer-page14.html': '2025-12-22',
    'soccer-page15.html': '2026-01-04',
    'soccer-page16.html': '2026-01-06',
    'soccer-page17.html': '2026-01-07',
    'soccer-page30.html': '2025-12-21',
    'soccer-page31.html': '2025-12-22',
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
