"""
COMPREHENSIVE PLACEHOLDER REMOVAL SCRIPT
Removes ALL placeholder content from ALL HTML files in the repository.
This script will eliminate: N/A, TBD, TBA, coming soon, and similar patterns.
"""

import os
import re

REPO_PATH = r'C:\Users\Nima\nimadamus.github.io'

# Patterns to remove or replace
PLACEHOLDER_PATTERNS = [
    # Remove "N/A" in stat values - replace with dash or empty
    (r'>N/A<', '><'),
    (r'"N/A"', '""'),
    (r"'N/A'", "''"),
    (r'\bN/A\b', ''),

    # Remove TBD/TBA
    (r'>TBD<', '><'),
    (r'>TBA<', '><'),
    (r'"TBD"', '""'),
    (r'"TBA"', '""'),
    (r"'TBD'", "''"),
    (r"'TBA'", "''"),

    # Remove "coming soon" variations
    (r'[Cc]oming soon\.?', ''),
    (r'[Aa]nalysis coming soon\.?', ''),
    (r'[Mm]atchup analysis coming soon\.?', ''),
    (r'[Pp]review coming soon\.?', ''),
    (r'[Aa]nalysis pending\.?', ''),

    # Remove placeholder messages in paragraphs
    (r'<p>\s*Matchup analysis coming soon\.\s*</p>', ''),
    (r'<p>\s*Analysis coming soon\.\s*</p>', ''),
    (r'<p>\s*Preview coming soon\.\s*</p>', ''),
    (r'<p>\s*Coming soon\.\s*</p>', ''),

    # Clean up empty paragraphs that result
    (r'<p>\s*</p>', ''),

    # Clean up stat items with empty values - keep structure but show dash
    (r'<span class="value"></span>', '<span class="value">-</span>'),
    (r'<div class="stat-value"></div>', '<div class="stat-value">-</div>'),
]

# Files/directories to skip
SKIP_DIRS = ['.git', 'node_modules', '__pycache__']
SKIP_FILES = ['remove_all_placeholders.py']  # Don't modify self

def clean_file(filepath):
    """Remove all placeholder content from a single file."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        original = content

        # Apply all replacement patterns
        for pattern, replacement in PLACEHOLDER_PATTERNS:
            content = re.sub(pattern, replacement, content)

        # Only write if changes were made
        if content != original:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
    except Exception as e:
        print(f"  Error processing {filepath}: {e}")
        return False

def main():
    print("=" * 70)
    print("COMPREHENSIVE PLACEHOLDER REMOVAL")
    print("=" * 70)
    print(f"\nScanning: {REPO_PATH}")

    files_processed = 0
    files_modified = 0

    for root, dirs, files in os.walk(REPO_PATH):
        # Skip certain directories
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

        for filename in files:
            if filename.endswith('.html') and filename not in SKIP_FILES:
                filepath = os.path.join(root, filename)
                files_processed += 1

                if clean_file(filepath):
                    files_modified += 1
                    rel_path = os.path.relpath(filepath, REPO_PATH)
                    print(f"  [FIXED] {rel_path}")

    print("\n" + "=" * 70)
    print(f"COMPLETE: {files_modified}/{files_processed} files modified")
    print("=" * 70)

    if files_modified > 0:
        print("\nRun these commands to commit:")
        print("  git add -A")
        print('  git commit -m "Remove ALL placeholder content from HTML files"')
        print("  git push")

if __name__ == "__main__":
    main()
