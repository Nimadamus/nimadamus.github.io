#!/usr/bin/env python3
"""
noindex_old_pages.py - Add noindex to all old sport preview pages
and update their canonical URLs to point to the new rolling hub pages.

This script finds all old dated/numbered sport preview pages and:
1. Adds <meta name="robots" content="noindex, follow"> (or updates existing)
2. Updates canonical URL to point to the corresponding hub page
3. Skips the 5 new hub pages (those stay indexed)
4. Skips non-sport pages (featured game, blog, news, etc.)

Usage: python scripts/noindex_old_pages.py [--dry-run]
"""

import os
import re
import sys
import glob

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)

# The 5 hub pages - NEVER touch these
HUB_PAGES = {
    'nba-previews.html',
    'nhl-previews.html',
    'mlb-previews.html',
    'college-basketball-previews.html',
    'soccer-previews.html',
}

# Archive pages already have noindex
ARCHIVE_PAGES_PATTERN = '*-previews-archive-*.html'

# Map old pages to their hub canonical
SPORT_MAPPING = {
    'nba': 'https://www.betlegendpicks.com/nba-previews.html',
    'nhl': 'https://www.betlegendpicks.com/nhl-previews.html',
    'mlb': 'https://www.betlegendpicks.com/mlb-previews.html',
    'ncaab': 'https://www.betlegendpicks.com/college-basketball-previews.html',
    'college-basketball': 'https://www.betlegendpicks.com/college-basketball-previews.html',
    'soccer': 'https://www.betlegendpicks.com/soccer-previews.html',
}

# Files to skip (not sport preview pages)
SKIP_PATTERNS = [
    'index.html',
    'featured-game*',
    'blog-*',
    'news*',
    'handicapping-hub*',
    'injury-report*',
    'records*',
    '*-records.html',
    'proofofpicks*',
    'live-odds*',
    'howitworks*',
    'bankroll*',
    'kelly-*',
    'risk-of-ruin*',
    'betting-*',
    'contact*',
    'privacy*',
    'terms*',
    'podcast*',
    'screenshots*',
    'bestonline*',
    'moneyline-parlay*',
    'best-bets-today*',
    'mobile-optimize*',
    'crosssport*',
    '*-calendar.html',
    'test-*',
    'index-*',
    '*-redesign*',
    '*-backup*',
    'newlogo*',
    '404.html',
    'CNAME',
    'sitemap*',
    'robots.txt',
]


def identify_sport(filename):
    """Determine which sport a file belongs to."""
    fn = filename.lower()

    # Direct matches for old main pages
    if fn == 'nba.html':
        return 'nba'
    if fn == 'nhl.html':
        return 'nhl'
    if fn == 'mlb.html':
        return 'mlb'
    if fn == 'ncaab.html':
        return 'ncaab'
    if fn == 'soccer.html':
        return 'soccer'

    # Picks-today redirects (already noindexed, but ensure canonical is right)
    if 'nba-picks-today' in fn:
        return 'nba'
    if 'nhl-picks-today' in fn:
        return 'nhl'
    if 'ncaab-picks-today' in fn:
        return 'ncaab'
    if 'soccer-picks-today' in fn:
        return 'soccer'

    # Page-numbered files
    if fn.startswith('nba-page') or fn.startswith('nba-'):
        if 'nba' in fn and ('page' in fn or 'picks' in fn or 'game' in fn or 'analysis' in fn or 'preview' in fn):
            return 'nba'
    if fn.startswith('nhl-page') or fn.startswith('nhl-'):
        if 'nhl' in fn:
            return 'nhl'
    if fn.startswith('ncaab-page') or fn.startswith('ncaab-') or fn.startswith('college-basketball'):
        if 'ncaab' in fn or 'college-basketball' in fn:
            return 'ncaab'
    if fn.startswith('soccer-page') or fn.startswith('soccer-'):
        if 'soccer' in fn:
            return 'soccer'
    if fn.startswith('mlb-page') or fn.startswith('mlb-'):
        if 'mlb' in fn:
            return 'mlb'

    # Keyword-rich dated files with sport in the name
    if '-nba-' in fn or fn.endswith('-nba.html'):
        return 'nba'
    if '-nhl-' in fn or fn.endswith('-nhl.html'):
        return 'nhl'
    if '-ncaab-' in fn or '-college-basketball-' in fn:
        return 'ncaab'
    if '-soccer-' in fn or fn.endswith('-soccer.html'):
        return 'soccer'
    if '-mlb-' in fn or fn.endswith('-mlb.html'):
        return 'mlb'

    return None


def should_skip(filename):
    """Check if file should be skipped."""
    import fnmatch

    # Skip hub pages
    if filename in HUB_PAGES:
        return True

    # Skip archive pages
    if fnmatch.fnmatch(filename, ARCHIVE_PAGES_PATTERN):
        return True

    # Skip non-sport pages
    for pattern in SKIP_PATTERNS:
        if fnmatch.fnmatch(filename, pattern):
            return True

    return False


def process_file(filepath, canonical_url, dry_run=False):
    """Add noindex and update canonical for a single file."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
    except Exception as e:
        print(f"  ERROR reading {filepath}: {e}")
        return False

    original = content
    changes = []

    # Check if already noindexed
    has_noindex = bool(re.search(r'<meta[^>]*content=["\']noindex', content, re.IGNORECASE))

    if not has_noindex:
        # Check for existing robots meta tag
        robots_match = re.search(r'<meta[^>]*name=["\']robots["\'][^>]*content=["\']([^"\']*)["\'][^>]*/?>',
                                  content, re.IGNORECASE)
        if not robots_match:
            robots_match = re.search(r'<meta[^>]*content=["\']([^"\']*)["\'][^>]*name=["\']robots["\'][^>]*/?>',
                                      content, re.IGNORECASE)

        if robots_match:
            # Replace existing robots tag
            old_tag = robots_match.group(0)
            new_tag = '<meta name="robots" content="noindex, follow"/>'
            content = content.replace(old_tag, new_tag, 1)
            changes.append(f"Updated robots: {robots_match.group(1)} -> noindex, follow")
        else:
            # Insert after charset or viewport meta
            insert_patterns = [
                (r'(<meta[^>]*charset[^>]*/?>)', r'\1\n<meta name="robots" content="noindex, follow"/>'),
                (r'(<meta[^>]*viewport[^>]*/?>)', r'\1\n<meta name="robots" content="noindex, follow"/>'),
                (r'(<head[^>]*>)', r'\1\n<meta name="robots" content="noindex, follow"/>'),
            ]
            inserted = False
            for pattern, replacement in insert_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    content = re.sub(pattern, replacement, content, count=1, flags=re.IGNORECASE)
                    inserted = True
                    changes.append("Added noindex meta tag")
                    break
            if not inserted:
                changes.append("WARNING: Could not find insertion point for noindex")
    else:
        changes.append("Already noindexed")

    # Update canonical to point to hub
    canonical_match = re.search(r'<link[^>]*rel=["\']canonical["\'][^>]*href=["\']([^"\']*)["\'][^>]*/?>',
                                 content, re.IGNORECASE)
    if not canonical_match:
        canonical_match = re.search(r'<link[^>]*href=["\']([^"\']*)["\'][^>]*rel=["\']canonical["\'][^>]*/?>',
                                     content, re.IGNORECASE)

    if canonical_match:
        old_canonical = canonical_match.group(1)
        if old_canonical != canonical_url:
            old_tag = canonical_match.group(0)
            new_tag = f'<link href="{canonical_url}" rel="canonical"/>'
            content = content.replace(old_tag, new_tag, 1)
            changes.append(f"Canonical: {old_canonical} -> {canonical_url}")
        else:
            changes.append("Canonical already correct")
    else:
        # Add canonical after robots or in head
        insert_point = content.find('<meta name="robots"')
        if insert_point == -1:
            insert_point = content.find('</head>')
        if insert_point > 0:
            # Find end of that line
            line_end = content.find('\n', insert_point)
            if line_end > 0:
                content = content[:line_end+1] + f'<link href="{canonical_url}" rel="canonical"/>\n' + content[line_end+1:]
                changes.append(f"Added canonical: {canonical_url}")

    if content != original:
        if not dry_run:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
        return changes
    return changes


def main():
    dry_run = '--dry-run' in sys.argv

    if dry_run:
        print("=" * 60)
        print("  DRY RUN - No files will be modified")
        print("=" * 60)

    print("=" * 60)
    print("  NOINDEX OLD SPORT PREVIEW PAGES")
    print("=" * 60)

    os.chdir(REPO_ROOT)

    # Find all HTML files in repo root
    all_html = sorted(glob.glob('*.html'))

    processed = 0
    skipped = 0
    errors = 0
    already_done = 0
    sport_counts = {}

    for filename in all_html:
        if should_skip(filename):
            continue

        sport = identify_sport(filename)
        if sport is None:
            # Not a sport preview page
            continue

        canonical_url = SPORT_MAPPING.get(sport)
        if canonical_url is None:
            continue

        filepath = os.path.join(REPO_ROOT, filename)
        changes = process_file(filepath, canonical_url, dry_run)

        if changes:
            has_real_changes = any(c not in ["Already noindexed", "Canonical already correct"] for c in changes)
            if has_real_changes:
                processed += 1
                sport_counts[sport] = sport_counts.get(sport, 0) + 1
                if dry_run or processed <= 10:  # Show first 10 in detail
                    print(f"  [{sport.upper()}] {filename}")
                    for c in changes:
                        print(f"    -> {c}")
            else:
                already_done += 1

    print()
    print("=" * 60)
    print("  SUMMARY")
    print("=" * 60)
    print(f"  Files modified: {processed}")
    print(f"  Already noindexed: {already_done}")
    print(f"  Skipped (non-sport): {skipped}")
    if sport_counts:
        print()
        for sport, count in sorted(sport_counts.items()):
            print(f"    {sport.upper()}: {count} files")
    print()
    if dry_run:
        print("  This was a DRY RUN. Run without --dry-run to apply changes.")
    else:
        print("  Done! Run: git add . && git commit -m 'Noindex old sport pages' && git push")
    print("=" * 60)


if __name__ == '__main__':
    main()
