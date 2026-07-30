# BetLegendPicks.com — Full Technical SEO / Indexing / Rendering Audit — July 30, 2026

Scope: production site https://www.betlegendpicks.com (GitHub Pages, repo `nimadamus.github.io`).
Method: four parallel audits — repo-side scan (2,151 root HTML files), live HTTP/header/redirect
testing, Google Search Console API pull (service account, working), and Playwright raw-HTML vs
rendered-DOM comparison. All statements below are backed by same-day evidence.

---

## Headline conclusion

**There is no technical crawl or indexing blocker on the site.** Googlebot can reach it, fetch it,
and index it — and GSC confirms it does. The 21-impressions day is not a malfunction or a recent
breakage: **the last 28 days of GSC data show impressions have been flat-low the entire window
(6–63/day, no cliff)**, and essentially all clicks come from one brand query ("betlegend",
83 of ~84 clicks). The site is indexed but is not *ranking* for non-brand queries. That is a
competition/authority problem, not a crawlability problem. Real but secondary technical issues
were found and are listed below; three were fixed and deployed today.

## What was verified clean (evidence per line)

| Area | Result |
|---|---|
| GSC property | `https://www.betlegendpicks.com/` URL-prefix property exists, permission = siteOwner. Correct property for this site (all host variants 301 to it in one hop). |
| Sitemap in GSC | Index + 5 child sitemaps submitted, last downloaded by Google 2026-07-29 18:26 UTC, **0 errors / 0 warnings**. |
| URL Inspection | `/`, `/mlb-previews.html`, `/handicapping-hub.html`, `/records.html`, `/soccer-previews.html` all "Submitted and indexed", Google canonical = user canonical, robots ALLOWED, homepage last crawled 2026-07-28, mlb-previews 2026-07-29 (daily crawl of fresh content is happening). |
| robots.txt | `Allow: /`, sitemap declared. Only blocks `.py/.ps1/.bat/.log/.json`. Verified no page depends on a blocked `.json` for visible content. No `noindex` anywhere on the site (0 of 2,151 files) — the pre-commit hook's zero-tolerance noindex gate is active. |
| X-Robots-Tag / headers | Absent on all sampled responses. No crawl-blocking headers. |
| Host/protocol duplication | http/https × www/non-www all 301 in a single hop to `https://www.`; deep apex URLs too. `nimadamus.github.io` 301s to the domain. No staging/alternate-host references in served HTML. |
| Cloaking / bot handling | Googlebot UA receives byte-identical HTML to a normal browser on `/` and preview pages. No Cloudflare, no CAPTCHA/challenge layer (served directly by GitHub Pages, `Server: GitHub.com`). |
| HTTP health | All core section pages 200. Hard 404 (not soft) for nonexistent URLs. gzip works. |
| Caching | GitHub Pages standard `Cache-Control: max-age=600` + Fastly. Homepage `Last-Modified` matched the 05:19 UTC deploy the same morning — crawlers get fresh HTML within minutes of publish. No service workers registered on any tested page. |
| SSR of SEO content | Homepage and daily preview pages are fully server-baked: team names, odds, records, dates, 200+ anchor links present in raw HTML (verified by string-matching raw curl output). Rendered DOM adds nothing material on those pages. Zero console errors, zero failed subresource requests. |
| Mobile | 390×844 render carries the same content and nav anchors as desktop. |
| Canonicals | 0 missing, 0 bare-host, 0 http://, 0 wrong-page canonicals across all 1,567 non-stub root pages. June 3 recovery has not regressed. |
| Sitemap lastmod | Real git-history dates (spread Sept 2025 → Jul 2026), regenerated on publish — not fabricated stamps. |
| Deployment | GitHub Pages builds healthy (latest `built`; one transient failure Jul 29 self-recovered). Deploys verifiably reach production. |
| Dated-URL regression | 0 new dated content slugs since the June 3 recovery; pre-commit gate confirmed installed and identical to `hooks/pre-commit`. |

## Confirmed findings (fixed today — deployed in commit `d3d36cbef`)

1. **7 redirect stubs listed in sitemap-main.xml as live pages** (`model.html`, `odds-live.html`,
   `social.html`, `daily-picks.html`, `daily-mlb-breakdown-picks.html`, `picks-archive.html`,
   `track-record.html`). Root cause: `is_redirect_stub()` in
   `scripts/generate_discovery_artifacts.py` only matched `<meta http-equiv="refresh" content=...>`
   attribute order; these stubs are written `<meta content="0; url=..." http-equiv="refresh">`.
   Severity: low-medium (wastes crawl budget, sends mixed signals). Fix: order-agnostic regex;
   URLs removed from sitemap. Risk: none (sitemap-only; no routes/canonicals touched).
2. **April 2026 archive pages for MLB/NBA/NHL/Soccer missing from sitemaps.** Root cause: those
   pages embed an April 1 daily card containing the literal text "Redirecting to today's
   previews…" at byte ~12,000, which false-positived the stub detector. Fix: check scoped to the
   first 4KB. The 4 URLs are back in the sitemap (1,822 → 1,819 total; legacy sport hubs verified
   still present, per locked rule).
3. **feed.xml served oldest-first** (Nov 2025 items at top despite fresh lastBuildDate).
   Regenerated newest-first. Also **added `/favicon.ico`** (pages without an icon link 404'd it;
   cosmetic).

Verification: live `sitemap-main.xml` re-fetched after deploy — stub URLs gone, April archives
present; feed.xml newest-first; favicon.ico 200.

## Findings needing your decision (NOT changed — per repo locked rules, canonicals and SEO
structure are protected, and past AI SEO tuning on this site reduced traffic)

| # | Finding | Evidence | Severity | Proposed fix | Risk |
|---|---|---|---|---|---|
| A | **`/records.html` and `/upcomingpicks.html` are empty shells in server HTML** — every number is client-hydrated from Google Sheets CSVs; raw HTML contains only `--` placeholders / "Loading Picks...". GSC: `/upcomingpicks.html` = "Discovered – currently not indexed, never crawled". `/records.html` is indexed but Google's copy depends on its JS render queue seeing populated tables. | Playwright raw-vs-rendered diff | **High** (these are the site's trust pages: "verified record" content is invisible to non-JS fetches) | At publish time, bake the current record tables/pick rows into the static HTML (extend existing sync scripts); keep the JS hydration on top so live numbers still refresh. No route, canonical, or design changes. | Medium — touches the locked records-renderer system; needs careful implementation + Playwright regression. Do only with your go-ahead. |
| B | **The 7 stubs above carry self-canonicals** while meta-refreshing elsewhere (contradictory signals; canonical should point at the redirect target, matching the 583 correct stubs). | grep of stub files | Low | Point each canonical at its target page. 7 files, one line each. | Low, but canonical edits are protected — your call. |
| C | **122 sitemap URLs have zero internal links** (113 = legacy `handicapping-hub-YYYY-MM-DD.html`, documented as intentionally unlinked in the June 3 report; 9 misc incl. `verified-trends.html`, `email.html`). Google reaches them by sitemap only; "Discovered – not indexed" is the usual fate of link-less URLs. | link-graph scan | Medium | Add plain `<a>` crawl links from the relevant archive/hub pages (insert-only). | Low — additive links only. |
| D | **16 duplicate-title groups + generic boilerplate descriptions** concentrated on legacy `handicapping-hub-*` pages and legacy sport hubs sharing titles with same-day standalone pages. | title/description scan | Low-medium | Unique titles/descriptions per page (script pass). Legacy sport hubs are under a locked rule — explicitly ask before touching them. | Low for hub-archive pages; locked-rule territory for sport hubs. |
| E | **June 18 commit `2201b064e` hard-deleted 760 dated redirect stubs.** Any external backlink or residual index entry pointing at those URLs now 404s instead of passing to the dateless page. Cannot quantify without backlink data. | git history | Unknown (likely low) | If you have Ahrefs/Semrush/GSC-links data showing external links to those slugs, restore stubs for just those URLs. | Low if targeted. |
| F | **`/about-us.html` is a 200 JS/meta-refresh stub** (GitHub Pages can't serve real 301s). Canonical correctly points at `/about.html`. | curl | Low | Leave as-is (creating redirects needs your approval anyway and GH Pages offers no better mechanism). | — |
| G | **`/nfl-previews.html` 404s** — NFL never got a `-previews` hub (real page is `/nfl.html`). Nothing links to it; zero live impact. | curl + grep | Info | Optional: create it or ignore. | — |
| H | **Optional GSC hygiene**: add a Domain property (`sc-domain:betlegendpicks.com`) via DNS TXT to capture any stray-host impressions. Current www property is correct and sufficient; this is belt-and-suspenders. | sites.list | Info | Namecheap TXT record + GSC add. | None to the site. |

## Why impressions are low (the honest answer)

Google crawls the site daily, indexes the daily pages, and serves them for brand searches. What's
missing is non-brand ranking: sports-picks queries are dominated by high-authority sites
(Action Network, Covers, ESPN, Pickswise…), and this domain currently has ~1 ranking query.
Fixing items A–D improves crawl efficiency and the quality of what Google sees, but no technical
fix on this list will by itself move impressions materially — that battle is content depth,
long-tail query targeting, and backlinks. Per the repo's own locked rule, SEO strategy here is
your call; nothing beyond the three safe generator fixes was changed.

## Reindex requests (after you review — GSC → URL Inspection → Request indexing)

1. https://www.betlegendpicks.com/sitemap.xml — resubmit (picks up the −7/+4 changes)
2. https://www.betlegendpicks.com/mlb-previews-archive-april-2026.html
3. https://www.betlegendpicks.com/nba-previews-archive-april-2026.html
4. https://www.betlegendpicks.com/nhl-previews-archive-april-2026.html
5. https://www.betlegendpicks.com/soccer-previews-archive-april-2026.html
6. https://www.betlegendpicks.com/upcomingpicks.html — only after fix A, otherwise Google will
   fetch the empty shell again

## Regression verification performed

- Live sitemap re-fetched post-deploy: 1,819 URLs, stubs absent, April archives present, legacy
  sport hubs present (locked-rule check passed).
- Homepage, preview hubs, records, archive pages: HTTP 200 spot-check unchanged post-deploy.
- No canonical, robots, route, redirect, or noindex changes were made anywhere.
