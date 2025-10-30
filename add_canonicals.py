#!/usr/bin/env python3
"""
Add or fix canonical tags on all pages
"""
import glob
import re

BASE_URL = "https://www.betlegendpicks.com"

def add_or_fix_canonical(filepath):
    """Add or fix canonical tag in HTML file"""
    print(f"Processing {filepath}...")

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"  [ERROR] Could not read {filepath}: {e}")
        return False

    # Skip if not proper HTML
    if '<head>' not in content:
        print(f"  [SKIP] No <head> tag found")
        return False

    filename = filepath
    canonical_url = f"{BASE_URL}/{filename}"
    canonical_tag = f'<link href="{canonical_url}" rel="canonical"/>'

    # Check if canonical already exists
    has_canonical = 'rel="canonical"' in content or "rel='canonical'" in content

    if has_canonical:
        # Replace existing canonical
        content = re.sub(
            r'<link[^>]*rel=["\']canonical["\'][^>]*>',
            canonical_tag,
            content
        )
        print(f"  [FIXED] Updated canonical to {canonical_url}")
    else:
        # Add new canonical after <title> or before </head>
        if '</title>' in content:
            content = content.replace('</title>', f'</title>{canonical_tag}', 1)
            print(f"  [ADDED] Added canonical {canonical_url}")
        elif '</head>' in content:
            content = content.replace('</head>', f'  {canonical_tag}\n</head>', 1)
            print(f"  [ADDED] Added canonical {canonical_url}")
        else:
            print(f"  [SKIP] Could not find place to add canonical")
            return False

    # Write back
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"  [ERROR] Could not write {filepath}: {e}")
        return False

def main():
    # Important pages that need canonical tags
    important_pages = [
        'index.html',
        'blog.html',
        'blog-page2.html',
        'blog-page3.html',
        'blog-page4.html',
        'blog-page5.html',
        'blog-page6.html',
        'blog-page7.html',
        'blog-page8.html',
        'news.html',
        'news-page2.html',
        'news-page3.html',
        'betlegend-verified-records.html',
        'nfl-records.html',
        'ncaaf-records.html',
        'nhl-records.html',
        'nba-records.html',
        'soccer-records.html',
        'mlb-page2.html',
        'mlb-historical.html',
        'nfl.html',
        'nba.html',
        'nhl.html',
        'ncaaf.html',
        'betting-calculators.html',
        'expected-value-calculator.html',
        'implied-probability-calculator.html',
        'odds-converter.html',
        'parlay-calculator.html',
        'kelly-criterion.html',
        'featured-game-of-the-day.html',
        'betting-101.html',
        'bestonlinesportsbook.html',
        'live-odds.html',
        'records.html',
        'bankroll.html',
        'screenshots.html',
        'proofofpicks.html',
        'howitworks.html',
        'upcomingpicks.html',
        'subscribe.html',
    ]

    updated = 0
    skipped = 0
    errors = 0

    for page in important_pages:
        try:
            if add_or_fix_canonical(page):
                updated += 1
            else:
                skipped += 1
        except Exception as e:
            print(f"  [ERROR] {page}: {e}")
            errors += 1

    print(f"\n{'='*60}")
    print(f"Complete!")
    print(f"  Updated/Fixed: {updated} pages")
    print(f"  Skipped: {skipped} pages")
    print(f"  Errors: {errors} pages")
    print(f"{'='*60}")

if __name__ == '__main__':
    main()
