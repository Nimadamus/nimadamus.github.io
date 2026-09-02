#!/usr/bin/env python3
"""
fix_indexing.py - Remove all noindex tags, fix canonicals, update sitemap.

What it does:
1. Removes ALL noindex meta tags from ALL HTML files
2. For redirect stubs: keeps canonical pointing to redirect target (correct behavior)
3. For real content pages: ensures canonical is self-referencing
4. Generates updated sitemap.xml with all content pages
5. Reports everything it changed
"""

import os
import re
import glob
from datetime import datetime

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOMAIN = "https://www.betlegendpicks.com"

# Files that should genuinely NOT be indexed (not content)
SKIP_NOINDEX_REMOVAL = {
    '404.html',
    'pro/404.html',
    'google6f74b54ecd988601.html',  # Google verification
}

# Files that are test/preview/backup - remove noindex but flag for review
REVIEW_FILES = {
    'test-layout-fix.html',
    'test_article.html',
    'preview-card-redesign.html',
    'handicapping-hub-preview.html',
    'index-preview.html',
    'index-compact-preview.html',
    'index-redesign-preview.html',
    'transparency-preview.html',
    'index-backup.html',
    'index-backup-march21-2026.html',
    'kelly-criterion_2026-02-06_backup.html',
    'input.html',
    'screenshots.html',
    'sportsbettingprime-covers-consensus-2026-02-15.html',
}

def is_redirect_stub(content):
    """Check if a file is a redirect stub (meta refresh + short)."""
    if len(content) < 2000 and 'http-equiv="refresh"' in content.lower():
        return True
    if 'window.location.replace(' in content and len(content) < 3000:
        if 'Page Moved' in content or 'Redirecting' in content:
            return True
    return False

def get_redirect_target(content):
    """Extract the redirect target URL from a redirect stub."""
    m = re.search(r'http-equiv="refresh"\s+content="[^"]*url=([^"]+)"', content, re.I)
    if m:
        return m.group(1)
    return None

def remove_noindex(content):
    """Remove all noindex meta robot tags from content."""
    # Match various noindex patterns
    patterns = [
        r'<meta\s+name="robots"\s+content="[^"]*noindex[^"]*"\s*/?>',
        r'<meta\s+name="robots"\s+content="[^"]*noindex[^"]*"[^>]*/?>',
        r'<meta\s+content="[^"]*noindex[^"]*"\s+name="robots"\s*/?>',
    ]
    original = content
    for pattern in patterns:
        content = re.sub(pattern, '', content, flags=re.IGNORECASE)

    # Clean up any blank lines left behind
    content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)

    changed = content != original
    return content, changed

def fix_canonical(content, filename):
    """Ensure canonical is self-referencing for non-redirect pages."""
    expected_canonical = f'{DOMAIN}/{filename}'

    # Find existing canonical
    m = re.search(r'<link\s+rel="canonical"\s+href="([^"]+)"', content)
    if m:
        current = m.group(1)
        # Check if it points to self
        current_basename = current.split('/')[-1]
        if current_basename != filename:
            # This canonical points elsewhere - check if it's a redirect stub
            if not is_redirect_stub(content):
                # Real content page with canonical pointing elsewhere - fix it
                old_tag = m.group(0) + ('"' if not m.group(0).endswith('"') else '')
                # Actually replace the full tag
                content = re.sub(
                    r'<link\s+rel="canonical"\s+href="[^"]+"',
                    f'<link rel="canonical" href="{expected_canonical}"',
                    content
                )
                return content, True, current
    return content, False, None

def get_all_html_files():
    """Get all HTML files in the repo."""
    files = []
    for root, dirs, filenames in os.walk(REPO_ROOT):
        # Skip .git and node_modules
        dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', '.github']]
        for f in filenames:
            if f.endswith('.html'):
                rel_path = os.path.relpath(os.path.join(root, f), REPO_ROOT)
                rel_path = rel_path.replace('\\', '/')
                files.append(rel_path)
    return sorted(files)

def generate_sitemap(content_pages, redirect_stubs):
    """Generate a comprehensive sitemap.xml."""
    urls = []

    # High priority pages
    high_priority = {
        'index.html': 1.0,
        'nba-previews.html': 0.9,
        'nhl-previews.html': 0.9,
        'mlb-previews.html': 0.9,
        'college-basketball-previews.html': 0.9,
        'soccer-previews.html': 0.9,
        'best-bets-today.html': 0.8,
        'handicapping-hub.html': 0.8,
        'daily-picks.html': 0.8,
        'nfl.html': 0.8,
    }

    medium_priority_patterns = [
        'records', 'kelly-', 'blog-page', 'news-page',
        'featured-game', 'betlegend-daily',
    ]

    today = datetime.now().strftime('%Y-%m-%d')

    for page in content_pages:
        if page in SKIP_NOINDEX_REMOVAL:
            continue
        if page in REVIEW_FILES:
            continue
        if page in redirect_stubs:
            continue
        # Skip non-root-level utility files
        if page.startswith('scripts/') or page.startswith('pro/'):
            continue

        priority = high_priority.get(page, None)
        if priority is None:
            for pattern in medium_priority_patterns:
                if pattern in page:
                    priority = 0.7
                    break
        if priority is None:
            priority = 0.6

        changefreq = 'daily' if priority >= 0.8 else 'weekly'

        urls.append(f'''  <url>
    <loc>{DOMAIN}/{page}</loc>
    <lastmod>{today}</lastmod>
    <changefreq>{changefreq}</changefreq>
    <priority>{priority}</priority>
  </url>''')

    sitemap = f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{chr(10).join(urls)}
</urlset>'''

    return sitemap, len(urls)

def main():
    os.chdir(REPO_ROOT)

    all_files = get_all_html_files()

    noindex_removed = []
    canonical_fixed = []
    redirect_stubs = set()
    review_needed = []
    errors = []

    print(f"Scanning {len(all_files)} HTML files...\n")

    for filepath in all_files:
        full_path = os.path.join(REPO_ROOT, filepath)
        basename = os.path.basename(filepath)

        try:
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            errors.append(f"  ERROR reading {filepath}: {e}")
            continue

        original_content = content
        changed = False

        # Check if redirect stub
        if is_redirect_stub(content):
            redirect_stubs.add(filepath)

        # Skip noindex removal for specific files
        if basename in SKIP_NOINDEX_REMOVAL or filepath in SKIP_NOINDEX_REMOVAL:
            continue

        # Flag review files
        if basename in REVIEW_FILES:
            review_needed.append(filepath)

        # 1. Remove noindex
        if 'noindex' in content.lower():
            content, ni_changed = remove_noindex(content)
            if ni_changed:
                noindex_removed.append(filepath)
                changed = True

        # 2. Fix canonical for non-redirect content pages
        if not is_redirect_stub(content):
            content, canon_changed, old_canonical = fix_canonical(content, basename)
            if canon_changed:
                canonical_fixed.append(f"  {filepath}: was -> {old_canonical}")
                changed = True

        # Write back if changed
        if changed:
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)

    # 3. Generate new sitemap
    content_pages = [f for f in all_files if f.endswith('.html')]
    sitemap_content, sitemap_count = generate_sitemap(content_pages, redirect_stubs)

    sitemap_path = os.path.join(REPO_ROOT, 'sitemap.xml')
    with open(sitemap_path, 'w', encoding='utf-8') as f:
        f.write(sitemap_content)

    # Report
    print("=" * 70)
    print("  INDEXING FIX COMPLETE")
    print("=" * 70)

    print(f"\n1. NOINDEX TAGS REMOVED: {len(noindex_removed)} files")
    if noindex_removed:
        # Categorize
        categories = {
            'Featured Game pages': [],
            'NBA pages': [],
            'NHL pages': [],
            'NCAAB pages': [],
            'NCAAF pages': [],
            'NFL pages': [],
            'Soccer pages': [],
            'MLB pages': [],
            'Handicapping Hub dated': [],
            'Handicapping Hub archive': [],
            'Sport archive pages': [],
            'News pages': [],
            'Blog pages': [],
            'Dated preview pages': [],
            'Legacy sport main pages': [],
            'Other': [],
        }

        for f in noindex_removed:
            if 'featured-game' in f:
                categories['Featured Game pages'].append(f)
            elif f.startswith('handicapping-hub-archive/') or f == 'handicapping-hub-archive.html':
                categories['Handicapping Hub archive'].append(f)
            elif f.startswith('handicapping-hub-'):
                categories['Handicapping Hub dated'].append(f)
            elif f.startswith('archives/'):
                categories['Sport archive pages'].append(f)
            elif 'nba-game-previews' in f or 'nba-page' in f or f in ('nba.html', 'nba-dec19.html', 'nba-picks-today.html'):
                categories['NBA pages'].append(f)
            elif 'nhl-game-previews' in f or 'nhl-page' in f or f in ('nhl.html', 'nhl-dec19.html', 'nhl-picks-today.html'):
                categories['NHL pages'].append(f)
            elif 'college-basketball' in f or 'ncaab-page' in f or f in ('ncaab.html', 'ncaab-picks-today.html'):
                categories['NCAAB pages'].append(f)
            elif 'ncaaf-page' in f or f == 'ncaaf.html':
                categories['NCAAF pages'].append(f)
            elif 'nfl-page' in f or f in ('nfl.html', 'nfl-dec19.html', 'nfl-picks-predictions-against-the-spread-december-21-2025-saturday.html'):
                categories['NFL pages'].append(f)
            elif 'soccer-game-previews' in f or 'soccer-page' in f or f in ('soccer.html', 'soccer-picks-today.html'):
                categories['Soccer pages'].append(f)
            elif 'mlb' in f:
                categories['MLB pages'].append(f)
            elif 'news-page' in f:
                categories['News pages'].append(f)
            elif 'blog' in f:
                categories['Blog pages'].append(f)
            elif 'game-previews' in f:
                categories['Dated preview pages'].append(f)
            else:
                categories['Other'].append(f)

        for cat, files in categories.items():
            if files:
                print(f"  {cat}: {len(files)} files")

    print(f"\n2. CANONICALS FIXED (self-referencing): {len(canonical_fixed)} files")
    for c in canonical_fixed[:10]:
        print(c)
    if len(canonical_fixed) > 10:
        print(f"  ... and {len(canonical_fixed) - 10} more")

    print(f"\n3. REDIRECT STUBS IDENTIFIED: {len(redirect_stubs)} files")
    print("  (These keep their canonical to redirect target - correct behavior)")

    print(f"\n4. SITEMAP UPDATED: {sitemap_count} URLs (was 340)")

    print(f"\n5. FILES NEEDING MANUAL REVIEW: {len(review_needed)}")
    for f in review_needed:
        print(f"  {f}")

    if errors:
        print(f"\n6. ERRORS: {len(errors)}")
        for e in errors:
            print(e)

    print(f"\n" + "=" * 70)
    print("NEXT STEPS:")
    print("  1. Disable noindex-adding scripts (noindex_old_pages.py, etc.)")
    print("  2. git add . && git commit && git push")
    print("  3. Request re-indexing in Google Search Console")
    print("=" * 70)

if __name__ == '__main__':
    main()
