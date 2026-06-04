# BetLegendPicks.com Indexation Recovery — June 3, 2026

Response to GSC "Crawled - currently not indexed" (727 pages, failed validation).

## Root cause

1. **May 3, 2026 directive** ("no dates in URLs") was implemented in commit
   `748da93a8`: 686 dated files renamed to dateless slugs + redirect stubs.
2. **May 15, 2026 commit `ee65c42d1`** ("Restore sport calendar article targets")
   clobbered the redirect stubs back to full-content pages.
3. Generators (SLATE command + repo CLAUDE.md formulas) still mandated dated
   slugs, so **120 new dated URLs** were created May 3 → June 3.
4. Net state found by audit: **640 dated full-content pages live**, 240 of them
   exact duplicates of their dateless twin, **all in the sitemap**, both sides
   self-canonical → Google saw massive duplication → "Crawled - not indexed".
5. Compounding signals: sport hubs (`mlb/nba/soccer-previews.html`) carried
   canonicals pointing at stale May 19 articles (hub-clone artifact); hubs and
   all sport calendar pages missing from sitemaps; 12 recent pick pages used
   bare-host canonicals (`https://betlegendpicks.com/...`); 69 handicapping-hub
   pages had no canonical; 410 pages were crawl orphans (only reachable through
   JS-rendered calendars Google does not follow).

## What was fixed (this commit)

| Area | Fix |
|------|-----|
| Duplicate URLs | All 640 dated URLs re-stubbed (meta refresh 0 + canonical + JS replace + noindex,follow) to their dateless twin. 240 pairs stubbed in place; 280 renamed to their May 3 mapped slug; 120 post-May-3 dated pages renamed to new dateless slugs. No content deleted — full content lives at the dateless URL. |
| References | 5,555 internal references rewritten across 698 files (hrefs, canonicals, og:url, JSON-LD, calendar data, homepage-picks-data.js); a later pass fixed 26 files still linking deleted dated URLs. |
| Canonicals | `mlb-previews.html`, `nba-previews.html`, `soccer-previews.html` → self-canonical; duplicate canonical removed from penguins NHL pick page; 12 bare-host canonicals → `https://www.`; 69 handicapping-hub pages given self-canonicals (each to ITSELF — no consolidation, per the locked rule). |
| Sitemaps | Rebuilt via `scripts/generate_discovery_artifacts.py`: **1,502 unique canonical URLs**, 0 dated URLs, 0 sitemap-404s, 0 noindex/stub/canonicalized-away URLs. Sport hubs + all sport calendar pages now included (fixed `is_redirect_stub` false positive on calendar `window.location.href` click handlers). lastmod from git history. |
| Internal linking | Static crawl chain hub → monthly archive → daily page: 30 new monthly archive pages created (all 7 sports, every month with content), each listing EVERY daily page of that month as plain `<a>` links; sport hubs link all their monthly archives + their archive calendar page; `handicapping-hub-archive.html` lists all 174 daily hub archives; `picks-archive.html` lists all 133 standalone pick/featured pages (linked from `upcomingpicks.html`). Orphans: **410 → 128** (remainder is mostly the legacy root `handicapping-hub-YYYY-MM-DD.html` duplicate set — intentionally NOT linked; see below). |
| Page quality | Removed banned "Sources:" citation block from canadiens pick page. Created archive pages have unique titles/descriptions per sport+month. |
| Regression guards | `hooks/pre-commit` now BLOCKS any new root HTML file with a dated slug. Repo `CLAUDE.md` URL formulas corrected to dateless (+ locked NO DATES IN URLS rule with this incident's history). `~/.claude/commands/slate.md` URL table corrected to dateless. Validator improvements: skips redirect stubs, honors skip-list in staged mode, roster check is full-name-only (no more NBA-name-vs-MLB-roster false errors), batting-average regex no longer matches ISO dates. |

## Intentionally left out of the sitemap

- 643 noindex pages: 640 redirect stubs at old dated URLs + `featured-game-of-the-day.html`
  (hub redirector, by design) + google verification + mlb-pitcher-model.
- `picks.html` (JS redirector to `upcomingpicks.html`), `404.html`, preview fragments.
- Legacy root `handicapping-hub-YYYY-MM-DD.html` pages remain in sitemap with
  self-canonicals but were NOT given crawl links (they duplicate
  `handicapping-hub-archive/hub-*.html`, which the live calendar links).
  Consolidating them is blocked by the locked rule — Nima's call.

## NOT touched (locked rules)

- Legacy sport pages `nhl.html`, `mlb.html`, `nba.html`, `soccer.html`,
  `ncaaf.html`, `ncaab.html`, `nfl.html` (Rolling-Hub-retired rule: no
  canonical/redirect/sitemap changes without Nima).
- No canonicalization of handicapping-hub archives to `handicapping-hub.html`.
- No files deleted; no homepage design changes.

## Manual Search Console actions (after deploy)

1. Sitemaps → resubmit `https://www.betlegendpicks.com/sitemap.xml`.
2. Page indexing → "Crawled - currently not indexed" → **Validate fix**.
3. URL Inspection → Request indexing for the highest-value fixed pages:
   homepage, `mlb-previews.html`, `nba-previews.html`, `nhl-previews.html`,
   `soccer-previews.html`, the monthly archive pages, and a sample of
   dateless daily pages.
4. Expect old dated URLs to move to "Page with redirect" / "Excluded by
   noindex" — that is correct and intentional.

## Maintenance

- Re-run after publishing days: `python scripts/build_preview_archives.py`
  (static archive lists), then `python scripts/generate_discovery_artifacts.py`.
- Audit anytime: `python scripts/indexation_audit.py`
  (report: `scripts/indexation_audit_report.json`).
