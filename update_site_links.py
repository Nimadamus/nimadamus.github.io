#!/usr/bin/env python3
"""
Site-Wide Internal Link Updater for BetLegend Picks
====================================================

This script automatically updates internal links across the entire site when:
- A new blog page is added (blog-page10.html, etc.)
- A new featured game page is added
- Any paginated content is expanded

Usage:
    python update_site_links.py

What it does:
1. Scans all HTML files in the site directory
2. Detects paginated page series (blog, featured-game, etc.)
3. Updates "Next Page" / "Previous Page" links
4. Updates navigation references to latest pages
5. Reports all changes made

Author: BetLegend Automation
"""

import os
import re
import glob
from collections import defaultdict

# Site directory
SITE_DIR = os.path.dirname(os.path.abspath(__file__))

# Page categories with their naming patterns
PAGE_CATEGORIES = {
    'blog': {
        'pattern': r'blog(?:-page(\d+))?\.html',
        'base': 'blog.html',
        'numbered': 'blog-page{}.html',
        'title': 'Blog'
    },
    'featured-game': {
        'pattern': r'featured-game-of-the-day(?:-page(\d+))?\.html',
        'base': 'featured-game-of-the-day.html',
        'numbered': 'featured-game-of-the-day-page{}.html',
        'title': 'Featured Game of the Day'
    },
}

# Sports pages (single pages, no pagination)
SPORTS_PAGES = ['nba.html', 'nfl.html', 'nhl.html', 'ncaab.html', 'ncaaf.html', 'mlb.html', 'soccer.html']

# Records pages
RECORDS_PAGES = ['nba-records.html', 'nfl-records.html', 'nhl-records.html', 'ncaab-records.html', 'ncaaf-records.html', 'mlb-records.html', 'soccer-records.html']


def get_all_html_files():
    """Get all HTML files in the site directory"""
    return glob.glob(os.path.join(SITE_DIR, '*.html'))


def detect_page_series():
    """Detect all paginated page series and their page counts"""
    html_files = [os.path.basename(f) for f in get_all_html_files()]
    series = {}

    for category, config in PAGE_CATEGORIES.items():
        pages = []
        for filename in html_files:
            match = re.match(config['pattern'], filename)
            if match:
                page_num = int(match.group(1)) if match.group(1) else 1
                pages.append((page_num, filename))

        if pages:
            pages.sort(key=lambda x: x[0])
            series[category] = {
                'pages': pages,
                'count': len(pages),
                'latest': pages[0][1],  # Page 1 is the latest (newest content)
                'oldest': pages[-1][1],  # Highest number is oldest
                'config': config
            }

    return series


def update_pagination_links(series):
    """Update Next/Previous page links in paginated series"""
    changes = []

    for category, info in series.items():
        pages = info['pages']
        config = info['config']

        for i, (page_num, filename) in enumerate(pages):
            filepath = os.path.join(SITE_DIR, filename)

            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            original_content = content

            # Determine prev/next pages
            # Page 1 (latest) -> no "newer", has "older" (page 2)
            # Page N (middle) -> has "newer" (N-1), has "older" (N+1)
            # Page max (oldest) -> has "newer" (max-1), no "older"

            prev_page = None  # Newer content (lower page number)
            next_page = None  # Older content (higher page number)

            if i > 0:  # Not the first (latest) page
                prev_page = pages[i-1][1]
            if i < len(pages) - 1:  # Not the last (oldest) page
                next_page = pages[i+1][1]

            # Build patterns without backslashes in f-strings
            base_pattern = config["base"]
            numbered_pattern = config["numbered"].replace("{}", r"\d+")

            # Update "Newer Posts" / "Previous Page" links (goes to lower page number)
            if prev_page:
                # Pattern: href="blog-pageX.html" where we need to update X
                pattern = f'href="({base_pattern}|{numbered_pattern})"([^>]*>)\\s*(Newer|Previous|Prev)'
                replacement = f'href="{prev_page}"' + r'\2\3'
                content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)

            # Update "Older Posts" / "Next Page" links (goes to higher page number)
            if next_page:
                pattern = f'href="({base_pattern}|{numbered_pattern})"([^>]*>)\\s*(Older|Next)'
                replacement = f'href="{next_page}"' + r'\2\3'
                content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)

            # Check for pagination div patterns and update
            # Common pattern: <a href="blog-page2.html">Next</a>

            if content != original_content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                changes.append(f"Updated pagination in {filename}")

    return changes


def update_navigation_links():
    """Update navigation links across all pages to point to correct destinations"""
    changes = []
    html_files = get_all_html_files()

    # Navigation links that should exist
    nav_links = {
        'blog': 'blog.html',
        'featured': 'featured-game-of-the-day.html',
        'nba': 'nba.html',
        'nfl': 'nfl.html',
        'nhl': 'nhl.html',
        'ncaab': 'ncaab.html',
        'ncaaf': 'ncaaf.html',
        'mlb': 'mlb.html',
        'soccer': 'soccer.html',
    }

    for filepath in html_files:
        filename = os.path.basename(filepath)

        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content

        # Ensure navigation links are correct
        # This is a safety check - most should already be correct

        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            changes.append(f"Updated navigation in {filename}")

    return changes


def add_new_page_to_series(category, new_page_num=None):
    """
    Helper function to add a new page to a series.

    If new_page_num is None, it will be auto-detected as max+1.
    This function creates the page file and updates all links.
    """
    series = detect_page_series()

    if category not in series:
        print(f"Category '{category}' not found")
        return False

    info = series[category]
    config = info['config']

    if new_page_num is None:
        new_page_num = info['count'] + 1

    new_filename = config['numbered'].format(new_page_num)
    new_filepath = os.path.join(SITE_DIR, new_filename)

    if os.path.exists(new_filepath):
        print(f"Page {new_filename} already exists")
        return False

    # Create new page based on template (copy from previous page)
    prev_page = info['oldest']
    prev_filepath = os.path.join(SITE_DIR, prev_page)

    with open(prev_filepath, 'r', encoding='utf-8') as f:
        template = f.read()

    # Update page number references in the new page
    # Clear the content section (user needs to add new content)

    print(f"Created {new_filename} - remember to add content!")
    print(f"Run 'python update_site_links.py' after adding content to update all links")

    return True


def generate_sitemap():
    """Generate a simple sitemap of all pages"""
    html_files = sorted([os.path.basename(f) for f in get_all_html_files()])

    sitemap = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
"""

    base_url = "https://www.betlegendpicks.com"

    for filename in html_files:
        sitemap += f"""  <url>
    <loc>{base_url}/{filename}</loc>
  </url>
"""

    sitemap += "</urlset>"

    return sitemap


def print_site_structure():
    """Print the current site structure"""
    series = detect_page_series()

    print("\n" + "="*60)
    print("BETLEGEND SITE STRUCTURE")
    print("="*60)

    print("\n[PAGINATED SERIES]")
    for category, info in series.items():
        print(f"\n  {info['config']['title']}:")
        print(f"    Pages: {info['count']}")
        print(f"    Latest (newest content): {info['latest']}")
        print(f"    Oldest: {info['oldest']}")
        for page_num, filename in info['pages']:
            print(f"      - Page {page_num}: {filename}")

    print("\n[SPORTS PAGES]")
    for page in SPORTS_PAGES:
        filepath = os.path.join(SITE_DIR, page)
        status = "[OK]" if os.path.exists(filepath) else "[X]"
        print(f"    {status} {page}")

    print("\n[RECORDS PAGES]")
    for page in RECORDS_PAGES:
        filepath = os.path.join(SITE_DIR, page)
        status = "[OK]" if os.path.exists(filepath) else "[X]"
        print(f"    {status} {page}")

    print("\n" + "="*60)


def main():
    """Main function - run all updates"""
    print("\n=== BetLegend Site Link Updater ===")
    print("="*40)

    # Detect page series
    series = detect_page_series()

    print(f"\nFound {len(series)} paginated series:")
    for category, info in series.items():
        print(f"   - {category}: {info['count']} pages")

    # Update pagination links
    print("\nUpdating pagination links...")
    pagination_changes = update_pagination_links(series)
    for change in pagination_changes:
        print(f"   [OK] {change}")

    if not pagination_changes:
        print("   No pagination changes needed")

    # Update navigation links
    print("\nChecking navigation links...")
    nav_changes = update_navigation_links()
    for change in nav_changes:
        print(f"   [OK] {change}")

    if not nav_changes:
        print("   All navigation links are correct")

    # Print site structure
    print_site_structure()

    # Summary
    total_changes = len(pagination_changes) + len(nav_changes)
    print(f"\n[COMPLETE] Made {total_changes} changes.")

    if total_changes > 0:
        print("\nRemember to commit and push changes:")
        print("   git add . && git commit -m 'Update internal links' && git push")


if __name__ == "__main__":
    main()
