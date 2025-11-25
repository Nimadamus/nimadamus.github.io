#!/usr/bin/env python3
"""
Site-Wide Internal Link Updater for BetLegend Picks
====================================================

Automatically updates pagination links AND navigation links when new pages are added.

Blog pages: Page 1 = newest, higher pages = older
Featured Game pages: Page 1 = oldest, higher pages = newer
"""

import os
import re
import glob

SITE_DIR = os.path.dirname(os.path.abspath(__file__))


def get_all_html_files():
    return glob.glob(os.path.join(SITE_DIR, '*.html'))


def detect_blog_pages():
    """Detect blog pages: blog.html, blog-page2.html, etc."""
    html_files = [os.path.basename(f) for f in get_all_html_files()]
    pages = []

    for filename in html_files:
        match = re.match(r'blog(?:-page(\d+))?\.html', filename)
        if match:
            page_num = int(match.group(1)) if match.group(1) else 1
            pages.append((page_num, filename))

    pages.sort(key=lambda x: x[0])
    return pages


def detect_featured_game_pages():
    """Detect featured game pages"""
    html_files = [os.path.basename(f) for f in get_all_html_files()]
    pages = []

    for filename in html_files:
        match = re.match(r'featured-game-of-the-day(?:-page(\d+))?\.html', filename)
        if match:
            page_num = int(match.group(1)) if match.group(1) else 1
            pages.append((page_num, filename))

    pages.sort(key=lambda x: x[0])
    return pages


def get_blog_filename(page_num):
    if page_num == 1:
        return 'blog.html'
    return f'blog-page{page_num}.html'


def get_featured_filename(page_num):
    if page_num == 1:
        return 'featured-game-of-the-day.html'
    return f'featured-game-of-the-day-page{page_num}.html'


def update_blog_pagination(pages):
    """Update blog pagination - Page 1 = newest"""
    changes = []
    max_page = len(pages)

    for page_num, filename in pages:
        filepath = os.path.join(SITE_DIR, filename)

        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        original = content

        # Blog: Previous = older (higher #), Next = newer (lower #)
        older_page = get_blog_filename(page_num + 1) if page_num < max_page else None
        newer_page = get_blog_filename(page_num - 1) if page_num > 1 else None

        # Find pagination div
        match = re.search(r'<div class="pagination"[^>]*>(.*?)</div>', content, re.DOTALL)
        if match:
            old_div = match.group(0)

            # Build new pagination
            parts = []

            # Previous link (older = higher page number)
            if older_page:
                parts.append(f'<a href="{older_page}">\u2190 Previous</a>')
            else:
                parts.append('<span>\u2190 Previous</span>')

            parts.append('<span>   </span>')

            # Next link (newer = lower page number)
            if newer_page:
                parts.append(f'<a href="{newer_page}">Next \u2192</a>')
            else:
                parts.append('<span>Next \u2192</span>')

            new_div = '<div class="pagination" style="text-align:center;margin:30px 0;">' + ''.join(parts) + '</div>'
            content = content.replace(old_div, new_div)

        if content != original:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            changes.append(filename)

    return changes


def update_featured_game_pagination(pages):
    """Update featured game pagination - Page 1 = oldest, highest = newest"""
    changes = []
    max_page = len(pages)

    for page_num, filename in pages:
        filepath = os.path.join(SITE_DIR, filename)

        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        original = content

        # Featured: Next = newer (higher #), Previous = older (lower #)
        newer_page = get_featured_filename(page_num + 1) if page_num < max_page else None
        older_page = get_featured_filename(page_num - 1) if page_num > 1 else None

        # Determine label
        if page_num == 1:
            page_label = "Page 1 (Oldest)"
        elif page_num == max_page:
            page_label = f"Page {page_num} (Newest)"
        else:
            page_label = f"Page {page_num}"

        # Find pagination div
        match = re.search(r'<div class="pagination"[^>]*>(.*?)</div>', content, re.DOTALL)
        if match:
            old_div = match.group(0)

            # Build new pagination (format: Next on left, label in middle, Previous on right)
            parts = []

            # Next link (newer = higher page number) - on the LEFT with left arrow
            if newer_page:
                next_num = page_num + 1
                parts.append(f'<a href="{newer_page}">\u2190 Next (Page {next_num})</a>')
            else:
                parts.append('<a href="#" class="disabled">\u2190 Next</a>')

            # Page label in middle
            parts.append(f'\n<span style="color: var(--text-secondary);">{page_label}</span>')

            # Previous link (older = lower page number) - on the RIGHT with right arrow
            if older_page:
                prev_num = page_num - 1
                parts.append(f'\n<a href="{older_page}">Previous (Page {prev_num}) \u2192</a>')
            else:
                parts.append('\n<a href="#" class="disabled">Previous \u2192</a>')

            new_div = '<div class="pagination">\n' + ''.join(parts) + '\n</div>'
            content = content.replace(old_div, new_div)

        if content != original:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            changes.append(filename)

    return changes


def update_nav_links_sitewide(featured_pages):
    """Update navigation links across ALL HTML files to point to the newest featured game page"""
    changes = []

    if not featured_pages:
        return changes

    # Get the newest featured game page (highest page number)
    max_page_num = max(p[0] for p in featured_pages)
    newest_page = get_featured_filename(max_page_num)

    html_files = get_all_html_files()

    for filepath in html_files:
        filename = os.path.basename(filepath)

        # Skip the featured game pages themselves (their internal links should vary)
        if filename.startswith('featured-game-of-the-day'):
            continue

        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        original = content

        # Update ALL nav links that point to any featured-game page
        # Pattern 1: "Game of the Day" links (dropdown and direct nav)
        content = re.sub(
            r'<a href="featured-game-of-the-day(?:-page\d+)?\.html"([^>]*)>Game of the Day</a>',
            f'<a href="{newest_page}"\\1>Game of the Day</a>',
            content
        )

        # Pattern 2: "Featured Game of the Day" links (sitemap, etc.)
        content = re.sub(
            r'<a href="featured-game-of-the-day(?:-page\d+)?\.html"([^>]*)>Featured Game of the Day</a>',
            f'<a href="{newest_page}"\\1>Featured Game of the Day</a>',
            content
        )

        # Pattern 3: "Back to Latest Featured Game" links (calendar)
        content = re.sub(
            r'<a href="featured-game-of-the-day(?:-page\d+)?\.html"([^>]*)>([^<]*Latest Featured Game[^<]*)</a>',
            f'<a href="{newest_page}"\\1>\\2</a>',
            content
        )

        # Pattern 4: onclick handlers pointing to featured game pages (calendar days)
        content = re.sub(
            r"onclick=\"window\.location\.href='featured-game-of-the-day(?:-page\d+)?\.html'\"",
            f"onclick=\"window.location.href='{newest_page}'\"",
            content
        )

        if content != original:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            changes.append(filename)

    return changes


def main():
    print("\n=== BetLegend Site Link Updater ===")
    print("="*40)

    # Blog pages
    blog_pages = detect_blog_pages()
    print(f"\nBlog pages: {len(blog_pages)}")

    blog_changes = update_blog_pagination(blog_pages)
    for f in blog_changes:
        print(f"  [OK] {f}")
    if not blog_changes:
        print("  No changes needed")

    # Featured game pages
    featured_pages = detect_featured_game_pages()
    print(f"\nFeatured Game pages: {len(featured_pages)}")

    # Show newest page
    if featured_pages:
        max_num = max(p[0] for p in featured_pages)
        newest = get_featured_filename(max_num)
        print(f"  Newest: {newest}")

    featured_changes = update_featured_game_pagination(featured_pages)
    for f in featured_changes:
        print(f"  [OK] {f}")
    if not featured_changes:
        print("  No pagination changes needed")

    # Update navigation links site-wide
    print(f"\nUpdating nav links site-wide...")
    nav_changes = update_nav_links_sitewide(featured_pages)
    print(f"  Updated {len(nav_changes)} files")
    if nav_changes and len(nav_changes) <= 10:
        for f in nav_changes:
            print(f"    - {f}")

    total = len(blog_changes) + len(featured_changes) + len(nav_changes)
    print(f"\n[COMPLETE] Made {total} total changes.")


if __name__ == "__main__":
    main()
