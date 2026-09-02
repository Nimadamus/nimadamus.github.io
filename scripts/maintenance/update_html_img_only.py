import os

def update_html_image_paths():
    image_dir = 'C:/Users/Nima/nimadamus.github.io/images'
    html_dir = 'C:/Users/Nima/nimadamus.github.io'
    
    # Identify all WebP files that have an original PNG/JPG counterpart
    mapping = {}
    for filename in os.listdir(image_dir):
        if filename.endswith('.webp'):
            base = os.path.splitext(filename)[0]
            # Check for potential original extensions
            for ext in ['.png', '.jpg', '.jpeg']:
                if os.path.exists(os.path.join(image_dir, base + ext)):
                    mapping[base + ext] = filename
                    break

    if not mapping:
        print("No WebP/Original pairs found to map.")
        # Fallback: map all webp files to their base names
        for filename in os.listdir(image_dir):
            if filename.endswith('.webp'):
                base = os.path.splitext(filename)[0]
                mapping[base + '.png'] = filename
                mapping[base + '.jpg'] = filename
                mapping[base + '.jpeg'] = filename

    print(f"Updating HTML files with image replacements...")
    for filename in os.listdir(html_dir):
        if filename.endswith('.html'):
            file_path = os.path.join(html_dir, filename)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            for old_img, new_img in mapping.items():
                content = content.replace(f'images/{old_img}', f'images/{new_img}')
                content = content.replace(f'"{old_img}"', f'"{new_img}"')
            
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"  Updated {filename}")

if __name__ == "__main__":
    update_html_image_paths()
