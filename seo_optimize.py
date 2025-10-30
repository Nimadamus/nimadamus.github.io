#!/usr/bin/env python3
"""
SEO Optimization Script for BetLegend
Adds meta descriptions, Open Graph tags, and schema markup
"""

import re
import os

# Meta descriptions for each page
META_DESCRIPTIONS = {
    'blog-page8.html': 'Free daily sports betting picks with full analysis. Expert MLB, NFL, NBA, NHL predictions backed by data. Verified 65% win rate. Get today\'s free picks now.',
    'news-page3.html': 'Latest sports betting news and headlines. Breaking updates on MLB, NFL, NBA, NHL, and betting industry. Stay informed with BetLegend News.',
    'nfl.html': 'NFL betting picks and analysis. Expert predictions for every game with verified track record. Free NFL picks, spreads, totals, and prop bets.',
    'nba.html': 'NBA betting picks and predictions. Daily basketball picks with analysis, player props, and game totals. Expert NBA betting advice.',
    'mlb-page2.html': 'MLB betting picks and baseball predictions. Daily moneyline, run line, and total picks. Expert baseball betting analysis with verified results.',
    'ncaaf.html': 'College football betting picks and NCAAF predictions. Expert analysis on spreads, totals, and moneylines. Free college football picks daily.',
    'betting-101.html': 'Sports betting guide for beginners. Learn how to bet on sports, understand odds, manage bankroll, and win consistently. Complete betting tutorial.',
    'live-odds.html': 'Live sports betting odds and lines. Real-time odds for MLB, NFL, NBA, NHL. Compare sportsbook lines and find the best value.',
    'proofofpicks.html': 'Verified betting picks and results. Transparent track record with screenshots and proof. See our documented wins and losses.',
    'featured-game-of-the-day.html': 'Featured game of the day betting pick. In-depth analysis on today\'s best betting opportunity. Expert prediction with full breakdown.',
}

# Open Graph tags template
OG_TAGS_TEMPLATE = """<meta property="og:title" content="{title}"/>
<meta property="og:description" content="{description}"/>
<meta property="og:url" content="https://www.betlegendpicks.com/{filename}"/>
<meta property="og:type" content="website"/>
<meta property="og:image" content="https://www.betlegendpicks.com/newlogo.png"/>
<meta property="og:site_name" content="BetLegend Picks"/>"""

# Twitter Card tags
TWITTER_TAGS = """<meta name="twitter:card" content="summary_large_image"/>
<meta name="twitter:site" content="@BetLegend2025"/>
<meta name="twitter:title" content="{title}"/>
<meta name="twitter:description" content="{description}"/>
<meta name="twitter:image" content="https://www.betlegendpicks.com/newlogo.png"/>"""

def extract_title(content):
    """Extract page title from HTML"""
    match = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(1).strip()
    return "BetLegend Picks"

def add_meta_description(filepath, description):
    """Add meta description to HTML file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check if meta description already exists
    if 'meta name="description"' in content.lower():
        print(f"[SKIP] {filepath} - Already has meta description")
        return False

    # Extract title for OG tags
    title = extract_title(content)
    filename = os.path.basename(filepath)

    # Create meta description tag
    meta_desc = f'<meta name="description" content="{description}"/>'

    # Create OG tags
    og_tags = OG_TAGS_TEMPLATE.format(
        title=title,
        description=description,
        filename=filename
    )

    # Create Twitter tags
    twitter_tags = TWITTER_TAGS.format(
        title=title,
        description=description
    )

    # Find insertion point (after charset or viewport meta tag)
    # Try to insert after <head> tag
    if '<head>' in content:
        # Insert after <head>
        content = content.replace('<head>', f'<head>\n{meta_desc}\n{og_tags}\n{twitter_tags}', 1)
    elif re.search(r'<meta.*?charset', content, re.IGNORECASE):
        # Insert after charset
        content = re.sub(
            r'(<meta[^>]*?charset[^>]*?>)',
            r'\1\n' + meta_desc + '\n' + og_tags + '\n' + twitter_tags,
            content,
            count=1,
            flags=re.IGNORECASE
        )
    else:
        print(f"[ERROR] {filepath} - Could not find insertion point")
        return False

    # Write back
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"[OK] {filepath} - Added meta description + OG tags + Twitter tags")
    return True

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))

    updated_count = 0
    for filename, description in META_DESCRIPTIONS.items():
        filepath = os.path.join(base_dir, filename)
        if os.path.exists(filepath):
            if add_meta_description(filepath, description):
                updated_count += 1
        else:
            print(f"[SKIP] {filename} - File not found")

    print(f"\n[OK] Updated {updated_count} files")

if __name__ == '__main__':
    main()
