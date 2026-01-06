#!/usr/bin/env python3
"""
BetLegendPicks.com - Comprehensive SEO Fix Script
January 6, 2026

This script fixes all identified SEO issues:
1. Duplicate canonical tags
2. Inconsistent www vs non-www URLs
3. Sitemap URL mismatches
4. Wrong canonical references

Run this script from the repository root.
"""

import os
import re
import glob
from datetime import datetime

REPO_ROOT = r'C:\Users\Nima\nimadamus.github.io'
CANONICAL_DOMAIN = 'https://www.betlegendpicks.com'
SITEMAP_DOMAIN = 'https://www.betlegendpicks.com'  # Standardize to www

# Track all fixes
fixes_made = {
    'duplicate_canonicals_fixed': [],
    'www_standardized': [],
    'wrong_canonical_fixed': [],
    'sitemap_urls_fixed': 0,
    'errors': []
}


def fix_duplicate_canonicals(filepath, content):
    """Remove duplicate canonical tags, keeping only one correct one."""
    filename = os.path.basename(filepath)
    relative_path = os.path.relpath(filepath, REPO_ROOT).replace('\\', '/')

    # Count canonical tags
    canonical_pattern = r'<link[^>]*rel=["\']canonical["\'][^>]*/?>|<link[^>]*href=["\'][^"\']+["\'][^>]*rel=["\']canonical["\'][^>]*/?>'
    canonicals = re.findall(canonical_pattern, content, re.IGNORECASE)

    if len(canonicals) > 1:
        # Build the correct canonical URL
        correct_url = f'{CANONICAL_DOMAIN}/{relative_path}'
        correct_canonical = f'<link rel="canonical" href="{correct_url}"/>'

        # Remove ALL existing canonical tags
        content = re.sub(canonical_pattern, '', content, flags=re.IGNORECASE)

        # Insert the correct one after <head> or at start of <head> content
        if '<head>' in content:
            content = content.replace('<head>', f'<head>\n{correct_canonical}', 1)
        elif '<head ' in content:
            # Handle <head with attributes
            head_match = re.search(r'<head[^>]*>', content)
            if head_match:
                insert_pos = head_match.end()
                content = content[:insert_pos] + f'\n{correct_canonical}' + content[insert_pos:]

        fixes_made['duplicate_canonicals_fixed'].append({
            'file': relative_path,
            'count_removed': len(canonicals),
            'correct_url': correct_url
        })

        return content, True

    return content, False


def standardize_www(filepath, content):
    """Ensure all canonicals use www version."""
    filename = os.path.basename(filepath)
    relative_path = os.path.relpath(filepath, REPO_ROOT).replace('\\', '/')

    # Pattern to find non-www canonical URLs
    non_www_pattern = r'href="https://betlegendpicks\.com/'

    if re.search(non_www_pattern, content):
        # Replace non-www with www in canonical URLs
        old_content = content
        content = re.sub(
            r'href="https://betlegendpicks\.com/',
            'href="https://www.betlegendpicks.com/',
            content
        )

        if content != old_content:
            fixes_made['www_standardized'].append(relative_path)
            return content, True

    return content, False


def fix_wrong_canonical(filepath, content):
    """Fix canonicals that point to the wrong page."""
    filename = os.path.basename(filepath)
    relative_path = os.path.relpath(filepath, REPO_ROOT).replace('\\', '/')

    # Special case: bestbook.html pointing to bestonlinesportsbook.html
    if filename == 'bestbook.html':
        wrong_pattern = r'href="https://www\.betlegendpicks\.com/bestonlinesportsbook\.html"[^>]*rel="canonical"'
        if re.search(wrong_pattern, content):
            correct_url = f'{CANONICAL_DOMAIN}/bestbook.html'
            # Remove the wrong canonical
            content = re.sub(
                r'<link[^>]*href="https://www\.betlegendpicks\.com/bestonlinesportsbook\.html"[^>]*rel="canonical"[^>]*/>',
                '',
                content
            )
            fixes_made['wrong_canonical_fixed'].append({
                'file': relative_path,
                'wrong': 'bestonlinesportsbook.html',
                'correct': 'bestbook.html'
            })
            return content, True

    return content, False


def process_html_files():
    """Process all HTML files for SEO fixes."""
    html_files = glob.glob(os.path.join(REPO_ROOT, '**', '*.html'), recursive=True)

    # Exclude .git directory
    html_files = [f for f in html_files if '.git' not in f]

    files_modified = 0

    for filepath in html_files:
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                original_content = f.read()

            content = original_content
            modified = False

            # Apply fixes in order
            content, changed = fix_wrong_canonical(filepath, content)
            modified = modified or changed

            content, changed = fix_duplicate_canonicals(filepath, content)
            modified = modified or changed

            content, changed = standardize_www(filepath, content)
            modified = modified or changed

            if modified:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                files_modified += 1

        except Exception as e:
            fixes_made['errors'].append({
                'file': filepath,
                'error': str(e)
            })

    return files_modified


def fix_sitemap():
    """Fix sitemap.xml to use www URLs and update lastmod dates."""
    sitemap_path = os.path.join(REPO_ROOT, 'sitemap.xml')

    try:
        with open(sitemap_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Replace non-www with www
        original = content
        content = re.sub(
            r'<loc>https://betlegendpicks\.com/',
            '<loc>https://www.betlegendpicks.com/',
            content
        )

        # Count replacements
        fixes_made['sitemap_urls_fixed'] = len(re.findall(r'<loc>https://betlegendpicks\.com/', original))

        # Update lastmod to today
        today = datetime.now().strftime('%Y-%m-%d')
        content = re.sub(r'<lastmod>\d{4}-\d{2}-\d{2}</lastmod>', f'<lastmod>{today}</lastmod>', content)

        with open(sitemap_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return True
    except Exception as e:
        fixes_made['errors'].append({
            'file': 'sitemap.xml',
            'error': str(e)
        })
        return False


def fix_robots_txt():
    """Ensure robots.txt uses www sitemap URL."""
    robots_path = os.path.join(REPO_ROOT, 'robots.txt')

    try:
        with open(robots_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Update sitemap URL to www
        original = content
        content = re.sub(
            r'Sitemap: https://betlegendpicks\.com/',
            'Sitemap: https://www.betlegendpicks.com/',
            content
        )

        if content != original:
            with open(robots_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
    except Exception as e:
        fixes_made['errors'].append({
            'file': 'robots.txt',
            'error': str(e)
        })
        return False


def generate_report():
    """Generate a detailed report of all fixes made."""
    report = []
    report.append("=" * 70)
    report.append("BETLEGENDPICKS.COM SEO COMPREHENSIVE FIX REPORT")
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("=" * 70)
    report.append("")

    # Duplicate canonicals
    report.append(f"DUPLICATE CANONICALS FIXED: {len(fixes_made['duplicate_canonicals_fixed'])}")
    report.append("-" * 40)
    for fix in fixes_made['duplicate_canonicals_fixed']:
        report.append(f"  - {fix['file']}: Removed {fix['count_removed']} duplicates")
    report.append("")

    # WWW standardization
    report.append(f"WWW STANDARDIZED: {len(fixes_made['www_standardized'])}")
    report.append("-" * 40)
    for file in fixes_made['www_standardized'][:20]:  # Show first 20
        report.append(f"  - {file}")
    if len(fixes_made['www_standardized']) > 20:
        report.append(f"  ... and {len(fixes_made['www_standardized']) - 20} more")
    report.append("")

    # Wrong canonicals
    report.append(f"WRONG CANONICALS FIXED: {len(fixes_made['wrong_canonical_fixed'])}")
    report.append("-" * 40)
    for fix in fixes_made['wrong_canonical_fixed']:
        report.append(f"  - {fix['file']}: {fix['wrong']} -> {fix['correct']}")
    report.append("")

    # Sitemap
    report.append(f"SITEMAP URLs FIXED: {fixes_made['sitemap_urls_fixed']}")
    report.append("-" * 40)
    report.append("  All URLs updated to use www.betlegendpicks.com")
    report.append("  All lastmod dates updated to today")
    report.append("")

    # Errors
    if fixes_made['errors']:
        report.append(f"ERRORS ENCOUNTERED: {len(fixes_made['errors'])}")
        report.append("-" * 40)
        for error in fixes_made['errors']:
            report.append(f"  - {error['file']}: {error['error']}")
    else:
        report.append("ERRORS: None")

    report.append("")
    report.append("=" * 70)
    report.append("SUMMARY")
    report.append("=" * 70)
    report.append(f"Total duplicate canonicals fixed: {len(fixes_made['duplicate_canonicals_fixed'])}")
    report.append(f"Total files WWW-standardized: {len(fixes_made['www_standardized'])}")
    report.append(f"Wrong canonicals corrected: {len(fixes_made['wrong_canonical_fixed'])}")
    report.append(f"Sitemap URLs fixed: {fixes_made['sitemap_urls_fixed']}")
    report.append("")
    report.append("ROBOTS.TXT STATUS: Updated to use www sitemap URL")
    report.append("SITEMAP.XML STATUS: All URLs now use www prefix")
    report.append("")

    return '\n'.join(report)


def main():
    print("BetLegendPicks.com SEO Comprehensive Fix")
    print("=" * 50)
    print()

    print("Step 1: Processing HTML files...")
    files_modified = process_html_files()
    print(f"  -> Modified {files_modified} files")

    print("Step 2: Fixing sitemap.xml...")
    if fix_sitemap():
        print(f"  -> Fixed {fixes_made['sitemap_urls_fixed']} URLs")

    print("Step 3: Fixing robots.txt...")
    if fix_robots_txt():
        print("  -> Updated sitemap URL to www")
    else:
        print("  -> Already using www (no change needed)")

    print()
    print("Generating report...")
    report = generate_report()

    # Save report
    report_path = os.path.join(REPO_ROOT, 'seo_fix_report.txt')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(report)
    print()
    print(f"Report saved to: {report_path}")


if __name__ == '__main__':
    main()
