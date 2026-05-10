import os
import re
from pathlib import Path
from bs4 import BeautifulSoup

def cleanup_site():
    site_dir = Path("C:/Users/Nima/nimadamus.github.io")
    base_url = "https://www.betlegendpicks.com"
    
    html_files = list(site_dir.rglob("*.html"))
    print(f"Starting cleanup of {len(html_files)} files...")
    
    processed = 0
    modified = 0
    
    for filepath in html_files:
        filename = filepath.name.lower()
        # Skip system/backup files
        if any(keyword in filename for keyword in ['backup', 'temp', 'test', '_']):
            continue
            
        try:
            # Use 'latin-1' or ignore errors to ensure we don't crash on encoded sports characters
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            if not content:
                continue

            soup = BeautifulSoup(content, 'html.parser')
            file_changed = False
            
            # 1. FIX CANONICAL
            rel_path = str(filepath.relative_to(site_dir)).replace('\\', '/')
            target_url = f"{base_url}/{rel_path}"
            if rel_path == "index.html":
                target_url = f"{base_url}/"
                
            head = soup.find('head')
            if head:
                existing_canonical = head.find('link', rel='canonical')
                if existing_canonical:
                    if existing_canonical.get('href') != target_url:
                        existing_canonical['href'] = target_url
                        file_changed = True
                else:
                    new_canonical = soup.new_tag('link', rel='canonical', href=target_url)
                    head.insert(0, new_canonical)
                    file_changed = True
            
            # 2. CLEAN ALT TEXT (Remove statistical keyword stuffing)
            for img in soup.find_all('img'):
                alt = img.get('alt', '')
                if alt and len(alt) > 100:
                    # Truncate at the first mention of betting technicals
                    cleaned_alt = re.split(r'moneyline|plus|minus|spread|total|over|under|units|betting|pick', alt, flags=re.IGNORECASE)[0].strip()
                    if not cleaned_alt or len(cleaned_alt) < 5:
                        cleaned_alt = "BetLegend Sports Analysis"
                    
                    if cleaned_alt != alt:
                        img['alt'] = cleaned_alt
                        file_changed = True
            
            # 3. ADD SITEMAP LINK TO FOOTER (Crawler discovery)
            footer = soup.find('footer')
            if footer:
                if not footer.find('a', href=re.compile(r'sitemap\.html')):
                    # Look for 'Learn' or 'Links' section to blend in
                    learn_div = footer.find(lambda tag: tag.name == 'div' and any(x in tag.get_text() for x in ['Learn', 'Resources', 'Network', 'Links']))
                    if learn_div:
                        new_link = soup.new_tag('a', href='sitemap.html')
                        new_link.string = "Archive Sitemap"
                        learn_div.append(new_link)
                        file_changed = True
                    else:
                        new_link = soup.new_tag('a', href='sitemap.html', style="margin-left:10px; opacity:0.7;")
                        new_link.string = "Sitemap"
                        footer.append(new_link)
                        file_changed = True

            if file_changed:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(str(soup))
                modified += 1
                
            processed += 1
            if processed % 200 == 0:
                print(f"Processed {processed}/{len(html_files)} files...")
                
        except Exception as e:
            print(f"Error processing {filepath.name}: {e}")
            
    print(f"\nSUCCESS: CLEANUP COMPLETE.")
    print(f"Total Files Scanned: {len(html_files)}")
    print(f"Total Files Fixed/Updated: {modified}")

if __name__ == "__main__":
    cleanup_site()
