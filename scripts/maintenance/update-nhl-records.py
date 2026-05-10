import csv
import json
import urllib.request

# Fetch the CSV from Google Sheets
url = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vRaRwsGOmbXrqAX0xqrDc9XwRCSaAOkuW68TArz3XQp7SMmLirKbdYqU5-zSM_A-MDNKG6sbdwZac6I/pub?output=csv'

print('Fetching NHL records from Google Sheets...')
with urllib.request.urlopen(url) as response:
    csv_data = response.read().decode('utf-8')

# Parse CSV
lines = csv_data.strip().split('\n')
reader = csv.DictReader(lines)
rows = list(reader)

# Convert to JSON format
nhl_data = []
for row in rows:
    nhl_data.append({
        'Sport': 'NHL',
        'League': '',
        'Date': row['Date'],
        'Picks': row['Pick'],
        'Odds': row['Odds'],
        'Units': '',
        'Result': row['Result'],
        'ProfitLoss': row['Units'],
        'GradedAt': ''
    })

# Write to JSON file
with open('nhl-records.json', 'w', encoding='utf-8') as f:
    json.dump(nhl_data, f, indent=2)

# Calculate stats
wins = sum(1 for r in rows if r['Result'].strip().upper() == 'W')
losses = sum(1 for r in rows if r['Result'].strip().upper() == 'L')
pushes = sum(1 for r in rows if r['Result'].strip().upper() == 'P')
total_units = sum(float(r['Units']) for r in rows)

print(f'Updated nhl-records.json')
print(f'  Total picks: {len(rows)}')
print(f'  Record: {wins}-{losses}-{pushes}')
print(f'  Total Units: {total_units:.2f}')
