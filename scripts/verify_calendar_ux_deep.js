/*
 * verify_calendar_ux_deep.js — FULL calendar user-experience simulation.
 *
 * Goes beyond verify_calendar_ux.js (which click-tests today only):
 *   For the Featured calendar + EVERY sport calendar, for EVERY date that the
 *   calendar data maps in the checked month range, this script:
 *     1. renders the month on the live host page,
 *     2. confirms the date cell is clickable with an onclick handler,
 *     3. CLICKS it like a user and confirms the browser lands on exactly the
 *        page the data file maps for that date, live HTTP 200,
 *     4. on the destination page confirms the article actually rendered:
 *        a real <h1>/hero title with text, page body substantial,
 *     5. checks the rendered title is NOT clipped/overflowing its container
 *        at desktop (1700px) AND mobile (390px) widths — catches the
 *        "title too long / partially hidden" failure class,
 *     6. checks document.title length (warn > 65 chars, the news-validator gate).
 *
 * Usage: node scripts/verify_calendar_ux_deep.js [--base URL] [--months N] [--date YYYY-MM-DD]
 *   --months N  how many months to walk back from the current month (default 1 = current only)
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
const MONTHS_BACK = parseInt(arg('--months', '1'), 10);
const ROOT = path.resolve(__dirname, '..');

const TARGETS = [
  { name: 'NBA',      host: 'nba-previews.html',                dataFile: 'scripts/nba-calendar.js',    engine: 'sport' },
  { name: 'NHL',      host: 'nhl-previews.html',                dataFile: 'scripts/nhl-calendar.js',    engine: 'sport' },
  { name: 'MLB',      host: 'mlb-previews.html',                dataFile: 'scripts/mlb-calendar.js',    engine: 'sport' },
  { name: 'Soccer',   host: 'soccer-previews.html',             dataFile: 'scripts/soccer-calendar.js', engine: 'sport' },
  { name: 'NCAAB',    host: 'college-basketball-previews.html', dataFile: 'scripts/ncaab-calendar.js',  engine: 'sport' },
  { name: 'NCAAF',    host: 'ncaaf.html',                       dataFile: 'scripts/ncaaf-calendar.js',  engine: 'sport' },
  { name: 'NFL',      host: 'nfl.html',                         dataFile: 'scripts/nfl-calendar.js',    engine: 'sport' },
  { name: 'Featured', host: 'featured-game-of-the-day.html',    dataFile: 'featured-games-data.js',     engine: 'featured' },
];

function monthsToCheck() {
  const out = [];
  const [y, m] = [parseInt(TODAY.slice(0, 4), 10), parseInt(TODAY.slice(5, 7), 10)];
  for (let i = 0; i < MONTHS_BACK; i++) {
    const d = new Date(y, m - 1 - i, 1);
    out.push(`${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`);
  }
  return out;
}

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

// Runs IN the destination page: find the main article title and detect clipping.
const TITLE_AUDIT = () => {
  const el = document.querySelector('.pick-article-hero__title')
    || document.querySelector('article h1') || document.querySelector('main h1')
    || document.querySelector('header h1') || document.querySelector('h1');
  if (!el) return { ok: false, reason: 'no h1/hero title found on page' };
  const text = (el.textContent || '').trim();
  if (text.length < 8) return { ok: false, reason: `title text too short: "${text}"` };
  const r = el.getBoundingClientRect();
  if (r.width === 0 || r.height === 0) return { ok: false, reason: 'title has zero rendered size (hidden)' };
  const problems = [];
  // horizontal clipping of the element itself
  if (el.scrollWidth > el.clientWidth + 2) problems.push(`title overflows horizontally (scrollWidth ${el.scrollWidth} > clientWidth ${el.clientWidth})`);
  // clipped by an overflow-hidden ancestor
  let a = el.parentElement;
  while (a && a !== document.body) {
    const cs = getComputedStyle(a);
    if (/(hidden|clip)/.test(cs.overflow + cs.overflowX + cs.overflowY)) {
      const ar = a.getBoundingClientRect();
      if (r.bottom > ar.bottom + 2 || r.right > ar.right + 2 || r.top < ar.top - 2)
        problems.push(`title clipped by overflow-hidden ancestor <${a.tagName.toLowerCase()} class="${a.className}">`);
    }
    a = a.parentElement;
  }
  // off-viewport horizontally
  if (r.right > window.innerWidth + 2 || r.left < -2) problems.push(`title extends past viewport (left ${Math.round(r.left)}, right ${Math.round(r.right)}, vw ${window.innerWidth})`);
  const bodyText = (document.body.innerText || '').length;
  return { ok: problems.length === 0, reason: problems.join('; '), text: text.slice(0, 90), docTitle: document.title, bodyText };
};

(async () => {
  const browser = await chromium.launch();
  const desktop = await browser.newContext({ viewport: { width: 1700, height: 1200 } });
  const mobile = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true });
  let failures = 0, warns = 0, clicks = 0;
  const checkedDest = new Set();
  console.log(`DEEP calendar UX simulation | base=${BASE} | months=${monthsToCheck().join(', ')}`);

  for (const t of TARGETS) {
    console.log(`\n=== ${t.name}  (host: ${t.host})`);
    const entries = parseEntries(t.dataFile);
    let anyMonth = false;

    // VISUAL HEALTH (Nima, June 24 2026): the calendar must highlight ONLY the
    // date of the article being viewed (current-page) and must NOT paint a
    // separate gold 'today' cell. Assert, on the live rendered current month,
    // that (a) has-content cells carry the cyan state styling (engine injected
    // its CSS) and (b) NO cell is marked `.today` (the wrong second highlight
    // that lit a no-article day on out-of-season sports). Click-tests miss both.
    {
      const vp = await desktop.newPage();
      try {
        await vp.goto(BASE + t.host, { waitUntil: 'networkidle', timeout: 45000 });
        await vp.waitForTimeout(700);
        await vp.evaluate((mo) => {
          const sel = document.getElementById('month-select');
          if (sel) {
            if (![...sel.options].some(o => o.value === mo)) { const o = document.createElement('option'); o.value = mo; o.text = mo; sel.appendChild(o); }
            sel.value = mo; sel.dispatchEvent(new Event('change'));
          }
        }, TODAY.slice(0, 7));
        await vp.waitForTimeout(350);
        const vh = await vp.evaluate(() => {
          const cells = [...document.querySelectorAll('#calendar-days .cal-day')];
          const hc = cells.find(x => x.className.includes('has-content') || x.className.includes('is-linked'));
          const problems = [];
          if (hc) {
            const cs = getComputedStyle(hc);
            const bg = cs.backgroundColor || '';
            const transparent = bg === 'transparent' || bg === 'rgba(0, 0, 0, 0)' || /, ?0\)$/.test(bg);
            if (transparent && (cs.borderTopWidth === '0px' || cs.borderTopStyle === 'none'))
              problems.push('has-content cell has NO state styling (transparent bg + no border) - engine did not inject cal-day state CSS');
          }
          const todayMarked = cells.filter(x => x.className.split(/\s+/).includes('today'));
          if (todayMarked.length)
            problems.push(`${todayMarked.length} cell(s) marked .today - BANNED. Highlight only the viewed article's date, never a separate today cell.`);
          return { problems, hadHc: !!hc };
        });
        if (vh.problems.length) { vh.problems.forEach(p => console.log(`  [FAIL] VISUAL ${t.name}: ${p}`)); failures += vh.problems.length; }
        else console.log(`  [OK] VISUAL ${t.name}: state styling applied, no stray today marker`);
      } catch (e) { console.log(`  [WARN] VISUAL ${t.name}: could not run visual health (${e.message})`); warns++; }
      await vp.close();
    }

    for (const MONTH of monthsToCheck()) {
      const monthEntries = entries.filter(e => e.date.startsWith(MONTH));
      const monthDays = [...new Set(monthEntries.map(e => parseInt(e.date.slice(8), 10)))].sort((a, b) => a - b);
      if (!monthDays.length) continue;
      anyMonth = true;
      console.log(`  -- ${MONTH}: ${monthDays.length} dated entr${monthDays.length === 1 ? 'y' : 'ies'} (${monthDays.join(', ')})`);

      for (const day of monthDays) {
        const dayEntries = monthEntries.filter(e => parseInt(e.date.slice(8), 10) === day);
        const expected = base(primaryForDate(dayEntries, t.engine).page);
        const page = await desktop.newPage();
        try {
          await page.goto(BASE + t.host, { waitUntil: 'networkidle', timeout: 45000 });
          await page.waitForTimeout(600);
          if (!(await page.$('#calendar-days'))) { console.log('  [FAIL] no #calendar-days on host'); failures++; await page.close(); continue; }
          await page.evaluate((mo) => {
            const sel = document.getElementById('month-select');
            if (sel) {
              if (![...sel.options].some(o => o.value === mo)) { const o = document.createElement('option'); o.value = mo; o.text = mo; sel.appendChild(o); }
              sel.value = mo; sel.dispatchEvent(new Event('change'));
            }
          }, MONTH);
          await page.waitForTimeout(350);
          const clicked = await page.evaluate((d) => {
            const c = [...document.querySelectorAll('#calendar-days .cal-day')].filter(x => /^\d+$/.test(x.textContent.trim()) && parseInt(x.textContent.trim(), 10) === d)
              .find(x => x.className.includes('has-content') || x.className.includes('is-linked'));
            if (!c || typeof c.onclick !== 'function') return false;
            c.click(); return true;
          }, day);
          if (!clicked) { console.log(`  [FAIL] ${MONTH}-${String(day).padStart(2, '0')}: date not clickable on rendered calendar`); failures++; await page.close(); continue; }
          clicks++;
          await page.waitForLoadState('domcontentloaded', { timeout: 20000 }).catch(() => {});
          await page.waitForTimeout(700);
          const destFile = base(page.url());
          const resp = await desktop.request.get(page.url());
          if (destFile !== expected || resp.status() !== 200) {
            console.log(`  [FAIL] ${MONTH}-${String(day).padStart(2, '0')}: click -> ${destFile} HTTP ${resp.status()} (expected ${expected})`); failures++; await page.close(); continue;
          }
          // destination render + title audit (desktop), dedupe repeats
          let line = `  [OK] ${MONTH}-${String(day).padStart(2, '0')} click -> ${destFile} 200`;
          if (!checkedDest.has(destFile)) {
            checkedDest.add(destFile);
            const a = await page.evaluate(TITLE_AUDIT);
            if (!a.ok) { console.log(`${line}\n  [FAIL] ${destFile} DESKTOP title/render: ${a.reason}`); failures++; await page.close(); continue; }
            if (a.bodyText < 1500) { console.log(`${line}\n  [FAIL] ${destFile}: page body too thin (${a.bodyText} chars) - article may not have rendered`); failures++; await page.close(); continue; }
            if ((a.docTitle || '').length > 65) { console.log(`  [WARN] ${destFile}: document.title ${a.docTitle.length} chars (> 65): "${a.docTitle.slice(0, 70)}..."`); warns++; }
            // mobile pass
            const mp = await mobile.newPage();
            try {
              await mp.goto(BASE + destFile, { waitUntil: 'domcontentloaded', timeout: 45000 });
              await mp.waitForTimeout(600);
              const am = await mp.evaluate(TITLE_AUDIT);
              if (!am.ok) { console.log(`${line}\n  [FAIL] ${destFile} MOBILE(390px) title: ${am.reason}`); failures++; await mp.close(); await page.close(); continue; }
              line += ' | title renders clean desktop+mobile';
            } finally { await mp.close().catch(() => {}); }
          }
          console.log(line);
        } catch (e) {
          console.log(`  [FAIL] ${t.name} ${MONTH}-${String(day).padStart(2, '0')} threw: ${e.message}`); failures++;
        } finally {
          await page.close().catch(() => {});
        }
      }
    }
    if (!anyMonth) console.log('  [SKIP] no entries in checked month range (off-season)');
  }

  await browser.close();
  console.log('\n=====================================');
  console.log(`clicks simulated: ${clicks} | unique destinations audited: ${checkedDest.size} | warns: ${warns}`);
  console.log(failures === 0 ? 'ALL DEEP CALENDAR UX CHECKS PASSED' : `${failures} CHECK(S) FAILED`);
  console.log('=====================================');
  process.exit(failures === 0 ? 0 : 1);
})();
