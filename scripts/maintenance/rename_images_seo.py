#!/usr/bin/env python3
"""
SEO Image Renaming Script for BetLegend
Renames all generic image filenames to SEO-optimized names based on context
"""

import os
import re
import glob
from pathlib import Path

# Map of current filenames to SEO-optimized names based on HTML context
IMAGE_RENAMES = {
    # October 2025 posts (most recent)
    "1027b.png": "mlb-dodgers-world-series-betting-analysis-oct-27-2025.png",
    "1027a.png": "nfl-adrian-peterson-vikings-news-oct-27-2025.png",
    "1026.png": "nfl-49ers-texans-betting-analysis-oct-26-2025.png",
    "1024.png": "mlb-world-series-game1-dodgers-betting-pick-oct-24-2025.png",
    "1023.png": "nfl-vikings-chargers-thursday-night-football-oct-23-2025.png",
    "1021.png": "nhl-avalanche-utah-road-matchup-oct-21-2025.png",
    "1020.png": "nfl-texans-seahawks-under-betting-pick-oct-20-2025.png",
    "1019.png": "nfl-panthers-jets-betting-analysis-oct-19-2025.png",
    "1018.png": "ncaaf-vanderbilt-lsu-betting-pick-oct-18-2025.png",
    "1017.png": "ncaaf-north-carolina-california-analysis-oct-17-2025.png",
    "1016.png": "nfl-bengals-steelers-betting-pick-oct-16-2025.png",
    "1015.png": "ncaaf-jacksonville-state-delaware-oct-15-2025.png",
    "1014.png": "soccer-armenia-ireland-corner-betting-oct-14-2025.png",
    "1013.png": "nfl-bills-falcons-monday-night-football-oct-13-2025.png",
    "1012.png": "nfl-49ers-buccaneers-betting-analysis-oct-12-2025.png",

    # October early (109-101)
    "109.png": "nfl-ncaaf-two-team-teaser-eagles-tulane-oct-09-2025.png",
    "108.png": "mlb-yankees-bluejays-alds-game4-total-oct-08-2025.png",
    "106.png": "nfl-chiefs-jaguars-betting-analysis-oct-06-2025.png",
    "105.png": "nfl-seahawks-buccaneers-pick-oct-05-2025.png",
    "104.png": "ncaaf-florida-texas-betting-pick-oct-04-2025.png",
    "103.png": "ncaaf-college-football-teaser-oct-03-2025.png",
    "102.png": "mlb-playoffs-betting-analysis-oct-02-2025.png",
    "101.png": "mlb-playoffs-pick-oct-01-2025.png",

    # September 2025
    "9262025.png": "ncaaf-tcu-arizona-state-under-betting-sept-26-2025.png",
    "924.png": "mlb-guardians-betting-pick-sept-24-2025.png",
    "9222025.png": "mlb-giants-first-five-innings-pick-sept-22-2025.png",
    "921.png": "nfl-rams-eagles-betting-pick-sept-21-2025.png",
    "920.png": "ncaaf-arkansas-memphis-under-pick-sept-20-2025.png",
    "919.png": "mlb-guardians-moneyline-pick-sept-19-2025.png",
    "918.png": "mlb-guardians-tigers-under-pick-sept-18-2025.png",
    "917.png": "mlb-cubs-pirates-betting-pick-sept-17-2025.png",
    "916.png": "mlb-cubs-pirates-team-total-under-sept-16-2025.png",
    "915.png": "mlb-rangers-astros-under-minute-maid-sept-15-2025.png",
    "913.png": "mlb-giants-dodgers-oracle-park-under-sept-13-2025.png",
    "912.png": "ncaaf-gambling-scandal-news-sept-12-2025.png",
    "9112025.png": "nfl-commanders-packers-lambeau-field-sept-11-2025.png",
    "9102025.png": "nfl-eagles-chiefs-super-bowl-rematch-sept-10-2025.png",
    "942025.png": "mlb-dodgers-pirates-pnc-park-sept-04-2025.png",
    "932025.png": "mlb-giants-rockies-first-five-pick-sept-03-2025.png",
    "922025.png": "mlb-garrett-crochet-fenway-park-sept-02-2025.png",
    "912025.png": "mlb-jose-altuve-astros-celebration-sept-01-2025.png",

    # August 2025
    "817.png": "mlb-betting-pick-aug-17-2025.png",
    "816.png": "mlb-betting-analysis-aug-16-2025.png",

    # July 2025
    "723card.png": "mlb-best-bets-picks-july-23-2025.png",
    "720.png": "mlb-betting-pick-july-20-2025.png",
    "712mlb.png": "mlb-picks-graphic-july-12-2025.png",
    "711mlb.png": "mlb-picks-team-logos-july-11-2025.png",

    # Named team/player images (already decent, but can improve)
    "rays.png": "mlb-tampa-bay-rays-betting-analysis.png",
    "col.png": "mlb-colorado-rockies-brewers-betting-pick.png",
    "stsa.png": "mlb-strider-suarez-phillies-braves-analysis.png",
    "soxjays.png": "mlb-red-sox-blue-jays-betting-pick.png",
    "cubsastros.png": "mlb-cubs-astros-betting-analysis.png",
    "sfg.png": "mlb-giants-white-sox-pitching-analysis.png",
    "clarkeschmidt.jpg": "mlb-clark-schmidt-yankees-stadium-pitch.jpg",
    "angel.png": "mlb-angels-dugout-team-photo.png",
    "judge.png": "mlb-aaron-judge-yankees-batting.png",
    "mariners.png": "mlb-seattle-mariners-twins-betting-pick.png",
    "tigers.png": "mlb-tigers-athletics-over-under-pick.png",
    "greatamerican.png": "mlb-great-american-ballpark-yankees-reds.png",
    "trout.png": "mlb-mike-trout-angels-red-sox-batting.png",
    "bravesmets.png": "mlb-braves-mets-first-five-innings-pick.png",
    "altuve.jpg": "mlb-jose-altuve-astros-angels-analysis.jpg",
    "coors.png": "mlb-coors-field-diamondbacks-rockies-over.png",
    "birdsong.png": "mlb-giants-birdsong-pitcher-red-sox.png",
    "tigersrays.png": "mlb-tigers-rays-first-five-innings-under.png",
    "strider.png": "mlb-spencer-strider-braves-mets-f5-under.png",
    "webb.png": "mlb-logan-webb-giants-guardians-moneyline.png",
    "texoa.png": "mlb-rangers-athletics-prediction-july.png",
    "twins.png": "mlb-twins-coors-field-betting-pick.png",
    "detroit.png": "mlb-detroit-tigers-celebration.png",
    "2025allstars.png": "mlb-2025-all-star-game-preview.png",
    "bravesrays.png": "mlb-braves-rays-betting-pick-july.png",
    "woo1.png": "mlb-bryan-woo-mariners-yankees-pitching.png",
    "arbitrage.png": "betting-strategy-arbitrage-betting-chart.png",

    # Generic numbered images (keep in images folder, they're screenshots)
    "1.png": "mlb-phillies-astros-suarez-valdez-matchup.png",
    "2.png": "betlegend-logo-2.png",

    # Screenshots (these are fine, just prepend category)
    "1000079685.jpg": "proof-bet-screenshot-1000079685.jpg",
    "1000079686.jpg": "proof-bet-screenshot-1000079686.jpg",
    "1000079687.jpg": "proof-bet-screenshot-1000079687.jpg",
}

def rename_images(images_dir, dry_run=False):
    """
    Rename images in the images directory according to the mapping
    """
    images_path = Path(images_dir)

    if not images_path.exists():
        print(f"Error: Images directory not found: {images_dir}")
        return

    renamed_count = 0
    skipped_count = 0

    print(f"\n{'DRY RUN - ' if dry_run else ''}Renaming images for SEO optimization...")
    print("=" * 80)

    for old_name, new_name in IMAGE_RENAMES.items():
        old_path = images_path / old_name
        new_path = images_path / new_name

        if old_path.exists():
            if new_path.exists():
                print(f"[SKIP] {new_name} already exists")
                skipped_count += 1
                continue

            print(f"[RENAME] {old_name:40s} -> {new_name}")

            if not dry_run:
                old_path.rename(new_path)

            renamed_count += 1
        else:
            print(f"  SKIP: {old_name} not found")
            skipped_count += 1

    print("=" * 80)
    print(f"\n{'[DRY RUN] ' if dry_run else ''}Summary:")
    print(f"  Renamed: {renamed_count}")
    print(f"  Skipped: {skipped_count}")
    print(f"  Total mappings: {len(IMAGE_RENAMES)}")

    return IMAGE_RENAMES

def update_html_references(base_dir, rename_map, dry_run=False):
    """
    Update all HTML file references to use new image names
    """
    base_path = Path(base_dir)
    html_files = list(base_path.glob("*.html"))

    print(f"\n{'DRY RUN - ' if dry_run else ''}Updating HTML file references...")
    print("=" * 80)

    updated_files = 0
    total_replacements = 0

    for html_file in html_files:
        content = html_file.read_text(encoding='utf-8')
        original_content = content
        file_replacements = 0

        for old_name, new_name in rename_map.items():
            # Match both images/oldname and images/oldname patterns
            old_ref = f'images/{old_name}'
            new_ref = f'images/{new_name}'

            if old_ref in content:
                count = content.count(old_ref)
                content = content.replace(old_ref, new_ref)
                file_replacements += count

        if file_replacements > 0:
            print(f"  {html_file.name}: {file_replacements} reference(s) updated")

            if not dry_run:
                html_file.write_text(content, encoding='utf-8')

            updated_files += 1
            total_replacements += file_replacements

    print("=" * 80)
    print(f"\n{'[DRY RUN] ' if dry_run else ''}Summary:")
    print(f"  Files updated: {updated_files}")
    print(f"  Total replacements: {total_replacements}")
    print(f"  HTML files checked: {len(html_files)}")

def main():
    import sys

    # Configuration
    base_dir = r"C:\Users\Nima\Desktop\betlegendpicks"
    images_dir = os.path.join(base_dir, "images")

    # Check if dry run
    dry_run = "--dry-run" in sys.argv or "-d" in sys.argv

    if dry_run:
        print("\n" + "=" * 80)
        print("DRY RUN MODE - No changes will be made")
        print("=" * 80)

    print(f"\nBetLegend SEO Image Renaming Tool")
    print(f"Base directory: {base_dir}")
    print(f"Images directory: {images_dir}\n")

    # Step 1: Rename images
    rename_map = rename_images(images_dir, dry_run=dry_run)

    # Step 2: Update HTML references
    update_html_references(base_dir, rename_map, dry_run=dry_run)

    print("\n" + "=" * 80)
    if dry_run:
        print("DRY RUN COMPLETE - Run without --dry-run to apply changes")
    else:
        print("[SUCCESS] ALL DONE! Images renamed and HTML files updated.")
        print("\nNext steps:")
        print("1. Check that images still display correctly on your site")
        print("2. Update any JSON or JavaScript files that reference images")
        print("3. Re-upload/deploy the changes to your live site")
    print("=" * 80)

if __name__ == "__main__":
    main()
