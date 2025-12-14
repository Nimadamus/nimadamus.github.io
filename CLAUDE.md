# CLAUDE.md - MANDATORY INSTRUCTIONS FOR EVERY SESSION

## CRITICAL: READ BEFORE DOING ANYTHING

**This file is automatically loaded at the start of every Claude Code session in this repository.**

---

## ⛔⛔⛔ HANDICAPPING HUB - PERMANENTLY LOCKED DESIGN ⛔⛔⛔

**DO NOT CHANGE THE HANDICAPPING HUB DESIGN. EVER.**

The Handicapping Hub (`handicapping-hub.html`) has a LOCKED design. If the user asks to update it, ONLY run the production script - DO NOT modify the HTML structure or CSS.

### The ONLY Script to Use:
```
python C:\Users\Nima\nimadamus.github.io\scripts\handicapping_hub_production.py
```

**OLD SCRIPTS HAVE BEEN DELETED - DO NOT RECREATE THEM:**
- ~~generate_handicapping_hub.py~~ - DELETED
- ~~github_handicapping_hub.py~~ - DELETED

### LOCKED Visual Design (DO NOT CHANGE):
- **Background**: Light gray (#f0f2f5)
- **Header**: Dark blue gradient (#1a365d to #2d4a7c)
- **Content panels**: White (#fff)
- **Accent**: Orange (#fd5000)
- **Font**: Inter

### LOCKED Structure (DO NOT CHANGE):
- **5 Sport Tabs**: NBA, NFL, NHL, NCAAB, NCAAF (in that order)
- **Game Cards**: White background, rounded corners
- **Game Time Header**: Dark blue (#1a365d)
- **Stats Table**: Horizontal layout with columns
- **Injury Bar**: Yellow (#fff3cd) below each game
- **Trends Bar**: Light blue (#e3f2fd) below injury bar

### LOCKED Stats Per Sport:
- **NBA**: PWR, PPG, OPP, PACE, ORTG, DRTG, NET, FG%, 3P%, FT%, eFG%, TS%, REB, AST, TO, STL, BLK
- **NFL**: PWR, PPG, OPP, YPP, PASS, RUSH, RZ%, TOP, TO+/-, 3RD%, SACK, INT
- **NHL**: PWR, GF, GA, GD, PP%, PK%, SOG, SV%, FOW%, PIM
- **NCAAB/NCAAF**: Similar comprehensive stats

### WHY THIS MATTERS:
Previous sessions kept changing the design between dark theme and light theme. This caused user frustration. The design is now PERMANENTLY LOCKED.

### IF USER ASKS TO UPDATE THE HUB:
1. Run `handicapping_hub_production.py` - that's it
2. DO NOT create new scripts
3. DO NOT modify the CSS
4. DO NOT change the layout
5. DO NOT switch to dark theme

---

## STEP 1: ALWAYS READ THE PROTOCOL FIRST

Before creating ANY content for this website, you MUST read:
- `POSTING_PROTOCOL.md` - Contains mandatory verification checklist

**Run this command at the start of every session:**
```
Read POSTING_PROTOCOL.md sections 1 and 1A
```

---

## STEP 2: MANDATORY VERIFICATION FOR SLATE POSTS

If the user asks you to create a slate post (NBA, NHL, NFL, NCAAB, MLB), you MUST:

1. **VERIFY TOTAL GAME COUNT FIRST**
   - Search ESPN/official schedule for the EXACT date
   - COUNT every single game
   - Do NOT write until you have the exact count

2. **VERIFY EVERY PLAYER-TEAM ASSOCIATION**
   - Search to confirm each player is on the team you mention
   - Check for 2025 trades (many players changed teams)

3. **VERIFY ALL INJURIES**
   - Search exact injury type (ACL vs Achilles matters!)
   - Confirm current status

4. **VERIFY ALL STATS AND RECORDS**
   - Never guess - search and verify everything

---

## STEP 3: KEY 2025 ROSTER CHANGES TO REMEMBER

### NBA 2025 Trades:
- Kevin Durant → Houston Rockets (July 2025)
- Brandon Ingram → Toronto Raptors (Feb 2025)
- Fred VanVleet → Houston (has torn ACL, out for season)

### NHL 2025 Trades:
- Mitch Marner → Vegas Golden Knights (July 2025)

### Key Injuries (November 2025):
- Jayson Tatum → ACHILLES injury (NOT ACL)
- Tyrese Haliburton → ACHILLES injury (2025 Finals)
- Connor Hellebuyck → Knee surgery, 4-6 weeks

### 2025 Champions:
- NBA: Oklahoma City Thunder (beat Pacers in 7 games)
- NHL: Florida Panthers (back-to-back, 2024 & 2025)

---

## STEP 4: POSTING LOCATIONS

- **Blog picks/analysis**: blog-page10.html (add to TOP)
- **NBA slate posts**: nba.html (add to TOP)
- **NHL slate posts**: nhl.html (add to TOP)
- **NCAAB posts**: ncaab.html (add to TOP)
- **NFL posts**: nfl.html (add to TOP)
- **Featured Game of the Day**: featured-game-of-the-day-page18.html (current - Dec 13, 2025)
- **Moneyline Parlay**: moneyline-parlay-of-the-day.html

### ⛔ CRITICAL: FEATURED GAME OF THE DAY = ANALYSIS ONLY, NO PICKS ⛔

**Featured Game pages are STATS and ANALYSIS only. NEVER give picks.**

**DO NOT include:**
- ❌ "BetLegend's Pick" or verdict sections
- ❌ "Take [Team]" language
- ❌ Any explicit betting recommendation

**MUST include:**
- ✅ Team logos next to team names (ESPN CDN: https://a.espncdn.com/i/teamlogos/nfl/500/[abbrev].png)
- ✅ Deep stats analysis with verified numbers
- ✅ Injury reports, betting lines, trends
- ✅ "Final Thoughts" section (analysis only, no picks)
- ✅ "Keys To Victory" for both teams

### ⛔ CRITICAL: FEATURED GAME LINK UPDATE REQUIRED ⛔

**EVERY TIME you create a new Featured Game of the Day:**

1. Create the new page (increment page number)
2. **IMMEDIATELY run this script to update ALL 300+ pages:**

```python
import os, re
REPO = r'C:\Users\Nima\nimadamus.github.io'
NEW = 'featured-game-of-the-day-pageXX.html'  # ← UPDATE NUMBER

for root, dirs, files in os.walk(REPO):
    dirs[:] = [d for d in dirs if d != '.git']
    for f in files:
        if f.endswith('.html'):
            path = os.path.join(root, f)
            with open(path, 'r', encoding='utf-8', errors='ignore') as file:
                c = file.read()
            orig = c
            c = re.sub(r'featured-game-of-the-day-page\d+\.html', NEW, c)
            if c != orig:
                with open(path, 'w', encoding='utf-8') as file:
                    file.write(c)
```

3. **UPDATE CALENDAR DATA** - Add entry to `featured-games-data.js`:
```javascript
{ date: "YYYY-MM-DD", page: "featured-game-of-the-day-pageXX.html", title: "Game Title" },
```
4. Push changes immediately
5. Verify on live site

**The calendar now auto-populates from the data file - no manual HTML editing needed!**

**DO NOT skip these steps. On Dec 8, 2025, users saw a 4-day-old game because links weren't updated.**

---

## STEP 5: AFTER MAKING CHANGES - MANDATORY DEPLOYMENT CHECKLIST

### A. VERIFY PAGINATION LINKS (CRITICAL!)
Before committing, verify that ALL sports pages have correct pagination:

**Pagination Structure:**
- `sport.html` = NEWEST content (e.g., Page 14 of 14)
- `sport-page2.html` = Second newest (e.g., Page 13 of 14)
- `sport-pageN.html` = OLDEST content (e.g., Page 1 of 14)

**The "Older" link on sport.html MUST point to sport-page2.html:**
- `nba.html` → "Older" links to `nba-page2.html`
- `nfl.html` → "Older" links to `nfl-page2.html`
- `nhl.html` → "Older" links to `nhl-page2.html`
- `ncaab.html` → "Older" links to `ncaab-page2.html`
- `soccer.html` → "Older" links to `soccer-page2.html`

**NEVER link "Older" to the highest page number (e.g., nhl-page19.html) - that's the OLDEST content!**

### B. ALWAYS PUSH TO GITHUB
```bash
git -C "C:\Users\Nima\nimadamus.github.io" add [files]
git -C "C:\Users\Nima\nimadamus.github.io" commit -m "[description]"
git -C "C:\Users\Nima\nimadamus.github.io" push
```

### C. VERIFY DEPLOYMENT IS LIVE
After pushing, wait 1-2 minutes for GitHub Pages to deploy, then verify:
1. The new content appears at https://www.betlegendpicks.com/[page].html
2. Navigation links work correctly
3. Pagination links go to the right pages

**DO NOT consider the task complete until changes are pushed and verified live.**

---

## CRITICAL REMINDERS

1. **ACCURACY OVER SPEED** - It's better to take time and verify than to publish errors
2. **NEVER GUESS** - If you can't verify, ask the user or omit the detail
3. **COUNT ALL GAMES** - Never claim "X-game slate" without verifying exact count
4. **CHECK ROSTERS** - Players change teams; always verify current team
5. **VERIFY INJURIES** - ACL and Achilles are different; details matter

---

**One false claim destroys credibility. Verify everything.**
