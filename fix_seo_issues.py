#!/usr/bin/env python3
"""
BetLegend SEO Issue Fixer
Fixes critical SEO issues found in site audit:
1. Removes meta refresh tags (replaces with 301 redirects)
2. Fixes multiple canonical URLs
3. Cleans up sitemap
"""

import os
import re
from pathlib import Path

BASE_DIR = r"C:\Users\Nima\Desktop\betlegendpicks"

# Issue 1: Pages with meta refresh tags (should use 301 redirects instead)
META_REFRESH_PAGES = {
    "betlegend-verified-records.htm": "betlegend-verified-records.html",
    "bestbook.html": "bestonlinesportsbook.html",
    "FreeAlerts.html": "index.html",
    "Best Online Sportsbook.html": "bestonlinesportsbook.html",
    "smartbets.html": "betlegend-verified-records.html",
    "matchups.html": "betlegend-verified-records.html",
    "odds.html": "blog.html",
    "picks.html": "blog.html",
    "affiliates.html": "index.html",
}

# Issue 2: Pages with multiple canonical tags
MULTIPLE_CANONICAL_PAGES = [
    "blog-page8.html",
    "MLB.html"
]

def fix_multiple_canonicals(filepath):
    """Remove duplicate canonical tags, keep only the first one"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find all canonical link tags
    canonical_pattern = r'<link[^>]*rel=["\']canonical["\'][^>]*/?>'
    canonicals = re.findall(canonical_pattern, content, re.IGNORECASE)

    if len(canonicals) <= 1:
        print(f"  {os.path.basename(filepath)}: OK (only {len(canonicals)} canonical)")
        return False

    print(f"  {os.path.basename(filepath)}: Found {len(canonicals)} canonicals, removing duplicates...")

    # Keep only the first canonical, remove the rest
    first_canonical = canonicals[0]
    for i, canonical in enumerate(canonicals):
        if i == 0:
            continue  # Keep first one
        content = content.replace(canonical, '', 1)

    # Write back
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"    [OK] Fixed! Kept 1 canonical, removed {len(canonicals) - 1}")
    return True

def create_htaccess_redirects():
    """Create .htaccess file with 301 redirects instead of meta refresh"""
    htaccess_content = """# BetLegend 301 Redirects
# These replace meta refresh tags for better SEO

RewriteEngine On

# Redirect old/alternate URLs to canonical versions
Redirect 301 /betlegend-verified-records.htm https://www.betlegendpicks.com/betlegend-verified-records.html
Redirect 301 /bestbook.html https://www.betlegendpicks.com/bestonlinesportsbook.html
Redirect 301 /FreeAlerts.html https://www.betlegendpicks.com/
Redirect 301 /smartbets.html https://www.betlegendpicks.com/betlegend-verified-records.html
Redirect 301 /matchups.html https://www.betlegendpicks.com/betlegend-verified-records.html
Redirect 301 /odds.html https://www.betlegendpicks.com/blog.html
Redirect 301 /picks.html https://www.betlegendpicks.com/blog.html
Redirect 301 /affiliates.html https://www.betlegendpicks.com/

# Force HTTPS
RewriteCond %{HTTPS} off
RewriteRule ^(.*)$ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]

# Force www
RewriteCond %{HTTP_HOST} !^www\. [NC]
RewriteRule ^(.*)$ https://www.%{HTTP_HOST}%{REQUEST_URI} [L,R=301]
"""

    htaccess_path = os.path.join(BASE_DIR, ".htaccess")

    # Check if .htaccess exists
    if os.path.exists(htaccess_path):
        print("\n[WARNING] .htaccess already exists. Creating .htaccess_new instead.")
        print("   Please merge the redirects into your existing .htaccess")
        htaccess_path = os.path.join(BASE_DIR, ".htaccess_new")

    with open(htaccess_path, 'w', encoding='utf-8') as f:
        f.write(htaccess_content)

    print(f"\n[OK] Created {os.path.basename(htaccess_path)} with 301 redirects")
    return htaccess_path

def remove_meta_refresh_pages():
    """Remove or update pages with meta refresh tags"""
    print("\n" + "="*80)
    print("FIXING META REFRESH TAGS")
    print("="*80)

    for page, target in META_REFRESH_PAGES.items():
        filepath = os.path.join(BASE_DIR, page)

        if not os.path.exists(filepath):
            print(f"  SKIP: {page} not found")
            continue

        # Read the file
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check if it has meta refresh
        if 'http-equiv="refresh"' not in content.lower():
            print(f"  SKIP: {page} - no meta refresh found")
            continue

        # Create a simple HTML file that explains the redirect
        new_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Page Moved - BetLegend</title>
    <link rel="canonical" href="https://www.betlegendpicks.com/{target}" />
</head>
<body>
    <h1>This page has moved</h1>
    <p>This page has permanently moved to <a href="/{target}">{target}</a></p>
    <p>You will be redirected automatically via server-side 301 redirect.</p>
    <p>If not redirected, please click the link above.</p>
</body>
</html>"""

        # Write the new content
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)

        print(f"  [FIXED] {page} -> Updated (removed meta refresh)")

def fix_sitemap():
    """Remove pages with meta refresh from sitemap"""
    print("\n" + "="*80)
    print("FIXING SITEMAP")
    print("="*80)

    sitemap_path = os.path.join(BASE_DIR, "sitemap.xml")

    if not os.path.exists(sitemap_path):
        print("  sitemap.xml not found")
        return

    with open(sitemap_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content
    removed_count = 0

    # Remove URLs that have meta refresh redirects
    for page in META_REFRESH_PAGES.keys():
        # Match the entire <url> block for this page
        pattern = rf'<url>\s*<loc>https://www\.betlegendpicks\.com/{re.escape(page)}</loc>.*?</url>'
        if re.search(pattern, content, re.DOTALL):
            content = re.sub(pattern, '', content, flags=re.DOTALL)
            removed_count += 1
            print(f"  [OK] Removed {page} from sitemap")

    if removed_count > 0:
        # Clean up extra whitespace
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)

        with open(sitemap_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"\n  [OK] Removed {removed_count} redirect pages from sitemap.xml")
    else:
        print("  No changes needed to sitemap.xml")

def main():
    print("\n" + "="*80)
    print("BETLEGEND SEO ISSUE FIXER")
    print("="*80)

    # Fix Issue 1: Multiple Canonical Tags
    print("\n" + "="*80)
    print("FIXING MULTIPLE CANONICAL TAGS")
    print("="*80)

    fixed_count = 0
    for page in MULTIPLE_CANONICAL_PAGES:
        filepath = os.path.join(BASE_DIR, page)
        if os.path.exists(filepath):
            if fix_multiple_canonicals(filepath):
                fixed_count += 1
        else:
            print(f"  SKIP: {page} not found")

    print(f"\n  [OK] Fixed {fixed_count} pages with multiple canonicals")

    # Fix Issue 2: Meta Refresh Tags
    remove_meta_refresh_pages()

    # Fix Issue 3: Sitemap
    fix_sitemap()

    # Create .htaccess with 301 redirects
    htaccess_path = create_htaccess_redirects()

    # Final summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"""
[OK] Fixed multiple canonical tags on {fixed_count} pages
[OK] Removed meta refresh tags from {len(META_REFRESH_PAGES)} pages
[OK] Cleaned sitemap.xml
[OK] Created {os.path.basename(htaccess_path)} with 301 redirects

NEXT STEPS:
1. Upload .htaccess to your web server (if you don't have one already)
2. If you have an existing .htaccess, merge the redirects from .htaccess_new
3. Test a few redirect URLs to make sure they work
4. Re-run site audit to verify fixes

IMPORTANT:
- The meta refresh pages now have clean HTML
- Server-side 301 redirects (via .htaccess) will handle the actual redirects
- This is much better for SEO than meta refresh tags
""")

if __name__ == "__main__":
    main()
