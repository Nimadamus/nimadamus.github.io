"""
Automated SEO Fixer for BetLegendPicks.com
Fixes missing metadata, canonical tags, H1 tags, and optimizes titles
"""

import json
from pathlib import Path
from bs4 import BeautifulSoup
import re

class SEOFixer:
    def __init__(self, site_dir, audit_data_file):
        self.site_dir = Path(site_dir)
        with open(audit_data_file, 'r', encoding='utf-8') as f:
            self.audit_data = json.load(f)
        self.base_url = "https://www.betlegendpicks.com"
        self.fixes_applied = {
            "titles_added": [],
            "descriptions_added": [],
            "h1_added": [],
            "canonical_added": [],
            "titles_optimized": [],
            "errors": []
        }

    def generate_title_from_filename(self, filename):
        """Generate SEO-friendly title from filename"""
        # Remove extension and directory
        base = Path(filename).stem

        # Skip certain files
        if base in ['google6f74b54ecd988601', 'input', 'test_avg_odds']:
            return None

        # Handle special cases
        title_map = {
            'nfl_analysis_example': 'NFL Game Analysis Example | BetLegend',
            'nfl_week9_analysis_REAL': 'NFL Week 9 Analysis | BetLegend Picks',
            'blog-page2': 'BetLegend Blog - Page 2 | Expert Betting Insights',
            'blog-page3': 'BetLegend Blog - Page 3 | Expert Betting Insights',
            'blog-page4': 'BetLegend Blog - Page 4 | Expert Betting Insights',
            'blog-page5': 'BetLegend Blog - Page 5 | Expert Betting Insights',
            'blog-page6': 'BetLegend Blog - Page 6 | Expert Betting Insights',
            'blog-page7': 'BetLegend Blog - Page 7 | Expert Betting Insights',
        }

        if base in title_map:
            return title_map[base]

        # Generate from filename
        words = re.sub(r'[-_]', ' ', base).title()
        return f"{words} | BetLegend"

    def generate_description_from_content(self, soup, filename):
        """Generate meta description from page content"""
        base = Path(filename).stem

        # Default descriptions by page type
        desc_map = {
            'affiliates': 'Partner with BetLegend for premium sports betting content and verified pick tracking.',
            'mlb-records': 'Complete MLB betting records with verified picks, units won, and detailed performance stats.',
            'nfl_analysis_example': 'Expert NFL game analysis with betting angles, key stats, and pick recommendations.',
            'nfl_week9_analysis_REAL': 'Week 9 NFL picks and analysis with advanced metrics and betting insights.',
        }

        if base in desc_map:
            return desc_map[base]

        # Try to extract from first paragraph
        first_p = soup.find('p')
        if first_p:
            text = first_p.get_text().strip()
            if len(text) > 155:
                return text[:152] + "..."
            return text

        # Generic description
        sport_keywords = {
            'mlb': 'MLB',
            'nfl': 'NFL',
            'nba': 'NBA',
            'ncaab': 'College Basketball',
            'ncaaf': 'College Football',
            'nhl': 'NHL',
            'soccer': 'Soccer'
        }

        for keyword, sport in sport_keywords.items():
            if keyword in base.lower():
                return f"Expert {sport} betting picks, analysis, and verified records from BetLegend."

        return "Expert sports betting picks and analysis with verified track records from BetLegend."

    def generate_h1_from_content(self, soup, filename):
        """Generate H1 tag from existing content or filename"""
        base = Path(filename).stem

        # Check if there's already a header we can use
        for tag in ['h2', 'h3']:
            header = soup.find(tag)
            if header:
                return header.get_text().strip()

        # Generate from title
        title = soup.find('title')
        if title:
            title_text = title.get_text().strip()
            # Remove " | BetLegend" suffix for H1
            return title_text.split('|')[0].strip()

        # Generate from filename
        words = re.sub(r'[-_]', ' ', base).title()
        return words

    def fix_missing_title(self, html_file):
        """Add missing title tag"""
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
                soup = BeautifulSoup(content, 'html.parser')

            title_tag = soup.find('title')
            new_title = self.generate_title_from_filename(str(html_file.relative_to(self.site_dir)))

            if not new_title:
                return False

            if not title_tag:
                # Create title tag
                title_tag = soup.new_tag('title')
                title_tag.string = new_title
                head = soup.find('head')
                if head:
                    head.insert(0, title_tag)
                else:
                    # Create head if it doesn't exist
                    head_tag = soup.new_tag('head')
                    title_tag = soup.new_tag('title')
                    title_tag.string = new_title
                    head_tag.append(title_tag)
                    if soup.html:
                        soup.html.insert(0, head_tag)
            else:
                title_tag.string = new_title

            # Write back
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(str(soup))

            self.fixes_applied["titles_added"].append(str(html_file.relative_to(self.site_dir)))
            return True

        except Exception as e:
            self.fixes_applied["errors"].append({
                "file": str(html_file.relative_to(self.site_dir)),
                "error": f"Title fix failed: {str(e)}"
            })
            return False

    def fix_missing_description(self, html_file):
        """Add missing meta description"""
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
                soup = BeautifulSoup(content, 'html.parser')

            meta_desc = soup.find('meta', attrs={'name': 'description'})
            new_desc = self.generate_description_from_content(soup, str(html_file.relative_to(self.site_dir)))

            if not meta_desc:
                meta_desc = soup.new_tag('meta')
                meta_desc['name'] = 'description'
                meta_desc['content'] = new_desc
                head = soup.find('head')
                if head:
                    head.append(meta_desc)
            else:
                meta_desc['content'] = new_desc

            # Write back
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(str(soup))

            self.fixes_applied["descriptions_added"].append(str(html_file.relative_to(self.site_dir)))
            return True

        except Exception as e:
            self.fixes_applied["errors"].append({
                "file": str(html_file.relative_to(self.site_dir)),
                "error": f"Description fix failed: {str(e)}"
            })
            return False

    def fix_missing_h1(self, html_file):
        """Add missing H1 tag"""
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
                soup = BeautifulSoup(content, 'html.parser')

            h1_tag = soup.find('h1')
            if h1_tag and h1_tag.get_text().strip():
                return False  # Already has H1

            new_h1_text = self.generate_h1_from_content(soup, str(html_file.relative_to(self.site_dir)))

            if not h1_tag:
                h1_tag = soup.new_tag('h1')
                h1_tag.string = new_h1_text
                # Insert after opening body tag
                body = soup.find('body')
                if body:
                    # Find first container or insert at top
                    container = body.find(['div', 'main', 'article'])
                    if container:
                        container.insert(0, h1_tag)
                    else:
                        body.insert(0, h1_tag)
            else:
                h1_tag.string = new_h1_text

            # Write back
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(str(soup))

            self.fixes_applied["h1_added"].append(str(html_file.relative_to(self.site_dir)))
            return True

        except Exception as e:
            self.fixes_applied["errors"].append({
                "file": str(html_file.relative_to(self.site_dir)),
                "error": f"H1 fix failed: {str(e)}"
            })
            return False

    def fix_missing_canonical(self, html_file):
        """Add missing canonical tag"""
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
                soup = BeautifulSoup(content, 'html.parser')

            canonical = soup.find('link', attrs={'rel': 'canonical'})
            rel_path = str(html_file.relative_to(self.site_dir)).replace('\\', '/')
            canonical_url = f"{self.base_url}/{rel_path}"

            if not canonical:
                canonical = soup.new_tag('link')
                canonical['rel'] = 'canonical'
                canonical['href'] = canonical_url
                head = soup.find('head')
                if head:
                    head.append(canonical)
            else:
                canonical['href'] = canonical_url

            # Write back
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(str(soup))

            self.fixes_applied["canonical_added"].append(str(html_file.relative_to(self.site_dir)))
            return True

        except Exception as e:
            self.fixes_applied["errors"].append({
                "file": str(html_file.relative_to(self.site_dir)),
                "error": f"Canonical fix failed: {str(e)}"
            })
            return False

    def optimize_title(self, html_file, current_title):
        """Optimize long titles and add BetLegend if missing"""
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
                soup = BeautifulSoup(content, 'html.parser')

            title_tag = soup.find('title')
            if not title_tag:
                return False

            new_title = current_title

            # Add BetLegend if missing
            if 'BetLegend' not in new_title and 'SportsBettingPrime' not in new_title:
                # Don't add to removed pages or test files
                if 'Removed Page' not in new_title and 'Test' not in new_title:
                    new_title = new_title.strip() + ' | BetLegend'

            # Shorten if too long
            if len(new_title) > 60:
                # Try to intelligently shorten
                parts = new_title.split('|')
                if len(parts) > 1:
                    # Keep main part and brand
                    main_part = parts[0].strip()
                    brand = parts[-1].strip()

                    # Shorten main part if needed
                    max_main_length = 60 - len(brand) - 3  # 3 for " | "
                    if len(main_part) > max_main_length:
                        main_part = main_part[:max_main_length-3] + "..."

                    new_title = f"{main_part} | {brand}"

            title_tag.string = new_title

            # Write back
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(str(soup))

            self.fixes_applied["titles_optimized"].append({
                "file": str(html_file.relative_to(self.site_dir)),
                "old": current_title,
                "new": new_title
            })
            return True

        except Exception as e:
            self.fixes_applied["errors"].append({
                "file": str(html_file.relative_to(self.site_dir)),
                "error": f"Title optimization failed: {str(e)}"
            })
            return False

    def run_fixes(self):
        """Run all SEO fixes based on audit data"""
        print("Starting automated SEO fixes...\n")

        # Fix missing titles
        print(f"Fixing {len(self.audit_data['missing_titles'])} missing titles...")
        for filename in self.audit_data['missing_titles']:
            file_path = self.site_dir / filename
            if file_path.exists():
                self.fix_missing_title(file_path)

        # Fix missing descriptions
        print(f"Fixing {len(self.audit_data['missing_descriptions'])} missing descriptions...")
        for filename in self.audit_data['missing_descriptions']:
            file_path = self.site_dir / filename
            if file_path.exists():
                self.fix_missing_description(file_path)

        # Fix missing H1 tags
        print(f"Fixing {len(self.audit_data['missing_h1'])} missing H1 tags...")
        for filename in self.audit_data['missing_h1']:
            file_path = self.site_dir / filename
            if file_path.exists():
                self.fix_missing_h1(file_path)

        # Fix missing canonical tags
        print(f"Fixing {len(self.audit_data['missing_canonical'])} missing canonical tags...")
        for filename in self.audit_data['missing_canonical']:
            file_path = self.site_dir / filename
            if file_path.exists():
                self.fix_missing_canonical(file_path)

        # Optimize titles without BetLegend
        print(f"Adding BetLegend to {len(self.audit_data['no_betlegend_in_title'])} titles...")
        for item in self.audit_data['no_betlegend_in_title']:
            file_path = self.site_dir / item['file']
            if file_path.exists():
                self.optimize_title(file_path, item['title'])

        # Optimize long titles
        print(f"Shortening {len(self.audit_data['long_titles'])} long titles...")
        for item in self.audit_data['long_titles']:
            file_path = self.site_dir / item['file']
            if file_path.exists():
                self.optimize_title(file_path, item['title'])

        print("\nFixes complete!")
        return self.fixes_applied

    def generate_fix_report(self, output_file="SEO_FIX_REPORT.md"):
        """Generate report of all fixes applied"""
        report = []
        report.append("# SEO Automated Fixes Report\n\n")

        report.append("## Summary\n")
        report.append(f"- Titles Added: {len(self.fixes_applied['titles_added'])}\n")
        report.append(f"- Descriptions Added: {len(self.fixes_applied['descriptions_added'])}\n")
        report.append(f"- H1 Tags Added: {len(self.fixes_applied['h1_added'])}\n")
        report.append(f"- Canonical Tags Added: {len(self.fixes_applied['canonical_added'])}\n")
        report.append(f"- Titles Optimized: {len(self.fixes_applied['titles_optimized'])}\n")
        report.append(f"- Errors: {len(self.fixes_applied['errors'])}\n\n")

        if self.fixes_applied['titles_added']:
            report.append("## Titles Added\n")
            for file in self.fixes_applied['titles_added']:
                report.append(f"- {file}\n")
            report.append("\n")

        if self.fixes_applied['descriptions_added']:
            report.append("## Descriptions Added\n")
            for file in self.fixes_applied['descriptions_added']:
                report.append(f"- {file}\n")
            report.append("\n")

        if self.fixes_applied['h1_added']:
            report.append("## H1 Tags Added\n")
            for file in self.fixes_applied['h1_added']:
                report.append(f"- {file}\n")
            report.append("\n")

        if self.fixes_applied['titles_optimized']:
            report.append("## Titles Optimized\n")
            for item in self.fixes_applied['titles_optimized']:
                report.append(f"- **{item['file']}**\n")
                report.append(f"  - Old: {item['old']}\n")
                report.append(f"  - New: {item['new']}\n")
            report.append("\n")

        if self.fixes_applied['errors']:
            report.append("## Errors Encountered\n")
            for error in self.fixes_applied['errors']:
                report.append(f"- **{error['file']}**: {error['error']}\n")
            report.append("\n")

        output_path = self.site_dir / output_file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(''.join(report))

        print(f"\nFix report generated: {output_path}")
        return output_path

if __name__ == "__main__":
    fixer = SEOFixer(
        "C:/Users/Nima/betlegendpicks",
        "C:/Users/Nima/betlegendpicks/SEO_AUDIT_DATA.json"
    )
    fixes = fixer.run_fixes()
    fixer.generate_fix_report()

    print("\n" + "="*50)
    print("SEO FIXES COMPLETE")
    print("="*50)
