#!/usr/bin/env python3
"""
Calendar Sync Script for BetLegend
Automatically scans all sports pages and rebuilds calendar JS files.
Run this script after creating new pages to ensure calendars are complete.

ENHANCED: December 25, 2025 - Improved date extraction to find dates in:
- Title
- Meta description
- Hero section
- Game-time spans (ISO format like 2025-12-20T22:00Z)
- Game-time written dates (like "Friday, December 20")
- Content body dates
"""

import os
import re
import json
import html
from datetime import datetime
from pathlib import Path

# Auto-detect repo directory (works on Windows locally and Linux in GitHub Actions)
import sys
REPO_DIR = Path(__file__).resolve().parent.parent  # scripts/ -> repo root
SCRIPTS_DIR = REPO_DIR / 'scripts'

# Sport configurations
# 'hub' = the rolling hub page (nba-previews.html, etc.) - always represents today's content
SPORTS = {
    'nba': {'prefix': 'nba', 'globs': ['nba*.html', '*-nba-*.html'], 'main': 'nba.html', 'hub': 'nba-previews.html', 'calendar_js': 'nba-calendar.js', 'archive_pattern': 'nba-previews-archive-*.html'},
    'nhl': {'prefix': 'nhl', 'globs': ['nhl*.html', '*-nhl-*.html'], 'main': 'nhl.html', 'hub': 'nhl-previews.html', 'calendar_js': 'nhl-calendar.js', 'archive_pattern': 'nhl-previews-archive-*.html'},
    'ncaab': {'prefix': 'ncaab', 'globs': ['ncaab*.html', 'college-basketball-*.html', '*-ncaab-*.html', '*-college-basketball-*.html'], 'main': 'ncaab.html', 'hub': 'college-basketball-previews.html', 'calendar_js': 'ncaab-calendar.js', 'archive_pattern': 'college-basketball-previews-archive-*.html'},
    'ncaaf': {'prefix': 'ncaaf', 'globs': ['ncaaf*.html', 'college-football-*.html', '*-ncaaf-*.html', '*-college-football-*.html'], 'main': 'ncaaf.html', 'hub': None, 'calendar_js': 'ncaaf-calendar.js', 'archive_pattern': None},
    'nfl': {'prefix': 'nfl', 'globs': ['nfl*.html', '*-nfl-*.html'], 'main': 'nfl.html', 'hub': None, 'calendar_js': 'nfl-calendar.js', 'archive_pattern': None},
    'mlb': {'prefix': 'mlb', 'globs': ['mlb*.html', '*-mlb-*.html'], 'main': 'mlb.html', 'hub': 'mlb-previews.html', 'calendar_js': 'mlb-calendar.js', 'archive_pattern': 'mlb-previews-archive-*.html'},
    'soccer': {'prefix': 'soccer', 'globs': ['soccer*.html', '*-soccer-*.html'], 'main': 'soccer.html', 'hub': 'soccer-previews.html', 'calendar_js': 'soccer-calendar.js', 'archive_pattern': 'soccer-previews-archive-*.html'},
}

SPORT_DISPLAY_NAMES = {
    'nba': 'NBA',
    'nhl': 'NHL',
    'ncaab': 'NCAAB',
    'ncaaf': 'NCAAF',
    'nfl': 'NFL',
    'mlb': 'MLB',
    'soccer': 'Soccer',
}

# Hub pages - these always represent today's content, not a fixed date
HUB_PAGES = {cfg['hub'] for cfg in SPORTS.values() if cfg.get('hub')}

# Pages to exclude from calendar (utility pages, news pages, data hubs, not daily analysis)
# NOTE: 'archive' excludes *-archive-* files from page scanning (dates from archives are extracted separately)
# NOTE: hub pages are handled specially (not excluded, but assigned today's date)
EXCLUDE_PATTERNS = ['calendar', 'archive', 'records', 'index', '-news', 'news-', 'offseason', 'insights', 'historical', 'trends', 'splits', 'betting-hub', 'handicapping-hub', 'how-to-bet', '-guide', 'complete-guide', 'line-shopping']

# Dates to EXCLUDE from calendars (days when no content was posted but pages exist)
# Format: { 'sport': ['YYYY-MM-DD', ...] }
# NOTE: Jan 25-27 exclusion was removed April 2, 2026 - pages exist and should be in calendar
EXCLUDED_DATES = {
}

CONTENT_START_MARKER = '<!-- ========== DAILY CONTENT START ========== -->'
CONTENT_END_MARKER = '<!-- ========== DAILY CONTENT END ========== -->'
PLACEHOLDER_TEXT = "Today's previews will be published shortly"

# Manual date overrides for pages where automatic extraction fails
# Format: 'filename.html': 'YYYY-MM-DD'
# These are used when the page title is generic and content dates are unreliable
MANUAL_DATE_OVERRIDES = {
    # NFL archive pages with Week 16 games
    'nfl-picks-predictions-against-the-spread-november-28-2025.html': '2025-11-28',  # Thanksgiving games (Week 13)
    'nfl-picks-predictions-against-the-spread-december-21-2025.html': '2025-12-21',  # Week 16 Saturday games
    'nfl-picks-predictions-against-the-spread-december-19-2025.html': '2025-12-19',  # Week 16 Thursday Night Football
    'nfl-picks-predictions-against-the-spread-december-20-2025.html': '2025-12-20',  # Week 16 Friday/Saturday games
    'nfl-picks-predictions-against-the-spread-december-21-2025-part-2.html': '2025-12-21',  # Week 16 Sunday games
    'nfl-picks-predictions-against-the-spread-december-21-2025-part-3.html': '2025-12-21',  # Week 16 Sunday games (duplicate)
    'nfl-picks-predictions-against-the-spread-december-21-2025-part-4.html': '2025-12-21',  # Week 16 Sunday games
    'nfl-picks-predictions-against-the-spread-december-21-2025-part-5.html': '2025-12-21',  # Week 16 Sunday games
    # NBA archive pages - CORRECTED based on actual game-time spans
    'nba-picks-analysis-against-the-spread-december-15-2025.html': '2025-12-15',   # December 15 NBA (title confirms)
    'nba-picks-analysis-against-the-spread-december-20-2025-part-4.html': '2025-12-20',   # December 20 NBA (game-time)
    'nba-picks-analysis-against-the-spread-december-21-2025-part-3.html': '2025-12-21',   # December 21 NBA (game-time)
    'nba-picks-analysis-against-the-spread-december-15-2025-part-2.html': '2025-12-15',   # December 15 NBA (title confirms)
    'nba-picks-analysis-against-the-spread-december-18-2025.html': '2025-12-18',   # December 18 NBA (game-time)
    'nba-picks-analysis-against-the-spread-december-19-2025.html': '2025-12-19',   # December 19 NBA (game-time)
    'nba-picks-analysis-against-the-spread-december-21-2025.html': '2025-12-21',  # December 21 NBA (game-time)
    'nba-picks-analysis-against-the-spread-december-22-2025.html': '2025-12-22',  # December 22 NBA
    'nba-picks-analysis-against-the-spread-december-22-2025-part-2.html': '2025-12-22',  # December 22 NBA (game-time 23T = 22 ET)
    'nba-picks-analysis-against-the-spread-december-22-2025-part-3.html': '2025-12-22',  # December 22 NBA (game-time 23T = 22 ET)
    'nba-picks-analysis-against-the-spread-december-23-2025.html': '2025-12-23',  # December 23 NBA (game-time 24T = 23 ET)
    'nba-picks-analysis-against-the-spread-december-26-2025.html': '2025-12-26',  # December 26 NBA
    'nba-picks-analysis-against-the-spread-december-21-2025-part-2.html': '2025-12-21',  # December 21 NBA
    'nba-picks-analysis-against-the-spread-december-28-2025.html': '2025-12-28',  # December 28 NBA
    'nba-picks-analysis-against-the-spread-december-28-2025-part-2.html': '2025-12-28',  # December 28 NBA (duplicate/same day)
    # NHL archive pages
    'nhl-predictions-best-bets-tonight-december-09-2025.html': '2025-12-09',   # December 9 NHL
    'nhl-predictions-best-bets-tonight-december-17-2025.html': '2025-12-17',  # December 17 NHL
    'nhl-predictions-best-bets-tonight-december-18-2025.html': '2025-12-18',  # December 18 NHL
    'nhl-predictions-best-bets-tonight-december-19-2025-part-2.html': '2025-12-19',  # December 19 NHL
    'nhl-predictions-best-bets-tonight-december-20-2025-part-2.html': '2025-12-20',  # December 20 NHL
    'nhl-predictions-best-bets-tonight-december-21-2025.html': '2025-12-21',  # December 21 NHL
    'nhl-predictions-best-bets-tonight-december-22-2025.html': '2025-12-22',  # December 22 NHL
    'nhl-predictions-best-bets-tonight-december-23-2025.html': '2025-12-23',  # December 23 NHL
    'nhl-predictions-best-bets-tonight-december-23-2025-part-2.html': '2025-12-23',  # December 23 NHL (evening games)
    'nhl-predictions-best-bets-tonight-december-27-2025.html': '2025-12-27',  # December 27 NHL (Saturday slate)
    'nhl-predictions-best-bets-tonight-december-27-2025-part-2.html': '2025-12-27',  # December 27 NHL (Saturday slate part 2)
    'nhl-predictions-best-bets-tonight-december-28-2025.html': '2025-12-28',  # December 28 NHL (Sunday slate)
    'nhl-predictions-best-bets-tonight-december-28-2025-part-2.html': '2025-12-28',  # December 28 NHL (Sunday slate part 2)
    'nhl-predictions-best-bets-tonight-december-29-2025.html': '2025-12-29',  # December 29 NHL (Sunday slate)
    'nhl-predictions-best-bets-tonight-december-31-2025.html': '2025-12-31',  # December 31 NHL (New Year's Eve - has ISO dates 2025-12-31)
    'nhl-predictions-best-bets-tonight-december-31-2025-part-2.html': '2025-12-31',  # December 31 NHL (New Year's Eve slate part 2)
    'nhl-predictions-best-bets-tonight-january-01-2026.html': '2026-01-01',  # January 1 NHL (New Year's Day)
    'nhl-predictions-best-bets-tonight-january-01-2026-part-2.html': '2026-01-01',  # January 1 NHL (New Year's Day part 2)
    'nhl-predictions-best-bets-tonight-january-01-2026-part-3.html': '2026-01-01',  # January 1 NHL (New Year's Day part 3)
    'nhl-predictions-best-bets-tonight-january-03-2026.html': '2026-01-03',  # January 3 NHL (Friday slate - Jets@Leafs, Caps@Sens, etc.)
    # NCAAB archive pages
    'college-basketball-picks-predictions-best-bets-december-04-2025.html': '2025-12-04',   # December 4 NCAAB
    'college-basketball-picks-predictions-best-bets-december-05-2025-part-2.html': '2025-12-05',   # December 5 NCAAB
    'college-basketball-picks-predictions-best-bets-december-07-2025-part-2.html': '2025-12-07',   # December 7 NCAAB
    'college-basketball-picks-predictions-best-bets-december-08-2025.html': '2025-12-08',   # December 8 NCAAB
    'college-basketball-picks-predictions-best-bets-december-09-2025-part-2.html': '2025-12-09',   # December 9 NCAAB
    'college-basketball-picks-predictions-best-bets-december-16-2025.html': '2025-12-16',  # December 16 NCAAB
    'college-basketball-picks-predictions-best-bets-december-17-2025.html': '2025-12-17',  # December 17 NCAAB
    'college-basketball-picks-predictions-best-bets-december-18-2025.html': '2025-12-18',  # December 18 NCAAB
    'college-basketball-picks-predictions-best-bets-december-19-2025-part-2.html': '2025-12-19',  # December 19 NCAAB
    'college-basketball-picks-predictions-best-bets-december-20-2025-part-2.html': '2025-12-20',  # December 20 NCAAB
    'college-basketball-picks-predictions-best-bets-december-21-2025.html': '2025-12-21',  # December 21 NCAAB
    'college-basketball-picks-predictions-best-bets-december-22-2025.html': '2025-12-22',  # December 22 NCAAB
    # NCAAF archive pages - CLEANED UP Jan 8, 2026
    # Most NCAAF pages now have dates in their titles, so we removed incorrect overrides.
    # Only keep overrides for pages that DON'T have dates in their titles.
    # Pages with correct title dates will extract automatically:
    # - college-football-picks-predictions-against-the-spread-december-19-2025.html: December 19, 2025 (title)
    # - college-football-picks-predictions-against-the-spread-december-23-2025.html: December 23, 2025 (title)
    # - college-football-picks-predictions-against-the-spread-december-27-2025.html: December 27, 2025 (title)
    # - college-football-picks-predictions-against-the-spread-december-29-2025.html: December 29, 2025 (title)
    # - college-football-picks-predictions-against-the-spread-december-30-2025.html: December 30, 2025 (title)
    # - college-football-picks-predictions-against-the-spread-december-31-2025.html: December 31, 2025 (title)
    # - college-football-picks-predictions-against-the-spread-january-01-2026.html: January 1, 2026 (title)
    # - college-football-picks-predictions-against-the-spread-january-02-2026.html: January 2, 2026 (title)
    # - college-football-picks-predictions-against-the-spread-january-06-2026.html: January 6, 2026 (title)
    # ============================================================
    # IMPORTANT: MAIN PAGES ARE NOT IN THIS LIST!
    # nba.html, nhl.html, ncaab.html, soccer.html, nfl.html, mlb.html
    # MUST extract dates from their page titles (not static overrides)
    # because main pages change daily with new content.
    # Only archive pages (pageXX.html) belong in this list.
    # ============================================================

    # NBA archive pages (NOT main page - nba.html extracts from title)
    'nba-picks-analysis-against-the-spread-january-07-2026.html': '2026-01-07',     # January 7 NBA
    'nba-picks-analysis-against-the-spread-january-05-2026.html': '2026-01-05',     # January 5 NBA
    'nba-picks-analysis-against-the-spread-january-06-2026.html': '2026-01-06',     # January 6 NBA
    'nba-picks-analysis-against-the-spread-january-04-2026.html': '2026-01-04',     # January 4 NBA
    'nba-picks-analysis-against-the-spread-january-03-2026-part-2.html': '2026-01-03',     # January 3 NBA
    # NHL archive pages (NOT main page - nhl.html extracts from title)
    'nhl-predictions-best-bets-tonight-january-07-2026.html': '2026-01-07',     # January 7 NHL
    'nhl-predictions-best-bets-tonight-january-05-2026.html': '2026-01-05',     # January 5 NHL
    'nhl-predictions-best-bets-tonight-january-06-2026.html': '2026-01-06',     # January 6 NHL
    'nhl-predictions-best-bets-tonight-january-04-2026.html': '2026-01-04',     # January 4 NHL
    'nhl-predictions-best-bets-tonight-january-03-2026-part-2.html': '2026-01-03',     # January 3 NHL
    # NCAAB archive pages (NOT main page - ncaab.html extracts from title)
    'college-basketball-picks-predictions-best-bets-january-07-2026.html': '2026-01-07',   # January 7 NCAAB
    'college-basketball-picks-predictions-best-bets-january-06-2026.html': '2026-01-06',   # January 6 NCAAB
    # Soccer archive pages (NOT main page - soccer.html extracts from title)
    'soccer-predictions-picks-best-bets-january-27-2026.html': '2026-01-27',  # January 27 Soccer
    'soccer-predictions-picks-best-bets-january-26-2026.html': '2026-01-26',  # January 26 Soccer
}

# Month name to number mapping
MONTH_MAP = {
    'january': 1, 'february': 2, 'march': 3, 'april': 4,
    'may': 5, 'june': 6, 'july': 7, 'august': 8,
    'september': 9, 'october': 10, 'november': 11, 'december': 12,
    'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4,
    'jun': 6, 'jul': 7, 'aug': 8, 'sep': 9, 'sept': 9,
    'oct': 10, 'nov': 11, 'dec': 12
}

def parse_written_date(text):
    """Parse a written date like 'December 23, 2025', 'Dec 23 2025', or 'Jan 26' into YYYY-MM-DD.

    Updated Jan 26, 2026: Now handles dates without year (assumes current year).
    This supports CTR-optimized title formats like 'NBA Picks Today - Jan 26 Matchups'.
    """
    # Pattern 1: Month Day, Year or Month Day Year (full format with year)
    pattern_with_year = r'(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)\.?\s+(\d{1,2}),?\s*(\d{4})'
    match = re.search(pattern_with_year, text, re.I)
    if match:
        month_name, day, year = match.groups()
        month_num = MONTH_MAP.get(month_name.lower())
        if month_num:
            return f"{year}-{month_num:02d}-{int(day):02d}"

    # Pattern 2: Month Day without year (e.g., 'Jan 26' or 'January 26')
    # Assumes current year. Used for CTR-optimized titles.
    pattern_no_year = r'(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)\.?\s+(\d{1,2})(?:\s|,|$|[^0-9])'
    match = re.search(pattern_no_year, text, re.I)
    if match:
        month_name, day = match.groups()
        month_num = MONTH_MAP.get(month_name.lower())
        if month_num:
            current_year = datetime.now().year
            return f"{current_year}-{month_num:02d}-{int(day):02d}"

    return None

def read_archive_manifest():
    """
    Read the hub-archive-manifest.json - the SINGLE SOURCE OF TRUTH for archived dates.
    The rotation script writes to this manifest every time it archives content.
    Returns dict like {'nba': ['2026-03-19', '2026-03-20', ...], 'nhl': [...], ...}
    """
    manifest_path = SCRIPTS_DIR / 'hub-archive-manifest.json'
    try:
        if manifest_path.exists():
            import json
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
            return manifest
    except Exception as e:
        print(f"  WARNING: Could not read archive manifest: {e}")
    return {}


def extract_dates_from_rotation_archive(filepath):
    """
    Extract ALL dates from a rotation archive file (e.g., nba-previews-archive-march-2026.html).
    These files contain <div class="archive-day" id="YYYY-MM-DD"> sections for each archived day.
    Also looks for date headers like "Tuesday, March 24, 2026" inside archive content.
    This is the FALLBACK method - the manifest is the primary source.
    Returns a list of date strings (YYYY-MM-DD).
    """
    dates = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # Method 1: Extract from archive-day div IDs
        archive_day_ids = re.findall(r'<div[^>]*class="archive-day"[^>]*id="(\d{4}-\d{2}-\d{2})"', content)
        dates.extend(archive_day_ids)

        # Method 2: Extract from archive-date headings like "Tuesday, March 24, 2026"
        archive_headings = re.findall(r'<h2[^>]*class="archive-date"[^>]*>([^<]+)</h2>', content)
        for heading in archive_headings:
            date = parse_written_date(heading)
            if date and date not in dates:
                dates.append(date)

        # Method 3: Extract from updated-line paragraphs within archived sections
        updated_lines = re.findall(r'<p[^>]*class="updated-line"[^>]*>[^<]*(?:Updated|Last Updated)[^<]*(\w+ \d{1,2},? \d{4})', content)
        for line in updated_lines:
            date = parse_written_date(line)
            if date and date not in dates:
                dates.append(date)

        # Method 4: Extract from HTML comment date markers like <!-- ===== MARCH 23, 2026 ===== -->
        comment_dates = re.findall(r'<!--\s*=+\s*(\w+ \d{1,2},? \d{4})\s*=+\s*-->', content)
        for cd in comment_dates:
            date = parse_written_date(cd)
            if date and date not in dates:
                dates.append(date)

        # Method 5: Extract from h2 headings with inline style (rotation archives use these)
        h2_dates = re.findall(r'<h2[^>]*>(\w+ \d{1,2},? \d{4})</h2>', content)
        for hd in h2_dates:
            date = parse_written_date(hd)
            if date and date not in dates:
                dates.append(date)

    except Exception as e:
        print(f"  ERROR reading rotation archive {filepath}: {e}")

    return sorted(set(dates))


def extract_date_from_page(filepath):
    """
    Extract date from page content using multiple methods.
    Searches in order of reliability:
    0. Hub pages (rolling hubs) - always return today's date
    0a. Manual override (for pages with unreliable dates)
    1. Title tag
    2. Meta description
    3. Hero section
    4. Game-time spans (various formats)
    5. datetime attributes
    6. Any written date in content
    7. File modification date (fallback)
    """
    try:
        filename = filepath.name if hasattr(filepath, 'name') else os.path.basename(filepath)

        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()  # Read full file to find game-time dates

        # Method 0: Hub pages should use the date shown in their updated line.
        # Treating every non-placeholder hub as "today" creates false calendar
        # entries whenever the hub content is a day or two behind publication.
        if filename in HUB_PAGES:
            start_marker = '<!-- ========== DAILY CONTENT START ========== -->'
            end_marker = '<!-- ========== DAILY CONTENT END ========== -->'
            start_idx = content.find(start_marker)
            end_idx = content.find(end_marker)
            if start_idx != -1 and end_idx != -1:
                daily_content = content[start_idx + len(start_marker):end_idx].strip()
                stripped = re.sub(r'<[^>]+>', '', daily_content).strip().lower()
                if not stripped or 'previews will be published shortly' in stripped:
                    return None
            updated_match = re.search(
                r'class="updated-line"[^>]*>[^<]*(?:Updated|Last Updated):?\s*(\w+ \d{1,2},?\s*\d{4})',
                content,
                re.I
            )
            if updated_match:
                updated_date = parse_written_date(updated_match.group(1).strip())
                if updated_date:
                    return updated_date
            return datetime.now().strftime('%Y-%m-%d')

        # Method 0a: Check manual override
        if filename in MANUAL_DATE_OVERRIDES:
            return MANUAL_DATE_OVERRIDES[filename]

        # UPDATED Jan 10, 2026: Main pages now extract date from TITLE
        MAIN_PAGES = ['nba.html', 'nhl.html', 'ncaab.html', 'ncaaf.html', 'nfl.html', 'mlb.html', 'soccer.html']

        # Method 1: Look for date in title
        title_match = re.search(r'<title>([^<]+)</title>', content[:5000], re.I)
        if title_match:
            date = parse_written_date(title_match.group(1))
            if date:
                return date

        # Method 2: Look for date in meta description
        desc_match = re.search(r'<meta\s+(?:name="description"\s+)?content="([^"]*)"', content[:5000], re.I)
        if desc_match:
            date = parse_written_date(desc_match.group(1))
            if date:
                return date

        # Method 3: Look in hero section (h1, hero-tagline, etc.)
        hero_match = re.search(r'<(?:h1|p)[^>]*class="[^"]*(?:hero|tagline)[^"]*"[^>]*>([^<]+)', content[:10000], re.I)
        if hero_match:
            date = parse_written_date(hero_match.group(1))
            if date:
                return date

        # Method 4: Look for ISO dates in game-time spans
        # Handles formats like:
        # - "2025-11-30 | Thursday, 12:30 PM ET"
        # - "2025-12-21T01:20Z | Soldier Field"
        game_time_matches = re.findall(r'<span[^>]*class="[^"]*game-time[^"]*"[^>]*>([^<]+)', content)
        for game_time in game_time_matches:
            # Look for ISO date at start: "2025-11-30 |"
            iso_start = re.search(r'^(\d{4}-\d{2}-\d{2})\s*\|', game_time)
            if iso_start:
                return iso_start.group(1)
            # Look for ISO datetime: "2025-12-21T01:20Z"
            iso_datetime = re.search(r'(\d{4}-\d{2}-\d{2})T\d{2}:\d{2}', game_time)
            if iso_datetime:
                return iso_datetime.group(1)
            # Look for written date in game-time
            date = parse_written_date(game_time)
            if date:
                return date

        # Method 5: Look for datetime attribute in content
        iso_datetime_matches = re.findall(r'datetime="(\d{4}-\d{2}-\d{2})T', content)
        if iso_datetime_matches:
            return iso_datetime_matches[0]

        # Method 6: Look for ISO dates anywhere in content (not the most reliable)
        # Skip dates that look like timestamps in scripts
        iso_match = re.search(r'[^0-9](\d{4}-\d{2}-\d{2})[^0-9T]', content[:100000])
        if iso_match:
            return iso_match.group(1)

        # Method 7: Look for any written date in the content (within first 50KB)
        # Skip if it looks like a generic archive date (avoid false positives)
        date = parse_written_date(content[:50000])
        if date:
            return date

        # Method 8: Fallback to file modification date
        mtime = os.path.getmtime(filepath)
        dt = datetime.fromtimestamp(mtime)
        return dt.strftime('%Y-%m-%d')

    except Exception as e:
        print(f"  ERROR reading {filepath}: {e}")
        return None

def extract_title_from_page(filepath, sport_prefix):
    """Extract a nice title from the page."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read(3000)

        # Look for title tag
        title_match = re.search(r'<title>([^<|]+)', content, re.I)
        if title_match:
            title = title_match.group(1).strip()
            # Clean up common suffixes
            title = re.sub(r'\s*\|\s*BetLegend.*$', '', title, flags=re.I)
            return title

        return f"{sport_prefix.upper()} Analysis"
    except:
        return f"{sport_prefix.upper()} Analysis"

def get_sport_pages(sport_config):
    """Get all pages for a sport."""
    prefix = sport_config['prefix']
    pages = []

    # Scan main directory for sport pages using multiple glob patterns
    glob_patterns = sport_config.get('globs', [f'{prefix}*.html'])
    seen_files = set()
    for pattern in glob_patterns:
        for filepath in REPO_DIR.glob(pattern):
            filename = filepath.name
            if filename in seen_files:
                continue
            seen_files.add(filename)

            # Skip utility pages
            skip = False
            for excl_pattern in EXCLUDE_PATTERNS:
                if excl_pattern in filename.lower():
                    skip = True
                    break
            if skip:
                continue

            # Skip redirect stubs (renamed pages that now just redirect)
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as peek:
                    first_500 = peek.read(500)
                    if 'Page Moved' in first_500 or 'http-equiv="refresh"' in first_500:
                        continue
            except:
                pass

            # This is a content page
            date = extract_date_from_page(filepath)
            title = extract_title_from_page(filepath, prefix)

            if date:
                pages.append({
                    'date': date,
                    'page': filename,
                    'title': title
                })
                print(f"    {filename}: {date}")

    # Also scan archives folder for this sport (e.g., archives/nba/)
    archives_dir = REPO_DIR / 'archives' / prefix
    if archives_dir.exists():
        for filepath in archives_dir.glob('*.html'):
            filename = filepath.name
            # Archive files use date format like 2025-12-01.html
            date_match = re.match(r'(\d{4}-\d{2}-\d{2})\.html', filename)
            if date_match:
                date = date_match.group(1)
                relative_path = f'archives/{prefix}/{filename}'
                pages.append({
                    'date': date,
                    'page': relative_path,
                    'title': f'{prefix.upper()} Archive - {date}'
                })
                print(f"    {relative_path}: {date}")

    def archive_page_for_date(date):
        """Return a month archive anchor for a recovered hub date when it exists."""
        if not archive_pattern:
            return None

        date_obj = datetime.strptime(date, '%Y-%m-%d')
        month_name = date_obj.strftime('%B').lower()
        year = date_obj.strftime('%Y')
        archive_filename = archive_pattern.replace('*', f'{month_name}-{year}')
        archive_path = REPO_DIR / archive_filename

        if not archive_path.exists():
            return None

        try:
            with open(archive_path, 'r', encoding='utf-8', errors='ignore') as f:
                archive_html = f.read()
            if f'id="{date}"' in archive_html or f"id='{date}'" in archive_html:
                return f'{archive_filename}#{date}'
        except Exception:
            return None

        return None

    # =========================================================================
    # ARCHIVE DATE RECOVERY: Read from JSON manifest (primary) + HTML (fallback)
    # The manifest is the single source of truth, written by rotate_hub_content.py.
    # HTML parsing is a fallback for dates that predate the manifest.
    # =========================================================================
    hub_page = sport_config.get('hub')
    archive_pattern = sport_config.get('archive_pattern')
    existing_dates = {p['date'] for p in pages}
    manifest_dates = set()

    # PRIMARY: Read from hub-archive-manifest.json
    manifest_path = SCRIPTS_DIR / 'hub-archive-manifest.json'
    if manifest_path.exists():
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
            sport_dates = manifest.get(prefix, [])
            for date in sport_dates:
                if date not in existing_dates:
                    archive_page = archive_page_for_date(date)
                    if not archive_page and hub_page:
                        print(f"    [SKIP MANIFEST] {hub_page}: {date} has no archive anchor or specific page")
                        continue
                    pages.append({
                        'date': date,
                        'page': archive_page or hub_page or f'{prefix}.html',
                        'title': f'{prefix.upper()} Analysis - {date}'
                    })
                    existing_dates.add(date)
                    manifest_dates.add(date)
                    print(f"    [FROM MANIFEST] {hub_page}: {date}")
        except Exception as e:
            print(f"  WARNING: Could not read manifest: {e}")

    # FALLBACK: Also scan rotation archive HTML files for dates not in manifest
    if archive_pattern:
        for filepath in REPO_DIR.glob(archive_pattern):
            archive_dates = extract_dates_from_rotation_archive(filepath)
            for date in archive_dates:
                if date not in existing_dates:
                    archive_page = archive_page_for_date(date)
                    if not archive_page and hub_page:
                        print(f"    [SKIP ARCHIVE HTML] {hub_page}: {date} has no archive anchor or specific page")
                        continue
                    pages.append({
                        'date': date,
                        'page': archive_page or hub_page or f'{prefix}.html',
                        'title': f'{prefix.upper()} Analysis - {date}'
                    })
                    existing_dates.add(date)
                    print(f"    [FROM ARCHIVE HTML] {hub_page}: {date}")

    # Sort by date (newest first) then by page name
    pages.sort(key=lambda x: (x['date'], x['page']), reverse=True)

    # Deduplicate: for each date, prefer specific analysis pages over generic main/hub pages
    # The calendar shows only one page per date (dateMap uses first match),
    # so we order entries to put specific pages BEFORE hub/main pages for each date
    generic_pages = {sport_config.get('main', ''), sport_config.get('hub', '')}
    generic_pages.discard(None)
    generic_pages.discard('')

    def sort_key(entry):
        """Sort by date desc, then specific pages before generic ones."""
        is_generic = 1 if entry['page'] in generic_pages else 0
        return (-int(entry['date'].replace('-', '')), is_generic, entry['page'])

    pages.sort(key=sort_key)

    return pages

def generate_calendar_js(sport_name, sport_config, pages):
    """Generate the calendar JS file content."""
    today = datetime.now().strftime('%B %d, %Y')

    lines = [
        f'// {sport_name.upper()} Archive Calendar Data',
        f'// Last updated: {today}',
        f'// Auto-generated by sync_calendars.py - DO NOT EDIT MANUALLY',
        '',
        'const ARCHIVE_DATA = ['
    ]

    for page in pages:
        escaped_title = page['title'].replace('"', '\\"')
        lines.append(f'    {{ date: "{page["date"]}", page: "{page["page"]}", title: "{escaped_title}" }},')

    lines.append('];')
    lines.append('')

    # Build the MAIN_PAGES list dynamically - includes both legacy main pages AND hub pages
    hub_page = sport_config.get('hub')
    main_pages_list = ['nba.html', 'nhl.html', 'ncaab.html', 'ncaaf.html', 'nfl.html', 'mlb.html', 'soccer.html']
    if hub_page and hub_page not in main_pages_list:
        main_pages_list.append(hub_page)
    main_pages_js = ', '.join(f"'{p}'" for p in main_pages_list)

    # Add the rest of the calendar JS code
    lines.extend([
        'const dateMap = {};',
        'ARCHIVE_DATA.forEach(item => { if (!dateMap[item.date]) dateMap[item.date] = item; });',
        '',
        'const pageToDateMap = {};',
        'ARCHIVE_DATA.forEach(item => { pageToDateMap[item.page] = item.date; });',
        '',
        f"const SPORT_HUB_PAGE = '{hub_page or ''}';",
        f"const MAIN_PAGES = [{main_pages_js}];",
        "function isConcreteContentPage(page) {",
        "    return !!page && !MAIN_PAGES.includes(page) && !page.includes('#') && !page.includes('-archive-');",
        "}",
        "const latestContentEntry = ARCHIVE_DATA.find(item => item.page && item.page !== SPORT_HUB_PAGE);",
        "const latestConcreteEntry = ARCHIVE_DATA.find(item => isConcreteContentPage(item.page));",
        "window.LATEST_CONTENT_PAGE = latestConcreteEntry ? latestConcreteEntry.page : (latestContentEntry ? latestContentEntry.page : null);",
        '',
        '// Main pages and hub pages show today when today has data; otherwise show the latest available content',
        "const today = new Date();",
        "const todayStr = today.getFullYear() + '-' + String(today.getMonth() + 1).padStart(2, '0') + '-' + String(today.getDate()).padStart(2, '0');",
        '',
        "const todayMonth = todayStr.substring(0, 7);",
        "const latestAvailableDate = latestConcreteEntry ? latestConcreteEntry.date : (ARCHIVE_DATA.length > 0 ? ARCHIVE_DATA[0].date : todayStr);",
        "const todayHasData = ARCHIVE_DATA.some(item => item.date === todayStr && isConcreteContentPage(item.page));",
        '',
        '// Handle both root pages and archive pages',
        'const pathname = window.location.pathname;',
        'let currentPage;',
        "if (pathname.includes('/archives/')) {",
        "    // For archive pages, get the full relative path from archives/",
        "    currentPage = pathname.replace(/^\\//, '');",
        '} else {',
        "    // For root pages, just get the filename",
        "    currentPage = pathname.split('/').pop() || 'index.html';",
        '}',
        '',
        '// For main/hub pages, prefer today when populated, then fall back to latest available content',
        '// For archive pages, use the page\'s mapped date',
        'const isMainPage = MAIN_PAGES.includes(currentPage);',
        'const forcedDate = window.FORCED_PAGE_DATE || null;',
        'const currentPageDate = isMainPage ? (forcedDate || (todayHasData ? todayStr : latestAvailableDate)) : (pageToDateMap[currentPage] || null);',
        '',
        'const months = new Set();',
        "ARCHIVE_DATA.forEach(item => { const [y, m] = item.date.split('-'); months.add(y + '-' + m); });",
        '// Include today\'s month only when that sport has content today',
        "if (todayHasData) months.add(todayMonth);",
        '',
        '// Main/hub pages show today\'s month; archive pages show their month',
        'const sortedMonths = Array.from(months).sort().reverse();',
        "const monthNames = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];",
        '',
        '// For main pages, default to today\'s month; for archive pages, use their month',
        "let displayMonth = currentPageDate ? currentPageDate.substring(0, 7) : sortedMonths[0];",
        '',
        'function renderCalendar(yearMonth) {',
        "    const [year, month] = yearMonth.split('-').map(Number);",
        "    const yearEl = document.getElementById('cal-year');",
        '    if (yearEl) yearEl.textContent = year;',
        '    const firstDay = new Date(year, month - 1, 1).getDay();',
        '    const daysInMonth = new Date(year, month, 0).getDate();',
        "    const container = document.getElementById('calendar-days');",
        '    if (!container) return;',
        "    container.innerHTML = '';",
        "    for (let i = 0; i < firstDay; i++) { const cell = document.createElement('div'); cell.className = 'cal-day empty'; container.appendChild(cell); }",
        '    for (let d = 1; d <= daysInMonth; d++) {',
        "        const dateStr = year + '-' + String(month).padStart(2, '0') + '-' + String(d).padStart(2, '0');",
        '        const hasData = dateMap[dateStr];',
        "        let classes = 'cal-day';",
        "        if (dateStr === currentPageDate) classes += ' current-page';",
        "        if (dateStr === todayStr) classes += ' today';",
        "        if (hasData) classes += ' has-content';",
        "        const cell = document.createElement('div');",
        '        cell.className = classes;',
        '        cell.textContent = d;',
        '        if (hasData) { cell.title = hasData.title; cell.onclick = () => window.location.href = "/" + hasData.page; }',
        '        container.appendChild(cell);',
        '    }',
        '}',
        '',
        'function initSportCalendar() {',
        '    if (SPORT_HUB_PAGE && currentPage === SPORT_HUB_PAGE && window.LATEST_CONTENT_PAGE && window.LATEST_CONTENT_PAGE !== currentPage) {',
        "        window.location.replace('/' + window.LATEST_CONTENT_PAGE);",
        '        return;',
        '    }',
        '',
        "    const monthSelect = document.getElementById('month-select');",
        '    if (monthSelect) {',
        "        monthSelect.innerHTML = '';",
        '        sortedMonths.forEach(m => {',
        "            const [year, month] = m.split('-');",
        "            const opt = document.createElement('option');",
        '            opt.value = m;',
        "            opt.textContent = monthNames[parseInt(month) - 1] + ' ' + year;",
        '            if (m === displayMonth) opt.selected = true;',
        '            monthSelect.appendChild(opt);',
        '        });',
        "        monthSelect.addEventListener('change', function() { renderCalendar(this.value); });",
        '    }',
        '    renderCalendar(displayMonth);',
        "    const mobileSelect = document.getElementById('mobile-archive-select');",
        '    if (mobileSelect) {',
        '        mobileSelect.innerHTML = \'<option value="">Select a date...</option>\';',
        '        ARCHIVE_DATA.forEach(item => {',
        "            const opt = document.createElement('option');",
        '            opt.value = item.page;',
        "            const dateObj = new Date(item.date + 'T12:00:00');",
        "            const dateLabel = dateObj.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });",
        "            opt.textContent = dateLabel + ' - ' + item.title;",
        '            if (item.page === currentPage) opt.selected = true;',
        '            mobileSelect.appendChild(opt);',
        '        });',
        "        mobileSelect.addEventListener('change', (e) => { if (e.target.value) window.location.href = '/' + e.target.value; });",
        '    }',
        '}',
        '',
        "if (document.readyState === 'loading') { document.addEventListener('DOMContentLoaded', initSportCalendar); } else { initSportCalendar(); }",
        ''
    ])

    return '\n'.join(lines)


def _format_iso_date_for_display(date_str):
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').strftime('%A, %B %d, %Y')
    except ValueError:
        return date_str


def _build_latest_preview_fallback(display_name, latest_page):
    latest_date = _format_iso_date_for_display(latest_page['date'])
    latest_title = html.escape(html.unescape(latest_page['title']))
    latest_href = html.escape(latest_page['page'])
    cta_label = f"Open Latest {display_name} Preview"
    return f'''<div style="text-align:center;padding:48px 24px;">
<p style="font-size:12px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:var(--accent-cyan);margin-bottom:12px;">Latest Available Preview</p>
<p style="font-size:18px;font-family:var(--font-display);letter-spacing:1px;text-transform:uppercase;color:var(--accent-gold);margin-bottom:14px;">{latest_date}</p>
<p style="font-size:20px;color:var(--text-primary);margin-bottom:24px;max-width:760px;margin-left:auto;margin-right:auto;">{latest_title}</p>
<a href="{latest_href}" style="display:inline-block;padding:16px 32px;background:linear-gradient(135deg,var(--accent-orange),#ff6b20);color:#fff;font-family:var(--font-display);font-size:15px;font-weight:700;text-decoration:none;border-radius:12px;text-transform:uppercase;letter-spacing:1.5px;box-shadow:0 4px 20px rgba(253,80,0,0.35);">{html.escape(cta_label)} &rarr;</a>
</div>'''


def update_hub_placeholder_fallback(sport_name, sport_config, pages):
    """When a hub is empty, publish a latest-available preview card into the daily slot."""
    hub_page = sport_config.get('hub')
    if not hub_page:
        return False

    hub_path = REPO_DIR / hub_page
    if not hub_path.exists():
        return False

    with open(hub_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    start_idx = content.find(CONTENT_START_MARKER)
    end_idx = content.find(CONTENT_END_MARKER)
    if start_idx == -1 or end_idx == -1:
        return False

    daily_start = start_idx + len(CONTENT_START_MARKER)
    daily_html = content[daily_start:end_idx].strip()
    daily_text = re.sub(r'<[^>]+>', ' ', daily_html)
    daily_text = re.sub(r'\s+', ' ', daily_text).strip().lower()
    has_placeholder = PLACEHOLDER_TEXT.lower() in daily_text
    has_existing_fallback = 'latest available preview' in daily_text
    if not has_placeholder and not has_existing_fallback:
        return False

    excluded_pages = {hub_page}
    main_page = sport_config.get('main')
    if main_page:
        excluded_pages.add(main_page)
    latest_page = next((
        p for p in pages
        if p.get('page') not in excluded_pages
        and '#' not in p.get('page', '')
        and '-archive-' not in p.get('page', '')
    ), None)
    if not latest_page:
        latest_page = next((p for p in pages if p.get('page') != hub_page), None)
    if not latest_page:
        return False

    fallback_html = _build_latest_preview_fallback(SPORT_DISPLAY_NAMES[sport_name], latest_page)
    updated = (
        content[:daily_start]
        + '\n'
        + fallback_html
        + '\n'
        + content[end_idx:]
    )

    latest_date_label = _format_iso_date_for_display(latest_page['date'])
    updated = re.sub(
        r'(<p class="updated-line">Last Updated:\s*)[^<]+(</p>)',
        rf'\1{latest_date_label}\2',
        updated,
        count=1
    )

    if updated == content:
        return False

    with open(hub_path, 'w', encoding='utf-8') as f:
        f.write(updated)

    print(f"  Updated {hub_page} placeholder with latest preview fallback")
    return True

def remove_pagination_from_sports_pages():
    """
    PERMANENTLY removes pagination from ALL sports pages AND featured game pages.
    These pages use calendar sidebar only - NO archive-link pagination.
    Added January 3, 2026 - This runs automatically with every calendar sync.
    Updated January 8, 2026 - Now also cleans featured game pages.
    """
    print("\n[CLEANUP] Removing pagination from sports + featured game pages...")
    sports_patterns = ['nba', 'nhl', 'nfl', 'ncaab', 'ncaaf', 'mlb', 'soccer']
    count = 0

    for f in os.listdir(REPO_DIR):
        if not f.endswith('.html'):
            continue
        # Check if it's a sports page OR a featured game page
        is_target = False
        for sp in sports_patterns:
            if f == f'{sp}.html' or f.startswith(f'{sp}-page'):
                is_target = True
                break
        # Also include featured game pages
        if f.startswith('featured-game'):
            is_target = True
        if not is_target:
            continue

        path = REPO_DIR / f
        with open(path, 'r', encoding='utf-8', errors='ignore') as file:
            content = file.read()

        orig = content
        # Remove archive-link divs (pagination)
        content = re.sub(r'\n*<div class="archive-link">.*?</div>\n*', '\n', content, flags=re.DOTALL)
        # Remove date-section divs that might be pagination
        content = re.sub(r'\n*<div class="date-section">.*?</div>\n*', '\n', content, flags=re.DOTALL)

        if content != orig:
            with open(path, 'w', encoding='utf-8') as file:
                file.write(content)
            count += 1

    if count > 0:
        print(f"  [OK] Removed pagination from {count} files")
    else:
        print(f"  [OK] No pagination found - all clean!")
    return count

def fix_main_page_canonicals():
    """
    Enforces canonical + og:url on main sport pages.

    Updated April 19, 2026: Pages that have a preview hub (nba-previews.html etc.)
    must canonical to the HUB, not themselves. Prior self-canonicals created a
    duplicate-content pair (nba.html + nba-previews.html both indexable, both
    self-canonical) which split authority and collapsed impressions.

    SLATE still copies archive content into the main pages, so this runs after
    every sync to reset the canonical back to the correct target.
    """
    print("\n[CANONICAL FIX] Enforcing canonicals on main sport pages...")
    MAIN_PAGES = {
        'nba.html': 'https://www.betlegendpicks.com/nba-previews.html',
        'nhl.html': 'https://www.betlegendpicks.com/nhl-previews.html',
        'ncaab.html': 'https://www.betlegendpicks.com/college-basketball-previews.html',
        'ncaaf.html': 'https://www.betlegendpicks.com/ncaaf.html',
        'nfl.html': 'https://www.betlegendpicks.com/nfl.html',
        'mlb.html': 'https://www.betlegendpicks.com/mlb-previews.html',
        'soccer.html': 'https://www.betlegendpicks.com/soccer-previews.html',
    }
    fixed_count = 0

    for filename, correct_url in MAIN_PAGES.items():
        filepath = REPO_DIR / filename
        if not filepath.exists():
            continue

        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        original = content

        # Fix canonical tag - replace any href value with the correct self-referential URL
        content = re.sub(
            r'(<link\s[^>]*rel="canonical"[^>]*href=")[^"]*(")',
            rf'\g<1>{correct_url}\2',
            content
        )
        # Also handle reversed attribute order: href before rel
        content = re.sub(
            r'(<link\s[^>]*href=")[^"]*("[^>]*rel="canonical")',
            rf'\g<1>{correct_url}\2',
            content
        )

        # Fix og:url tag
        content = re.sub(
            r'(<meta\s[^>]*property="og:url"[^>]*content=")[^"]*(")',
            rf'\g<1>{correct_url}\2',
            content
        )
        # Also handle reversed attribute order
        content = re.sub(
            r'(<meta\s[^>]*content=")[^"]*("[^>]*property="og:url")',
            rf'\g<1>{correct_url}\2',
            content
        )

        if content != original:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            fixed_count += 1
            print(f"  [FIXED] {filename} - canonical/og:url now points to itself")

    if fixed_count == 0:
        print("  [OK] All main pages already have correct canonicals")
    else:
        print(f"  [OK] Fixed {fixed_count} main page(s)")
    return fixed_count


def auto_archive_hub_content():
    """
    AUTOMATIC ARCHIVAL: Before syncing calendars, check each hub page.
    If a hub has real content (not placeholder) and that date is NOT yet
    in the manifest, archive it automatically. This prevents content loss
    when the hub gets overwritten by the next SLATE.

    This is the SAFETY NET - it runs every time sync_calendars.py runs,
    which happens after every SLATE. So even if rotate_all_hubs.py was
    forgotten, the content gets archived here before it can be lost.

    Added March 24, 2026 - PERMANENT FIX for lost calendar days.
    """
    import subprocess

    print("\n[AUTO-ARCHIVE] Checking hub pages for unarchived content...")
    manifest = read_archive_manifest()
    archived_count = 0

    for sport_name, sport_config in SPORTS.items():
        hub_file = sport_config.get('hub')
        if not hub_file:
            continue

        hub_path = REPO_DIR / hub_file
        if not hub_path.exists():
            continue

        # Read the hub page
        with open(hub_path, 'r', encoding='utf-8', errors='ignore') as f:
            html = f.read()

        # Check if it has real content (not placeholder)
        start_marker = '<!-- ========== DAILY CONTENT START ========== -->'
        end_marker = '<!-- ========== DAILY CONTENT END ========== -->'
        start_idx = html.find(start_marker)
        end_idx = html.find(end_marker)

        if start_idx == -1 or end_idx == -1:
            continue

        content = html[start_idx + len(start_marker):end_idx].strip()
        stripped = re.sub(r'<[^>]+>', '', content).strip()

        # Skip if placeholder only
        if not stripped or "previews will be published shortly" in stripped.lower():
            continue

        # Extract the content date from the updated-line
        updated_match = re.search(
            r'class="updated-line"[^>]*>[^<]*(?:Updated|Last Updated):?\s*(\w+ \d{1,2},?\s*\d{4})',
            html
        )
        if updated_match:
            content_date = parse_written_date(updated_match.group(1).strip())
        else:
            content_date = datetime.now().strftime('%Y-%m-%d')

        if not content_date:
            continue

        # Check if this date is already in the manifest
        sport_dates = manifest.get(sport_name, [])
        if content_date in sport_dates:
            continue

        # This date has real content but is NOT archived yet - archive it now
        print(f"  [ARCHIVING] {sport_name.upper()} {content_date} - content found in hub but not in manifest")
        try:
            result = subprocess.run(
                [sys.executable, str(SCRIPTS_DIR / 'rotate_hub_content.py'), sport_name],
                capture_output=True, text=True, cwd=str(REPO_DIR)
            )
            if result.returncode == 0:
                archived_count += 1
                print(f"    Archived successfully")
            else:
                # Don't clear the hub - just record the date in the manifest so the calendar sees it
                print(f"    Archive script returned error, recording date in manifest directly")
                manifest.setdefault(sport_name, [])
                if content_date not in manifest[sport_name]:
                    manifest[sport_name].append(content_date)
                    manifest[sport_name] = sorted(set(manifest[sport_name]))
                    manifest_path = SCRIPTS_DIR / 'hub-archive-manifest.json'
                    with open(manifest_path, 'w', encoding='utf-8') as f:
                        json.dump(manifest, f, indent=2)
        except Exception as e:
            print(f"    WARNING: Auto-archive failed: {e}")
            # Still record the date so the calendar shows it
            manifest.setdefault(sport_name, [])
            if content_date not in manifest[sport_name]:
                manifest[sport_name].append(content_date)
                manifest[sport_name] = sorted(set(manifest[sport_name]))
                manifest_path = SCRIPTS_DIR / 'hub-archive-manifest.json'
                with open(manifest_path, 'w', encoding='utf-8') as f:
                    json.dump(manifest, f, indent=2)

    if archived_count > 0:
        print(f"  [OK] Auto-archived {archived_count} hub(s)")
    else:
        print(f"  [OK] All hub content already archived")


def main():
    print("=" * 60)
    print("BetLegend Calendar Sync (Enhanced Date Extraction)")
    print("=" * 60)

    # AUTOMATIC ARCHIVAL: Archive any unarchived hub content before syncing
    # This is the safety net that prevents content loss. It runs EVERY time.
    auto_archive_hub_content()

    # ALWAYS fix main page canonicals first (prevents SLATE from breaking SEO)
    fix_main_page_canonicals()

    # ALWAYS remove pagination first - sports pages use calendar only
    remove_pagination_from_sports_pages()

    total_pages = 0
    for sport_name, sport_config in SPORTS.items():
        print(f"\n{'='*40}")
        print(f"Processing {sport_name.upper()}...")
        print(f"{'='*40}")

        pages = get_sport_pages(sport_config)

        # Filter out excluded dates for this sport
        excluded = EXCLUDED_DATES.get(sport_name, [])
        if excluded:
            before_count = len(pages)
            pages = [p for p in pages if p['date'] not in excluded]
            if before_count != len(pages):
                print(f"  [EXCLUDED] Removed {before_count - len(pages)} pages with excluded dates: {excluded}")

        total_pages += len(pages)
        print(f"\n  Total: {len(pages)} content pages found")

        if pages:
            js_content = generate_calendar_js(sport_name, sport_config, pages)
            js_path = SCRIPTS_DIR / sport_config['calendar_js']

            with open(js_path, 'w', encoding='utf-8') as f:
                f.write(js_content)

            print(f"  Updated {sport_config['calendar_js']}")
            update_hub_placeholder_fallback(sport_name, sport_config, pages)

    # Update cache busters on all preview hub pages so browsers load fresh calendar JS
    update_calendar_cache_busters()

    print("\n" + "=" * 60)
    print(f"Calendar sync complete! Total: {total_pages} pages across all sports")
    print("Don't forget to commit and push the changes.")
    print("=" * 60)


def update_calendar_cache_busters():
    """
    Updates the ?v= cache buster on calendar JS script tags in all hub pages.
    This ensures browsers always load the latest calendar data after sync.
    Without this, browsers serve stale calendar JS and show wrong months/dates.

    Added April 7, 2026 - fixes bug where calendars showed March instead of current month.
    """
    from datetime import datetime
    today_stamp = datetime.now().strftime('%Y%m%d%H%M')

    hub_calendar_map = {
        'nba-previews.html': 'nba-calendar.js',
        'nhl-previews.html': 'nhl-calendar.js',
        'mlb-previews.html': 'mlb-calendar.js',
        'soccer-previews.html': 'soccer-calendar.js',
        'college-basketball-previews.html': 'ncaab-calendar.js',
        'nfl.html': 'nfl-calendar.js',
        'ncaaf.html': 'ncaaf-calendar.js',
    }

    print(f"\n[CACHE BUSTER] Updating calendar JS versions to {today_stamp}...")
    updated = 0

    for hub_page, cal_js in hub_calendar_map.items():
        filepath = REPO_DIR / hub_page
        if not filepath.exists():
            continue

        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        original = content
        # Match the calendar JS script tag and update its version parameter
        content = re.sub(
            rf'{re.escape(cal_js)}\?v=\d+',
            f'{cal_js}?v={today_stamp}',
            content
        )

        if content != original:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            updated += 1
            print(f"  [UPDATED] {hub_page} -> {cal_js}?v={today_stamp}")

    if updated == 0:
        print("  [OK] All cache busters already current")
    else:
        print(f"  [OK] Updated {updated} hub page(s)")


if __name__ == '__main__':
    main()
