#!/usr/bin/env python3
"""
Repoint every "Featured Game" nav link to the STABLE permanent hub
`/featured-game-of-the-day.html` (which auto-redirects to the latest featured
game). This kills the root cause of stale nav targets: previously each page's
nav was frozen to whatever dated featured page was newest when the file was
last touched, so old pages pointed at old featured games forever.

Anchor-aware: only rewrites the href of an <a> whose visible text begins with
"Featured Game". Leaves hero badges / headings like "Featured Game of the Day -
May 19" untouched (those are not anchors and are not followed by '<').
"""
import os
import re
import glob

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STABLE = '/featured-game-of-the-day.html'

# <a ...href="X"...>Featured Game<   (text immediately followed by < of <span> or </a>)
PATTERN = re.compile(r'(<a\b[^>]*?href=")([^"]*)("[^>]*>\s*Featured Game<)')

def fix(path):
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    def repl(m):
        return m.group(1) + STABLE + m.group(3)

    new = PATTERN.sub(repl, content)
    if new != content:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new)
        return PATTERN.findall(content) and 1 or 0
    return 0

def main():
    files = glob.glob(os.path.join(REPO, '**', '*.html'), recursive=True)
    changed = 0
    for fp in files:
        if fix(fp):
            changed += 1
    print(f"Repointed Featured Game nav in {changed} file(s) -> {STABLE}")

if __name__ == '__main__':
    main()
