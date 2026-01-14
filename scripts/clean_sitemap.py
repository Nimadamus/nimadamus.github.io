#!/usr/bin/env python3
"""
Sitemap Cleanup Script
----------------------
Removes entries from sitemap.xml where the corresponding file doesn't exist.
This is a conservative SEO hygiene task - only removes invalid entries,
never deletes actual content files.
"""

import os
import re
from urllib.parse import urlparse

REPO_ROOT = r'C:\Users\Nima\nimadamus.github.io'
SITEMAP_PATH = os.path.join(REPO_ROOT, 'sitemap.xml')
BASE_URL = 'https://www.betlegendpicks.com/'

def get_existing_files():
    """Get all existing HTML files in the repository."""
    existing = set()
    for root, dirs, files in os.walk(REPO_ROOT):
        # Skip .git directory
        dirs[:] = [d for d in dirs if d != '.git']
        for f in files:
            if f.endswith('.html'):
                rel_path = os.path.relpath(os.path.join(root, f), REPO_ROOT)
                # Normalize path separators
                rel_path = rel_path.replace('\\', '/')
                existing.add(rel_path)
    return existing

def url_to_path(url):
    """Convert a sitemap URL to a relative file path."""
    if url.startswith(BASE_URL):
        return url[len(BASE_URL):]
    # Handle URLs without www
    alt_base = 'https://betlegendpicks.com/'
    if url.startswith(alt_base):
        return url[len(alt_base):]
    return None

def clean_sitemap():
    """Clean the sitemap by removing entries for non-existent files."""

    # Get existing files
    existing_files = get_existing_files()
    print(f"Found {len(existing_files)} existing HTML files in repository")

    # Read the current sitemap
    with open(SITEMAP_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    # Parse URL entries
    url_pattern = re.compile(r'<url>\s*<loc>(.*?)</loc>.*?</url>', re.DOTALL)
    matches = url_pattern.findall(content)

    print(f"Found {len(matches)} URLs in sitemap")

    # Track removals
    removed = []
    kept = []

    for url in matches:
        path = url_to_path(url)
        if path is None:
            # Unknown URL format, keep it
            kept.append(url)
            continue

        if path in existing_files:
            kept.append(url)
        else:
            removed.append((url, path))

    # Report removals
    print(f"\n=== URLS TO BE REMOVED ({len(removed)}) ===")
    for url, path in removed:
        print(f"  - {path}")

    print(f"\n=== KEEPING ({len(kept)}) valid URLs ===")

    # Create new sitemap content
    # We need to rebuild the XML properly
    new_urls = []
    for url in kept:
        new_urls.append(f"""    <url>
        <loc>{url}</loc>
        <changefreq>daily</changefreq>
        <priority>0.8</priority>
    </url>""")

    new_sitemap = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{chr(10).join(new_urls)}
</urlset>
"""

    # Write the cleaned sitemap
    with open(SITEMAP_PATH, 'w', encoding='utf-8') as f:
        f.write(new_sitemap)

    print(f"\nSitemap cleaned! Removed {len(removed)} invalid entries.")
    print(f"New sitemap has {len(kept)} valid URLs.")

    return removed

if __name__ == '__main__':
    removed = clean_sitemap()
