"""
Comprehensive script to fix ALL validation errors across the BetLegend site.
Fixes:
1. Line movement discussions (BANNED per January 24, 2026 rule)
2. Kevin Durant team references (Suns/Phoenix -> Rockets)
3. "Sharp money" references
4. "Reverse line movement" references
5. Opened at / moved to / ticked content
"""

import os
import re

REPO = r'C:\Users\Nima\nimadamus.github.io'

# Files to skip (educational content about betting mechanics)
SKIP_FILES = {
    'how-betting-lines-move.html',
    'betting-101.html',
    'betting-glossary.html',
    'line-shopping-betting-strategy.html',
    'CLAUDE.md',  # Protocol file
    'betlegend_validator.py',  # Validator script
    'fix_all_validation_errors.py',  # This script
    'fix_validation_errors.py',  # Previous script
}

def fix_file(filepath):
    """Fix all validation errors in a single file."""
    filename = os.path.basename(filepath)

    # Skip certain files
    if filename in SKIP_FILES:
        return False

    # Skip non-HTML files except for some specific patterns
    if not filepath.endswith('.html'):
        return False

    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        original = content

        # Fix Kevin Durant references - Suns/Phoenix -> Rockets/Houston
        # Be careful not to match historical content like "Durant signed with the Suns in 2023"
        content = re.sub(r'Durant([\'"]?s?)?\s+(with|for|on)\s+(the\s+)?(Phoenix\s+)?Suns',
                        r'Durant\1 \2 the Houston Rockets', content, flags=re.IGNORECASE)
        content = re.sub(r'Durant([\'"]?s?)?\s+tenure\s+(with|on)\s+(the\s+)?(Phoenix\s+)?Suns',
                        r"Durant's tenure with the Houston Rockets", content, flags=re.IGNORECASE)
        content = re.sub(r'Kevin\s+Durant.{0,15}(Phoenix|Suns)',
                        lambda m: m.group(0).replace('Phoenix', 'Houston').replace('Suns', 'Rockets'),
                        content, flags=re.IGNORECASE)

        # Fix line movement keywords in meta tags
        content = re.sub(r'reverse\s+line\s+movement', 'betting analysis', content, flags=re.IGNORECASE)
        content = re.sub(r'market\s+movement', 'betting trends', content, flags=re.IGNORECASE)

        # Fix "sharp money" references
        content = re.sub(r'sharp\s+money\s+(is\s+|has\s+been\s+|)coming\s+in\s+on', 'value exists on', content, flags=re.IGNORECASE)
        content = re.sub(r'sharp\s+money\s+(is\s+|has\s+been\s+|)hitting', 'value exists on', content, flags=re.IGNORECASE)
        content = re.sub(r'sharp\s+money\s+backing', 'the matchup advantage in favor of', content, flags=re.IGNORECASE)
        content = re.sub(r'sharp\s+money\s+(is\s+)?on\s+the', 'value is on the', content, flags=re.IGNORECASE)
        content = re.sub(r'where\s+the\s+sharp\s+money\s+is\s+going', 'where the value lies', content, flags=re.IGNORECASE)
        content = re.sub(r'sharp\s+money\s+sees', 'analysis suggests', content, flags=re.IGNORECASE)
        content = re.sub(r'sharp\s+money', 'professional analysis', content, flags=re.IGNORECASE)

        # Fix line opened/moved references in meta descriptions and content
        # Be more aggressive but careful
        content = re.sub(r'The\s+line\s+(has\s+)?opened\s+at\s+[^.]+\.', '', content, flags=re.IGNORECASE)
        content = re.sub(r'line\s+(has\s+)?moved\s+(from|to)[^.]+\.', '', content, flags=re.IGNORECASE)
        content = re.sub(r'The\s+line\s+(has\s+)?ticked\s+(down|up)[^.]+\.', '', content, flags=re.IGNORECASE)

        # Clean up double spaces from removals
        content = re.sub(r'  +', ' ', content)
        content = re.sub(r'\n\n\n+', '\n\n', content)

        if content != original:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False

def main():
    fixed_count = 0

    # Process all HTML files
    for root, dirs, files in os.walk(REPO):
        # Skip .git directory
        dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules']]

        for filename in files:
            filepath = os.path.join(root, filename)
            if fix_file(filepath):
                print(f"Fixed: {filepath}")
                fixed_count += 1

    print(f"\nTotal files fixed: {fixed_count}")

if __name__ == "__main__":
    main()
