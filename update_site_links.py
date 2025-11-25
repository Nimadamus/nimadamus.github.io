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
3. Updates "Next" / "Previous" links correctly
4. Reports all changes made

Site convention:
- "Previous" = older posts (higher page number)
- "Next" = newer posts (lower page number)

Author: BetLegend Automation
"""

import os
import re
import glob

# Site directory
SITE_DIR = os.path.dirname(os.path.abspath(__file__))

# Page categories with their naming patterns
# Note: Only blog pages use the "Previous=older, Next=newer" convention
# Featured-game pages use opposite convention and are handled separately
PAGE_CATEGORIES = {
    'blog': {
        'pattern': r'blog(?:-page(\d+))?\.html',
        'base': 'blog.html',
        'numbered': 'blog-page{}.html',
        'title': 'Blog'
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


def get_page_filename(config, page_num):
    """Get filename for a page number"""
    if page_num == 1:
        return config['base']
    else:
        return config['numbered'].format(page_num)


def update_pagination_links(series):
    """Update Next/Previous page links in paginated series"""
    changes = []

    for category, info in series.items():
        pages = info['pages']
        config = info['config']
        max_page = len(pages)

        for i, (page_num, filename) in enumerate(pages):
            filepath = os.path.join(SITE_DIR, filename)

            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            original_content = content

            # Site convention:
            # "Previous" = older posts (higher page number)
            # "Next" = newer posts (lower page number)

            # Calculate correct targets
            older_page = get_page_filename(config, page_num + 1) if page_num < max_page else None
            newer_page = get_page_filename(config, page_num - 1) if page_num > 1 else None

            # Find the pagination div
            pagination_match = re.search(r'<div class="pagination"[^>]*>(.*?)</div>', content, re.DOTALL)

            if pagination_match:
                old_pagination = pagination_match.group(0)
                pagination_content = pagination_match.group(1)

                # Build new pagination content
                new_pagination_inner = ''

                # Previous link (goes to older/higher page number)
                if older_page:
                    new_pagination_inner += f'<a href="{older_page}">[Previous]</a>'
                else:
                    new_pagination_inner += '<span>[Previous]</span>'

                new_pagination_inner += '<span>   </span>'

                # Next link (goes to newer/lower page number)
                if newer_page:
                    new_pagination_inner += f'<a href="{newer_page}">Next [arrow]</a>'
                else:
                    new_pagination_inner += '<span>Next [arrow]</span>'

                # Actually, let's preserve the exact arrow format from the original
                # Just update the hrefs

                new_pagination = pagination_content

                # Update Previous link
                if older_page:
                    # Replace any existing Previous link or span
                    new_pagination = re.sub(
                        r'<a href="[^"]*">[^<]*Previous[^<]*</a>',
                        f'<a href="{older_page}">[Previous]</a>',
                        new_pagination
                    )
                    new_pagination = re.sub(
                        r'<span>[^<]*Previous[^<]*</span>',
                        f'<a href="{older_page}">[Previous]</a>',
                        new_pagination
                    )
                else:
                    # Make it a span (no link)
                    new_pagination = re.sub(
                        r'<a href="[^"]*">[^<]*Previous[^<]*</a>',
                        '<span>[Previous]</span>',
                        new_pagination
                    )

                # Update Next link
                if newer_page:
                    new_pagination = re.sub(
                        r'<a href="[^"]*">[^<]*Next[^<]*</a>',
                        f'<a href="{newer_page}">Next [arrow]</a>',
                        new_pagination
                    )
                    new_pagination = re.sub(
                        r'<span>[^<]*Next[^<]*</span>',
                        f'<a href="{newer_page}">Next [arrow]</a>',
                        new_pagination
                    )
                else:
                    new_pagination = re.sub(
                        r'<a href="[^"]*">[^<]*Next[^<]*</a>',
                        '<span>Next [arrow]</span>',
                        new_pagination
                    )

                # Restore the arrow characters
                new_pagination = new_pagination.replace('[Previous]', '\u2190 Previous')
                new_pagination = new_pagination.replace('Next [arrow]', 'Next \u2192')

                new_div = f'<div class="pagination" style="text-align:center;margin:30px 0;">{new_pagination}</div>'
                content = content.replace(old_pagination, new_div)

            if content != original_content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                changes.append(f"Updated pagination in {filename}")

    return changes


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

    # Print site structure
    print_site_structure()

    # Summary
    total_changes = len(pagination_changes)
    print(f"\n[COMPLETE] Made {total_changes} changes.")


if __name__ == "__main__":
    main()
