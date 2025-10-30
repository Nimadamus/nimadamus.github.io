import os
import glob

# Directory containing HTML files
directory = r'C:\Users\Nima\Desktop\betlegendpicks'

# Pattern to find and replace
old_pattern = '''            <a href="bestonlinesportsbook.html">Best Sportsbook</a>
            <a href="betting-101.html">Betting 101</a>'''

new_pattern = '''            <a href="bestonlinesportsbook.html">Best Sportsbook</a>
            <a href="betting-glossary.html">Betting Glossary</a>
            <a href="betting-101.html">Betting 101</a>'''

# Get all HTML files
html_files = glob.glob(os.path.join(directory, '*.html'))

# Track results
updated_files = []
skipped_files = []

for filepath in html_files:
    filename = os.path.basename(filepath)

    # Skip the glossary page itself
    if filename == 'betting-glossary.html':
        continue

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check if pattern exists and glossary link is not already there
        if old_pattern in content and 'betting-glossary.html' not in content:
            # Replace the pattern
            new_content = content.replace(old_pattern, new_pattern)

            # Write back to file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)

            updated_files.append(filename)
            print(f"[+] Updated: {filename}")
        else:
            skipped_files.append(filename)

    except Exception as e:
        print(f"[!] Error processing {filename}: {e}")

print(f"\n--- Summary ---")
print(f"Updated: {len(updated_files)} files")
print(f"Skipped: {len(skipped_files)} files")
print(f"\nUpdated files:")
for f in updated_files:
    print(f"  - {f}")
