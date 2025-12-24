#!/usr/bin/env python3
"""
Calendar Sync Script for BetLegend
Automatically scans all sports pages and rebuilds calendar JS files.
Run this script after creating new pages to ensure calendars are complete.
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
}

# Pages to exclude from calendar (utility pages, not content pages)
EXCLUDE_PATTERNS = ['calendar', 'archive', 'records', 'index']

def extract_date_from_page(filepath):
    """Extract date from page content - looks in meta description and title."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read(5000)  # Only need the head section

        # Look for date patterns in meta description
        desc_match = re.search(r'<meta\s+(?:name="description"\s+)?content="([^"]*)"', content, re.I)
        if desc_match:
            desc = desc_match.group(1)
            # Try to find date like "December 23, 2025" or "Dec 23, 2025"
            date_match = re.search(r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(\d{4})', desc, re.I)
            if date_match:
                month_name, day, year = date_match.groups()
                month_num = datetime.strptime(month_name, '%B').month
                return f"{year}-{month_num:02d}-{int(day):02d}"

        # Look for date in title
        title_match = re.search(r'<title>([^<]+)</title>', content, re.I)
        if title_match:
            title = title_match.group(1)
            date_match = re.search(r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(\d{4})', title, re.I)
            if date_match:
                month_name, day, year = date_match.groups()
                month_num = datetime.strptime(month_name, '%B').month
                return f"{year}-{month_num:02d}-{int(day):02d}"

        # Look for ISO date in content
        iso_match = re.search(r'(\d{4}-\d{2}-\d{2})', content)
        if iso_match:
            return iso_match.group(1)

        # Fallback: use file modification date
        mtime = os.path.getmtime(filepath)
        dt = datetime.fromtimestamp(mtime)
        return dt.strftime('%Y-%m-%d')

    except Exception as e:
        print(f"Error reading {filepath}: {e}")
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
    print("BetLegend Calendar Sync")
    print("=" * 60)

    for sport_name, sport_config in SPORTS.items():
        print(f"\nProcessing {sport_name.upper()}...")

        pages = get_sport_pages(sport_config)
        print(f"  Found {len(pages)} content pages")

        if pages:
            js_content = generate_calendar_js(sport_name, sport_config, pages)
            js_path = SCRIPTS_DIR / sport_config['calendar_js']

            with open(js_path, 'w', encoding='utf-8') as f:
                f.write(js_content)

            print(f"  Updated {sport_config['calendar_js']}")

            # Show first few entries
            for page in pages[:3]:
                print(f"    - {page['date']}: {page['page']}")
            if len(pages) > 3:
                print(f"    ... and {len(pages) - 3} more")

    print("\n" + "=" * 60)
    print("Calendar sync complete!")
    print("Don't forget to commit and push the changes.")
    print("=" * 60)

if __name__ == '__main__':
    main()
