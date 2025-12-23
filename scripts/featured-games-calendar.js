// Featured Games Archive Data - CENTRALIZED FILE
// All featured-game-of-the-day pages should reference this file for consistent calendar highlighting
// Last updated: December 23, 2025

const ARCHIVE_DATA = [
    { date: "2025-10-25", page: "featured-game-of-the-day.html", title: "Archive" },
    { date: "2025-10-29", page: "featured-game-of-the-day.html", title: "Archive" },
    { date: "2025-10-30", page: "featured-game-of-the-day.html", title: "Archive" },
    { date: "2025-10-31", page: "featured-game-of-the-day.html", title: "Archive" },
    { date: "2025-11-01", page: "featured-game-of-the-day.html", title: "Vanderbilt @ Texas" },
    { date: "2025-11-03", page: "featured-game-of-the-day.html", title: "Evening Slate" },
    { date: "2025-11-05", page: "featured-game-of-the-day.html", title: "NHL Game" },
    { date: "2025-11-06", page: "featured-game-of-the-day.html", title: "NHL Analysis" },
    { date: "2025-11-07", page: "featured-game-of-the-day.html", title: "USC Game" },
    { date: "2025-11-09", page: "featured-game-of-the-day.html", title: "49ers Game" },
    { date: "2025-11-11", page: "featured-game-of-the-day.html", title: "Avalanche Game" },
    { date: "2025-11-12", page: "featured-game-of-the-day.html", title: "NHL Tampa" },
    { date: "2025-11-13", page: "featured-game-of-the-day.html", title: "Jets vs Patriots TNF" },
    { date: "2025-11-15", page: "featured-game-of-the-day.html", title: "Alabama Game" },
    { date: "2025-11-16", page: "featured-game-of-the-day.html", title: "Seahawks @ Rams" },
    { date: "2025-11-17", page: "featured-game-of-the-day.html", title: "MNF" },
    { date: "2025-11-19", page: "featured-game-of-the-day.html", title: "Wild Game" },
    { date: "2025-11-21", page: "featured-game-of-the-day.html", title: "Archive" },
    { date: "2025-11-22", page: "featured-game-of-the-day-page2.html", title: "USC vs Oregon" },
    { date: "2025-11-23", page: "featured-game-of-the-day-page3.html", title: "Rams vs Buccaneers SNF" },
    { date: "2025-11-24", page: "featured-game-of-the-day-page4.html", title: "Panthers vs 49ers MNF" },
    { date: "2025-11-25", page: "featured-game-of-the-day-page5.html", title: "Clippers vs Lakers" },
    { date: "2025-11-26", page: "featured-game-of-the-day-page6.html", title: "Rockets vs Warriors" },
    { date: "2025-11-27", page: "featured-game-of-the-day-page7.html", title: "Steelers vs Browns" },
    { date: "2025-11-29", page: "featured-game-of-the-day-page8.html", title: "Vanderbilt vs Tennessee" },
    { date: "2025-11-30", page: "featured-game-of-the-day-page9.html", title: "Texans vs Colts" },
    { date: "2025-12-01", page: "featured-game-of-the-day-page10.html", title: "Giants vs Patriots MNF" },
    { date: "2025-12-03", page: "featured-game-of-the-day-page11.html", title: "Pistons vs Bucks" },
    { date: "2025-12-04", page: "featured-game-of-the-day-page12.html", title: "Cowboys vs Lions TNF" },
    { date: "2025-12-06", page: "featured-game-of-the-day-page13.html", title: "Georgia vs Alabama SEC" },
    { date: "2025-12-07", page: "featured-game-of-the-day-page14.html", title: "Bengals vs Bills" },
    { date: "2025-12-08", page: "featured-game-of-the-day-page15.html", title: "Eagles vs Chargers MNF" },
    { date: "2025-12-10", page: "featured-game-of-the-day-page16.html", title: "Lakers vs Spurs NBA Cup" },
    { date: "2025-12-11", page: "featured-game-of-the-day-page17.html", title: "Falcons vs Buccaneers TNF" },
    { date: "2025-12-13", page: "featured-game-of-the-day-page18.html", title: "Army vs Navy" },
    { date: "2025-12-17", page: "featured-game-of-the-day-page19.html", title: "USF vs Old Dominion" },
    { date: "2025-12-18", page: "featured-game-of-the-day-page20.html", title: "Stars vs Sharks" },
    { date: "2025-12-19", page: "featured-game-of-the-day-page21.html", title: "Alabama vs Oklahoma CFP" },
    { date: "2025-12-21", page: "featured-game-of-the-day-page22.html", title: "Buccaneers vs Panthers" },
    { date: "2025-12-22", page: "featured-game-of-the-day-page23.html", title: "49ers vs Colts MNF" },
    { date: "2025-12-23", page: "featured-game-of-the-day-page24.html", title: "WKU vs Southern Miss" }
];

// Build date map for quick lookups
const dateMap = {};
ARCHIVE_DATA.forEach(item => { dateMap[item.date] = item; });

// Build page-to-date map (uses LAST/most recent matching date for pages with multiple entries)
const pageToDateMap = {};
ARCHIVE_DATA.forEach(item => {
    // Always overwrite - last entry wins (most recent date for pages with multiple dates)
    pageToDateMap[item.page] = item.date;
});

// Get current page filename and find its date
const currentPage = window.location.pathname.split('/').pop() || 'index.html';
let currentPageDate = pageToDateMap[currentPage] || null;

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

// Initialize calendar when DOM is ready
function initFeaturedGamesCalendar() {
    // Populate month dropdown
    const monthSelect = document.getElementById('month-select');
    if (monthSelect) {
        monthSelect.innerHTML = ''; // Clear any existing options
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

    // Initial render
    renderCalendar(displayMonth);
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
        const cell = document.createElement('div');
        cell.className = 'cal-day';
        cell.textContent = d;

        // Highlight current page's date with gold
        if (dateStr === currentPageDate) {
            cell.classList.add('current-page');
        }

        // Add clickable styling for days with content
        if (dateMap[dateStr]) {
            cell.classList.add('has-content');
            cell.title = dateMap[dateStr].title;
            cell.onclick = () => window.location.href = dateMap[dateStr].page;
        }

        container.appendChild(cell);
    }
}

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initFeaturedGamesCalendar);
} else {
    initFeaturedGamesCalendar();
}
