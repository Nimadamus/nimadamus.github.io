#!/usr/bin/env python3
"""
BetLegend SEO Optimization Script
Systematically optimizes all HTML pages for SEO without losing content
"""

import os
import re
from datetime import datetime

# Page-specific SEO data
PAGE_SEO_DATA = {
    'index.html': {
        'title': 'BetLegend - Sports Betting Picks, Analysis & Predictions',
        'description': 'BetLegend provides expert sports betting picks, analysis, and predictions for NFL, NBA, NHL, MLB, and NCAAF. Data-driven insights and verified track records.',
        'keywords': 'sports betting picks, NFL picks, NBA picks, NHL picks, betting analysis, sports predictions',
        'h1': 'BetLegend - Expert Sports Betting Analysis'
    },
    'nfl.html': {
        'title': 'NFL Betting Picks & Analysis | BetLegend',
        'description': 'Expert NFL betting picks, game analysis, spreads, totals, and prop bets. Daily predictions powered by advanced analytics and years of betting experience.',
        'keywords': 'NFL picks, NFL predictions, NFL betting, football picks, NFL spreads, NFL totals',
        'h1': None  # Already has H1
    },
    'nba.html': {
        'title': 'NBA Betting Picks & Analysis | BetLegend',
        'description': '2024-25 NBA season recap – Thunder win their first championship, key offseason storylines, free agency rumors, and expert NBA betting picks from BetLegend.',
        'keywords': 'NBA picks, basketball predictions, NBA betting model, NBA analysis, championship odds',
        'h1': None  # Already has H1
    },
    'nhl.html': {
        'title': 'NHL Betting Picks & Analysis | BetLegend',
        'description': 'Expert NHL betting picks, puck lines, totals, and prop bets. Daily hockey predictions powered by advanced analytics and goaltending matchup analysis.',
        'keywords': 'NHL picks, NHL predictions, hockey betting, puck line, NHL totals, goalie matchups',
        'h1': None  # Already has H1
    },
    'mlb.html': {
        'title': 'MLB Betting Picks & Analysis | BetLegend',
        'description': 'Expert MLB betting picks, run lines, totals, and prop bets. Daily baseball predictions powered by advanced analytics and pitcher matchup analysis.',
        'keywords': 'MLB picks, MLB predictions, baseball betting, run line, MLB totals, pitcher matchups',
        'h1': 'MLB Betting Hub'
    },
    'ncaaf.html': {
        'title': 'College Football Betting Picks & Analysis | BetLegend',
        'description': 'Expert NCAAF betting picks, spreads, totals, and prop bets. College football predictions powered by advanced analytics and conference insights.',
        'keywords': 'college football picks, NCAAF predictions, college football betting, NCAAF spreads',
        'h1': 'NCAAF Betting Hub'
    },
    'blog.html': {
        'title': 'Sports Betting Blog & News | BetLegend',
        'description': 'Latest sports betting news, analysis, strategies, and insights. Daily updates on NFL, NBA, NHL, MLB, and college football betting markets.',
        'keywords': 'sports betting blog, betting news, betting strategies, sports analysis',
        'h1': 'BetLegend Blog'
    },
    'upcomingpicks.html': {
        'title': 'Upcoming Betting Picks | BetLegend',
        'description': 'View all upcoming sports betting picks across NFL, NBA, NHL, MLB, and NCAAF. Updated daily with expert analysis and betting lines.',
        'keywords': 'upcoming picks, today\'s picks, betting picks, sports predictions',
        'h1': 'Upcoming Picks'
    },
    'betlegend-verified-records.html': {
        'title': 'Verified Betting Records | BetLegend',
        'description': 'Transparent, verified betting records across all sports. Track our performance with detailed win-loss records, ROI, and unit tracking.',
        'keywords': 'verified records, betting track record, sports betting results, ROI',
        'h1': 'Verified Betting Records'
    },
    'betting-calculators.html': {
        'title': 'Betting Calculators & Tools | BetLegend',
        'description': 'Free sports betting calculators including parlay, Kelly Criterion, odds converter, implied probability, and expected value calculators.',
        'keywords': 'betting calculator, parlay calculator, Kelly Criterion, odds converter',
        'h1': 'Betting Calculators'
    },
    'bankroll.html': {
        'title': 'Bankroll Management Guide | BetLegend',
        'description': 'Learn professional bankroll management strategies for sports betting. Unit sizing, Kelly Criterion, and risk management fundamentals.',
        'keywords': 'bankroll management, betting units, Kelly Criterion, risk management',
        'h1': 'Bankroll Management'
    },
    'betting-101.html': {
        'title': 'Sports Betting 101 - Beginner\'s Guide | BetLegend',
        'description': 'Complete beginner\'s guide to sports betting. Learn spreads, moneylines, totals, props, and fundamental betting strategies.',
        'keywords': 'betting guide, how to bet, sports betting basics, betting for beginners',
        'h1': 'Sports Betting 101'
    },
    'kelly-criterion.html': {
        'title': 'Kelly Criterion Calculator | BetLegend',
        'description': 'Free Kelly Criterion calculator for optimal bet sizing. Calculate the exact percentage of your bankroll to wager based on edge and odds.',
        'keywords': 'Kelly Criterion, bet sizing, bankroll calculator, optimal bets',
        'h1': 'Kelly Criterion Calculator'
    },
    'parlay-calculator.html': {
        'title': 'Parlay Calculator | BetLegend',
        'description': 'Free parlay calculator for sports betting. Calculate payouts for 2-12 leg parlays with American, Decimal, or Fractional odds.',
        'keywords': 'parlay calculator, parlay payout, multi-leg bets, parlay odds',
        'h1': 'Parlay Calculator'
    },
    'odds-converter.html': {
        'title': 'Odds Converter | BetLegend',
        'description': 'Convert betting odds between American, Decimal, Fractional, and Implied Probability formats instantly.',
        'keywords': 'odds converter, American odds, decimal odds, fractional odds',
        'h1': 'Odds Converter'
    },
    'implied-probability-calculator.html': {
        'title': 'Implied Probability Calculator | BetLegend',
        'description': 'Calculate implied probability from betting odds. Convert American, Decimal, or Fractional odds to probability percentages.',
        'keywords': 'implied probability, betting odds probability, odds to percentage',
        'h1': 'Implied Probability Calculator'
    },
    'expected-value-calculator.html': {
        'title': 'Expected Value (EV) Calculator | BetLegend',
        'description': 'Calculate expected value for sports bets. Determine if a bet has positive expected value (EV+) based on your edge.',
        'keywords': 'expected value, EV calculator, positive EV, value betting',
        'h1': 'Expected Value Calculator'
    },
    'bestonlinesportsbook.html': {
        'title': 'Best Online Sportsbooks 2025 | BetLegend',
        'description': 'Compare the best online sportsbooks for 2025. Reviews, bonuses, and recommendations for NFL, NBA, NHL, and MLB betting.',
        'keywords': 'best sportsbooks, online betting sites, sportsbook reviews, betting bonuses',
        'h1': 'Best Online Sportsbooks'
    },
    'howitworks.html': {
        'title': 'How BetLegend Works | Betting System Explained',
        'description': 'Learn how BetLegend\'s betting system works. Our methodology, analytics, and approach to sports betting predictions explained.',
        'keywords': 'betting system, how it works, betting methodology, prediction model',
        'h1': 'How BetLegend Works'
    },
}

# Core pages that should be in main navigation
CORE_NAV_PAGES = [
    ('index.html', 'Home'),
    ('nfl.html', 'NFL'),
    ('nba.html', 'NBA'),
    ('nhl.html', 'NHL'),
    ('mlb.html', 'MLB'),
    ('ncaaf.html', 'NCAAF'),
    ('blog.html', 'Blog'),
    ('upcomingpicks.html', 'Upcoming Picks'),
    ('betlegend-verified-records.html', 'Verified Records'),
]

def add_seo_meta_tags(content, filename):
    """Add or update SEO meta tags"""

    if filename not in PAGE_SEO_DATA:
        return content

    seo_data = PAGE_SEO_DATA[filename]

    # Update title if missing or generic
    if '<title>' in content:
        content = re.sub(r'<title>.*?</title>',
                        f'<title>{seo_data["title"]}</title>',
                        content, flags=re.DOTALL)
    else:
        # Insert after <head>
        content = content.replace('<head>', f'<head>\n    <title>{seo_data["title"]}</title>')

    # Add canonical URL
    canonical = f'<link rel="canonical" href="https://www.betlegendpicks.com/{filename}"/>'
    if 'rel="canonical"' not in content:
        # Insert after meta viewport or after <head>
        if '<meta name="viewport"' in content:
            content = content.replace('name="viewport"', f'name="viewport"\n{canonical}', 1).replace(f'name="viewport"\n{canonical}', f'name="viewport"/>\n{canonical}')
        else:
            content = content.replace('<head>', f'<head>\n{canonical}')

    # Add meta description
    if seo_data['description']:
        if 'name="description"' in content:
            content = re.sub(r'<meta.*?name="description".*?content=".*?".*?/?>',
                           f'<meta name="description" content="{seo_data["description"]}"/>',
                           content)
        else:
            # Insert after canonical
            content = content.replace(canonical, f'{canonical}\n<meta name="description" content="{seo_data["description"]}"/>')

    # Add meta keywords
    if seo_data['keywords']:
        if 'name="keywords"' in content:
            content = re.sub(r'<meta.*?name="keywords".*?content=".*?".*?/?>',
                           f'<meta name="keywords" content="{seo_data["keywords"]}"/>',
                           content)
        else:
            # Insert after description
            desc_tag = f'<meta name="description" content="{seo_data["description"]}"/>'
            if desc_tag in content:
                content = content.replace(desc_tag, f'{desc_tag}\n<meta name="keywords" content="{seo_data["keywords"]}"/>')

    # Add Open Graph tags
    og_tags = f'''<meta property="og:title" content="{seo_data["title"]}"/>
<meta property="og:description" content="{seo_data["description"]}"/>
<meta property="og:url" content="https://www.betlegendpicks.com/{filename}"/>
<meta property="og:type" content="website"/>
<meta property="og:site_name" content="BetLegend"/>'''

    if 'property="og:' not in content:
        # Insert after meta tags
        keywords_tag = f'<meta name="keywords" content="{seo_data["keywords"]}"/>'
        if keywords_tag in content:
            content = content.replace(keywords_tag, f'{keywords_tag}\n{og_tags}')

    return content

def fix_internal_links(content, current_file):
    """Ensure all internal links use proper format"""

    # Fix relative links to be consistent
    content = re.sub(r'href="\./([\w\-]+\.html)"', r'href="\1"', content)

    # Ensure main nav links are present (if there's a nav section)
    if '<nav' in content or 'nav-links' in content:
        # This will be handled separately for each page type
        pass

    return content

def add_structured_data(content, filename):
    """Add JSON-LD structured data for better search visibility"""

    if filename in ['index.html']:
        schema = '''<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "WebSite",
  "name": "BetLegend",
  "url": "https://www.betlegendpicks.com",
  "description": "Expert sports betting picks and analysis",
  "potentialAction": {
    "@type": "SearchAction",
    "target": "https://www.betlegendpicks.com/search?q={search_term_string}",
    "query-input": "required name=search_term_string"
  }
}
</script>'''

        if '</head>' in content and 'application/ld+json' not in content:
            content = content.replace('</head>', f'{schema}\n</head>')

    return content

def optimize_page(filename):
    """Optimize a single HTML page"""

    try:
        with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        original_content = content

        # Apply optimizations
        content = add_seo_meta_tags(content, filename)
        content = fix_internal_links(content, filename)
        content = add_structured_data(content, filename)

        # Only write if changed
        if content != original_content:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            return True

        return False

    except Exception as e:
        print(f"Error processing {filename}: {e}")
        return False

def main():
    """Main optimization function"""

    print("BetLegend SEO Optimization")
    print("=" * 50)

    optimized = 0
    skipped = 0

    for file in os.listdir('.'):
        if file.endswith('.html') and file != 'google6f74b54ecd988601.html':
            print(f"Processing {file}...", end=' ')

            if optimize_page(file):
                print("[OK] Optimized")
                optimized += 1
            else:
                print("[ ] Skipped (no changes)")
                skipped += 1

    print("\n" + "=" * 50)
    print(f"Optimization complete!")
    print(f"  Optimized: {optimized} pages")
    print(f"  Skipped: {skipped} pages")

if __name__ == '__main__':
    main()
