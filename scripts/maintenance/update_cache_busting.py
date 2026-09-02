import re
import time

timestamp = int(time.time())

pages = ['soccer-records.html', 'nhl-records.html']

for filename in pages:
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()

    # Update the cache-busting timestamp
    old_pattern = r"fetch\('all-records\.json\?v=\d+'\)"
    new_url = f"fetch('all-records.json?v={timestamp}')"

    content = re.sub(old_pattern, new_url, content)

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"Updated {filename} with timestamp {timestamp}")

print("Done!")
