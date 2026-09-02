#!/usr/bin/env python3
"""
COVERS CONSENSUS SCRAPER v3.1 - Date-Filtered + Sport-Specific
================================================================
Scrapes the first 50 entries per sport from Covers.com leaderboards.
Only includes picks for TODAY's games using date headers on profile pages.
Uses sport-specific pending picks URLs to avoid cross-sport contamination.

For each active sport:
1. Fetch King of Covers leaderboard pages
2. For each contestant, fetch their sport-specific pending picks page
3. Only extract picks under TODAY's date heading
4. Collect first 50 contestants who have today's picks
5. Group picks by game, count expert consensus
6. Generate HTML

Run at 5:00 AM PST daily via Task Scheduler.
"""

import os
import re
import shutil
import subprocess
from datetime import datetime
from collections import Counter, defaultdict
import time

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("Installing required packages...")
    os.system('pip install requests beautifulsoup4 lxml')
    import requests
    from bs4 import BeautifulSoup

# Configuration
REPO = r"C:\Users\Nima\sportsbettingprime"
TODAY = datetime.now()
DATE_STR = TODAY.strftime("%Y-%m-%d")
DATE_DISPLAY = TODAY.strftime("%A, %B %d, %Y")
# For matching Covers date headers like "Friday, February 27"
TODAY_MONTH_DAY = f"{TODAY.strftime('%B')} {TODAY.day}"  # "February 27" (no leading zero)

# Season config - which sports are active
SPORTS_CONFIG = {
    'nba': {'name': 'NBA', 'active_months': list(range(1, 7)) + list(range(10, 13)),
            'leaderboard': 'nba', 'pages': 10},
    'nhl': {'name': 'NHL', 'active_months': list(range(1, 7)) + list(range(10, 13)),
            'leaderboard': 'nhl', 'pages': 10},
    'nfl': {'name': 'NFL', 'active_months': [1, 2, 9, 10, 11, 12],
            'leaderboard': 'nfl', 'pages': 10},
    'ncaab': {'name': 'NCAAB', 'active_months': list(range(1, 4)) + list(range(11, 13)),
              'leaderboard': 'ncaab', 'pages': 10},
    'ncaaf': {'name': 'NCAAF', 'active_months': [1, 8, 9, 10, 11, 12],
              'leaderboard': 'ncaaf', 'pages': 10},
    'mlb': {'name': 'MLB', 'active_months': list(range(2, 11)),
            'leaderboard': 'mlb', 'pages': 10},
}

# Full team name lookup: (lowercase_key, SPORT) -> Full Name
# Includes shortcodes AND city names for robust resolution
TEAM_FULL_NAMES = {
    # ======================== NBA ========================
    # Shortcodes
    ('atl', 'NBA'): 'Atlanta Hawks', ('bos', 'NBA'): 'Boston Celtics', ('bk', 'NBA'): 'Brooklyn Nets',
    ('cha', 'NBA'): 'Charlotte Hornets', ('chi', 'NBA'): 'Chicago Bulls', ('cle', 'NBA'): 'Cleveland Cavaliers',
    ('dal', 'NBA'): 'Dallas Mavericks', ('den', 'NBA'): 'Denver Nuggets', ('det', 'NBA'): 'Detroit Pistons',
    ('gs', 'NBA'): 'Golden State Warriors', ('hou', 'NBA'): 'Houston Rockets', ('ind', 'NBA'): 'Indiana Pacers',
    ('lac', 'NBA'): 'LA Clippers', ('lal', 'NBA'): 'LA Lakers', ('mem', 'NBA'): 'Memphis Grizzlies',
    ('mia', 'NBA'): 'Miami Heat', ('mil', 'NBA'): 'Milwaukee Bucks', ('min', 'NBA'): 'Minnesota Timberwolves',
    ('no', 'NBA'): 'New Orleans Pelicans', ('ny', 'NBA'): 'New York Knicks', ('okc', 'NBA'): 'Oklahoma City Thunder',
    ('orl', 'NBA'): 'Orlando Magic', ('phi', 'NBA'): 'Philadelphia 76ers', ('pho', 'NBA'): 'Phoenix Suns',
    ('por', 'NBA'): 'Portland Trail Blazers', ('sac', 'NBA'): 'Sacramento Kings', ('sa', 'NBA'): 'San Antonio Spurs',
    ('tor', 'NBA'): 'Toronto Raptors', ('uta', 'NBA'): 'Utah Jazz', ('utah', 'NBA'): 'Utah Jazz',
    ('was', 'NBA'): 'Washington Wizards',
    # City names (as Covers displays them)
    ('atlanta', 'NBA'): 'Atlanta Hawks', ('boston', 'NBA'): 'Boston Celtics', ('brooklyn', 'NBA'): 'Brooklyn Nets',
    ('charlotte', 'NBA'): 'Charlotte Hornets', ('chicago', 'NBA'): 'Chicago Bulls',
    ('cleveland', 'NBA'): 'Cleveland Cavaliers', ('dallas', 'NBA'): 'Dallas Mavericks',
    ('denver', 'NBA'): 'Denver Nuggets', ('detroit', 'NBA'): 'Detroit Pistons',
    ('golden state', 'NBA'): 'Golden State Warriors', ('houston', 'NBA'): 'Houston Rockets',
    ('indiana', 'NBA'): 'Indiana Pacers', ('memphis', 'NBA'): 'Memphis Grizzlies',
    ('miami', 'NBA'): 'Miami Heat', ('milwaukee', 'NBA'): 'Milwaukee Bucks',
    ('minnesota', 'NBA'): 'Minnesota Timberwolves', ('new orleans', 'NBA'): 'New Orleans Pelicans',
    ('new york', 'NBA'): 'New York Knicks', ('oklahoma city', 'NBA'): 'Oklahoma City Thunder',
    ('orlando', 'NBA'): 'Orlando Magic', ('philadelphia', 'NBA'): 'Philadelphia 76ers',
    ('phoenix', 'NBA'): 'Phoenix Suns', ('portland', 'NBA'): 'Portland Trail Blazers',
    ('sacramento', 'NBA'): 'Sacramento Kings', ('san antonio', 'NBA'): 'San Antonio Spurs',
    ('toronto', 'NBA'): 'Toronto Raptors', ('washington', 'NBA'): 'Washington Wizards',

    # ======================== NHL ========================
    # Shortcodes
    ('ana', 'NHL'): 'Anaheim Ducks', ('bos', 'NHL'): 'Boston Bruins', ('buf', 'NHL'): 'Buffalo Sabres',
    ('cgy', 'NHL'): 'Calgary Flames', ('car', 'NHL'): 'Carolina Hurricanes', ('chi', 'NHL'): 'Chicago Blackhawks',
    ('col', 'NHL'): 'Colorado Avalanche', ('cbj', 'NHL'): 'Columbus Blue Jackets', ('dal', 'NHL'): 'Dallas Stars',
    ('det', 'NHL'): 'Detroit Red Wings', ('edm', 'NHL'): 'Edmonton Oilers', ('fla', 'NHL'): 'Florida Panthers',
    ('la', 'NHL'): 'Los Angeles Kings', ('min', 'NHL'): 'Minnesota Wild', ('mtl', 'NHL'): 'Montreal Canadiens',
    ('nsh', 'NHL'): 'Nashville Predators', ('nj', 'NHL'): 'New Jersey Devils', ('nyi', 'NHL'): 'New York Islanders',
    ('nyr', 'NHL'): 'New York Rangers', ('ott', 'NHL'): 'Ottawa Senators', ('phi', 'NHL'): 'Philadelphia Flyers',
    ('pit', 'NHL'): 'Pittsburgh Penguins', ('sj', 'NHL'): 'San Jose Sharks', ('sea', 'NHL'): 'Seattle Kraken',
    ('stl', 'NHL'): 'St. Louis Blues', ('tb', 'NHL'): 'Tampa Bay Lightning', ('tor', 'NHL'): 'Toronto Maple Leafs',
    ('uta', 'NHL'): 'Utah Hockey Club', ('utah', 'NHL'): 'Utah Hockey Club',
    ('van', 'NHL'): 'Vancouver Canucks',
    ('vgk', 'NHL'): 'Vegas Golden Knights', ('veg', 'NHL'): 'Vegas Golden Knights',
    ('was', 'NHL'): 'Washington Capitals',
    ('wpg', 'NHL'): 'Winnipeg Jets', ('win', 'NHL'): 'Winnipeg Jets',
    # City names
    ('anaheim', 'NHL'): 'Anaheim Ducks', ('boston', 'NHL'): 'Boston Bruins', ('buffalo', 'NHL'): 'Buffalo Sabres',
    ('calgary', 'NHL'): 'Calgary Flames', ('carolina', 'NHL'): 'Carolina Hurricanes',
    ('chicago', 'NHL'): 'Chicago Blackhawks', ('colorado', 'NHL'): 'Colorado Avalanche',
    ('columbus', 'NHL'): 'Columbus Blue Jackets', ('dallas', 'NHL'): 'Dallas Stars',
    ('detroit', 'NHL'): 'Detroit Red Wings', ('edmonton', 'NHL'): 'Edmonton Oilers',
    ('florida', 'NHL'): 'Florida Panthers', ('los angeles', 'NHL'): 'Los Angeles Kings',
    ('minnesota', 'NHL'): 'Minnesota Wild', ('montreal', 'NHL'): 'Montreal Canadiens',
    ('nashville', 'NHL'): 'Nashville Predators', ('new jersey', 'NHL'): 'New Jersey Devils',
    ('ottawa', 'NHL'): 'Ottawa Senators', ('philadelphia', 'NHL'): 'Philadelphia Flyers',
    ('pittsburgh', 'NHL'): 'Pittsburgh Penguins', ('san jose', 'NHL'): 'San Jose Sharks',
    ('seattle', 'NHL'): 'Seattle Kraken', ('st. louis', 'NHL'): 'St. Louis Blues',
    ('tampa bay', 'NHL'): 'Tampa Bay Lightning', ('toronto', 'NHL'): 'Toronto Maple Leafs',
    ('vancouver', 'NHL'): 'Vancouver Canucks', ('vegas', 'NHL'): 'Vegas Golden Knights',
    ('washington', 'NHL'): 'Washington Capitals', ('winnipeg', 'NHL'): 'Winnipeg Jets',

    # ======================== NFL ========================
    # Shortcodes
    ('ari', 'NFL'): 'Arizona Cardinals', ('atl', 'NFL'): 'Atlanta Falcons', ('bal', 'NFL'): 'Baltimore Ravens',
    ('buf', 'NFL'): 'Buffalo Bills', ('car', 'NFL'): 'Carolina Panthers', ('chi', 'NFL'): 'Chicago Bears',
    ('cin', 'NFL'): 'Cincinnati Bengals', ('cle', 'NFL'): 'Cleveland Browns', ('dal', 'NFL'): 'Dallas Cowboys',
    ('den', 'NFL'): 'Denver Broncos', ('det', 'NFL'): 'Detroit Lions', ('gb', 'NFL'): 'Green Bay Packers',
    ('hou', 'NFL'): 'Houston Texans', ('ind', 'NFL'): 'Indianapolis Colts', ('jax', 'NFL'): 'Jacksonville Jaguars',
    ('kc', 'NFL'): 'Kansas City Chiefs', ('lv', 'NFL'): 'Las Vegas Raiders', ('lac', 'NFL'): 'LA Chargers',
    ('lar', 'NFL'): 'LA Rams', ('mia', 'NFL'): 'Miami Dolphins', ('min', 'NFL'): 'Minnesota Vikings',
    ('ne', 'NFL'): 'New England Patriots', ('no', 'NFL'): 'New Orleans Saints', ('nyg', 'NFL'): 'New York Giants',
    ('nyj', 'NFL'): 'New York Jets', ('phi', 'NFL'): 'Philadelphia Eagles', ('pit', 'NFL'): 'Pittsburgh Steelers',
    ('sf', 'NFL'): 'San Francisco 49ers', ('sea', 'NFL'): 'Seattle Seahawks', ('tb', 'NFL'): 'Tampa Bay Buccaneers',
    ('ten', 'NFL'): 'Tennessee Titans', ('was', 'NFL'): 'Washington Commanders',
    # City names
    ('arizona', 'NFL'): 'Arizona Cardinals', ('atlanta', 'NFL'): 'Atlanta Falcons',
    ('baltimore', 'NFL'): 'Baltimore Ravens', ('buffalo', 'NFL'): 'Buffalo Bills',
    ('carolina', 'NFL'): 'Carolina Panthers', ('chicago', 'NFL'): 'Chicago Bears',
    ('cincinnati', 'NFL'): 'Cincinnati Bengals', ('cleveland', 'NFL'): 'Cleveland Browns',
    ('dallas', 'NFL'): 'Dallas Cowboys', ('denver', 'NFL'): 'Denver Broncos',
    ('detroit', 'NFL'): 'Detroit Lions', ('green bay', 'NFL'): 'Green Bay Packers',
    ('houston', 'NFL'): 'Houston Texans', ('indianapolis', 'NFL'): 'Indianapolis Colts',
    ('jacksonville', 'NFL'): 'Jacksonville Jaguars', ('kansas city', 'NFL'): 'Kansas City Chiefs',
    ('las vegas', 'NFL'): 'Las Vegas Raiders', ('miami', 'NFL'): 'Miami Dolphins',
    ('minnesota', 'NFL'): 'Minnesota Vikings', ('new england', 'NFL'): 'New England Patriots',
    ('new orleans', 'NFL'): 'New Orleans Saints', ('philadelphia', 'NFL'): 'Philadelphia Eagles',
    ('pittsburgh', 'NFL'): 'Pittsburgh Steelers', ('san francisco', 'NFL'): 'San Francisco 49ers',
    ('seattle', 'NFL'): 'Seattle Seahawks', ('tampa bay', 'NFL'): 'Tampa Bay Buccaneers',
    ('tennessee', 'NFL'): 'Tennessee Titans', ('washington', 'NFL'): 'Washington Commanders',

    # ======================== MLB ========================
    # Shortcodes
    ('ari', 'MLB'): 'Arizona Diamondbacks', ('az', 'MLB'): 'Arizona Diamondbacks',
    ('atl', 'MLB'): 'Atlanta Braves', ('bal', 'MLB'): 'Baltimore Orioles',
    ('bos', 'MLB'): 'Boston Red Sox', ('chc', 'MLB'): 'Chicago Cubs', ('chw', 'MLB'): 'Chicago White Sox',
    ('cin', 'MLB'): 'Cincinnati Reds', ('cle', 'MLB'): 'Cleveland Guardians', ('col', 'MLB'): 'Colorado Rockies',
    ('det', 'MLB'): 'Detroit Tigers', ('hou', 'MLB'): 'Houston Astros', ('kc', 'MLB'): 'Kansas City Royals',
    ('laa', 'MLB'): 'Los Angeles Angels', ('lad', 'MLB'): 'Los Angeles Dodgers', ('mia', 'MLB'): 'Miami Marlins',
    ('mil', 'MLB'): 'Milwaukee Brewers', ('min', 'MLB'): 'Minnesota Twins', ('nym', 'MLB'): 'New York Mets',
    ('nyy', 'MLB'): 'New York Yankees', ('oak', 'MLB'): 'Oakland Athletics', ('ath', 'MLB'): 'Oakland Athletics',
    ('phi', 'MLB'): 'Philadelphia Phillies',
    ('pit', 'MLB'): 'Pittsburgh Pirates', ('sd', 'MLB'): 'San Diego Padres', ('sf', 'MLB'): 'San Francisco Giants',
    ('sea', 'MLB'): 'Seattle Mariners', ('stl', 'MLB'): 'St. Louis Cardinals', ('tb', 'MLB'): 'Tampa Bay Rays',
    ('tex', 'MLB'): 'Texas Rangers', ('tor', 'MLB'): 'Toronto Blue Jays', ('was', 'MLB'): 'Washington Nationals',
    # City names
    ('arizona', 'MLB'): 'Arizona Diamondbacks', ('atlanta', 'MLB'): 'Atlanta Braves',
    ('baltimore', 'MLB'): 'Baltimore Orioles', ('boston', 'MLB'): 'Boston Red Sox',
    ('cincinnati', 'MLB'): 'Cincinnati Reds', ('cleveland', 'MLB'): 'Cleveland Guardians',
    ('colorado', 'MLB'): 'Colorado Rockies', ('detroit', 'MLB'): 'Detroit Tigers',
    ('houston', 'MLB'): 'Houston Astros', ('kansas city', 'MLB'): 'Kansas City Royals',
    ('miami', 'MLB'): 'Miami Marlins', ('milwaukee', 'MLB'): 'Milwaukee Brewers',
    ('minnesota', 'MLB'): 'Minnesota Twins', ('oakland', 'MLB'): 'Oakland Athletics',
    ('philadelphia', 'MLB'): 'Philadelphia Phillies', ('pittsburgh', 'MLB'): 'Pittsburgh Pirates',
    ('san diego', 'MLB'): 'San Diego Padres', ('san francisco', 'MLB'): 'San Francisco Giants',
    ('seattle', 'MLB'): 'Seattle Mariners', ('st. louis', 'MLB'): 'St. Louis Cardinals',
    ('tampa bay', 'MLB'): 'Tampa Bay Rays', ('texas', 'MLB'): 'Texas Rangers',
    ('toronto', 'MLB'): 'Toronto Blue Jays', ('washington', 'MLB'): 'Washington Nationals',
}


def resolve_team_name(raw_name, sport):
    """Resolve a raw team identifier to its full display name.
    Handles shortcodes (min, veg), city names (Minnesota, Vegas),
    nicknames (Wild, Knights), and full names (Minnesota Wild)."""
    cleaned = raw_name.lower().strip()

    # 1. Exact match (shortcode or city name) for this sport
    result = TEAM_FULL_NAMES.get((cleaned, sport))
    if result:
        return result

    # 2. Full name exact match (e.g., "Minnesota Wild" already correct)
    for (code, s), name in TEAM_FULL_NAMES.items():
        if s == sport and name.lower() == cleaned:
            return name

    # 3. City/market prefix match: "vegas" -> "Vegas Golden Knights"
    #    Only accept if exactly ONE team matches for this sport
    matches = []
    for (code, s), name in TEAM_FULL_NAMES.items():
        if s == sport and name.lower().startswith(cleaned + ' '):
            if name not in matches:
                matches.append(name)
    if len(matches) == 1:
        return matches[0]

    # 4. Nickname match: "celtics" -> "Boston Celtics"
    for (code, s), name in TEAM_FULL_NAMES.items():
        if s == sport:
            parts = name.lower().split()
            if cleaned == parts[-1]:
                return name
            if len(parts) >= 3 and cleaned == ' '.join(parts[-2:]):
                return name

    # 5. Any-sport shortcode match (fallback)
    for (code, s), name in TEAM_FULL_NAMES.items():
        if cleaned == code:
            return name

    # 6. Broad startswith (last resort before giving up)
    for (code, s), name in TEAM_FULL_NAMES.items():
        if s == sport and len(cleaned) > 2:
            if name.lower().startswith(cleaned):
                return name

    # 7. Return as-is (title-cased if all lowercase)
    return raw_name.title() if raw_name == raw_name.lower() else raw_name


class CoversExpertScraper:
    """Scrape Covers.com King of Covers leaderboards and contestant profiles."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        })

    def get_top_entries(self, sport_code, max_pages=10, target=50):
        """Get first 50 leaderboard contestants with today's pending picks.
        Walks leaderboard pages until we find `target` contestants with
        today's picks, or exhaust all pages."""
        entries = []
        seen_usernames = set()

        for page in range(1, max_pages + 1):
            url = f"https://contests.covers.com/consensus/pickleaders/{sport_code}?page={page}"
            print(f"      Page {page}: {url}")

            try:
                resp = self.session.get(url, timeout=15)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, 'html.parser')

                table = soup.find('table')
                if not table:
                    print(f"        No table found")
                    break

                rows = table.find_all('tr')[1:]  # Skip header
                if not rows:
                    break

                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) < 4:
                        continue

                    link = cells[1].find('a')
                    if not link:
                        continue

                    username = link.text.strip()
                    if username in seen_usernames:
                        continue
                    seen_usernames.add(username)

                    profile_url = link.get('href', '')
                    if not profile_url.startswith('http'):
                        profile_url = 'https://contests.covers.com' + profile_url

                    try:
                        units = float(cells[2].text.strip().replace('+', '').replace(',', ''))
                    except (ValueError, AttributeError):
                        units = 0.0

                    # Get today's pending picks for this sport
                    picks = self._get_pending_picks(username, profile_url, sport_code)
                    time.sleep(0.2)

                    if picks:
                        entries.append({
                            'name': username,
                            'units': units,
                            'picks': picks,
                        })
                        if len(entries) >= target:
                            print(f"        Reached {target} entries with today's picks")
                            return entries

                time.sleep(0.3)

            except Exception as e:
                print(f"        Error on page {page}: {e}")
                continue

        return entries

    def _get_pending_picks(self, username, profile_url, sport_code):
        """Get pending picks for a specific sport on today's date only.
        Uses the sport-specific pending picks URL, with fallback to profile."""

        # Try sport-specific pending picks URL first
        picks_url = f"https://contests.covers.com/kingofcovers/contestant/pendingpicks/{username}/{sport_code}"
        soup = self._fetch_page(picks_url)

        if not soup:
            # Fallback to profile URL
            soup = self._fetch_page(profile_url)

        if not soup:
            return []

        # Walk h3 date headings and tables in document order
        # Only extract picks from tables that follow TODAY's date heading
        picks = []
        current_date = None
        is_today = False

        for element in soup.find_all(['h3', 'table']):
            if element.name == 'h3':
                current_date = element.text.strip()
                # Match "February 27" within "Friday, February 27"
                is_today = TODAY_MONTH_DAY in current_date
            elif (element.name == 'table' and
                  'cmg_contests_pendingpicks' in (element.get('class') or [])):
                if is_today:
                    picks.extend(self._extract_table_picks(element))

        return picks

    def _fetch_page(self, url):
        """Fetch a URL and return BeautifulSoup, or None on failure."""
        try:
            resp = self.session.get(url, timeout=15)
            if resp.status_code == 200:
                return BeautifulSoup(resp.text, 'html.parser')
        except Exception:
            pass
        return None

    def _extract_table_picks(self, table):
        """Extract picks from a single pending picks table."""
        picks = []

        for row in table.find_all('tr'):
            cells = row.find_all('td')
            if len(cells) < 4:
                continue

            # Extract team names from cell 0 (Away <br> Home)
            team_parts = []
            for child in cells[0].children:
                if hasattr(child, 'name') and child.name == 'br':
                    continue
                text = child.strip() if isinstance(child, str) else child.text.strip()
                if text:
                    team_parts.append(text)

            away = team_parts[0] if len(team_parts) > 0 else ''
            home = team_parts[1] if len(team_parts) > 1 else ''

            if not away or not home:
                continue

            # Extract picks from cell 3 (data-market-id divs)
            picks_cell = cells[3]
            market_divs = picks_cell.find_all('div', attrs={'data-market-id': True})

            if not market_divs:
                # Fallback: get innermost divs
                for child_div in picks_cell.find_all('div', recursive=False):
                    inner = child_div.find('div')
                    market_divs.append(inner if inner else child_div)

            for div in market_divs:
                pick_text = div.text.strip()
                if not pick_text or len(pick_text) < 3:
                    continue

                # Classify pick type
                pick_lower = pick_text.lower()
                if 'over' in pick_lower:
                    pick_type = 'Total (Over)'
                elif 'under' in pick_lower:
                    pick_type = 'Total (Under)'
                elif re.search(r'[+-]\d', pick_text):
                    pick_type = 'Spread (ATS)'
                else:
                    pick_type = 'Moneyline'

                picks.append({
                    'away': away,
                    'home': home,
                    'pick_type': pick_type,
                    'pick_text': pick_text,
                })

        return picks


def scrape_all():
    """Main scraping orchestrator. For each active sport, gets first 50 entries."""
    print("\n" + "=" * 60)
    print("COVERS CONSENSUS SCRAPER v3.1")
    print(f"Date: {DATE_DISPLAY}")
    print(f"Filtering picks for: {TODAY_MONTH_DAY}")
    print("=" * 60)

    current_month = TODAY.month
    scraper = CoversExpertScraper()

    all_games = {}  # sport -> list of game dicts

    for sport_code, config in SPORTS_CONFIG.items():
        sport = config['name']

        if current_month not in config['active_months']:
            print(f"\n  [{sport}] Off-season, skipping")
            continue

        print(f"\n  [{sport}] Scraping first 50 entries with today's picks...")
        entries = scraper.get_top_entries(
            config['leaderboard'],
            max_pages=config['pages'],
            target=50
        )

        print(f"    Found {len(entries)} contestants with today's picks")

        if not entries:
            continue

        # Group picks by game (resolve team names for consistent keys)
        game_picks = defaultdict(list)  # matchup_key -> [pick dicts]

        for entry in entries:
            for pick in entry['picks']:
                away_full = resolve_team_name(pick['away'], sport)
                home_full = resolve_team_name(pick['home'], sport)
                matchup_key = f"{away_full} @ {home_full}"

                game_picks[matchup_key].append({
                    'pick_type': pick['pick_type'],
                    'pick_text': pick['pick_text'],
                })

        # Build game list with aggregated consensus counts
        games = []
        for matchup, picks in game_picks.items():
            pick_counter = Counter()
            for p in picks:
                key = f"{p['pick_type']}|{p['pick_text']}"
                pick_counter[key] += 1

            expert_picks = []
            for pick_key, count in pick_counter.most_common():
                parts = pick_key.split('|', 1)
                if len(parts) == 2:
                    expert_picks.append({
                        'pick_type': parts[0],
                        'pick_text': parts[1],
                        'count': count,
                    })

            games.append({
                'sport': sport,
                'matchup': matchup,
                'expert_picks': expert_picks,
                'total_picks': len(picks),
            })

        # Sort by total picks (most popular games first)
        games.sort(key=lambda g: -g['total_picks'])

        total_picks = sum(g['total_picks'] for g in games)
        print(f"    {len(games)} games, {total_picks} total picks")

        if games:
            all_games[sport] = games

    return all_games


def generate_game_cards_html(all_games):
    """Generate HTML game cards for all games."""

    def get_sport_class(sport):
        return {
            'NFL': 'sport-nfl', 'NBA': 'sport-nba', 'NHL': 'sport-nhl',
            'NCAAB': 'sport-ncaab', 'NCAAF': 'sport-ncaaf',
            'MLB': 'sport-mlb',
        }.get(sport, 'sport-nfl')

    def get_pick_class(pick_type):
        if 'Over' in pick_type:
            return 'pick-total-over'
        elif 'Under' in pick_type:
            return 'pick-total-under'
        elif 'Spread' in pick_type:
            return 'pick-spread'
        return 'pick-moneyline'

    def get_consensus_class(count):
        if count >= 10:
            return 'consensus-high'
        elif count >= 5:
            return 'consensus-medium'
        return 'consensus-low'

    cards = []
    sport_order = ['NFL', 'NBA', 'NHL', 'NCAAB', 'NCAAF', 'MLB']

    for sport in sport_order:
        if sport not in all_games:
            continue

        for game in all_games[sport]:
            sport_cls = get_sport_class(sport)

            top_count = max((p['count'] for p in game['expert_picks']), default=0)
            top_label = f"{top_count}x TOP" if top_count > 0 else ""

            picks_html = ''
            for pick in game['expert_picks'][:8]:  # Show top 8 picks per game
                cnt = pick['count']
                cls = get_consensus_class(cnt)
                ptype_cls = get_pick_class(pick['pick_type'])
                picks_html += f'''
                            <div class="pick-row">
                                <span class="consensus-badge {cls}">{cnt}x</span>
                                <span class="pick-type-badge {ptype_cls}">{pick['pick_type']}</span>
                                <span class="pick-value">{pick['pick_text']}</span>
                            </div>'''

            if not picks_html.strip():
                picks_html = '''
                            <div class="pick-row" style="opacity:0.5;">
                                <span class="consensus-badge consensus-low">--</span>
                                <span class="pick-type-badge pick-spread">Awaiting</span>
                                <span class="pick-value">No picks yet</span>
                            </div>'''

            card = f'''                <div class="game-card" data-sport="{sport}">
                    <div class="game-header">
                        <span class="sport-tag {sport_cls}">{sport}</span>
                        <span class="game-matchup">{game['matchup']}</span>
                        <span class="game-top-consensus">{top_label}</span>
                    </div>
                    <div class="game-picks">{picks_html}
                    </div>
                </div>'''
            cards.append(card)

    return '\n'.join(cards)


def update_consensus_page(all_games):
    """Update the main covers-consensus.html page with new data."""
    main_file = os.path.join(REPO, "covers-consensus.html")

    if not os.path.exists(main_file):
        print(f"  [ERROR] Main consensus page not found: {main_file}")
        return False

    with open(main_file, 'r', encoding='utf-8') as f:
        html = f.read()

    # Generate new game cards
    cards_html = generate_game_cards_html(all_games)

    # Calculate stats
    total_games = sum(len(g) for g in all_games.values())
    total_expert_picks = sum(
        sum(p['count'] for p in game['expert_picks'])
        for games in all_games.values()
        for game in games
    )
    sports_count = len(all_games)
    highest_consensus = max(
        (p['count'] for games in all_games.values()
         for game in games
         for p in game['expert_picks']),
        default=0
    )

    # Replace games container content
    container_start = html.find('<div class="games-container">')
    if container_start != -1:
        depth = 0
        i = container_start
        container_end = len(html)
        while i < len(html):
            if html[i:i + 4] == '<div':
                depth += 1
            elif html[i:i + 6] == '</div>':
                depth -= 1
                if depth == 0:
                    container_end = i + 6
                    break
            i += 1

        html = (html[:container_start] +
                '<div class="games-container">\n' + cards_html + '\n        </div>' +
                html[container_end:])

    # Update stats bar
    html = re.sub(
        r'(<div class="stat-value">)\d+(</div>\s*<div class="stat-label">Total Picks)',
        f'\\g<1>{total_expert_picks}\\2', html)
    html = re.sub(
        r'(<div class="stat-value">)\d+(</div>\s*<div class="stat-label">Games)',
        f'\\g<1>{total_games}\\2', html)
    html = re.sub(
        r'(<div class="stat-value">)\d+(</div>\s*<div class="stat-label">Sports)',
        f'\\g<1>{sports_count}\\2', html)
    html = re.sub(
        r'(<div class="stat-value">)\d+x(</div>\s*<div class="stat-label">Highest)',
        f'\\g<1>{highest_consensus}x\\2', html)

    # Update date display
    html = re.sub(
        r'<div class="update-date"[^>]*>[^<]*',
        f'<div class="update-date">{DATE_DISPLAY}', html)

    # Update timestamp
    timestamp = TODAY.strftime('%B %d, %Y at %I:%M %p ET')
    html = re.sub(
        r'<strong>Last Updated:</strong> [^<]+',
        f'<strong>Last Updated:</strong> {timestamp}', html)

    with open(main_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"  Updated consensus page:")
    print(f"    Games: {total_games}")
    print(f"    Expert picks: {total_expert_picks}")
    print(f"    Sports: {sports_count}")
    print(f"    Highest consensus: {highest_consensus}x")
    return True


def archive_current_consensus():
    """Archive current consensus page with today's date."""
    main_file = os.path.join(REPO, "covers-consensus.html")
    if not os.path.exists(main_file):
        print("  No existing consensus page to archive")
        return

    archive_file = os.path.join(REPO, f"covers-consensus-{DATE_STR}.html")
    if not os.path.exists(archive_file):
        shutil.copy2(main_file, archive_file)
        print(f"  Archived to covers-consensus-{DATE_STR}.html")
    else:
        print(f"  Archive already exists for {DATE_STR}")


def update_archive_data():
    """Update the ARCHIVE_DATA JavaScript array in the consensus page."""
    main_file = os.path.join(REPO, "covers-consensus.html")
    if not os.path.exists(main_file):
        return

    archive_dates = []
    for f in os.listdir(REPO):
        match = re.match(r'covers-consensus-(\d{4}-\d{2}-\d{2})\.html$', f)
        if match:
            archive_dates.append(match.group(1))

    archive_dates.sort()

    entries = []
    for d in archive_dates:
        entries.append(f'            {{ date: "{d}", page: "covers-consensus-{d}.html" }}')

    archive_data_js = ',\n'.join(entries)

    with open(main_file, 'r', encoding='utf-8') as f:
        html = f.read()

    pattern = r'const ARCHIVE_DATA = \[.*?\];'
    replacement = f'const ARCHIVE_DATA = [\n{archive_data_js}\n        ];'
    html = re.sub(pattern, replacement, html, flags=re.DOTALL)

    with open(main_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"  Updated ARCHIVE_DATA with {len(archive_dates)} dates")


def git_commit_and_push():
    """Commit and push consensus changes only."""
    try:
        # Only stage consensus files
        subprocess.run(['git', '-C', REPO, 'add',
                        'covers-consensus.html',
                        f'covers-consensus-{DATE_STR}.html'],
                       check=True, capture_output=True)

        commit_msg = (f"Covers consensus update - {DATE_DISPLAY}\n\n"
                      f"Auto-generated by Covers Consensus Scraper v3.1")
        subprocess.run(['git', '-C', REPO, 'commit', '-m', commit_msg],
                       check=True, capture_output=True)

        subprocess.run(['git', '-C', REPO, 'push'],
                       check=True, capture_output=True)
        print("  Pushed to GitHub!")
        return True
    except subprocess.CalledProcessError as e:
        stderr = e.stderr.decode() if e.stderr else ''
        if 'nothing to commit' in stderr:
            print("  Nothing to commit")
            return True
        print(f"  Git error: {stderr}")
        return False


def main():
    print("=" * 60)
    print("COVERS CONSENSUS SCRAPER v3.1 - Date-Filtered")
    print(f"Date: {DATE_DISPLAY}")
    print(f"Today filter: {TODAY_MONTH_DAY}")
    print("=" * 60)

    # 1. Archive current page
    print("\n[1] Archiving current consensus page...")
    archive_current_consensus()

    # 2. Scrape all data
    print("\n[2] Scraping Covers.com leaderboards...")
    all_games = scrape_all()

    if not all_games:
        print("\n[ERROR] No data scraped - aborting")
        return 1

    # 3. Update consensus page
    print("\n[3] Updating consensus page...")
    success = update_consensus_page(all_games)
    if not success:
        print("  [ERROR] Failed to update consensus page")
        return 1

    # 4. Update archive data
    print("\n[4] Updating archive calendar data...")
    update_archive_data()

    # 5. Push to GitHub
    print("\n[5] Pushing to GitHub...")
    git_commit_and_push()

    # Summary
    total_games = sum(len(g) for g in all_games.values())
    total_picks = sum(
        sum(p['count'] for p in game['expert_picks'])
        for games in all_games.values()
        for game in games
    )

    print("\n" + "=" * 60)
    print("COMPLETE!")
    print(f"  Games: {total_games}")
    print(f"  Expert picks tracked: {total_picks}")
    print(f"  Sports: {', '.join(all_games.keys())}")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    exit(main())
