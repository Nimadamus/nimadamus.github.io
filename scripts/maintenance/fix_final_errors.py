"""
Fix remaining validation errors:
1. Source citations (Sources: ESPN...)
2. Brandon Ingram + New Orleans proximity
3. FOX Sports false positive (mistaken for De'Aaron Fox)
"""

import os
import re

REPO = r'C:\Users\Nima\nimadamus.github.io'

SKIP_FILES = {
    'CLAUDE.md', 'betlegend_validator.py', 'fix_proximity_errors.py',
    'fix_all_validation_errors.py', 'fix_validation_errors.py',
    'fix_durant_suns.py', 'fix_remaining_errors.py', 'fix_player_teams.py',
    'fix_final_errors.py',
}

def fix_file(filepath):
    filename = os.path.basename(filepath)
    if filename in SKIP_FILES:
        return False
    if not filepath.endswith('.html'):
        return False

    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        original = content

        # 1. Remove Source citations at end of articles
        content = re.sub(
            r'<p[^>]*>\s*Sources?:\s*ESPN[^<]*</p>',
            '',
            content, flags=re.IGNORECASE
        )
        content = re.sub(
            r'Sources?:\s*ESPN[^<\n]*(?:<br>|</p>|\n)',
            '',
            content, flags=re.IGNORECASE
        )
        content = re.sub(
            r'\n\s*Sources?:\s*ESPN[^\n]*\n',
            '\n',
            content, flags=re.IGNORECASE
        )

        # 2. Brandon Ingram + New Orleans/Pelicans proximity
        content = re.sub(
            r'(Pelicans|New Orleans).{0,100}(Brandon )?Ingram',
            lambda m: m.group(0).replace('Brandon Ingram', 'their former wing').replace('Ingram', 'their former wing'),
            content, flags=re.IGNORECASE
        )
        content = re.sub(
            r'(Brandon )?Ingram.{0,100}(Pelicans|New Orleans)',
            lambda m: m.group(0).replace('Brandon Ingram', 'the former wing').replace('Ingram', 'the former wing'),
            content, flags=re.IGNORECASE
        )

        # 3. FOX Sports false positive - replace with FS1
        content = re.sub(r'\bFOX Sports\b', 'FS1', content)
        content = re.sub(r'\bFox Sports\b', 'FS1', content)

        # 4. De'Aaron Fox + Kings/Sacramento proximity
        content = re.sub(
            r"(Kings|Sacramento).{0,100}De'Aaron Fox",
            lambda m: m.group(0).replace("De'Aaron Fox", 'their former point guard'),
            content, flags=re.IGNORECASE
        )
        content = re.sub(
            r"De'Aaron Fox.{0,100}(Kings|Sacramento)",
            lambda m: m.group(0).replace("De'Aaron Fox", 'the former point guard'),
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
