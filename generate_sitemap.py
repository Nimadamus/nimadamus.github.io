#!/usr/bin/env python3
"""
Generate sitemap.xml for BetLegend site
"""
from datetime import datetime
import os

BASE_URL = "https://www.betlegendpicks.com"

# All pages with their priorities and change frequencies
pages = {
    # Homepage - highest priority
    'index.html': {'priority': '1.0', 'changefreq': 'daily'},

    # Blog/Picks pages - very high priority (main content)
    'blog.html': {'priority': '0.9', 'changefreq': 'daily'},
    'blog-page2.html': {'priority': '0.9', 'changefreq': 'daily'},
    'blog-page3.html': {'priority': '0.9', 'changefreq': 'daily'},
    'blog-page4.html': {'priority': '0.9', 'changefreq': 'daily'},
    'blog-page5.html': {'priority': '0.9', 'changefreq': 'daily'},
    'blog-page6.html': {'priority': '0.9', 'changefreq': 'daily'},
    'blog-page7.html': {'priority': '0.9', 'changefreq': 'daily'},
    'blog-page8.html': {'priority': '0.9', 'changefreq': 'daily'},

    # News pages - high priority (updated frequently)
    'news.html': {'priority': '0.8', 'changefreq': 'daily'},
    'news-page2.html': {'priority': '0.8', 'changefreq': 'daily'},
    'news-page3.html': {'priority': '0.8', 'changefreq': 'daily'},

    # Records pages - high priority (important for SEO)
    'betlegend-verified-records.html': {'priority': '0.8', 'changefreq': 'weekly'},
    'nfl-records.html': {'priority': '0.8', 'changefreq': 'weekly'},
    'ncaaf-records.html': {'priority': '0.8', 'changefreq': 'weekly'},
    'nhl-records.html': {'priority': '0.8', 'changefreq': 'weekly'},
    'nba-records.html': {'priority': '0.8', 'changefreq': 'weekly'},
    'soccer-records.html': {'priority': '0.8', 'changefreq': 'weekly'},
    'records.html': {'priority': '0.7', 'changefreq': 'weekly'},

    # Sport-specific pages
    'mlb-page2.html': {'priority': '0.7', 'changefreq': 'daily'},
    'mlb-historical.html': {'priority': '0.6', 'changefreq': 'monthly'},
    'nfl.html': {'priority': '0.7', 'changefreq': 'daily'},
    'nba.html': {'priority': '0.7', 'changefreq': 'daily'},
    'nhl.html': {'priority': '0.7', 'changefreq': 'daily'},
    'ncaaf.html': {'priority': '0.7', 'changefreq': 'weekly'},

    # Calculator pages (important tools)
    'betting-calculators.html': {'priority': '0.7', 'changefreq': 'monthly'},
    'expected-value-calculator.html': {'priority': '0.6', 'changefreq': 'monthly'},
    'implied-probability-calculator.html': {'priority': '0.6', 'changefreq': 'monthly'},
    'odds-converter.html': {'priority': '0.6', 'changefreq': 'monthly'},
    'parlay-calculator.html': {'priority': '0.6', 'changefreq': 'monthly'},
    'kelly-criterion.html': {'priority': '0.6', 'changefreq': 'monthly'},

    # Feature pages
    'featured-game-of-the-day.html': {'priority': '0.7', 'changefreq': 'daily'},
    'betting-101.html': {'priority': '0.6', 'changefreq': 'monthly'},
    'bestonlinesportsbook.html': {'priority': '0.6', 'changefreq': 'monthly'},
    'live-odds.html': {'priority': '0.7', 'changefreq': 'daily'},
    'bankroll.html': {'priority': '0.5', 'changefreq': 'monthly'},
    'screenshots.html': {'priority': '0.5', 'changefreq': 'monthly'},
    'proofofpicks.html': {'priority': '0.7', 'changefreq': 'weekly'},
    'howitworks.html': {'priority': '0.6', 'changefreq': 'monthly'},

    # Other pages
    'upcomingpicks.html': {'priority': '0.6', 'changefreq': 'daily'},
    'subscribe.html': {'priority': '0.4', 'changefreq': 'monthly'},
}

def generate_sitemap():
    """Generate sitemap.xml"""

    # Get current date in ISO format
    today = datetime.now().strftime('%Y-%m-%d')

    # Start sitemap XML
    sitemap = ['<?xml version="1.0" encoding="UTF-8"?>']
    sitemap.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')

    # Add each page
    for page, config in sorted(pages.items()):
        # Check if file exists
        if os.path.exists(page):
            # Get last modified date
            try:
                mtime = os.path.getmtime(page)
                lastmod = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d')
            except:
                lastmod = today

            sitemap.append('  <url>')
            sitemap.append(f'    <loc>{BASE_URL}/{page}</loc>')
            sitemap.append(f'    <lastmod>{lastmod}</lastmod>')
            sitemap.append(f'    <changefreq>{config["changefreq"]}</changefreq>')
            sitemap.append(f'    <priority>{config["priority"]}</priority>')
            sitemap.append('  </url>')

    sitemap.append('</urlset>')

    return '\n'.join(sitemap)

def main():
    sitemap_content = generate_sitemap()

    # Write sitemap
    with open('sitemap.xml', 'w', encoding='utf-8') as f:
        f.write(sitemap_content)

    print("Sitemap generated successfully!")
    print(f"Total URLs: {len(pages)}")
    print("\nPriority distribution:")
    priorities = {}
    for config in pages.values():
        p = config['priority']
        priorities[p] = priorities.get(p, 0) + 1

    for priority in sorted(priorities.keys(), reverse=True):
        print(f"  {priority}: {priorities[priority]} pages")

    print("\nSitemap written to: sitemap.xml")

if __name__ == '__main__':
    main()
