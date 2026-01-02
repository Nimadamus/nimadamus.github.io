#!/usr/bin/env python3
"""
Fix calendar CSS across all sports pages.
Makes has-content subtle and only today prominent.
"""

import os
import re

REPO_PATH = r'C:\Users\Nima\nimadamus.github.io'

# Old CSS pattern (with various formats)
OLD_PATTERNS = [
    # Pattern 1: has-content with full styling
    (r'\.cal-day\.has-content\{background:rgba\(253,80,0,0\.15\);color:var\(--accent-orange\);cursor:pointer;font-weight:600;border:1px solid rgba\(253,80,0,0\.3\)\}\s*\.cal-day\.has-content:hover\{background:rgba\(253,80,0,0\.3\);transform:scale\(1\.1\)\}\s*\.cal-day\.today\{[^}]+\}',
     '.cal-day.has-content{cursor:pointer}\n.cal-day.has-content:hover{background:rgba(253,80,0,0.2);color:var(--accent-orange)}\n.cal-day.today{background:rgba(253,80,0,0.25);color:var(--accent-orange);font-weight:600;border:2px solid var(--accent-gold)}'),
]

# Simpler replacement approach
OLD_CSS = '.cal-day.has-content{background:rgba(253,80,0,0.15);color:var(--accent-orange);cursor:pointer;font-weight:600;border:1px solid rgba(253,80,0,0.3)}'
NEW_CSS = '.cal-day.has-content{cursor:pointer}'

OLD_HOVER = '.cal-day.has-content:hover{background:rgba(253,80,0,0.3);transform:scale(1.1)}'
NEW_HOVER = '.cal-day.has-content:hover{background:rgba(253,80,0,0.2);color:var(--accent-orange)}'

# Various today patterns to replace
TODAY_PATTERNS = [
    ('.cal-day.today{box-shadow:0 0 0 2px var(--accent-gold)}', '.cal-day.today{background:rgba(253,80,0,0.25);color:var(--accent-orange);font-weight:600;border:2px solid var(--accent-gold)}'),
    ('.cal-day.today{position:relative}', '.cal-day.today{background:rgba(253,80,0,0.25);color:var(--accent-orange);font-weight:600;border:2px solid var(--accent-gold)}'),
]

def fix_file(filepath):
    """Fix calendar CSS in a single file."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        original = content

        # Replace has-content
        content = content.replace(OLD_CSS, NEW_CSS)

        # Replace hover
        content = content.replace(OLD_HOVER, NEW_HOVER)

        # Replace today patterns
        for old, new in TODAY_PATTERNS:
            content = content.replace(old, new)

        if content != original:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
    except Exception as e:
        print(f"  ERROR: {filepath}: {e}")
        return False

def main():
    print("=" * 60)
    print("Fixing Calendar CSS Across All Sports Pages")
    print("=" * 60)

    fixed_count = 0

    for root, dirs, files in os.walk(REPO_PATH):
        # Skip .git directory
        dirs[:] = [d for d in dirs if d != '.git']

        for filename in files:
            if filename.endswith('.html'):
                filepath = os.path.join(root, filename)
                if fix_file(filepath):
                    print(f"  Fixed: {filename}")
                    fixed_count += 1

    print("=" * 60)
    print(f"Fixed {fixed_count} files")
    print("=" * 60)

if __name__ == '__main__':
    main()
