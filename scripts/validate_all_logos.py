#!/usr/bin/env python3
"""
Comprehensive Logo Validator for BetLegend
Scans ALL sports pages for broken logos and validates ESPN IDs.

This script:
1. Finds all logo URLs in HTML files
2. Checks against known-broken IDs
3. Validates unknown IDs against ESPN CDN
4. Reports issues and optionally fixes them

Usage:
    python scripts/validate_all_logos.py         # Audit only
    python scripts/validate_all_logos.py --fix   # Audit and fix

Run this BEFORE committing new sports content!
"""

import os
import re
import sys
import argparse
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError

# Auto-detect repo directory
if sys.platform == 'win32':
    REPO_DIR = Path(r'C:\Users\Nima\nimadamus.github.io')
else:
    REPO_DIR = Path(__file__).parent.parent

# =============================================================================
# KNOWN BROKEN IDs - These MUST be corrected
# =============================================================================

BROKEN_SOCCER_IDS = {
    '355': ('397', 'Barnsley'),
    '3199': ('3263', 'Genoa'),
    '3282': ('4050', 'Cremonese'),
    '5168': ('6851', 'Paris FC'),
    '108': ('2925', 'Cagliari'),
}

# =============================================================================
# VERIFIED WORKING IDs - Reference for commonly used teams
# =============================================================================

VERIFIED_SOCCER_IDS = {
    # Premier League
    '359': 'Arsenal', '362': 'Aston Villa', '349': 'Bournemouth',
    '337': 'Brentford', '331': 'Brighton', '379': 'Burnley',
    '363': 'Chelsea', '384': 'Crystal Palace', '368': 'Everton',
    '370': 'Fulham', '364': 'Liverpool', '382': 'Manchester City',
    '360': 'Manchester United', '361': 'Newcastle', '393': 'Nottingham Forest',
    '367': 'Tottenham', '371': 'West Ham', '380': 'Wolves',
    # Championship
    '397': 'Barnsley', '357': 'Leeds', '366': 'Sunderland',
    '372': 'Charlton', '562': 'Exeter City', '2598': 'Accrington Stanley',
    '318': 'Swansea', '2457': 'Wrexham',
    # Serie A
    '103': 'AC Milan', '110': 'Inter', '111': 'Juventus',
    '114': 'Napoli', '104': 'Roma', '112': 'Lazio',
    '105': 'Atalanta', '109': 'Fiorentina', '107': 'Bologna',
    '239': 'Torino', '3263': 'Genoa', '2925': 'Cagliari',
    '4050': 'Cremonese', '488': 'Sassuolo', '3207': 'Lecce',
    '115': 'Parma', '118': 'Udinese', '119': 'Hellas Verona',
    # La Liga
    '83': 'Barcelona', '86': 'Real Madrid', '1068': 'Atletico Madrid',
    '243': 'Sevilla', '85': 'Celta Vigo', '94': 'Valencia',
    '95': 'Mallorca', '96': 'Getafe', '87': 'Rayo Vallecano',
    # Ligue 1
    '160': 'PSG', '6851': 'Paris FC', '176': 'Marseille',
    '167': 'Lyon', '174': 'Monaco', '175': 'Lens', '183': 'Toulouse',
    # Bundesliga
    '132': 'Bayern', '124': 'Dortmund', '131': 'Gladbach/Leverkusen',
}

# Teams WITHOUT ESPN logos (will always show placeholder)
NO_ESPN_LOGO = {
    '131494': 'Macclesfield FC',
    '3129': 'Bromley FC',
}

# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================

def check_url_exists(url, timeout=5):
    """Check if a URL returns 200 OK."""
    try:
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        response = urlopen(req, timeout=timeout)
        return response.status == 200
    except (HTTPError, URLError, Exception):
        return False

def find_all_logos(filepath):
    """Extract all ESPN logo URLs from an HTML file."""
    logos = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # Find all teamlogos URLs
        pattern = r'teamlogos/(soccer|nba|nfl|nhl|ncaa|mlb)/500/([^"\']+\.png)'
        matches = re.findall(pattern, content)

        for sport, logo_file in matches:
            # Extract ID from filename
            logo_id = logo_file.replace('.png', '').replace('scoreboard/', '')
            logos.append({
                'sport': sport,
                'id': logo_id,
                'file': logo_file,
                'full_url': f'https://a.espncdn.com/i/teamlogos/{sport}/500/{logo_file}'
            })
    except Exception as e:
        print(f"Error reading {filepath}: {e}")

    return logos

def validate_file(filepath, verify_online=False):
    """Validate all logos in a single file."""
    issues = []
    logos = find_all_logos(filepath)

    for logo in logos:
        sport = logo['sport']
        logo_id = logo['id']

        # Check for known broken soccer IDs
        if sport == 'soccer' and logo_id in BROKEN_SOCCER_IDS:
            correct_id, team_name = BROKEN_SOCCER_IDS[logo_id]
            issues.append({
                'type': 'BROKEN',
                'file': str(filepath),
                'sport': sport,
                'bad_id': logo_id,
                'correct_id': correct_id,
                'team': team_name,
                'message': f"Broken ID {logo_id} should be {correct_id} ({team_name})"
            })

        # Check for default placeholder (warning only)
        elif 'default-team-logo' in logo_id:
            issues.append({
                'type': 'WARNING',
                'file': str(filepath),
                'sport': sport,
                'bad_id': logo_id,
                'message': f"Using default placeholder (team has no ESPN logo)"
            })

        # Optionally verify unknown IDs online
        elif verify_online and sport == 'soccer' and logo_id not in VERIFIED_SOCCER_IDS:
            if not check_url_exists(logo['full_url']):
                issues.append({
                    'type': 'UNKNOWN',
                    'file': str(filepath),
                    'sport': sport,
                    'bad_id': logo_id,
                    'url': logo['full_url'],
                    'message': f"Unknown ID {logo_id} - URL returns 404"
                })

    return issues

def fix_file(filepath, issues):
    """Fix broken logos in a file."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        original = content
        fixes_made = 0

        for issue in issues:
            if issue['type'] == 'BROKEN' and issue['file'] == str(filepath):
                bad_id = issue['bad_id']
                correct_id = issue['correct_id']
                sport = issue['sport']

                old_pattern = f'teamlogos/{sport}/500/{bad_id}.png'
                new_pattern = f'teamlogos/{sport}/500/{correct_id}.png'

                if old_pattern in content:
                    content = content.replace(old_pattern, new_pattern)
                    fixes_made += 1

        if content != original:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return fixes_made
        return 0
    except Exception as e:
        print(f"Error fixing {filepath}: {e}")
        return 0

def main():
    parser = argparse.ArgumentParser(description='Validate all ESPN logos in sports pages')
    parser.add_argument('--fix', action='store_true', help='Automatically fix broken logos')
    parser.add_argument('--verify', action='store_true', help='Verify unknown IDs online (slow)')
    parser.add_argument('--files', nargs='*', help='Specific files to check (default: all sports pages)')
    args = parser.parse_args()

    print("=" * 60)
    print("BetLegend Logo Validator")
    print("=" * 60)

    # Determine which files to check
    if args.files:
        files = [Path(f) for f in args.files]
    else:
        # All sports pages
        patterns = ['soccer*.html', 'nba*.html', 'nhl*.html', 'nfl*.html',
                   'ncaab*.html', 'ncaaf*.html', 'mlb*.html']
        files = []
        for pattern in patterns:
            files.extend(REPO_DIR.glob(pattern))

        # Exclude calendar and records
        files = [f for f in files if 'calendar' not in f.name and 'records' not in f.name]

    print(f"\nChecking {len(files)} files...")
    if args.verify:
        print("(Online verification enabled - this may be slow)")
    print()

    all_issues = []

    for filepath in sorted(files):
        issues = validate_file(filepath, verify_online=args.verify)
        if issues:
            all_issues.extend(issues)
            for issue in issues:
                print(f"[{issue['type']}] {filepath.name}: {issue['message']}")

    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)

    broken_count = len([i for i in all_issues if i['type'] == 'BROKEN'])
    warning_count = len([i for i in all_issues if i['type'] == 'WARNING'])
    unknown_count = len([i for i in all_issues if i['type'] == 'UNKNOWN'])

    print(f"Broken logos (MUST FIX): {broken_count}")
    print(f"Placeholder warnings:    {warning_count}")
    print(f"Unknown IDs:             {unknown_count}")

    if args.fix and broken_count > 0:
        print()
        print("Fixing broken logos...")

        # Group issues by file
        files_to_fix = set(i['file'] for i in all_issues if i['type'] == 'BROKEN')
        total_fixes = 0

        for filepath in files_to_fix:
            file_issues = [i for i in all_issues if i['file'] == filepath]
            fixes = fix_file(Path(filepath), file_issues)
            if fixes:
                print(f"  Fixed {fixes} logo(s) in {Path(filepath).name}")
                total_fixes += fixes

        print(f"\nTotal fixes: {total_fixes}")

    elif broken_count > 0:
        print()
        print("To fix broken logos, run:")
        print("  python scripts/validate_all_logos.py --fix")
        print()
        print("Or run the sport-specific fixer:")
        print("  python scripts/soccer_logo_ids.py")

    print("=" * 60)

    # Return error code if broken logos found
    return 1 if broken_count > 0 else 0

if __name__ == '__main__':
    sys.exit(main())
