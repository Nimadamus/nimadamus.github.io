#!/usr/bin/env python3
"""
BetLegendPicks.com - Comprehensive SEO Fix Script v2
January 6, 2026

Fixes:
1. Remove ALL duplicate canonical tags, keeping only ONE correct one
2. Standardize all to: <link rel="canonical" href="https://www.betlegendpicks.com/..."/>
3. Fix wrong canonical references (like bestbook.html -> bestonlinesportsbook.html)
"""

import os
import re
import glob
from datetime import datetime

REPO_ROOT = r'C:\Users\Nima\nimadamus.github.io'
CANONICAL_DOMAIN = 'https://www.betlegendpicks.com'

fixes_made = {
    'files_fixed': [],
    'sitemap_fixed': False,
    'robots_fixed': False,
    'errors': []
}


def get_correct_canonical_url(filepath):
    """Generate the correct canonical URL for a file."""
    relative_path = os.path.relpath(filepath, REPO_ROOT).replace('\\', '/')
    return f'{CANONICAL_DOMAIN}/{relative_path}'


def fix_html_file(filepath):
    """Fix all canonical issues in an HTML file."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        original_content = content

        # Pattern 1: <link rel="canonical" href="...">
        pattern1 = r'<link\s+rel=["\']canonical["\']\s+href=["\'][^"\']*["\'][^>]*/?>'

        # Pattern 2: <link href="..." rel="canonical">  or  <link href="..." rel="canonical"/>
        pattern2 = r'<link\s+href=["\'][^"\']*["\']\s+rel=["\']canonical["\'][^>]*/?>'

        # Find all canonical tags
        matches1 = re.findall(pattern1, content, re.IGNORECASE)
        matches2 = re.findall(pattern2, content, re.IGNORECASE)

        total_canonicals = len(matches1) + len(matches2)

        if total_canonicals == 0:
            return False  # No canonicals found

        # Get the correct URL for this file
        correct_url = get_correct_canonical_url(filepath)
        correct_canonical = f'<link rel="canonical" href="{correct_url}"/>'

        # Remove ALL existing canonical tags
        content = re.sub(pattern1, '', content, flags=re.IGNORECASE)
        content = re.sub(pattern2, '', content, flags=re.IGNORECASE)

        # Clean up any leftover empty lines where canonicals were
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)

        # Insert the correct canonical tag after <head> or first meta charset
        if '<meta charset' in content.lower():
            # Insert after charset meta tag
            content = re.sub(
                r'(<meta\s+charset=["\'][^"\']*["\'][^>]*/?>)',
                r'\1\n' + correct_canonical,
                content,
                count=1,
                flags=re.IGNORECASE
            )
        elif '<head>' in content:
            content = content.replace('<head>', f'<head>\n{correct_canonical}', 1)
        elif re.search(r'<head\s+', content):
            content = re.sub(r'(<head[^>]*>)', r'\1\n' + correct_canonical, content, count=1)

        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

            relative_path = os.path.relpath(filepath, REPO_ROOT)
            fixes_made['files_fixed'].append({
                'file': relative_path,
                'canonicals_removed': total_canonicals,
                'correct_url': correct_url
            })
            return True

    except Exception as e:
        fixes_made['errors'].append({
            'file': filepath,
            'error': str(e)
        })

    return False


def fix_sitemap():
    """Fix sitemap.xml URLs."""
    sitemap_path = os.path.join(REPO_ROOT, 'sitemap.xml')

    try:
        with open(sitemap_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original = content

        # Replace non-www with www
        content = content.replace('https://betlegendpicks.com/', 'https://www.betlegendpicks.com/')

        # Update lastmod to today
        today = datetime.now().strftime('%Y-%m-%d')
        content = re.sub(r'<lastmod>\d{4}-\d{2}-\d{2}</lastmod>', f'<lastmod>{today}</lastmod>', content)

        if content != original:
            with open(sitemap_path, 'w', encoding='utf-8') as f:
                f.write(content)
            fixes_made['sitemap_fixed'] = True
            return True

    except Exception as e:
        fixes_made['errors'].append({'file': 'sitemap.xml', 'error': str(e)})

    return False


def fix_robots():
    """Fix robots.txt sitemap URL."""
    robots_path = os.path.join(REPO_ROOT, 'robots.txt')

    try:
        with open(robots_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original = content
        content = content.replace('https://betlegendpicks.com/sitemap.xml', 'https://www.betlegendpicks.com/sitemap.xml')

        if content != original:
            with open(robots_path, 'w', encoding='utf-8') as f:
                f.write(content)
            fixes_made['robots_fixed'] = True
            return True

    except Exception as e:
        fixes_made['errors'].append({'file': 'robots.txt', 'error': str(e)})

    return False


def main():
    print("=" * 60)
    print("BETLEGENDPICKS.COM SEO FIX v2")
    print("=" * 60)
    print()

    # Find all HTML files
    html_files = glob.glob(os.path.join(REPO_ROOT, '**', '*.html'), recursive=True)
    html_files = [f for f in html_files if '.git' not in f]

    print(f"Found {len(html_files)} HTML files to process...")
    print()

    # Process HTML files
    files_modified = 0
    for filepath in html_files:
        if fix_html_file(filepath):
            files_modified += 1

    print(f"HTML files modified: {files_modified}")

    # Fix sitemap
    print("\nFixing sitemap.xml...")
    fix_sitemap()
    print(f"  Sitemap fixed: {fixes_made['sitemap_fixed']}")

    # Fix robots.txt
    print("\nFixing robots.txt...")
    fix_robots()
    print(f"  Robots.txt fixed: {fixes_made['robots_fixed']}")

    # Generate report
    print("\n" + "=" * 60)
    print("FIX REPORT")
    print("=" * 60)

    print(f"\nTotal HTML files fixed: {len(fixes_made['files_fixed'])}")
    print("\nFiles with duplicate/wrong canonicals fixed:")
    for fix in fixes_made['files_fixed'][:30]:  # Show first 30
        print(f"  - {fix['file']}: removed {fix['canonicals_removed']} old tags")

    if len(fixes_made['files_fixed']) > 30:
        print(f"  ... and {len(fixes_made['files_fixed']) - 30} more")

    if fixes_made['errors']:
        print(f"\nErrors encountered: {len(fixes_made['errors'])}")
        for err in fixes_made['errors']:
            print(f"  - {err['file']}: {err['error']}")

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"HTML files with canonicals fixed: {len(fixes_made['files_fixed'])}")
    print(f"Sitemap.xml: {'FIXED' if fixes_made['sitemap_fixed'] else 'Already correct'}")
    print(f"Robots.txt: {'FIXED' if fixes_made['robots_fixed'] else 'Already correct'}")
    print(f"Errors: {len(fixes_made['errors'])}")
    print()
    print("All canonicals now use: https://www.betlegendpicks.com/")
    print("All canonicals now use format: <link rel=\"canonical\" href=\"...\"/>")


if __name__ == '__main__':
    main()
