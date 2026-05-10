import os
from pathlib import Path
from bs4 import BeautifulSoup
from datetime import datetime

def generate_html_sitemap():
    site_dir = Path("C:/Users/Nima/nimadamus.github.io")
    base_url = "https://www.betlegendpicks.com"
    
    skip_keywords = ['backup', 'test', 'temp', '_', 'grade', 'audit', 'fix', 'copy', 'old', 'v2', 'v3', 'draft']
    
    html_files = []
    
    # Collect valid HTML files
    for filepath in site_dir.rglob("*.html"):
        filename = filepath.name.lower()
        if any(keyword in filename for keyword in skip_keywords):
            continue
        if 'archives' in str(filepath).lower() and 'consensus' in str(filepath).lower():
            continue
            
        # Get relative path
        rel_path = str(filepath.relative_to(site_dir)).replace('\\', '/')
        
        # Try to extract title
        title = filename.replace('.html', '').replace('-', ' ').title()
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                if '<title>' in content:
                    title_str = content.split('<title>')[1].split('</title>')[0].strip()
                    if title_str:
                        title = title_str.replace(' | BetLegend Picks', '').replace(' | BetLegend', '')
        except Exception:
            pass
            
        # Determine category
        category = "Other Picks & Articles"
        if 'mlb' in filename or 'baseball' in filename or 'yankees' in filename or 'dodgers' in filename:
            category = "MLB Picks"
        elif 'nba' in filename or 'basketball' in filename or 'lakers' in filename or 'celtics' in filename:
            category = "NBA Picks"
        elif 'nhl' in filename or 'hockey' in filename or 'bruins' in filename or 'rangers' in filename:
            category = "NHL Picks"
        elif 'nfl' in filename or 'football' in filename or 'chiefs' in filename or 'eagles' in filename:
            category = "NFL Picks"
        elif 'ncaab' in filename or 'college-basketball' in filename:
            category = "College Basketball Picks"
        elif 'ncaaf' in filename or 'college-football' in filename or 'bowl' in filename:
            category = "College Football Picks"
        elif 'soccer' in filename or 'premier-league' in filename or 'champions-league' in filename:
            category = "Soccer Picks"
        elif 'record' in filename:
            category = "Records & Transparency"
        elif 'preview' in filename and not ('pick' in filename or 'analysis' in filename):
            category = "Daily Hubs & Previews"
        elif filename in ['index.html', 'about.html', 'contact.html', 'howitworks.html', 'proofofpicks.html', 'bankroll.html', 'kelly-criterion.html', 'live-odds.html']:
            category = "Core Pages"
            
        html_files.append({
            'url': f"{rel_path}",
            'title': title,
            'category': category,
            'mtime': filepath.stat().st_mtime
        })
        
    # Sort by modification time (newest first)
    html_files.sort(key=lambda x: x['mtime'], reverse=True)
    
    # Group by category
    categories = {}
    for f in html_files:
        if f['category'] not in categories:
            categories[f['category']] = []
        categories[f['category']].append(f)
        
    # Generate HTML
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Complete Pick Archive & Sitemap | BetLegend</title>
    <meta name="description" content="Complete archive of all BetLegend sports betting picks, analysis, and records.">
    <link rel="canonical" href="https://www.betlegendpicks.com/sitemap.html"/>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&family=Poppins:wght@300;400;600&display=swap" rel="stylesheet">
    <style>
        :root { --bg-color: #000; --text-color: #eaf8ff; --glow-color: #00e0ff; --neon-gold: #FFD700; }
        body { background: #0a0a0a; font-family: 'Poppins', sans-serif; color: var(--text-color); line-height: 1.6; padding: 40px 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 { font-family: 'Orbitron', sans-serif; color: var(--neon-gold); text-align: center; margin-bottom: 20px; }
        .intro { text-align: center; color: #aaa; margin-bottom: 50px; }
        .sitemap-section { background: rgba(15, 20, 30, 0.8); border: 1px solid rgba(0, 224, 255, 0.2); border-radius: 15px; padding: 30px; margin-bottom: 30px; }
        .sitemap-section h2 { font-family: 'Orbitron', sans-serif; color: var(--glow-color); font-size: 1.5rem; margin-bottom: 20px; border-bottom: 1px solid rgba(0, 224, 255, 0.3); padding-bottom: 10px; }
        .sitemap-links { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 10px; }
        .sitemap-links a { color: #fff; text-decoration: none; padding: 8px 12px; background: rgba(0, 224, 255, 0.05); border: 1px solid rgba(0, 224, 255, 0.2); border-radius: 6px; font-size: 0.9rem; transition: all 0.2s; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; display: block; }
        .sitemap-links a:hover { background: rgba(0, 224, 255, 0.15); border-color: var(--glow-color); }
        .nav-back { display: inline-block; margin-bottom: 20px; color: var(--neon-gold); text-decoration: none; font-family: 'Orbitron', sans-serif; }
        .nav-back:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="container">
        <a href="index.html" class="nav-back">&larr; Back to Home</a>
        <h1>Complete Pick Archive & Sitemap</h1>
        <p class="intro">This page contains a static directory of every betting pick, analysis article, and core page on BetLegend. Search engines use this page to index our entire history.</p>
"""
    
    # Priority order for categories
    category_order = ["Core Pages", "Daily Hubs & Previews", "Records & Transparency", "MLB Picks", "NBA Picks", "NFL Picks", "NHL Picks", "College Basketball Picks", "College Football Picks", "Soccer Picks", "Other Picks & Articles"]
    
    for cat in category_order:
        if cat in categories and categories[cat]:
            html += f'\n        <div class="sitemap-section">\n            <h2>{cat} ({len(categories[cat])})</h2>\n            <div class="sitemap-links">\n'
            for item in categories[cat]:
                html += f'                <a href="{item["url"]}" title="{item["title"]}">{item["title"]}</a>\n'
            html += '            </div>\n        </div>\n'
            
    html += """
    </div>
</body>
</html>"""

    with open(site_dir / "sitemap.html", 'w', encoding='utf-8') as f:
        f.write(html)
        
    print(f"Generated HTML sitemap with {len(html_files)} static links.")

if __name__ == "__main__":
    generate_html_sitemap()
