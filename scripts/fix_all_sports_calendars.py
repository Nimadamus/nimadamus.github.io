"""
Fix calendar highlighting for ALL sports pages.
Creates centralized JS files and updates all pages to use them.
"""

import os
import re
import glob

REPO = r'C:\Users\Nima\nimadamus.github.io'
SCRIPTS_DIR = os.path.join(REPO, 'scripts')

# Sports to process
SPORTS = ['nba', 'nfl', 'nhl', 'ncaab', 'ncaaf']

def extract_archive_data(content):
    """Extract ARCHIVE_DATA from page content."""
    match = re.search(r'const ARCHIVE_DATA = \[([\s\S]*?)\];', content)
    if match:
        return match.group(0)
    return None

def get_archive_entries(content):
    """Parse ARCHIVE_DATA and return list of entries."""
    entries = []
    pattern = r'\{\s*date:\s*["\']([^"\']+)["\'],\s*page:\s*["\']([^"\']+)["\'],\s*title:\s*["\']([^"\']+)["\']\s*\}'
    for match in re.finditer(pattern, content):
        entries.append({
            'date': match.group(1),
            'page': match.group(2),
            'title': match.group(3)
        })
    return entries

def create_sport_calendar_js(sport, entries):
    """Create centralized calendar JS for a sport."""

    # Format entries as JavaScript
    entries_js = ',\n    '.join([
        f'{{ date: "{e["date"]}", page: "{e["page"]}", title: "{e["title"]}" }}'
        for e in entries
    ])

    js_content = f'''// {sport.upper()} Archive Calendar Data - CENTRALIZED FILE
// All {sport} pages should reference this file for consistent calendar highlighting
// Last updated: December 22, 2025

const ARCHIVE_DATA = [
    {entries_js}
];

// Build date map for quick lookups (first entry for each date wins for linking)
const dateMap = {{}};
ARCHIVE_DATA.forEach(item => {{
    if (!dateMap[item.date]) {{
        dateMap[item.date] = item;
    }}
}});

// Build page-to-date map - CRITICAL for correct highlighting
// Each page gets its FIRST matching date
const pageToDateMap = {{}};
ARCHIVE_DATA.forEach(item => {{
    if (!pageToDateMap[item.page]) {{
        pageToDateMap[item.page] = item.date;
    }}
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
    return js_content

def update_page_to_use_shared_js(filepath, sport):
    """Update a page to use the centralized calendar JS."""
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    original = content
    script_ref = f'<script src="scripts/{sport}-calendar.js"></script>'

    # Check if already using the new script
    if f'scripts/{sport}-calendar.js' in content:
        return 'skip'

    # Find the calendar script section - matches from ARCHIVE_DATA to end of script
    # Pattern 1: Matches the full calendar script block
    patterns = [
        # Pattern for script starting with comment
        re.compile(
            r'<script>\s*\n?'
            r'//[^\n]*Archive[^\n]*\n'
            r'const ARCHIVE_DATA = \[[\s\S]*?'
            r'</script>',
            re.MULTILINE
        ),
        # Pattern for script starting directly with const
        re.compile(
            r'<script>\s*\n?'
            r'const ARCHIVE_DATA = \[[\s\S]*?'
            r'</script>',
            re.MULTILINE
        ),
    ]

    replaced = False
    for pattern in patterns:
        if pattern.search(content):
            content = pattern.sub(script_ref, content)
            replaced = True
            break

    if not replaced:
        # Try manual find/replace
        if 'const ARCHIVE_DATA = [' in content:
            # Find script containing ARCHIVE_DATA
            start_markers = [
                '<script>\n// ' + sport.upper(),
                '<script>\nconst ARCHIVE_DATA',
                '<script>const ARCHIVE_DATA',
            ]

            for marker in start_markers:
                idx = content.find(marker)
                if idx == -1:
                    idx = content.lower().find(marker.lower())
                if idx != -1:
                    # Find the actual <script> tag
                    script_start = content.rfind('<script>', 0, idx + len(marker))
                    if script_start == -1:
                        script_start = idx

                    # Find corresponding </script>
                    remaining = content[script_start:]
                    # Count script tags to find the right closing one
                    depth = 0
                    end_idx = -1
                    i = 0
                    while i < len(remaining):
                        if remaining[i:i+8] == '<script>':
                            depth += 1
                            i += 8
                        elif remaining[i:i+9] == '</script>':
                            depth -= 1
                            if depth == 0:
                                end_idx = i + 9
                                break
                            i += 9
                        else:
                            i += 1

                    if end_idx != -1:
                        old_script = remaining[:end_idx]
                        # Verify this is the calendar script
                        if 'ARCHIVE_DATA' in old_script and 'renderCalendar' in old_script:
                            content = content[:script_start] + script_ref + content[script_start + end_idx:]
                            replaced = True
                            break

    if content != original and replaced:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return 'updated'
    elif replaced:
        return 'no_change'
    else:
        return 'failed'

def process_sport(sport):
    """Process all pages for a sport."""
    print(f'\n{"="*60}')
    print(f'Processing {sport.upper()}')
    print(f'{"="*60}')

    # Find all pages for this sport
    main_page = os.path.join(REPO, f'{sport}.html')
    archive_pages = glob.glob(os.path.join(REPO, f'{sport}-page*.html'))
    all_pages = [main_page] + sorted(archive_pages)

    print(f'Found {len(all_pages)} {sport} pages')

    # Extract ARCHIVE_DATA from main page
    if not os.path.exists(main_page):
        print(f'  ERROR: Main page {sport}.html not found!')
        return

    with open(main_page, 'r', encoding='utf-8', errors='ignore') as f:
        main_content = f.read()

    entries = get_archive_entries(main_content)
    if not entries:
        print(f'  ERROR: Could not extract ARCHIVE_DATA from {sport}.html')
        return

    print(f'  Found {len(entries)} archive entries')

    # Create centralized JS file
    js_content = create_sport_calendar_js(sport, entries)
    js_path = os.path.join(SCRIPTS_DIR, f'{sport}-calendar.js')
    with open(js_path, 'w', encoding='utf-8') as f:
        f.write(js_content)
    print(f'  Created {sport}-calendar.js')

    # Update all pages
    updated = 0
    skipped = 0
    failed = 0

    for page in all_pages:
        result = update_page_to_use_shared_js(page, sport)
        basename = os.path.basename(page)
        if result == 'updated':
            print(f'    UPDATED: {basename}')
            updated += 1
        elif result == 'skip':
            print(f'    SKIP: {basename} (already done)')
            skipped += 1
        else:
            print(f'    FAILED: {basename}')
            failed += 1

    print(f'\n  Summary for {sport.upper()}:')
    print(f'    Updated: {updated}')
    print(f'    Skipped: {skipped}')
    print(f'    Failed: {failed}')

    return updated, skipped, failed

def main():
    print('='*60)
    print('FIXING CALENDAR HIGHLIGHTING FOR ALL SPORTS')
    print('='*60)

    total_updated = 0
    total_skipped = 0
    total_failed = 0

    for sport in SPORTS:
        result = process_sport(sport)
        if result:
            updated, skipped, failed = result
            total_updated += updated
            total_skipped += skipped
            total_failed += failed

    print('\n' + '='*60)
    print('OVERALL SUMMARY')
    print('='*60)
    print(f'Total Updated: {total_updated}')
    print(f'Total Skipped: {total_skipped}')
    print(f'Total Failed: {total_failed}')

if __name__ == '__main__':
    main()
