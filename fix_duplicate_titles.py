"""
Fix duplicate titles across BetLegendPicks.com
"""

from pathlib import Path
from bs4 import BeautifulSoup

def update_title(file_path, new_title, new_description=None):
    """Update title and optionally description for a file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            soup = BeautifulSoup(content, 'html.parser')

        # Update title
        title_tag = soup.find('title')
        if title_tag:
            title_tag.string = new_title
        else:
            title_tag = soup.new_tag('title')
            title_tag.string = new_title
            head = soup.find('head')
            if head:
                head.insert(0, title_tag)

        # Update description if provided
        if new_description:
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc:
                meta_desc['content'] = new_description
            else:
                meta_desc = soup.new_tag('meta')
                meta_desc['name'] = 'description'
                meta_desc['content'] = new_description
                head = soup.find('head')
                if head:
                    head.append(meta_desc)

        # Write back
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))

        print(f"[OK] Updated: {file_path.name} -> {new_title}")
        return True

    except Exception as e:
        print(f"[ERROR] Error updating {file_path.name}: {str(e)}")
        return False

def main():
    site_dir = Path("C:/Users/Nima/betlegendpicks")

    print("Fixing duplicate 'Page Moved - BetLegend' titles...\n")

    # Files with "Page Moved - BetLegend" that need unique titles
    page_moved_files = {
        'affiliates.html': (
            'Affiliate Program | Partner with BetLegend',
            'Join the BetLegend affiliate program and earn commissions promoting premium sports betting picks and verified records.'
        ),
        'best-online-sportsbook-old.html': (
            'Best Online Sportsbooks 2024 | BetLegend',
            'Compare top-rated online sportsbooks with exclusive bonuses, betting markets, and expert reviews from BetLegend.'
        ),
        'bestbook.html': (
            'Best Sportsbooks for Betting | BetLegend Guide',
            'Find the best sportsbooks for your betting needs with our comprehensive guide to bonuses, odds, and features.'
        ),
        'daily-mlb-breakdown-picks-july-26-2025.html': (
            'Daily MLB Picks - July 26, 2025 | BetLegend',
            'Expert MLB betting picks and analysis for July 26, 2025 with advanced stats, pitcher matchups, and game predictions.'
        ),
        'daily-picks.html': (
            'Daily Sports Picks | BetLegend Today',
            'Today\'s expert sports betting picks across all major leagues with analysis, stats, and verified track records.'
        ),
        'FreeAlerts.html': (
            'Free Betting Alerts | BetLegend Picks',
            'Get free betting alerts and pick notifications from BetLegend\'s expert handicappers delivered to your inbox.'
        ),
        'how-to-bet-mlb-totals.html': (
            'How to Bet MLB Totals | BetLegend Guide',
            'Master MLB totals betting with expert strategies, weather analysis, pitcher tendencies, and bankroll management tips.'
        ),
        'matchups.html': (
            'Today\'s Matchups & Betting Lines | BetLegend',
            'Live sports matchups with real-time betting lines, odds comparisons, and expert analysis for today\'s games.'
        ),
        'model.html': (
            'BetLegend Prediction Model | How It Works',
            'Learn how BetLegend\'s advanced prediction model uses data analytics and machine learning for sports betting picks.'
        ),
        'odds.html': (
            'Live Sports Betting Odds | BetLegend',
            'Real-time sports betting odds across all major leagues with line movement tracking and best book comparisons.'
        ),
        'picks-archive.html': (
            'Picks Archive | Historical Results | BetLegend',
            'Browse BetLegend\'s complete archive of historical picks with verified results and performance analytics.'
        ),
        'picks.html': (
            'Expert Sports Picks | BetLegend Today',
            'Today\'s premium sports picks from BetLegend with detailed analysis, betting angles, and edge identification.'
        ),
        'smartbets.html': (
            'Smart Bets & Value Plays | BetLegend',
            'Discover today\'s smart bets and high-value plays identified by BetLegend\'s prediction models and expert analysis.'
        ),
        'social.html': (
            'Follow BetLegend | Social Media',
            'Follow BetLegend on social media for free picks, betting tips, analysis, and community engagement.'
        ),
        'track-record.html': (
            'Verified Track Record | BetLegend Results',
            'View BetLegend\'s complete verified track record with transparent results, units won, and sport-by-sport breakdowns.'
        ),
    }

    for filename, (new_title, new_desc) in page_moved_files.items():
        file_path = site_dir / filename
        if file_path.exists():
            update_title(file_path, new_title, new_desc)

    print("\nFixing duplicate news page titles...\n")

    # News pages need unique titles
    news_files = {
        'news.html': (
            'Sports Betting News | Latest Updates | BetLegend',
            'Latest sports betting news, legal updates, industry insights, and analysis from BetLegend\'s expert team.'
        ),
        'news-page2.html': (
            'Sports Betting News - Page 2 | BetLegend',
            'More sports betting news, trends, and analysis from BetLegend covering all major sports and betting markets.'
        ),
        'news-page3.html': (
            'Sports Betting News - Page 3 | BetLegend',
            'Additional sports betting news and insights from BetLegend\'s coverage of the betting industry.'
        ),
    }

    for filename, (new_title, new_desc) in news_files.items():
        file_path = site_dir / filename
        if file_path.exists():
            update_title(file_path, new_title, new_desc)

    print("\n" + "="*50)
    print("DUPLICATE TITLE FIXES COMPLETE")
    print("="*50)

if __name__ == "__main__":
    main()
