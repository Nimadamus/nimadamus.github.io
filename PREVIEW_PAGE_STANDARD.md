# BETLEGEND PREVIEW/REVIEW PAGE STANDARD (LOCKED JULY 4, 2026)

This is the single source of truth for the structure of every BetLegendPicks
game preview, review, featured-game, and daily-board page across ALL sports
(MLB, NFL, NBA, NHL, Soccer, NCAAB, NCAAF, and any future sport).

It restores the clean April 29, 2026 article format (commit `4afee4cec`,
`celtics-vs-76ers-game-6-...-analysis-stats-preview.html`) and adds the
improvements that arrived later (hero band, captioned figure image, mobile
archive selector). The June-July 2026 drift (inline-styled H2 walls, dropped
TOC/FAQ/schema/share buttons, half-length articles) is the failure mode this
document exists to prevent.

Canonical skeletons live in:
- `docs/templates/featured-preview.template` - single-game preview/featured page
- `docs/templates/daily-board.template` - multi-game daily slate board

Copy the skeleton, replace every `{{PLACEHOLDER}}`, delete nothing structural.

---

## 1. The two page families

| Family | Slug | Skeleton |
|---|---|---|
| Single-game preview / Featured Game | `[away]-vs-[home]-analysis-stats-preview.html` | featured-preview.template |
| Daily sport board (multi-game) | `[storyline]-[sport].html` | daily-board.template |

Both families share: full site nav, hero band, calendar sidebar + mobile
archive select, unique hero image, anchored sections, related-links block,
footer, sport-correct calendar JS (see CLAUDE.md lookup table).

## 2. Required structure - single-game preview

In order, none optional unless marked:

1. **Head**: title with full date, meta description, canonical, robots
   index/follow, keywords, og:/twitter: cards pointing at the page's UNIQUE
   hero image (never newlogo.png), `window.FORCED_PAGE_DATE` (= POST date).
2. **Schema (JSON-LD), all four blocks**:
   - NewsArticle (image = the unique hero image)
   - BreadcrumbList (Home -> section -> page)
   - FAQPage (5-6 real Question/Answer pairs; answers restate verified page
     facts - time, venue, odds, series/records, key players)
   - SportsEvent (startDate with time, awayTeam/homeTeam SportsTeam, Place)
3. **Nav**: full site nav copied from a current live page.
4. **Hero band** (`header.hero`): `hero-badge` (sport + weekday + date),
   H1 = full-sentence storyline headline naming both teams (NEVER a generic
   "Featured Game of the Day"), subtitle line, `post-date` "Published
   Month D, YYYY", one-paragraph lede.
5. **Calendar sidebar** (`aside.calendar-sidebar`) + **mobile archive select**
   (`div.mobile-archive`), with the sport-correct calendar JS at the bottom of
   the body (CLAUDE.md lookup table - never invent a filename).
6. **Game card** (`div.game-card`):
   - `figure.hero-figure`: unique real action photo relevant to this exact
     matchup, `img.feature-photo` (aspect-ratio 3/2, object-fit cover,
     object-position center 15% - face-safe rule, LOCKED June 9 2026),
     descriptive alt text naming the player/teams, `figcaption` describing the
     photo.
   - `h2.game-title` with both team logos inline (ESPN CDN; numeric IDs for
     college).
   - `game-details`: Day, full date | time ET | venue, city | network.
   - `div.betting-lines` grid of `line-item` cards (Moneyline / Spread or
     Series / Total / Implied Probability) - ONLY with verified numbers.
     No lines found = omit the entire grid. NEVER ship empty or "--" boxes.
7. **Content section** (`div.content-section`):
   - `div.toc-box` "In This Preview" with anchor links to every H2.
   - `div.share-buttons` (Twitter/X, Facebook, Reddit).
   - Anchored sections, each `<h2 id="..." class="section-header">` (styling
     comes from the class - NEVER inline style attributes on headings):
     a. Matchup Context (records, standings, form - the "why this matters")
     b. Injury Report & Lineup Notes (`matchup-grid` of two `team-card`s)
     c. Tactical / Pitching Match-Up (sport-appropriate; `h3` sub-heads allowed)
     d. Advanced Stats & Style Profile (`stats-comparison` two-column grid)
     e. Keys To The Game (two `team-card`s)
     f. Betting Angle / Market Context (only when lines are verified)
     g. Final Lean / Pick - ONLY on pick pages when a real graded pick exists.
        Featured Game pages are analysis-only: no picks, ever.
     h. Final Thoughts
     i. FAQ (`faq-item` blocks mirroring the FAQPage schema)
   - `div.related-links` block: sport preview hub, sport monthly archive,
     sport records page, handicapping hub (4 links minimum).
   - `div.back-nav` Back to Home.
8. **Footer** + sport calendar JS + mobile dropdown script.

Target length: 1,400+ words of matchup-specific prose (the clean-era pages ran
40-48 KB). If verified facts cannot support a section, cut the section - never
pad with generic filler.

## 3. Required structure - daily board (multi-game)

Same head/schema (NewsArticle + BreadcrumbList; SportsEvent per marquee game),
nav, hero band, calendar sidebar + mobile archive, footer. Body:

1. `figure.hero-figure` at the top of `main`: unique action photo for the
   day's marquee game, captioned. og:image/twitter:image/schema image = this
   photo. NEVER newlogo.png.
2. `div.toc-box` listing every game on the board as anchor links.
3. One `<article class="game-preview" id="game-N-away-home">` per game
   (marquee game gets `class="game-preview marquee"`): `game-number` label,
   `game-header` with both `team-logo`s + `matchup-info` H2 + `game-time`
   (day, time ET, venue), `preview-content` with 3 substantial
   matchup-specific paragraphs. `game-divider` between articles.
4. `div.related-links` block before the footer close (hub, archive, records,
   handicapping hub).

## 4. Images (every page, every sport)

- Every preview/review page carries a UNIQUE hero image. One image may not
  serve two pages. Repeating one generic photo across a sport is the failure
  this rule kills.
- Real action photos of the actual teams/players/competition only. No logos
  as heroes, no headshots, no stock, no text/graphic tiles.
- Source from stable CDNs (a.espncdn.com/photo, img.mlbstatic.com, Wikimedia
  upload.wikimedia.org) and verify HTTP 200 before publish.
- Alt text names the player(s)/teams and action. Figcaption describes the shot.
- Face-safe crop CSS is mandatory (`object-position:center 15%`; mobile 4/5
  aspect with center 18% - see CLAUDE.md image-centering rule).
- og:image, twitter:image, and NewsArticle schema image all point at the same
  unique hero image.
- Team logos (ESPN CDN) still appear beside team names in game headers - they
  are in addition to, not instead of, the hero photo.

## 5. Data accuracy gates

- Every record, line, pitcher, time, venue, injury: searched and verified at
  write time, or omitted. No invented stats, no stale odds presented as live.
- No placeholder text, no empty betting boxes, no "--" values.
- FORCED_PAGE_DATE = post date (never game date); title/meta carry the full date.
- Run before publish: `accuracy_filter.py`, `validate_news_before_publish.py`,
  `scripts/sync_calendars.py`, `scripts/validate_calendar_continuity.py`.

## 6. SEO protection

- Existing slugs are never renamed. New slugs: dateless, storyline-driven,
  sport token included (pre-commit enforced).
- Canonical tags are protected - do not touch existing canonicals.
- Titles/H1/meta keep long-tail keywords + full date.
- Every new page must have at least one inbound link from live structure
  (calendar JS, hub, archive, homepage surface) before it counts as published.

## 7. Why this document exists (July 4, 2026)

Between June and July 2026 the daily automation quietly replaced the locked
April format with a stripped-down version: generic inline-styled H2s with no
anchors, no TOC, no FAQ/FAQPage, no BreadcrumbList/SportsEvent schema, no
share buttons, no unique image (og:image fell back to newlogo.png on 1,000+
pages), and articles half the length. Nothing in SLATE/ATLAS specified the
template, so the format only lived by example and decayed. This standard, the
two skeletons, and the SLATE/ATLAS references to them are the fix. If a new
page does not match this document, it is not done.
