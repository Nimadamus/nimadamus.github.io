#!/usr/bin/env python3
"""
rotate_hub_content.py - Archive current hub content before daily refresh.

Usage:
    python rotate_hub_content.py <sport>

Where sport is one of: nba, nhl, mlb, ncaab, soccer

This script:
1. Reads the current hub page for the given sport
2. Extracts content between DAILY CONTENT START/END markers
3. If content is just the placeholder, skips archiving
4. Appends the content to a monthly archive file (creating it if needed)
5. Clears the hub content area with the placeholder message

The archive files are noindexed and canonical-point to the main hub page.
"""

import os
import sys
import re
import json
from datetime import datetime

# Resolve paths relative to the script location (repo root)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)

# Sport -> hub filename mapping
SPORT_MAP = {
    'nba': 'nba-previews.html',
    'nhl': 'nhl-previews.html',
    'mlb': 'mlb-previews.html',
    'ncaab': 'college-basketball-previews.html',
    'soccer': 'soccer-previews.html',
}

# Sport -> display name
SPORT_DISPLAY = {
    'nba': 'NBA',
    'nhl': 'NHL',
    'mlb': 'MLB',
    'ncaab': 'College Basketball',
    'soccer': 'Soccer',
}

CONTENT_START_MARKER = '<!-- ========== DAILY CONTENT START ========== -->'
CONTENT_END_MARKER = '<!-- ========== DAILY CONTENT END ========== -->'

PLACEHOLDER_TEXT = "Today's previews will be published shortly"

PLACEHOLDER_HTML = f'''<div style="text-align:center;padding:60px 24px;color:var(--text-muted);">
<p style="font-size:18px;font-family:var(--font-display);letter-spacing:1.5px;text-transform:uppercase;">{PLACEHOLDER_TEXT}</p>
<p style="margin-top:12px;font-size:14px;">Check back soon for full game analysis, betting lines, and previews.</p>
</div>'''


def get_archive_filename(sport, date):
    """Generate the monthly archive filename for a sport and date."""
    month_name = date.strftime('%B').lower()
    year = date.strftime('%Y')
    base = SPORT_MAP[sport].replace('.html', '')
    return f'{base}-archive-{month_name}-{year}.html'


def build_archive_page(sport, date, hub_filename):
    """Create a new monthly archive HTML page."""
    display = SPORT_DISPLAY[sport]
    month_year = date.strftime('%B %Y')

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="robots" content="noindex, follow"/>
<link href="https://www.betlegendpicks.com/{hub_filename}" rel="canonical"/>
<title>{display} Previews Archive - {month_year} | BetLegend</title>
<meta name="description" content="Archive of {display} game previews and analysis from {month_year}. Daily betting analysis, spreads, moneylines, and totals."/>
<meta content="width=device-width, initial-scale=1" name="viewport"/>
<meta content="{display} Previews Archive - {month_year} | BetLegend" property="og:title"/>
<meta content="Archive of {display} game previews from {month_year}." property="og:description"/>
<meta content="website" property="og:type"/>
<meta content="https://www.betlegendpicks.com/{hub_filename}" property="og:url"/>
<meta content="BetLegend Picks" property="og:site_name"/>
<meta property="og:image" content="https://www.betlegendpicks.com/newlogo.png"/>
<meta content="summary_large_image" name="twitter:card"/>
<meta content="{display} Previews Archive - {month_year} | BetLegend" name="twitter:title"/>
<meta content="Archive of {display} game previews from {month_year}." name="twitter:description"/>
<meta name="twitter:image" content="https://www.betlegendpicks.com/newlogo.png"/>
<link href="https://www.betlegendpicks.com/newlogo.png" rel="icon"/>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&amp;family=Orbitron:wght@500;700;900&amp;family=Poppins:wght@400;500;600&amp;display=swap" rel="stylesheet"/>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
:root{{--bg-primary:#0a0c10;--bg-card:#12151c;--bg-card-hover:#181c25;--accent-orange:#fd5000;--accent-cyan:#00e5ff;--accent-gold:#ffd54f;--text-primary:#ffffff;--text-secondary:#b0b8c4;--text-muted:#6b7280;--border-subtle:rgba(255,255,255,0.08);--font-display:'Orbitron',sans-serif;--font-body:'Inter',system-ui,sans-serif}}
body{{background:var(--bg-primary);color:var(--text-primary);font-family:var(--font-body);line-height:1.8}}
.nav-container{{position:fixed;top:0;left:0;right:0;z-index:1000;background:rgba(10,12,16,0.95);backdrop-filter:blur(12px);border-bottom:1px solid var(--border-subtle)}}
.nav-inner{{max-width:1400px;margin:0 auto;display:flex;align-items:center;justify-content:center;gap:12px;padding:18px 5% 18px 280px}}
.logo{{position:fixed;top:15px;left:15px;z-index:1001}}
.logo a{{font-family:var(--font-display);font-size:2.2rem;font-weight:900;color:#fff;text-decoration:none;text-shadow:0 0 10px rgba(255,255,255,0.5)}}
.logo a span{{color:var(--accent-cyan);text-shadow:0 0 15px rgba(0,229,255,0.8)}}
.nav-links{{display:flex;align-items:center;gap:24px;flex-wrap:nowrap}}
.nav-links>a,.nav-links>.dropdown,.dropbtn{{font-family:var(--font-body);color:#fff;text-decoration:none;font-size:13px;font-weight:600;padding:12px 18px;white-space:nowrap;border-radius:8px;background:none;border:none;cursor:pointer;text-transform:uppercase;letter-spacing:1.5px;transition:all 0.2s;margin:0}}
.dropbtn::after{{content:'\\25BE';margin-left:5px;font-size:10px;opacity:0.7}}
.nav-links>a:hover,.dropbtn:hover{{color:var(--accent-gold)}}
.dropdown{{position:relative;padding:0;margin:0}}
.dropdown-content{{display:none;position:absolute;top:100%;left:0;background:rgba(10,12,16,0.98);min-width:180px;border:1px solid var(--border-subtle);border-radius:10px;padding:10px 0;margin-top:8px}}
.dropdown-content a{{color:var(--accent-cyan);padding:12px 18px;display:block;text-decoration:none;font-size:14px}}
.dropdown-content a:hover{{background:rgba(0,229,255,0.1);color:#fff}}
.dropdown:hover .dropdown-content{{display:block}}
.dropdown.active .dropdown-content{{display:block}}
.dropdown.active .dropbtn{{color:var(--accent-gold)}}
.hero{{padding:140px 24px 50px;text-align:center;background:linear-gradient(180deg,rgba(253,80,0,0.12) 0%,rgba(253,80,0,0.03) 50%,transparent 100%);position:relative;overflow:hidden}}
.hero::before{{content:'';position:absolute;top:0;left:0;right:0;bottom:0;background:url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23fd5000' fill-opacity='0.03'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");opacity:0.5}}
.hero h1{{font-family:var(--font-display);font-size:clamp(28px,4vw,44px);font-weight:700;margin-bottom:16px;color:#fff;position:relative;z-index:1;text-shadow:0 0 40px rgba(253,80,0,0.3)}}
.hero p{{color:var(--text-secondary);font-size:18px;max-width:750px;margin:0 auto;position:relative;z-index:1}}
.page-wrapper{{max-width:900px;margin:0 auto;padding:0 24px 80px}}
details{{background:rgba(0,8,20,0.75);border:1px solid rgba(0,180,200,0.12);border-radius:12px;margin-bottom:16px;overflow:hidden}}
summary{{padding:18px 24px;cursor:pointer;display:flex;justify-content:space-between;align-items:center;font-family:'Orbitron',sans-serif;font-size:1rem;font-weight:700;color:#fff;list-style:none}}
summary::-webkit-details-marker{{display:none}}
summary::after{{content:'\\25BC';font-size:0.7rem;color:var(--accent-cyan);transition:transform 0.3s}}
details[open] summary::after{{transform:rotate(180deg)}}
details[open] summary{{border-bottom:1px solid rgba(0,180,200,0.12)}}
details .game-content{{padding:20px 24px}}
details .game-content p{{color:var(--text-secondary);font-size:16px;line-height:1.9;margin-bottom:16px}}
details .game-content p:last-child{{margin-bottom:0}}
.game-odds{{display:flex;gap:20px;margin-top:4px;flex-wrap:wrap}}
.game-odds span{{font-family:'Poppins',sans-serif;font-size:0.82rem;color:rgba(255,255,255,0.5)}}
.game-meta-line{{font-size:0.8rem;color:rgba(0,200,220,0.7);margin-top:4px}}
.summary-left{{display:flex;flex-direction:column;gap:2px}}
.summary-teams{{font-size:1rem}}
.bet-pills{{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:16px}}
.bet-pill{{background:rgba(0,229,255,0.08);border:1px solid rgba(0,229,255,0.15);padding:8px 16px;border-radius:8px;text-align:center;min-width:110px}}
.bet-pill .pill-label{{font-size:10px;text-transform:uppercase;letter-spacing:1.5px;color:var(--text-muted);margin-bottom:4px}}
.bet-pill .pill-value{{font-family:var(--font-display);font-size:15px;font-weight:700;color:var(--accent-gold)}}
.internal-links{{margin-top:40px;padding:24px;background:var(--bg-card);border:1px solid var(--border-subtle);border-radius:12px;text-align:center}}
.internal-links h3{{font-family:var(--font-display);font-size:16px;color:var(--accent-orange);margin-bottom:16px;text-transform:uppercase;letter-spacing:1.5px}}
.internal-links a{{color:var(--accent-cyan);text-decoration:none;margin:0 12px;font-size:14px;font-weight:600}}
.internal-links a:hover{{color:#fff}}
.archive-day{{background:var(--bg-card);border:1px solid var(--border-subtle);border-radius:16px;padding:24px;margin-bottom:32px}}
.archive-date{{font-family:var(--font-display);font-size:18px;color:var(--accent-orange);margin-bottom:20px;padding-bottom:12px;border-bottom:2px solid rgba(253,80,0,0.3);text-transform:uppercase;letter-spacing:1.5px}}
.back-to-hub{{text-align:center;margin:32px 0;padding:16px;background:var(--bg-card);border:1px solid var(--border-subtle);border-radius:12px}}
.back-to-hub a{{color:var(--accent-cyan);text-decoration:none;font-size:16px;font-weight:600}}
.back-to-hub a:hover{{color:#fff}}
footer{{text-align:center;padding:50px 24px;color:var(--text-muted);font-size:13px;border-top:1px solid var(--border-subtle)}}
footer a{{color:var(--accent-cyan);text-decoration:none}}
@media(max-width:768px){{
.hero{{padding:130px 20px 40px}}
summary{{padding:14px 16px;font-size:0.88rem}}
details .game-content{{padding:16px}}
.game-odds{{gap:10px}}
.bet-pills{{gap:8px}}
.bet-pill{{min-width:90px;padding:6px 10px}}
.bet-pill .pill-value{{font-size:13px}}
.nav-inner{{padding:14px 10px 14px 70px}}
.logo a{{font-size:1.4rem}}
.nav-links{{gap:8px}}
.nav-links>a,.dropbtn{{font-size:11px;padding:8px 10px}}
.archive-day{{padding:16px}}
}}
</style>
<link rel="stylesheet" href="/mobile-optimize.css" media="screen">
</head>
<body>
<nav class="nav-container">
<div class="nav-inner">
<div class="logo"><a href="index.html">BET<span>LEGEND</span></a></div>
<div class="nav-links">
<a href="index.html">Home</a>
<div class="dropdown">
 <button class="dropbtn hub-btn">Handicapping Hub</button>
 <div class="dropdown-content">
 <a href="handicapping-hub.html">Today's Games</a>
 <a href="injury-report.html">Injury Report</a>
 </div>
 </div>
<a href="nba-college-basketball-picks-predictions-analysis-february-2026.html">Picks</a>
<div class="dropdown"><button class="dropbtn">Game Previews</button><div class="dropdown-content"><a href="nba-previews.html">NBA</a><a href="nhl-previews.html">NHL</a><a href="mlb-previews.html">MLB</a><a href="college-basketball-previews.html">NCAAB</a><a href="soccer-previews.html">Soccer</a><a href="nfl.html">NFL</a><a href="ncaaf.html">NCAAF</a></div></div>
<div class="dropdown"><button class="dropbtn">Records</button><div class="dropdown-content"><a href="records.html">Detailed Breakdown</a><a href="nfl-records.html">NFL</a><a href="nba-records.html">NBA</a><a href="nhl-records.html">NHL</a><a href="ncaaf-records.html">NCAAF</a><a href="ncaab-records.html">NCAAB</a><a href="mlb-records.html">MLB</a><a href="soccer-records.html">Soccer</a><a href="crosssport-parlays-records.html" title="Cross-Sport Bets">Cross-Sport Bets</a></div></div>
<div class="dropdown"><button class="dropbtn">Resources</button><div class="dropdown-content"><a href="proofofpicks.html">Proof of Picks</a><a href="live-odds.html">Live Odds</a><a href="howitworks.html">How It Works</a><a href="bankroll.html">Bankroll Management</a><a href="kelly-criterion.html">Kelly Criterion</a><a href="risk-of-ruin-calculator.html">Risk of Ruin</a><a href="bankroll-simulator.html">Bankroll Simulator</a><a href="betting-calculators.html">Calculators</a><a href="betting-glossary.html">Glossary</a><a href="betting-101.html">Betting 101</a><a href="how-to-bet-mlb-totals.html">How to Bet MLB Totals</a><a href="contact.html">Contact Us</a></div></div>
<a href="yasiel-puig-convicted-gambling-case-sports-news.html">News</a>
<a href="podcast.html">Podcast</a>
<div class="dropdown"><button class="dropbtn">Game of Day</button><div class="dropdown-content"><a href="kentucky-vs-santa-clara-analysis-stats-preview-march-20-2026.html">Featured Game</a><a href="moneyline-parlay-of-the-day.html">ML Parlay</a></div></div>
</div>
</div>
</nav>

<header class="hero">
<div class="hero-badge">Archive</div>
<h1>{display} Previews Archive - {month_year}</h1>
<p>Daily game previews and betting analysis from {month_year}. Browse past analysis by date.</p>
</header>

<div class="page-wrapper">

<div class="back-to-hub">
<a href="{hub_filename}">&larr; Back to Today's {display} Previews</a>
</div>

<!-- ========== ARCHIVE CONTENT START ========== -->
<!-- ========== ARCHIVE CONTENT END ========== -->

<div class="back-to-hub">
<a href="{hub_filename}">&larr; Back to Today's {display} Previews</a>
</div>

</div>

<footer>
<p>&copy; 2026 BetLegend Picks. All Rights Reserved.</p>
<p><a href="privacy.html">Privacy Policy</a> | <a href="terms.html">Terms of Service</a> | <a href="contact.html">Contact</a></p>
</footer>

<script>
document.querySelectorAll('.dropdown').forEach(d=>{{d.addEventListener('click',function(e){{if(window.innerWidth<=768){{e.stopPropagation();this.classList.toggle('active')}}}})}});
document.addEventListener('click',()=>document.querySelectorAll('.dropdown').forEach(d=>d.classList.remove('active')));
</script>
</body>
</html>'''


def extract_daily_content(html):
    """Extract content between DAILY CONTENT START and END markers."""
    start_idx = html.find(CONTENT_START_MARKER)
    end_idx = html.find(CONTENT_END_MARKER)

    if start_idx == -1 or end_idx == -1:
        return None, None, None

    content_start = start_idx + len(CONTENT_START_MARKER)
    content = html[content_start:end_idx].strip()

    return content, start_idx, end_idx + len(CONTENT_END_MARKER)


def is_placeholder_only(content):
    """Check if the extracted content is just the placeholder message."""
    if not content:
        return True
    stripped = re.sub(r'<[^>]+>', '', content).strip()
    if not stripped:
        return True
    if PLACEHOLDER_TEXT in stripped:
        # Check if there's substantial content beyond the placeholder
        without_placeholder = stripped.replace(PLACEHOLDER_TEXT, '').strip()
        # Allow for the secondary placeholder line
        without_secondary = without_placeholder.replace(
            'Check back soon for full game analysis, betting lines, and previews.', ''
        ).strip()
        if not without_secondary:
            return True
    return False


def append_to_archive(archive_path, content, date, sport):
    """Append today's content to the archive file, creating it if needed."""
    hub_filename = SPORT_MAP[sport]
    date_str = date.strftime('%Y-%m-%d')
    full_date = date.strftime('%A, %B %d, %Y')

    archive_entry = f'''
<div class="archive-day" id="{date_str}">
<h2 class="archive-date">{full_date}</h2>
{content}
</div>
'''

    if not os.path.exists(archive_path):
        # Create the archive file
        archive_html = build_archive_page(sport, date, hub_filename)
        with open(archive_path, 'w', encoding='utf-8') as f:
            f.write(archive_html)
        print(f'  Created new archive file: {os.path.basename(archive_path)}')

    # Read existing archive
    with open(archive_path, 'r', encoding='utf-8') as f:
        archive_html = f.read()

    # Check if this date already exists in the archive
    if f'id="{date_str}"' in archive_html:
        print(f'  WARNING: Content for {date_str} already exists in archive. Skipping to avoid duplicates.')
        return False

    # Insert before the ARCHIVE CONTENT END marker
    archive_end_marker = '<!-- ========== ARCHIVE CONTENT END ========== -->'
    if archive_end_marker in archive_html:
        archive_html = archive_html.replace(
            archive_end_marker,
            archive_entry + '\n' + archive_end_marker
        )
    else:
        # Fallback: insert before the second back-to-hub div
        # Find the closing </div> of page-wrapper area
        print('  WARNING: Archive end marker not found. Cannot append content safely.')
        return False

    with open(archive_path, 'w', encoding='utf-8') as f:
        f.write(archive_html)

    return True


MANIFEST_PATH = os.path.join(SCRIPT_DIR, 'hub-archive-manifest.json')


def update_manifest(sport, date_str):
    """Record this archived date in the JSON manifest so sync_calendars.py can find it."""
    try:
        if os.path.exists(MANIFEST_PATH):
            with open(MANIFEST_PATH, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
        else:
            manifest = {}

        if sport not in manifest:
            manifest[sport] = []

        if date_str not in manifest[sport]:
            manifest[sport].append(date_str)
            manifest[sport] = sorted(set(manifest[sport]))

        with open(MANIFEST_PATH, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2)

        print(f'  Manifest updated: {sport} += {date_str}')
    except Exception as e:
        print(f'  WARNING: Could not update manifest: {e}')
        # Non-fatal - the HTML fallback in sync_calendars.py still works


def clear_hub_content(hub_path, html, content_start_idx, content_end_idx):
    """Replace the hub content area with the placeholder message."""
    new_html = (
        html[:html.find(CONTENT_START_MARKER) + len(CONTENT_START_MARKER)]
        + '\n'
        + PLACEHOLDER_HTML
        + '\n'
        + html[html.find(CONTENT_END_MARKER):]
    )

    with open(hub_path, 'w', encoding='utf-8') as f:
        f.write(new_html)


def main():
    if len(sys.argv) < 2:
        print('Usage: python rotate_hub_content.py <sport>')
        print(f'  Sports: {", ".join(sorted(SPORT_MAP.keys()))}')
        sys.exit(1)

    sport = sys.argv[1].lower()

    if sport not in SPORT_MAP:
        print(f'ERROR: Unknown sport "{sport}"')
        print(f'  Valid sports: {", ".join(sorted(SPORT_MAP.keys()))}')
        sys.exit(1)

    hub_filename = SPORT_MAP[sport]
    hub_path = os.path.join(REPO_ROOT, hub_filename)

    if not os.path.exists(hub_path):
        print(f'ERROR: Hub page not found: {hub_path}')
        print(f'  The hub page {hub_filename} does not exist yet.')
        sys.exit(1)

    # Read current hub page
    with open(hub_path, 'r', encoding='utf-8') as f:
        html = f.read()

    # Check for content markers
    if CONTENT_START_MARKER not in html or CONTENT_END_MARKER not in html:
        print(f'ERROR: Content markers not found in {hub_filename}')
        print(f'  Expected markers:')
        print(f'    {CONTENT_START_MARKER}')
        print(f'    {CONTENT_END_MARKER}')
        print(f'  Add these markers around the daily content section before using this script.')
        sys.exit(1)

    # Extract daily content
    content, start_idx, end_idx = extract_daily_content(html)

    if content is None:
        print(f'ERROR: Could not extract content from {hub_filename}')
        sys.exit(1)

    # Check if it's just the placeholder
    if is_placeholder_only(content):
        print(f'No content to archive for {sport} - hub has placeholder only')
        sys.exit(0)

    # Determine date and archive path
    today = datetime.now()
    archive_filename = get_archive_filename(sport, today)
    archive_path = os.path.join(REPO_ROOT, archive_filename)

    display = SPORT_DISPLAY[sport]
    date_display = today.strftime('%A, %B %d, %Y')

    print(f'Archiving {display} content for {date_display}...')

    # Append to archive
    success = append_to_archive(archive_path, content, today, sport)

    if success:
        print(f'  Archived {sport} content for {today.strftime("%Y-%m-%d")} to {archive_filename}')

        # Record in manifest (the single source of truth for sync_calendars.py)
        update_manifest(sport, today.strftime('%Y-%m-%d'))

        # Clear hub content
        clear_hub_content(hub_path, html, start_idx, end_idx)
        print(f'  Hub page {hub_filename} cleared for fresh content')
    else:
        print(f'  Archive operation did not complete. Hub page left unchanged.')
        sys.exit(1)


if __name__ == '__main__':
    main()
