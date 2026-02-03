"""
Fix source citations in articles.
Pattern: <div class="data-source">Sources: ESPN, Team Stats, Official League Data</div>
"""

import os
import re

REPO = r'C:\Users\Nima\nimadamus.github.io'

def fix_file(filepath):
    if not filepath.endswith('.html'):
        return False

    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        original = content

        # Remove data-source divs with Sources: content
        content = re.sub(
            r'<div class="data-source">Sources?:[^<]*</div>\s*',
            '',
            content, flags=re.IGNORECASE
        )

        # Also remove any standalone Sources: lines
        content = re.sub(
            r'\n\s*Sources?:\s*ESPN[^\n<]*(?:\n|</)',
            '\n',
            content, flags=re.IGNORECASE
        )

        if content != original:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False

    except Exception as e:
        print(f"Error: {filepath}: {e}")
        return False

def main():
    fixed = 0
    for root, dirs, files in os.walk(REPO):
        dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules']]
        for f in files:
            path = os.path.join(root, f)
            if fix_file(path):
                print(f"Fixed: {path}")
                fixed += 1
    print(f"\nTotal fixed: {fixed}")

if __name__ == "__main__":
    main()
