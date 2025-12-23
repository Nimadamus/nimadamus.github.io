"""
Regenerate all sport calendar JS files with correct code.
"""

import os
import re

REPO = r'C:\Users\Nima\nimadamus.github.io'
SCRIPTS_DIR = os.path.join(REPO, 'scripts')

# Template for calendar JS
CALENDAR_TEMPLATE = '''// {SPORT_UPPER} Archive Calendar Data - CENTRALIZED FILE
// All {sport} pages should reference this file for consistent calendar highlighting
// Last updated: December 22, 2025

const ARCHIVE_DATA = [
{entries}
];

// Build date map for quick lookups (first entry for each date wins for linking)
const dateMap = {{}};
ARCHIVE_DATA.forEach(item => {{
    if (!dateMap[item.date]) {{
        dateMap[item.date] = item;
    }}
}});

// Build page-to-date map (uses LAST/most recent date for pages with multiple entries)
const pageToDateMap = {{}};
ARCHIVE_DATA.forEach(item => {{
    // Always overwrite - last entry wins (most recent date for pages with multiple dates)
    pageToDateMap[item.page] = item.date;
}});

// Get current page filename and find its date
const currentPage = window.location.pathname.split('/').pop() || 'index.html';
const currentPageDate = pageToDateMap[currentPage] || null;

// Get available months from archive data
const months = new Set();
ARCHIVE_DATA.forEach(item => {{
    const [y, m] = item.date.split('-');
    months.add(`${{y}}-${{m}}`);
}});

// Add current month
const today = new Date();
const currentMonth = `${{today.getFullYear()}}-${{String(today.getMonth() + 1).padStart(2, '0')}}`;
const todayStr = `${{today.getFullYear()}}-${{String(today.getMonth() + 1).padStart(2, '0')}}-${{String(today.getDate()).padStart(2, '0')}}`;
months.add(currentMonth);

// Sort months descending (newest first)
const sortedMonths = Array.from(months).sort().reverse();

// Month names for display
const monthNames = ['January', 'February', 'March', 'April', 'May', 'June',
                    'July', 'August', 'September', 'October', 'November', 'December'];

// Determine which month to display - prefer the current page's month if available
let displayMonth = currentMonth;
if (currentPageDate) {{
    const [pageYear, pageMonth] = currentPageDate.split('-');
    displayMonth = `${{pageYear}}-${{pageMonth}}`;
}}

// Render calendar for a specific month
function renderCalendar(yearMonth) {{
    const [year, month] = yearMonth.split('-').map(Number);
    const yearEl = document.getElementById('cal-year');
    if (yearEl) yearEl.textContent = year;

    const firstDay = new Date(year, month - 1, 1).getDay();
    const daysInMonth = new Date(year, month, 0).getDate();

    const container = document.getElementById('calendar-days');
    if (!container) return;
    container.innerHTML = '';

    // Empty cells before first day
    for (let i = 0; i < firstDay; i++) {{
        const cell = document.createElement('div');
        cell.className = 'cal-day empty';
        container.appendChild(cell);
    }}

    // Day cells
    for (let d = 1; d <= daysInMonth; d++) {{
        const dateStr = `${{year}}-${{String(month).padStart(2, '0')}}-${{String(d).padStart(2, '0')}}`;
        const hasData = dateMap[dateStr];
        let classes = 'cal-day';

        if (dateStr === todayStr) classes += ' today';
        if (dateStr === currentPageDate) classes += ' current-page';
        if (hasData) classes += ' has-content';

        const cell = document.createElement('div');
        cell.className = classes;
        cell.textContent = d;

        if (hasData) {{
            cell.title = hasData.title;
            cell.onclick = () => window.location.href = hasData.page;
        }}

        container.appendChild(cell);
    }}
}}

// Initialize calendar when DOM is ready
function initSportCalendar() {{
    // Populate month dropdown
    const monthSelect = document.getElementById('month-select');
    if (monthSelect) {{
        monthSelect.innerHTML = '';
        sortedMonths.forEach(m => {{
            const [year, month] = m.split('-');
            const opt = document.createElement('option');
            opt.value = m;
            opt.textContent = `${{monthNames[parseInt(month) - 1]}} ${{year}}`;
            if (m === displayMonth) opt.selected = true;
            monthSelect.appendChild(opt);
        }});
        monthSelect.addEventListener('change', function() {{
            renderCalendar(this.value);
        }});
    }}

    // Initial render - show the current page's month
    renderCalendar(displayMonth);

    // Mobile archive dropdown
    const mobileSelect = document.getElementById('mobile-archive-select');
    if (mobileSelect) {{
        mobileSelect.innerHTML = '<option value="">Select a date...</option>';
        ARCHIVE_DATA.forEach(item => {{
            const opt = document.createElement('option');
            opt.value = item.page;
            const dateObj = new Date(item.date + 'T12:00:00');
            const dateLabel = dateObj.toLocaleDateString('en-US', {{ weekday: 'short', month: 'short', day: 'numeric' }});
            opt.textContent = `${{dateLabel}} - ${{item.title}}`;
            if (item.page === currentPage) opt.selected = true;
            mobileSelect.appendChild(opt);
        }});
        mobileSelect.addEventListener('change', (e) => {{
            if (e.target.value) window.location.href = e.target.value;
        }});
    }}
}}

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {{
    document.addEventListener('DOMContentLoaded', initSportCalendar);
}} else {{
    initSportCalendar();
}}
'''

# Archive data for each sport (extracted from the corrupted files)
ARCHIVE_DATA = {
    'nba': [
        { 'date': "2025-12-23", 'page': "nba.html", 'title': "NBA Analysis - December 22, 2025" },
        { 'date': "2025-12-23", 'page': "nba-page17.html", 'title': "NBA Analysis Archive - Page 17" },
        { 'date': "2025-12-21", 'page': "nba-page4.html", 'title': "NBA Analysis Archive - Page 4" },
        { 'date': "2025-12-21", 'page': "nba-page5.html", 'title': "NBA Analysis Archive - Page 5" },
        { 'date': "2025-12-21", 'page': "nba-page15.html", 'title': "NBA Analysis Archive - Page 15" },
        { 'date': "2025-12-20", 'page': "nba-page16.html", 'title': "NBA Analysis Archive - Page 16" },
        { 'date': "2025-12-19", 'page': "nba-page9.html", 'title': "NBA Analysis Archive - Page 11" },
        { 'date': "2025-12-18", 'page': "nba-page8.html", 'title': "NBA Analysis Archive - Page 10" },
        { 'date': "2025-12-17", 'page': "nba-page7.html", 'title': "NBA Preview - December 17, 2025" },
        { 'date': "2025-12-15", 'page': "nba-page2.html", 'title': "NBA Analysis - December 15, 2025" },
        { 'date': "2025-12-15", 'page': "nba-page6.html", 'title': "NBA Analysis - December 15, 2025" },
        { 'date': "2025-12-14", 'page': "nba-page14.html", 'title': "NBA Preview - December 14, 2025" },
        { 'date': "2025-12-13", 'page': "nba-page13.html", 'title': "NBA December 13, 2025 Preview" },
        { 'date': "2025-12-12", 'page': "nba-page12.html", 'title': "NBA December 12, 2025 Preview" },
        { 'date': "2025-12-11", 'page': "nba-page11.html", 'title': "NBA December 11, 2025 Preview" },
        { 'date': "2025-12-10", 'page': "nba-page10.html", 'title': "NBA December 10, 2025 Preview" },
        { 'date': "2025-11-24", 'page': "nba-page3.html", 'title': "NBA November 24, 2025 Preview" },
    ],
    'nfl': [
        { 'date': "2025-12-22", 'page': "nfl.html", 'title': "Monday Night Football - 49ers @ Colts" },
        { 'date': "2025-12-21", 'page': "nfl-page2.html", 'title': "NFL Week 16 Sunday" },
        { 'date': "2025-12-21", 'page': "nfl-page15.html", 'title': "NFL Analysis Archive - Page 15" },
        { 'date': "2025-12-21", 'page': "nfl-page16.html", 'title': "NFL Analysis Archive - Page 16" },
        { 'date': "2025-12-21", 'page': "nfl-page17.html", 'title': "NFL Analysis Archive - Page 17" },
        { 'date': "2025-12-13", 'page': "nfl-page11.html", 'title': "NFL Analysis Archive - Page 11" },
        { 'date': "2025-12-11", 'page': "nfl-page12.html", 'title': "NFL Analysis Archive - Page 12" },
        { 'date': "2025-12-07", 'page': "nfl-page13.html", 'title': "NFL Week 14 Preview - December 7, 2025" },
        { 'date': "2025-12-05", 'page': "nfl-page14.html", 'title': "NFL Week 14 TNF - December 5, 2025" },
        { 'date': "2025-11-30", 'page': "nfl-page10.html", 'title': "NFL Analysis Archive - Page 10" },
        { 'date': "2025-11-23", 'page': "nfl-page3.html", 'title': "NFL Analysis - Page 2" },
        { 'date': "2025-11-16", 'page': "nfl-page4.html", 'title': "NFL Analysis - Page 3" },
        { 'date': "2025-11-10", 'page': "nfl-page5.html", 'title': "NFL Analysis - Page 4" },
        { 'date': "2025-11-03", 'page': "nfl-page6.html", 'title': "NFL Analysis - Page 5" },
        { 'date': "2025-10-30", 'page': "nfl-page7.html", 'title': "NFL Analysis - Page 6" },
        { 'date': "2025-10-26", 'page': "nfl-page8.html", 'title': "NFL Analysis - Page 7" },
        { 'date': "2025-09-10", 'page': "nfl-page9.html", 'title': "NFL Analysis - Page 8" },
    ],
    'nhl': [
        { 'date': "2025-12-23", 'page': "nhl.html", 'title': "NHL Analysis - December 22, 2025" },
        { 'date': "2025-12-23", 'page': "nhl-page21.html", 'title': "NHL Analysis Archive - Page 21" },
        { 'date': "2025-12-22", 'page': "nhl-page18.html", 'title': "NHL Analysis Archive - Page 18" },
        { 'date': "2025-12-22", 'page': "nhl-page19.html", 'title': "NHL Analysis Archive - Page 19" },
        { 'date': "2025-12-22", 'page': "nhl-page20.html", 'title': "NHL Analysis Archive - Page 20" },
        { 'date': "2025-12-21", 'page': "nhl-page17.html", 'title': "NHL Analysis Archive - Page 17" },
        { 'date': "2025-12-20", 'page': "nhl-page3.html", 'title': "NHL Betting Archive - Page 15" },
        { 'date': "2025-12-19", 'page': "nhl-page9.html", 'title': "NHL Betting Archive - Page 9" },
        { 'date': "2025-12-19", 'page': "nhl-page11.html", 'title': "NHL Analysis Archive - Page 11" },
        { 'date': "2025-12-18", 'page': "nhl-page6.html", 'title': "NHL Betting Archive - Page 12" },
        { 'date': "2025-12-18", 'page': "nhl-page8.html", 'title': "NHL Analysis Archive - Page 8" },
        { 'date': "2025-12-17", 'page': "nhl-page5.html", 'title': "NHL Betting Archive - Page 13" },
        { 'date': "2025-12-17", 'page': "nhl-page7.html", 'title': "NHL Analysis Archive - Page 7" },
        { 'date': "2025-12-16", 'page': "nhl-page4.html", 'title': "NHL Analysis Archive - Page 4" },
        { 'date': "2025-12-15", 'page': "nhl-page2.html", 'title': "NHL Analysis - December 15, 2025" },
        { 'date': "2025-12-15", 'page': "nhl-page10.html", 'title': "NHL Analysis - December 15, 2025" },
        { 'date': "2025-12-14", 'page': "nhl-page12.html", 'title': "NHL Analysis Archive - Page 12" },
        { 'date': "2025-12-13", 'page': "nhl-page16.html", 'title': "NHL December 13, 2025" },
        { 'date': "2025-12-12", 'page': "nhl-page15.html", 'title': "NHL December 12, 2025" },
        { 'date': "2025-12-11", 'page': "nhl-page14.html", 'title': "NHL December 11, 2025" },
        { 'date': "2025-12-10", 'page': "nhl-page13.html", 'title': "NHL December 10, 2025" },
    ],
    'ncaab': [
        { 'date': "2025-12-23", 'page': "ncaab.html", 'title': "NCAAB Analysis - December 22, 2025" },
        { 'date': "2025-12-23", 'page': "ncaab-page20.html", 'title': "NCAAB Analysis Archive - Page 20" },
        { 'date': "2025-12-21", 'page': "ncaab-page17.html", 'title': "NCAAB Analysis Archive - Page 17" },
        { 'date': "2025-12-21", 'page': "ncaab-page18.html", 'title': "NCAAB Analysis Archive - Page 18" },
        { 'date': "2025-12-21", 'page': "ncaab-page19.html", 'title': "NCAAB Analysis Archive - Page 19" },
        { 'date': "2025-12-20", 'page': "ncaab-page16.html", 'title': "NCAAB Analysis Archive - Page 16" },
        { 'date': "2025-12-19", 'page': "ncaab-page4.html", 'title': "College Basketball Picks - Champions Classic 2025" },
        { 'date': "2025-12-19", 'page': "ncaab-page10.html", 'title': "NCAAB Analysis - December 19, 2025" },
        { 'date': "2025-12-18", 'page': "ncaab-page9.html", 'title': "NCAAB Analysis Archive - Page 9" },
        { 'date': "2025-12-17", 'page': "ncaab-page8.html", 'title': "NCAAB Analysis Archive - Page 8" },
        { 'date': "2025-12-16", 'page': "ncaab-page7.html", 'title': "NCAAB Analysis Archive - Page 7" },
        { 'date': "2025-12-15", 'page': "ncaab-page2.html", 'title': "NCAAB Analysis - December 15, 2025" },
        { 'date': "2025-12-15", 'page': "ncaab-page5.html", 'title': "NCAAB Analysis Archive - Page 5" },
        { 'date': "2025-12-15", 'page': "ncaab-page6.html", 'title': "NCAAB Analysis - December 15, 2025" },
        { 'date': "2025-12-11", 'page': "ncaab-page11.html", 'title': "NCAAB Analysis Archive - Page 11" },
        { 'date': "2025-12-09", 'page': "ncaab-page12.html", 'title': "NCAAB Analysis Archive - Page 12" },
        { 'date': "2025-12-07", 'page': "ncaab-page13.html", 'title': "NCAAB Analysis Archive - Page 13" },
        { 'date': "2025-12-05", 'page': "ncaab-page14.html", 'title': "NCAAB Analysis Archive - Page 14" },
        { 'date': "2025-12-03", 'page': "ncaab-page15.html", 'title': "NCAAB Analysis Archive - Page 15" },
        { 'date': "2025-11-27", 'page': "ncaab-page3.html", 'title': "College Basketball Picks - Thanksgiving Day, November 27, 2025" },
    ],
    'ncaaf': [
        { 'date': "2025-12-21", 'page': "ncaaf-page13.html", 'title': "NCAAF Analysis Archive - Page 13" },
        { 'date': "2025-12-20", 'page': "ncaaf.html", 'title': "NCAAF Analysis - December 22, 2025" },
        { 'date': "2025-12-20", 'page': "ncaaf-page4.html", 'title': "NCAAF Analysis Archive - Page 4" },
        { 'date': "2025-12-20", 'page': "ncaaf-page18.html", 'title': "NCAAF Analysis Archive - Page 18" },
        { 'date': "2025-12-20", 'page': "ncaaf-page19.html", 'title': "NCAAF Analysis Archive - Page 19" },
        { 'date': "2025-12-20", 'page': "ncaaf-page20.html", 'title': "NCAAF Analysis Archive - Page 20" },
        { 'date': "2025-12-19", 'page': "ncaaf-page10.html", 'title': "NCAAF Analysis Archive - Page 10" },
        { 'date': "2025-12-18", 'page': "ncaaf-page5.html", 'title': "NCAAF Analysis Archive - Page 5" },
        { 'date': "2025-12-17", 'page': "ncaaf-page6.html", 'title': "NCAAF Analysis Archive - Page 6" },
        { 'date': "2025-12-16", 'page': "ncaaf-page7.html", 'title': "NCAAF Analysis Archive - Page 7" },
        { 'date': "2025-12-15", 'page': "ncaaf-page9.html", 'title': "NCAAF Analysis - December 15, 2025" },
        { 'date': "2025-12-14", 'page': "ncaaf-page8.html", 'title': "NCAAF Analysis Archive - Page 8" },
        { 'date': "2025-12-13", 'page': "ncaaf-page11.html", 'title': "NCAAF Analysis Archive - Page 11" },
        { 'date': "2025-12-12", 'page': "ncaaf-page12.html", 'title': "NCAAF Analysis Archive - Page 12" },
        { 'date': "2025-12-10", 'page': "ncaaf-page14.html", 'title': "NCAAF Analysis - December 10, 2025" },
        { 'date': "2025-12-08", 'page': "ncaaf-page15.html", 'title': "NCAAF Analysis - December 8, 2025" },
        { 'date': "2025-12-06", 'page': "ncaaf-page16.html", 'title': "NCAAF Analysis - December 6, 2025" },
        { 'date': "2025-12-04", 'page': "ncaaf-page17.html", 'title': "NCAAF Analysis - December 4, 2025" },
        { 'date': "2025-11-28", 'page': "ncaaf-page2.html", 'title': "College Football Rivalry Week Nov 28 2025" },
        { 'date': "2025-11-01", 'page': "ncaaf-page3.html", 'title': "College Football Picks - Week 1, November 1, 2025" },
    ],
}

def generate_calendar_js(sport):
    """Generate clean calendar JS for a sport."""
    entries = ARCHIVE_DATA[sport]
    entries_str = ',\n    '.join([
        f'{{ date: "{e["date"]}", page: "{e["page"]}", title: "{e["title"]}" }}'
        for e in entries
    ])

    content = CALENDAR_TEMPLATE.format(
        SPORT_UPPER=sport.upper(),
        sport=sport,
        entries=entries_str
    )

    filepath = os.path.join(SCRIPTS_DIR, f'{sport}-calendar.js')
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'Regenerated {sport}-calendar.js')

def main():
    print('Regenerating all sport calendar JS files...\n')
    for sport in ARCHIVE_DATA:
        generate_calendar_js(sport)
    print('\nDone!')

if __name__ == '__main__':
    main()
