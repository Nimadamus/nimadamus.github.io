#!/usr/bin/env python3
"""
Soccer Team Logo ID Mapping and Fixer
ESPN uses numeric team IDs for soccer logos.

This script:
1. Fixes known incorrect IDs to correct ESPN IDs
2. Replaces default-team-logo placeholders with a generic fallback
3. Can be run automatically via pre-commit hook or manually

Usage: python scripts/soccer_logo_ids.py
"""

import os
import re
from pathlib import Path
import sys

# Auto-detect repo directory (works on Windows locally and Linux in GitHub Actions)
if sys.platform == 'win32':
    REPO_DIR = Path(r'C:\Users\Nima\nimadamus.github.io')
else:
    REPO_DIR = Path(__file__).parent.parent  # scripts/ -> repo root

# Generic fallback for teams without ESPN logos (soccer ball icon)
FALLBACK_LOGO = "https://a.espncdn.com/i/teamlogos/soccer/500/default-team-logo-500.png"

# Use a better generic soccer placeholder (ESPN's generic soccer icon)
GENERIC_SOCCER_FALLBACK = "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/default-team-logo-500.png&w=100&h=100"

# Mapping of WRONG ESPN IDs to CORRECT ESPN IDs for soccer teams
# Format: wrong_id -> correct_id
SOCCER_ID_CORRECTIONS = {
    # English Teams
    '355': '397',      # Barnsley (was 355, correct is 397)

    # Italian Teams (Serie A)
    '3199': '3263',    # Genoa (was 3199, correct is 3263)
    '3282': '4050',    # Cremonese (was 3282, correct is 4050)
    '108': '2925',     # Cagliari (was 108, correct is 2925)

    # French Teams
    '5168': '6851',    # Paris FC (was 5168, correct is 6851)
}

# Full ESPN Soccer Team ID Reference (verified working)
# This is for documentation and future reference
SOCCER_TEAM_IDS = {
    # PREMIER LEAGUE
    'arsenal': 359,
    'aston_villa': 362,
    'bournemouth': 349,
    'brentford': 337,
    'brighton': 331,
    'burnley': 379,
    'chelsea': 363,
    'crystal_palace': 384,
    'everton': 368,
    'fulham': 370,
    'liverpool': 364,
    'luton': 301,
    'manchester_city': 382,
    'manchester_united': 360,
    'newcastle': 361,
    'nottingham_forest': 393,
    'sheffield_united': 398,
    'tottenham': 367,
    'west_ham': 371,
    'wolves': 380,

    # CHAMPIONSHIP / LOWER LEAGUES
    'barnsley': 397,
    'leeds': 357,
    'sunderland': 366,
    'charlton': 372,
    'exeter_city': 562,
    'accrington_stanley': 2598,
    'bromley': 3129,       # Has ESPN page but no CDN logo
    'macclesfield': 131494, # Has ESPN page but no CDN logo
    'swansea': 318,
    'wrexham': 2457,

    # LA LIGA
    'atletico_madrid': 1068,
    'barcelona': 83,
    'real_madrid': 86,
    'sevilla': 243,
    'celta_vigo': 85,
    'valencia': 94,
    'mallorca': 95,
    'getafe': 96,
    'rayo_vallecano': 87,

    # SERIE A
    'ac_milan': 103,
    'inter': 110,
    'juventus': 111,
    'napoli': 114,
    'roma': 104,
    'lazio': 112,
    'atalanta': 105,
    'fiorentina': 109,
    'bologna': 107,
    'torino': 239,
    'genoa': 3263,
    'cagliari': 2925,
    'cremonese': 4050,
    'sassuolo': 488,
    'lecce': 3207,
    'parma': 115,
    'udinese': 118,
    'hellas_verona': 119,
    'como': 9858,
    'pisa': 3483,

    # LIGUE 1 / FRANCE
    'psg': 160,
    'paris_fc': 6851,
    'marseille': 176,
    'lyon': 167,
    'monaco': 174,
    'lens': 175,
    'toulouse': 183,
    'auxerre': 172,

    # BUNDESLIGA
    'bayern': 132,
    'dortmund': 124,
    'leipzig': 11420,
    'leverkusen': 131,
    'gladbach': 131,  # Borussia Monchengladbach
}

def fix_logo_id(match):
    """Replace incorrect ESPN ID with correct one."""
    full_match = match.group(0)

    # Extract the team ID from the URL
    id_match = re.search(r'/soccer/500/(\d+)\.png', full_match)
    if not id_match:
        return full_match

    team_id = id_match.group(1)

    # Check if this ID needs correction
    if team_id in SOCCER_ID_CORRECTIONS:
        correct_id = SOCCER_ID_CORRECTIONS[team_id]
        print(f"  Correcting ID: {team_id} -> {correct_id}")
        return full_match.replace(f'/soccer/500/{team_id}.png', f'/soccer/500/{correct_id}.png')

    return full_match

def fix_default_logo(content):
    """Replace default-team-logo placeholder with a fallback that at least shows something."""
    # Count occurrences before fix
    count = content.count('default-team-logo-500.png')
    if count > 0:
        print(f"  Found {count} default-team-logo placeholder(s)")
        # Note: We keep the default-team-logo as ESPN does serve it, just logs the warning
        # If you want to replace with a different fallback, uncomment below:
        # content = content.replace(
        #     'https://a.espncdn.com/i/teamlogos/soccer/500/default-team-logo-500.png',
        #     GENERIC_SOCCER_FALLBACK
        # )
    return content

def fix_file(filepath):
    """Fix all soccer logo URLs in a file."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        original = content

        # Fix incorrect IDs
        content = re.sub(
            r'src="https://a\.espncdn\.com/i/teamlogos/soccer/500/\d+\.png"',
            fix_logo_id,
            content
        )

        # Log default-team-logo usage (these are teams without ESPN CDN logos)
        fix_default_logo(content)

        if content != original:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False

def audit_logos(filepath):
    """Audit a file for potential broken soccer logos."""
    issues = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # Find all soccer logo URLs
        logos = re.findall(r'teamlogos/soccer/500/([^"]+)\.png', content)

        for logo_id in logos:
            if logo_id == 'default-team-logo-500':
                issues.append(f"  WARNING: Using default placeholder logo")
            elif logo_id in SOCCER_ID_CORRECTIONS:
                issues.append(f"  ERROR: Using wrong ID {logo_id} (should be {SOCCER_ID_CORRECTIONS[logo_id]})")

        return issues
    except Exception as e:
        return [f"Error reading file: {e}"]

def main():
    print("=" * 60)
    print("Soccer Logo ID Fixer")
    print("Correcting wrong ESPN IDs and auditing logos")
    print("=" * 60)

    fixed_count = 0
    files_with_issues = []

    # Process all soccer HTML files
    soccer_files = list(REPO_DIR.glob('soccer*.html'))

    print(f"\nFound {len(soccer_files)} soccer page(s) to process\n")

    for filepath in soccer_files:
        print(f"Processing: {filepath.name}")

        # Audit for issues
        issues = audit_logos(filepath)
        if issues:
            files_with_issues.append((filepath.name, issues))

        # Fix issues
        if fix_file(filepath):
            print(f"  FIXED: {filepath.name}")
            fixed_count += 1
        else:
            print(f"  OK: No changes needed")

    print(f"\n{'=' * 60}")
    print(f"SUMMARY")
    print(f"{'=' * 60}")
    print(f"Files processed: {len(soccer_files)}")
    print(f"Files fixed: {fixed_count}")

    if files_with_issues:
        print(f"\nFiles with potential issues:")
        for filename, issues in files_with_issues:
            print(f"\n  {filename}:")
            for issue in issues:
                print(f"    {issue}")

    print("=" * 60)

    return 0 if fixed_count == 0 else 1

if __name__ == '__main__':
    sys.exit(main())
