#!/usr/bin/env python3
"""
Remove betting picks/recommendations from NBA sports pages.
Keep the analysis, remove explicit betting advice.
"""

import os
import re
import glob

REPO_PATH = r'C:\Users\Nima\nimadamus.github.io'

# Patterns to remove (entire paragraph containing these)
PICK_PATTERNS = [
    # Bold pick lines
    r'<p>\s*\*\*\s*(LEAN|Take|The play):.*?\*\*\s*</p>',
    r'<p>\s*\*\*(LEAN|Take):.*?</p>',
    # Lines that are ONLY picks (short recommendation lines)
    r'<p>\*\*Take the.*?\*\*</p>',
    r'<p>\*\*LEAN:.*?\*\*</p>',
]

# Patterns to clean from within paragraphs (but keep the rest of the paragraph)
INLINE_PICK_PATTERNS = [
    # Bold inline picks at end of paragraphs
    (r'\s*\*\*LEAN:\s*[^*]+\*\*', ''),
    (r'\s*\*\*Take:\s*[^*]+\*\*', ''),
    (r'\s*\*\*The play:\s*[^*]+\*\*', ''),
    # Remove "Take the X" recommendation sentences
    (r'\s*Take the \w+ [-+]?\d+\.?\d*\s*and\s+hammer\s+the\s+(over|under)\.?', ''),
    (r'\s*Take the (over|under) \d+\.?\d*\s+and don\'t think twice about it\.?', ''),
    (r'\s*Take the (over|under) \d+\.?\d*\.?', ''),
    (r'\s*hammer the (over|under)\.?', ''),
    (r'\s*crush the spread at [-+]?\d+\.?\d*\.?', ''),
    # Recommendation phrases to soften
    (r'\bTake the (\w+) to cover\b', r'The \1 could cover'),
    (r'\bTake the (\w+) and\b', r'The \1 could'),
    (r'\bTake the (\w+)\b(?!\s+(time|opportunity|over|under))', r'The \1 are worth watching'),
]

def process_file(filepath):
    """Process a single NBA HTML file to remove picks."""
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    original = content

    # Remove standalone pick paragraphs
    for pattern in PICK_PATTERNS:
        content = re.sub(pattern, '', content, flags=re.IGNORECASE | re.DOTALL)

    # Clean inline picks from paragraphs
    for pattern, replacement in INLINE_PICK_PATTERNS:
        content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)

    # Clean up empty paragraphs that might result
    content = re.sub(r'<p>\s*</p>', '', content)

    # Clean up multiple newlines
    content = re.sub(r'\n{3,}', '\n\n', content)

    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def main():
    """Process all NBA pages."""
    nba_files = glob.glob(os.path.join(REPO_PATH, 'nba*.html'))

    # Exclude non-content pages
    exclude = ['nba-calendar.html', 'nba-records.html']
    nba_files = [f for f in nba_files if os.path.basename(f) not in exclude]

    modified_count = 0
    for filepath in sorted(nba_files):
        filename = os.path.basename(filepath)
        if process_file(filepath):
            print(f"Modified: {filename}")
            modified_count += 1
        else:
            print(f"No changes: {filename}")

    print(f"\nTotal files modified: {modified_count}")

if __name__ == '__main__':
    main()
