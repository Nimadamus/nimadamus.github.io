"""
Implement Internal Linking Strategy for BetLegendPicks.com
Adds contextual internal links to improve SEO and user navigation
"""

from pathlib import Path
from bs4 import BeautifulSoup
import re

class InternalLinkBuilder:
    def __init__(self, site_dir):
        self.site_dir = Path(site_dir)
        self.base_url = "https://www.betlegendpicks.com"

        # Define key pages and their related keywords
        self.link_opportunities = {
            # Records pages
            'betlegend-verified-records.html': {
                'keywords': ['verified records', 'track record', 'betting results', 'historical performance', 'verified picks'],
                'anchor': 'verified track record'
            },
            'nfl-records.html': {
                'keywords': ['nfl picks record', 'nfl betting results', 'nfl performance'],
                'anchor': 'NFL verified records'
            },
            'mlb-records.html': {
                'keywords': ['mlb picks record', 'mlb betting results', 'baseball performance'],
                'anchor': 'MLB verified records'
            },
            'nba-records.html': {
                'keywords': ['nba picks record', 'nba betting results', 'basketball performance'],
                'anchor': 'NBA verified records'
            },

            # Sport pages
            'nfl.html': {
                'keywords': ['nfl picks', 'nfl predictions', 'football picks', 'nfl betting'],
                'anchor': 'NFL picks and analysis'
            },
            'mlb.html': {
                'keywords': ['mlb picks', 'mlb predictions', 'baseball picks', 'mlb betting'],
                'anchor': 'MLB picks and analysis'
            },
            'nba.html': {
                'keywords': ['nba picks', 'nba predictions', 'basketball picks', 'nba betting'],
                'anchor': 'NBA picks and analysis'
            },
            'ncaaf.html': {
                'keywords': ['college football picks', 'ncaaf predictions', 'college football betting'],
                'anchor': 'College Football picks'
            },
            'ncaab.html': {
                'keywords': ['college basketball picks', 'ncaab predictions', 'college basketball betting'],
                'anchor': 'College Basketball picks'
            },

            # Tools
            'betting-calculators.html': {
                'keywords': ['betting calculator', 'odds calculator', 'parlay calculator'],
                'anchor': 'betting calculators'
            },
            'odds-converter.html': {
                'keywords': ['convert odds', 'american odds', 'decimal odds'],
                'anchor': 'odds converter'
            },
            'implied-probability-calculator.html': {
                'keywords': ['implied probability', 'probability calculator'],
                'anchor': 'implied probability calculator'
            },
            'kelly-criterion.html': {
                'keywords': ['kelly criterion', 'bankroll management', 'bet sizing'],
                'anchor': 'Kelly Criterion calculator'
            },

            # Educational
            'betting-101.html': {
                'keywords': ['how to bet', 'betting basics', 'sports betting guide'],
                'anchor': 'betting fundamentals guide'
            },
            'betting-glossary.html': {
                'keywords': ['betting terms', 'betting glossary', 'sports betting terminology'],
                'anchor': 'betting glossary'
            },
        }

        # Define contextual link insertions for specific pages
        self.footer_links = [
            ('betlegend-verified-records.html', 'View Verified Records'),
            ('betting-101.html', 'Betting 101 Guide'),
            ('betting-calculators.html', 'Betting Tools'),
            ('index.html', 'Home')
        ]

    def add_contextual_link(self, content, target_page, anchor_text, keyword):
        """Add a contextual link if keyword is found in content"""
        # Don't add link if it already exists
        if target_page in content:
            return content

        # Search for keyword in content (case insensitive)
        pattern = re.compile(r'\b' + re.escape(keyword) + r'\b', re.IGNORECASE)
        match = pattern.search(content)

        if match:
            # Replace first occurrence with linked version
            original = match.group(0)
            linked = f'<a href="{target_page}">{original}</a>'
            content = pattern.sub(linked, content, count=1)
            return content

        return content

    def add_footer_links_to_page(self, soup):
        """Add footer navigation links if not present"""
        # Check if footer already has links
        footer = soup.find('footer')
        if not footer:
            # Try to find a footer-like div
            footer = soup.find('div', class_=re.compile(r'footer', re.I))

        # If still no footer, create one
        if not footer:
            footer = soup.new_tag('footer')
            footer['style'] = 'background-color: #111; padding: 40px 20px; text-align: center; margin-top: 60px; border-top: 2px solid gold;'
            body = soup.find('body')
            if body:
                body.append(footer)

        # Check if footer already has links
        existing_links = footer.find_all('a')
        if len(existing_links) >= 3:
            return False  # Already has footer navigation

        # Add footer navigation
        nav_div = soup.new_tag('div')
        nav_div['style'] = 'display: flex; justify-content: center; gap: 30px; flex-wrap: wrap; margin-bottom: 20px;'

        for page, text in self.footer_links:
            link = soup.new_tag('a')
            link['href'] = page
            link['style'] = 'color: gold; text-decoration: none; font-size: 16px; font-weight: 600;'
            link.string = text
            nav_div.append(link)

        # Clear existing footer content if minimal
        if len(footer.get_text().strip()) < 50:
            footer.clear()

        footer.insert(0, nav_div)
        return True

    def process_file(self, html_file):
        """Process a single HTML file to add internal links"""
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
                soup = BeautifulSoup(content, 'html.parser')

            changes_made = False
            filename = html_file.name

            # Skip certain files
            if filename in ['google6f74b54ecd988601.html', 'input.html', 'test_avg_odds.html']:
                return False

            # Add footer links
            if self.add_footer_links_to_page(soup):
                changes_made = True

            # Find main content area
            main_content = soup.find('main') or soup.find('article') or soup.find('body')

            if main_content:
                # Convert to string to search for keywords
                content_text = main_content.get_text().lower()

                # Check for link opportunities
                links_added = 0
                for target_page, data in self.link_opportunities.items():
                    # Don't link to self
                    if target_page == filename:
                        continue

                    # Don't add too many links
                    if links_added >= 3:
                        break

                    # Check if any keywords are present
                    for keyword in data['keywords']:
                        if keyword.lower() in content_text:
                            # Try to add link
                            paragraphs = main_content.find_all('p')
                            for p in paragraphs:
                                p_text = p.get_text().lower()
                                if keyword.lower() in p_text and target_page not in str(p):
                                    # Found opportunity - add link
                                    p_html = str(p)
                                    new_html = self.add_contextual_link(
                                        p_html,
                                        target_page,
                                        data['anchor'],
                                        keyword
                                    )
                                    if new_html != p_html:
                                        new_p = BeautifulSoup(new_html, 'html.parser').p
                                        if new_p:
                                            p.replace_with(new_p)
                                            links_added += 1
                                            changes_made = True
                                            break

            # Save if changes were made
            if changes_made:
                with open(html_file, 'w', encoding='utf-8') as f:
                    f.write(str(soup))
                return True

            return False

        except Exception as e:
            print(f"Error processing {html_file.name}: {str(e)}")
            return False

    def process_all_files(self):
        """Process all HTML files in the site"""
        html_files = [f for f in self.site_dir.glob("*.html")
                      if f.name not in ['google6f74b54ecd988601.html', 'input.html', 'test_avg_odds.html']]

        print(f"Processing {len(html_files)} HTML files for internal linking...\n")

        updated = 0
        for html_file in html_files:
            if self.process_file(html_file):
                print(f"[OK] Updated: {html_file.name}")
                updated += 1

        print(f"\n{updated} files updated with internal links")
        return updated

if __name__ == "__main__":
    linker = InternalLinkBuilder("C:/Users/Nima/betlegendpicks")
    updated_count = linker.process_all_files()

    print("\n" + "="*50)
    print("INTERNAL LINKING COMPLETE")
    print("="*50)
    print(f"\nFiles updated: {updated_count}")
    print("\nInternal linking improves:")
    print("- SEO through better site structure")
    print("- User navigation and engagement")
    print("- PageRank distribution")
    print("- Crawl depth and indexing")
