#!/usr/bin/env python3
"""
Add Sharp vs Square navigation link to all HTML pages
Inserts after Handicapping Hub link in the nav menu
"""

import os
import re

REPO = r'C:\Users\Nima\nimadamus.github.io'

def add_nav_link():
    """Add Sharp vs Square nav link to all HTML pages"""
    updated_count = 0
    skipped_count = 0

    for root, dirs, files in os.walk(REPO):
        # Skip .git directory
        dirs[:] = [d for d in dirs if d != '.git']

        for filename in files:
            if not filename.endswith('.html'):
                continue

            filepath = os.path.join(root, filename)

            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                # Skip if already has Sharp vs Square link
                if 'sharp-vs-square.html' in content:
                    skipped_count += 1
                    continue

                original_content = content
                modified = False

                # Pattern 1: Full format with class="hub-btn" (index.html style)
                # <a href="handicapping-hub.html" class="hub-btn">Handicapping Hub</a>
                pattern1 = r'(<a\s+href="handicapping-hub\.html"\s+class="hub-btn">Handicapping Hub</a>)'
                if re.search(pattern1, content):
                    link = '''
                <!-- Sharp vs Square -->
                <a href="sharp-vs-square.html" class="hub-btn" style="background: linear-gradient(135deg, #00d4ff, #0099cc);">Sharp vs Square</a>'''
                    content = re.sub(pattern1, r'\1' + link, content)
                    modified = True

                # Pattern 2: Inline nav with style (sports pages style)
                # <a href="handicapping-hub.html" style="background:linear-gradient(...);">Handicapping Hub</a>
                if not modified:
                    pattern2 = r'(<a\s+href="handicapping-hub\.html"\s+style="[^"]*">Handicapping Hub</a>)'
                    if re.search(pattern2, content):
                        link = '\n<a href="sharp-vs-square.html" style="background:linear-gradient(135deg,#00d4ff,#0099cc);color:#fff;border-radius:8px;">Sharp vs Square</a>'
                        content = re.sub(pattern2, r'\1' + link, content)
                        modified = True

                # Pattern 3: Simple link (fallback)
                # <a href="handicapping-hub.html">Handicapping Hub</a>
                if not modified:
                    pattern3 = r'(<a\s+href="handicapping-hub\.html">Handicapping Hub</a>)'
                    if re.search(pattern3, content):
                        link = '\n<a href="sharp-vs-square.html">Sharp vs Square</a>'
                        content = re.sub(pattern3, r'\1' + link, content)
                        modified = True

                if modified and content != original_content:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
                    updated_count += 1
                    print(f"Updated: {filename}")

            except Exception as e:
                print(f"Error processing {filename}: {e}")

    print()
    print(f"Updated: {updated_count} files")
    print(f"Skipped (already has link): {skipped_count} files")


if __name__ == '__main__':
    print("Adding Sharp vs Square navigation link to all pages...")
    print("=" * 60)
    add_nav_link()
    print("=" * 60)
    print("Done!")
