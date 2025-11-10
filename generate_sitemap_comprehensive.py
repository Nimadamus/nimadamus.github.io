"""
Generate comprehensive sitemap.xml for BetLegendPicks.com
Includes all pages with proper priority and changefreq settings
"""

from pathlib import Path
from datetime import datetime
import xml.etree.ElementTree as ET
from xml.dom import minidom

class SitemapGenerator:
    def __init__(self, site_dir, base_url):
        self.site_dir = Path(site_dir)
        self.base_url = base_url.rstrip('/')
        self.urls = []

    def get_priority_and_freq(self, filepath):
        """Determine priority and change frequency based on page type"""
        filename = filepath.name.lower()
        rel_path = str(filepath.relative_to(self.site_dir)).lower()

        # Skip certain files
        skip_files = [
            'google6f74b54ecd988601.html',
            'input.html',
            'test_avg_odds.html',
            'nfl_analysis_example.html',
            'email.html',
            'best-online-sportsbook-old.html',
            'nfl-records-broken-backup.html',
            'blog-page8.html.backup',
            'ncaab-records.html.backup'
        ]

        if filename in skip_files:
            return None, None

        # Skip consensus_library archive and history
        if 'consensus_library' in rel_path and ('archive' in rel_path or 'history' in rel_path):
            return None, None

        # Homepage
        if filename == 'index.html':
            return 1.0, 'daily'

        # Main sport pages (live data)
        if filename in ['nfl.html', 'mlb.html', 'nba.html', 'ncaaf.html', 'ncaab.html', 'nhl.html', 'soccer.html']:
            return 0.9, 'daily'

        # Records pages
        if 'records' in filename:
            return 0.9, 'weekly'

        # Betting tools and calculators
        if any(term in filename for term in ['calculator', 'odds-converter', 'betting-101', 'betting-glossary']):
            return 0.8, 'monthly'

        # Blog and news pages
        if 'blog' in filename or 'news' in filename:
            if 'page' in filename:
                # Pagination pages have lower priority
                return 0.6, 'weekly'
            return 0.8, 'daily'

        # Featured content
        if any(term in filename for term in ['featured', 'best-bets', 'sharp-consensus']):
            return 0.8, 'daily'

        # Analysis pages
        if any(term in filename for term in ['analysis', 'breakdown', 'sunday-analytics']):
            return 0.7, 'weekly'

        # Static content pages
        if any(term in filename for term in ['howitworks', 'contact', 'subscribe', 'proofofpicks', 'screenshots']):
            return 0.7, 'monthly'

        # Regional betting pages
        if 'new-york' in filename or 'bestonlinesportsbook' in filename:
            return 0.7, 'monthly'

        # Secondary pages
        if filename in ['upcomingpicks.html', 'bankroll.html', 'sitemap.html']:
            return 0.6, 'weekly'

        # Default for other HTML pages
        return 0.5, 'monthly'

    def add_url(self, filepath):
        """Add a URL to the sitemap"""
        priority, changefreq = self.get_priority_and_freq(filepath)

        if priority is None:
            return False

        # Get relative path and convert to URL
        rel_path = str(filepath.relative_to(self.site_dir)).replace('\\', '/')
        url = f"{self.base_url}/{rel_path}"

        # Get last modified time
        lastmod = datetime.fromtimestamp(filepath.stat().st_mtime).strftime('%Y-%m-%d')

        self.urls.append({
            'loc': url,
            'lastmod': lastmod,
            'changefreq': changefreq,
            'priority': priority
        })

        return True

    def generate_sitemap(self):
        """Generate the sitemap XML"""
        # Find all HTML files
        html_files = list(self.site_dir.rglob("*.html"))
        print(f"Found {len(html_files)} HTML files")

        # Add each URL
        added = 0
        skipped = 0
        for html_file in html_files:
            if self.add_url(html_file):
                added += 1
            else:
                skipped += 1

        print(f"Added {added} URLs to sitemap")
        print(f"Skipped {skipped} files")

        # Sort by priority (highest first)
        self.urls.sort(key=lambda x: x['priority'], reverse=True)

        # Create XML
        urlset = ET.Element('urlset')
        urlset.set('xmlns', 'http://www.sitemaps.org/schemas/sitemap/0.9')

        for url_data in self.urls:
            url = ET.SubElement(urlset, 'url')

            loc = ET.SubElement(url, 'loc')
            loc.text = url_data['loc']

            lastmod = ET.SubElement(url, 'lastmod')
            lastmod.text = url_data['lastmod']

            changefreq = ET.SubElement(url, 'changefreq')
            changefreq.text = url_data['changefreq']

            priority = ET.SubElement(url, 'priority')
            priority.text = str(url_data['priority'])

        # Pretty print XML
        xml_str = ET.tostring(urlset, encoding='utf-8')
        parsed = minidom.parseString(xml_str)
        pretty_xml = parsed.toprettyxml(indent="  ", encoding='utf-8').decode('utf-8')

        # Remove extra blank lines
        lines = [line for line in pretty_xml.split('\n') if line.strip()]
        pretty_xml = '\n'.join(lines)

        return pretty_xml

    def save_sitemap(self, output_file='sitemap.xml'):
        """Save sitemap to file"""
        sitemap_content = self.generate_sitemap()

        output_path = self.site_dir / output_file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(sitemap_content)

        print(f"\nSitemap saved to: {output_path}")
        print(f"Total URLs: {len(self.urls)}")

        return output_path

    def generate_report(self):
        """Generate a report of URLs in the sitemap"""
        report = []
        report.append("# Sitemap Generation Report\n\n")
        report.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        report.append(f"**Total URLs**: {len(self.urls)}\n\n")

        # Group by priority
        priority_groups = {}
        for url in self.urls:
            priority = url['priority']
            if priority not in priority_groups:
                priority_groups[priority] = []
            priority_groups[priority].append(url)

        report.append("## URLs by Priority\n\n")
        for priority in sorted(priority_groups.keys(), reverse=True):
            urls = priority_groups[priority]
            report.append(f"### Priority {priority} ({len(urls)} URLs)\n")
            for url_data in urls[:20]:  # Show first 20
                report.append(f"- {url_data['loc'].split('/')[-1]} (changefreq: {url_data['changefreq']})\n")
            if len(urls) > 20:
                report.append(f"  ... and {len(urls) - 20} more\n")
            report.append("\n")

        report_path = self.site_dir / 'SITEMAP_REPORT.md'
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(''.join(report))

        print(f"Report saved to: {report_path}")
        return report_path

if __name__ == "__main__":
    generator = SitemapGenerator(
        site_dir="C:/Users/Nima/betlegendpicks",
        base_url="https://www.betlegendpicks.com"
    )

    sitemap_path = generator.save_sitemap()
    report_path = generator.generate_report()

    print("\n" + "="*50)
    print("SITEMAP GENERATION COMPLETE")
    print("="*50)
    print(f"\nNext steps:")
    print(f"1. Upload sitemap.xml to your site root")
    print(f"2. Submit to Google Search Console")
    print(f"3. Submit to Bing Webmaster Tools")
