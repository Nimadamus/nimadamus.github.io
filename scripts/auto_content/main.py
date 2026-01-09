"""
Auto-Content Generation System - Main Orchestrator
Coordinates data scraping, content generation, and HTML updates
"""

import os
import sys
import argparse
import subprocess
from datetime import datetime
from typing import List, Dict, Optional
import json

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import REPO_PATH, SPORTS, GIT_AUTO_COMMIT, GIT_AUTO_PUSH
from scrapers import get_scraper, SCRAPERS
from generators.content_generator import ContentGenerator
from html_updater import HTMLUpdater


class AutoContentOrchestrator:
    """Main orchestrator for the auto-content generation system."""

    def __init__(self, api_key: str = None, dry_run: bool = False):
        """Initialize the orchestrator.

        Args:
            api_key: Anthropic API key (or set ANTHROPIC_API_KEY env var)
            dry_run: If True, don't write files or push to git
        """
        self.dry_run = dry_run
        self.html_updater = HTMLUpdater(REPO_PATH)

        # Initialize content generator with API key
        try:
            self.content_generator = ContentGenerator(api_key)
        except ValueError as e:
            print(f"Warning: {e}")
            print("Content generation will be skipped.")
            self.content_generator = None

    def run_sport(self, sport: str, date: str = None) -> Dict:
        """Run the full pipeline for a single sport.

        Args:
            sport: Sport code (nba, nhl, nfl, ncaab, ncaaf, mlb, soccer)
            date: Date in YYYYMMDD format (defaults to today)

        Returns:
            Dict with results: {success: bool, games: int, message: str}
        """
        sport_lower = sport.lower()

        if sport_lower not in SCRAPERS:
            return {
                'success': False,
                'games': 0,
                'message': f"Unknown sport: {sport}"
            }

        config = SPORTS.get(sport_lower, {})
        sport_name = config.get('name', sport.upper())

        # Check if sport is in season
        if date is None:
            date = datetime.now().strftime("%Y%m%d")
            display_date = datetime.now().strftime("%B %d, %Y")
        else:
            display_date = datetime.strptime(date, "%Y%m%d").strftime("%B %d, %Y")

        current_month = int(date[4:6])
        season_months = config.get('season_months', list(range(1, 13)))

        if current_month not in season_months:
            return {
                'success': True,
                'games': 0,
                'message': f"{sport_name} is not in season"
            }

        print(f"\n{'='*60}")
        print(f"Processing {sport_name} for {display_date}")
        print('='*60)

        try:
            # Step 1: Scrape game data
            print(f"\n[1/4] Fetching {sport_name} games...")
            scraper = get_scraper(sport_lower)
            games_data = scraper.get_full_game_data(date)

            if not games_data:
                return {
                    'success': True,
                    'games': 0,
                    'message': f"No {sport_name} games found for {display_date}"
                }

            print(f"Found {len(games_data)} games")

            # Step 2: Format game data for articles
            print(f"\n[2/4] Processing game data...")
            formatted_games = []
            for game_data in games_data:
                try:
                    formatted = scraper.format_for_article(game_data)
                    formatted_games.append(formatted)
                except Exception as e:
                    print(f"  Warning: Could not format game: {e}")

            if not formatted_games:
                return {
                    'success': False,
                    'games': 0,
                    'message': "Failed to format any games"
                }

            # Step 3: Generate content
            print(f"\n[3/4] Generating content...")
            game_cards_html = []

            if self.content_generator:
                for i, game in enumerate(formatted_games):
                    matchup = game.get('matchup', f'Game {i+1}')
                    print(f"  Generating: {matchup}")

                    try:
                        # Generate stat grid
                        stat_grid = self.content_generator.generate_stat_grid_html(
                            game, sport_lower
                        )

                        # Generate article
                        article = self.content_generator.generate_game_article(
                            game, sport_lower
                        )

                        # Build complete game card
                        game_card = self.html_updater.generate_game_card_html(
                            game, sport_lower, stat_grid, article
                        )

                        game_cards_html.append(game_card)

                    except Exception as e:
                        print(f"    Error generating content: {e}")
                        print(f"    SKIPPING {matchup} - NO PLACEHOLDER CONTENT ALLOWED")
                        # DO NOT use fallback - skip games that can't get real content
            else:
                # No API key - CANNOT generate content without API
                print("  ERROR: No API key available - cannot generate content")
                print("  Set ANTHROPIC_API_KEY environment variable to enable content generation")
                print("  NO PLACEHOLDER CONTENT WILL BE GENERATED")
                return {
                    'success': False,
                    'games': 0,
                    'message': f"No API key - cannot generate {sport_name} content (placeholders not allowed)"
                }

            if not game_cards_html:
                return {
                    'success': False,
                    'games': 0,
                    'message': "Failed to generate any content"
                }

            # Step 4: Update HTML files
            print(f"\n[4/4] Updating HTML files...")

            if self.dry_run:
                print("  [DRY RUN] Would update files:")
                print(f"    - {config.get('main_page', f'{sport}.html')}")
                print(f"    - {len(game_cards_html)} game cards")
            else:
                try:
                    # Combine all game cards into daily content
                    daily_content = '\n'.join(game_cards_html)

                    # Insert into main page
                    updated_html, archived = self.html_updater.insert_content_to_main_page(
                        sport_lower, daily_content, display_date
                    )

                    # Write updated main page
                    main_page_path = self.html_updater.get_page_path(sport_lower)
                    self.html_updater.write_page(main_page_path, updated_html)
                    print(f"  Updated: {os.path.basename(main_page_path)}")

                    # Handle archived content if any
                    if archived:
                        self.html_updater.archive_content(sport_lower, archived)
                        print(f"  Archived {len(archived)} old posts")

                except Exception as e:
                    return {
                        'success': False,
                        'games': len(formatted_games),
                        'message': f"Error updating HTML: {e}"
                    }

            return {
                'success': True,
                'games': len(formatted_games),
                'message': f"Successfully processed {len(formatted_games)} {sport_name} games"
            }

        except Exception as e:
            return {
                'success': False,
                'games': 0,
                'message': f"Error: {e}"
            }

    def _generate_fallback_card(self, game: Dict, sport: str) -> str:
        """Generate a game card - REQUIRES real content, NO placeholders.

        Returns None if content cannot be generated - the game will be skipped.
        NEVER use placeholder text like 'coming soon' or 'analysis pending'.
        """
        # NO PLACEHOLDERS ALLOWED - return None to skip this game
        # The calling code must handle None and skip games without content
        return None

    def run_all_sports(self, date: str = None) -> Dict[str, Dict]:
        """Run the pipeline for all active sports.

        Args:
            date: Date in YYYYMMDD format (defaults to today)

        Returns:
            Dict mapping sport codes to result dicts
        """
        results = {}

        for sport_code, config in SPORTS.items():
            if config.get('active', True):
                results[sport_code] = self.run_sport(sport_code, date)
            else:
                results[sport_code] = {
                    'success': True,
                    'games': 0,
                    'message': f"{config.get('name', sport_code)} is disabled"
                }

        return results

    def sync_calendars(self):
        """Run calendar sync after content generation.

        This ensures the calendar sidebar always shows the correct dates
        including the newly generated content.
        """
        if self.dry_run:
            print("\n[DRY RUN] Would sync calendars")
            return

        print("\n[SYNC] Syncing calendars...")
        try:
            # Run sync_calendars.py script
            sync_script = os.path.join(os.path.dirname(REPO_PATH), 'nimadamus.github.io', 'scripts', 'sync_calendars.py')
            if not os.path.exists(sync_script):
                sync_script = os.path.join(REPO_PATH, 'scripts', 'sync_calendars.py')

            result = subprocess.run(
                ['python', sync_script],
                capture_output=True,
                text=True,
                cwd=REPO_PATH
            )
            if result.returncode == 0:
                print("  Calendars synced successfully")
            else:
                print(f"  Warning: Calendar sync had issues: {result.stderr}")
        except Exception as e:
            print(f"  Warning: Could not sync calendars: {e}")

    def git_commit_and_push(self, message: str = None):
        """Commit and push changes to git.

        Args:
            message: Custom commit message (auto-generated if not provided)
        """
        if self.dry_run:
            print("\n[DRY RUN] Would commit and push changes")
            return

        if message is None:
            date = datetime.now().strftime("%B %d, %Y")
            message = f"Auto-update sports content for {date}"

        try:
            # Add all changes
            subprocess.run(
                ['git', '-C', REPO_PATH, 'add', '-A'],
                check=True, capture_output=True
            )

            # Commit
            full_message = f"""{message}

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"""

            subprocess.run(
                ['git', '-C', REPO_PATH, 'commit', '-m', full_message],
                check=True, capture_output=True
            )
            print(f"\nCommitted changes: {message}")

            # Push
            if GIT_AUTO_PUSH:
                subprocess.run(
                    ['git', '-C', REPO_PATH, 'push'],
                    check=True, capture_output=True
                )
                print("Pushed to remote")

        except subprocess.CalledProcessError as e:
            if b'nothing to commit' in e.stderr:
                print("\nNo changes to commit")
            else:
                print(f"\nGit error: {e.stderr.decode()}")


def main():
    """Main entry point for the auto-content system."""
    parser = argparse.ArgumentParser(
        description='Auto-Content Generation System for BetLegend Picks'
    )

    parser.add_argument(
        '--sport', '-s',
        choices=list(SCRAPERS.keys()) + ['all'],
        default='all',
        help='Sport to process (default: all)'
    )

    parser.add_argument(
        '--date', '-d',
        help='Date to process (YYYYMMDD format, default: today)'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run without writing files or pushing to git'
    )

    parser.add_argument(
        '--no-push',
        action='store_true',
        help='Skip git push (still commits)'
    )

    parser.add_argument(
        '--api-key',
        help='Anthropic API key (or set ANTHROPIC_API_KEY env var)'
    )

    args = parser.parse_args()

    # Override git push setting if requested
    if args.no_push:
        import config
        config.GIT_AUTO_PUSH = False

    print("\n" + "="*60)
    print("BetLegend Auto-Content Generation System")
    print("="*60)

    if args.dry_run:
        print("[DRY RUN MODE - No files will be modified]")

    # Initialize orchestrator
    orchestrator = AutoContentOrchestrator(
        api_key=args.api_key,
        dry_run=args.dry_run
    )

    # Run for specified sports
    if args.sport == 'all':
        results = orchestrator.run_all_sports(args.date)
    else:
        results = {args.sport: orchestrator.run_sport(args.sport, args.date)}

    # Print summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    total_games = 0
    successful = 0

    for sport, result in results.items():
        status = "[OK]" if result['success'] else "[FAIL]"
        print(f"{status} {sport.upper()}: {result['message']}")
        if result['success']:
            successful += 1
            total_games += result['games']

    print(f"\nTotal: {total_games} games across {successful}/{len(results)} sports")

    # ALWAYS sync calendars after content generation
    # This ensures the calendar sidebar shows today's date correctly
    if total_games > 0:
        orchestrator.sync_calendars()

    # Git operations
    if not args.dry_run and GIT_AUTO_COMMIT and total_games > 0:
        orchestrator.git_commit_and_push()

    return 0 if all(r['success'] for r in results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
