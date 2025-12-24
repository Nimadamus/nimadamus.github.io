#!/usr/bin/env python3
"""
College Football/Basketball Logo ID Mapping
ESPN uses numeric team IDs for college logos.

Usage: Run this script to fix all college logo URLs in HTML files.
"""

import os
import re
from pathlib import Path

# Auto-detect repo directory (works on Windows locally and Linux in GitHub Actions)
import sys
if sys.platform == 'win32':
    REPO_DIR = Path(r'C:\Users\Nima\nimadamus.github.io')
else:
    REPO_DIR = Path(__file__).parent.parent  # scripts/ -> repo root

# ESPN Team ID mapping for college teams
# Format: abbreviated code -> ESPN numeric ID
COLLEGE_TEAM_IDS = {
    # ACC
    'bc': 103, 'bos': 103,       # Boston College
    'clem': 228,                  # Clemson
    'duke': 150,                  # Duke
    'fsu': 52,                    # Florida State
    'gt': 59,                     # Georgia Tech
    'lou': 97,                    # Louisville
    'mia': 2390,                  # Miami
    'unc': 153,                   # North Carolina
    'ncsu': 152, 'ncst': 152,    # NC State
    'pitt': 221,                  # Pittsburgh
    'syr': 183,                   # Syracuse
    'uva': 258,                   # Virginia
    'vt': 259,                    # Virginia Tech
    'wake': 154,                  # Wake Forest
    'cal': 25,                    # California
    'stan': 24,                   # Stanford
    'smu': 2567,                  # SMU

    # Missing ACC/Big East
    'vill': 222,                  # Villanova
    'hall': 2550,                 # Seton Hall
    'sju': 2599,                  # St. John's
    'gonz': 2250,                 # Gonzaga
    'ariz': 12,                   # Arizona

    # Big Ten
    'ill': 356,                   # Illinois
    'ind': 84,                    # Indiana
    'iowa': 2294,                 # Iowa
    'md': 120,                    # Maryland
    'mich': 130,                  # Michigan
    'msu': 127,                   # Michigan State
    'minn': 135,                  # Minnesota
    'neb': 158,                   # Nebraska
    'nu': 77,                     # Northwestern
    'osu': 194,                   # Ohio State
    'psu': 213,                   # Penn State
    'pur': 2509,                  # Purdue
    'rut': 164,                   # Rutgers
    'wisc': 275,                  # Wisconsin
    'ucla': 26,                   # UCLA
    'usc': 30,                    # USC
    'ore': 2483,                  # Oregon
    'wash': 264,                  # Washington

    # Big 12
    'ari': 12,                    # Arizona
    'asu': 9,                     # Arizona State
    'bay': 239,                   # Baylor
    'byu': 252,                   # BYU
    'cin': 2132,                  # Cincinnati
    'col': 38,                    # Colorado
    'hou': 248,                   # Houston
    'isu': 66,                    # Iowa State
    'ku': 2305,                   # Kansas
    'ksu': 2306,                  # Kansas State
    'okst': 197,                  # Oklahoma State
    'tcu': 2628,                  # TCU
    'tex': 251,                   # Texas
    'ttu': 2641,                  # Texas Tech
    'ucf': 2116,                  # UCF
    'wvu': 277,                   # West Virginia
    'utah': 254,                  # Utah

    # SEC
    'ala': 333,                   # Alabama
    'ark': 8,                     # Arkansas
    'aub': 2,                     # Auburn
    'fla': 57,                    # Florida
    'uga': 61,                    # Georgia
    'uk': 96,                     # Kentucky
    'lsu': 99,                    # LSU
    'miss': 145,                  # Ole Miss
    'msst': 344,                  # Mississippi State
    'miz': 142,                   # Missouri
    'ou': 201,                    # Oklahoma
    'scar': 2579,                 # South Carolina
    'tenn': 2633,                 # Tennessee
    'tamu': 245, 'ta&m': 245,    # Texas A&M
    'van': 238,                   # Vanderbilt

    # Group of 5 / Independents
    'mem': 235,                   # Memphis
    'unlv': 2439,                 # UNLV
    'tol': 2649,                  # Toledo
    'wku': 98,                    # Western Kentucky
    'usm': 2572,                  # Southern Miss
    'bois': 68,                   # Boise State
    'troy': 2653,                 # Troy
    'jvst': 55,                   # Jacksonville State
    'odu': 295,                   # Old Dominion
    'usf': 58,                    # South Florida
    'ul': 309,                    # Louisiana
    'del': 48,                    # Delaware
    'most': 2623,                 # Missouri State
    'arst': 2032,                 # Arkansas State
    'kenn': 338,                  # Kennesaw State
    'wmu': 2711,                  # Western Michigan
    'jmu': 256,                   # James Madison
    'tuln': 2655,                 # Tulane
    'ohio': 195,                  # Ohio
    'scst': 2569,                 # South Carolina State
    'pv': 2504,                   # Prairie View A&M
    'nd': 87,                     # Notre Dame
    'army': 349,                  # Army
    'navy': 2426,                 # Navy
    'af': 2005,                   # Air Force
    'byu': 252,                   # BYU
    'conn': 41,                   # UConn
    'umass': 113,                 # UMass
    'lib': 2335,                  # Liberty

    # More G5 teams
    'app': 2026,                  # Appalachian State
    'ccu': 324,                   # Coastal Carolina
    'gaso': 290,                  # Georgia Southern
    'gast': 2247,                 # Georgia State
    'jmu': 256,                   # James Madison
    'marsh': 276, 'mrsh': 276,   # Marshall
    'odu': 295,                   # Old Dominion
    'usa': 6,                     # South Alabama
    'txst': 326,                  # Texas State
    'troy': 2653,                 # Troy
    'ull': 309,                   # Louisiana
    'ulm': 2433,                  # UL Monroe
    'mtsu': 2393,                 # Middle Tennessee
    'wku': 98,                    # Western Kentucky
    'fiu': 2229,                  # FIU
    'fau': 2226,                  # FAU
    'utep': 2638,                 # UTEP
    'unt': 249,                   # North Texas
    'rice': 242,                  # Rice
    'utsa': 2636,                 # UTSA
    'char': 2429,                 # Charlotte
    'uab': 5,                     # UAB
    'akr': 2006,                  # Akron
    'ball': 2050,                 # Ball State
    'bgsu': 189,                  # Bowling Green
    'buff': 2084,                 # Buffalo
    'cmu': 2117,                  # Central Michigan
    'emu': 2199,                  # Eastern Michigan
    'kent': 2309,                 # Kent State
    'mia-oh': 193, 'mioh': 193,  # Miami (OH)
    'niu': 2459,                  # Northern Illinois
    'ohio': 195,                  # Ohio
    'tol': 2649,                  # Toledo
    'wmu': 2711,                  # Western Michigan
    'af': 2005,                   # Air Force
    'bois': 68,                   # Boise State
    'csu': 36,                    # Colorado State
    'fres': 278,                  # Fresno State
    'haw': 62,                    # Hawaii
    'nev': 2440,                  # Nevada
    'unlv': 2439,                 # UNLV
    'nm': 167,                    # New Mexico
    'sdsu': 21,                   # San Diego State
    'sjsu': 23,                   # San Jose State
    'usu': 328,                   # Utah State
    'wyo': 2751,                  # Wyoming

    # FCS / HBCU / Other
    'scst': 2569,                 # South Carolina State
    'pv': 2504,                   # Prairie View A&M
    'gram': 2755,                 # Grambling State
    'alst': 2010,                 # Alabama State
    'famu': 50,                   # Florida A&M
    'jsu': 2296,                  # Jackson State
    'ncat': 2448,                 # North Carolina A&T
    'txso': 2640,                 # Texas Southern
    'sou': 2582,                  # Southern
    'aamu': 2010,                 # Alabama A&M
    'mvsu': 2400,                 # Mississippi Valley State
    'uapb': 2029,                 # Arkansas Pine-Bluff
    'alcn': 2016,                 # Alcorn State

    # More FCS
    'idho': 70,                   # Idaho
    'mont': 149,                  # Montana
    'mtst': 2674,                 # Montana State
    'ndsu': 2449,                 # North Dakota State
    'sdsu': 21,                   # South Dakota State (use San Diego State ID as fallback)
    'und': 2515,                  # North Dakota
    'usd': 233,                   # South Dakota

    # NCAAB additional teams
    'lmu': 2350,                  # Loyola Marymount
    'csub': 2934,                 # Cal State Bakersfield
    'ucr': 2927,                  # UC Riverside
    'morg': 2400,                 # Morgan State
    'harv': 108,                  # Harvard
    'wvut': 2916,                 # WVU Tech (placeholder)
    'gb': 2739,                   # Green Bay
    'cam': 2097,                  # Campbell
    'bing': 2066,                 # Binghamton
    'bell': 2057,                 # Bellarmine
    'lin': 2815,                  # Lindenwood
    'oak': 2473,                  # Oakland
    'dep': 2166,                  # DePaul
    'lbsu': 2815,                 # Long Beach State
    'wsu': 2692,                  # Washington State / Wichita State
    'ilst': 2287,                 # Illinois State
    'ecu': 151,                   # East Carolina
    'etsu': 2193,                 # ETSU
    'vcu': 2670,                  # VCU
    'sfpa': 2608,                 # San Francisco
    'wcu': 2717,                  # Western Carolina
    'dav': 2166,                  # Davidson
    'bcu': 2065,                  # Bethune-Cookman
    'ewu': 331,                   # Eastern Washington
    'but': 2086,                  # Butler
    'acu': 2000,                  # Abilene Christian
    'pac': 279,                   # Pacific
    'quc': 2523,                  # Quinnipiac
    'tow': 119,                   # Towson
    'haw': 62,                    # Hawaii
    'unco': 2458,                 # Northern Colorado
    'lt': 2348,                   # Louisiana Tech

    # Additional small schools
    'colg': 2142,                 # Colgate
    'gweb': 2739,                 # Gardner-Webb
    'las': 2325,                  # La Salle
    'wga': 2739,                  # placeholder
    'amer': 44,                   # American
    'brtn': 2083,                 # Bryant
    'sam': 2534,                  # Samford
    'eccl': 151,                  # placeholder
    'wof': 2747,                  # Wofford
    'rho': 227,                   # Rhode Island
    'stet': 56,                   # Stetson
    'nia': 2450,                  # Niagara
    'etam': 2640,                 # Texas A&M Commerce (placeholder)
    'sela': 2545,                 # SE Louisiana
    'cbvu': 2083,                 # placeholder
    'mncr': 2739,                 # placeholder
    'eawe': 2739,                 # placeholder
    'usi': 2739,                  # placeholder
    'sdst': 2571,                 # South Dakota State
    'una': 2453,                  # North Alabama
    'mcn': 2377,                  # McNeese
    'hcu': 2277,                  # Houston Christian
    'uiw': 2916,                  # Incarnate Word
    'campbellsville': 2739,       # Campbellsville (placeholder)
    'lip': 2335,                  # Lipscomb
}

def fix_logo_url(match):
    """Replace abbreviated code with numeric ID in logo URL."""
    full_match = match.group(0)

    # Extract the team code from the URL
    code_match = re.search(r'/ncaa/500/([^.]+)\.png', full_match)
    if not code_match:
        return full_match

    code = code_match.group(1).lower()

    # Check if this is already a numeric ID
    if code.isdigit():
        return full_match

    # Look up the numeric ID
    if code in COLLEGE_TEAM_IDS:
        team_id = COLLEGE_TEAM_IDS[code]
        return full_match.replace(f'/ncaa/500/{code_match.group(1)}.png', f'/ncaa/500/{team_id}.png')
    else:
        print(f"  WARNING: Unknown team code '{code}' - keeping as-is")
        return full_match

def fix_file(filepath):
    """Fix all college logo URLs in a file."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        original = content

        # Find and fix all ncaa logo URLs
        content = re.sub(
            r'src="https://a\.espncdn\.com/i/teamlogos/ncaa/500/[^"]+\.png"',
            fix_logo_url,
            content
        )

        if content != original:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False

def main():
    print("=" * 60)
    print("College Logo URL Fixer")
    print("Converting abbreviated codes to ESPN numeric IDs")
    print("=" * 60)

    fixed_count = 0

    # Process all HTML files
    for filepath in REPO_DIR.glob('*.html'):
        if fix_file(filepath):
            print(f"Fixed: {filepath.name}")
            fixed_count += 1

    # Also check subfolders
    for filepath in REPO_DIR.glob('**/*.html'):
        if filepath.parent != REPO_DIR:  # Skip already processed root files
            if fix_file(filepath):
                print(f"Fixed: {filepath}")
                fixed_count += 1

    print(f"\n{'=' * 60}")
    print(f"Fixed {fixed_count} files")
    print("=" * 60)

if __name__ == '__main__':
    main()
