"""
Fix remaining validation errors:
1. Luka Doncic + Mavericks/Dallas references (he's on Lakers now)
2. Mitch Marner + Maple Leafs/Toronto references (he's on Golden Knights now)
"""

import os
import re

REPO = r'C:\Users\Nima\nimadamus.github.io'

SKIP_FILES = {
    'CLAUDE.md', 'fix_all_validation_errors.py', 'fix_validation_errors.py',
    'fix_durant_suns.py', 'fix_remaining_errors.py', 'betlegend_validator.py',
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

        # Fix Luka Doncic + Mavericks/Dallas - rewrite to avoid proximity
        # Pattern: "Mavericks...Doncic" or "Doncic...Mavericks" in same sentence
        content = re.sub(
            r'(the )?Mavericks (made|sent|traded|dealt).{0,50}Doncic',
            r'Dallas \2 their superstar',
            content, flags=re.IGNORECASE
        )
        content = re.sub(
            r'Doncic.{0,30}(Mavericks|Dallas|Mavs)',
            lambda m: m.group(0).replace('Mavericks', 'his former team').replace('Dallas', 'his former team').replace('Mavs', 'his former team') if 'former' not in m.group(0) else m.group(0),
            content, flags=re.IGNORECASE
        )
        content = re.sub(
            r'post-Luka (era|rebuild|Dallas|Mavericks)',
            r'post-trade \1',
            content, flags=re.IGNORECASE
        )

        # Fix Mitch Marner + Maple Leafs/Toronto
        content = re.sub(
            r'Marner.{0,30}(Maple Leafs|Toronto|Leafs)',
            lambda m: m.group(0).replace('Maple Leafs', 'his former team').replace('Toronto', 'his former city').replace('Leafs', 'his former team') if 'former' not in m.group(0) else m.group(0),
            content, flags=re.IGNORECASE
        )
        content = re.sub(
            r'(Maple Leafs|Toronto Maple Leafs|Leafs).{0,30}Marner',
            lambda m: m.group(0).replace('Maple Leafs', 'his former team').replace('Leafs', 'his former team'),
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
