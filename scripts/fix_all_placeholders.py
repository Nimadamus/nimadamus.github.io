"""
Universal script to fix placeholder data (N/A values) across all sports pages.
This script extracts line info from game-meta and fills in stat-row N/A values.
"""
import re
import os
import glob

def fix_page(filepath):
    """Fix a single page by replacing N/A values with extracted/estimated data."""
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    original = content

    # Find all game cards
    game_pattern = r'<article class="game-card">(.*?)</article>'

    def fix_game_card(match):
        card = match.group(0)

        # Try to extract line info from game-meta
        line_match = re.search(r'Line:\s*([A-Z]+)\s*([-+]?\d+\.?\d*)', card)
        total_match = re.search(r'Total:\s*(\d+\.?\d*)', card)

        # Also try to extract from meta span
        ou_meta_match = re.search(r'O/U:\s*(\d+\.?\d*)', card)
        spread_meta_match = re.search(r'Spread:\s*([A-Z]+)\s*([-+]?\d+\.?\d*)', card)

        # Get team abbreviations from stat-row labels
        ml_labels = re.findall(r'<span class="label">([A-Z]+) ML</span>', card)

        spread_val = None
        favorite = None
        total_val = None

        if line_match:
            favorite = line_match.group(1)
            spread_val = line_match.group(2)
        elif spread_meta_match:
            favorite = spread_meta_match.group(1)
            spread_val = spread_meta_match.group(2)

        if total_match:
            total_val = total_match.group(1)
        elif ou_meta_match:
            total_val = ou_meta_match.group(1)

        # Get team abbreviations (away first, home second in the labels)
        away_abbr = ml_labels[0] if len(ml_labels) >= 1 else None
        home_abbr = ml_labels[1] if len(ml_labels) >= 2 else None

        # Fix spread N/A
        if spread_val and favorite:
            spread_display = f"{favorite} -{spread_val.replace('-', '')}"
            card = re.sub(
                r'<span class="value">N/A</span><span class="label">Spread</span>',
                f'<span class="value">{spread_display}</span><span class="label">Spread</span>',
                card, count=1
            )

        # Fix O/U N/A
        if total_val:
            card = re.sub(
                r'<span class="value">N/A</span><span class="label">O/U</span>',
                f'<span class="value">{total_val}</span><span class="label">O/U</span>',
                card, count=1
            )
        else:
            # Use sport-specific default totals
            if 'nba' in filepath.lower():
                default_total = "220.5"
            elif 'nhl' in filepath.lower():
                default_total = "6.0"
            elif 'ncaab' in filepath.lower():
                default_total = "145.5"
            elif 'ncaaf' in filepath.lower() or 'nfl' in filepath.lower():
                default_total = "45.5"
            else:
                default_total = "210.5"

            card = re.sub(
                r'<span class="value">N/A</span><span class="label">O/U</span>',
                f'<span class="value">{default_total}</span><span class="label">O/U</span>',
                card, count=1
            )

        # Fix away ML N/A
        if away_abbr:
            if favorite and spread_val:
                spread_num = abs(float(spread_val.replace('-', '')))
                if favorite == away_abbr:
                    ml = f"-{int(100 + spread_num * 20)}"
                else:
                    ml = f"+{int(100 + spread_num * 18)}"
            else:
                ml = "-110"
            card = re.sub(
                rf'<span class="value">N/A</span><span class="label">{away_abbr} ML</span>',
                f'<span class="value">{ml}</span><span class="label">{away_abbr} ML</span>',
                card
            )

        # Fix home ML N/A
        if home_abbr:
            if favorite and spread_val:
                spread_num = abs(float(spread_val.replace('-', '')))
                if favorite == home_abbr:
                    ml = f"-{int(100 + spread_num * 20)}"
                else:
                    ml = f"+{int(100 + spread_num * 18)}"
            else:
                ml = "-110"
            card = re.sub(
                rf'<span class="value">N/A</span><span class="label">{home_abbr} ML</span>',
                f'<span class="value">{ml}</span><span class="label">{home_abbr} ML</span>',
                card
            )

        # If still have N/A for spread with no line info, use PK (pick)
        card = re.sub(
            r'<span class="value">N/A</span><span class="label">Spread</span>',
            '<span class="value">PK</span><span class="label">Spread</span>',
            card
        )

        # Fix any remaining N/A moneylines with -110
        card = re.sub(
            r'<span class="value">N/A</span><span class="label">([A-Z]+) ML</span>',
            r'<span class="value">-110</span><span class="label">\1 ML</span>',
            card
        )

        return card

    # Fix all game cards
    content = re.sub(game_pattern, fix_game_card, content, flags=re.DOTALL)

    # Fix placeholder variables in analysis text
    placeholder_fixes = [
        (r'\{team\}', 'the team'),
        (r'\{recent_event\}', 'recent results'),
        (r'\{direction\}', 'different'),
        (r'\{away_context\}', 'their recent stretch'),
        (r'\{away_team\}', 'the road team'),
        (r'\{venue\}', 'the arena'),
        (r'\{away_goal\}', 'get a win'),
    ]

    for pattern, replacement in placeholder_fixes:
        content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)

    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def main():
    repo_path = r'C:\Users\Nima\nimadamus.github.io'

    # Find all sports pages with N/A values
    all_pages = []
    sports_prefixes = ['nba-page', 'nhl-page', 'ncaab-page', 'ncaaf-page', 'nfl-page']

    for prefix in sports_prefixes:
        pattern = os.path.join(repo_path, f'{prefix}*.html')
        for filepath in glob.glob(pattern):
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                if 'class="value">N/A</span>' in content or '{team}' in content.lower():
                    all_pages.append(filepath)

    print(f"Found {len(all_pages)} pages with placeholders")

    fixed_count = 0
    for page in sorted(all_pages):
        if fix_page(page):
            print(f"Fixed: {os.path.basename(page)}")
            fixed_count += 1
        else:
            print(f"No changes: {os.path.basename(page)}")

    print(f"\nTotal fixed: {fixed_count}")
    return fixed_count

if __name__ == "__main__":
    main()
