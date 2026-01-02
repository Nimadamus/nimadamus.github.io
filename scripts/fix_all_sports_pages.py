#!/usr/bin/env python3
"""
MASTER FIX SCRIPT - Fixes ALL sports page issues at once.
Run this after any major update to ensure consistency.

Fixes:
1. Calendar CSS - removes current-page, ensures today class styling
2. Calendar JS - uses todayStr instead of currentPageDate
3. College logo URLs - converts abbreviations to numeric ESPN IDs
4. Empty logo src tags - flags for review
"""

import os
import re

REPO_PATH = r'C:\Users\Nima\nimadamus.github.io'

# =============================================================================
# COLLEGE TEAM IDs (ESPN numeric)
# =============================================================================
COLLEGE_TEAM_IDS = {
    # SEC
    'ala': '333', 'alabama': '333', 'aub': '2', 'auburn': '2',
    'ark': '8', 'arkansas': '8', 'fla': '57', 'florida': '57',
    'uga': '61', 'georgia': '61', 'ga': '61', 'uky': '96', 'kentucky': '96',
    'lsu': '99', 'miss': '145', 'olemiss': '145',
    'msst': '344', 'mississippi state': '344',
    'miz': '142', 'missouri': '142', 'scar': '2579', 'south carolina': '2579',
    'tenn': '2633', 'tennessee': '2633',
    'tamu': '245', 'texas a&m': '245', 'ta&m': '245', 'tam': '245',
    'van': '238', 'vanderbilt': '238', 'tex': '251', 'texas': '251',
    'ou': '201', 'oklahoma': '201',

    # Big Ten
    'ill': '356', 'illinois': '356', 'ind': '84', 'indiana': '84',
    'iowa': '2294', 'md': '120', 'maryland': '120',
    'mich': '130', 'michigan': '130', 'msu': '127', 'michigan state': '127',
    'minn': '135', 'minnesota': '135', 'neb': '158', 'nebraska': '158',
    'nu': '77', 'northwestern': '77', 'osu': '194', 'ohio state': '194',
    'psu': '213', 'penn state': '213', 'pur': '2509', 'purdue': '2509',
    'rut': '164', 'rutgers': '164', 'wisc': '275', 'wisconsin': '275',
    'ucla': '26', 'usc': '30', 'ore': '2483', 'oregon': '2483',
    'wsu': '265', 'washington state': '265', 'wash': '264', 'washington': '264',

    # ACC
    'bc': '103', 'boston college': '103', 'clem': '228', 'clemson': '228',
    'duke': '150', 'fsu': '52', 'florida state': '52',
    'gt': '59', 'georgia tech': '59', 'lou': '97', 'louisville': '97',
    'mia': '2390', 'miami': '2390', 'unc': '153', 'north carolina': '153',
    'ncsu': '152', 'nc state': '152', 'pitt': '221', 'pittsburgh': '221',
    'cuse': '183', 'syracuse': '183', 'uva': '258', 'virginia': '258',
    'vt': '259', 'virginia tech': '259', 'wake': '154', 'wake forest': '154',
    'smu': '2567', 'cal': '25', 'california': '25', 'stan': '24', 'stanford': '24',

    # Big 12
    'ariz': '12', 'arizona': '12', 'asu': '9', 'arizona state': '9',
    'bay': '239', 'baylor': '239', 'byu': '252',
    'cin': '2132', 'cincinnati': '2132', 'col': '38', 'colorado': '38',
    'hou': '248', 'houston': '248', 'isu': '66', 'iowa state': '66',
    'ku': '2305', 'kansas': '2305', 'ksu': '2306', 'kansas state': '2306',
    'okst': '197', 'oklahoma state': '197', 'tcu': '2628',
    'ttu': '2641', 'texas tech': '2641', 'ucf': '2116',
    'utah': '254', 'wvu': '277', 'west virginia': '277',

    # Mountain West
    'af': '2005', 'air force': '2005', 'bois': '68', 'boise': '68', 'boise state': '68',
    'csu': '36', 'colorado state': '36', 'fres': '278', 'fresno': '278', 'fresno state': '278',
    'haw': '62', 'hawaii': '62', 'nev': '2440', 'nevada': '2440',
    'unm': '167', 'new mexico': '167', 'sdsu': '21', 'san diego state': '21',
    'sjsu': '23', 'san jose state': '23', 'unlv': '2439',
    'usu': '328', 'utah state': '328', 'wyo': '2751', 'wyoming': '2751',

    # AAC
    'army': '349', 'char': '2429', 'charlotte': '2429',
    'ecu': '151', 'east carolina': '151', 'fau': '2226', 'florida atlantic': '2226',
    'mem': '235', 'memphis': '235', 'navy': '2426',
    'rice': '242', 'temp': '218', 'temple': '218',
    'tul': '202', 'tulsa': '202', 'tuln': '2655', 'tulane': '2655',
    'uab': '5', 'unt': '249', 'north texas': '249',
    'usf': '58', 'south florida': '58', 'utsa': '2636',

    # Sun Belt
    'app': '2026', 'appalachian state': '2026',
    'arst': '2032', 'arkansas state': '2032',
    'ccu': '324', 'coastal carolina': '324',
    'gaso': '290', 'georgia southern': '290',
    'gast': '2247', 'georgia state': '2247',
    'jmu': '256', 'james madison': '256',
    'lt': '2348', 'louisiana tech': '2348',
    'marshall': '276', 'odu': '295', 'old dominion': '295',
    'ul': '309', 'louisiana': '309', 'ulm': '2433',
    'usa': '6', 'south alabama': '6', 'troy': '2653',
    'txst': '326', 'texas state': '326',
    'usm': '2572', 'southern miss': '2572',

    # MAC
    'akr': '2006', 'akron': '2006', 'ball': '2050', 'ball state': '2050',
    'bgsu': '189', 'bowling green': '189', 'buff': '2084', 'buffalo': '2084',
    'cmu': '2117', 'central michigan': '2117',
    'emu': '2199', 'eastern michigan': '2199',
    'kent': '2309', 'kent state': '2309',
    'm-oh': '193', 'miamioh': '193', 'miami ohio': '193',
    'niu': '2459', 'northern illinois': '2459',
    'ohio': '195', 'tol': '2649', 'toledo': '2649',
    'wmu': '2711', 'western michigan': '2711',

    # C-USA
    'fiu': '2229', 'jvst': '55', 'jacksonville state': '55',
    'kenn': '338', 'kennesaw': '338', 'lib': '2335', 'liberty': '2335',
    'mtsu': '2393', 'middle tennessee': '2393',
    'nmsu': '166', 'new mexico state': '166',
    'shsu': '2534', 'sam houston': '2534',
    'wku': '98', 'western kentucky': '98',

    # Independents & FCS
    'conn': '41', 'uconn': '41', 'nd': '87', 'notre dame': '87',
    'umass': '113', 'del': '48', 'delaware': '48',
    'ilst': '2287', 'illinois state': '2287',
    'vill': '222', 'villanova': '222',
    'most': '2623', 'missouri state': '2623',
    'mont': '149', 'montana': '149',
    'mtst': '147', 'montana state': '147',
    'ndsu': '2449', 'north dakota state': '2449',
    'scst': '2569', 'south carolina state': '2569',
    'pv': '2504', 'prairie view': '2504',
}

# =============================================================================
# CSS FIXES
# =============================================================================

# Old calendar CSS patterns to replace
OLD_CSS_PATTERNS = [
    # current-page styles - remove entirely
    (r'\.cal-day\.current-page\{[^}]+\}', ''),
    (r'\.cal-day\.current-page:hover\{[^}]+\}', ''),

    # Old has-content with full styling - make subtle
    (r'\.cal-day\.has-content\{background:rgba\(253,80,0,0\.15\);[^}]+\}',
     '.cal-day.has-content{cursor:pointer}'),

    # Old hover - simplify
    (r'\.cal-day\.has-content:hover\{background:rgba\(253,80,0,0\.3\);transform:scale\(1\.1\)\}',
     '.cal-day.has-content:hover{background:rgba(253,80,0,0.2);color:var(--accent-orange)}'),

    # Old today styles - standardize
    (r'\.cal-day\.today\{position:relative\}',
     '.cal-day.today{background:rgba(253,80,0,0.25);color:var(--accent-orange);font-weight:600;border:2px solid var(--accent-gold)}'),
    (r'\.cal-day\.today\{box-shadow:0 0 0 2px var\(--accent-gold\)\}',
     '.cal-day.today{background:rgba(253,80,0,0.25);color:var(--accent-orange);font-weight:600;border:2px solid var(--accent-gold)}'),
]

# JS fixes - replace currentPageDate with todayStr
JS_FIXES = [
    (r"if \(dateStr === currentPageDate\) classes \+= ' current-page';",
     "if (dateStr === todayStr) classes += ' today';"),
    (r'if\(dateStr===currentPageDate\)classes\+=" current-page"',
     "if(dateStr===todayStr)classes+=' today'"),
]

def fix_college_logo_url(match):
    """Convert college logo URL to use numeric ESPN ID."""
    full_url = match.group(0)

    # Extract team code
    pattern = r'ncaa/500/(?:scoreboard/)?([^"\'>\s]+)\.png'
    code_match = re.search(pattern, full_url)

    if not code_match:
        return full_url

    code = code_match.group(1).lower().replace('&amp;', '&')

    # Already numeric - just remove scoreboard/ if present
    if code.isdigit():
        return full_url.replace('/scoreboard/', '/')

    # Look up team ID
    team_id = COLLEGE_TEAM_IDS.get(code)
    if team_id:
        return f'https://a.espncdn.com/i/teamlogos/ncaa/500/{team_id}.png'

    return full_url

def fix_file(filepath):
    """Apply all fixes to a single HTML file."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        original = content

        # 1. Fix CSS patterns
        for pattern, replacement in OLD_CSS_PATTERNS:
            content = re.sub(pattern, replacement, content)

        # 2. Fix JS patterns
        for pattern, replacement in JS_FIXES:
            content = re.sub(pattern, replacement, content)

        # 3. Fix college logo URLs
        content = re.sub(
            r'https://a\.espncdn\.com/i/teamlogos/ncaa/500/[^"\'>\s]+',
            fix_college_logo_url,
            content
        )

        # 4. Clean up duplicate empty lines created by removals
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)

        if content != original:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False

    except Exception as e:
        print(f"  ERROR: {filepath}: {e}")
        return False

def main():
    print("=" * 70)
    print("MASTER FIX SCRIPT - Fixing ALL Sports Pages")
    print("=" * 70)

    fixed_count = 0

    for root, dirs, files in os.walk(REPO_PATH):
        dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules']]

        for filename in files:
            if filename.endswith('.html'):
                filepath = os.path.join(root, filename)
                if fix_file(filepath):
                    print(f"  Fixed: {filename}")
                    fixed_count += 1

    print("=" * 70)
    print(f"Fixed {fixed_count} files")
    print("=" * 70)
    print("\nNext steps:")
    print("1. Run: python scripts/sync_calendars.py")
    print("2. Commit and push changes")

if __name__ == '__main__':
    main()
