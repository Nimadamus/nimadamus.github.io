import os
import re
from datetime import datetime

REPO = r'C:\Users\Nima\nimadamus.github.io'

def extract_date_from_page(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        match = re.search(r'current-date.*?<h2>(.*?)</h2>', content)
        if match:
            date_str = match.group(1).strip()
            try:
                dt = datetime.strptime(date_str, '%B %d, %Y')
                return dt.strftime('%Y-%m-%d')
            except:
                pass

        match = re.search(r'Posted:?\s*([A-Za-z]+\s+\d+,?\s+\d{4})', content)
        if match:
            date_str = match.group(1).strip().replace(',', '')
            try:
                dt = datetime.strptime(date_str, '%B %d %Y')
                return dt.strftime('%Y-%m-%d')
            except:
                pass

        return None
    except:
        return None

def extract_title(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        match = re.search(r'hero-badge.*?>(.*?)</div>', content)
        if match:
            return match.group(1).strip()

        return 'Analysis'
    except:
        return 'Analysis'

# Sports configuration
sports_config = {
    'nba': {'name': 'NBA', 'color': '#C9082A', 'logo': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/leagues/500/nba.png'},
    'nhl': {'name': 'NHL', 'color': '#000000', 'logo': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/leagues/500/nhl.png'},
    'ncaab': {'name': 'NCAAB', 'color': '#0033A0', 'logo': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/leagues/500/mens-college-basketball.png'},
    'ncaaf': {'name': 'NCAAF', 'color': '#500000', 'logo': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/leagues/500/college-football.png'}
}

for sport, config in sports_config.items():
    print(f'Creating {sport} calendar system...')

    # Find all pages and extract dates
    pages = []
    for f in os.listdir(REPO):
        if f.startswith(f'{sport}-page') and f.endswith('.html'):
            pages.append(f)
        elif f == f'{sport}.html':
            pages.append(f)

    entries = []
    for page in pages:
        filepath = os.path.join(REPO, page)
        date = extract_date_from_page(filepath)
        title = extract_title(filepath)

        if date:
            entries.append((date, page, title))
        else:
            # Assign default date for older pages
            if 'page30' in page or 'page31' in page:
                entries.append(('2025-11-28', page, 'Archive'))
            elif 'page14' in page and sport == 'ncaaf':
                entries.append(('2025-12-06', page, 'Championship Weekend'))
            elif 'page17' in page and sport == 'ncaaf':
                entries.append(('2025-11-29', page, 'Rivalry Week'))

    entries.sort(key=lambda x: x[0])

    # Create data file
    data_content = f'''// {config['name']} Games Data - All {config['name']} analysis pages by date
// Format: {{ date: "YYYY-MM-DD", page: "filename.html", title: "Description" }}

const {sport.upper()}_GAMES = [
'''

    for date, page, title in entries:
        data_content += f'    {{ date: "{date}", page: "{page}", title: "{title}" }},\n'

    data_content += f'''];

// Export for use in calendar
if (typeof module !== 'undefined' && module.exports) {{
    module.exports = {sport.upper()}_GAMES;
}}
'''

    with open(os.path.join(REPO, f'{sport}-games-data.js'), 'w', encoding='utf-8') as f:
        f.write(data_content)

    print(f'  Created {sport}-games-data.js with {len(entries)} entries')

print('\nAll data files created!')
