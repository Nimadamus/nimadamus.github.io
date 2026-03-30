#!/usr/bin/env python3
"""
Validate No Duplicate Picks - March 30, 2026
=============================================
Checks that no pick exists in BOTH a standalone page AND the blog archive.
Picks are STANDALONE PAGES ONLY. The archive is frozen.

Usage:
    python scripts/validate_no_duplicate_picks.py

Exit codes:
    0 = No duplicates found
    1 = Duplicates detected (FIX REQUIRED)
"""

import os
import re
import sys

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARCHIVE_PAGE = os.path.join(REPO_DIR, "nba-college-basketball-picks-predictions-analysis-february-2026.html")
PICKS_DATA = os.path.join(REPO_DIR, "homepage-picks-data.js")


def get_archive_post_ids(filepath):
    """Extract all blog-post IDs from the archive page."""
    if not os.path.exists(filepath):
        return []
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    return re.findall(r'id="(post-\d{8}-[^"]+)"', content)


def get_standalone_pick_urls(filepath):
    """Extract all standalone pick page URLs from homepage-picks-data.js."""
    if not os.path.exists(filepath):
        return []
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    urls = re.findall(r'url:\s*"([^"]+)"', content)
    # Only return standalone pages (not archive anchors)
    return [u for u in urls if "#" not in u]


def extract_date_from_post_id(post_id):
    """Extract YYYYMMDD from post ID like post-20260329-brewers-ml."""
    match = re.match(r'post-(\d{8})-', post_id)
    return match.group(1) if match else None


def extract_date_from_picks_data(filepath):
    """Extract date -> url mapping from homepage-picks-data.js."""
    if not os.path.exists(filepath):
        return {}
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    date_url = {}
    # Find all entries with date and url
    entries = re.findall(r'date:\s*"([^"]+)"[^}]*url:\s*"([^"]+)"', content, re.DOTALL)
    for date_str, url in entries:
        date_url[date_str] = url
    return date_url


def main():
    print("=" * 60)
    print("  DUPLICATE PICKS VALIDATOR")
    print("=" * 60)
    print()

    archive_ids = get_archive_post_ids(ARCHIVE_PAGE)
    standalone_urls = get_standalone_pick_urls(PICKS_DATA)

    if not archive_ids:
        print("  No posts found in archive page.")
        print("  [OK] No duplicates possible.")
        return 0

    if not standalone_urls:
        print("  No standalone pick pages found.")
        print("  [OK] No duplicates possible.")
        return 0

    print(f"  Archive posts found: {len(archive_ids)}")
    print(f"  Standalone pages found: {len(standalone_urls)}")
    print()

    # Check if any archive post dates match standalone page dates
    # This is a heuristic - check by date overlap
    archive_dates = {}
    for pid in archive_ids:
        date = extract_date_from_post_id(pid)
        if date:
            archive_dates[date] = pid

    date_url_map = extract_date_from_picks_data(PICKS_DATA)

    duplicates = []

    for date_str, url in date_url_map.items():
        if "#" in url:
            continue  # This is an archive reference, not a standalone page

        # Convert "March 29, 2026" to "20260329"
        try:
            from datetime import datetime
            dt = datetime.strptime(date_str, "%B %d, %Y")
            date_key = dt.strftime("%Y%m%d")
        except (ValueError, ImportError):
            continue

        if date_key in archive_dates:
            duplicates.append({
                "date": date_str,
                "archive_id": archive_dates[date_key],
                "standalone_url": url
            })

    if duplicates:
        print("  [ERROR] DUPLICATE PICKS DETECTED!")
        print()
        for dup in duplicates:
            print(f"  DATE: {dup['date']}")
            print(f"    Archive:    {dup['archive_id']}")
            print(f"    Standalone: {dup['standalone_url']}")
            print()
        print("  FIX: Remove the duplicate entries from the archive page.")
        print(f"  File: {ARCHIVE_PAGE}")
        print()
        print("  Picks should ONLY exist as standalone pages.")
        print("  The archive is FROZEN for historical picks only.")
        print("=" * 60)
        return 1
    else:
        print("  [OK] No duplicate picks found.")
        print("  All standalone picks are properly separated from the archive.")
        print("=" * 60)
        return 0


if __name__ == "__main__":
    sys.exit(main())
