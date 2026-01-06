#!/usr/bin/env python3
"""
SEO Validation Script for BetLegendPicks.com
Run this before committing to catch SEO issues early.

Usage: python scripts/validate_seo.py [--fix]
"""

import os
import re
import sys
import argparse

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CANONICAL_DOMAIN = 'https://www.betlegendpicks.com'

errors = []
warnings = []


def check_duplicate_canonicals(filepath, content):
    """Check for multiple canonical tags."""
    pattern1 = r'<link\s+rel=["\']canonical["\']\s+href=["\'][^"\']*["\'][^>]*/?\s*>'
    pattern2 = r'<link\s+href=["\'][^"\']*["\']\s+rel=["\']canonical["\']\s*[^>]*/?\s*>'

    m1 = re.findall(pattern1, content, re.IGNORECASE)
    m2 = re.findall(pattern2, content, re.IGNORECASE)

    total = len(m1) + len(m2)
    if total > 1:
        errors.append(f'{filepath}: Has {total} canonical tags (should be 1)')
        return False
    elif total == 0:
        warnings.append(f'{filepath}: Missing canonical tag')
        return True
    return True


def check_canonical_format(filepath, content):
    """Check canonical uses www.betlegendpicks.com."""
    rel_path = os.path.relpath(filepath, REPO_ROOT).replace('\\', '/')
    expected_url = f'{CANONICAL_DOMAIN}/{rel_path}'

    # Find canonical URL
    match = re.search(r'href=["\']([^"\']*betlegendpicks[^"\']*)["\'][^>]*rel=["\']canonical', content, re.IGNORECASE)
    if not match:
        match = re.search(r'rel=["\']canonical["\'][^>]*href=["\']([^"\']*)["\']', content, re.IGNORECASE)

    if match:
        actual_url = match.group(1)

        # Check for non-www
        if 'https://betlegendpicks.com' in actual_url and 'www' not in actual_url:
            errors.append(f'{filepath}: Canonical uses non-www URL: {actual_url}')
            return False

        # Check for wrong file reference
        if rel_path not in actual_url:
            errors.append(f'{filepath}: Canonical points to wrong file: {actual_url}')
            return False

    return True


def check_file(filepath):
    """Run all checks on a file."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        check_duplicate_canonicals(filepath, content)
        check_canonical_format(filepath, content)

    except Exception as e:
        errors.append(f'{filepath}: Error reading file: {e}')


def main():
    parser = argparse.ArgumentParser(description='Validate SEO for BetLegendPicks.com')
    parser.add_argument('--fix', action='store_true', help='Attempt to fix issues')
    parser.add_argument('files', nargs='*', help='Specific files to check (default: all)')
    args = parser.parse_args()

    # Find HTML files to check
    if args.files:
        html_files = [f for f in args.files if f.endswith('.html')]
    else:
        html_files = []
        for root, dirs, files in os.walk(REPO_ROOT):
            dirs[:] = [d for d in dirs if d != '.git']
            for f in files:
                if f.endswith('.html'):
                    html_files.append(os.path.join(root, f))

    print(f'Checking {len(html_files)} HTML files...')

    for filepath in html_files:
        check_file(filepath)

    # Report results
    print()
    if errors:
        print(f'ERRORS ({len(errors)}):')
        for err in errors:
            print(f'  [ERROR] {err}')
        print()

    if warnings:
        print(f'WARNINGS ({len(warnings)}):')
        for warn in warnings[:10]:  # Limit warnings shown
            print(f'  [WARN] {warn}')
        if len(warnings) > 10:
            print(f'  ... and {len(warnings) - 10} more')
        print()

    if errors:
        print('SEO VALIDATION FAILED')
        print('Run: python scripts/seo_comprehensive_fix.py to fix issues')
        return 1
    else:
        print('SEO VALIDATION PASSED')
        return 0


if __name__ == '__main__':
    sys.exit(main())
