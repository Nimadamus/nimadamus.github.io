"""
Fix player-old team proximity errors.
The validator flags ANY mention of player + old team in same paragraph.
Need to remove player names when discussing their old teams.
"""

import os
import re

REPO = r'C:\Users\Nima\nimadamus.github.io'

SKIP_FILES = {
    'CLAUDE.md', 'betlegend_validator.py', 'fix_proximity_errors.py',
    'fix_all_validation_errors.py', 'fix_validation_errors.py',
    'fix_durant_suns.py', 'fix_remaining_errors.py', 'fix_player_teams.py',
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

        # Butler + Heat/Miami proximity - remove Butler references
        content = re.sub(
            r'since (the )?Butler trade to Golden State',
            'since their February roster overhaul',
            content, flags=re.IGNORECASE
        )
        content = re.sub(
            r'since (the )?(Jimmy )?Butler (trade|deal|was traded)',
            'since their February roster changes',
            content, flags=re.IGNORECASE
        )
        content = re.sub(
            r'(Heat|Miami).{0,100}(Jimmy )?Butler',
            lambda m: m.group(0).replace('Jimmy Butler', 'their star').replace('Butler', 'their star')
            if 'traded' not in m.group(0).lower() and 'former' not in m.group(0).lower()
            else m.group(0).replace('Jimmy Butler', 'their former star').replace('Butler', 'their former star'),
            content, flags=re.IGNORECASE
        )
        content = re.sub(
            r'(Jimmy )?Butler.{0,100}(Heat|Miami)',
            lambda m: m.group(0).replace('Jimmy Butler', 'the former star').replace('Butler', 'the former star'),
            content, flags=re.IGNORECASE
        )

        # Fox + Kings/Sacramento proximity
        content = re.sub(
            r'since (trading )?(De\'?Aaron )?Fox to San Antonio',
            'since their February roster overhaul',
            content, flags=re.IGNORECASE
        )
        content = re.sub(
            r'(Kings|Sacramento).{0,100}(De\'?Aaron )?Fox',
            lambda m: m.group(0).replace("De'Aaron Fox", 'their former point guard').replace('Fox', 'their former point guard'),
            content, flags=re.IGNORECASE
        )
        content = re.sub(
            r'(De\'?Aaron )?Fox.{0,100}(Kings|Sacramento)',
            lambda m: m.group(0).replace("De'Aaron Fox", 'the former point guard').replace('Fox', 'the former point guard'),
            content, flags=re.IGNORECASE
        )

        # LaVine + Bulls/Chicago proximity
        content = re.sub(
            r'since (the )?(Zach )?LaVine trade to Sacramento',
            'since their February roster changes',
            content, flags=re.IGNORECASE
        )
        content = re.sub(
            r'(Bulls|Chicago).{0,100}(Zach )?LaVine',
            lambda m: m.group(0).replace('Zach LaVine', 'their former star').replace('LaVine', 'their former star'),
            content, flags=re.IGNORECASE
        )

        # Luka + Mavericks/Dallas proximity
        content = re.sub(
            r'(Mavericks|Dallas|Mavs).{0,100}(Luka |Doncic)',
            lambda m: m.group(0).replace('Luka ', '').replace('Doncic', 'their former superstar'),
            content, flags=re.IGNORECASE
        )
        content = re.sub(
            r'(Luka |Doncic).{0,100}(Mavericks|Dallas|Mavs)',
            lambda m: m.group(0).replace('Luka ', '').replace('Doncic', 'the former superstar'),
            content, flags=re.IGNORECASE
        )

        # Durant + Suns/Phoenix proximity
        content = re.sub(
            r'(Suns|Phoenix).{0,100}(Kevin )?Durant',
            lambda m: m.group(0).replace('Kevin Durant', 'their former star').replace('Durant', 'their former star'),
            content, flags=re.IGNORECASE
        )
        content = re.sub(
            r'(Kevin )?Durant.{0,100}(Suns|Phoenix)',
            lambda m: m.group(0).replace('Kevin Durant', 'the former star').replace('Durant', 'the former star'),
            content, flags=re.IGNORECASE
        )

        # Ingram + Pelicans/New Orleans proximity
        content = re.sub(
            r'(Pelicans|New Orleans).{0,100}(Brandon )?Ingram',
            lambda m: m.group(0).replace('Brandon Ingram', 'their former wing').replace('Ingram', 'their former wing'),
            content, flags=re.IGNORECASE
        )

        # Marner + Maple Leafs/Toronto proximity
        content = re.sub(
            r'(Maple Leafs|Leafs|Toronto).{0,100}(Mitch )?Marner',
            lambda m: m.group(0).replace('Mitch Marner', 'their former winger').replace('Marner', 'their former winger'),
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
