#!/usr/bin/env python3
"""
Update Featured Game of the Day Links Across All Pages
=======================================================
REPLACES the old inline script that was documented in CLAUDE.md.

The OLD script used:
    re.sub(r'featured-game-of-the-day-page\d+\.html', NEW, c)
This replaced ALL occurrences, including canonical tags, og:url tags,
and other page-specific references. This caused ALL pages to have their
canonical pointing to the latest page, destroying Google indexing.

THIS SCRIPT:
- Only replaces navigation links (href= and sidebar links)
- PRESERVES canonical tags on each page (keeps self-referencing)
- PRESERVES og:url tags on each page (keeps self-referencing)
- PRESERVES og:url in property-first format too
- Reports what was changed

Usage:
    python scripts/update_featured_game_links.py page75
    python scripts/update_featured_game_links.py 10-michigan-state-at-wisconsin-prediction-picks-february-13-2026.html
"""

import os
import re
import sys
import glob

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATTERN = r'featured-game-of-the-day-page\d+\.html'


def update_file(filepath, new_page):
    """Update featured game links in a file, preserving canonical and og:url."""
    filename = os.path.basename(filepath)

    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    original = content
    lines = content.split('\n')
    new_lines = []
    changes = 0

    for line in lines:
        # SKIP lines containing canonical - never touch these
        if 'rel="canonical"' in line:
            new_lines.append(line)
            continue

        # SKIP lines containing og:url - never touch these
        if 'og:url' in line:
            new_lines.append(line)
            continue

        # SKIP lines containing mainEntityOfPage in JSON-LD - never touch these
        if 'mainEntityOfPage' in line:
            new_lines.append(line)
            continue

        # SKIP lines in FEATURED_GAMES data array (featured-games-data.js references)
        # These have page: "featured-game-..." format and should be preserved
        if re.search(r'page:\s*"featured-game-of-the-day-page\d+\.html"', line):
            new_lines.append(line)
            continue

        # For all other lines, replace old page references with new page
        new_line, count = re.subn(PATTERN, new_page, line)
        if count > 0:
            changes += count
        new_lines.append(new_line)

    new_content = '\n'.join(new_lines)

    if new_content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return changes
    return 0


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/update_featured_game_links.py <page_number_or_filename>")
        print("  Example: python scripts/update_featured_game_links.py page75")
        print("  Example: python scripts/update_featured_game_links.py 10-michigan-state-at-wisconsin-prediction-picks-february-13-2026.html")
        sys.exit(1)

    arg = sys.argv[1]

    # Accept either "page75" or full filename
    if arg.startswith('featured-game-of-the-day-'):
        new_page = arg
    elif arg.startswith('page'):
        new_page = f'featured-game-of-the-day-{arg}.html'
    else:
        new_page = f'featured-game-of-the-day-page{arg}.html'

    # Ensure .html extension
    if not new_page.endswith('.html'):
        new_page += '.html'

    print(f"Updating all featured game links to: {new_page}")
    print(f"Scanning: {REPO}")
    print("=" * 60)
    print("NOTE: Canonical and og:url tags are PRESERVED (not replaced)")
    print("NOTE: featured-games-data.js entries are PRESERVED")
    print("=" * 60)

    total_files = 0
    total_changes = 0

    for root, dirs, files in os.walk(REPO):
        # Skip .git directory
        dirs[:] = [d for d in dirs if d != '.git']

        for f in files:
            if f.endswith('.html'):
                filepath = os.path.join(root, f)
                changes = update_file(filepath, new_page)
                if changes > 0:
                    total_files += 1
                    total_changes += changes
                    print(f"  Updated: {os.path.relpath(filepath, REPO)} ({changes} link(s))")

    print("=" * 60)
    print(f"Files updated: {total_files}")
    print(f"Total links replaced: {total_changes}")
    print(f"\nCanonical tags: PRESERVED (not touched)")
    print(f"OG:URL tags: PRESERVED (not touched)")

    # Verify canonicals are still correct
    print("\nVerifying canonicals are still self-referencing...")
    errors = 0
    pages = glob.glob(os.path.join(REPO, 'featured-game-of-the-day-page*.html'))
    for page in pages:
        page_filename = os.path.basename(page)
        expected = f"https://www.betlegendpicks.com/{page_filename}"
        with open(page, 'r', encoding='utf-8', errors='ignore') as pf:
            page_content = pf.read()
        canonical = re.search(r'<link\s+rel="canonical"\s+href="([^"]+)"', page_content)
        if canonical and canonical.group(1) != expected:
            print(f"  ERROR: {page_filename} canonical = {canonical.group(1)}")
            errors += 1

    if errors == 0:
        print("  ALL canonicals verified correct!")
    else:
        print(f"\n  {errors} canonical errors found!")
        print("  Run: python scripts/fix_featured_game_canonicals.py")


if __name__ == '__main__':
    main()
