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
    # NBA archive pages - CORRECTED based on actual game-time spans
    'nba-page2.html': '2025-12-15',   # December 15 NBA (title confirms)
    'nba-page4.html': '2025-12-20',   # December 20 NBA (game-time)
    'nba-page5.html': '2025-12-21',   # December 21 NBA (game-time)
    'nba-page6.html': '2025-12-15',   # December 15 NBA (title confirms)
    'nba-page8.html': '2025-12-18',   # December 18 NBA (game-time)
    'nba-page9.html': '2025-12-19',   # December 19 NBA (game-time)
    'nba-page15.html': '2025-12-21',  # December 21 NBA (game-time)
    'nba-page16.html': '2025-12-22',  # December 22 NBA
    'nba-page17.html': '2025-12-22',  # December 22 NBA (game-time 23T = 22 ET)
    'nba-page18.html': '2025-12-22',  # December 22 NBA (game-time 23T = 22 ET)
    'nba-page19.html': '2025-12-23',  # December 23 NBA (game-time 24T = 23 ET)
    'nba-page20.html': '2025-12-26',  # December 26 NBA
    'nba-page22.html': '2025-12-21',  # December 21 NBA
    'nba-page24.html': '2025-12-28',  # December 28 NBA
    'nba-page25.html': '2025-12-28',  # December 28 NBA (duplicate/same day)
    # NHL archive pages
    'nhl-page9.html': '2025-12-09',   # December 9 NHL
    'nhl-page17.html': '2025-12-17',  # December 17 NHL
    'nhl-page18.html': '2025-12-18',  # December 18 NHL
    'nhl-page19.html': '2025-12-19',  # December 19 NHL
    'nhl-page20.html': '2025-12-20',  # December 20 NHL
    'nhl-page21.html': '2025-12-21',  # December 21 NHL
    'nhl-page22.html': '2025-12-22',  # December 22 NHL
    'nhl-page23.html': '2025-12-23',  # December 23 NHL
    'nhl-page24.html': '2025-12-23',  # December 23 NHL (evening games)
    'nhl-page25.html': '2025-12-27',  # December 27 NHL (Saturday slate)
    'nhl-page26.html': '2025-12-27',  # December 27 NHL (Saturday slate part 2)
    'nhl-page27.html': '2025-12-28',  # December 28 NHL (Sunday slate)
    'nhl-page28.html': '2025-12-28',  # December 28 NHL (Sunday slate part 2)
    'nhl-page29.html': '2025-12-29',  # December 29 NHL (Sunday slate)
    'nhl-page30.html': '2025-12-31',  # December 31 NHL (New Year's Eve - has ISO dates 2025-12-31)
    'nhl-page31.html': '2025-12-31',  # December 31 NHL (New Year's Eve slate part 2)
    'nhl-page32.html': '2026-01-01',  # January 1 NHL (New Year's Day)
    'nhl-page33.html': '2026-01-01',  # January 1 NHL (New Year's Day part 2)
    'nhl-page34.html': '2026-01-01',  # January 1 NHL (New Year's Day part 3)
    'nhl-page35.html': '2026-01-03',  # January 3 NHL (Friday slate - Jets@Leafs, Caps@Sens, etc.)
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
    # NCAAF archive pages - Complete bowl season coverage
    'ncaaf-page4.html': '2025-12-04',   # December 4 NCAAF
    'ncaaf-page5.html': '2025-12-05',   # December 5 NCAAF
    'ncaaf-page6.html': '2025-12-06',   # December 6 NCAAF
    'ncaaf-page7.html': '2025-12-07',   # December 7 NCAAF
    'ncaaf-page8.html': '2025-12-08',   # December 8 NCAAF
    'ncaaf-page10.html': '2025-12-10',  # December 10 NCAAF
    'ncaaf-page11.html': '2025-12-11',  # December 11 NCAAF
    'ncaaf-page12.html': '2025-12-12',  # December 12 NCAAF
    'ncaaf-page13.html': '2025-12-13',  # December 13 NCAAF
    'ncaaf-page18.html': '2025-12-18',  # December 18 NCAAF (Bowl games)
    'ncaaf-page19.html': '2025-12-19',  # December 19 NCAAF (Bowl games)
    'ncaaf-page20.html': '2025-12-20',  # December 20 NCAAF (Bowl games)
    'ncaaf-page21.html': '2025-12-21',  # December 21 NCAAF (Bowl games)
    'ncaaf-page22.html': '2025-12-22',  # December 22 NCAAF (Bowl games)
    'ncaaf-page23.html': '2025-12-23',  # December 23 NCAAF (Bowl games)
    'ncaaf-page24.html': '2025-12-24',  # December 24 NCAAF (Bowl games)
    'ncaaf-page25.html': '2025-12-25',  # December 25 NCAAF (Bowl games)
    'ncaaf-page26.html': '2025-12-26',  # December 26 NCAAF (Bowl games)
    'ncaaf-page27.html': '2025-12-27',  # December 27 NCAAF (Bowl games)
    'ncaaf-page28.html': '2025-12-28',  # December 28 NCAAF (Bowl games)
    'ncaaf-page29.html': '2025-12-29',  # December 29 NCAAF (Bowl games)
    'ncaaf-page30.html': '2025-12-30',  # December 30 NCAAF (Bowl games)
    'ncaaf-page31.html': '2025-12-17',  # December 17 NCAAF (Bowl games - Cramton Bowl etc)
    'ncaaf-page32.html': '2025-12-17',  # December 17 NCAAF (Bowl games - Gasparilla etc)
    'ncaaf-page33.html': '2025-12-19',  # December 19 NCAAF (Bowl games - Myrtle Beach)
    'ncaaf-page34.html': '2025-12-19',  # December 19 NCAAF (Bowl games - Gasparilla)
    'ncaaf-page35.html': '2025-12-31',  # December 31 NCAAF (New Year's Eve bowls)
    'ncaaf-page36.html': '2026-01-01',  # January 1 NCAAF (CFP Quarterfinals)
    'ncaaf-page37.html': '2026-01-01',  # January 1 NCAAF (CFP Quarterfinals - duplicate/overflow)
    'ncaaf-page38.html': '2026-01-01',  # January 1 NCAAF (CFP Quarterfinals - Rose Bowl, etc.)
    'ncaaf-page39.html': '2026-01-02',  # January 2 NCAAF (Bowl games - Armed Forces, Liberty)
    'ncaaf-page40.html': '2026-01-01',  # January 1 NCAAF (CFP Quarterfinals - overflow)
    'ncaaf-page41.html': '2025-12-14',  # December 14 NCAAF (FCS Playoffs + early bowls)
    'ncaaf-page43.html': '2025-12-13',  # December 13 NCAAF (FCS Playoffs - Quarterfinals)
    'ncaaf-page44.html': '2025-12-14',  # December 14 NCAAF (FCS Playoffs + Army-Navy)
    # ============================================================
    # IMPORTANT: MAIN PAGES ARE NOT IN THIS LIST!
    # nba.html, nhl.html, ncaab.html, soccer.html, nfl.html, mlb.html
    # MUST extract dates from their page titles (not static overrides)
    # because main pages change daily with new content.
    # Only archive pages (pageXX.html) belong in this list.
    # ============================================================

    # NBA archive pages (NOT main page - nba.html extracts from title)
    'nba-page40.html': '2026-01-07',     # January 7 NBA
    'nba-page39.html': '2026-01-05',     # January 5 NBA
    'nba-page38.html': '2026-01-06',     # January 6 NBA
    'nba-page35.html': '2026-01-04',     # January 4 NBA
    'nba-page37.html': '2026-01-03',     # January 3 NBA
    # NHL archive pages (NOT main page - nhl.html extracts from title)
    'nhl-page41.html': '2026-01-07',     # January 7 NHL
    'nhl-page40.html': '2026-01-05',     # January 5 NHL
    'nhl-page39.html': '2026-01-06',     # January 6 NHL
    'nhl-page36.html': '2026-01-04',     # January 4 NHL
    'nhl-page38.html': '2026-01-03',     # January 3 NHL
    # NCAAB archive pages (NOT main page - ncaab.html extracts from title)
    'ncaab-page39.html': '2026-01-07',   # January 7 NCAAB
    'ncaab-page38.html': '2026-01-06',   # January 6 NCAAB
    # Soccer archive pages (NOT main page - soccer.html extracts from title)
    'soccer-page35.html': '2026-01-07',  # January 7 Soccer
    'soccer-page34.html': '2026-01-06',  # January 6 Soccer
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

        # CRITICAL FIX (Jan 8, 2026): Main pages ALWAYS use today's date
        # These are the "current" pages that show today's content
        # Archive pages (page2, page3, etc.) extract dates from content
        MAIN_PAGES = ['nba.html', 'nhl.html', 'ncaab.html', 'ncaaf.html', 'nfl.html', 'mlb.html', 'soccer.html']
        if filename in MAIN_PAGES:
            return datetime.now().strftime('%Y-%m-%d')

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
        '// Handle both root pages and archive pages',
        'const pathname = window.location.pathname;',
        'let currentPage;',
        "if (pathname.includes('/archives/')) {",
        "    // For archive pages, get the full relative path from archives/",
        "    currentPage = pathname.replace(/^\\//, '');",
        '} else {',
        "    // For root pages, just get the filename",
        "    currentPage = pathname.split('/').pop() || 'index.html';",
        '}',
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
        '// Default to page date month if available, otherwise current month',
        'let displayMonth = currentPageDate ? currentPageDate.substring(0, 7) : currentMonth;',
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
        "        if (dateStr === currentPageDate) classes += ' current-page';",
        "        if (dateStr === todayStr) classes += ' today';",
        "        if (hasData) classes += ' has-content';",
        "        const cell = document.createElement('div');",
        '        cell.className = classes;',
        '        cell.textContent = d;',
        '        if (hasData) { cell.title = hasData.title; cell.onclick = () => window.location.href = "/" + hasData.page; }',
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
        "        mobileSelect.addEventListener('change', (e) => { if (e.target.value) window.location.href = '/' + e.target.value; });",
        '    }',
        '}',
        '',
        "if (document.readyState === 'loading') { document.addEventListener('DOMContentLoaded', initSportCalendar); } else { initSportCalendar(); }",
        ''
    ])

    return '\n'.join(lines)

def remove_pagination_from_sports_pages():
    """
    PERMANENTLY removes pagination from ALL sports pages AND featured game pages.
    These pages use calendar sidebar only - NO archive-link pagination.
    Added January 3, 2026 - This runs automatically with every calendar sync.
    Updated January 8, 2026 - Now also cleans featured game pages.
    """
    print("\n[CLEANUP] Removing pagination from sports + featured game pages...")
    sports_patterns = ['nba', 'nhl', 'nfl', 'ncaab', 'ncaaf', 'mlb', 'soccer']
    count = 0

    for f in os.listdir(REPO_DIR):
        if not f.endswith('.html'):
            continue
        # Check if it's a sports page OR a featured game page
        is_target = False
        for sp in sports_patterns:
            if f == f'{sp}.html' or f.startswith(f'{sp}-page'):
                is_target = True
                break
        # Also include featured game pages
        if f.startswith('featured-game'):
            is_target = True
        if not is_target:
            continue

        path = REPO_DIR / f
        with open(path, 'r', encoding='utf-8', errors='ignore') as file:
            content = file.read()

        orig = content
        # Remove archive-link divs (pagination)
        content = re.sub(r'\n*<div class="archive-link">.*?</div>\n*', '\n', content, flags=re.DOTALL)
        # Remove date-section divs that might be pagination
        content = re.sub(r'\n*<div class="date-section">.*?</div>\n*', '\n', content, flags=re.DOTALL)

        if content != orig:
            with open(path, 'w', encoding='utf-8') as file:
                file.write(content)
            count += 1

    if count > 0:
        print(f"  [OK] Removed pagination from {count} files")
    else:
        print(f"  [OK] No pagination found - all clean!")
    return count

def main():
    print("=" * 60)
    print("BetLegend Calendar Sync (Enhanced Date Extraction)")
    print("=" * 60)

    # ALWAYS remove pagination first - sports pages use calendar only
    remove_pagination_from_sports_pages()

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
