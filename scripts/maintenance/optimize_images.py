import os
import re
from PIL import Image

def optimize_images():
    image_dir = 'C:/Users/Nima/nimadamus.github.io/images'
    html_dir = 'C:/Users/Nima/nimadamus.github.io'
    
    mapping = {}
    
    for filename in os.listdir(image_dir):
        file_path = os.path.join(image_dir, filename)
        if not os.path.isfile(file_path):
            continue
            
        ext = os.path.splitext(filename)[1].lower()
        if ext not in ['.png', '.jpg', '.jpeg']:
            continue
            
        size = os.path.getsize(file_path)
        if size < 300 * 1024: # Skip if already < 300KB
            continue
            
        if 'logo' in filename.lower():
            continue
            
        print(f"Optimizing {filename} ({size//1024}KB)...")
        
        try:
            img = Image.open(file_path)
            # Convert RGBA to RGB if saving as JPG/WebP
            if img.mode in ('RGBA', 'LA'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[-1])
                img = background
            
            new_filename = os.path.splitext(filename)[0] + '.webp'
            new_path = os.path.join(image_dir, new_filename)
            
            # Resize if too large
            if img.width > 1200:
                ratio = 1200 / img.width
                new_size = (1200, int(img.height * ratio))
                img = img.resize(new_size, Image.Resampling.LANCZOS)
                
            img.save(new_path, 'WEBP', quality=80)
            
            new_size = os.path.getsize(new_path)
            print(f"  -> {new_filename} ({new_size//1024}KB)")
            
            mapping[filename] = new_filename
            
            # Only remove if conversion was successful and actually smaller
            if new_size < size:
                os.remove(file_path)
            else:
                print(f"  Warning: WebP was larger! Keeping original.")
                os.remove(new_path)
                del mapping[filename]
                
        except Exception as e:
            print(f"  Error optimizing {filename}: {e}")

    if not mapping:
        print("No images were optimized.")
        return

    # Update HTML files
    print(f"Updating HTML files with {len(mapping)} image replacements...")
    for filename in os.listdir(html_dir):
        if filename.endswith('.html'):
            file_path = os.path.join(html_dir, filename)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            for old_img, new_img in mapping.items():
                # Be careful with replacements to avoid partial matches
                # Match images/filename.ext or just filename.ext
                content = content.replace(f'images/{old_img}', f'images/{new_img}')
                content = content.replace(f'"{old_img}"', f'"{new_img}"')
            
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"  Updated {filename}")

if __name__ == "__main__":
    optimize_images()
