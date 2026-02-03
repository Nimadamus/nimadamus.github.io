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

# Auto-detect repo path (works on Windows locally and in GitHub Actions)
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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

# NCAAB ESPN numeric IDs to team names/abbreviations
# The ESPN CDN uses numeric IDs for college logos (e.g., ncaa/500/2305.png)
NCAAB_TEAM_MAP = {
    '2305': ('Kansas', 'KU'),
    '2641': ('Texas Tech', 'TTU'),
    '127': ('Michigan', 'MICH'),
    '130': ('Michigan State', 'MSU'),
    '2': ('Auburn', 'AUB'),
    '333': ('Alabama', 'ALA'),
    '61': ('Georgia', 'UGA'),
    '57': ('Florida', 'UF'),
    '96': ('Louisville', 'LOU'),
    '97': ('Kentucky', 'UK'),
    '153': ('Duke', 'DUKE'),
    '152': ('NC State', 'NCST'),
    '153': ('Duke', 'DUKE'),
    '99': ('North Carolina', 'UNC'),
    '12': ('Arizona', 'ARIZ'),
    '9': ('Arizona State', 'ASU'),
    '2483': ('UCLA', 'UCLA'),
    '26': ('USC', 'USC'),
    '30': ('Stanford', 'STAN'),
    '251': ('Texas', 'TEX'),
    '239': ('Texas A&M', 'TAMU'),
    '248': ('TCU', 'TCU'),
    '66': ('Baylor', 'BAY'),
    '156': ('Houston', 'HOU'),
    '120': ('Iowa', 'IOWA'),
    '84': ('Iowa State', 'ISU'),
    '2509': ('Purdue', 'PUR'),
    '84': ('Illinois', 'ILL'),
    '275': ('Wisconsin', 'WISC'),
    '356': ('UConn', 'UCONN'),
    '258': ('Villanova', 'NOVA'),
    '150': ('Marquette', 'MARQ'),
    '2250': ('Gonzaga', 'GONZ'),
    '2': ('Auburn', 'AUB'),
    '328': ('Tennessee', 'TENN'),
    '238': ('Ole Miss', 'MISS'),
    '8': ('Arkansas', 'ARK'),
    '2390': ('Miami OH', 'MIAOH'),
    '2084': ('Buffalo', 'BUFF'),
    '2006': ('Akron', 'AKR'),
    '2199': ('Eastern Michigan', 'EMU'),
    '2181': ('Canisius', 'CAN'),
    '2430': ('Niagara', 'NIAG'),
    '52': ('Florida State', 'FSU'),
    '228': ('Clemson', 'CLEM'),
    '2628': ('Syracuse', 'SYR'),
    '259': ('Virginia', 'UVA'),
    '258': ('Virginia Tech', 'VT'),
    '2566': ('St. Johns', 'SJU'),
    '164': ('Providence', 'PROV'),
    '2507': ('Creighton', 'CREI'),
    '2086': ('Butler', 'BUT'),
    '2229': ('Dayton', 'DAY'),
    '2599': ('San Diego State', 'SDSU'),
    '68': ('Boise State', 'BSU'),
    '2440': ('Nevada', 'NEV'),
    '2348': ('New Mexico', 'UNM'),
    '2439': ('UNLV', 'UNLV'),
    '235': ('Memphis', 'MEM'),
    '2116': ('Cincinnati', 'CIN'),
    '197': ('Oklahoma', 'OU'),
    '201': ('Oklahoma State', 'OKST'),
    '2306': ('Kansas State', 'KSU'),
    '2628': ('Colorado', 'COL'),
    '254': ('Utah', 'UTAH'),
    '252': ('BYU', 'BYU'),
}


def get_ncaab_team_info(espn_id):
    """Get (name, abbreviation) for NCAAB team from ESPN numeric ID."""
    return NCAAB_TEAM_MAP.get(str(espn_id), (str(espn_id), str(espn_id)))


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

    # For NCAAB/NCAAF: If abbreviations are numeric ESPN IDs, convert to team names
    if data['sport'] in ('NCAAB', 'NCAAF'):
        # Check if away_abbr is a numeric ID
        if data['away_abbr'].isdigit():
            away_name, away_abbr = get_ncaab_team_info(data['away_abbr'])
            data['away_name'] = away_name
            data['away_abbr'] = away_abbr
        # Check if home_abbr is a numeric ID
        if data['home_abbr'].isdigit():
            home_name, home_abbr = get_ncaab_team_info(data['home_abbr'])
            data['home_name'] = home_name
            data['home_abbr'] = home_abbr

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

    # Extract injuries from the featured game page
    # Look for injury section patterns
    data['away_injuries'] = 'Check injury report'
    data['home_injuries'] = 'Check injury report'

    # Try to find injury data in the featured game page
    # Pattern 1: Look for injury-item divs
    injury_items = re.findall(
        r'class="injury-item"[^>]*>.*?<span[^>]*>([^<]+)</span>.*?<span[^>]*>([^<]+)</span>',
        page_content, re.DOTALL | re.IGNORECASE
    )

    away_injuries = []
    home_injuries = []

    # Pattern 2: Look for "Key Injuries" or "Injury Report" sections
    injury_section = re.search(
        r'(?:Key Injuries|Injury Report|Injuries to Watch).*?</section>',
        page_content, re.DOTALL | re.IGNORECASE
    )

    if injury_section:
        section_text = injury_section.group(0)
        # Look for player names with injury status
        # Pattern: "Player Name (injury) - Status" or "Player Name - Status (injury)"
        injury_patterns = re.findall(
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\s*[\(\-]\s*([\w\s]+?)[\)\-]\s*[\-\:]\s*(OUT|GTD|Questionable|Doubtful|Probable)',
            section_text, re.IGNORECASE
        )
        for name, injury, status in injury_patterns:
            # Determine which team based on position in section or nearby team reference
            pass  # Complex logic needed here

    # Pattern 3: Look for simpler injury mentions
    # "DAL: Player (injury) - OUT" or "Away Team Injuries: ..."
    away_inj_match = re.search(
        rf'{data["away_abbr"]}[:\s]+([^<\n]+(?:OUT|GTD|Questionable|Doubtful)[^<\n]*)',
        page_content, re.IGNORECASE
    )
    if away_inj_match:
        data['away_injuries'] = away_inj_match.group(1).strip()[:60]  # Limit length

    home_inj_match = re.search(
        rf'{data["home_abbr"]}[:\s]+([^<\n]+(?:OUT|GTD|Questionable|Doubtful)[^<\n]*)',
        page_content, re.IGNORECASE
    )
    if home_inj_match:
        data['home_injuries'] = home_inj_match.group(1).strip()[:60]

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


def generate_preview_html(data, page_filename):
    """Generate the Featured Game preview HTML for index.html.

    IMPORTANT: This must match the exact structure in index.html:
    1. Header Banner - Matchup Info
    2. Betting Lines Table
    3. Betting Trends (Records)
    4. Injuries
    5. Link to Featured Game Page (View Full Breakdown)
    6. Subscribe to Premium Button
    7. Affiliate Banner (YouWager)
    """
    # Parse spread to get numbers
    away_spread = data.get('away_spread', 'PK')
    # Try to extract numeric spread for home team (opposite sign)
    spread_num = re.search(r'([+-]?\d+\.?\d*)', away_spread)
    if spread_num:
        away_spread_val = float(spread_num.group(1))
        home_spread_val = -away_spread_val
        home_spread = f"+{home_spread_val}" if home_spread_val > 0 else str(home_spread_val)
        away_spread_display = f"+{abs(away_spread_val)}" if away_spread_val > 0 else f"-{abs(away_spread_val)}"
    else:
        away_spread_display = "PK"
        home_spread = "PK"

    # Parse moneyline
    ml_parts = data.get('moneyline', '').split('|')
    away_ml = ml_parts[0].strip().split()[-1] if ml_parts else '-110'
    home_ml = ml_parts[1].strip().split()[-1] if len(ml_parts) > 1 else '+100'

    # Parse total
    total = data.get('total', 'O/U 220').replace('O/U ', '')

    return f'''<!-- Header Banner - Matchup Info -->
                <div style="background: linear-gradient(135deg, {data['away_color']} 0%, {data['home_color']} 100%); padding: 14px 20px; border-bottom: 3px solid {data['away_accent']};">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                        <span style="font-family: var(--font-primary); font-size: 0.75rem; color: {data['away_accent']}; text-transform: uppercase; letter-spacing: 2px; font-weight: 700;">Tonight's Featured Game</span>
                        <span style="background: #39FF14; color: #000; font-family: var(--font-primary); font-size: 0.7rem; font-weight: 700; padding: 4px 12px; border-radius: 4px; text-transform: uppercase;">{data['sport']} {data['time']}</span>
                    </div>
                    <div style="display: flex; align-items: center; justify-content: center; gap: 20px;">
                        <div style="text-align: center;">
                            <img src="https://a.espncdn.com/i/teamlogos/{data['sport_path']}/500/{data['away_abbr'].lower()}.png" style="width: 55px; height: 55px; margin-bottom: 6px;">
                            <div style="font-family: var(--font-primary); font-size: 1rem; color: #fff; font-weight: 700;">{data['away_name']}</div>
                            <div style="font-size: 0.85rem; color: #aaa;">({data['away_record']})</div>
                        </div>
                        <div style="font-family: var(--font-primary); font-size: 1.5rem; color: {data['away_accent']}; font-weight: 900;">@</div>
                        <div style="text-align: center;">
                            <img src="https://a.espncdn.com/i/teamlogos/{data['sport_path']}/500/{data['home_abbr'].lower()}.png" style="width: 55px; height: 55px; margin-bottom: 6px;">
                            <div style="font-family: var(--font-primary); font-size: 1rem; color: #fff; font-weight: 700;">{data['home_name']}</div>
                            <div style="font-size: 0.85rem; color: #aaa;">({data['home_record']})</div>
                        </div>
                    </div>
                    <div style="text-align: center; margin-top: 10px; font-size: 0.8rem; color: #8ab4f8;">{data['short_date']} | {data['venue']} | {data['network']}</div>
                </div>

                <!-- Betting Lines Table -->
                <div style="padding: 10px 20px; background: rgba(0,0,0,0.3);">
                    <table style="width: 100%; border-collapse: collapse; font-family: var(--font-secondary);">
                        <thead>
                            <tr style="border-bottom: 2px solid rgba(239,97,0,0.5);">
                                <th style="text-align: left; padding: 6px 5px; font-size: 0.7rem; color: #888; text-transform: uppercase; font-weight: 600;">Team</th>
                                <th style="text-align: center; padding: 6px 5px; font-size: 0.7rem; color: #888; text-transform: uppercase; font-weight: 600;">Spread</th>
                                <th style="text-align: center; padding: 6px 5px; font-size: 0.7rem; color: #888; text-transform: uppercase; font-weight: 600;">ML</th>
                                <th style="text-align: center; padding: 6px 5px; font-size: 0.7rem; color: #888; text-transform: uppercase; font-weight: 600;">O/U</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr style="border-bottom: 1px solid rgba(255,255,255,0.1);">
                                <td style="padding: 8px 5px; display: flex; align-items: center; gap: 8px;">
                                    <img src="https://a.espncdn.com/i/teamlogos/{data['sport_path']}/500/{data['away_abbr'].lower()}.png" style="width: 22px; height: 22px;">
                                    <span style="font-weight: 600; color: #fff; font-size: 0.9rem;">{data['away_abbr']}</span>
                                </td>
                                <td style="text-align: center; padding: 8px 5px; font-weight: 700; color: #39FF14; font-size: 0.95rem;">{away_spread_display}</td>
                                <td style="text-align: center; padding: 8px 5px; font-weight: 700; color: #39FF14; font-size: 0.95rem;">{away_ml}</td>
                                <td style="text-align: center; padding: 8px 5px; font-weight: 600; color: #fff; font-size: 0.9rem;">O {total}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 5px; display: flex; align-items: center; gap: 8px;">
                                    <img src="https://a.espncdn.com/i/teamlogos/{data['sport_path']}/500/{data['home_abbr'].lower()}.png" style="width: 22px; height: 22px;">
                                    <span style="font-weight: 600; color: #fff; font-size: 0.9rem;">{data['home_abbr']}</span>
                                </td>
                                <td style="text-align: center; padding: 8px 5px; font-weight: 700; color: #ff6b6b; font-size: 0.95rem;">{home_spread}</td>
                                <td style="text-align: center; padding: 8px 5px; font-weight: 700; color: #ff6b6b; font-size: 0.95rem;">{home_ml}</td>
                                <td style="text-align: center; padding: 8px 5px; font-weight: 600; color: #fff; font-size: 0.9rem;">U {total}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <!-- Betting Trends -->
                <div style="padding: 8px 20px; background: rgba(0,0,0,0.25);">
                    <div style="font-family: var(--font-primary); font-size: 0.7rem; color: #00f0ff; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 8px; font-weight: 600;">Records</div>
                    <div style="display: flex; justify-content: space-between; font-size: 0.8rem; color: #ccc;">
                        <div><span style="color: {data['away_accent']}; font-weight: 600;">{data['away_abbr']}:</span> {data['away_record']} SU</div>
                        <div><span style="color: {data['away_accent']}; font-weight: 600;">{data['home_abbr']}:</span> {data['home_record']} SU</div>
                    </div>
                </div>

                <!-- Injuries -->
                <div style="padding: 8px 20px; background: linear-gradient(135deg, rgba(255,215,0,0.1), rgba(239,97,0,0.1)); border-top: 1px solid rgba(255,215,0,0.3);">
                    <div style="font-family: var(--font-primary); font-size: 0.7rem; color: #ffd700; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 8px; font-weight: 600;">Injuries</div>
                    <div style="font-size: 0.8rem; color: #ddd; line-height: 1.5;">
                        <div style="margin-bottom: 4px;"><span style="color: {data['away_accent']}; font-weight: 600;">{data['away_abbr']}:</span> {data['away_injuries']}</div>
                        <div><span style="color: {data['away_accent']}; font-weight: 600;">{data['home_abbr']}:</span> {data['home_injuries']}</div>
                    </div>
                </div>

                <!-- Link to Featured Game Page - NEVER DELETE -->
                <a href="{page_filename}" style="display: block; padding: 12px 20px; background: linear-gradient(135deg, rgba(255, 215, 0, 0.2), rgba(239, 97, 0, 0.15)); text-align: center; text-decoration: none; border-top: 1px solid rgba(255, 215, 0, 0.3); transition: all 0.3s ease;">
                    <span style="font-family: var(--font-primary); font-size: 0.9rem; color: #FFD700; font-weight: 700; text-transform: uppercase; letter-spacing: 1px;">
                        View Full Breakdown →
                    </span>
                </a>

                <!-- Subscribe to Premium Button - NEVER DELETE -->
                <div style="padding: 12px 20px; background: linear-gradient(135deg, rgba(57, 255, 20, 0.15), rgba(0, 240, 255, 0.1)); border-top: 1px solid rgba(57, 255, 20, 0.3);">
                    <a href="premium.html" style="display: block; text-align: center; background: linear-gradient(135deg, #39FF14, #00f0ff); color: #000; font-family: var(--font-primary); font-size: 0.85rem; font-weight: 700; padding: 12px 20px; border-radius: 8px; text-decoration: none; text-transform: uppercase; letter-spacing: 1px; box-shadow: 0 0 20px rgba(57, 255, 20, 0.4); transition: all 0.3s ease;">
                        🔥 Subscribe to Premium Picks
                    </a>
                </div>

                <!-- Affiliate Banner - Moved here per user request Jan 30, 2026 -->
                <div class="affiliate-banner" style="padding: 20px; background: linear-gradient(135deg, rgba(0, 10, 30, 0.8), rgba(0, 30, 60, 0.8)); border-top: 2px solid rgba(0, 240, 255, 0.8); display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px;">
                    <div>
                        <h2 style="font-family: var(--font-primary); font-size: 1.1rem; color: var(--neon-gold); margin: 0 0 5px 0; text-transform: uppercase; letter-spacing: 1px;">Join YouWager — 350% Bonus!</h2>
                        <p style="font-size: 0.85rem; color: #ccc; margin: 0;">Trusted sportsbook with fast payouts • Our recommended book</p>
                    </div>
                    <a href="https://record.revmasters.com/_I-xl5bHAf88RxlNGag_0XWNd7ZgqdRLk/111/" target="_blank" rel="noopener" style="font-family: var(--font-primary); font-size: 0.85rem; font-weight: 700; color: #000; background: var(--neon-gold); padding: 12px 25px; border-radius: 8px; text-decoration: none; text-transform: uppercase; letter-spacing: 1px; box-shadow: 0 0 15px rgba(255, 215, 0, 0.4); transition: all 0.3s ease;">Claim Your Bonus</a>
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
    print(f"  Away Injuries: {data['away_injuries']}")
    print(f"  Home Injuries: {data['home_injuries']}")
    print(f"  Colors: {data['away_color']} -> {data['home_color']} (accent: {data['away_accent']})")

    # Generate new preview HTML
    new_preview = generate_preview_html(data, page_filename)

    # Replace in index.html - updated pattern to capture through affiliate banner
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

    # SAFETY CHECK: Verify required elements are present after write
    required_elements = [
        ('Subscribe to Premium', 'Subscribe button'),
        ('View Full Breakdown', 'Full breakdown link'),
        ('featured-game-of-the-day-page', 'Featured game page link'),
        ('Join YouWager', 'Affiliate banner'),
    ]

    missing = []
    for pattern, name in required_elements:
        if pattern not in updated_content:
            missing.append(name)

    if missing:
        print(f"\n  ERROR: Required elements missing after sync!")
        for m in missing:
            print(f"    [MISSING] {m}")
        print(f"\n  This is a bug in the sync script. Please report.")
        return False

    print(f"\n  SUCCESS: index.html preview updated to match {page_filename}")
    print(f"  ✓ Subscribe button present")
    print(f"  ✓ Full breakdown link present")
    print(f"  ✓ Affiliate banner present")
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

    # Extract team abbrs from the betting lines table (look for team abbreviation spans)
    lines_abbrs = re.findall(r'<span[^>]*font-weight: 600[^>]*>\s*(\w{2,4})\s*</span>', section)
    if len(lines_abbrs) >= 2:
        lines_away = lines_abbrs[0].upper()
        lines_home = lines_abbrs[1].upper()
    else:
        # Fallback: just use header logos
        lines_away = header_away
        lines_home = header_home

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
