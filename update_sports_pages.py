#!/usr/bin/env python3
"""
BETLEGEND SPORTS PAGE MANAGEMENT SYSTEM

This script manages sports pages and ensures:
1. Main pages (nfl.html, nba.html, etc.) always contain the NEWEST content
2. When new content is added, old content shifts to archive pages
3. All pagination is automatically updated
4. All links are correct

USAGE:
  python update_sports_pages.py verify           - Verify all pages are correct
  python update_sports_pages.py fix-pagination   - Fix pagination on all pages
  python update_sports_pages.py shift-pages NBA  - Shift NBA pages to make room for new content

HOW THE SYSTEM WORKS:
- Sports dropdown ALWAYS links to main page (nba.html, nfl.html, etc.)
- Main page is ALWAYS the newest content (Page N of N)
- Archive pages are numbered: page2 (2nd newest), page3 (3rd newest), etc.
- Highest numbered page is the OLDEST content (Page 1 of N)

POSTING NEW CONTENT:
1. Run: python update_sports_pages.py shift-pages NBA
   - This moves nba.html -> nba-page2.html, nba-page2 -> nba-page3, etc.
2. Edit nba.html with your new content
3. Run: python update_sports_pages.py fix-pagination
   - This updates all "Page X of Y" numbers

Author: BetLegend Team
"""

import re
import os
import sys
import shutil
from glob import glob
from datetime import datetime

REPO = os.path.dirname(os.path.abspath(__file__))

SPORTS = ['nfl', 'nba', 'nhl', 'ncaab', 'ncaaf', 'mlb', 'soccer']

def get_page_number(filename, sport):
    """Get the page number from filename. Main page = 0, page2 = 2, etc."""
    basename = os.path.basename(filename)
    if basename == f"{sport}.html":
        return 0  # Main page (newest)
    match = re.search(rf'{sport}-page(\d+)\.html', basename)
    if match:
        return int(match.group(1))
    return -1

def get_all_pages(sport):
    """Get all pages for a sport, sorted by page number."""
    main_page = os.path.join(REPO, f"{sport}.html")
    archive_pages = sorted(
        glob(os.path.join(REPO, f"{sport}-page*.html")),
        key=lambda x: get_page_number(x, sport)
    )
    # Filter out records pages
    archive_pages = [p for p in archive_pages if 'records' not in p.lower()]

    all_pages = []
    if os.path.exists(main_page):
        all_pages.append(main_page)
    all_pages.extend(archive_pages)

    return all_pages

def fix_pagination_for_sport(sport):
    """Fix pagination for a single sport."""
    all_pages = get_all_pages(sport)
    total_pages = len(all_pages)

    if total_pages == 0:
        print(f"  No pages found for {sport}")
        return 0

    print(f"\n{sport.upper()}: {total_pages} total pages")
    fixed = 0

    for idx, filepath in enumerate(all_pages):
        filename = os.path.basename(filepath)

        # Page numbering: main page = newest = Page N of N
        # page2 = Page N-1 of N, etc.
        display_page = total_pages - idx

        # Determine newer/older links
        if idx == 0:
            newer_link = None
        else:
            newer_file = os.path.basename(all_pages[idx - 1])
            newer_link = newer_file

        if idx == len(all_pages) - 1:
            older_link = None
        else:
            older_file = os.path.basename(all_pages[idx + 1])
            older_link = older_file

        # Build pagination HTML
        if newer_link:
            newer_html = f'<a href="{newer_link}" title="Newer">&#8592; Newer</a>'
        else:
            newer_html = '<span class="disabled">&#8592; Newer</span>'

        if older_link:
            older_html = f'<a href="{older_link}" title="Older">Older &#8594;</a>'
        else:
            older_html = '<span class="disabled">Older &#8594;</span>'

        new_pagination = f'''<nav class="pagination">
{newer_html}
<span class="current">Page {display_page} of {total_pages}</span>
{older_html}
</nav>'''

        # Read file
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        original = content

        # Replace pagination nav
        content = re.sub(
            r'<nav class="pagination">.*?</nav>',
            new_pagination,
            content,
            flags=re.DOTALL
        )

        # Also fix subtitle pagination in hero section
        content = re.sub(
            r'(<p class="subtitle">)Page \d+ of \d+(</p>)',
            lambda m: f'{m.group(1)}Page {display_page} of {total_pages}{m.group(2)}',
            content
        )

        # Fix hero paragraph pagination
        content = re.sub(
            r'(Archive - Page )\d+ of \d+',
            lambda m: f'{m.group(1)}{display_page} of {total_pages}',
            content
        )

        # Fix any "Page X of Y" in span.current
        content = re.sub(
            r'(<span class="current">)Page \d+ of \d+(</span>)',
            lambda m: f'{m.group(1)}Page {display_page} of {total_pages}{m.group(2)}',
            content
        )

        if content != original:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  [FIXED] {filename}: Page {display_page} of {total_pages}")
            fixed += 1
        else:
            print(f"  [OK] {filename}: Page {display_page} of {total_pages}")

    return fixed

def verify_all_pages():
    """Verify all sports pages are correctly configured."""
    print("=" * 60)
    print("VERIFYING ALL SPORTS PAGES")
    print("=" * 60)

    for sport in SPORTS:
        all_pages = get_all_pages(sport)
        total = len(all_pages)
        print(f"\n{sport.upper()}: {total} pages")

        for idx, filepath in enumerate(all_pages):
            filename = os.path.basename(filepath)
            expected_display = total - idx

            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check pagination
            match = re.search(r'Page (\d+) of (\d+)', content)
            if match:
                curr = int(match.group(1))
                tot = int(match.group(2))
                if curr == expected_display and tot == total:
                    status = "OK"
                else:
                    status = f"WRONG (shows {curr}/{tot}, should be {expected_display}/{total})"
            else:
                status = "NO PAGINATION FOUND"

            print(f"  {filename}: {status}")

def fix_all_pagination():
    """Fix pagination on all sports pages."""
    print("=" * 60)
    print("FIXING PAGINATION ON ALL SPORTS PAGES")
    print("=" * 60)

    total_fixed = 0
    for sport in SPORTS:
        fixed = fix_pagination_for_sport(sport)
        total_fixed += fixed

    print("\n" + "=" * 60)
    print(f"COMPLETE - Fixed {total_fixed} files")
    print("=" * 60)

def shift_pages(sport):
    """
    Shift all pages for a sport to make room for new content.

    Before: nba.html (newest), nba-page2.html, nba-page3.html
    After:  nba.html (empty for new), nba-page2.html (was nba.html), nba-page3.html (was page2)
    """
    sport = sport.lower()
    if sport not in SPORTS:
        print(f"ERROR: Unknown sport '{sport}'. Valid options: {', '.join(SPORTS)}")
        return

    print("=" * 60)
    print(f"SHIFTING {sport.upper()} PAGES TO MAKE ROOM FOR NEW CONTENT")
    print("=" * 60)

    all_pages = get_all_pages(sport)
    if not all_pages:
        print(f"No pages found for {sport}")
        return

    # Get the highest page number
    page_nums = [get_page_number(p, sport) for p in all_pages]
    max_page = max([p for p in page_nums if p >= 0], default=0)

    # Create backup
    backup_dir = os.path.join(REPO, f".backup_{sport}_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    os.makedirs(backup_dir, exist_ok=True)
    for page in all_pages:
        shutil.copy2(page, backup_dir)
    print(f"Created backup in {backup_dir}")

    # Shift pages starting from the highest numbered page
    new_max = max_page + 1 if max_page >= 2 else 2

    # Rename from highest to lowest to avoid overwriting
    for page_num in range(new_max, 1, -1):
        if page_num == 2:
            # Main page becomes page2
            src = os.path.join(REPO, f"{sport}.html")
        else:
            src = os.path.join(REPO, f"{sport}-page{page_num - 1}.html")

        dst = os.path.join(REPO, f"{sport}-page{page_num}.html")

        if os.path.exists(src):
            if os.path.exists(dst):
                os.remove(dst)
            shutil.move(src, dst)
            print(f"  {os.path.basename(src)} -> {os.path.basename(dst)}")

    # Create empty main page template
    main_page = os.path.join(REPO, f"{sport}.html")
    print(f"\n  Created space for new content at {sport}.html")
    print(f"\n  NEXT STEPS:")
    print(f"  1. Edit {sport}.html with your new content")
    print(f"  2. Run: python update_sports_pages.py fix-pagination")

def print_usage():
    """Print usage information."""
    print("""
BETLEGEND SPORTS PAGE MANAGEMENT SYSTEM
========================================

USAGE:
  python update_sports_pages.py <command> [options]

COMMANDS:
  verify              - Verify all pages have correct pagination
  fix-pagination      - Fix pagination on all sports pages
  shift-pages <SPORT> - Shift pages to make room for new content

EXAMPLES:
  python update_sports_pages.py verify
  python update_sports_pages.py fix-pagination
  python update_sports_pages.py shift-pages NBA

WORKFLOW FOR POSTING NEW CONTENT:
1. python update_sports_pages.py shift-pages NBA
2. Edit nba.html with new content
3. python update_sports_pages.py fix-pagination
4. git add . && git commit -m "Add new NBA picks" && git push
""")

def main():
    if len(sys.argv) < 2:
        print_usage()
        return

    command = sys.argv[1].lower()

    if command == 'verify':
        verify_all_pages()
    elif command == 'fix-pagination':
        fix_all_pagination()
    elif command == 'shift-pages':
        if len(sys.argv) < 3:
            print("ERROR: Please specify a sport (e.g., NBA, NFL, NHL)")
            return
        shift_pages(sys.argv[2])
    elif command in ['-h', '--help', 'help']:
        print_usage()
    else:
        print(f"Unknown command: {command}")
        print_usage()

if __name__ == "__main__":
    main()
