#!/usr/bin/env python3
"""
Update Featured Game of the Day Links Across All Pages
=======================================================

Updates all nav bar "Featured Game" links across the entire site to point
to the newest featured game page.

Supports BOTH old page## format AND new keyword-rich format:
  OLD: featured-game-of-the-day-page75.html
  NEW: knicks-vs-lakers-analysis-stats-preview-march-8-2026.html

This script:
- Takes the OLD featured game filename and NEW featured game filename
- Replaces all nav link occurrences of OLD with NEW
- PRESERVES canonical tags on each page (keeps self-referencing)
- PRESERVES og:url tags on each page (keeps self-referencing)
- PRESERVES mainEntityOfPage in JSON-LD
- PRESERVES featured-games-data.js entries

Usage:
    # Auto-detect old filename, provide new one:
    python scripts/update_featured_game_links.py knicks-vs-lakers-analysis-stats-preview-march-8-2026.html

    # Explicit old and new:
    python scripts/update_featured_game_links.py --old warriors-vs-thunder-nba-analysis-stats-preview-march-7-2026.html --new knicks-vs-lakers-analysis-stats-preview-march-8-2026.html

    # Old page## format still works:
    python scripts/update_featured_game_links.py --old featured-game-of-the-day-page75.html --new knicks-vs-lakers-analysis-stats-preview-march-8-2026.html
"""

import os
import re
import sys
import glob

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def detect_current_featured_game():
    """Auto-detect the current featured game filename from index.html nav links."""
    index_path = os.path.join(REPO, 'index.html')
    if not os.path.exists(index_path):
        return None

    with open(index_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # Look for Featured Game nav link
    # Pattern: href="FILENAME">Featured Game
    match = re.search(r'href="([^"]+)"[^>]*>Featured Game', content)
    if match:
        return match.group(1)

    # Fallback: look for old page## pattern anywhere in nav
    match = re.search(r'href="(featured-game-of-the-day-page\d+\.html)"', content)
    if match:
        return match.group(1)

    # Fallback: look for any *-analysis-stats-preview-*.html in nav
    match = re.search(r'href="([^"]*analysis-stats-preview[^"]*\.html)"', content)
    if match:
        return match.group(1)

    return None


def update_file(filepath, old_page, new_page):
    """Update featured game links in a file, preserving canonical and og:url."""
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    if old_page not in content:
        return 0

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

        # SKIP lines containing mainEntityOfPage in JSON-LD
        if 'mainEntityOfPage' in line:
            new_lines.append(line)
            continue

        # SKIP lines in FEATURED_GAMES data array (featured-games-data.js references)
        if 'page:' in line and old_page in line and ('FEATURED_GAMES' in content[:500] or 'featured-games-data' in filepath):
            new_lines.append(line)
            continue

        # For all other lines, replace old page reference with new page
        if old_page in line:
            new_line = line.replace(old_page, new_page)
            changes += line.count(old_page)
            new_lines.append(new_line)
        else:
            new_lines.append(line)

    new_content = '\n'.join(new_lines)

    if new_content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return changes
    return 0


def main():
    old_page = None
    new_page = None

    args = sys.argv[1:]

    # Parse arguments
    i = 0
    while i < len(args):
        if args[i] == '--old' and i + 1 < len(args):
            old_page = args[i + 1]
            i += 2
        elif args[i] == '--new' and i + 1 < len(args):
            new_page = args[i + 1]
            i += 2
        elif not new_page:
            # Single positional arg = new page (auto-detect old)
            new_page = args[i]
            i += 1
        else:
            i += 1

    if not new_page:
        print("Usage:")
        print("  python scripts/update_featured_game_links.py NEW_FILENAME.html")
        print("  python scripts/update_featured_game_links.py --old OLD.html --new NEW.html")
        print()
        print("Examples:")
        print("  python scripts/update_featured_game_links.py knicks-vs-lakers-analysis-stats-preview-march-8-2026.html")
        print("  python scripts/update_featured_game_links.py --old warriors-vs-thunder.html --new knicks-vs-lakers.html")
        sys.exit(1)

    # Ensure .html extension
    if not new_page.endswith('.html'):
        new_page += '.html'

    # Auto-detect old page if not provided
    if not old_page:
        old_page = detect_current_featured_game()
        if not old_page:
            print("[ERROR] Could not auto-detect current featured game filename.")
            print("        Use --old to specify it manually.")
            sys.exit(1)

    if old_page == new_page:
        print(f"[OK] Featured game links already point to: {new_page}")
        sys.exit(0)

    print("=" * 60)
    print("  FEATURED GAME LINK UPDATER")
    print("=" * 60)
    print(f"  OLD: {old_page}")
    print(f"  NEW: {new_page}")
    print()
    print("  Canonical/og:url tags: PRESERVED (not touched)")
    print("  featured-games-data.js entries: PRESERVED")
    print("=" * 60)

    total_files = 0
    total_changes = 0

    for root, dirs, files in os.walk(REPO):
        # Skip .git and node_modules
        dirs[:] = [d for d in dirs if d not in ('.git', 'node_modules')]

        for f in files:
            if f.endswith('.html') or f.endswith('.js'):
                filepath = os.path.join(root, f)

                # Skip featured-games-data.js (calendar data entries)
                if f == 'featured-games-data.js':
                    continue

                changes = update_file(filepath, old_page, new_page)
                if changes > 0:
                    total_files += 1
                    total_changes += changes
                    if total_files <= 20:
                        print(f"  Updated: {os.path.relpath(filepath, REPO)} ({changes} link(s))")

    if total_files > 20:
        print(f"  ... and {total_files - 20} more files")

    print()
    print("=" * 60)
    print(f"  Files updated: {total_files}")
    print(f"  Total links replaced: {total_changes}")
    print("=" * 60)

    return 0


if __name__ == '__main__':
    sys.exit(main())
