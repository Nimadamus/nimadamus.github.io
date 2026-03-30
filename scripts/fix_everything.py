#!/usr/bin/env python3
"""Fix ALL remaining indexing issues in one pass."""
import re, os, glob
from datetime import datetime

DOMAIN = "https://www.betlegendpicks.com"
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(REPO)

# Map broken links to correct targets
LINK_MAP = {
    'betting-education-hub.html': 'betting-education.html',
    'implied-probability.html': 'implied-probability-sports-betting.html',
    'parlay-guide.html': 'parlay-betting-explained-complete-guide.html',
    'parlay-betting-guide.html': 'parlay-betting-explained-complete-guide.html',
    'odds-guide.html': 'odds.html',
    'premium.html': 'index.html',
    'sportsbettingprime.html': 'index.html',
    'test-layout-fix.html': 'index.html',
    'test_article.html': 'index.html',
    'preview-card-redesign.html': 'index.html',
    'handicapping-hub-preview.html': 'handicapping-hub.html',
    'index-preview.html': 'index.html',
    'index-compact-preview.html': 'index.html',
    'index-redesign-preview.html': 'index.html',
    'transparency-preview.html': 'index.html',
    'index-backup.html': 'index.html',
    'index-backup-march21-2026.html': 'index.html',
    'kelly-criterion_2026-02-06_backup.html': 'kelly-criterion.html',
    'input.html': 'index.html',
    'screenshots.html': 'index.html',
    'sportsbettingprime-covers-consensus-2026-02-15.html': 'index.html',
    'sportsbettingprime-covers-consensus-2025-11-24.html': 'index.html',
    'sportsbettingprime-covers-consensus-2025-11-25.html': 'index.html',
    'sportsbettingprime-covers-consensus-2025-11-26.html': 'index.html',
    'sportsbettingprime-covers-consensus-2025-11-27.html': 'index.html',
    'sportsbettingprime-covers-consensus-2025-11-28.html': 'index.html',
}

SKIP_NOINDEX = {'404.html', 'google6f74b54ecd988601.html', 'pro/404.html'}

def get_all_html():
    files = []
    for root, dirs, filenames in os.walk('.'):
        dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', '.github']]
        for f in filenames:
            if f.endswith('.html'):
                rel = os.path.relpath(os.path.join(root, f), '.').replace('\\', '/')
                files.append(rel)
    return sorted(files)

def is_redirect(content):
    return len(content) < 3000 and 'http-equiv=' in content.lower() and 'refresh' in content.lower()

def main():
    all_html = get_all_html()

    # Build link map for old dated preview pages
    for f in all_html:
        bn = os.path.basename(f)
        if re.match(r'nba-game-previews-analysis-\w+-\d+-2026\.html', bn) and not os.path.exists(bn):
            LINK_MAP[bn] = 'nba-previews.html'
        elif re.match(r'nhl-game-previews-analysis-\w+-\d+-2026\.html', bn) and not os.path.exists(bn):
            LINK_MAP[bn] = 'nhl-previews.html'
        elif re.match(r'college-basketball-game-previews-\w+-\d+-2026\.html', bn) and not os.path.exists(bn):
            LINK_MAP[bn] = 'college-basketball-previews.html'
        elif re.match(r'soccer-game-previews-analysis-\w+-\d+-2026\.html', bn) and not os.path.exists(bn):
            LINK_MAP[bn] = 'soccer-previews.html'

    stats = {'links': 0, 'canonicals': 0, 'noindex': 0, 'files_changed': 0}

    for filepath in all_html:
        if not os.path.exists(filepath):
            continue

        with open(filepath, 'r', encoding='utf-8', errors='ignore') as fh:
            content = fh.read()

        original = content
        basename = os.path.basename(filepath)

        # Fix broken internal links
        for old, new in LINK_MAP.items():
            if old in content:
                content = content.replace(old, new)
                stats['links'] += 1

        # Skip redirect stubs for canonical/meta fixes
        if is_redirect(content):
            if content != original:
                with open(filepath, 'w', encoding='utf-8') as fh:
                    fh.write(content)
                stats['files_changed'] += 1
            continue

        if filepath in SKIP_NOINDEX or basename in SKIP_NOINDEX:
            if content != original:
                with open(filepath, 'w', encoding='utf-8') as fh:
                    fh.write(content)
                stats['files_changed'] += 1
            continue

        expected = f'{DOMAIN}/{filepath}'

        # Remove any remaining noindex
        if 'noindex' in content.lower():
            content = re.sub(
                r'<meta\s+name="robots"\s+content="[^"]*noindex[^"]*"[^>]*/?>',
                '', content, flags=re.IGNORECASE
            )
            stats['noindex'] += 1

        # Fix canonical - must self-reference
        canon = re.search(r'<link[^>]*rel="canonical"[^>]*href="([^"]+)"', content)
        if canon:
            cur = canon.group(1)
            cur_base = cur.split('/')[-1]
            if cur_base != basename:
                content = re.sub(
                    r'(<link[^>]*rel="canonical"[^>]*href=")[^"]+(")',
                    lambda m: m.group(1) + expected + m.group(2),
                    content, count=1
                )
                stats['canonicals'] += 1
        elif '<head>' in content:
            content = content.replace('<head>', f'<head>\n<link rel="canonical" href="{expected}"/>', 1)
            stats['canonicals'] += 1

        if content != original:
            with open(filepath, 'w', encoding='utf-8') as fh:
                fh.write(content)
            stats['files_changed'] += 1

    # Regenerate sitemap
    today = datetime.now().strftime('%Y-%m-%d')
    urls = []
    for filepath in sorted(all_html):
        bn = os.path.basename(filepath)
        if bn in SKIP_NOINDEX or filepath in SKIP_NOINDEX:
            continue
        if filepath.startswith('scripts/') or filepath.startswith('pro/'):
            continue
        if not os.path.exists(filepath):
            continue

        with open(filepath, 'r', encoding='utf-8', errors='ignore') as fh:
            c = fh.read()
        if is_redirect(c):
            continue

        pri = 0.6
        if filepath == 'index.html': pri = 1.0
        elif 'previews.html' in filepath and '/' not in filepath: pri = 0.9
        elif filepath in ('handicapping-hub.html', 'best-bets-today.html', 'daily-picks.html', 'nfl.html'): pri = 0.8
        elif any(x in filepath for x in ('records', 'kelly-', 'blog-page', 'featured-game', 'news')): pri = 0.7

        freq = 'daily' if pri >= 0.8 else 'weekly'
        urls.append(f'  <url>\n    <loc>{DOMAIN}/{filepath}</loc>\n    <lastmod>{today}</lastmod>\n    <changefreq>{freq}</changefreq>\n    <priority>{pri}</priority>\n  </url>')

    sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + '\n'.join(urls) + '\n</urlset>'
    with open('sitemap.xml', 'w', encoding='utf-8') as f:
        f.write(sm)

    print(f"Files changed: {stats['files_changed']}")
    print(f"Link fixes: {stats['links']}")
    print(f"Canonical fixes: {stats['canonicals']}")
    print(f"Noindex removals: {stats['noindex']}")
    print(f"Sitemap URLs: {len(urls)}")

if __name__ == '__main__':
    main()
