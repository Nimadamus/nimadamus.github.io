"""
Script to fix validation errors across the BetLegend site:
1. Remove line movement discussions (BANNED per January 24, 2026 rule)
2. Fix Kevin Durant team references (Suns/Phoenix -> Rockets)
"""

import os
import re

REPO = r'C:\Users\Nima\nimadamus.github.io'

# Patterns for line movement discussions to remove/replace
LINE_MOVEMENT_PATTERNS = [
    # Sentences about line movement
    (r"The line (has |)opened at [^.]+\.", ""),
    (r"The line (has |)moved (from|to) [^.]+\.", ""),
    (r"Sharp money (is |has been |)coming in on [^.]+\.", ""),
    (r"Sharp money (is |has been |)hitting [^.]+\.", ""),
    (r"The line (has |)ticked (down|up) [^.]+\.", ""),
    (r"Money (is |has been |)coming in on [^.]+\.", ""),
    (r"We've seen the line move [^.]+\.", ""),
    (r"Line movement suggests [^.]+\.", ""),
    (r"The early line was [^.]+, but it's moved to [^.]+\.", ""),
]

# Durant team fixes
DURANT_FIXES = [
    (r"Durant['\"]?s? (time |tenure |)with (the )?Suns", "Durant's time with the Rockets"),
    (r"Durant.{0,20}(Phoenix|Suns)", lambda m: m.group(0).replace("Phoenix", "Houston").replace("Suns", "Rockets")),
    (r"Kevin Durant.{0,30}(Phoenix|Suns)", lambda m: m.group(0).replace("Phoenix", "Houston").replace("Suns", "Rockets")),
]

def fix_file(filepath):
    """Fix line movement and Durant references in a single file."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        original = content

        # Fix Durant references
        for pattern, replacement in DURANT_FIXES:
            if callable(replacement):
                content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
            else:
                content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)

        # For line movement patterns, we need to be more careful
        # Only remove if it's in educational content, not if it's a general statement
        # Skip certain files that are educational content about how betting works
        skip_files = [
            'how-betting-lines-move.html',
            'betting-101.html',
            'betting-glossary.html',
            'line-shopping-betting-strategy.html',
        ]

        filename = os.path.basename(filepath)
        if filename not in skip_files:
            for pattern, replacement in LINE_MOVEMENT_PATTERNS:
                content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)

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
        dirs[:] = [d for d in dirs if d != '.git']

        for filename in files:
            if filename.endswith('.html'):
                filepath = os.path.join(root, filename)
                if fix_file(filepath):
                    print(f"Fixed: {filepath}")
                    fixed_count += 1

    print(f"\nTotal files fixed: {fixed_count}")

if __name__ == "__main__":
    main()
