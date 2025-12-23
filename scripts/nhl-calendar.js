// NHL Archive Calendar Data
// Last updated: December 23, 2025

const ARCHIVE_DATA = [
    { date: "2025-12-23", page: "nhl.html", title: "NHL Analysis - December 23, 2025" },
    { date: "2025-12-20", page: "nhl-page4.html", title: "NHL Analysis Archive - Page 4" },
    { date: "2025-12-20", page: "nhl-page7.html", title: "NHL Analysis Archive - Page 7" },
    { date: "2025-12-20", page: "nhl-page8.html", title: "NHL Analysis Archive - Page 8" },
    { date: "2025-12-20", page: "nhl-page9.html", title: "NHL Betting Archive - Page 9" },
    { date: "2025-12-20", page: "nhl-page11.html", title: "NHL Analysis Archive - Page 11" },
    { date: "2025-12-20", page: "nhl-page12.html", title: "NHL Analysis Archive - Page 12" },
    { date: "2025-12-20", page: "nhl-page17.html", title: "NHL Analysis Archive - Page 17" },
    { date: "2025-12-20", page: "nhl-page18.html", title: "NHL Analysis Archive - Page 18" },
    { date: "2025-12-20", page: "nhl-page19.html", title: "NHL Analysis Archive - Page 19" },
    { date: "2025-12-20", page: "nhl-page20.html", title: "NHL Analysis Archive - Page 20" },
    { date: "2025-12-20", page: "nhl-page21.html", title: "NHL Analysis Archive - Page 21" },
    { date: "2025-12-20", page: "nhl-page22.html", title: "NHL Analysis Archive - Page 22" },
    { date: "2025-12-18", page: "nhl-page6.html", title: "NHL December 18, 2025 - 8-Game Slate" },
    { date: "2025-12-17", page: "nhl-page5.html", title: "NHL December 17, 2025 - 4-Game Slate" },
    { date: "2025-12-15", page: "nhl-page2.html", title: "NHL Analysis - December 15, 2025" },
    { date: "2025-12-15", page: "nhl-page10.html", title: "NHL Analysis - December 15, 2025" },
    { date: "2025-12-13", page: "nhl-page16.html", title: "NHL December 13, 2025" },
    { date: "2025-12-12", page: "nhl-page15.html", title: "NHL December 12, 2025" },
    { date: "2025-12-11", page: "nhl-page14.html", title: "NHL December 11, 2025" },
    { date: "2025-12-10", page: "nhl-page13.html", title: "NHL December 10, 2025" },
    { date: "2025-11-24", page: "nhl-page3.html", title: "NHL November 24, 2025 - 7-Game Slate" }
];

const dateMap = {{}};
ARCHIVE_DATA.forEach(item => {{ if (!dateMap[item.date]) dateMap[item.date] = item; }});

const pageToDateMap = {{}};
ARCHIVE_DATA.forEach(item => {{ pageToDateMap[item.page] = item.date; }});

const currentPage = window.location.pathname.split('/').pop() || 'index.html';
const currentPageDate = pageToDateMap[currentPage] || null;

const months = new Set();
ARCHIVE_DATA.forEach(item => {{ const [y, m] = item.date.split('-'); months.add(y + '-' + m); }});

const today = new Date();
const currentMonth = today.getFullYear() + '-' + String(today.getMonth() + 1).padStart(2, '0');
const todayStr = today.getFullYear() + '-' + String(today.getMonth() + 1).padStart(2, '0') + '-' + String(today.getDate()).padStart(2, '0');
months.add(currentMonth);

const sortedMonths = Array.from(months).sort().reverse();
const monthNames = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];

let displayMonth = currentMonth;
if (currentPageDate) {{ const [py, pm] = currentPageDate.split('-'); displayMonth = py + '-' + pm; }}

function renderCalendar(yearMonth) {{
    const [year, month] = yearMonth.split('-').map(Number);
    const yearEl = document.getElementById('cal-year');
    if (yearEl) yearEl.textContent = year;
    const firstDay = new Date(year, month - 1, 1).getDay();
    const daysInMonth = new Date(year, month, 0).getDate();
    const container = document.getElementById('calendar-days');
    if (!container) return;
    container.innerHTML = '';
    for (let i = 0; i < firstDay; i++) {{ const cell = document.createElement('div'); cell.className = 'cal-day empty'; container.appendChild(cell); }}
    for (let d = 1; d <= daysInMonth; d++) {{
        const dateStr = year + '-' + String(month).padStart(2, '0') + '-' + String(d).padStart(2, '0');
        const hasData = dateMap[dateStr];
        let classes = 'cal-day';
        if (dateStr === todayStr) classes += ' today';
        if (dateStr === currentPageDate) classes += ' current-page';
        if (hasData) classes += ' has-content';
        const cell = document.createElement('div');
        cell.className = classes;
        cell.textContent = d;
        if (hasData) {{ cell.title = hasData.title; cell.onclick = () => window.location.href = hasData.page; }}
        container.appendChild(cell);
    }}
}}

function initSportCalendar() {{
    const monthSelect = document.getElementById('month-select');
    if (monthSelect) {{
        monthSelect.innerHTML = '';
        sortedMonths.forEach(m => {{
            const [year, month] = m.split('-');
            const opt = document.createElement('option');
            opt.value = m;
            opt.textContent = monthNames[parseInt(month) - 1] + ' ' + year;
            if (m === displayMonth) opt.selected = true;
            monthSelect.appendChild(opt);
        }});
        monthSelect.addEventListener('change', function() {{ renderCalendar(this.value); }});
    }}
    renderCalendar(displayMonth);
    const mobileSelect = document.getElementById('mobile-archive-select');
    if (mobileSelect) {{
        mobileSelect.innerHTML = '<option value="">Select a date...</option>';
        ARCHIVE_DATA.forEach(item => {{
            const opt = document.createElement('option');
            opt.value = item.page;
            const dateObj = new Date(item.date + 'T12:00:00');
            const dateLabel = dateObj.toLocaleDateString('en-US', {{ weekday: 'short', month: 'short', day: 'numeric' }});
            opt.textContent = dateLabel + ' - ' + item.title;
            if (item.page === currentPage) opt.selected = true;
            mobileSelect.appendChild(opt);
        }});
        mobileSelect.addEventListener('change', (e) => {{ if (e.target.value) window.location.href = e.target.value; }});
    }}
}}

if (document.readyState === 'loading') {{ document.addEventListener('DOMContentLoaded', initSportCalendar); }} else {{ initSportCalendar(); }}
