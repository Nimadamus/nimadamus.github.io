#!/usr/bin/env python3
"""
Add navigation to final remaining important pages
"""
import sys
sys.path.insert(0, '.')
from add_navigation_all import add_navigation_to_file

# Pages that should get navigation (excluding placeholders and verification files)
important_pages = [
    'howitworks.html',  # How it works page - important
]

# These are either placeholders, verification files, or not BetLegend pages
skip_pages = [
    'google6f74b54ecd988601.html',  # Google verification
    'office-page2.html',  # Different site (RealAI Girls)
    'affiliates.html',  # Likely placeholder
    'bestbook.html',  # Placeholder
    'Best Online Sportsbook.html',  # Duplicate
    'email.html',  # Form page
    'FreeAlerts.html',  # Signup form
    'input.html',  # Form page
    'matchups.html',  # Placeholder
    'odds-live.html',  # Placeholder
    'odds.html',  # Placeholder
    'picks.html',  # Placeholder
    'smartbets.html',  # Placeholder
]

def main():
    updated = 0

    print("Adding navigation to important pages...")
    for page in important_pages:
        if add_navigation_to_file(page):
            updated += 1

    print(f"\n{'='*50}")
    print(f"Complete! Updated {updated} pages with navigation")
    print(f"Skipped {len(skip_pages)} placeholder/verification files")
    print(f"{'='*50}")

if __name__ == '__main__':
    main()
