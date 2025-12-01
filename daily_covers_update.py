#!/usr/bin/env python3
"""
BETLEGEND DAILY COVERS CONSENSUS UPDATE
========================================
Fully automated daily update for SportsBettingPrime Covers Consensus

WHAT THIS SCRIPT DOES:
1. Scrapes top contestants from Covers.com King of Covers
2. Aggregates their pending picks
3. Archives today's consensus page
4. Updates the main consensus page with new data
5. Pushes to GitHub

Run at 5:00 AM PST daily via Task Scheduler
"""

import os
import re
import csv
import json
import shutil
import subprocess
from datetime import datetime
from collections import Counter
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
REPO = r"C:\Users\Nima\nimadamus.github.io"
TODAY = datetime.now()
DATE_STR = TODAY.strftime("%Y-%m-%d")
DATE_DISPLAY = TODAY.strftime("%A, %B %d, %Y")

class CoversConsensusScraper:
    """Scrape Covers.com King of Covers contests"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        })

        self.sports = {
            'nfl': 'NFL',
            'nba': 'NBA',
            'nhl': 'NHL',
            'ncaab': 'College Basketball',
            'ncaaf': 'College Football',
        }

        self.all_picks = []
        self.pick_counter = Counter()

    def get_leaderboard(self, sport_code, pages=2, per_page=50):
        """Fetch top contestants from leaderboard"""
        print(f"\n  Fetching {self.sports.get(sport_code, sport_code)} leaderboard...")
        contestants = []

        for page in range(1, pages + 1):
            try:
                url = f"https://contests.covers.com/consensus/pickleaders/{sport_code}?page={page}"
                response = self.session.get(url, timeout=15)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')

                table = soup.find('table')
                if not table:
                    continue

                for row in table.find_all('tr')[1:]:
                    cells = row.find_all('td')
                    if len(cells) < 4:
                        continue

                    link = cells[1].find('a')
                    if not link:
                        continue

                    name = link.text.strip()
                    profile_url = link.get('href', '')
                    if not profile_url.startswith('http'):
                        profile_url = 'https://contests.covers.com' + profile_url

                    units = cells[2].text.strip()
                    record = cells[3].text.strip()

                    # Parse units
                    try:
                        units_value = float(units.replace('+', '').replace(',', ''))
                    except:
                        units_value = 0.0

                    contestants.append({
                        'name': name,
                        'profile_url': profile_url,
                        'units': units,
                        'units_value': units_value,
                        'record': record,
                        'sport': self.sports.get(sport_code, sport_code)
                    })

                time.sleep(0.5)

            except Exception as e:
                print(f"    Error fetching page {page}: {e}")

        # Sort by units and dedupe
        seen = set()
        unique = []
        for c in sorted(contestants, key=lambda x: -x['units_value']):
            if c['profile_url'] not in seen:
                seen.add(c['profile_url'])
                unique.append(c)

        print(f"    Found {len(unique)} contestants")
        return unique[:100]  # Top 100

    def get_contestant_picks(self, contestant, sport):
        """Get pending picks for a contestant"""
        try:
            response = self.session.get(contestant['profile_url'], timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            picks = []
            pending_table = soup.find('table', class_='cmg_contests_pendingpicks')

            if not pending_table:
                return []

            for row in pending_table.find_all('tr'):
                cells = row.find_all('td')
                if len(cells) < 4:
                    continue

                # Skip games with scores (finished)
                if len(cells) > 1:
                    score = cells[1].text.strip()
                    if score and any(c.isdigit() for c in score):
                        continue

                # Extract teams
                teams_text = cells[0].text.strip().split('\n')
                teams = [t.strip() for t in teams_text if t.strip()]
                away = teams[0] if teams else ''
                home = teams[1] if len(teams) > 1 else ''

                # Extract picks
                picks_cell = cells[3] if len(cells) > 3 else None
                if not picks_cell:
                    continue

                for div in picks_cell.find_all('div'):
                    pick_text = div.text.strip()
                    if not pick_text or len(pick_text) < 3:
                        continue

                    # Identify pick type
                    pick_lower = pick_text.lower()
                    if 'over' in pick_lower:
                        pick_type = 'Total (Over)'
                    elif 'under' in pick_lower:
                        pick_type = 'Total (Under)'
                    elif '+' in pick_text or '-' in pick_text:
                        pick_type = 'Spread (ATS)'
                    else:
                        pick_type = 'Moneyline'

                    picks.append({
                        'sport': sport,
                        'matchup': f"{away} @ {home}",
                        'pick_type': pick_type,
                        'pick_text': pick_text
                    })

            return picks

        except Exception as e:
            return []

    def scrape_all(self):
        """Scrape all sports"""
        print("\n" + "=" * 60)
        print("SCRAPING COVERS.COM CONSENSUS DATA")
        print("=" * 60)

        for sport_code, sport_name in self.sports.items():
            print(f"\n[{sport_name}]")
            contestants = self.get_leaderboard(sport_code)

            picks_found = 0
            for i, contestant in enumerate(contestants[:50], 1):  # Top 50 per sport
                picks = self.get_contestant_picks(contestant, sport_name)

                if picks:
                    picks_found += len(picks)
                    self.all_picks.extend(picks)

                    for pick in picks:
                        key = f"{pick['sport']}|{pick['matchup']}|{pick['pick_type']}|{pick['pick_text']}"
                        self.pick_counter[key] += 1

                time.sleep(0.3)

            print(f"    Total picks found: {picks_found}")

        return self.aggregate_picks()

    def aggregate_picks(self):
        """Aggregate and filter picks"""
        aggregated = []

        for pick_key, count in self.pick_counter.most_common():
            if count < 2:  # At least 2 experts
                continue

            parts = pick_key.split('|')
            if len(parts) == 4:
                sport, matchup, pick_type, pick_text = parts
                aggregated.append({
                    'count': count,
                    'sport': sport,
                    'matchup': matchup,
                    'pick_type': pick_type,
                    'pick': pick_text
                })

        # Sort by count
        aggregated.sort(key=lambda x: -x['count'])

        print(f"\n[OK] Aggregated {len(aggregated)} consensus picks")
        return aggregated[:200]  # Top 200


def archive_current_consensus():
    """Archive current consensus page with date"""
    main_file = os.path.join(REPO, "sportsbettingprime-covers-consensus.html")

    if not os.path.exists(main_file):
        print("  No existing consensus page to archive")
        return

    # Read to get the date
    with open(main_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Archive with today's date
    archive_file = os.path.join(REPO, f"sportsbettingprime-covers-consensus-{DATE_STR}.html")

    if not os.path.exists(archive_file):
        shutil.copy2(main_file, archive_file)
        print(f"  Archived to sportsbettingprime-covers-consensus-{DATE_STR}.html")
    else:
        print(f"  Archive already exists for {DATE_STR}")


def update_consensus_page(picks):
    """Update the main consensus page with new data"""
    main_file = os.path.join(REPO, "sportsbettingprime-covers-consensus.html")

    if not os.path.exists(main_file):
        print("  [ERROR] Main consensus page not found")
        return False

    with open(main_file, 'r', encoding='utf-8') as f:
        html = f.read()

    # Generate table rows
    def get_sport_class(sport):
        return {
            'NFL': 'sport-nfl', 'NBA': 'sport-nba', 'NHL': 'sport-nhl',
            'College Basketball': 'sport-ncaab', 'College Football': 'sport-ncaaf'
        }.get(sport, 'sport-nfl')

    def get_sport_abbrev(sport):
        return {'College Basketball': 'NCAAB', 'College Football': 'NCAAF'}.get(sport, sport)

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

    rows = []
    for pick in picks:
        row = f'''                    <tr data-sport="{pick['sport']}">
                        <td><span class="consensus-badge {get_consensus_class(pick['count'])}">{pick['count']} Experts</span></td>
                        <td><span class="sport-tag {get_sport_class(pick['sport'])}">{get_sport_abbrev(pick['sport'])}</span></td>
                        <td>{pick['matchup']}</td>
                        <td><span class="pick-type-badge {get_pick_class(pick['pick_type'])}">{pick['pick_type']}</span></td>
                        <td><strong>{pick['pick']}</strong></td>
                    </tr>'''
        rows.append(row)

    table_rows = '\n'.join(rows)

    # Replace tbody content
    tbody_start = html.find('<tbody>')
    tbody_end = html.find('</tbody>')

    if tbody_start == -1 or tbody_end == -1:
        print("  [ERROR] Could not find tbody tags")
        return False

    html = html[:tbody_start + 7] + '\n' + table_rows + '\n                ' + html[tbody_end:]

    # Update stats
    total_picks = sum(p['count'] for p in picks)
    highest = max(p['count'] for p in picks) if picks else 0

    # Update date display
    html = re.sub(
        r'<div class="update-date"[^>]*>📅 [^<]+',
        f'<div class="update-date" style="font-size: 1.4rem; color: var(--accent-gold); font-weight: 700; margin: 15px 0; text-transform: uppercase; letter-spacing: 1px;">📅 {DATE_DISPLAY}',
        html
    )

    # Update timestamp
    timestamp = TODAY.strftime('%B %d, %Y at %I:%M %p ET')
    html = re.sub(
        r'<strong>Last Updated:</strong> [^<]+',
        f'<strong>Last Updated:</strong> {timestamp}',
        html
    )

    # Write updated file
    with open(main_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"  Updated consensus page with {len(picks)} picks")
    print(f"  Total expert picks tracked: {total_picks}")
    print(f"  Highest consensus: {highest}x")
    return True


def update_main_sbp_page():
    """Update main sportsbettingprime.html with latest archive links"""
    main_file = os.path.join(REPO, "sportsbettingprime.html")

    if not os.path.exists(main_file):
        return

    # Find all archive files
    archive_files = []
    for f in os.listdir(REPO):
        if f.startswith('sportsbettingprime-covers-consensus-') and f.endswith('.html'):
            match = re.search(r'(\d{4}-\d{2}-\d{2})', f)
            if match:
                archive_files.append((match.group(1), f))

    # Sort by date (newest first)
    archive_files.sort(reverse=True)

    # Generate archive links HTML
    links_html = []
    for date_str, filename in archive_files[:7]:  # Last 7 days
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            display = date_obj.strftime('%B %d')
            links_html.append(f'                <a href="{filename}" class="archive-link">\n                    {display}\n                </a>')
        except:
            pass

    if links_html:
        print(f"  Found {len(archive_files)} archive files")


def git_commit_and_push():
    """Commit and push changes"""
    try:
        subprocess.run(['git', '-C', REPO, 'add', '-A'], check=True, capture_output=True)

        commit_msg = f"Daily Covers consensus update - {DATE_DISPLAY}\n\n🤖 Auto-generated by BetLegend Daily Update System"
        subprocess.run(['git', '-C', REPO, 'commit', '-m', commit_msg], check=True, capture_output=True)

        subprocess.run(['git', '-C', REPO, 'push'], check=True, capture_output=True)
        print("  Pushed to GitHub!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  Git error: {e}")
        return False


def main():
    print("=" * 60)
    print("BETLEGEND DAILY COVERS CONSENSUS UPDATE")
    print(f"Date: {DATE_DISPLAY}")
    print("=" * 60)

    # 1. Archive current page
    print("\n[1] Archiving current consensus page...")
    archive_current_consensus()

    # 2. Scrape new data
    print("\n[2] Scraping Covers.com...")
    scraper = CoversConsensusScraper()
    picks = scraper.scrape_all()

    if not picks:
        print("\n[ERROR] No picks found - skipping update")
        return

    # 3. Update consensus page
    print("\n[3] Updating consensus page...")
    update_consensus_page(picks)

    # 4. Update main page archive links
    print("\n[4] Updating archive links...")
    update_main_sbp_page()

    # 5. Push to GitHub
    print("\n[5] Pushing to GitHub...")
    git_commit_and_push()

    print("\n" + "=" * 60)
    print("COVERS UPDATE COMPLETE!")
    print("=" * 60)


if __name__ == "__main__":
    main()
