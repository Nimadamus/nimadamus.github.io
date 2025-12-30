#!/usr/bin/env python3
"""
Fix NCAAF pagination across all pages.

Structure:
- ncaaf.html = NEWEST (Page 32 of 32)
- ncaaf-page2.html = Page 31 of 32
- ncaaf-page3.html = Page 30 of 32
- ...
- ncaaf-page32.html = OLDEST (Page 1 of 32)
"""

import os
import re
from pathlib import Path

REPO = Path(r'C:\Users\Nima\nimadamus.github.io')

def get_ncaaf_pages():
    """Get all NCAAF pages in order."""
    pages = []

    # Main page is newest
    if (REPO / 'ncaaf.html').exists():
        pages.append('ncaaf.html')

    # Find all numbered pages
    numbered = []
    for f in REPO.glob('ncaaf-page*.html'):
        match = re.search(r'ncaaf-page(\d+)\.html', f.name)
        if match:
            numbered.append((int(match.group(1)), f.name))

    # Sort by page number (page2 comes after main, page32 is oldest)
    numbered.sort(key=lambda x: x[0])
    pages.extend([p[1] for p in numbered])

    return pages

def fix_pagination(pages):
    """Fix pagination on all pages."""
    total = len(pages)
    print(f"Found {total} NCAAF pages")

    for i, page in enumerate(pages):
        filepath = REPO / page
        if not filepath.exists():
            print(f"  SKIP: {page} not found")
            continue

        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        original = content

        # Calculate page number (newest = total, oldest = 1)
        page_num = total - i

        # Determine prev/next links
        prev_page = pages[i - 1] if i > 0 else None
        next_page = pages[i + 1] if i < total - 1 else None

        # Build new pagination HTML
        if prev_page and next_page:
            # Middle page
            new_pagination = f'<div class="archive-link"><a href="{prev_page}">← Newer</a> <span>Page {page_num} of {total}</span> <a href="{next_page}">Older →</a></div>'
        elif prev_page:
            # Last page (oldest)
            new_pagination = f'<div class="archive-link"><a href="{prev_page}">← Newer</a> <span>Page {page_num} of {total}</span></div>'
        elif next_page:
            # First page (newest)
            new_pagination = f'<div class="archive-link"><span>Page {page_num} of {total}</span> <a href="{next_page}">Older →</a></div>'
        else:
            # Only page
            new_pagination = f'<div class="archive-link"><span>Page {page_num} of {total}</span></div>'

        # Replace existing pagination
        pattern = r'<div class="archive-link">.*?</div>'
        if re.search(pattern, content):
            content = re.sub(pattern, new_pagination, content)
        else:
            # Add pagination before </main> if not present
            content = content.replace('</main>', f'{new_pagination}\n</main>')

        if content != original:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  FIXED: {page} -> Page {page_num} of {total}")
        else:
            print(f"  OK: {page}")

def main():
    pages = get_ncaaf_pages()
    print(f"\nNCAAF Pages (newest to oldest):")
    for i, p in enumerate(pages):
        print(f"  {i+1}. {p}")

    print(f"\nFixing pagination...")
    fix_pagination(pages)
    print("\nDone!")

if __name__ == '__main__':
    main()
