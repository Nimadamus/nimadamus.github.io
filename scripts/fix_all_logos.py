#!/usr/bin/env python3
"""
Fix ALL college logo URLs - converts any non-numeric ID to proper ESPN numeric ID.
"""

import os
import re

REPO_PATH = r'C:\Users\Nima\nimadamus.github.io'

# Complete team ID mapping
TEAM_IDS = {
    # SEC
    'ala': '333', 'alabama': '333',
    'aub': '2', 'auburn': '2',
    'ark': '8', 'arkansas': '8',
    'fla': '57', 'florida': '57',
    'uga': '61', 'georgia': '61', 'ga': '61',
    'uky': '96', 'kentucky': '96', 'ky': '96',
    'lsu': '99',
    'miss': '145', 'olemiss': '145', 'ole miss': '145',
    'msst': '344', 'mississippi state': '344', 'msu': '344',
    'miz': '142', 'missouri': '142', 'mo': '142',
    'scar': '2579', 'south carolina': '2579', 'sc': '2579',
    'tenn': '2633', 'tennessee': '2633', 'ut': '2633',
    'tamu': '245', 'texas a&m': '245', 'ta&m': '245', 'tam': '245', 'texasam': '245',
    'van': '238', 'vanderbilt': '238', 'vandy': '238',
    'tex': '251', 'texas': '251',
    'ou': '201', 'oklahoma': '201',

    # Big Ten
    'ill': '356', 'illinois': '356',
    'ind': '84', 'indiana': '84',
    'iowa': '2294',
    'md': '120', 'maryland': '120', 'umd': '120',
    'mich': '130', 'michigan': '130', 'um': '130',
    'msu': '127', 'michiganst': '127', 'michigan state': '127',
    'minn': '135', 'minnesota': '135',
    'neb': '158', 'nebraska': '158',
    'nu': '77', 'northwestern': '77',
    'osu': '194', 'ohio state': '194', 'ohiostate': '194', 'ohst': '194',
    'psu': '213', 'penn state': '213', 'pennstate': '213',
    'pur': '2509', 'purdue': '2509',
    'rut': '164', 'rutgers': '164',
    'wisc': '275', 'wisconsin': '275', 'wis': '275',
    'ucla': '26',
    'usc': '30',
    'ore': '2483', 'oregon': '2483',
    'wsu': '265', 'washington state': '265', 'washst': '265',
    'wash': '264', 'washington': '264', 'uw': '264',

    # ACC
    'bc': '103', 'boston college': '103',
    'clem': '228', 'clemson': '228',
    'duke': '150',
    'fsu': '52', 'florida state': '52', 'floridast': '52',
    'gt': '59', 'georgia tech': '59', 'gatech': '59',
    'lou': '97', 'louisville': '97',
    'mia': '2390', 'miami': '2390',
    'unc': '153', 'north carolina': '153', 'northcarolina': '153',
    'ncsu': '152', 'nc state': '152', 'ncstate': '152',
    'pitt': '221', 'pittsburgh': '221',
    'cuse': '183', 'syracuse': '183', 'syr': '183',
    'uva': '258', 'virginia': '258',
    'vt': '259', 'virginia tech': '259', 'vatech': '259',
    'wake': '154', 'wake forest': '154', 'wakeforest': '154',
    'smu': '2567',
    'cal': '25', 'california': '25',
    'stan': '24', 'stanford': '24',

    # Big 12
    'ariz': '12', 'arizona': '12',
    'asu': '9', 'arizona state': '9', 'arizonast': '9',
    'bay': '239', 'baylor': '239',
    'byu': '252',
    'cin': '2132', 'cincinnati': '2132', 'cinci': '2132',
    'col': '38', 'colorado': '38', 'colo': '38', 'cu': '38',
    'hou': '248', 'houston': '248',
    'isu': '66', 'iowa state': '66', 'iowast': '66',
    'ku': '2305', 'kansas': '2305',
    'ksu': '2306', 'kansas state': '2306', 'kstate': '2306',
    'okst': '197', 'oklahoma state': '197', 'okstate': '197',
    'tcu': '2628',
    'ttu': '2641', 'texas tech': '2641', 'texastech': '2641',
    'ucf': '2116',
    'utah': '254',
    'wvu': '277', 'west virginia': '277', 'westvirginia': '277',

    # Mountain West
    'af': '2005', 'air force': '2005', 'airforce': '2005',
    'bois': '68', 'boise': '68', 'boise state': '68', 'boisestate': '68', 'boisestate': '68',
    'csu': '36', 'colorado state': '36', 'coloradost': '36',
    'fres': '278', 'fresno': '278', 'fresno state': '278', 'fresnst': '278', 'fresnost': '278',
    'haw': '62', 'hawaii': '62',
    'nev': '2440', 'nevada': '2440',
    'unm': '167', 'new mexico': '167', 'newmexico': '167',
    'sdsu': '21', 'san diego state': '21', 'sandiegost': '21',
    'sjsu': '23', 'san jose state': '23', 'sanjosest': '23',
    'unlv': '2439',
    'usu': '328', 'utah state': '328', 'utahst': '328',
    'wyo': '2751', 'wyoming': '2751',

    # AAC
    'army': '349',
    'char': '2429', 'charlotte': '2429',
    'ecu': '151', 'east carolina': '151', 'eastcarolina': '151',
    'fau': '2226', 'florida atlantic': '2226',
    'mem': '235', 'memphis': '235',
    'navy': '2426',
    'rice': '242',
    'temp': '218', 'temple': '218',
    'tul': '202', 'tulsa': '202',
    'tuln': '2655', 'tulane': '2655',
    'uab': '5',
    'unt': '249', 'north texas': '249',
    'usf': '58', 'south florida': '58',
    'utsa': '2636',

    # Sun Belt
    'app': '2026', 'appalachian state': '2026', 'appstate': '2026',
    'arst': '2032', 'arkansas state': '2032', 'arkst': '2032',
    'ccu': '324', 'coastal carolina': '324', 'coastal': '324',
    'gaso': '290', 'georgia southern': '290', 'gasouthern': '290',
    'gast': '2247', 'georgia state': '2247', 'gastate': '2247',
    'jmu': '256', 'james madison': '256', 'jamesmadison': '256',
    'lt': '2348', 'louisiana tech': '2348', 'latech': '2348',
    'marshall': '276', 'marsh': '276',
    'odu': '295', 'old dominion': '295', 'olddominion': '295',
    'ul': '309', 'louisiana': '309', 'ull': '309', 'ulala': '309',
    'ulm': '2433', 'louisiana-monroe': '2433',
    'usa': '6', 'south alabama': '6', 'southalabama': '6',
    'troy': '2653',
    'txst': '326', 'texas state': '326', 'texasst': '326',
    'usm': '2572', 'southern miss': '2572', 'southernmiss': '2572',

    # MAC
    'akr': '2006', 'akron': '2006',
    'ball': '2050', 'ball state': '2050', 'ballst': '2050',
    'bgsu': '189', 'bowling green': '189', 'bowlinggreen': '189',
    'buff': '2084', 'buffalo': '2084',
    'cmu': '2117', 'central michigan': '2117', 'centralmich': '2117',
    'emu': '2199', 'eastern michigan': '2199', 'easternmich': '2199',
    'kent': '2309', 'kent state': '2309', 'kentst': '2309',
    'm-oh': '193', 'miamioh': '193', 'miami ohio': '193', 'miami-oh': '193',
    'niu': '2459', 'northern illinois': '2459',
    'ohio': '195',
    'tol': '2649', 'toledo': '2649',
    'wmu': '2711', 'western michigan': '2711', 'westernmich': '2711',

    # C-USA
    'fiu': '2229', 'florida international': '2229',
    'jvst': '55', 'jacksonville state': '55', 'jaxst': '55', 'jacksonvillest': '55',
    'kenn': '338', 'kennesaw': '338', 'kennesaw state': '338',
    'lib': '2335', 'liberty': '2335',
    'mtsu': '2393', 'middle tennessee': '2393', 'middletenn': '2393',
    'nmsu': '166', 'new mexico state': '166', 'newmexicost': '166',
    'shsu': '2534', 'sam houston': '2534', 'samhouston': '2534',
    'wku': '98', 'western kentucky': '98', 'westernky': '98',

    # Independents
    'conn': '41', 'uconn': '41', 'connecticut': '41',
    'nd': '87', 'notre dame': '87', 'notredame': '87',
    'umass': '113', 'massachusetts': '113',

    # FCS Notable
    'ilst': '2287', 'illinois state': '2287', 'illinoisst': '2287',
    'vill': '222', 'villanova': '222',
    'del': '48', 'delaware': '48',
    'most': '2623', 'missouri state': '2623', 'missourist': '2623',
    'mont': '149', 'montana': '149',
    'mtst': '147', 'montana state': '147', 'montanast': '147',
    'ndsu': '2449', 'north dakota state': '2449',
    'scst': '2569', 'south carolina state': '2569',
    'pv': '2504', 'prairie view': '2504', 'prairieview': '2504',
}

def fix_logo_url(match):
    """Fix a single logo URL match."""
    full_url = match.group(0)

    # Extract the team code from the URL
    # Handles patterns like:
    # - ncaa/500/mem.png
    # - ncaa/500/scoreboard/mem.png
    # - ncaa/500/ta&amp;m.png

    pattern = r'ncaa/500/(?:scoreboard/)?([^".]+)\.png'
    code_match = re.search(pattern, full_url)

    if not code_match:
        return full_url

    code = code_match.group(1).lower()

    # Handle HTML entities
    code = code.replace('&amp;', '&')

    # Check if already numeric
    if code.isdigit():
        # Just remove scoreboard/ if present
        return full_url.replace('/scoreboard/', '/')

    # Look up the team ID
    team_id = TEAM_IDS.get(code)

    if team_id:
        # Build the correct URL
        new_url = f'https://a.espncdn.com/i/teamlogos/ncaa/500/{team_id}.png'
        return new_url
    else:
        print(f"    WARNING: Unknown team code '{code}'")
        return full_url

def fix_file(filepath):
    """Fix all logo URLs in a file."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        original = content

        # Fix all ESPN NCAA logo URLs
        pattern = r'https://a\.espncdn\.com/i/teamlogos/ncaa/500/[^"\'>\s]+'
        content = re.sub(pattern, fix_logo_url, content)

        if content != original:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
    except Exception as e:
        print(f"  ERROR: {filepath}: {e}")
        return False

def main():
    print("=" * 60)
    print("Fixing ALL College Logo URLs")
    print("=" * 60)

    fixed_count = 0

    for root, dirs, files in os.walk(REPO_PATH):
        dirs[:] = [d for d in dirs if d != '.git']

        for filename in files:
            if filename.endswith('.html'):
                filepath = os.path.join(root, filename)
                if fix_file(filepath):
                    print(f"  Fixed: {filename}")
                    fixed_count += 1

    print("=" * 60)
    print(f"Fixed {fixed_count} files")
    print("=" * 60)

if __name__ == '__main__':
    main()
