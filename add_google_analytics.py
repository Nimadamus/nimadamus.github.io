import os
import glob
import re

# Directory containing HTML files
directory = r'C:\Users\Nima\Desktop\betlegendpicks'

# Google Analytics tracking code
ga_code = '''<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-QS8L5TDNLY"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());

  gtag('config', 'G-QS8L5TDNLY');
</script>
'''

# Get all HTML files
html_files = glob.glob(os.path.join(directory, '*.html'))

# Track results
updated_files = []
skipped_files = []
already_has_ga = []

for filepath in html_files:
    filename = os.path.basename(filepath)

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check if GA is already present
        if 'G-QS8L5TDNLY' in content or 'gtag' in content:
            already_has_ga.append(filename)
            continue

        # Find </head> tag and insert GA code before it
        if '</head>' in content:
            # Insert GA code right before </head>
            new_content = content.replace('</head>', ga_code + '\n</head>')

            # Write back to file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)

            updated_files.append(filename)
            print(f"[+] Added GA to: {filename}")
        else:
            skipped_files.append(filename)
            print(f"[!] No </head> tag found in: {filename}")

    except Exception as e:
        print(f"[!] Error processing {filename}: {e}")

print(f"\n--- Summary ---")
print(f"Added GA: {len(updated_files)} files")
print(f"Already has GA: {len(already_has_ga)} files")
print(f"Skipped (no </head>): {len(skipped_files)} files")

if updated_files:
    print(f"\nUpdated files:")
    for f in updated_files:
        print(f"  - {f}")
