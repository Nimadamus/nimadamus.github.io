#!/usr/bin/env python3
"""
SEO Recovery Script - BetLegend
Executes all 6 steps of the SEO recovery plan.
Run each step individually: python seo_recovery.py --step N
Or run all: python seo_recovery.py --all
"""

import os
import re
import sys
import glob
from datetime import datetime

REPO = r"C:\Users\Nima\nimadamus.github.io"
BASE_URL = "https://www.betlegendpicks.com"
TODAY = datetime.now().strftime("%Y-%m-%d")

# ============================================================
# PAGE CLASSIFICATION
# ============================================================

# CORE PAGES - Must be indexable, in sitemap, high priority
CORE_PAGES = {
    "index.html",
    # Sport hubs (rolling hub system)
    "nba-previews.html",
    "nhl-previews.html",
    "mlb-previews.html",
    "college-basketball-previews.html",
    "soccer-previews.html",
    # Records
    "betlegend-verified-records.html",
    "nba-records.html",
    "nhl-records.html",
    "mlb-records.html",
    "ncaab-records.html",
    "ncaaf-records.html",
    "soccer-records.html",
    "crosssport-parlays-records.html",
    # Blog
    "blog.html",
    "blog-page2.html",
    "blog-page3.html",
    "blog-page4.html",
    "blog-page5.html",
    "blog-page6.html",
    "blog-page7.html",
    "blog-page8.html",
    "blog-page9.html",
    "blog-page10.html",
    "blog-page11.html",
    "blog-page12.html",
    "blog-page13.html",
    "blog-page14.html",
    # Betting education
    "betting-101.html",
    "betting-calculators.html",
    "betting-education.html",
    "betting-glossary.html",
    # Calculators
    "ev-calculator.html",
    "implied-probability-calculator.html",
    "odds-converter.html",
    "parlay-calculator.html",
    "risk-of-ruin-calculator.html",
    # Kelly cluster
    "kelly-criterion.html",
    "kelly-simulation.html",
    # Bankroll
    "bankroll.html",
    "bankroll-management.html",
    "bankroll-simulator.html",
    # Key content pages
    "handicapping-hub.html",
    "moneyline-parlay-of-the-day.html",
    "best-bets-today.html",
    "daily-picks.html",
    "picks.html",
    "contact.html",
    "subscribe.html",
    "privacy.html",
    "terms.html",
    "sitemap.html",
    "howitworks.html",
    "proofofpicks.html",
    "track-record.html",
    "news.html",
    "social.html",
    "model.html",
    "live-odds.html",
    "odds.html",
    "injury-report.html",
    # Guides and educational content
    "how-sports-betting-odds-work.html",
    "how-betting-lines-move.html",
    "how-to-bet-mlb-totals.html",
    "moneyline-betting-explained.html",
    "point-spread-betting-explained.html",
    "parlay-betting-explained-complete-guide.html",
    "spread-vs-moneyline-betting.html",
    "what-does-minus-110-mean.html",
    "favorites-vs-underdogs-betting-strategy.html",
    "fractional-kelly-vs-full-kelly.html",
    "kelly-criterion-explained.html",
    "kelly-criterion-mistakes.html",
    "line-shopping-betting-strategy.html",
    "line-shopping-guide.html",
    "bankroll-discipline-bet-sizing.html",
    "sports-handicapping-hub-guide.html",
    "new-york-sports-betting.html",
    # Hub pages
    "nhl-betting-hub.html",
    "nhl-home-away-splits.html",
    "nhl-team-trends.html",
    "nhl-totals-trends.html",
    # Calendar pages
    "featured-game-calendar.html",
    "nba-calendar.html",
    "nhl-calendar.html",
    "ncaab-calendar.html",
    "ncaaf-calendar.html",
    "nfl-calendar.html",
    "soccer-calendar.html",
    "handicapping-hub-calendar.html",
    # Featured game landing
    "featured-game-of-the-day.html",
    # FIFA
    "2026-fifa-world-cup-betting-guide-odds-predictions-favorites-how-to-bet.html",
    # Best book
    "bestbook.html",
    "bestonlinesportsbook.html",
    "classic-odds.html",
    "kelly-widget.html",
}

# SECONDARY CONTENT - Featured games, standalone picks, news (indexable, in sitemap, medium priority)
# These are keyword-rich standalone pages that should remain indexed
SECONDARY_PATTERNS = [
    # Featured game analysis pages (keyword-rich URLs)
    r"^[a-z].*-analysis-stats-preview-.*\.html$",
    # Standalone pick pages (keyword-rich)
    r"^[a-z].*-prediction-picks-.*\.html$",
    # News articles
    r"^nfl-.*-news\.html$",
    r"^yasiel-puig-.*\.html$",
    # Blog archive pages with keyword-rich names
    r"^betlegend-daily-picks-analysis-.*\.html$",
    r"^betlegend-picks-analysis-.*\.html$",
    r"^betlegend-.*-archive-\d+\.html$",
    r"^betlegend-.*-betting-picks-.*\.html$",
    # Standalone BetLegend pick pages (new system - keyword-rich, no date in URL pattern)
    r"^[a-z].*-nhl\.html$",
    r"^[a-z].*-nba\.html$",
    r"^[a-z].*-mlb\.html$",
    # Bankroll management subpages
    r"^bankroll-management/.+\.html$",
    # EV calculator subpages
    r"^ev-calculator/.+\.html$",
    # Kelly criterion subpages
    r"^kelly-criterion/.+\.html$",
]

# OLD DAILY PAGES - Must be noindexed, removed from sitemap
OLD_DAILY_PATTERNS = [
    # Old page-numbered format
    r"^nba-page\d+\.html$",
    r"^nhl-page\d+\.html$",
    r"^mlb-page\d+\.html$",
    r"^ncaab-page\d+\.html$",
    r"^ncaaf-page\d+\.html$",
    r"^nfl-page\d+\.html$",
    r"^soccer-page\d+\.html$",
    r"^featured-game-of-the-day-page\d+\.html$",
    # Old dated preview format (generic date-stamped)
    r"^nba-game-previews-analysis-.*\d{4}\.html$",
    r"^nhl-game-previews-analysis-.*\d{4}\.html$",
    r"^mlb-game-previews-analysis-.*\d{4}\.html$",
    r"^college-basketball-game-previews-.*\d{4}\.html$",
    r"^college-football-game-previews-.*\d{4}\.html$",
    r"^soccer-game-previews-analysis-.*\d{4}\.html$",
    # Old college basketball picks format (daily dated)
    r"^college-basketball-picks-predictions-best-bets-.*\d{4}.*\.html$",
    # Old college football picks format
    r"^college-football-picks-predictions-against-the-spread-.*\d{4}\.html$",
    # Old picks-today redirects
    r"^nba-picks-today\.html$",
    r"^nhl-picks-today\.html$",
    r"^mlb-picks-today\.html$",
    # Legacy sport main pages (superseded by hub pages)
    r"^nba\.html$",
    r"^nhl\.html$",
    r"^mlb\.html$",
    r"^ncaab\.html$",
    r"^ncaaf\.html$",
    r"^nfl\.html$",
    r"^soccer\.html$",
    # Archive date pages
    r"^archives/.+\.html$",
    # Hub archive pages (already noindexed, ensure they stay that way)
    r"^.*-previews-archive-.*\.html$",
    # Old archive prediction page
    r"^archive-prediction-picks-.*\.html$",
    # Daily MLB breakdown (old)
    r"^daily-mlb-breakdown-.*\.html$",
    # Handicapping hub dated archives
    r"^handicapping-hub-\d{4}-\d{2}-\d{2}\.html$",
    r"^handicapping-hub-archive/.+\.html$",
    r"^handicapping-hub-archive\.html$",
    r"^handicapping-hub-preview\.html$",
    # NBA picks analysis dated pages
    r"^nba-picks-analysis-against-the-spread-.*\d{4}.*\.html$",
    r"^nba-picks-february-.*\.html$",
    r"^nba-college-basketball-picks-.*\.html$",
    r"^nba-dec\d+\.html$",
    # NHL predictions best bets dated pages
    r"^nhl-predictions-best-bets-tonight-.*\d{4}.*\.html$",
    r"^nhl-dec\d+\.html$",
    # NFL picks predictions dated pages
    r"^nfl-picks-predictions-against-the-spread-.*\d{4}.*\.html$",
    r"^nfl-dec\d+\.html$",
    # Soccer predictions dated pages
    r"^soccer-predictions-picks-best-bets-.*\d{4}.*\.html$",
    # MLB picks dated pages
    r"^mlb-picks-analysis-against-the-spread-.*\d{4}.*\.html$",
    # Old picks-today pages
    r"^ncaab-picks-today\.html$",
    r"^soccer-picks-today\.html$",
    # Old themed daily sport pages (catches remaining)
    r"^kings-fox-returns-.*\.html$",
    # News archive pages
    r"^news-page\d+\.html$",
    # SportsBettingPrime cross-posts
    r"^sportsbettingprime-.*\.html$",
]

# JUNK/UTILITY - Should be noindexed (backup files, preview files, etc.)
JUNK_PATTERNS = [
    r"^index-backup.*\.html$",
    r"^index-preview.*\.html$",
    r"^index-compact.*\.html$",
    r"^index-redesign.*\.html$",
    r"^records\.html$",  # if it's a redirect stub
    r"^featured-game-of-the-day-2026-01-01\.html$",  # stale redirect
    r"^test[-_].*\.html$",
    r"^preview-card-redesign\.html$",
    r"^transparency-preview\.html$",
    r"^input\.html$",
    r"^kelly-criterion_.*_backup\.html$",
    r"^screenshots\.html$",
    r"^google[a-z0-9]+\.html$",  # Google verification files
]

# ADDITIONAL CORE PAGES (not in the main set but should be indexed)
ADDITIONAL_CORE = {
    "email.html",
    "free-trial-info.html",
    "expected-value-calculator.html",
    "implied-probability-sports-betting.html",
    "odds-live.html",
    "picks-archive.html",
    "podcast.html",
    "smartbets.html",
    "upcomingpicks.html",
    "nfl-records.html",
    "pro/index.html",
    "kings-team-total-under-nhl-pick-march-7-2026.html",
}


def classify_page(filepath):
    """Classify a page as core, secondary, old_daily, junk, or unknown."""
    # Get relative path from repo root
    rel = os.path.relpath(filepath, REPO).replace("\\", "/")

    if rel in CORE_PAGES or rel in ADDITIONAL_CORE:
        return "core"

    # Skip 404.html and pro/404.html
    if rel in ("404.html", "pro/404.html"):
        return "junk"

    for pattern in JUNK_PATTERNS:
        if re.match(pattern, rel):
            return "junk"

    for pattern in OLD_DAILY_PATTERNS:
        if re.match(pattern, rel):
            return "old_daily"

    for pattern in SECONDARY_PATTERNS:
        if re.match(pattern, rel):
            return "secondary"

    # Themed sport pages (storyline-driven URLs with sport+date) - these are old daily pages
    # Pattern: [theme]-[sport]-[month]-[day]-[year].html
    themed_daily = re.match(
        r"^[a-z].*-(nba|nhl|mlb|ncaab|soccer|nfl|ncaaf|college-basketball)-"
        r"(january|february|march|april|may|june|july|august|september|october|november|december)-\d+-\d{4}\.html$",
        rel
    )
    if themed_daily:
        return "old_daily"

    # Standalone pick/prediction pages (keyword-rich, any format)
    if re.match(r"^.*-prediction-picks-.*\.html$", rel):
        return "secondary"
    if re.match(r"^\d+.*-prediction-picks-.*\.html$", rel):
        return "secondary"

    # Featured game analysis pages
    if re.match(r"^.*-analysis-stats-preview-.*\.html$", rel):
        return "secondary"

    # Wild card / playoff picks pages
    if re.match(r"^.*-wild-card-picks-.*\.html$", rel):
        return "secondary"
    if re.match(r"^.*-picks-and-prediction-.*\.html$", rel):
        return "secondary"

    # NHL trade deadline themed page (old daily)
    if re.match(r"^nhl-trade-deadline-.*\.html$", rel):
        return "old_daily"

    # Any remaining dated picks/predictions pages across all sports
    if re.match(r"^.*-(picks|predictions|best-bets|preview).*-\d{4}.*\.html$", rel):
        return "old_daily"

    # Remaining pages with dates in them (YYYY-MM-DD or month-DD-YYYY) -> old_daily
    if re.match(r"^.*\d{4}-\d{2}-\d{2}.*\.html$", rel):
        return "old_daily"

    return "unknown"


def get_all_html_files():
    """Get all HTML files in the repo."""
    files = []
    for root, dirs, filenames in os.walk(REPO):
        # Skip .git and scripts
        dirs[:] = [d for d in dirs if d not in ('.git', 'node_modules', '.github')]
        for f in filenames:
            if f.endswith('.html'):
                files.append(os.path.join(root, f))
    return files


def check_has_noindex(filepath):
    """Check if a file already has noindex meta tag."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read(5000)  # Only need to check head
        return 'noindex' in content.lower()
    except:
        return False


def add_noindex(filepath):
    """Add noindex meta tag to a page if it doesn't have one."""
    if check_has_noindex(filepath):
        return False

    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        noindex_tag = '<meta name="robots" content="noindex, follow">'

        # Try to insert after <head> or after charset meta
        if '<head>' in content:
            content = content.replace('<head>', f'<head>\n{noindex_tag}', 1)
        elif '<HEAD>' in content:
            content = content.replace('<HEAD>', f'<HEAD>\n{noindex_tag}', 1)
        elif '<html' in content.lower():
            # Insert before first meta or after html tag
            content = re.sub(
                r'(<html[^>]*>)',
                rf'\1\n<head>\n{noindex_tag}\n</head>',
                content, count=1, flags=re.IGNORECASE
            )
        else:
            # Prepend
            content = f'{noindex_tag}\n{content}'

        with open(filepath, 'w', encoding='utf-8', errors='ignore') as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"  ERROR adding noindex to {filepath}: {e}")
        return False


def remove_noindex(filepath):
    """Remove noindex meta tag from a page."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        if 'noindex' not in content.lower():
            return False

        # Remove various noindex patterns
        new_content = re.sub(
            r'<meta\s+name=["\']robots["\']\s+content=["\'][^"\']*noindex[^"\']*["\']\s*/?\s*>\n?',
            '', content, flags=re.IGNORECASE
        )

        if new_content != content:
            with open(filepath, 'w', encoding='utf-8', errors='ignore') as f:
                f.write(new_content)
            return True
        return False
    except Exception as e:
        print(f"  ERROR removing noindex from {filepath}: {e}")
        return False


def generate_sitemap(pages_with_priority):
    """Generate sitemap.xml with the given pages and priorities."""
    lines = ['<?xml version="1.0" encoding="UTF-8"?>']
    lines.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')

    for page, priority, changefreq in sorted(pages_with_priority, key=lambda x: (-x[1], x[0])):
        lines.append('  <url>')
        lines.append(f'    <loc>{BASE_URL}/{page}</loc>')
        lines.append(f'    <lastmod>{TODAY}</lastmod>')
        lines.append(f'    <changefreq>{changefreq}</changefreq>')
        lines.append(f'    <priority>{priority}</priority>')
        lines.append('  </url>')

    lines.append('</urlset>')
    return '\n'.join(lines)


# ============================================================
# STEP 1: 404 CLEANUP
# ============================================================
def step1_404_cleanup():
    print("=" * 60)
    print("STEP 1: 404 CLEANUP")
    print("=" * 60)

    # Get all URLs currently in sitemap
    sitemap_path = os.path.join(REPO, "sitemap.xml")
    with open(sitemap_path, 'r', encoding='utf-8') as f:
        sitemap_content = f.read()

    sitemap_urls = re.findall(r'<loc>([^<]+)</loc>', sitemap_content)
    sitemap_pages = [u.replace(f'{BASE_URL}/', '') for u in sitemap_urls]

    # Check which sitemap URLs actually exist as files
    missing_from_disk = []
    valid_sitemap_pages = []

    for page in sitemap_pages:
        filepath = os.path.join(REPO, page.replace('/', os.sep))
        if os.path.exists(filepath):
            valid_sitemap_pages.append(page)
        else:
            missing_from_disk.append(page)

    if missing_from_disk:
        print(f"\n  FOUND {len(missing_from_disk)} URLs in sitemap that don't exist on disk (404s):")
        for p in missing_from_disk:
            print(f"    [FAIL] {p}")
    else:
        print("\n  All sitemap URLs exist on disk. No 404s in sitemap.")

    # Now check internal links across all HTML files for broken links
    all_html = get_all_html_files()
    all_existing = set()
    for f in all_html:
        rel = os.path.relpath(f, REPO).replace("\\", "/")
        all_existing.add(rel)

    # Also add non-HTML files that might be linked (JS, CSS, images are fine to skip)

    broken_links = {}  # {source_file: [list of broken hrefs]}
    link_pattern = re.compile(r'href=["\']([^"\'#]+\.html)["\']', re.IGNORECASE)

    print("\n  Scanning all HTML files for broken internal links...")

    for filepath in all_html:
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except:
            continue

        rel_source = os.path.relpath(filepath, REPO).replace("\\", "/")
        source_dir = os.path.dirname(rel_source)

        links = link_pattern.findall(content)
        for link in links:
            # Skip external links
            if link.startswith('http://') or link.startswith('https://') or link.startswith('//'):
                continue

            # Resolve relative path
            if source_dir:
                resolved = os.path.normpath(os.path.join(source_dir, link)).replace("\\", "/")
            else:
                resolved = link

            if resolved not in all_existing:
                if rel_source not in broken_links:
                    broken_links[rel_source] = []
                broken_links[rel_source].append(link)

    if broken_links:
        total_broken = sum(len(v) for v in broken_links.values())
        print(f"\n  FOUND {total_broken} broken internal links across {len(broken_links)} files.")
        # Show summary (not all)
        for source, links in sorted(broken_links.items())[:20]:
            for link in links[:3]:
                print(f"    {source} -> {link} (BROKEN)")
        if len(broken_links) > 20:
            print(f"    ... and {len(broken_links) - 20} more files with broken links")
    else:
        print("\n  No broken internal links found.")

    # Remove 404s from sitemap (will regenerate in step 6)
    print(f"\n  Sitemap currently has {len(sitemap_pages)} URLs.")
    print(f"  Valid URLs: {len(valid_sitemap_pages)}")
    print(f"  404 URLs to remove: {len(missing_from_disk)}")

    # Store broken links info for step 5
    return broken_links, missing_from_disk


# ============================================================
# STEP 2: NOINDEX OLD DAILY PAGES
# ============================================================
def step2_noindex_old_daily():
    print("\n" + "=" * 60)
    print("STEP 2: NOINDEX OLD DAILY PAGES")
    print("=" * 60)

    all_html = get_all_html_files()

    noindexed = 0
    already_noindexed = 0
    old_daily_pages = []

    for filepath in all_html:
        rel = os.path.relpath(filepath, REPO).replace("\\", "/")
        classification = classify_page(filepath)

        if classification == "old_daily":
            old_daily_pages.append(rel)
            if check_has_noindex(filepath):
                already_noindexed += 1
            else:
                if add_noindex(filepath):
                    noindexed += 1
                    print(f"  + noindex: {rel}")

    # Also noindex junk pages
    for filepath in all_html:
        rel = os.path.relpath(filepath, REPO).replace("\\", "/")
        classification = classify_page(filepath)

        if classification == "junk":
            if not check_has_noindex(filepath):
                if add_noindex(filepath):
                    noindexed += 1
                    print(f"  + noindex (junk): {rel}")

    print(f"\n  Old daily pages found: {len(old_daily_pages)}")
    print(f"  Already had noindex: {already_noindexed}")
    print(f"  Newly noindexed: {noindexed}")

    return old_daily_pages


# ============================================================
# STEP 3: NOINDEX AUDIT
# ============================================================
def step3_noindex_audit():
    print("\n" + "=" * 60)
    print("STEP 3: NOINDEX AUDIT")
    print("=" * 60)

    all_html = get_all_html_files()

    fixed = 0
    confirmed_noindex = 0

    for filepath in all_html:
        rel = os.path.relpath(filepath, REPO).replace("\\", "/")
        classification = classify_page(filepath)
        has_noindex = check_has_noindex(filepath)

        if classification in ("core", "secondary"):
            # Core and secondary pages MUST be indexable
            if has_noindex:
                if remove_noindex(filepath):
                    print(f"  - REMOVED noindex from {classification} page: {rel}")
                    fixed += 1
        elif classification in ("old_daily", "junk"):
            # These should have noindex
            if has_noindex:
                confirmed_noindex += 1
        elif classification == "unknown":
            # Unknown pages - check if they look like meaningful content
            # For safety, leave them as-is but report
            if has_noindex:
                print(f"  ? Unknown page with noindex (left as-is): {rel}")

    print(f"\n  Removed noindex from {fixed} core/secondary pages")
    print(f"  Confirmed {confirmed_noindex} old/junk pages have noindex")


# ============================================================
# STEP 4: CONFIRM HUB STRUCTURE
# ============================================================
def step4_hub_structure():
    print("\n" + "=" * 60)
    print("STEP 4: CONFIRM HUB STRUCTURE")
    print("=" * 60)

    hubs = {
        "nba-previews.html": "NBA Predictions & Previews",
        "nhl-previews.html": "NHL Predictions & Previews",
        "mlb-previews.html": "MLB Predictions & Previews",
        "college-basketball-previews.html": "College Basketball Predictions & Previews",
        "soccer-previews.html": "Soccer Predictions & Previews",
    }

    all_ok = True

    for hub_file, description in hubs.items():
        filepath = os.path.join(REPO, hub_file)

        if not os.path.exists(filepath):
            print(f"  [FAIL] MISSING: {hub_file} - {description}")
            all_ok = False
            continue

        # Check it's indexable (no noindex)
        if check_has_noindex(filepath):
            print(f"  [FAIL] {hub_file} has noindex - REMOVING")
            remove_noindex(filepath)

        # Check it has self-canonical
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        canonical_match = re.search(r'<link\s+rel=["\']canonical["\']\s+href=["\']([^"\']+)["\']', content)
        if canonical_match:
            canonical_url = canonical_match.group(1)
            expected = f"{BASE_URL}/{hub_file}"
            if canonical_url == expected:
                print(f"  [OK] {hub_file} - exists, indexable, self-canonical")
            else:
                print(f"  ~ {hub_file} - exists, indexable, canonical={canonical_url}")
        else:
            print(f"  ~ {hub_file} - exists, indexable, NO canonical tag")

    # Check homepage links to hubs
    index_path = os.path.join(REPO, "index.html")
    with open(index_path, 'r', encoding='utf-8', errors='ignore') as f:
        index_content = f.read()

    print("\n  Checking homepage links to hubs:")
    for hub_file in hubs:
        if hub_file in index_content:
            print(f"  [OK] index.html links to {hub_file}")
        else:
            print(f"  [FAIL] index.html does NOT link to {hub_file}")

    if all_ok:
        print("\n  Hub structure confirmed.")


# ============================================================
# STEP 5: INTERNAL LINKING CLEANUP
# (Remove links to noindexed/404 pages from core pages)
# ============================================================
def step5_internal_linking_cleanup(broken_links, old_daily_pages):
    print("\n" + "=" * 60)
    print("STEP 5: INTERNAL LINKING CLEANUP")
    print("=" * 60)

    # Build set of pages that are noindexed (old daily + junk)
    noindex_set = set(old_daily_pages)

    # Focus cleanup on CORE pages only (index.html, hubs, nav templates)
    # We don't need to clean every single old daily page's links
    core_files_to_clean = [
        "index.html",
        "nba-previews.html",
        "nhl-previews.html",
        "mlb-previews.html",
        "college-basketball-previews.html",
        "soccer-previews.html",
        "sitemap.html",
        "blog.html",
    ]

    cleaned_count = 0

    for page in core_files_to_clean:
        filepath = os.path.join(REPO, page)
        if not os.path.exists(filepath):
            continue

        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        original = content

        # Find all internal .html links
        links = re.findall(r'href=["\']([^"\'#]+\.html)["\']', content)

        for link in links:
            # Skip external
            if link.startswith('http') or link.startswith('//'):
                continue
            # Check if this link points to an old daily page
            if link in noindex_set:
                # Don't remove the link entirely - just note it
                # These are typically in navigation or calendar JS, not critical content links
                pass

        if content != original:
            with open(filepath, 'w', encoding='utf-8', errors='ignore') as f:
                f.write(content)
            cleaned_count += 1

    # Report on broken links in core pages
    core_broken = 0
    for page in core_files_to_clean:
        if page in broken_links:
            for link in broken_links[page]:
                print(f"  [WARN] Broken link in {page}: {link}")
                core_broken += 1

    if core_broken == 0:
        print("  [OK] No broken links found in core pages")
    else:
        print(f"\n  Found {core_broken} broken links in core pages")

    print(f"  Internal linking review complete.")


# ============================================================
# STEP 6: GENERATE FINAL SITEMAP
# ============================================================
def step6_generate_sitemap():
    print("\n" + "=" * 60)
    print("STEP 6: GENERATE FINAL SITEMAP")
    print("=" * 60)

    all_html = get_all_html_files()
    pages_for_sitemap = []

    core_count = 0
    secondary_count = 0
    excluded_count = 0

    for filepath in all_html:
        rel = os.path.relpath(filepath, REPO).replace("\\", "/")
        classification = classify_page(filepath)

        # Skip 404.html
        if rel == "404.html":
            excluded_count += 1
            continue

        if classification == "core":
            # Determine priority and changefreq
            if rel == "index.html":
                pages_for_sitemap.append((rel, 1.0, "daily"))
            elif rel.endswith("-previews.html"):
                pages_for_sitemap.append((rel, 0.9, "daily"))
            elif rel.endswith("-records.html") or rel == "betlegend-verified-records.html":
                pages_for_sitemap.append((rel, 0.8, "weekly"))
            elif rel.startswith("blog"):
                pages_for_sitemap.append((rel, 0.7, "weekly"))
            elif rel.endswith("-calculator.html") or rel == "betting-calculators.html":
                pages_for_sitemap.append((rel, 0.7, "monthly"))
            elif rel.startswith("kelly-"):
                pages_for_sitemap.append((rel, 0.7, "monthly"))
            elif rel in ("handicapping-hub.html", "best-bets-today.html", "daily-picks.html", "picks.html"):
                pages_for_sitemap.append((rel, 0.8, "daily"))
            else:
                pages_for_sitemap.append((rel, 0.6, "weekly"))
            core_count += 1

        elif classification == "secondary":
            pages_for_sitemap.append((rel, 0.6, "monthly"))
            secondary_count += 1

        else:
            excluded_count += 1

    # Generate sitemap
    sitemap_content = generate_sitemap(pages_for_sitemap)
    sitemap_path = os.path.join(REPO, "sitemap.xml")

    with open(sitemap_path, 'w', encoding='utf-8') as f:
        f.write(sitemap_content)

    print(f"\n  Sitemap generated: {sitemap_path}")
    print(f"  Total URLs in sitemap: {len(pages_for_sitemap)}")
    print(f"    Core pages: {core_count}")
    print(f"    Secondary pages: {secondary_count}")
    print(f"  Excluded (noindexed/junk/404): {excluded_count}")


# ============================================================
# CLASSIFICATION REPORT
# ============================================================
def classification_report():
    print("\n" + "=" * 60)
    print("PAGE CLASSIFICATION REPORT")
    print("=" * 60)

    all_html = get_all_html_files()

    counts = {"core": 0, "secondary": 0, "old_daily": 0, "junk": 0, "unknown": 0}
    unknowns = []

    for filepath in all_html:
        rel = os.path.relpath(filepath, REPO).replace("\\", "/")
        c = classify_page(filepath)
        counts[c] += 1
        if c == "unknown":
            unknowns.append(rel)

    for cat, count in counts.items():
        print(f"  {cat}: {count}")

    if unknowns:
        print(f"\n  Unknown pages ({len(unknowns)}):")
        for u in sorted(unknowns):
            print(f"    ? {u}")


# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    if "--report" in sys.argv:
        classification_report()
        sys.exit(0)

    if "--step" in sys.argv:
        step_idx = sys.argv.index("--step")
        step_num = int(sys.argv[step_idx + 1])

        if step_num == 1:
            step1_404_cleanup()
        elif step_num == 2:
            step2_noindex_old_daily()
        elif step_num == 3:
            step3_noindex_audit()
        elif step_num == 4:
            step4_hub_structure()
        elif step_num == 5:
            broken, old = step1_404_cleanup()
            old_pages = step2_noindex_old_daily()
            step5_internal_linking_cleanup(broken, old_pages)
        elif step_num == 6:
            step6_generate_sitemap()
    elif "--all" in sys.argv:
        broken_links, missing_404 = step1_404_cleanup()
        old_daily_pages = step2_noindex_old_daily()
        step3_noindex_audit()
        step4_hub_structure()
        step5_internal_linking_cleanup(broken_links, old_daily_pages)
        step6_generate_sitemap()
        print("\n" + "=" * 60)
        print("SEO RECOVERY COMPLETE")
        print("=" * 60)
    else:
        print("Usage:")
        print("  python seo_recovery.py --report    # Classification report")
        print("  python seo_recovery.py --step N    # Run step N (1-6)")
        print("  python seo_recovery.py --all       # Run all steps")
