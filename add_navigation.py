#!/usr/bin/env python3
"""
Script to add navigation to blog pages that are missing it
"""

NAV_CSS = """
/* Logo */
.logo-container {
    position: fixed;
    top: 20px;
    left: 40px;
    z-index: 1000;
}

.logo-container a {
    color: #fff;
    text-decoration: none;
    font-family: var(--font-primary);
    font-size: 2.5rem;
    font-weight: 900;
    text-transform: uppercase;
    text-shadow:
        0 0 10px rgba(255, 255, 255, 0.8),
        0 0 20px rgba(255, 255, 255, 0.4);
}

.logo-container span {
    color: var(--neon-cyan);
    text-shadow:
        0 0 15px rgba(0, 255, 255, 1),
        0 0 30px rgba(0, 255, 255, 0.8),
        0 0 50px rgba(0, 255, 255, 0.6);
}

/* Navigation */
.nav-links {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 18px;
    padding: 15px 5% 15px 5%;
    background: rgba(0, 0, 0, 0.95);
    backdrop-filter: blur(10px);
    border-bottom: 2px solid rgba(0, 224, 255, 0.3);
    z-index: 999;
    flex-wrap: wrap;
}

.nav-links a, .dropdown {
    display: inline-flex;
    align-items: center;
}

.nav-links a {
    font-family: var(--font-secondary);
    text-decoration: none;
    color: var(--text-color);
    font-weight: 600;
    font-size: 0.9rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    padding: 8px 10px;
    border-radius: 5px;
    transition: all 0.3s ease;
    text-shadow: 0 0 5px rgba(0, 0, 0, 0.8);
    white-space: nowrap;
}

.nav-links a:hover, .nav-links a.active {
    color: var(--neon-gold);
    text-shadow: 0 0 8px var(--neon-gold);
}

/* Dropdown */
.dropdown {
    position: relative;
    display: inline-flex;
    align-items: center;
}

.dropdown .dropbtn {
    font-family: var(--font-secondary);
    text-decoration: none;
    color: var(--text-color);
    font-weight: 600;
    font-size: 0.9rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    padding: 8px 10px;
    border-radius: 5px;
    transition: all 0.3s ease;
    text-shadow: 0 0 5px rgba(0, 0, 0, 0.8);
    background: none;
    border: none;
    cursor: pointer;
    white-space: nowrap;
    display: inline-flex;
    align-items: center;
}

.dropdown:hover .dropbtn {
    color: var(--neon-gold);
    text-shadow: 0 0 8px var(--neon-gold);
}

.dropdown-content {
    display: none;
    position: absolute;
    top: 100%;
    left: 0;
    background: rgba(0, 0, 0, 0.95);
    backdrop-filter: blur(20px);
    min-width: 200px;
    box-shadow: 0px 8px 30px rgba(0, 224, 255, 0.4);
    z-index: 1000;
    border: 2px solid rgba(0, 224, 255, 0.5);
    border-radius: 10px;
    padding: 15px 0;
    margin-top: 10px;
}

.dropdown-content a {
    color: var(--neon-cyan);
    padding: 14px 20px;
    text-decoration: none;
    display: block;
    font-size: 0.95rem;
    text-align: left;
    transition: all 0.3s ease;
    text-shadow: 0 0 5px rgba(0, 255, 255, 0.5);
    border-left: 3px solid transparent;
}

.dropdown-content a:hover {
    background: linear-gradient(90deg, rgba(0, 224, 255, 0.3), rgba(0, 224, 255, 0.1));
    color: #fff;
    padding-left: 30px;
    text-shadow: 0 0 10px var(--glow-color);
    border-left-color: var(--neon-cyan);
}

.dropdown:hover .dropdown-content {
    display: block;
    animation: dropdownFade 0.3s ease;
}

@keyframes dropdownFade {
    from { opacity: 0; transform: translateY(-10px); }
    to { opacity: 1; transform: translateY(0); }
}

@media (max-width: 768px) {
    .logo-container {
        top: 10px;
        left: 20px;
    }

    .logo-container a {
        font-size: 1.5rem;
    }

    .nav-links {
        flex-wrap: wrap;
        gap: 8px;
        justify-content: center;
        padding: 10px 5px;
    }

    .nav-links a {
        font-size: 0.75rem;
        padding: 6px 10px;
    }

    .dropdown .dropbtn {
        font-size: 0.75rem;
        padding: 6px 10px;
    }

    .dropdown-content {
        min-width: 160px;
        padding: 10px 0;
    }

    .dropdown-content a {
        font-size: 0.85rem;
        padding: 10px 15px;
    }
}
"""

NAV_HTML = """
<!-- Logo -->
<div class="logo-container">
    <a href="index.html">BET<span>LEGEND</span></a>
</div>

<!-- Navigation -->
<nav class="nav-links">
    <a href="index.html">HOME</a>
    <a href="blog-page8.html">PICKS & ANALYSIS</a>

    <div class="dropdown">
        <button class="dropbtn">Records</button>
        <div class="dropdown-content">
            <a href="betlegend-verified-records.html">MLB</a>
            <a href="nfl-records.html">NFL</a>
            <a href="ncaaf-records.html">NCAAF</a>
            <a href="nhl-records.html">NHL</a>
            <a href="nba-records.html">NBA</a>
            <a href="soccer-records.html">Soccer</a>
        </div>
    </div>

    <div class="dropdown">
        <button class="dropbtn">Sports</button>
        <div class="dropdown-content">
            <a href="nfl.html">NFL</a>
            <a href="mlb-page2.html">MLB</a>
            <a href="ncaaf.html">NCAAF</a>
            <a href="nba.html">NBA</a>
            <a href="nhl.html">NHL</a>
        </div>
    </div>

    <div class="dropdown">
        <button class="dropbtn">Resources</button>
        <div class="dropdown-content">
            <a href="live-odds.html">Live Odds</a>
            <a href="howitworks.html">How It Works</a>
            <a href="bankroll.html">Bankroll Management</a>
            <a href="screenshots.html">Screenshots</a>
            <a href="bestonlinesportsbook.html">Best Sportsbook</a>
            <a href="betting-101.html">Betting 101</a>
        </div>
    </div>

    <a href="proofofpicks.html">Proof</a>
    <a href="news-page5.html">News</a>
    <a href="featured-game-of-the-day-page50.html">Game of the Day</a>

    <div class="dropdown">
        <button class="dropbtn">Community</button>
        <div class="dropdown-content">
            <a href="https://twitter.com/BetLegend2025" target="_blank" rel="noopener">Twitter</a>
            <a href="https://discord.gg/NbMc3wCV" target="_blank" rel="noopener">Discord</a>
        </div>
    </div>
</nav>

"""

def add_navigation_to_file(filepath):
    """Add navigation CSS and HTML to a blog page"""
    print(f"Processing {filepath}...")

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check if navigation already exists
    if 'class="nav-links"' in content:
        print(f"  [OK] Navigation already exists in {filepath}")
        return False

    # Add fonts if not present
    if 'Orbitron' not in content and 'Poppins' not in content:
        content = content.replace(
            'family=Sora:wght@600&amp;family=Rubik&amp;display=swap',
            'Orbitron:wght@500;700;900&family=Poppins:wght@300;400;600&family=Sora:wght@600&family=Rubik&display=swap'
        )

    # Add CSS variables if not present
    if ':root {' not in content:
        css_vars = """
        :root {
            --bg-color: #000;
            --text-color: #eaf8ff;
            --glow-color: #00e0ff;
            --neon-cyan: #00ffff;
            --neon-gold: #FFD700;
            --font-primary: 'Orbitron', sans-serif;
            --font-secondary: 'Poppins', sans-serif;
        }

        """
        content = content.replace('<style>', '<style>' + css_vars)

    # Update body padding for fixed nav
    if 'padding: 0;' in content and 'body {' in content:
        content = content.replace(
            'padding: 0;',
            'padding: 140px 0 0 0;'
        )
    elif 'padding: 140px' not in content:
        # Add padding if body doesn't have it
        import re
        content = re.sub(
            r'(body\s*\{[^}]*)(})',
            r'\1  padding-top: 140px;\2',
            content,
            flags=re.DOTALL
        )

    # Add navigation CSS before </style>
    content = content.replace('</style>', NAV_CSS + '\n    </style>')

    # Add navigation HTML after <body>
    content = content.replace('<body>', '<body>\n' + NAV_HTML)

    # Write back
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"  [OK] Added navigation to {filepath}")
    return True

def main():
    blog_pages = [
        'blog.html',
        'blog-page2.html',
        'blog-page3.html',
        'blog-page4.html',
        'blog-page5.html',
        'blog-page6.html'
    ]

    updated = 0
    for page in blog_pages:
        if add_navigation_to_file(page):
            updated += 1

    print(f"\nComplete! Updated {updated} blog pages with navigation.")

if __name__ == '__main__':
    main()
