// Featured Games Calendar - RENDERING ENGINE ONLY
// Data comes from featured-games-data.js (loaded before this script)
// This file contains ONLY rendering logic - NO embedded data
// Last updated: March 6, 2026
//
// !! CRITICAL - DO NOT CHANGE THE activeDate LOGIC !!
// activeDate MUST equal: pageDate || newestDate
// This ensures the calendar highlights the page you're VIEWING.
// If you set activeDate = newestDate alone, the highlight will be
// stuck on the newest date no matter which page the user visits.
// The pre-commit hook enforces this. See March 6 2026 fix.

// Read data from FEATURED_GAMES (defined by featured-games-data.js)
// Sort newest-first for display purposes
const ARCHIVE_DATA = (typeof FEATURED_GAMES !== 'undefined') ? [...FEATURED_GAMES].sort((a, b) => b.date.localeCompare(a.date)) : [];

// newestDate = fallback for pages not in the calendar (homepage, sport pages)
const newestDate = ARCHIVE_DATA.length > 0 ? ARCHIVE_DATA[0].date : null;

const dateMap = {};
ARCHIVE_DATA.forEach(item => { if (!dateMap[item.date]) dateMap[item.date] = item; });

const pageToDateMap = {};
ARCHIVE_DATA.forEach(item => { pageToDateMap[item.page] = item.date; });

const currentPage = window.location.pathname.split('/').pop().split('?')[0].split('#')[0] || 'index.html';

// pageDate = the date of the specific page being viewed
const pageDate = window.FORCED_PAGE_DATE || pageToDateMap[currentPage] || (function() {
    const title = document.title || '';
    const mNames = ['January', 'February', 'March', 'April', 'May', 'June',
                    'July', 'August', 'September', 'October', 'November', 'December'];
    const dateMatch = title.match(/(\w+)\s+(\d{1,2}),?\s+(\d{4})/);
    if (dateMatch) {
        const monthStr = dateMatch[1];
        const day = parseInt(dateMatch[2]);
        const year = parseInt(dateMatch[3]);
        let monthIdx = mNames.findIndex(m => m.toLowerCase().startsWith(monthStr.toLowerCase()));
        if (monthIdx !== -1) {
            return year + '-' + String(monthIdx + 1).padStart(2, '0') + '-' + String(day).padStart(2, '0');
        }
    }
    return null;
})();

// Highlight the DATE OF THE PAGE YOU'RE ACTUALLY VIEWING
// If you're on a featured game page, highlight THAT date
// Only fall back to newest date on non-featured pages (homepage, sport pages, etc.)
const activeDate = pageDate || newestDate;

// Auto-add current page to dateMap if not already there
if (pageDate && !dateMap[pageDate]) {
    dateMap[pageDate] = { date: pageDate, page: currentPage, title: document.title.split('|')[0].trim() };
}

const months = new Set();
ARCHIVE_DATA.forEach(item => { const [y, m] = item.date.split('-'); months.add(y + '-' + m); });
if (pageDate) { const [y, m] = pageDate.split('-'); months.add(y + '-' + m); }
if (newestDate) { const [y, m] = newestDate.split('-'); months.add(y + '-' + m); }

const sortedMonths = Array.from(months).sort().reverse();
const monthNames = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];

// Calendar opens to the ACTIVE date's month (the page you're viewing)
// This ensures the highlighted day is always visible when the calendar loads
let displayMonth;
if (activeDate) {
    const [ay, am] = activeDate.split('-');
    displayMonth = ay + '-' + am;
} else if (newestDate) {
    const [ny, nm] = newestDate.split('-');
    displayMonth = ny + '-' + nm;
} else {
    const today = new Date();
    displayMonth = today.getFullYear() + '-' + String(today.getMonth() + 1).padStart(2, '0');
}

function initFeaturedGamesCalendar() {
    const monthSelect = document.getElementById('month-select');
    if (monthSelect) {
        monthSelect.innerHTML = '';
        sortedMonths.forEach(m => {
            const [year, month] = m.split('-');
            const opt = document.createElement('option');
            opt.value = m;
            opt.textContent = monthNames[parseInt(month) - 1] + ' ' + year;
            if (m === displayMonth) opt.selected = true;
            monthSelect.appendChild(opt);
        });
        monthSelect.addEventListener('change', function() { renderCalendar(this.value); });
    }
    renderCalendar(displayMonth);
}

function renderCalendar(yearMonth) {
    const [year, month] = yearMonth.split('-').map(Number);
    const yearEl = document.getElementById('cal-year');
    if (yearEl) yearEl.textContent = year;
    const firstDay = new Date(year, month - 1, 1).getDay();
    const daysInMonth = new Date(year, month, 0).getDate();
    const container = document.getElementById('calendar-days');
    if (!container) return;
    container.innerHTML = '';
    for (let i = 0; i < firstDay; i++) { const cell = document.createElement('div'); cell.className = 'cal-day empty'; container.appendChild(cell); }
    for (let d = 1; d <= daysInMonth; d++) {
        const dateStr = year + '-' + String(month).padStart(2, '0') + '-' + String(d).padStart(2, '0');
        const cell = document.createElement('div');
        cell.className = 'cal-day';
        cell.textContent = d;
        // Gold highlight = the page you're currently viewing (or newest if on homepage)
        if (dateStr === activeDate) cell.classList.add('current-page');
        if (dateMap[dateStr]) {
            cell.classList.add('has-content');
            cell.title = dateMap[dateStr].title;
            cell.onclick = () => window.location.href = dateMap[dateStr].page;
        }
        container.appendChild(cell);
    }
}

if (document.readyState === 'loading') { document.addEventListener('DOMContentLoaded', initFeaturedGamesCalendar); } else { initFeaturedGamesCalendar(); }
