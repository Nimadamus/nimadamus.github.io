#!/usr/bin/env python3
"""
Fix Featured Game Page Canonical & OG:URL Tags
===============================================
ROOT CAUSE: The featured game link update script uses:
    re.sub(r'featured-game-of-the-day-page\d+\.html', NEW, c)
This replaces ALL occurrences including canonical and og:url tags,
causing ALL 73 pages to point their canonical to the latest page.

This script fixes:
1. Canonical tags - each page points to itself
2. OG:URL tags - each page points to itself
3. Duplicate template meta tags on older pages (pages 2-19)

Run: python scripts/fix_featured_game_canonicals.py
"""

import os
import re
import glob

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_URL = "https://www.betlegendpicks.com"

def fix_page(filepath):
    """Fix canonical and og:url for a single featured game page."""
    filename = os.path.basename(filepath)
    correct_url = f"{BASE_URL}/{filename}"

    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    original = content
    changes = []

    # Fix 1: Canonical tag - replace any featured-game canonical with self-reference
    canonical_pattern = r'(<link\s+rel="canonical"\s+href=")https?://[^"]*featured-game-of-the-day-page\d+\.html(")'
    canonical_replacement = rf'\g<1>{correct_url}\2'
    new_content, count = re.subn(canonical_pattern, canonical_replacement, content)
    if count > 0:
        changes.append(f"  Fixed canonical tag ({count} occurrence(s))")
        content = new_content

    # Fix 2: OG:URL with content= first format
    # <meta content="https://www.betlegendpicks.com/featured-game-of-the-day-page74.html" property="og:url"/>
    og_url_pattern1 = r'(<meta\s+content=")https?://[^"]*featured-game-of-the-day-page\d+\.html("\s+property="og:url")'
    og_url_replacement1 = rf'\g<1>{correct_url}\2'
    new_content, count = re.subn(og_url_pattern1, og_url_replacement1, content)
    if count > 0:
        changes.append(f"  Fixed og:url (content-first format, {count} occurrence(s))")
        content = new_content

    # Fix 3: OG:URL with property= first format
    # <meta property="og:url" content="https://betlegendpicks.com/featured-game-of-the-day-page74.html">
    og_url_pattern2 = r'(<meta\s+property="og:url"\s+content=")https?://[^"]*featured-game-of-the-day-page\d+\.html(")'
    og_url_replacement2 = rf'\g<1>{correct_url}\2'
    new_content, count = re.subn(og_url_pattern2, og_url_replacement2, content)
    if count > 0:
        changes.append(f"  Fixed og:url (property-first format, {count} occurrence(s))")
        content = new_content

    # Fix 4: Remove duplicate generic template meta tags (older pages have these)
    # These are generic tags that duplicate the page-specific ones above them
    generic_patterns = [
        r'\s*<meta\s+property="og:title"\s+content="Featured Game Of The Day \| BetLegend Picks">\s*\n?',
        r'\s*<meta\s+property="og:description"\s+content="Expert sports betting picks and analysis with verified track records\.[^"]*">\s*\n?',
        r'\s*<meta\s+name="twitter:title"\s+content="Featured Game Of The Day \| BetLegend Picks">\s*\n?',
        r'\s*<meta\s+name="twitter:description"\s+content="Expert sports betting picks and analysis with verified track records\.[^"]*">\s*\n?',
    ]

    for pattern in generic_patterns:
        new_content, count = re.subn(pattern, '\n', content)
        if count > 0:
            changes.append(f"  Removed generic template meta tag ({count})")
            content = new_content

    # Fix 5: Remove duplicate generic description meta tag
    # Keep the page-specific description (line ~5), remove the generic one (line ~22)
    # <meta name="description" content="Expert sports betting picks and analysis with verified track records...">
    generic_desc_pattern = r'\s*<meta\s+name="description"\s+content="Expert sports betting picks and analysis with verified track records\.[^"]*">\s*\n?'
    new_content, count = re.subn(generic_desc_pattern, '\n', content)
    if count > 0:
        changes.append(f"  Removed generic description meta tag ({count})")
        content = new_content

    # Clean up any double blank lines created by removals
    content = re.sub(r'\n{3,}', '\n\n', content)

    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True, changes
    return False, []


def main():
    pattern = os.path.join(REPO, 'featured-game-of-the-day-page*.html')
    pages = sorted(glob.glob(pattern))

    print(f"Found {len(pages)} featured game pages")
    print("=" * 60)

    fixed_count = 0
    for filepath in pages:
        filename = os.path.basename(filepath)
        fixed, changes = fix_page(filepath)
        if fixed:
            fixed_count += 1
            print(f"FIXED: {filename}")
            for change in changes:
                print(change)
        else:
            print(f"  OK: {filename} (no changes needed)")

    print("=" * 60)
    print(f"Total pages: {len(pages)}")
    print(f"Pages fixed: {fixed_count}")
    print(f"Pages already correct: {len(pages) - fixed_count}")

    # Verification pass
    print("\n" + "=" * 60)
    print("VERIFICATION PASS")
    print("=" * 60)
    errors = 0
    for filepath in pages:
        filename = os.path.basename(filepath)
        correct_url = f"{BASE_URL}/{filename}"
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # Check canonical
        canonical_match = re.search(r'<link\s+rel="canonical"\s+href="([^"]+)"', content)
        if canonical_match:
            if canonical_match.group(1) != correct_url:
                print(f"ERROR: {filename} canonical = {canonical_match.group(1)}")
                errors += 1
        else:
            print(f"WARNING: {filename} has no canonical tag")

        # Check og:url
        og_matches = re.findall(r'property="og:url"[^>]*content="([^"]+)"', content)
        og_matches += re.findall(r'content="([^"]+)"[^>]*property="og:url"', content)
        for og_url in og_matches:
            if 'featured-game-of-the-day-page' in og_url and og_url != correct_url:
                print(f"ERROR: {filename} og:url = {og_url}")
                errors += 1

    if errors == 0:
        print("ALL PAGES VERIFIED - Canonicals and OG:URLs are correct!")
    else:
        print(f"\n{errors} errors remain. Please investigate.")


if __name__ == '__main__':
    main()
