// Featured Games Calendar - RENDERING ENGINE ONLY
// Data comes from featured-games-data.js (loaded before this script)
// This file contains ONLY rendering logic - NO embedded data
// Last updated: February 16, 2026

// Read data from FEATURED_GAMES (defined by featured-games-data.js)
// Sort newest-first for display purposes
const ARCHIVE_DATA = (typeof FEATURED_GAMES !== 'undefined') ? [...FEATURED_GAMES].sort((a, b) => b.date.localeCompare(a.date)) : [];

// The newest entry is always the first item (sorted newest-first)
const newestDate = ARCHIVE_DATA.length > 0 ? ARCHIVE_DATA[0].date : null;

const dateMap = {};
ARCHIVE_DATA.forEach(item => { if (!dateMap[item.date]) dateMap[item.date] = item; });

const pageToDateMap = {};
ARCHIVE_DATA.forEach(item => { pageToDateMap[item.page] = item.date; });

const currentPage = window.location.pathname.split('/').pop().split('?')[0].split('#')[0] || 'index.html';

// PRIORITY: FORCED_PAGE_DATE > page lookup > title parsing > newest entry (NEVER browser date)
const currentPageDate = window.FORCED_PAGE_DATE || pageToDateMap[currentPage] || (function() {
    const title = document.title || '';
    const monthNames = ['January', 'February', 'March', 'April', 'May', 'June',
                        'July', 'August', 'September', 'October', 'November', 'December'];
    const dateMatch = title.match(/(\w+)\s+(\d{1,2}),?\s+(\d{4})/);
    if (dateMatch) {
        const monthStr = dateMatch[1];
        const day = parseInt(dateMatch[2]);
        const year = parseInt(dateMatch[3]);
        let monthIdx = monthNames.findIndex(m => m.toLowerCase().startsWith(monthStr.toLowerCase()));
        if (monthIdx !== -1) {
            return year + '-' + String(monthIdx + 1).padStart(2, '0') + '-' + String(day).padStart(2, '0');
        }
    }
    return null;
})() || newestDate;

// Auto-add current page to dateMap if not already there (makes it clickable)
if (currentPageDate && !dateMap[currentPageDate]) {
    dateMap[currentPageDate] = { date: currentPageDate, page: currentPage, title: document.title.split('|')[0].trim() };
}

const months = new Set();
ARCHIVE_DATA.forEach(item => { const [y, m] = item.date.split('-'); months.add(y + '-' + m); });
// Also add current page's month and newest entry's month
if (currentPageDate) { const [y, m] = currentPageDate.split('-'); months.add(y + '-' + m); }
if (newestDate) { const [y, m] = newestDate.split('-'); months.add(y + '-' + m); }

const sortedMonths = Array.from(months).sort().reverse();
const monthNames = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];

// ALWAYS show the page's date month - falls back to newest entry month (never browser date)
let displayMonth;
if (currentPageDate) {
    const [py, pm] = currentPageDate.split('-');
    displayMonth = py + '-' + pm;
} else if (newestDate) {
    const [ny, nm] = newestDate.split('-');
    displayMonth = ny + '-' + nm;
} else {
    const today = new Date();
    displayMonth = today.getFullYear() + '-' + String(today.getMonth() + 1).padStart(2, '0');
}

function initFeaturedGamesCalendar() {
    // Inject latest-entry CSS so all pages get it automatically
    if (!document.getElementById('latest-entry-style')) {
        const style = document.createElement('style');
        style.id = 'latest-entry-style';
        style.textContent = '.cal-day.latest-entry:not(.current-page){background:rgba(57,255,20,0.25)!important;color:#39FF14!important;font-weight:700;border:2px solid rgba(57,255,20,0.5)!important;animation:pulse-latest 2s ease-in-out infinite}@keyframes pulse-latest{0%,100%{box-shadow:0 0 4px rgba(57,255,20,0.3)}50%{box-shadow:0 0 12px rgba(57,255,20,0.6)}}';
        document.head.appendChild(style);
    }
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
        if (dateStr === currentPageDate) cell.classList.add('current-page');
        if (dateStr === newestDate) cell.classList.add('latest-entry');
        if (dateMap[dateStr]) {
            cell.classList.add('has-content');
            cell.title = dateMap[dateStr].title;
            cell.onclick = () => window.location.href = dateMap[dateStr].page;
        }
        container.appendChild(cell);
    }
}

if (document.readyState === 'loading') { document.addEventListener('DOMContentLoaded', initFeaturedGamesCalendar); } else { initFeaturedGamesCalendar(); }
