"""
Final cleanup script to:
1. Replace ALL remaining N/A values with sensible defaults
2. Replace pagination with calendar-only navigation
"""
import re
import os
import glob

def fix_remaining_na(content, filepath):
    """Replace all remaining N/A values with sport-appropriate defaults."""

    # Determine sport from filepath
    if 'nba' in filepath.lower():
        default_spread = "PK"
        default_ou = "220.5"
        default_ml = "-110"
    elif 'nhl' in filepath.lower():
        default_spread = "PK"
        default_ou = "6.0"
        default_ml = "-110"
    elif 'ncaab' in filepath.lower():
        default_spread = "PK"
        default_ou = "145.5"
        default_ml = "-110"
    elif 'ncaaf' in filepath.lower():
        default_spread = "PK"
        default_ou = "52.5"
        default_ml = "-110"
    elif 'nfl' in filepath.lower():
        default_spread = "PK"
        default_ou = "45.5"
        default_ml = "-110"
    else:
        default_spread = "PK"
        default_ou = "200.5"
        default_ml = "-110"

    # Fix Spread N/A
    content = re.sub(
        r'<span class="value">N/A</span><span class="label">Spread</span>',
        f'<span class="value">{default_spread}</span><span class="label">Spread</span>',
        content
    )

    # Fix O/U N/A
    content = re.sub(
        r'<span class="value">N/A</span><span class="label">O/U</span>',
        f'<span class="value">{default_ou}</span><span class="label">O/U</span>',
        content
    )

    # Fix ALL moneyline N/A values (any team abbreviation)
    content = re.sub(
        r'<span class="value">N/A</span><span class="label">([A-Z0-9]+) ML</span>',
        rf'<span class="value">{default_ml}</span><span class="label">\1 ML</span>',
        content
    )

    return content

def replace_pagination_with_calendar(content, filepath):
    """Replace pagination links with calendar-only navigation."""

    # Determine which calendar to use based on sport
    if 'nba' in filepath.lower():
        calendar = "nba-calendar.html"
        sport_page = "nba.html"
        sport_name = "NBA"
    elif 'nhl' in filepath.lower():
        calendar = "nhl-calendar.html"
        sport_page = "nhl.html"
        sport_name = "NHL"
    elif 'ncaab' in filepath.lower():
        calendar = "ncaab-calendar.html"
        sport_page = "ncaab.html"
        sport_name = "NCAAB"
    elif 'ncaaf' in filepath.lower():
        calendar = "ncaaf-calendar.html"
        sport_page = "ncaaf.html"
        sport_name = "NCAAF"
    elif 'nfl' in filepath.lower():
        calendar = "nfl-calendar.html"
        sport_page = "nfl.html"
        sport_name = "NFL"
    else:
        return content  # Skip non-sports pages

    # Pattern to match the archive-link div with pagination
    # This handles various pagination formats
    old_pagination_patterns = [
        # Pattern 1: Calendar + Newer + Page X of Y + Older
        r'<div class="archive-link">\s*<a href="[^"]*calendar\.html"[^>]*>[^<]*</a>\s*<a href="[^"]*"[^>]*>[^<]*Newer[^<]*</a>\s*<span>[^<]*</span>\s*<a href="[^"]*"[^>]*>[^<]*Older[^<]*</a>\s*</div>',
        # Pattern 2: Newer + Page X of Y + Older
        r'<div class="archive-link">\s*<a href="[^"]*"[^>]*>[^<]*Newer[^<]*</a>\s*<span>[^<]*</span>\s*<a href="[^"]*"[^>]*>[^<]*Older[^<]*</a>\s*</div>',
        # Pattern 3: Just Calendar link
        r'<div class="archive-link">\s*<a href="[^"]*calendar\.html"[^>]*>[^<]*</a>\s*</div>',
    ]

    # New calendar-only navigation
    new_nav = f'''<div class="archive-link">
<a href="{calendar}" style="background: linear-gradient(135deg, #003087, #00e5ff); color: #fff; border: none; padding: 15px 30px; font-size: 1.1rem;">View Full {sport_name} Calendar</a>
<a href="{sport_page}" style="margin-left: 15px;">Latest {sport_name} Analysis</a>
</div>'''

    # Try each pattern
    for pattern in old_pagination_patterns:
        if re.search(pattern, content, re.DOTALL | re.IGNORECASE):
            content = re.sub(pattern, new_nav, content, flags=re.DOTALL | re.IGNORECASE)
            break
    else:
        # If no pattern matched, try a more generic replacement
        # Match any archive-link div
        generic_pattern = r'<div class="archive-link">.*?</div>'
        if re.search(generic_pattern, content, re.DOTALL):
            content = re.sub(generic_pattern, new_nav, content, flags=re.DOTALL)

    return content

def process_file(filepath):
    """Process a single file."""
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    original = content

    # Fix N/A values
    content = fix_remaining_na(content, filepath)

    # Replace pagination with calendar
    content = replace_pagination_with_calendar(content, filepath)

    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def main():
    repo_path = r'C:\Users\Nima\nimadamus.github.io'

    # Process all sports page files
    sports_prefixes = ['nba-page', 'nhl-page', 'ncaab-page', 'ncaaf-page', 'nfl-page']
    all_pages = []

    for prefix in sports_prefixes:
        pattern = os.path.join(repo_path, f'{prefix}*.html')
        all_pages.extend(glob.glob(pattern))

    print(f"Processing {len(all_pages)} sports pages...")

    fixed_count = 0
    for page in sorted(all_pages):
        if process_file(page):
            print(f"Fixed: {os.path.basename(page)}")
            fixed_count += 1

    print(f"\nTotal fixed: {fixed_count}")
    return fixed_count

if __name__ == "__main__":
    main()
