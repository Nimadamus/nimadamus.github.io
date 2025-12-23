// NCAAB Archive Calendar Data - CENTRALIZED FILE
// All ncaab pages should reference this file for consistent calendar highlighting
// Last updated: December 23, 2025

const ARCHIVE_DATA = [
{ date: "2025-12-23", page: "ncaab.html", title: "NCAAB Analysis - December 23, 2025" },
    { date: "2025-12-23", page: "ncaab-page20.html", title: "NCAAB Analysis Archive - Page 20" },
    { date: "2025-12-21", page: "ncaab-page17.html", title: "NCAAB Analysis Archive - Page 17" },
    { date: "2025-12-21", page: "ncaab-page18.html", title: "NCAAB Analysis Archive - Page 18" },
    { date: "2025-12-21", page: "ncaab-page19.html", title: "NCAAB Analysis Archive - Page 19" },
    { date: "2025-12-20", page: "ncaab-page16.html", title: "NCAAB Analysis Archive - Page 16" },
    { date: "2025-12-19", page: "ncaab-page4.html", title: "College Basketball Picks - Champions Classic 2025" },
    { date: "2025-12-19", page: "ncaab-page10.html", title: "NCAAB Analysis - December 19, 2025" },
    { date: "2025-12-18", page: "ncaab-page9.html", title: "NCAAB Analysis Archive - Page 9" },
    { date: "2025-12-17", page: "ncaab-page8.html", title: "NCAAB Analysis Archive - Page 8" },
    { date: "2025-12-16", page: "ncaab-page7.html", title: "NCAAB Analysis Archive - Page 7" },
    { date: "2025-12-15", page: "ncaab-page2.html", title: "NCAAB Analysis - December 15, 2025" },
    { date: "2025-12-15", page: "ncaab-page5.html", title: "NCAAB Analysis Archive - Page 5" },
    { date: "2025-12-15", page: "ncaab-page6.html", title: "NCAAB Analysis - December 15, 2025" },
    { date: "2025-12-11", page: "ncaab-page11.html", title: "NCAAB Analysis Archive - Page 11" },
    { date: "2025-12-09", page: "ncaab-page12.html", title: "NCAAB Analysis Archive - Page 12" },
    { date: "2025-12-07", page: "ncaab-page13.html", title: "NCAAB Analysis Archive - Page 13" },
    { date: "2025-12-05", page: "ncaab-page14.html", title: "NCAAB Analysis Archive - Page 14" },
    { date: "2025-12-03", page: "ncaab-page15.html", title: "NCAAB Analysis Archive - Page 15" },
    { date: "2025-11-27", page: "ncaab-page3.html", title: "College Basketball Picks - Thanksgiving Day, November 27, 2025" }
];

// Build date map for quick lookups (first entry for each date wins for linking)
const dateMap = {};
ARCHIVE_DATA.forEach(item => {
    if (!dateMap[item.date]) {
        dateMap[item.date] = item;
    }
});

// Build page-to-date map (uses LAST/most recent date for pages with multiple entries)
const pageToDateMap = {};
ARCHIVE_DATA.forEach(item => {
    // Always overwrite - last entry wins (most recent date for pages with multiple dates)
    pageToDateMap[item.page] = item.date;
});

// Get current page filename and find its date
const currentPage = window.location.pathname.split('/').pop() || 'index.html';
const currentPageDate = pageToDateMap[currentPage] || null;

// Get available months from archive data
const months = new Set();
ARCHIVE_DATA.forEach(item => {
    const [y, m] = item.date.split('-');
    months.add(`${y}-${m}`);
});

// Add current month
const today = new Date();
const currentMonth = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}`;
const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;
months.add(currentMonth);

// Sort months descending (newest first)
const sortedMonths = Array.from(months).sort().reverse();

// Month names for display
const monthNames = ['January', 'February', 'March', 'April', 'May', 'June',
                    'July', 'August', 'September', 'October', 'November', 'December'];

// Determine which month to display - prefer the current page's month if available
let displayMonth = currentMonth;
if (currentPageDate) {
    const [pageYear, pageMonth] = currentPageDate.split('-');
    displayMonth = `${pageYear}-${pageMonth}`;
}

// Render calendar for a specific month
function renderCalendar(yearMonth) {
    const [year, month] = yearMonth.split('-').map(Number);
    const yearEl = document.getElementById('cal-year');
    if (yearEl) yearEl.textContent = year;

    const firstDay = new Date(year, month - 1, 1).getDay();
    const daysInMonth = new Date(year, month, 0).getDate();

    const container = document.getElementById('calendar-days');
    if (!container) return;
    container.innerHTML = '';

    // Empty cells before first day
    for (let i = 0; i < firstDay; i++) {
        const cell = document.createElement('div');
        cell.className = 'cal-day empty';
        container.appendChild(cell);
    }

    // Day cells
    for (let d = 1; d <= daysInMonth; d++) {
        const dateStr = `${year}-${String(month).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
        const hasData = dateMap[dateStr];
        let classes = 'cal-day';

        if (dateStr === todayStr) classes += ' today';
        if (dateStr === currentPageDate) classes += ' current-page';
        if (hasData) classes += ' has-content';

        const cell = document.createElement('div');
        cell.className = classes;
        cell.textContent = d;

        if (hasData) {
            cell.title = hasData.title;
            cell.onclick = () => window.location.href = hasData.page;
        }

        container.appendChild(cell);
    }
}

// Initialize calendar when DOM is ready
function initSportCalendar() {
    // Populate month dropdown
    const monthSelect = document.getElementById('month-select');
    if (monthSelect) {
        monthSelect.innerHTML = '';
        sortedMonths.forEach(m => {
            const [year, month] = m.split('-');
            const opt = document.createElement('option');
            opt.value = m;
            opt.textContent = `${monthNames[parseInt(month) - 1]} ${year}`;
            if (m === displayMonth) opt.selected = true;
            monthSelect.appendChild(opt);
        });
        monthSelect.addEventListener('change', function() {
            renderCalendar(this.value);
        });
    }

    // Initial render - show the current page's month
    renderCalendar(displayMonth);

    // Mobile archive dropdown
    const mobileSelect = document.getElementById('mobile-archive-select');
    if (mobileSelect) {
        mobileSelect.innerHTML = '<option value="">Select a date...</option>';
        ARCHIVE_DATA.forEach(item => {
            const opt = document.createElement('option');
            opt.value = item.page;
            const dateObj = new Date(item.date + 'T12:00:00');
            const dateLabel = dateObj.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
            opt.textContent = `${dateLabel} - ${item.title}`;
            if (item.page === currentPage) opt.selected = true;
            mobileSelect.appendChild(opt);
        });
        mobileSelect.addEventListener('change', (e) => {
            if (e.target.value) window.location.href = e.target.value;
        });
    }
}

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initSportCalendar);
} else {
    initSportCalendar();
}
