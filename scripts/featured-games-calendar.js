// Featured Games Calendar - RENDERING ENGINE ONLY
// Data comes from featured-games-data.js (loaded before this script)
// This file contains ONLY rendering logic - NO embedded data
// Last updated: February 16, 2026

// Read data from FEATURED_GAMES (defined by featured-games-data.js)
// Sort newest-first for display purposes
const ARCHIVE_DATA = (typeof FEATURED_GAMES !== 'undefined') ? [...FEATURED_GAMES].sort((a, b) => b.date.localeCompare(a.date)) : [];

// The newest entry is ALWAYS the active date in the calendar
// This ensures: add a new page -> calendar immediately shows that date
const newestDate = ARCHIVE_DATA.length > 0 ? ARCHIVE_DATA[0].date : null;

const dateMap = {};
ARCHIVE_DATA.forEach(item => { if (!dateMap[item.date]) dateMap[item.date] = item; });

const pageToDateMap = {};
ARCHIVE_DATA.forEach(item => { pageToDateMap[item.page] = item.date; });

const currentPage = window.location.pathname.split('/').pop().split('?')[0].split('#')[0] || 'index.html';

// The calendar ALWAYS highlights the newest entry in featured-games-data.js
// This way, whenever you add a new page, every calendar across the site
// immediately shows that new date as the active/highlighted one
const activeDate = newestDate;

// pageDate is the date of the specific page being viewed (for month display fallback)
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

// Calendar ALWAYS opens to the newest entry's month
let displayMonth;
if (newestDate) {
    const [ny, nm] = newestDate.split('-');
    displayMonth = ny + '-' + nm;
} else if (pageDate) {
    const [py, pm] = pageDate.split('-');
    displayMonth = py + '-' + pm;
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
        // Gold highlight = newest entry (the "current" featured game)
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
