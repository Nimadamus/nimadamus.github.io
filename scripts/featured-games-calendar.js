// Featured Games Archive Data - CENTRALIZED FILE
// All featured-game-of-the-day pages should reference this file
// Last updated: December 23, 2025

const ARCHIVE_DATA = [
    { date: "2025-12-23", page: "featured-game-of-the-day-page24.html", title: "Featured Game" },
    { date: "2025-12-22", page: "featured-game-of-the-day-page23.html", title: "Featured Game" },
    { date: "2025-12-21", page: "featured-game-of-the-day-page22.html", title: "Featured Game" },
    { date: "2025-12-19", page: "featured-game-of-the-day-page21.html", title: "Featured Game" },
    { date: "2025-12-18", page: "featured-game-of-the-day-page20.html", title: "Featured Game" },
    { date: "2025-12-17", page: "featured-game-of-the-day-page19.html", title: "Featured Game" },
    { date: "2025-12-13", page: "featured-game-of-the-day-page18.html", title: "Featured Game" },
    { date: "2025-12-11", page: "featured-game-of-the-day-page17.html", title: "Featured Game" },
    { date: "2025-12-10", page: "featured-game-of-the-day-page16.html", title: "Featured Game" },
    { date: "2025-12-08", page: "featured-game-of-the-day-page15.html", title: "Featured Game" },
    { date: "2025-12-07", page: "featured-game-of-the-day-page14.html", title: "Featured Game" },
    { date: "2025-12-06", page: "featured-game-of-the-day-page13.html", title: "Featured Game" },
    { date: "2025-12-04", page: "featured-game-of-the-day-page12.html", title: "Featured Game" },
    { date: "2025-12-03", page: "featured-game-of-the-day-page11.html", title: "Featured Game" },
    { date: "2025-12-01", page: "featured-game-of-the-day-page10.html", title: "Featured Game" },
    { date: "2025-11-30", page: "featured-game-of-the-day-page9.html", title: "Featured Game" },
    { date: "2025-11-29", page: "featured-game-of-the-day-page8.html", title: "Featured Game" },
    { date: "2025-11-27", page: "featured-game-of-the-day-page7.html", title: "Featured Game" },
    { date: "2025-11-26", page: "featured-game-of-the-day-page6.html", title: "Featured Game" },
    { date: "2025-11-25", page: "featured-game-of-the-day-page5.html", title: "Featured Game" },
    { date: "2025-11-24", page: "featured-game-of-the-day-page4.html", title: "Featured Game" },
    { date: "2025-11-23", page: "featured-game-of-the-day-page3.html", title: "Featured Game" },
    { date: "2025-11-22", page: "featured-game-of-the-day-page2.html", title: "Featured Game" },
    { date: "2025-11-19", page: "featured-game-of-the-day.html", title: "Featured Game" }
];

const dateMap = {};
ARCHIVE_DATA.forEach(item => { if (!dateMap[item.date]) dateMap[item.date] = item; });

const pageToDateMap = {};
ARCHIVE_DATA.forEach(item => { pageToDateMap[item.page] = item.date; });

const currentPage = window.location.pathname.split('/').pop() || 'index.html';
const currentPageDate = pageToDateMap[currentPage] || null;

const months = new Set();
ARCHIVE_DATA.forEach(item => { const [y, m] = item.date.split('-'); months.add(y + '-' + m); });

const today = new Date();
const currentMonth = today.getFullYear() + '-' + String(today.getMonth() + 1).padStart(2, '0');
const todayStr = today.getFullYear() + '-' + String(today.getMonth() + 1).padStart(2, '0') + '-' + String(today.getDate()).padStart(2, '0');
months.add(currentMonth);

const sortedMonths = Array.from(months).sort().reverse();
const monthNames = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];

let displayMonth = currentMonth;
if (currentPageDate) { const [py, pm] = currentPageDate.split('-'); displayMonth = py + '-' + pm; }

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
        if (dateStr === currentPageDate) cell.classList.add('current-page');
        if (dateMap[dateStr]) {
            cell.classList.add('has-content');
            cell.title = dateMap[dateStr].title;
            cell.onclick = () => window.location.href = dateMap[dateStr].page;
        }
        container.appendChild(cell);
    }
}

if (document.readyState === 'loading') { document.addEventListener('DOMContentLoaded', initFeaturedGamesCalendar); } else { initFeaturedGamesCalendar(); }
