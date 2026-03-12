// Featured Games Calendar - RENDERING ENGINE ONLY
// Data comes from featured-games-data.js (loaded before this script)
// This file contains ONLY rendering logic - NO embedded data
// Last updated: March 11, 2026 - Added dynamic data refresh to prevent stale cache issues
//
// !! CRITICAL - DO NOT CHANGE THE activeDate LOGIC !!
// activeDate MUST equal: pageDate || newestDate
// This ensures the calendar highlights the page you're VIEWING.
// If you set activeDate = newestDate alone, the highlight will be
// stuck on the newest date no matter which page the user visits.
// The pre-commit hook enforces this. See March 6 2026 fix.
//
// CACHE FIX (March 11, 2026):
// After the initial render (from whatever data the browser has cached),
// this script dynamically reloads featured-games-data.js with a timestamp
// cache buster. If the fresh data has new entries, the calendar re-renders
// automatically. This eliminates stale cache issues permanently.
// Static cache-busting params (?v=dataXXX) have been removed from all pages.

function buildCalendarState() {
    // Read data from FEATURED_GAMES (defined by featured-games-data.js)
    // Sort newest-first for display purposes
    var archiveData = (typeof FEATURED_GAMES !== 'undefined') ? FEATURED_GAMES.slice().sort(function(a, b) { return b.date.localeCompare(a.date); }) : [];

    var newestDate = archiveData.length > 0 ? archiveData[0].date : null;

    var dateMap = {};
    archiveData.forEach(function(item) { if (!dateMap[item.date]) dateMap[item.date] = item; });

    var pageToDateMap = {};
    archiveData.forEach(function(item) { pageToDateMap[item.page] = item.date; });

    var currentPage = window.location.pathname.split('/').pop().split('?')[0].split('#')[0] || 'index.html';

    // pageDate = the date of the specific page being viewed
    var pageDate = window.FORCED_PAGE_DATE || pageToDateMap[currentPage] || (function() {
        var title = document.title || '';
        var mNames = ['January', 'February', 'March', 'April', 'May', 'June',
                        'July', 'August', 'September', 'October', 'November', 'December'];
        var dateMatch = title.match(/(\w+)\s+(\d{1,2}),?\s+(\d{4})/);
        if (dateMatch) {
            var monthStr = dateMatch[1];
            var day = parseInt(dateMatch[2]);
            var year = parseInt(dateMatch[3]);
            var monthIdx = -1;
            for (var i = 0; i < mNames.length; i++) {
                if (mNames[i].toLowerCase().indexOf(monthStr.toLowerCase()) === 0) { monthIdx = i; break; }
            }
            if (monthIdx !== -1) {
                return year + '-' + String(monthIdx + 1).padStart(2, '0') + '-' + String(day).padStart(2, '0');
            }
        }
        return null;
    })();

    // Highlight the DATE OF THE PAGE YOU'RE ACTUALLY VIEWING
    var activeDate = pageDate || newestDate;

    // Auto-add current page to dateMap if not already there
    if (pageDate && !dateMap[pageDate]) {
        dateMap[pageDate] = { date: pageDate, page: currentPage, title: document.title.split('|')[0].trim() };
    }

    var months = {};
    archiveData.forEach(function(item) { var parts = item.date.split('-'); months[parts[0] + '-' + parts[1]] = true; });
    if (pageDate) { var p = pageDate.split('-'); months[p[0] + '-' + p[1]] = true; }
    if (newestDate) { var n = newestDate.split('-'); months[n[0] + '-' + n[1]] = true; }

    var sortedMonths = Object.keys(months).sort().reverse();
    var monthNames = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];

    // Calendar opens to the ACTIVE date's month
    var displayMonth;
    if (activeDate) {
        var ap = activeDate.split('-');
        displayMonth = ap[0] + '-' + ap[1];
    } else if (newestDate) {
        var np = newestDate.split('-');
        displayMonth = np[0] + '-' + np[1];
    } else {
        var today = new Date();
        displayMonth = today.getFullYear() + '-' + String(today.getMonth() + 1).padStart(2, '0');
    }

    return {
        archiveData: archiveData,
        newestDate: newestDate,
        dateMap: dateMap,
        pageDate: pageDate,
        activeDate: activeDate,
        sortedMonths: sortedMonths,
        monthNames: monthNames,
        displayMonth: displayMonth
    };
}

var _calState = buildCalendarState();

function initFeaturedGamesCalendar() {
    var state = _calState;
    var monthSelect = document.getElementById('month-select');
    if (monthSelect) {
        monthSelect.innerHTML = '';
        state.sortedMonths.forEach(function(m) {
            var parts = m.split('-');
            var opt = document.createElement('option');
            opt.value = m;
            opt.textContent = state.monthNames[parseInt(parts[1]) - 1] + ' ' + parts[0];
            if (m === state.displayMonth) opt.selected = true;
            monthSelect.appendChild(opt);
        });
        monthSelect.addEventListener('change', function() { renderCalendar(this.value); });
    }
    renderCalendar(state.displayMonth);
}

function renderCalendar(yearMonth) {
    var state = _calState;
    var parts = yearMonth.split('-');
    var year = parseInt(parts[0]);
    var month = parseInt(parts[1]);
    var yearEl = document.getElementById('cal-year');
    if (yearEl) yearEl.textContent = year;
    var firstDay = new Date(year, month - 1, 1).getDay();
    var daysInMonth = new Date(year, month, 0).getDate();
    var container = document.getElementById('calendar-days');
    if (!container) return;
    container.innerHTML = '';
    for (var i = 0; i < firstDay; i++) { var cell = document.createElement('div'); cell.className = 'cal-day empty'; container.appendChild(cell); }
    for (var d = 1; d <= daysInMonth; d++) {
        var dateStr = year + '-' + String(month).padStart(2, '0') + '-' + String(d).padStart(2, '0');
        var cell = document.createElement('div');
        cell.className = 'cal-day';
        cell.textContent = d;
        // Gold highlight = the page you're currently viewing (or newest if on homepage)
        if (dateStr === state.activeDate) cell.classList.add('current-page');
        if (state.dateMap[dateStr]) {
            cell.classList.add('has-content');
            cell.title = state.dateMap[dateStr].title;
            (function(page) {
                cell.onclick = function() { window.location.href = page; };
            })(state.dateMap[dateStr].page);
        }
        container.appendChild(cell);
    }
}

if (document.readyState === 'loading') { document.addEventListener('DOMContentLoaded', initFeaturedGamesCalendar); } else { initFeaturedGamesCalendar(); }

// DYNAMIC DATA REFRESH - Prevents stale cache issues permanently
// After the initial render, dynamically reload featured-games-data.js with a
// timestamp cache buster. If the data has changed in ANY way, re-render.
// We fingerprint the data (count + newest date + newest page) so changes
// are detected even when the entry count stays the same.
(function() {
    function dataFingerprint() {
        if (typeof FEATURED_GAMES === 'undefined' || !FEATURED_GAMES.length) return '';
        var sorted = FEATURED_GAMES.slice().sort(function(a, b) { return b.date.localeCompare(a.date); });
        return FEATURED_GAMES.length + '|' + sorted[0].date + '|' + sorted[0].page;
    }
    var initialFingerprint = dataFingerprint();
    var script = document.createElement('script');
    script.src = 'featured-games-data.js?_=' + Date.now();
    script.onload = function() {
        if (dataFingerprint() !== initialFingerprint) {
            // Data changed - rebuild state and re-render
            _calState = buildCalendarState();
            initFeaturedGamesCalendar();
        }
    };
    document.head.appendChild(script);
})();
