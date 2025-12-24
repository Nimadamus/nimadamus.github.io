#!/usr/bin/env python3
"""
PRE-POST VALIDATION SCRIPT
==========================
Run this BEFORE committing ANY changes to sports pages.
This script performs comprehensive validation and BLOCKS bad content.

Usage: python scripts/pre_post_check.py [filename]
       python scripts/pre_post_check.py  (checks all modified files)
"""

import os
import re
import sys
import subprocess
from pathlib import Path

# Auto-detect repo directory
if sys.platform == 'win32':
    REPO_DIR = Path(r'C:\Users\Nima\nimadamus.github.io')
else:
    REPO_DIR = Path(__file__).parent.parent

ERRORS = []
WARNINGS = []

# ============================================================
# BANNED PLACEHOLDER PATTERNS
# ============================================================
PLACEHOLDER_PATTERNS = [
    (r'coming soon', 'Placeholder text'),
    (r'matchup analysis coming', 'Placeholder text'),
    (r'analysis coming', 'Placeholder text'),
    (r'preview coming', 'Placeholder text'),
    (r'\bTBD\b', 'TBD placeholder'),
    (r'\bTBA\b', 'TBA placeholder'),
]

# Files where N/A is acceptable (stats pages, JS calculations)
NA_ALLOWED_FILES = [
    'handicapping-hub',
    'betlegend-verified-records',
    'records.html',
]

# ============================================================
# CHECK FUNCTIONS
# ============================================================

def check_placeholders(filepath, content):
    """Check for banned placeholder content."""
    filename = os.path.basename(filepath)

    for pattern, desc in PLACEHOLDER_PATTERNS:
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            ERRORS.append(f"{filename}: Found {desc} - '{matches[0]}'")

def check_college_logos(filepath, content):
    """Check that college logos use numeric ESPN IDs."""
    filename = os.path.basename(filepath)

    # Pattern for non-numeric college logo URLs (excluding scoreboard paths)
    bad_pattern = r'teamlogos/ncaa/500/([a-zA-Z][a-zA-Z0-9-]+)\.png'

    matches = re.findall(bad_pattern, content)
    for match in matches:
        if 'scoreboard' not in match.lower():
            ERRORS.append(f"{filename}: Bad college logo '{match}' - must use numeric ID")

def check_nav_text(filepath, content):
    """Check for incorrect navigation text."""
    filename = os.path.basename(filepath)

    if re.search(r'>Overview<', content):
        ERRORS.append(f"{filename}: Found 'Overview' - should be 'Detailed Breakdown'")

def check_minimum_content(filepath, content):
    """Check that game previews have minimum content length."""
    filename = os.path.basename(filepath)

    # Only check main sports pages
    if not any(sport in filename for sport in ['nba.html', 'nhl.html', 'ncaab.html', 'ncaaf.html', 'nfl.html', 'mlb.html']):
        if not re.match(r'^(nba|nhl|ncaab|ncaaf|nfl|mlb)\.html$', filename):
            return

    # Find game preview sections
    previews = re.findall(r'<div class="preview-content">(.*?)</div>', content, re.DOTALL)

    for i, preview in enumerate(previews):
        # Strip HTML tags
        text = re.sub(r'<[^>]+>', '', preview)
        text = text.strip()

        # Check minimum length (at least 200 characters for real analysis)
        if len(text) < 200:
            WARNINGS.append(f"{filename}: Game {i+1} has short analysis ({len(text)} chars)")

def check_na_placeholders(filepath, content):
    """Check for N/A placeholders in sports pages."""
    filename = os.path.basename(filepath)

    # Skip files where N/A is acceptable
    if any(allowed in filename for allowed in NA_ALLOWED_FILES):
        return

    # Only check main sports pages
    if not any(sport in filename for sport in ['nba.html', 'nhl.html', 'ncaab.html', 'ncaaf.html', 'nfl.html', 'mlb.html']):
        return

    # Look for N/A in content areas (not JavaScript)
    content_sections = re.findall(r'<div class="preview-content">(.*?)</div>', content, re.DOTALL)
    for section in content_sections:
        if re.search(r'\bN/A\b', section):
            ERRORS.append(f"{filename}: Found N/A placeholder in game content")

def validate_file(filepath):
    """Run all validations on a single file."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        check_placeholders(filepath, content)
        check_college_logos(filepath, content)
        check_nav_text(filepath, content)
        check_minimum_content(filepath, content)
        check_na_placeholders(filepath, content)

    except Exception as e:
        ERRORS.append(f"Error reading {filepath}: {e}")

def get_modified_files():
    """Get list of modified HTML files from git."""
    try:
        result = subprocess.run(
            ['git', '-C', str(REPO_DIR), 'diff', '--name-only', 'HEAD'],
            capture_output=True, text=True
        )
        files = [f for f in result.stdout.strip().split('\n') if f.endswith('.html')]

        # Also check staged files
        result2 = subprocess.run(
            ['git', '-C', str(REPO_DIR), 'diff', '--cached', '--name-only'],
            capture_output=True, text=True
        )
        staged = [f for f in result2.stdout.strip().split('\n') if f.endswith('.html')]

        all_files = list(set(files + staged))
        return [REPO_DIR / f for f in all_files if f]

    except Exception:
        return []

# ============================================================
# MAIN
# ============================================================

def main():
    global ERRORS, WARNINGS
    ERRORS = []
    WARNINGS = []

    print("=" * 60)
    print("PRE-POST VALIDATION CHECK")
    print("=" * 60)
    print()

    # Get files to check
    if len(sys.argv) > 1:
        # Check specific file(s)
        files = [Path(f) if os.path.isabs(f) else REPO_DIR / f for f in sys.argv[1:]]
    else:
        # Check modified files
        files = get_modified_files()
        if not files:
            print("No modified HTML files found.")
            print("Checking main sports pages instead...")
            files = [
                REPO_DIR / 'nba.html',
                REPO_DIR / 'nhl.html',
                REPO_DIR / 'ncaab.html',
                REPO_DIR / 'ncaaf.html',
                REPO_DIR / 'nfl.html',
                REPO_DIR / 'mlb.html',
            ]

    print(f"Checking {len(files)} file(s)...")
    print()

    for filepath in files:
        if filepath.exists():
            validate_file(filepath)

    # Report results
    print("=" * 60)

    if ERRORS:
        print(f"[X] ERRORS FOUND: {len(ERRORS)}")
        print("-" * 60)
        for error in ERRORS:
            print(f"  [X] {error}")
        print()

    if WARNINGS:
        print(f"[!] WARNINGS: {len(WARNINGS)}")
        print("-" * 60)
        for warning in WARNINGS:
            print(f"  [!] {warning}")
        print()

    if not ERRORS and not WARNINGS:
        print("[OK] ALL CHECKS PASSED!")
        print()
        print("Safe to commit and push.")
        return 0

    if ERRORS:
        print("=" * 60)
        print("[X] VALIDATION FAILED")
        print("    Fix all errors before committing!")
        print("=" * 60)
        return 1

    print("=" * 60)
    print("[!] Warnings found - review before committing")
    print("=" * 60)
    return 0

if __name__ == '__main__':
    sys.exit(main())
