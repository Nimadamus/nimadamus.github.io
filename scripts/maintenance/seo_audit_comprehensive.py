"""
Comprehensive SEO Audit Script for BetLegendPicks.com
Checks for 404s, missing metadata, broken links, and generates actionable report
"""

import os
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import json

class SEOAuditor:
    def __init__(self, site_dir):
        self.site_dir = Path(site_dir)
        self.all_html_files = list(self.site_dir.rglob("*.html"))
        self.issues = {
            "missing_files": [],
            "broken_internal_links": [],
            "missing_titles": [],
            "missing_descriptions": [],
            "missing_h1": [],
            "duplicate_titles": {},
            "long_titles": [],
            "long_descriptions": [],
            "missing_canonical": [],
            "no_betlegend_in_title": [],
            "files_without_extensions": []
        }
        self.all_valid_paths = set()
        self.base_url = "https://www.betlegendpicks.com"

    def build_valid_paths(self):
        """Build set of all valid file paths"""
        for html_file in self.all_html_files:
            rel_path = html_file.relative_to(self.site_dir)
            self.all_valid_paths.add(str(rel_path).replace('\\', '/'))
            self.all_valid_paths.add('/' + str(rel_path).replace('\\', '/'))

    def extract_links_from_html(self, html_content):
        """Extract all internal links from HTML"""
        links = []
        soup = BeautifulSoup(html_content, 'html.parser')

        for tag in soup.find_all(['a', 'link', 'script', 'img']):
            if tag.name == 'a':
                href = tag.get('href')
                if href:
                    links.append(('a', href))
            elif tag.name == 'link':
                href = tag.get('href')
                if href:
                    links.append(('link', href))
            elif tag.name == 'script':
                src = tag.get('src')
                if src:
                    links.append(('script', src))
            elif tag.name == 'img':
                src = tag.get('src')
                if src:
                    links.append(('img', src))

        return links

    def is_internal_link(self, url):
        """Check if URL is internal"""
        if not url:
            return False
        if url.startswith('#') or url.startswith('javascript:') or url.startswith('mailto:'):
            return False
        if url.startswith('http://') or url.startswith('https://'):
            parsed = urlparse(url)
            return 'betlegendpicks.com' in parsed.netloc
        return True

    def normalize_path(self, url, current_file):
        """Normalize URL path to file system path"""
        if url.startswith('http://') or url.startswith('https://'):
            parsed = urlparse(url)
            path = parsed.path.lstrip('/')
        elif url.startswith('/'):
            path = url.lstrip('/')
        else:
            # Relative path
            current_dir = current_file.parent
            path = (current_dir / url).relative_to(self.site_dir)
            path = str(path).replace('\\', '/')
            return path

        return path

    def check_metadata(self, html_file):
        """Check metadata for single HTML file"""
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
                soup = BeautifulSoup(content, 'html.parser')

                rel_path = str(html_file.relative_to(self.site_dir))

                # Check title
                title_tag = soup.find('title')
                if not title_tag or not title_tag.string or not title_tag.string.strip():
                    self.issues["missing_titles"].append(rel_path)
                else:
                    title_text = title_tag.string.strip()
                    if len(title_text) > 60:
                        self.issues["long_titles"].append({
                            "file": rel_path,
                            "title": title_text,
                            "length": len(title_text)
                        })
                    if "BetLegend" not in title_text:
                        self.issues["no_betlegend_in_title"].append({
                            "file": rel_path,
                            "title": title_text
                        })
                    # Track duplicates
                    if title_text in self.issues["duplicate_titles"]:
                        self.issues["duplicate_titles"][title_text].append(rel_path)
                    else:
                        self.issues["duplicate_titles"][title_text] = [rel_path]

                # Check meta description
                meta_desc = soup.find('meta', attrs={'name': 'description'})
                if not meta_desc or not meta_desc.get('content') or not meta_desc.get('content').strip():
                    self.issues["missing_descriptions"].append(rel_path)
                else:
                    desc_text = meta_desc.get('content').strip()
                    if len(desc_text) > 155:
                        self.issues["long_descriptions"].append({
                            "file": rel_path,
                            "description": desc_text[:100] + "...",
                            "length": len(desc_text)
                        })

                # Check H1
                h1_tag = soup.find('h1')
                if not h1_tag or not h1_tag.get_text().strip():
                    self.issues["missing_h1"].append(rel_path)

                # Check canonical
                canonical = soup.find('link', attrs={'rel': 'canonical'})
                if not canonical:
                    self.issues["missing_canonical"].append(rel_path)

        except Exception as e:
            print(f"Error checking {html_file}: {str(e)}")

    def check_broken_links(self, html_file):
        """Check for broken internal links in HTML file"""
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
                links = self.extract_links_from_html(content)

                for link_type, url in links:
                    if self.is_internal_link(url):
                        # Remove query strings and fragments
                        clean_url = url.split('?')[0].split('#')[0]
                        if not clean_url:
                            continue

                        # Check if file exists
                        if clean_url.startswith('/'):
                            check_path = self.site_dir / clean_url.lstrip('/')
                        else:
                            check_path = html_file.parent / clean_url

                        if not check_path.exists():
                            self.issues["broken_internal_links"].append({
                                "file": str(html_file.relative_to(self.site_dir)),
                                "link_type": link_type,
                                "broken_url": url
                            })
        except Exception as e:
            print(f"Error checking links in {html_file}: {str(e)}")

    def run_audit(self):
        """Run complete SEO audit"""
        print("Starting comprehensive SEO audit...")
        print(f"Found {len(self.all_html_files)} HTML files")

        self.build_valid_paths()

        # Check each file
        for i, html_file in enumerate(self.all_html_files, 1):
            if i % 10 == 0:
                print(f"Processing {i}/{len(self.all_html_files)}...")
            self.check_metadata(html_file)
            self.check_broken_links(html_file)

        # Filter duplicate titles to only show actual duplicates
        self.issues["duplicate_titles"] = {
            title: files for title, files in self.issues["duplicate_titles"].items()
            if len(files) > 1
        }

        return self.issues

    def generate_report(self, output_file="SEO_AUDIT_REPORT.md"):
        """Generate markdown report"""
        from datetime import datetime
        report = []
        report.append("# BetLegendPicks.com - SEO Audit Report\n")
        report.append(f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        report.append(f"**Total HTML Files Scanned**: {len(self.all_html_files)}\n\n")

        # Summary
        report.append("## Executive Summary\n")
        report.append(f"- Missing Titles: {len(self.issues['missing_titles'])}\n")
        report.append(f"- Missing Meta Descriptions: {len(self.issues['missing_descriptions'])}\n")
        report.append(f"- Missing H1 Tags: {len(self.issues['missing_h1'])}\n")
        report.append(f"- Missing Canonical Tags: {len(self.issues['missing_canonical'])}\n")
        report.append(f"- Titles Without 'BetLegend': {len(self.issues['no_betlegend_in_title'])}\n")
        report.append(f"- Long Titles (>60 chars): {len(self.issues['long_titles'])}\n")
        report.append(f"- Long Descriptions (>155 chars): {len(self.issues['long_descriptions'])}\n")
        report.append(f"- Duplicate Titles: {len(self.issues['duplicate_titles'])}\n")
        report.append(f"- Broken Internal Links: {len(self.issues['broken_internal_links'])}\n\n")

        # Details
        if self.issues['missing_titles']:
            report.append("## Missing Titles\n")
            for file in self.issues['missing_titles']:
                report.append(f"- {file}\n")
            report.append("\n")

        if self.issues['missing_descriptions']:
            report.append("## Missing Meta Descriptions\n")
            for file in self.issues['missing_descriptions']:
                report.append(f"- {file}\n")
            report.append("\n")

        if self.issues['missing_h1']:
            report.append("## Missing H1 Tags\n")
            for file in self.issues['missing_h1']:
                report.append(f"- {file}\n")
            report.append("\n")

        if self.issues['missing_canonical']:
            report.append("## Missing Canonical Tags\n")
            for file in self.issues['missing_canonical']:
                report.append(f"- {file}\n")
            report.append("\n")

        if self.issues['no_betlegend_in_title']:
            report.append("## Titles Missing 'BetLegend' Branding\n")
            for item in self.issues['no_betlegend_in_title']:
                report.append(f"- **{item['file']}**: \"{item['title']}\"\n")
            report.append("\n")

        if self.issues['long_titles']:
            report.append("## Titles Too Long (>60 chars)\n")
            for item in self.issues['long_titles']:
                report.append(f"- **{item['file']}** ({item['length']} chars): \"{item['title'][:80]}...\"\n")
            report.append("\n")

        if self.issues['duplicate_titles']:
            report.append("## Duplicate Titles (SEO Issue)\n")
            for title, files in self.issues['duplicate_titles'].items():
                report.append(f"### \"{title}\"\n")
                for file in files:
                    report.append(f"  - {file}\n")
                report.append("\n")

        if self.issues['broken_internal_links']:
            report.append("## Broken Internal Links (404 Errors)\n")
            seen = set()
            for item in self.issues['broken_internal_links']:
                key = f"{item['file']}|{item['broken_url']}"
                if key not in seen:
                    report.append(f"- **{item['file']}** → `{item['broken_url']}` ({item['link_type']} tag)\n")
                    seen.add(key)
            report.append("\n")

        # Action items
        report.append("## Recommended Actions\n\n")
        report.append("### Priority 1: Critical Fixes\n")
        report.append("1. Fix all broken internal links (404 errors)\n")
        report.append("2. Add missing meta descriptions to all pages\n")
        report.append("3. Add missing H1 tags to all pages\n")
        report.append("4. Add canonical tags to all pages\n\n")

        report.append("### Priority 2: Optimization\n")
        report.append("1. Add 'BetLegend' branding to all page titles\n")
        report.append("2. Shorten titles to under 60 characters\n")
        report.append("3. Resolve duplicate title issues\n")
        report.append("4. Shorten meta descriptions to under 155 characters\n\n")

        # Write report
        output_path = self.site_dir / output_file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(''.join(report))

        print(f"\nReport generated: {output_path}")
        return output_path

if __name__ == "__main__":
    auditor = SEOAuditor("C:/Users/Nima/betlegendpicks")
    issues = auditor.run_audit()
    report_path = auditor.generate_report()

    # Also save JSON for programmatic access
    json_path = Path("C:/Users/Nima/betlegendpicks/SEO_AUDIT_DATA.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(issues, f, indent=2)

    print(f"\nAudit complete!")
    print(f"Report: {report_path}")
    print(f"Data: {json_path}")
