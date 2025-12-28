#!/usr/bin/env python3
"""
Calendar Sync Script for BetLegend
Automatically scans all sports pages and rebuilds calendar JS files.
Run this script after creating new pages to ensure calendars are complete.

ENHANCED: December 25, 2025 - Improved date extraction to find dates in:
- Title
- Meta description
- Hero section
- Game-time spans (ISO format like 2025-12-20T22:00Z)
- Game-time written dates (like "Friday, December 20")
- Content body dates
"""

import os
import re
from datetime import datetime
from pathlib import Path

# Auto-detect repo directory (works on Windows locally and Linux in GitHub Actions)
import sys
if sys.platform == 'win32':
    REPO_DIR = Path(r'C:\Users\Nima\nimadamus.github.io')
else:
    REPO_DIR = Path(__file__).parent.parent  # scripts/ -> repo root
SCRIPTS_DIR = REPO_DIR / 'scripts'

# Sport configurations
SPORTS = {
    'nba': {'prefix': 'nba', 'main': 'nba.html', 'calendar_js': 'nba-calendar.js'},
    'nhl': {'prefix': 'nhl', 'main': 'nhl.html', 'calendar_js': 'nhl-calendar.js'},
    'ncaab': {'prefix': 'ncaab', 'main': 'ncaab.html', 'calendar_js': 'ncaab-calendar.js'},
    'ncaaf': {'prefix': 'ncaaf', 'main': 'ncaaf.html', 'calendar_js': 'ncaaf-calendar.js'},
    'nfl': {'prefix': 'nfl', 'main': 'nfl.html', 'calendar_js': 'nfl-calendar.js'},
    'mlb': {'prefix': 'mlb', 'main': 'mlb.html', 'calendar_js': 'mlb-calendar.js'},
    'soccer': {'prefix': 'soccer', 'main': 'soccer.html', 'calendar_js': 'soccer-calendar.js'},
}

# Pages to exclude from calendar (utility pages, not content pages)
EXCLUDE_PATTERNS = ['calendar', 'archive', 'records', 'index']

# Manual date overrides for pages where automatic extraction fails
# Format: 'filename.html': 'YYYY-MM-DD'
# These are used when the page title is generic and content dates are unreliable
MANUAL_DATE_OVERRIDES = {
    # NFL archive pages with Week 16 games
    'nfl-page10.html': '2025-11-28',  # Thanksgiving games (Week 13)
    'nfl-page11.html': '2025-12-21',  # Week 16 Saturday games
    'nfl-page12.html': '2025-12-19',  # Week 16 Thursday Night Football
    'nfl-page15.html': '2025-12-20',  # Week 16 Friday/Saturday games
    'nfl-page16.html': '2025-12-21',  # Week 16 Sunday games
    'nfl-page17.html': '2025-12-21',  # Week 16 Sunday games (duplicate)
    'nfl-page18.html': '2025-12-21',  # Week 16 Sunday games
    'nfl-page19.html': '2025-12-21',  # Week 16 Sunday games
    # NBA archive pages
    'nba-page4.html': '2025-12-04',   # December 4 NBA
    'nba-page5.html': '2025-12-05',   # December 5 NBA
    'nba-page8.html': '2025-12-08',   # December 8 NBA
    'nba-page9.html': '2025-12-09',   # December 9 NBA
    'nba-page15.html': '2025-12-15',  # December 15 NBA
    'nba-page16.html': '2025-12-16',  # December 16 NBA
    'nba-page17.html': '2025-12-17',  # December 17 NBA
    'nba-page18.html': '2025-12-18',  # December 18 NBA
    'nba-page19.html': '2025-12-19',  # December 19 NBA (continuation)
    # NHL archive pages
    'nhl-page9.html': '2025-12-09',   # December 9 NHL
    'nhl-page17.html': '2025-12-17',  # December 17 NHL
    'nhl-page18.html': '2025-12-18',  # December 18 NHL
    'nhl-page19.html': '2025-12-19',  # December 19 NHL
    'nhl-page20.html': '2025-12-20',  # December 20 NHL
    'nhl-page21.html': '2025-12-21',  # December 21 NHL
    'nhl-page22.html': '2025-12-22',  # December 22 NHL
    'nhl-page23.html': '2025-12-23',  # December 23 NHL
    # NCAAB archive pages
    'ncaab-page4.html': '2025-12-04',   # December 4 NCAAB
    'ncaab-page5.html': '2025-12-05',   # December 5 NCAAB
    'ncaab-page7.html': '2025-12-07',   # December 7 NCAAB
    'ncaab-page8.html': '2025-12-08',   # December 8 NCAAB
    'ncaab-page9.html': '2025-12-09',   # December 9 NCAAB
    'ncaab-page16.html': '2025-12-16',  # December 16 NCAAB
    'ncaab-page17.html': '2025-12-17',  # December 17 NCAAB
    'ncaab-page18.html': '2025-12-18',  # December 18 NCAAB
    'ncaab-page19.html': '2025-12-19',  # December 19 NCAAB
    'ncaab-page20.html': '2025-12-20',  # December 20 NCAAB
    'ncaab-page21.html': '2025-12-21',  # December 21 NCAAB
    'ncaab-page22.html': '2025-12-22',  # December 22 NCAAB
    # NCAAF archive pages
    'ncaaf-page4.html': '2025-12-04',   # December 4 NCAAF
    'ncaaf-page5.html': '2025-12-05',   # December 5 NCAAF
    'ncaaf-page7.html': '2025-12-07',   # December 7 NCAAF
    'ncaaf-page8.html': '2025-12-08',   # December 8 NCAAF
    'ncaaf-page18.html': '2025-12-18',  # December 18 NCAAF (Bowl games)
    'ncaaf-page19.html': '2025-12-19',  # December 19 NCAAF (Bowl games)
    'ncaaf-page20.html': '2025-12-20',  # December 20 NCAAF (Bowl games)
    'ncaaf-page21.html': '2025-12-21',  # December 21 NCAAF (Bowl games)
    'ncaaf-page22.html': '2025-12-22',  # December 22 NCAAF (Bowl games)
    'ncaaf-page23.html': '2025-12-23',  # December 23 NCAAF (Bowl games)
    'ncaaf-page24.html': '2025-12-24',  # December 24 NCAAF (Bowl games)
}

# Month name to number mapping
MONTH_MAP = {
    'january': 1, 'february': 2, 'march': 3, 'april': 4,
    'may': 5, 'june': 6, 'july': 7, 'august': 8,
    'september': 9, 'october': 10, 'november': 11, 'december': 12,
    'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4,
    'jun': 6, 'jul': 7, 'aug': 8, 'sep': 9, 'sept': 9,
    'oct': 10, 'nov': 11, 'dec': 12
}

def parse_written_date(text):
    """Parse a written date like 'December 23, 2025' or 'Dec 23 2025' into YYYY-MM-DD."""
    # Pattern: Month Day, Year or Month Day Year
    pattern = r'(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)\.?\s+(\d{1,2}),?\s*(\d{4})'
    match = re.search(pattern, text, re.I)
    if match:
        month_name, day, year = match.groups()
        month_num = MONTH_MAP.get(month_name.lower())
        if month_num:
            return f"{year}-{month_num:02d}-{int(day):02d}"
    return None

def extract_date_from_page(filepath):
    """
    Extract date from page content using multiple methods.
    Searches in order of reliability:
    0. Manual override (for pages with unreliable dates)
    1. Title tag
    2. Meta description
    3. Hero section
    4. Game-time spans (various formats)
    5. datetime attributes
    6. Any written date in content
    7. File modification date (fallback)
    """
    try:
        filename = filepath.name if hasattr(filepath, 'name') else os.path.basename(filepath)

        # Method 0: Check manual override first
        if filename in MANUAL_DATE_OVERRIDES:
            return MANUAL_DATE_OVERRIDES[filename]

        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()  # Read full file to find game-time dates

        # Method 1: Look for date in title
        title_match = re.search(r'<title>([^<]+)</title>', content[:5000], re.I)
        if title_match:
            date = parse_written_date(title_match.group(1))
            if date:
                return date

        # Method 2: Look for date in meta description
        desc_match = re.search(r'<meta\s+(?:name="description"\s+)?content="([^"]*)"', content[:5000], re.I)
        if desc_match:
            date = parse_written_date(desc_match.group(1))
            if date:
                return date

        # Method 3: Look in hero section (h1, hero-tagline, etc.)
        hero_match = re.search(r'<(?:h1|p)[^>]*class="[^"]*(?:hero|tagline)[^"]*"[^>]*>([^<]+)', content[:10000], re.I)
        if hero_match:
            date = parse_written_date(hero_match.group(1))
            if date:
                return date

        # Method 4: Look for ISO dates in game-time spans
        # Handles formats like:
        # - "2025-11-30 | Thursday, 12:30 PM ET"
        # - "2025-12-21T01:20Z | Soldier Field"
        game_time_matches = re.findall(r'<span[^>]*class="[^"]*game-time[^"]*"[^>]*>([^<]+)', content)
        for game_time in game_time_matches:
            # Look for ISO date at start: "2025-11-30 |"
            iso_start = re.search(r'^(\d{4}-\d{2}-\d{2})\s*\|', game_time)
            if iso_start:
                return iso_start.group(1)
            # Look for ISO datetime: "2025-12-21T01:20Z"
            iso_datetime = re.search(r'(\d{4}-\d{2}-\d{2})T\d{2}:\d{2}', game_time)
            if iso_datetime:
                return iso_datetime.group(1)
            # Look for written date in game-time
            date = parse_written_date(game_time)
            if date:
                return date

        # Method 5: Look for datetime attribute in content
        iso_datetime_matches = re.findall(r'datetime="(\d{4}-\d{2}-\d{2})T', content)
        if iso_datetime_matches:
            return iso_datetime_matches[0]

        # Method 6: Look for ISO dates anywhere in content (not the most reliable)
        # Skip dates that look like timestamps in scripts
        iso_match = re.search(r'[^0-9](\d{4}-\d{2}-\d{2})[^0-9T]', content[:100000])
        if iso_match:
            return iso_match.group(1)

        # Method 7: Look for any written date in the content (within first 50KB)
        # Skip if it looks like a generic archive date (avoid false positives)
        date = parse_written_date(content[:50000])
        if date:
            return date

        # Method 8: Fallback to file modification date
        mtime = os.path.getmtime(filepath)
        dt = datetime.fromtimestamp(mtime)
        return dt.strftime('%Y-%m-%d')

    except Exception as e:
        print(f"  ERROR reading {filepath}: {e}")
        return None

def extract_title_from_page(filepath, sport_prefix):
    """Extract a nice title from the page."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read(3000)

        # Look for title tag
        title_match = re.search(r'<title>([^<|]+)', content, re.I)
        if title_match:
            title = title_match.group(1).strip()
            # Clean up common suffixes
            title = re.sub(r'\s*\|\s*BetLegend.*$', '', title, flags=re.I)
            return title

        return f"{sport_prefix.upper()} Analysis"
    except:
        return f"{sport_prefix.upper()} Analysis"

def get_sport_pages(sport_config):
    """Get all pages for a sport."""
    prefix = sport_config['prefix']
    pages = []

    # Scan main directory for sport pages
    for filepath in REPO_DIR.glob(f'{prefix}*.html'):
        filename = filepath.name

        # Skip utility pages
        skip = False
        for pattern in EXCLUDE_PATTERNS:
            if pattern in filename.lower():
                skip = True
                break
        if skip:
            continue

        # This is a content page
        date = extract_date_from_page(filepath)
        title = extract_title_from_page(filepath, prefix)

        if date:
            pages.append({
                'date': date,
                'page': filename,
                'title': title
            })
            print(f"    {filename}: {date}")

    # Also scan archives folder for this sport (e.g., archives/nba/)
    archives_dir = REPO_DIR / 'archives' / prefix
    if archives_dir.exists():
        for filepath in archives_dir.glob('*.html'):
            filename = filepath.name
            # Archive files use date format like 2025-12-01.html
            date_match = re.match(r'(\d{4}-\d{2}-\d{2})\.html', filename)
            if date_match:
                date = date_match.group(1)
                relative_path = f'archives/{prefix}/{filename}'
                pages.append({
                    'date': date,
                    'page': relative_path,
                    'title': f'{prefix.upper()} Archive - {date}'
                })
                print(f"    {relative_path}: {date}")

    # Sort by date (newest first) then by page name
    pages.sort(key=lambda x: (x['date'], x['page']), reverse=True)
    return pages

def generate_calendar_js(sport_name, sport_config, pages):
    """Generate the calendar JS file content."""
    today = datetime.now().strftime('%B %d, %Y')

    lines = [
        f'// {sport_name.upper()} Archive Calendar Data',
        f'// Last updated: {today}',
        f'// Auto-generated by sync_calendars.py - DO NOT EDIT MANUALLY',
        '',
        'const ARCHIVE_DATA = ['
    ]

    for page in pages:
        escaped_title = page['title'].replace('"', '\\"')
        lines.append(f'    {{ date: "{page["date"]}", page: "{page["page"]}", title: "{escaped_title}" }},')

    lines.append('];')
    lines.append('')

    # Add the rest of the calendar JS code
    lines.extend([
        'const dateMap = {};',
        'ARCHIVE_DATA.forEach(item => { if (!dateMap[item.date]) dateMap[item.date] = item; });',
        '',
        'const pageToDateMap = {};',
        'ARCHIVE_DATA.forEach(item => { pageToDateMap[item.page] = item.date; });',
        '',
        "const currentPage = window.location.pathname.split('/').pop() || 'index.html';",
        'const currentPageDate = pageToDateMap[currentPage] || null;',
        '',
        'const months = new Set();',
        "ARCHIVE_DATA.forEach(item => { const [y, m] = item.date.split('-'); months.add(y + '-' + m); });",
        '',
        'const today = new Date();',
        "const currentMonth = today.getFullYear() + '-' + String(today.getMonth() + 1).padStart(2, '0');",
        "const todayStr = today.getFullYear() + '-' + String(today.getMonth() + 1).padStart(2, '0') + '-' + String(today.getDate()).padStart(2, '0');",
        'months.add(currentMonth);',
        '',
        'const sortedMonths = Array.from(months).sort().reverse();',
        "const monthNames = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];",
        '',
        'let displayMonth = currentMonth;',
        "if (currentPageDate) { const [py, pm] = currentPageDate.split('-'); displayMonth = py + '-' + pm; }",
        '',
        'function renderCalendar(yearMonth) {',
        "    const [year, month] = yearMonth.split('-').map(Number);",
        "    const yearEl = document.getElementById('cal-year');",
        '    if (yearEl) yearEl.textContent = year;',
        '    const firstDay = new Date(year, month - 1, 1).getDay();',
        '    const daysInMonth = new Date(year, month, 0).getDate();',
        "    const container = document.getElementById('calendar-days');",
        '    if (!container) return;',
        "    container.innerHTML = '';",
        "    for (let i = 0; i < firstDay; i++) { const cell = document.createElement('div'); cell.className = 'cal-day empty'; container.appendChild(cell); }",
        '    for (let d = 1; d <= daysInMonth; d++) {',
        "        const dateStr = year + '-' + String(month).padStart(2, '0') + '-' + String(d).padStart(2, '0');",
        '        const hasData = dateMap[dateStr];',
        "        let classes = 'cal-day';",
        "        if (dateStr === todayStr) classes += ' today';",
        "        if (dateStr === currentPageDate) classes += ' current-page';",
        "        if (hasData) classes += ' has-content';",
        "        const cell = document.createElement('div');",
        '        cell.className = classes;',
        '        cell.textContent = d;',
        '        if (hasData) { cell.title = hasData.title; cell.onclick = () => window.location.href = hasData.page; }',
        '        container.appendChild(cell);',
        '    }',
        '}',
        '',
        'function initSportCalendar() {',
        "    const monthSelect = document.getElementById('month-select');",
        '    if (monthSelect) {',
        "        monthSelect.innerHTML = '';",
        '        sortedMonths.forEach(m => {',
        "            const [year, month] = m.split('-');",
        "            const opt = document.createElement('option');",
        '            opt.value = m;',
        "            opt.textContent = monthNames[parseInt(month) - 1] + ' ' + year;",
        '            if (m === displayMonth) opt.selected = true;',
        '            monthSelect.appendChild(opt);',
        '        });',
        "        monthSelect.addEventListener('change', function() { renderCalendar(this.value); });",
        '    }',
        '    renderCalendar(displayMonth);',
        "    const mobileSelect = document.getElementById('mobile-archive-select');",
        '    if (mobileSelect) {',
        '        mobileSelect.innerHTML = \'<option value="">Select a date...</option>\';',
        '        ARCHIVE_DATA.forEach(item => {',
        "            const opt = document.createElement('option');",
        '            opt.value = item.page;',
        "            const dateObj = new Date(item.date + 'T12:00:00');",
        "            const dateLabel = dateObj.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });",
        "            opt.textContent = dateLabel + ' - ' + item.title;",
        '            if (item.page === currentPage) opt.selected = true;',
        '            mobileSelect.appendChild(opt);',
        '        });',
        "        mobileSelect.addEventListener('change', (e) => { if (e.target.value) window.location.href = e.target.value; });",
        '    }',
        '}',
        '',
        "if (document.readyState === 'loading') { document.addEventListener('DOMContentLoaded', initSportCalendar); } else { initSportCalendar(); }",
        ''
    ])

    return '\n'.join(lines)

def main():
    print("=" * 60)
    print("BetLegend Calendar Sync (Enhanced Date Extraction)")
    print("=" * 60)

    total_pages = 0
    for sport_name, sport_config in SPORTS.items():
        print(f"\n{'='*40}")
        print(f"Processing {sport_name.upper()}...")
        print(f"{'='*40}")

        pages = get_sport_pages(sport_config)
        total_pages += len(pages)
        print(f"\n  Total: {len(pages)} content pages found")

        if pages:
            js_content = generate_calendar_js(sport_name, sport_config, pages)
            js_path = SCRIPTS_DIR / sport_config['calendar_js']

            with open(js_path, 'w', encoding='utf-8') as f:
                f.write(js_content)

            print(f"  Updated {sport_config['calendar_js']}")

    print("\n" + "=" * 60)
    print(f"Calendar sync complete! Total: {total_pages} pages across all sports")
    print("Don't forget to commit and push the changes.")
    print("=" * 60)

if __name__ == '__main__':
    main()
