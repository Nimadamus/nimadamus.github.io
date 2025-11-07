import re

pages = [
    'nba-records.html',
    'nhl-records.html',
    'ncaaf-records.html',
    'ncaab-records.html',
    'soccer-records.html',
    'betlegend-verified-records.html'
]

for filename in pages:
    print(f"\nProcessing {filename}...")

    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find the intro section block
    section_pattern = r'(<section style="background: rgba\(0, 224, 255, 0\.05\).*?</section>)\s*'
    match = re.search(section_pattern, content, re.DOTALL)

    if not match:
        print(f"  No intro section found in {filename}")
        continue

    intro_section = match.group(1)
    print(f"  Found intro section ({len(intro_section)} chars)")

    # Remove the section from its current location
    content_without_section = re.sub(section_pattern, '', content, count=1, flags=re.DOTALL)

    # Find the location to insert at bottom (before closing </div></body>)
    # Look for the main container closing div before </body>
    insert_pattern = r'(</div>\s*</body>)'

    if not re.search(insert_pattern, content_without_section):
        print(f"  Could not find insertion point in {filename}")
        continue

    # Insert the section before the closing tags, with spacing
    new_content = re.sub(
        insert_pattern,
        f'\n\n{intro_section}\n\n\\1',
        content_without_section,
        count=1
    )

    # Verify nav bar is still present
    if '<nav' not in new_content:
        print(f"  ERROR: Nav bar missing after transformation!")
        continue

    # Verify section was moved, not duplicated
    section_count = new_content.count('<section style="background: rgba(0, 224, 255, 0.05)')
    if section_count != 1:
        print(f"  ERROR: Section appears {section_count} times (should be 1)")
        continue

    # Write the updated content
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"  * Successfully moved intro section to bottom")

print("\nDone! Intro sections moved to bottom of all pages.")
