"""
Fix player-team references where players are mentioned with old teams.
Key trades to update:
- Luka Doncic: Mavericks -> Lakers (Feb 2025)
- Jimmy Butler: Heat -> Warriors (Feb 2025)
- Zach LaVine: Bulls -> Kings (Feb 2025)
- De'Aaron Fox: Kings -> Spurs (Feb 2025)
- Brandon Ingram: Pelicans -> Raptors (Feb 2025)
"""

import os
import re

REPO = r'C:\Users\Nima\nimadamus.github.io'

SKIP_FILES = {
    'CLAUDE.md', 'fix_all_validation_errors.py', 'fix_validation_errors.py',
    'fix_durant_suns.py', 'fix_remaining_errors.py', 'fix_player_teams.py',
    'betlegend_validator.py', 'generate_nba_analysis.py',
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

        # Luka Doncic - now on Lakers
        # Replace mentions of Luka with Mavericks/Dallas
        content = re.sub(
            r'Dallas.{0,50}Luka (Doncic)?',
            lambda m: "Dallas's roster (post-trade)" if 'traded' not in m.group(0).lower() else m.group(0),
            content, flags=re.IGNORECASE
        )
        content = re.sub(
            r'Luka (Doncic )?doing everything.{0,50}(Mavs|Mavericks|Dallas)',
            "Luka Doncic doing everything humanly possible for the Lakers",
            content, flags=re.IGNORECASE
        )
        # Pattern: "Luka" near "Dallas" or "Mavericks" or "Mavs"
        def fix_luka(text):
            if re.search(r'Luka|Doncic', text, re.IGNORECASE):
                # If Luka and Dallas/Mavericks/Mavs are mentioned together, rewrite
                if re.search(r'Dallas|Mavericks|Mavs', text, re.IGNORECASE):
                    # Don't rewrite if it's about the trade itself
                    if 'traded' in text.lower() or 'former' in text.lower():
                        return text
                    # Replace Dallas/Mavericks/Mavs context with Lakers
                    text = re.sub(r"(Dallas|Mavericks|Mavs)'?s?", "the Lakers", text, flags=re.IGNORECASE)
            return text

        # Apply to paragraphs containing both Luka and Dallas/Mavs
        content = re.sub(r'<p[^>]*>[^<]*(?:Luka|Doncic)[^<]*(?:Dallas|Mavericks|Mavs)[^<]*</p>',
                        lambda m: fix_luka(m.group(0)), content, flags=re.IGNORECASE)
        content = re.sub(r'<p[^>]*>[^<]*(?:Dallas|Mavericks|Mavs)[^<]*(?:Luka|Doncic)[^<]*</p>',
                        lambda m: fix_luka(m.group(0)), content, flags=re.IGNORECASE)

        # Jimmy Butler - now on Warriors
        content = re.sub(
            r'(Miami|Heat).{0,50}Jimmy Butler',
            lambda m: m.group(0).replace('Jimmy Butler', 'their roster') if 'traded' not in m.group(0).lower() and 'former' not in m.group(0).lower() else m.group(0),
            content, flags=re.IGNORECASE
        )
        content = re.sub(
            r'Jimmy Butler.{0,50}(Miami|Heat)',
            lambda m: m.group(0).replace('Miami', 'Golden State').replace('Heat', 'Warriors') if 'traded' not in m.group(0).lower() and 'former' not in m.group(0).lower() else m.group(0),
            content, flags=re.IGNORECASE
        )
        content = re.sub(
            r'post-Jimmy Butler',
            'post-trade',
            content, flags=re.IGNORECASE
        )
        content = re.sub(
            r'since (trading )?Jimmy Butler',
            'since the Butler trade',
            content, flags=re.IGNORECASE
        )

        # Zach LaVine - now on Kings
        content = re.sub(
            r'(Bulls|Chicago).{0,50}(Zach )?LaVine',
            lambda m: m.group(0).replace('LaVine', 'their current roster') if 'traded' not in m.group(0).lower() and 'former' not in m.group(0).lower() else m.group(0),
            content, flags=re.IGNORECASE
        )
        content = re.sub(
            r'(Zach )?LaVine.{0,50}(Bulls|Chicago)',
            lambda m: m.group(0).replace('Bulls', 'Kings').replace('Chicago', 'Sacramento') if 'traded' not in m.group(0).lower() and 'former' not in m.group(0).lower() else m.group(0),
            content, flags=re.IGNORECASE
        )
        content = re.sub(
            r'since (trading )?Zach LaVine',
            'since the LaVine trade',
            content, flags=re.IGNORECASE
        )

        # Line movement cleanup
        content = re.sub(
            r'The line opened.{0,50}(and |)(dropped|moved)',
            lambda m: "The spread is currently set" if 'higher' not in m.group(0) else m.group(0).replace("The line opened higher and dropped", "The spread is"),
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
