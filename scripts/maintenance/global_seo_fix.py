import os
import re
from bs4 import BeautifulSoup

def fix_html_file(file_path):
    print(f"Processing {file_path}...")
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    soup = BeautifulSoup(content, 'html.parser')
    changed = False

    # 1. Add Canonical Tag if missing
    if not soup.find('link', rel='canonical'):
        filename = os.path.basename(file_path)
        canonical_url = f"https://www.betlegendpicks.com/{filename}"
        if filename == 'index.html':
            canonical_url = "https://www.betlegendpicks.com/"
        
        canonical_tag = soup.new_tag('link', rel='canonical', href=canonical_url)
        if soup.head:
            soup.head.insert(0, canonical_tag)
            changed = True
        else:
            # If no head, maybe it's a stub, but let's try to be safe
            pass

    # 2. Fix Alt-Text Stuffing
    for img in soup.find_all('img'):
        alt = img.get('alt', '')
        if len(alt) > 150:
            # Trim to first sentence or first 120 chars
            new_alt = alt.split('.')[0]
            if len(new_alt) > 120:
                new_alt = new_alt[:117] + "..."
            img['alt'] = new_alt
            print(f"  Trimming alt text on {img.get('src')}")
            changed = True

    # 3. Ensure Viewport and Charset (basic optimization)
    if soup.head:
        if not soup.find('meta', charset=True):
            charset_tag = soup.new_tag('meta')
            charset_tag['charset'] = 'utf-8'
            soup.head.insert(0, charset_tag)
            changed = True
        if not soup.find('meta', attrs={'name': 'viewport'}):
            viewport_tag = soup.new_tag('meta')
            viewport_tag['name'] = 'viewport'
            viewport_tag['content'] = 'width=device-width, initial-scale=1.0'
            soup.head.append(viewport_tag)
            changed = True

    if changed:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))
        return True
    return False

def main():
    root_dir = 'C:/Users/Nima/nimadamus.github.io'
    for filename in os.listdir(root_dir):
        if filename.endswith('.html'):
            file_path = os.path.join(root_dir, filename)
            try:
                fix_html_file(file_path)
            except Exception as e:
                print(f"Error processing {filename}: {e}")

if __name__ == "__main__":
    main()
