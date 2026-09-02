"""
Injects mobile-optimize.css link into all HTML files.
Safe: ONLY adds a single <link> tag before </head>.
Never removes, modifies, or deletes any existing content.
Skips frozen pages (kelly-criterion.html, kelly-simulation.html).
"""
import os

REPO = r'C:\Users\Nima\nimadamus.github.io'
LINK_TAG = '<link rel="stylesheet" href="/mobile-optimize.css" media="screen">'
FROZEN_FILES = {'kelly-criterion.html', 'kelly-simulation.html'}


def inject_css_link(filepath):
    """Insert mobile CSS link before </head> if not already present."""
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # Skip if already injected
    if 'mobile-optimize.css' in content:
        return 'already'

    # Find </head> and insert before it
    head_close = content.find('</head>')
    if head_close == -1:
        return 'no_head'

    new_content = content[:head_close] + LINK_TAG + '\n' + content[head_close:]

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)

    return 'injected'


def main():
    injected = 0
    already = 0
    skipped = 0
    no_head = 0

    for root, dirs, files in os.walk(REPO):
        dirs[:] = [d for d in dirs if d not in ('.git', 'node_modules', '__pycache__')]
        for f in files:
            if not f.endswith('.html'):
                continue
            if f in FROZEN_FILES:
                skipped += 1
                print(f'  SKIPPED (frozen): {f}')
                continue

            filepath = os.path.join(root, f)
            result = inject_css_link(filepath)

            if result == 'injected':
                injected += 1
                print(f'  Injected: {os.path.relpath(filepath, REPO)}')
            elif result == 'already':
                already += 1
            elif result == 'no_head':
                no_head += 1
                print(f'  No </head> tag: {os.path.relpath(filepath, REPO)}')

    print(f'\nDone: {injected} files updated, {already} already had it, {skipped} frozen, {no_head} no head tag')


if __name__ == '__main__':
    main()
