/*
 * verify_calendar_ux.js  —  DAILY CALENDAR UX VERIFICATION (mandatory SLATE step)
 *
 * Simulates the real user experience for EVERY sport calendar + the Featured
 * calendar in a headless browser against the LIVE site:
 *   1. renders the current month,
 *   2. confirms every date that exists in the calendar's data file renders as a
 *      clickable cell that has an onclick handler (no orphan/missing entries),
 *   3. clicks TODAY's date and confirms it navigates to exactly the page the
 *      data file maps that date to, and that the destination returns HTTP 200.
 *
 * Off-day / offseason sports (no entry for the current month, or no entry for
 * today) are reported as [SKIP], not failures.
 *
 * Usage:  node scripts/verify_calendar_ux.js [--base https://www.betlegendpicks.com/] [--date YYYY-MM-DD]
 * Exit 0 = all checks passed. Exit 1 = at least one failure.
 */
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const args = process.argv.slice(2);
function arg(flag, def) { const i = args.indexOf(flag); return i >= 0 && args[i + 1] ? args[i + 1] : def; }
const BASE = arg('--base', 'https://www.betlegendpicks.com/').replace(/\/?$/, '/');
const now = new Date();
const TODAY = arg('--date', `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`);
const MONTH = TODAY.slice(0, 7);
const TODAY_DAY = parseInt(TODAY.slice(8), 10);
const ROOT = path.resolve(__dirname, '..');

const TARGETS = [
  { name: 'NBA',     host: 'nba-previews.html',                 dataFile: 'scripts/nba-calendar.js',   engine: 'sport' },
  { name: 'NHL',     host: 'nhl-previews.html',                 dataFile: 'scripts/nhl-calendar.js',   engine: 'sport' },
  { name: 'MLB',     host: 'mlb-previews.html',                 dataFile: 'scripts/mlb-calendar.js',   engine: 'sport' },
  { name: 'Soccer',  host: 'soccer-previews.html',              dataFile: 'scripts/soccer-calendar.js',engine: 'sport' },
  { name: 'NCAAB',   host: 'college-basketball-previews.html',  dataFile: 'scripts/ncaab-calendar.js', engine: 'sport' },
  { name: 'NCAAF',   host: 'ncaaf.html',                        dataFile: 'scripts/ncaaf-calendar.js', engine: 'sport' },
  { name: 'NFL',     host: 'nfl.html',                          dataFile: 'scripts/nfl-calendar.js',   engine: 'sport' },
  { name: 'Featured',host: 'featured-game-of-the-day.html',     dataFile: 'featured-games-data.js',    engine: 'featured' },
];

function parseEntries(file) {
  const txt = fs.readFileSync(path.join(ROOT, file), 'utf8');
  const re = /date:\s*"([^"]+)"\s*,\s*page:\s*"([^"]+)"\s*,\s*title:\s*"((?:[^"\\]|\\.)*)"/g;
  const out = []; let m;
  while ((m = re.exec(txt)) !== null) out.push({ date: m[1], page: m[2], title: m[3] });
  return out;
}
// mirrors pickPrimaryPostForDate() in the sport calendar engines
function primaryForDate(entries, engine) {
  if (!entries.length) return null;
  if (engine === 'featured') return entries.slice().sort((a, b) => b.date.localeCompare(a.date))[0];
  const slate = entries.find(it => {
    const t = (it.title || '').toLowerCase(), p = (it.page || '').toLowerCase();
    return /\banalysis\b|\bpreview\b|\bslate\b|\bboard\b|\bfull card\b/.test(t) || /-game-|-slate-|-board-|-previews|full-card/.test(p);
  });
  return slate || entries[0];
}
const base = p => (p || '').split('/').pop().split('#')[0].split('?')[0];

(async () => {
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport: { width: 1700, height: 1200 } });
  let failures = 0;
  console.log(`Calendar UX verification  |  base=${BASE}  today=${TODAY}`);

  for (const t of TARGETS) {
    console.log(`\n=== ${t.name}  (host: ${t.host}, data: ${t.dataFile})`);
    const entries = parseEntries(t.dataFile);
    const monthEntries = entries.filter(e => e.date.startsWith(MONTH));
    const monthDays = [...new Set(monthEntries.map(e => parseInt(e.date.slice(8), 10)))].sort((a, b) => a - b);
    const page = await ctx.newPage();
    try {
      await page.goto(BASE + t.host, { waitUntil: 'networkidle', timeout: 45000 });
      // featured hub redirects to newest dated page; let it settle
      await page.waitForTimeout(800);
      const hasCal = await page.$('#calendar-days');
      if (!hasCal) { console.log('  [FAIL] no #calendar-days container on rendered page'); failures++; await page.close(); continue; }

      await page.evaluate((mo) => {
        const sel = document.getElementById('month-select');
        if (sel) {
          if (![...sel.options].some(o => o.value === mo)) { const o = document.createElement('option'); o.value = mo; o.text = mo; sel.appendChild(o); }
          sel.value = mo; sel.dispatchEvent(new Event('change'));
        }
      }, MONTH);
      await page.waitForTimeout(400);

      const cells = await page.evaluate(() => [...document.querySelectorAll('#calendar-days .cal-day')].map(c => ({
        day: /^\d+$/.test(c.textContent.trim()) ? parseInt(c.textContent.trim(), 10) : null,
        cls: c.className,
        clickable: c.className.includes('has-content') || c.className.includes('is-linked'),
        hasOnclick: typeof c.onclick === 'function',
      })));
      const clickableDays = cells.filter(c => c.day && c.clickable && c.hasOnclick).map(c => c.day).sort((a, b) => a - b);

      if (monthDays.length === 0) { console.log(`  [SKIP] no ${MONTH} entries (off-season / off-month)`); await page.close(); continue; }

      // (2) every data date in this month must be clickable
      const missing = monthDays.filter(d => !clickableDays.includes(d));
      console.log(`  ${MONTH} entries in data: ${monthDays.length} -> ${monthDays.join(', ')}`);
      console.log(`  ${MONTH} clickable cells: ${clickableDays.length} -> ${clickableDays.join(', ')}`);
      if (missing.length) { console.log(`  [FAIL] data dates with NO clickable cell: ${missing.join(', ')}`); failures++; }
      else console.log('  [OK] every data entry this month renders clickable with onclick');

      // (3) click test — today if it has an entry, else newest day in the month
      const clickDay = monthDays.includes(TODAY_DAY) ? TODAY_DAY : monthDays[monthDays.length - 1];
      const note = clickDay === TODAY_DAY ? `today (June ${TODAY_DAY})` : `June ${clickDay} (today is an off-day for ${t.name})`;
      const dayEntries = monthEntries.filter(e => parseInt(e.date.slice(8), 10) === clickDay);
      const expected = base(primaryForDate(dayEntries, t.engine).page);
      const clicked = await page.evaluate((day) => {
        const c = [...document.querySelectorAll('#calendar-days .cal-day.has-content')].find(x => parseInt(x.textContent.trim(), 10) === day);
        if (!c || typeof c.onclick !== 'function') return false;
        c.click(); return true;
      }, clickDay);
      if (!clicked) { console.log(`  [FAIL] could not click ${note}`); failures++; }
      else {
        await page.waitForLoadState('domcontentloaded', { timeout: 20000 }).catch(() => {});
        await page.waitForTimeout(900);
        const destFile = base(page.url());
        const resp = await ctx.request.get(page.url());
        console.log(`  click ${note} -> ${destFile}  (expected ${expected}, HTTP ${resp.status()})`);
        if (destFile === expected && resp.status() === 200) console.log('  [OK] navigates to the correct mapped page, live 200');
        else { console.log(`  [FAIL] wrong destination or non-200`); failures++; }
      }
    } catch (e) {
      console.log(`  [FAIL] ${t.name} threw: ${e.message}`); failures++;
    } finally {
      await page.close();
    }
  }

  await browser.close();
  console.log('\n=====================================');
  console.log(failures === 0 ? 'ALL CALENDAR UX CHECKS PASSED' : `${failures} CHECK(S) FAILED`);
  console.log('=====================================');
  process.exit(failures === 0 ? 0 : 1);
})();
