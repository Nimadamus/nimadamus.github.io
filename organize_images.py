#!/usr/bin/env python3
"""
BetLegend Image Organization Script
Moves all images to /images folder and updates HTML references
"""

import os
import shutil
import re
from pathlib import Path

# Image extensions to move
IMAGE_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg', '.ico']

# Files to keep in root (don't move these)
KEEP_IN_ROOT = ['newlogo.png', 'favicon.ico']

def backup_repository():
    """Create a backup of the repository"""
    print("Creating backup...")
    backup_dir = Path('backup_before_image_organization')
    if backup_dir.exists():
        shutil.rmtree(backup_dir)

    # Copy all HTML files to backup
    backup_dir.mkdir()
    for html_file in Path('.').glob('*.html'):
        shutil.copy2(html_file, backup_dir / html_file.name)

    print(f"Backup created in {backup_dir}/")

def create_images_folder():
    """Create images folder if it doesn't exist"""
    images_dir = Path('images')
    if not images_dir.exists():
        images_dir.mkdir()
        print("Created /images folder")
    else:
        print("/images folder already exists")
    return images_dir

def find_images():
    """Find all image files in root directory"""
    images = []
    for ext in IMAGE_EXTENSIONS:
        for img in Path('.').glob(f'*{ext}'):
            if img.name not in KEEP_IN_ROOT and img.is_file():
                images.append(img)
    return images

def move_images(images, images_dir):
    """Move images to images folder"""
    moved_count = 0
    print("\nMoving images...")

    for img in images:
        dest = images_dir / img.name
        if dest.exists():
            print(f"  Skipping {img.name} (already exists in images/)")
        else:
            shutil.move(str(img), str(dest))
            print(f"  Moved {img.name}")
            moved_count += 1

    print(f"\nMoved {moved_count} images to /images/")
    return moved_count

def update_html_files(moved_images):
    """Update image references in HTML files"""
    html_files = list(Path('.').glob('*.html'))
    updated_files = 0
    total_updates = 0

    print(f"\nUpdating {len(html_files)} HTML files...")

    for html_file in html_files:
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()

            original_content = content
            updates_in_file = 0

            # Update each moved image
            for img in moved_images:
                img_name = img.name

                # Pattern 1: src="image.png"
                pattern1 = f'src="{img_name}"'
                replacement1 = f'src="images/{img_name}"'
                if pattern1 in content:
                    content = content.replace(pattern1, replacement1)
                    updates_in_file += 1

                # Pattern 2: src='image.png'
                pattern2 = f"src='{img_name}'"
                replacement2 = f"src='images/{img_name}'"
                if pattern2 in content:
                    content = content.replace(pattern2, replacement2)
                    updates_in_file += 1

                # Pattern 3: src="/image.png"
                pattern3 = f'src="/{img_name}"'
                replacement3 = f'src="/images/{img_name}"'
                if pattern3 in content:
                    content = content.replace(pattern3, replacement3)
                    updates_in_file += 1

                # Pattern 4: url(image.png) in CSS
                pattern4 = f"url({img_name})"
                replacement4 = f"url(images/{img_name})"
                if pattern4 in content:
                    content = content.replace(pattern4, replacement4)
                    updates_in_file += 1

                # Pattern 5: url('image.png')
                pattern5 = f"url('{img_name}')"
                replacement5 = f"url('images/{img_name}')"
                if pattern5 in content:
                    content = content.replace(pattern5, replacement5)
                    updates_in_file += 1

            # Only write if changes were made
            if content != original_content:
                with open(html_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"  {html_file.name}: {updates_in_file} references updated")
                updated_files += 1
                total_updates += updates_in_file
            else:
                print(f"  {html_file.name}: no changes needed")

        except Exception as e:
            print(f"  Error updating {html_file.name}: {e}")

    print(f"\nUpdated {total_updates} image references in {updated_files} files")

def main():
    print("=" * 60)
    print("BETLEGEND IMAGE ORGANIZATION SCRIPT")
    print("=" * 60)

    # Step 1: Backup
    backup_repository()

    # Step 2: Create images folder
    images_dir = create_images_folder()

    # Step 3: Find images
    images_to_move = find_images()
    print(f"\nFound {len(images_to_move)} images to organize")

    if not images_to_move:
        print("\nNo images to move! Repository is already organized.")
        return

    # Show what will be moved
    print("\nImages to move:")
    for img in images_to_move[:10]:  # Show first 10
        print(f"  - {img.name}")
    if len(images_to_move) > 10:
        print(f"  ... and {len(images_to_move) - 10} more")

    # Step 4: Move images
    moved_count = move_images(images_to_move, images_dir)

    if moved_count == 0:
        print("\nNo images were moved. Exiting.")
        return

    # Step 5: Update HTML files
    update_html_files(images_to_move)

    print("\n" + "=" * 60)
    print("IMAGE ORGANIZATION COMPLETE!")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Review the changes")
    print("  2. Test your site locally if possible")
    print("  3. Run: git add .")
    print("  4. Run: git commit -m 'Organize images into images folder'")
    print("  5. Run: git push")
    print("\nIf something breaks, restore from backup_before_image_organization/")
    print("=" * 60)

if __name__ == "__main__":
    main()
