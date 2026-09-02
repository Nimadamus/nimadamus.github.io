// Screenshot preview/review pages (desktop + mobile) for before/after evidence.
// Usage: node scripts/screenshot_preview_pages.js <outdir> <label> [--base <url>] [pages...]
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const DEFAULT_PAGES = [
  'padres-at-dodgers-ohtani-king-analysis-stats-preview.html',
  'canada-vs-morocco-analysis-stats-preview.html',
  'brewers-braves-padres-rangers-degrom-friday-board-mlb.html',
  'world-cup-round-of-16-canada-morocco-france-paraguay-saturday-soccer.html',
  '76ers-vs-celtics-analysis-stats-preview.html',
  'warriors-vs-thunder-nba-analysis-stats-preview.html',
  '9-alabama-vs-8-oklahoma-cfp-prediction-picks.html',
];

(async () => {
  const args = process.argv.slice(2);
  const outdir = args[0];
  const label = args[1];
  let base = 'https://www.betlegendpicks.com/';
  const baseIdx = args.indexOf('--base');
  if (baseIdx !== -1) base = args[baseIdx + 1];
  const pages = args.filter((a, i) => i > 1 && a !== '--base' && args[baseIdx + 1] !== a);
  const targets = pages.length ? pages : DEFAULT_PAGES;
  fs.mkdirSync(outdir, { recursive: true });

  const browser = await chromium.launch();
  for (const p of targets) {
    const slug = p.replace(/\.html$/, '').slice(0, 60);
    for (const [device, vp] of [['desktop', { width: 1440, height: 1000 }], ['mobile', { width: 390, height: 844 }]]) {
      const ctx = await browser.newContext({ viewport: vp, deviceScaleFactor: 1 });
      const page = await ctx.newPage();
      try {
        await page.goto(base + p, { waitUntil: 'networkidle', timeout: 45000 });
        await page.waitForTimeout(1200);
        const file = path.join(outdir, `${label}-${device}-${slug}.png`);
        await page.screenshot({ path: file, fullPage: true });
        console.log(`OK ${file}`);
      } catch (e) {
        console.log(`FAIL ${p} ${device}: ${e.message.split('\n')[0]}`);
      }
      await ctx.close();
    }
  }
  await browser.close();
})();
