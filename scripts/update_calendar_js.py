"""
Script to update all featured-game-of-the-day pages to use the centralized calendar JavaScript.
This removes inline ARCHIVE_DATA and replaces it with a reference to the shared JS file.
"""

import os
import re
import glob

REPO = r'C:\Users\Nima\nimadamus.github.io'

# Pattern to find and remove the old inline calendar JavaScript
# This matches from "// Featured Games Archive Data" or "const ARCHIVE_DATA" to the closing script tag
OLD_CALENDAR_PATTERN = re.compile(
    r'<script>\s*\n?'  # Opening script tag
    r'(?://\s*Featured Games Archive Data.*?\n)?'  # Optional comment
    r'const ARCHIVE_DATA = \[[\s\S]*?'  # ARCHIVE_DATA array
    r'renderCalendar\([^)]+\);?\s*'  # renderCalendar call
    r'(?:monthSelect\.addEventListener[\s\S]*?)?\s*'  # Optional event listener
    r'</script>',  # Closing script tag
    re.MULTILINE
)

# Alternative pattern for variations in the code
ALT_CALENDAR_PATTERN = re.compile(
    r'<script>\s*\n?'
    r'const ARCHIVE_DATA = \[[\s\S]*?'
    r'</script>',
    re.MULTILINE
)

# The new script reference
NEW_SCRIPT = '<script src="scripts/featured-games-calendar.js"></script>'

def update_page(filepath):
    """Update a single page to use the centralized calendar JS."""
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    original = content

    # Check if already using the new script
    if 'scripts/featured-games-calendar.js' in content:
        print(f'  SKIP: {os.path.basename(filepath)} - already updated')
        return False

    # Try to find and replace the old calendar script
    if OLD_CALENDAR_PATTERN.search(content):
        content = OLD_CALENDAR_PATTERN.sub(NEW_SCRIPT, content)
    elif ALT_CALENDAR_PATTERN.search(content):
        content = ALT_CALENDAR_PATTERN.sub(NEW_SCRIPT, content)
    else:
        # Try a more targeted approach - find script tag containing ARCHIVE_DATA
        if 'const ARCHIVE_DATA = [' in content:
            # Find the script section manually
            start_patterns = [
                '<script>\n// Featured Games Archive Data',
                '<script>\nconst ARCHIVE_DATA',
                '<script>// Featured Games Archive Data',
                '<script>const ARCHIVE_DATA'
            ]

            start_idx = -1
            for pattern in start_patterns:
                idx = content.find(pattern)
                if idx != -1:
                    start_idx = idx
                    break

            if start_idx != -1:
                # Find the closing </script> after renderCalendar
                search_area = content[start_idx:]
                end_marker = '</script>'

                # Find the specific closing script for this block
                # Look for renderCalendar or the end of the script
                if 'renderCalendar(' in search_area:
                    render_idx = search_area.find('renderCalendar(')
                    remaining = search_area[render_idx:]
                    script_end_idx = remaining.find('</script>')
                    if script_end_idx != -1:
                        total_end = start_idx + render_idx + script_end_idx + len('</script>')
                        old_script = content[start_idx:total_end]
                        content = content[:start_idx] + NEW_SCRIPT + content[total_end:]

    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'  UPDATED: {os.path.basename(filepath)}')
        return True
    else:
        print(f'  NO CHANGE: {os.path.basename(filepath)} - could not find calendar script')
        return False

def main():
    print('Updating featured-game-of-the-day pages to use centralized calendar JS...\n')

    # Find all featured game pages
    pattern = os.path.join(REPO, 'featured-game-of-the-day*.html')
    pages = glob.glob(pattern)

    print(f'Found {len(pages)} featured game pages\n')

    updated = 0
    skipped = 0
    failed = 0

    for page in sorted(pages):
        result = update_page(page)
        if result:
            updated += 1
        elif 'scripts/featured-games-calendar.js' in open(page, encoding='utf-8', errors='ignore').read():
            skipped += 1
        else:
            failed += 1

    print(f'\nSummary:')
    print(f'  Updated: {updated}')
    print(f'  Skipped (already done): {skipped}')
    print(f'  Failed: {failed}')

if __name__ == '__main__':
    main()
