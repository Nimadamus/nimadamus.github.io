#!/usr/bin/env python3
"""
fix_main_page_canonicals.py - Ensures main sport page canonicals always point to themselves.

ROOT CAUSE (Feb 15, 2026):
During SLATE workflow, archive page content gets copied into main sport pages,
bringing the archive page's canonical/og:url tags with it. This causes the main
page to tell Google to deindex itself in favor of the archive page.

This script fixes any main sport page whose canonical or og:url points to an
archive page instead of itself.

Usage:
    python scripts/fix_main_page_canonicals.py          # Fix all main pages
    python scripts/fix_main_page_canonicals.py nba.html  # Fix specific page
"""

import os
import re
import sys

REPO_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOMAIN = "https://www.betlegendpicks.com"

# Main sport pages that must ALWAYS canonicalize to themselves
MAIN_PAGES = [
    "nba.html",
    "nhl.html",
    "nfl.html",
    "ncaab.html",
    "ncaaf.html",
    "mlb.html",
    "soccer.html",
]


def fix_page(filename):
    """Fix canonical and og:url for a main sport page to point to itself."""
    filepath = os.path.join(REPO_PATH, filename)
    if not os.path.exists(filepath):
        return False, f"  [SKIP] {filename} does not exist"

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    correct_url = f"{DOMAIN}/{filename}"
    changes = []

    # Fix canonical tag
    canonical_pattern = r'<link\s+href="[^"]*"\s+rel="canonical"\s*/?\s*>'
    canonical_alt_pattern = r'<link\s+rel="canonical"\s+href="[^"]*"\s*/?\s*>'

    for pattern in [canonical_pattern, canonical_alt_pattern]:
        match = re.search(pattern, content)
        if match:
            current = match.group(0)
            if correct_url not in current:
                if 'href="' in current and 'rel="canonical"' in current:
                    # Extract current href
                    href_match = re.search(r'href="([^"]*)"', current)
                    if href_match:
                        old_url = href_match.group(1)
                        new_tag = current.replace(old_url, correct_url)
                        content = content.replace(current, new_tag)
                        changes.append(f"  canonical: {old_url} -> {correct_url}")
            break

    # Fix og:url tag
    ogurl_pattern = r'<meta\s+content="([^"]*)"\s+property="og:url"\s*/?\s*>'
    ogurl_alt_pattern = r'<meta\s+property="og:url"\s+content="([^"]*)"\s*/?\s*>'

    for pattern in [ogurl_pattern, ogurl_alt_pattern]:
        match = re.search(pattern, content)
        if match:
            old_url = match.group(1)
            if old_url != correct_url:
                content = content.replace(
                    match.group(0),
                    match.group(0).replace(old_url, correct_url)
                )
                changes.append(f"  og:url: {old_url} -> {correct_url}")
            break

    if changes:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return True, f"  [FIXED] {filename}:\n" + "\n".join(changes)
    else:
        return False, f"  [OK] {filename} - canonicals already correct"


def main():
    print("=" * 60)
    print("  MAIN PAGE CANONICAL FIXER")
    print("=" * 60)

    # Determine which pages to fix
    if len(sys.argv) > 1:
        pages = [p for p in sys.argv[1:] if p in MAIN_PAGES]
        if not pages:
            pages = sys.argv[1:]  # Allow any page to be specified
    else:
        pages = MAIN_PAGES

    fixed_count = 0
    for page in pages:
        was_fixed, message = fix_page(page)
        print(message)
        if was_fixed:
            fixed_count += 1

    print()
    if fixed_count > 0:
        print(f"  Fixed {fixed_count} page(s)")
    else:
        print("  All main pages have correct canonicals")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
