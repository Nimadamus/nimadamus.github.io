"""
HTML Updater and Archive Rotation System
Handles inserting new content into sport pages and archiving old content
"""

import os
import re
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from bs4 import BeautifulSoup

# Import config
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import REPO_PATH, SPORTS, POSTS_PER_PAGE, DATE_FORMAT


class HTMLUpdater:
    """Manages HTML updates and archive rotation for sport pages."""

    def __init__(self, repo_path: str = None):
        self.repo_path = repo_path or REPO_PATH

    def get_page_path(self, sport: str, page_num: int = None) -> str:
        """Get the file path for a sport page.

        Args:
            sport: Sport code (nba, nhl, etc.)
            page_num: Page number (None for main page, 2+ for archives)
        """
        config = SPORTS.get(sport.lower())
        if not config:
            raise ValueError(f"Unknown sport: {sport}")

        if page_num is None or page_num == 1:
            filename = config['main_page']
        else:
            filename = f"{config['page_prefix']}{page_num}.html"

        return os.path.join(self.repo_path, filename)

    def read_page(self, filepath: str) -> str:
        """Read HTML file content."""
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()

    def write_page(self, filepath: str, content: str):
        """Write HTML file content."""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

    def get_total_pages(self, sport: str) -> int:
        """Get current total number of pages for a sport."""
        config = SPORTS.get(sport.lower())
        if not config:
            return 0

        # Count existing pages
        page_num = 2
        while os.path.exists(self.get_page_path(sport, page_num)):
            page_num += 1

        return page_num - 1 if page_num > 2 else 1

    def extract_game_cards(self, html_content: str) -> List[str]:
        """Extract all game card articles from HTML."""
        soup = BeautifulSoup(html_content, 'html.parser')
        main_elem = soup.find('main')

        if not main_elem:
            return []

        game_cards = main_elem.find_all('article', class_='game-card')
        return [str(card) for card in game_cards]

    def count_game_cards(self, html_content: str) -> int:
        """Count number of game cards in HTML."""
        return len(self.extract_game_cards(html_content))

    def generate_daily_post_html(self, sport: str, date: str, games_html: List[str],
                                  intro_text: str = None) -> str:
        """Generate the complete HTML for a daily post.

        Args:
            sport: Sport code
            date: Date string
            games_html: List of HTML strings for each game
            intro_text: Optional intro paragraph
        """
        config = SPORTS.get(sport.lower())
        emoji = config.get('emoji', '') if config else ''
        sport_name = config.get('name', sport.upper()) if config else sport.upper()

        # Build the content
        content_parts = []

        # Date header
        content_parts.append(f"""
<!-- {sport_name} Analysis - {date} -->
<div class="daily-slate" data-date="{date}">
""")

        # Intro if provided
        if intro_text:
            content_parts.append(f"""
<div class="slate-intro">
<p>{intro_text}</p>
</div>
""")

        # All game cards
        for game_html in games_html:
            content_parts.append(game_html)

        content_parts.append("</div><!-- end daily-slate -->")

        return '\n'.join(content_parts)

    def insert_content_to_main_page(self, sport: str, new_content: str,
                                     date: str = None, clear_existing: bool = True) -> Tuple[str, List[str]]:
        """Insert new content at the top of main sport page.

        IMPORTANT: By default, this now CLEARS all existing game cards before
        adding new ones. This prevents stale games from previous days being
        shown alongside today's games.

        Args:
            sport: Sport code
            new_content: HTML content to insert
            date: Date for the new content
            clear_existing: If True (default), removes ALL existing game cards
                           before adding new content. Set to False only if you
                           explicitly want to keep old games (not recommended).

        Returns:
            Tuple of (updated HTML, list of archived content if any)
        """
        if date is None:
            date = datetime.now().strftime("%B %d, %Y")

        main_page_path = self.get_page_path(sport)
        html_content = self.read_page(main_page_path)

        # Update the date in hero/header
        html_content = self._update_page_date(html_content, date, sport)

        # Find the main content area and insert new content
        soup = BeautifulSoup(html_content, 'html.parser')
        main_elem = soup.find('main')

        if not main_elem:
            raise ValueError(f"Could not find <main> element in {main_page_path}")

        # Get existing game cards
        existing_cards = main_elem.find_all('article', class_='game-card')

        # Archive existing cards before clearing (if clear_existing is True)
        archived_content = []
        if clear_existing and existing_cards:
            print(f"[{sport.upper()}] Clearing {len(existing_cards)} old game cards before adding new content")
            for card in existing_cards:
                archived_content.append(str(card))
                card.decompose()

        # Insert new content at the beginning of main
        new_soup = BeautifulSoup(new_content, 'html.parser')
        new_elements = list(new_soup.children)

        # Prepend new content
        for elem in reversed(new_elements):
            main_elem.insert(0, elem)

        # If we didn't clear existing, check if we need to archive old content
        if not clear_existing:
            all_cards = main_elem.find_all('article', class_='game-card')
            if len(all_cards) > POSTS_PER_PAGE * 3:  # Keep 3 days on main page
                # Archive oldest cards
                cards_to_archive = all_cards[POSTS_PER_PAGE * 3:]
                for card in cards_to_archive:
                    archived_content.append(str(card))
                    card.decompose()

        return str(soup), archived_content

    def _update_page_date(self, html_content: str, date: str, sport: str) -> str:
        """Update the date displayed on the page."""
        config = SPORTS.get(sport.lower())
        sport_name = config.get('name', sport.upper()) if config else sport.upper()

        # Update title tag
        html_content = re.sub(
            r'<title>.*?</title>',
            f'<title>{sport_name} Analysis - {date} | BetLegend</title>',
            html_content,
            count=1
        )

        # Update meta description
        html_content = re.sub(
            r'<meta name="description" content="[^"]*">',
            f'<meta name="description" content="{sport_name} statistical analysis for {date}. Advanced stats, efficiency ratings, and betting trends.">',
            html_content,
            count=1
        )

        # Update current-date div
        html_content = re.sub(
            r'<div class="current-date">.*?</div>',
            f'<div class="current-date"><h2>{date}</h2></div>',
            html_content,
            flags=re.DOTALL
        )

        return html_content

    def archive_content(self, sport: str, content_to_archive: List[str]):
        """Move content to archive pages.

        Args:
            sport: Sport code
            content_to_archive: List of HTML content strings to archive
        """
        if not content_to_archive:
            return

        # Get current highest page number
        total_pages = self.get_total_pages(sport)
        new_page_num = total_pages + 1

        # Create new archive page from template
        self._create_archive_page(sport, new_page_num, content_to_archive)

        # Update pagination on all pages
        self.update_all_pagination(sport, new_page_num)

    def _create_archive_page(self, sport: str, page_num: int, content: List[str]):
        """Create a new archive page.

        Args:
            sport: Sport code
            page_num: New page number
            content: List of HTML content to include
        """
        config = SPORTS.get(sport.lower())
        sport_name = config.get('name', sport.upper()) if config else sport.upper()

        # Use page 2 as template if it exists, otherwise main page
        template_path = self.get_page_path(sport, 2)
        if not os.path.exists(template_path):
            template_path = self.get_page_path(sport)

        template_html = self.read_page(template_path)

        # Update the page content
        soup = BeautifulSoup(template_html, 'html.parser')
        main_elem = soup.find('main')

        if main_elem:
            # Clear existing content
            main_elem.clear()

            # Add archived content
            for html_content in content:
                content_soup = BeautifulSoup(html_content, 'html.parser')
                for elem in content_soup.children:
                    main_elem.append(elem)

        # Update title and meta
        title_tag = soup.find('title')
        if title_tag:
            title_tag.string = f"{sport_name} Analysis Archive - Page {page_num} | BetLegend"

        # Write new page
        new_page_path = self.get_page_path(sport, page_num)
        self.write_page(new_page_path, str(soup))
        print(f"Created archive page: {new_page_path}")

    def update_all_pagination(self, sport: str, total_pages: int):
        """Update pagination links on all pages for a sport.

        Args:
            sport: Sport code
            total_pages: Total number of pages including new ones
        """
        config = SPORTS.get(sport.lower())
        if not config:
            return

        for page_num in range(1, total_pages + 1):
            page_path = self.get_page_path(sport, page_num if page_num > 1 else None)
            if os.path.exists(page_path):
                html_content = self.read_page(page_path)
                updated_html = self._update_page_pagination(
                    html_content, sport, page_num, total_pages
                )
                self.write_page(page_path, updated_html)

    def _update_page_pagination(self, html_content: str, sport: str,
                                 current_page: int, total_pages: int) -> str:
        """Update pagination on a single page.

        Per CLAUDE.md:
        - sport.html = NEWEST content (Page X of X)
        - sport-page2.html = Second newest (Page X-1 of X)
        - sport-pageN.html = OLDEST (Page 1 of X)

        So main page "Older" link goes to page2, not pageN.
        """
        config = SPORTS.get(sport.lower())
        main_page = config.get('main_page', f'{sport}.html')
        page_prefix = config.get('page_prefix', f'{sport}-page')

        # Calculate display page number (newest = highest number)
        display_page = total_pages - current_page + 1 if current_page > 1 else total_pages

        # Build pagination HTML
        pagination_parts = ['<div class="archive-link">']

        # Newer link (higher page number in display = lower file number)
        if current_page > 1:
            if current_page == 2:
                newer_link = main_page
            else:
                newer_link = f"{page_prefix}{current_page - 1}.html"
            pagination_parts.append(f'<a href="{newer_link}">← Newer</a> ')

        pagination_parts.append(f'<span>Page {display_page} of {total_pages}</span>')

        # Older link (lower page number in display = higher file number)
        if current_page < total_pages:
            older_link = f"{page_prefix}{current_page + 1}.html"
            pagination_parts.append(f' <a href="{older_link}">Older →</a>')

        pagination_parts.append('</div>')
        new_pagination = ''.join(pagination_parts)

        # Replace existing pagination or add before </main>
        if '<div class="archive-link">' in html_content:
            html_content = re.sub(
                r'<div class="archive-link">.*?</div>',
                new_pagination,
                html_content,
                flags=re.DOTALL
            )
        else:
            html_content = html_content.replace(
                '</main>',
                f'\n{new_pagination}\n</main>'
            )

        return html_content

    def generate_game_card_html(self, game_data: Dict, sport: str,
                                  stat_grid_html: str, article_text: str) -> str:
        """Generate a complete game card HTML.

        Args:
            game_data: Formatted game data dict
            sport: Sport code
            stat_grid_html: Pre-generated stat grid HTML
            article_text: Pre-generated article text

        Returns:
            Complete game card HTML string
        """
        home = game_data.get('home', {})
        away = game_data.get('away', {})
        odds = game_data.get('odds', {})

        # Get team abbreviations for logo URLs
        home_abbrev = home.get('abbrev', '').lower()
        away_abbrev = away.get('abbrev', '').lower()

        # Build logo URLs based on sport
        sport_lower = sport.lower()
        if sport_lower == 'nba':
            logo_base = "https://a.espncdn.com/i/teamlogos/nba/500/scoreboard"
        elif sport_lower == 'nhl':
            logo_base = "https://a.espncdn.com/i/teamlogos/nhl/500/scoreboard"
        elif sport_lower == 'nfl':
            logo_base = "https://a.espncdn.com/i/teamlogos/nfl/500/scoreboard"
        elif sport_lower == 'mlb':
            logo_base = "https://a.espncdn.com/i/teamlogos/mlb/500/scoreboard"
        elif sport_lower in ['ncaab', 'ncaaf']:
            logo_base = "https://a.espncdn.com/i/teamlogos/ncaa/500"
        else:
            logo_base = ""

        home_logo = f"{logo_base}/{home_abbrev}.png" if logo_base else ""
        away_logo = f"{logo_base}/{away_abbrev}.png" if logo_base else ""

        # Build meta line
        meta_parts = []
        if game_data.get('game_time'):
            meta_parts.append(f"<span>{game_data['game_time']}</span>")
        if game_data.get('venue'):
            meta_parts.append(f"<span>{game_data['venue']}</span>")
        if game_data.get('broadcast'):
            meta_parts.append(f"<span>{game_data['broadcast']}</span>")
        if odds.get('spread'):
            meta_parts.append(f"<span>Line: {odds['spread']}</span>")
        if odds.get('total'):
            meta_parts.append(f"<span>Total: {odds['total']}</span>")

        meta_html = '\n'.join(meta_parts)

        # Build article paragraphs
        paragraphs = article_text.split('\n\n')
        article_html = '\n'.join(f'<p>{p.strip()}</p>' for p in paragraphs if p.strip())

        # Complete game card HTML
        return f"""
<article class="game-card">
<div class="teams-display">
<img src="{away_logo}" alt="{away.get('name', 'Away')}" class="team-logo" onerror="this.style.display='none'">
<span class="vs-badge">@</span>
<img src="{home_logo}" alt="{home.get('name', 'Home')}" class="team-logo" onerror="this.style.display='none'">
</div>
<h3 class="game-title">{away.get('name', 'Away')} ({away.get('record', '')}) @ {home.get('name', 'Home')} ({home.get('record', '')})</h3>
<div class="game-meta">
{meta_html}
</div>

{stat_grid_html}

{article_html}
<div class="data-source">Sources: ESPN, Team Stats, Official League Data</div>
</article>
"""


# Standalone test
if __name__ == "__main__":
    updater = HTMLUpdater()

    # Test reading a page
    print("Testing HTML Updater...")
    print(f"Repo path: {updater.repo_path}")

    # Test page counting
    for sport in ['nba', 'nhl', 'nfl']:
        try:
            pages = updater.get_total_pages(sport)
            print(f"{sport.upper()}: {pages} pages")
        except Exception as e:
            print(f"{sport.upper()}: Error - {e}")

    # Test game card count
    try:
        nba_path = updater.get_page_path('nba')
        nba_content = updater.read_page(nba_path)
        card_count = updater.count_game_cards(nba_content)
        print(f"\nNBA main page has {card_count} game cards")
    except Exception as e:
        print(f"Error reading NBA page: {e}")
