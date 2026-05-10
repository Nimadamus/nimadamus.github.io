import PyPDF2
import re
import requests
import concurrent.futures
import json
import traceback

pdf_path = r'C:\Users\Nima\Desktop\412 NHL trends.pdf'
reader = PyPDF2.PdfReader(pdf_path)
text = ""
for page in reader.pages:
    text += page.extract_text() + "\n"

lines = text.split('\n')
games = []
# Parse games
i = 0
while i < len(lines):
    line = lines[i].strip()
    if re.match(r'^\d{4}-\d{2}-\d{2}$', line):
        if i + 4 < len(lines):
            date = line
            at_vs = lines[i+1].strip()
            if at_vs in ('@', 'vs'):
                opponent = lines[i+2].strip()
                score = lines[i+3].strip()
                wl = lines[i+4].strip()
                games.append({'date': date, 'at_vs': at_vs, 'opponent': opponent, 'score': score, 'wl': wl})
                i += 5
                continue
    i += 1

print(f"Extracted {len(games)} game rows from PDF.")
dates = list(set(g['date'] for g in games))
print(f"Unique dates: {len(dates)}")

date_data = {}
def fetch_date(date_str):
    url = f"http://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard?dates={date_str.replace('-', '')}"
    try:
        resp = requests.get(url, timeout=10)
        return date_str, resp.json()
    except Exception as e:
        return date_str, None

print("Fetching data from ESPN...")
with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
    results = executor.map(fetch_date, dates)
    for date_str, data in results:
        date_data[date_str] = data
print("Data fetching complete.")

errors = []
for g in games:
    date_str = g['date']
    data = date_data.get(date_str)
    if not data or 'events' not in data:
        errors.append(f"No data for date {date_str} (Game: {g})")
        continue
    
    opponent_found = False
    match_found = False
    espn_scores = []
    
    for event in data['events']:
        competitors = event['competitions'][0]['competitors']
        team_names = []
        for c in competitors:
            t = c['team']
            team_names.append(t.get('displayName', '').lower())
            team_names.append(t.get('name', '').lower())
            team_names.append(t.get('location', '').lower() + ' ' + t.get('name', '').lower())
            
        # clean opponent
        opp_clean = g['opponent'].lower().replace('é', 'e')
        if any(opp_clean in tn.replace('é', 'e') for tn in team_names):
            opponent_found = True
            scores = [c['score'] for c in competitors]
            espn_scores = scores
            pdf_scores = g['score'].split('-')
            if len(pdf_scores) == 2:
                if (pdf_scores[0] == scores[0] and pdf_scores[1] == scores[1]) or \
                   (pdf_scores[0] == scores[1] and pdf_scores[1] == scores[0]):
                    match_found = True
            else:
                match_found = True 
            break
            
    if not opponent_found:
        events_on_date = [c['team']['displayName'] for ev in data.get('events', []) for c in ev['competitions'][0]['competitors']]
        errors.append(f"Opponent '{g['opponent']}' not found on {date_str}. Teams playing that day: {', '.join(events_on_date)}")
    elif not match_found:
        errors.append(f"Score mismatch for {g['opponent']} on {date_str}. PDF has {g['score']}. ESPN has {'-'.join(espn_scores)}")

print(f"Total Errors: {len(errors)}")
for e in errors:
    print(e)
