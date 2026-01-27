#!/usr/bin/env python3
"""
sync_featured_game_preview.py
==============================
Reads the current featured game page and updates the
index.html homepage preview section to match.

MUST be run every time a new featured game page is created or updated.

Usage:
  python C:\\Users\\Nima\\nimadamus.github.io\\scripts\\sync_featured_game_preview.py
"""

import re
import os
import sys

REPO = r'C:\Users\Nima\nimadamus.github.io'
INDEX_PATH = os.path.join(REPO, 'index.html')

# Sport to ESPN logo path
SPORT_LOGO_PATH = {
    'NBA': 'nba', 'NFL': 'nfl', 'NHL': 'nhl', 'MLB': 'mlb',
    'NCAAB': 'ncaa', 'NCAAF': 'ncaa', 'Soccer': 'soccer',
}

# Team colors: (sport, abbreviation) -> (primary_color, accent_color)
TEAM_COLORS = {
    # NBA
    ('NBA', 'ATL'): ('#E03A3E', '#C1D32F'), ('NBA', 'BOS'): ('#007A33', '#BA9653'),
    ('NBA', 'BKN'): ('#000000', '#FFFFFF'), ('NBA', 'CHA'): ('#1D1160', '#00788C'),
    ('NBA', 'CHI'): ('#CE1141', '#000000'), ('NBA', 'CLE'): ('#860038', '#FDBB30'),
    ('NBA', 'DAL'): ('#00538C', '#002B5E'), ('NBA', 'DEN'): ('#0E2240', '#FEC524'),
    ('NBA', 'DET'): ('#C8102E', '#1D428A'), ('NBA', 'GS'): ('#1D428A', '#FFC72C'),
    ('NBA', 'GSW'): ('#1D428A', '#FFC72C'), ('NBA', 'HOU'): ('#CE1141', '#C4CED4'),
    ('NBA', 'IND'): ('#002D62', '#FDBB30'), ('NBA', 'LAC'): ('#C8102E', '#1D428A'),
    ('NBA', 'LAL'): ('#552583', '#FDB927'), ('NBA', 'MEM'): ('#5D76A9', '#12173F'),
    ('NBA', 'MIA'): ('#98002E', '#F9A01B'), ('NBA', 'MIL'): ('#00471B', '#EEE1C6'),
    ('NBA', 'MIN'): ('#0C2340', '#78BE20'), ('NBA', 'NOP'): ('#0C2340', '#C8102E'),
    ('NBA', 'NO'): ('#0C2340', '#C8102E'), ('NBA', 'NY'): ('#006BB6', '#F58426'),
    ('NBA', 'NYK'): ('#006BB6', '#F58426'), ('NBA', 'OKC'): ('#007AC1', '#EF6100'),
    ('NBA', 'ORL'): ('#0077C0', '#C4CED4'), ('NBA', 'PHI'): ('#006BB6', '#ED174C'),
    ('NBA', 'PHX'): ('#1D1160', '#E56020'), ('NBA', 'POR'): ('#E03A3E', '#000000'),
    ('NBA', 'SAC'): ('#5A2D81', '#63727A'), ('NBA', 'SA'): ('#C4CED4', '#000000'),
    ('NBA', 'SAS'): ('#C4CED4', '#000000'), ('NBA', 'TOR'): ('#CE1141', '#000000'),
    ('NBA', 'UTA'): ('#002B5C', '#00471B'), ('NBA', 'WAS'): ('#002B5C', '#E31837'),
    # NFL
    ('NFL', 'ARI'): ('#97233F', '#000000'), ('NFL', 'ATL'): ('#A71930', '#000000'),
    ('NFL', 'BAL'): ('#241773', '#9E7C0C'), ('NFL', 'BUF'): ('#00338D', '#C60C30'),
    ('NFL', 'CAR'): ('#0085CA', '#101820'), ('NFL', 'CHI'): ('#0B162A', '#C83803'),
    ('NFL', 'CIN'): ('#FB4F14', '#000000'), ('NFL', 'CLE'): ('#311D00', '#FF3C00'),
    ('NFL', 'DAL'): ('#003594', '#869397'), ('NFL', 'DEN'): ('#FB4F14', '#002244'),
    ('NFL', 'DET'): ('#0076B6', '#B0B7BC'), ('NFL', 'GB'): ('#203731', '#FFB612'),
    ('NFL', 'HOU'): ('#03202F', '#A71930'), ('NFL', 'IND'): ('#002C5F', '#A2AAAD'),
    ('NFL', 'JAX'): ('#006778', '#9F792C'), ('NFL', 'KC'): ('#E31837', '#FFB81C'),
    ('NFL', 'LAC'): ('#0080C6', '#FFC20E'), ('NFL', 'LAR'): ('#003594', '#FFA300'),
    ('NFL', 'LV'): ('#A5ACAF', '#000000'), ('NFL', 'MIA'): ('#008E97', '#FC4C02'),
    ('NFL', 'MIN'): ('#4F2683', '#FFC62F'), ('NFL', 'NE'): ('#002244', '#C60C30'),
    ('NFL', 'NO'): ('#D3BC8D', '#101820'), ('NFL', 'NYG'): ('#0B2265', '#A71930'),
    ('NFL', 'NYJ'): ('#125740', '#000000'), ('NFL', 'PHI'): ('#004C54', '#A5ACAF'),
    ('NFL', 'PIT'): ('#FFB612', '#101820'), ('NFL', 'SF'): ('#AA0000', '#B3995D'),
    ('NFL', 'SEA'): ('#002244', '#69BE28'), ('NFL', 'TB'): ('#D50A0A', '#34302B'),
    ('NFL', 'TEN'): ('#0C2340', '#4B92DB'), ('NFL', 'WSH'): ('#5A1414', '#FFB612'),
    # NHL
    ('NHL', 'ANA'): ('#F47A38', '#B9975B'), ('NHL', 'BOS'): ('#FFB81C', '#000000'),
    ('NHL', 'BUF'): ('#002654', '#FCB514'), ('NHL', 'CAR'): ('#CC0000', '#000000'),
    ('NHL', 'CBJ'): ('#002654', '#CE1141'), ('NHL', 'CGY'): ('#D2001C', '#F1BE48'),
    ('NHL', 'CHI'): ('#CF0A2C', '#000000'), ('NHL', 'COL'): ('#6F263D', '#236192'),
    ('NHL', 'DAL'): ('#006847', '#8F8F8C'), ('NHL', 'DET'): ('#CE1141', '#FFFFFF'),
    ('NHL', 'EDM'): ('#041E42', '#FF4C00'), ('NHL', 'FLA'): ('#041E42', '#C8102E'),
    ('NHL', 'LA'): ('#111111', '#A2AAAD'), ('NHL', 'MIN'): ('#154734', '#A6192E'),
    ('NHL', 'MTL'): ('#AF1E2D', '#192168'), ('NHL', 'NJ'): ('#CE1141', '#000000'),
    ('NHL', 'NJD'): ('#CE1141', '#000000'), ('NHL', 'NSH'): ('#FFB81C', '#041E42'),
    ('NHL', 'NYI'): ('#00539B', '#F47D30'), ('NHL', 'NYR'): ('#0038A8', '#CE1141'),
    ('NHL', 'OTT'): ('#C52032', '#C2912C'), ('NHL', 'PHI'): ('#F74902', '#000000'),
    ('NHL', 'PIT'): ('#FFB81C', '#000000'), ('NHL', 'SEA'): ('#001628', '#99D9D9'),
    ('NHL', 'SJ'): ('#006D75', '#EA7200'), ('NHL', 'STL'): ('#002F87', '#FCB514'),
    ('NHL', 'TB'): ('#002868', '#FFFFFF'), ('NHL', 'TOR'): ('#00205B', '#FFFFFF'),
    ('NHL', 'UTA'): ('#6CACE4', '#010101'), ('NHL', 'VAN'): ('#00205B', '#00843D'),
    ('NHL', 'VGK'): ('#B4975A', '#333F42'), ('NHL', 'WPG'): ('#041E42', '#004C97'),
    ('NHL', 'WSH'): ('#C8102E', '#041E42'),
}

DEFAULT_COLORS = ('#1a365d', '#FFD700')


def get_team_colors(sport, abbr):
    """Get (primary, accent) colors for a team."""
    return TEAM_COLORS.get((sport, abbr.upper()), DEFAULT_COLORS)


def get_current_featured_page(index_content):
    """Find which featured game page index.html links to."""
    match = re.search(r'href="(featured-game-of-the-day-page\d+\.html)"', index_content)
    return match.group(1) if match else None


def extract_game_data(page_content):
    """Extract all game data from a featured game page."""
    data = {}

    # Sport from title: "NBA: Lakers @ Bulls - January 26, 2026 | BetLegend"
    title_match = re.search(r'<title>\s*(NBA|NFL|NHL|MLB|NCAAB|NCAAF|Soccer)\s*:', page_content)
    data['sport'] = title_match.group(1) if title_match else 'NBA'
    data['sport_path'] = SPORT_LOGO_PATH.get(data['sport'], 'nba')

    # Team abbreviations from <img> tag logo URLs only (skip meta tags)
    logo_pattern = rf'<img[^>]+teamlogos/{re.escape(data["sport_path"])}/500/(\w+)\.png'
    logos_raw = re.findall(logo_pattern, page_content, re.IGNORECASE)
    # Deduplicate preserving order of first appearance
    seen = set()
    logos = []
    for logo in logos_raw:
        upper = logo.upper()
        if upper not in seen:
            seen.add(upper)
            logos.append(upper)
    if len(logos) >= 2:
        data['away_abbr'] = logos[0]
        data['home_abbr'] = logos[1]
    else:
        # Fallback: try any sport path in <img> tags
        all_logos_raw = re.findall(r'<img[^>]+teamlogos/\w+/500/(\w+)\.png', page_content, re.IGNORECASE)
        seen2 = set()
        all_logos = []
        for logo in all_logos_raw:
            upper = logo.upper()
            if upper not in seen2:
                seen2.add(upper)
                all_logos.append(upper)
        if len(all_logos) >= 2:
            data['away_abbr'] = all_logos[0]
            data['home_abbr'] = all_logos[1]
        else:
            print("ERROR: Could not extract team abbreviations from featured game page")
            return None

    # Team short names from title: "NBA: Lakers @ Bulls - ..."
    name_match = re.search(r'<title>\s*\w+:\s*(.+?)\s*@\s*(.+?)\s*-', page_content)
    if name_match:
        data['away_name'] = name_match.group(1).strip()
        data['home_name'] = name_match.group(2).strip()
    else:
        data['away_name'] = data['away_abbr']
        data['home_name'] = data['home_abbr']

    # Team records: look for (XX-XX) or (XX-XX-XX) patterns
    records = re.findall(r'\((\d+-\d+(?:-\d+)?)\)', page_content)
    if len(records) >= 2:
        data['away_record'] = records[0]
        data['home_record'] = records[1]
    else:
        data['away_record'] = '0-0'
        data['home_record'] = '0-0'

    # Spread (handles "Spread", "Puck Line", "Run Line")
    spread_match = re.search(
        r'(?:Spread|Puck Line|Run Line)</div>.*?class="line-value">\s*([^<]+?)\s*</div>',
        page_content, re.DOTALL | re.IGNORECASE
    )
    if spread_match:
        spread_full = spread_match.group(1).strip()
        data['away_spread'] = spread_full.split('/')[0].strip()
    else:
        data['away_spread'] = f"{data['away_abbr']} PK"

    # Total (O/U)
    total_match = re.search(
        r'Total</div>.*?class="line-value">\s*([^<]+?)\s*</div>',
        page_content, re.DOTALL | re.IGNORECASE
    )
    data['total'] = total_match.group(1).strip() if total_match else 'O/U TBD'

    # Moneyline
    ml_match = re.search(
        r'Moneyline</div>.*?class="line-value">\s*([^<]+?)\s*</div>',
        page_content, re.DOTALL | re.IGNORECASE
    )
    if ml_match:
        data['moneyline'] = ml_match.group(1).strip().replace(' / ', ' | ')
    else:
        data['moneyline'] = f"{data['away_abbr']} TBD | {data['home_abbr']} TBD"

    # Game details: "Monday, January 26, 2026 | 8:00 PM ET | United Center, Chicago | ESPN"
    details_match = re.search(r'class="game-details">\s*([^<]+?)\s*</div>', page_content)
    if details_match:
        details = details_match.group(1).strip()
        parts = [p.strip() for p in details.split('|')]

        if len(parts) >= 4:
            date_str = parts[0]
            data['time'] = parts[1]
            # Venue: take name only, strip city after comma
            venue_full = parts[2]
            data['venue'] = venue_full.split(',')[0].strip()
            data['network'] = parts[3]

            # Short date: "January 26" from "Monday, January 26, 2026"
            month_match = re.search(
                r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d+',
                date_str
            )
            data['short_date'] = month_match.group(0) if month_match else date_str
        elif len(parts) >= 3:
            data['time'] = parts[0]
            data['venue'] = parts[1].split(',')[0].strip()
            data['network'] = parts[2]
            data['short_date'] = 'Today'
        else:
            data['time'] = '7:00 PM ET'
            data['venue'] = 'TBD'
            data['network'] = 'TBD'
            data['short_date'] = 'Today'
    else:
        data['time'] = '7:00 PM ET'
        data['venue'] = 'TBD'
        data['network'] = 'TBD'
        data['short_date'] = 'Today'

    # Team colors
    away_primary, away_accent = get_team_colors(data['sport'], data['away_abbr'])
    home_primary, _ = get_team_colors(data['sport'], data['home_abbr'])
    data['away_color'] = away_primary
    data['away_accent'] = away_accent
    data['home_color'] = home_primary

    return data


def generate_preview_html(data):
    """Generate the Featured Game preview HTML for index.html."""
    return f'''<!-- Header Banner - Matchup Info -->
                <div style="background: linear-gradient(135deg, {data['away_color']} 0%, {data['home_color']} 100%); padding: 10px 20px 12px 20px; border-bottom: 2px solid rgba(255,107,0,0.5);">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                        <span style="font-family: var(--font-primary); font-size: 0.75rem; color: {data['away_accent']}; text-transform: uppercase; letter-spacing: 2px; font-weight: 700;">{data['sport']} on {data['network']}</span>
                        <span style="background: #39FF14; color: #000; font-family: var(--font-primary); font-size: 0.7rem; font-weight: 700; padding: 4px 12px; border-radius: 4px; text-transform: uppercase;">{data['time']}</span>
                    </div>
                    <div style="display: flex; align-items: center; justify-content: center; gap: 15px;">
                        <div style="text-align: center;">
                            <img src="https://a.espncdn.com/i/teamlogos/{data['sport_path']}/500/{data['away_abbr'].lower()}.png" alt="{data['away_name']}" style="width: 45px; height: 45px; margin-bottom: 4px;">
                            <div style="font-family: var(--font-primary); font-size: 0.9rem; color: #fff; font-weight: 700;">{data['away_name']}</div>
                            <div style="font-size: 0.75rem; color: #ddd;">({data['away_record']})</div>
                        </div>
                        <div style="font-family: var(--font-primary); font-size: 1.3rem; color: {data['away_accent']}; font-weight: 900;">@</div>
                        <div style="text-align: center;">
                            <img src="https://a.espncdn.com/i/teamlogos/{data['sport_path']}/500/{data['home_abbr'].lower()}.png" alt="{data['home_name']}" style="width: 45px; height: 45px; margin-bottom: 4px;">
                            <div style="font-family: var(--font-primary); font-size: 0.9rem; color: #fff; font-weight: 700;">{data['home_name']}</div>
                            <div style="font-size: 0.75rem; color: #ddd;">({data['home_record']})</div>
                        </div>
                    </div>
                    <div style="text-align: center; margin-top: 6px; font-size: 0.75rem; color: #f0d0d0;">{data['short_date']} | {data['venue']} | {data['network']}</div>
                </div>

                <!-- FREE PICK - Main focus, tighter -->
                <div style="padding: 8px 20px 12px 20px; background: linear-gradient(180deg, rgba(0,20,10,0.95) 0%, rgba(0,30,15,0.9) 100%); text-align: center; border-left: 4px solid #39FF14; border-right: 4px solid #39FF14;" onclick="gtag('event', 'free_pick_click', {{'event_category': 'engagement'}});">
                    <div style="font-family: var(--font-primary); font-size: 0.85rem; color: #39FF14; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 8px; font-weight: 700;">Tonight's Featured Game</div>
                    <div style="font-family: var(--font-primary); font-size: 1.3rem; font-weight: 900; color: #fff; text-shadow: 0 0 20px rgba(255,255,255,0.2); margin-bottom: 3px;">
                        {data['away_spread']} | {data['total']}
                    </div>
                    <div style="font-family: var(--font-primary); font-size: 0.9rem; font-weight: 700; color: var(--neon-gold);">
                        {data['moneyline']}
                    </div>
                    <div style="margin-top: 8px; font-size: 0.95rem; color: rgba(57, 255, 20, 0.9); font-family: var(--font-primary); letter-spacing: 2px; font-weight: 700;">
                        {data['away_abbr']} @ {data['home_abbr']} | {data['time']} | {data['network']}
                    </div>
                </div>

'''


def sync_preview():
    """Main sync function."""
    print("=" * 60)
    print("  FEATURED GAME PREVIEW SYNC")
    print("=" * 60)

    # Read index.html
    with open(INDEX_PATH, 'r', encoding='utf-8', errors='ignore') as f:
        index_content = f.read()

    # Find current featured game page
    page_filename = get_current_featured_page(index_content)
    if not page_filename:
        print("ERROR: Could not find featured game page link in index.html")
        return False

    print(f"\n  Featured game page: {page_filename}")

    # Read featured game page
    page_path = os.path.join(REPO, page_filename)
    if not os.path.exists(page_path):
        print(f"  ERROR: File not found: {page_path}")
        return False

    with open(page_path, 'r', encoding='utf-8', errors='ignore') as f:
        page_content = f.read()

    # Extract game data
    data = extract_game_data(page_content)
    if not data:
        print("  ERROR: Could not extract game data")
        return False

    print(f"  Game: {data['away_name']} ({data['away_abbr']}) @ {data['home_name']} ({data['home_abbr']})")
    print(f"  Sport: {data['sport']} | Time: {data['time']} | Network: {data['network']}")
    print(f"  Spread: {data['away_spread']} | Total: {data['total']}")
    print(f"  Moneyline: {data['moneyline']}")
    print(f"  Colors: {data['away_color']} -> {data['home_color']} (accent: {data['away_accent']})")

    # Generate new preview HTML
    new_preview = generate_preview_html(data)

    # Replace in index.html
    pattern = r'<!-- Header Banner - Matchup Info -->.*?(?=\s*<!-- CTA to Full Breakdown -->)'

    if not re.search(pattern, index_content, re.DOTALL):
        print("\n  ERROR: Could not find Featured Game preview section in index.html")
        print("  Looking for: <!-- Header Banner - Matchup Info --> ... <!-- CTA to Full Breakdown -->")
        return False

    updated_content = re.sub(pattern, new_preview.rstrip(), index_content, flags=re.DOTALL)

    # Verify something actually changed (or already synced)
    if updated_content == index_content:
        print("\n  Already in sync - no changes needed.")
        return True

    # Write updated index.html
    with open(INDEX_PATH, 'w', encoding='utf-8') as f:
        f.write(updated_content)

    print(f"\n  SUCCESS: index.html preview updated to match {page_filename}")
    print("=" * 60)
    return True


def verify_sync():
    """Verify that index.html preview matches the featured game page (read-only check)."""
    print("=" * 60)
    print("  FEATURED GAME SYNC VERIFICATION")
    print("=" * 60)

    with open(INDEX_PATH, 'r', encoding='utf-8', errors='ignore') as f:
        index_content = f.read()

    page_filename = get_current_featured_page(index_content)
    if not page_filename:
        print("  ERROR: No featured game link found")
        return False

    page_path = os.path.join(REPO, page_filename)
    if not os.path.exists(page_path):
        print(f"  ERROR: {page_filename} not found")
        return False

    with open(page_path, 'r', encoding='utf-8', errors='ignore') as f:
        page_content = f.read()

    data = extract_game_data(page_content)
    if not data:
        print("  ERROR: Could not extract game data")
        return False

    # Check internal consistency of index.html
    section_match = re.search(
        r'<!-- Header Banner - Matchup Info -->(.+?)<!-- CTA to Full Breakdown -->',
        index_content, re.DOTALL
    )
    if not section_match:
        print("  WARNING: No featured game section found in index.html")
        return True

    section = section_match.group(1)

    # Extract team abbrs from logos in the section
    logos = re.findall(r'teamlogos/\w+/500/(\w+)\.png', section, re.IGNORECASE)
    if len(logos) < 2:
        print("  WARNING: Could not find team logos in preview section")
        return True

    header_away = logos[0].upper()
    header_home = logos[1].upper()

    # Extract team abbrs from the matchup line (e.g., "LAL @ CHI | ...")
    matchup_match = re.search(r'>\s*(\w{2,4})\s*@\s*(\w{2,4})\s*\|', section)
    if not matchup_match:
        print("  WARNING: Could not find matchup line in preview section")
        return True

    lines_away = matchup_match.group(1).upper()
    lines_home = matchup_match.group(2).upper()

    errors = []

    # Check header logos match betting lines
    if header_away != lines_away:
        errors.append(f"Header logo shows {header_away} but betting lines show {lines_away}")
    if header_home != lines_home:
        errors.append(f"Header logo shows {header_home} but betting lines show {lines_home}")

    # Check index.html matches featured game page
    if header_away != data['away_abbr']:
        errors.append(f"Index shows {header_away} but {page_filename} has {data['away_abbr']}")
    if header_home != data['home_abbr']:
        errors.append(f"Index shows {header_home} but {page_filename} has {data['home_abbr']}")

    if errors:
        print(f"\n  MISMATCH DETECTED:")
        for e in errors:
            print(f"    [ERROR] {e}")
        print(f"\n  FIX: Run this script without --verify to sync automatically")
        print("=" * 60)
        return False
    else:
        print(f"\n  SYNCED: index.html preview matches {page_filename}")
        print(f"  Game: {data['away_abbr']} @ {data['home_abbr']} ({data['sport']})")
        print("=" * 60)
        return True


if __name__ == '__main__':
    if '--verify' in sys.argv:
        success = verify_sync()
    else:
        success = sync_preview()
    sys.exit(0 if success else 1)
