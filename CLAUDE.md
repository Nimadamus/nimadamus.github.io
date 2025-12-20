# CLAUDE.md - MANDATORY INSTRUCTIONS FOR EVERY SESSION

## CRITICAL: READ BEFORE DOING ANYTHING

**This file is automatically loaded at the start of every Claude Code session in this repository.**

---

## ⛔⛔⛔ HANDICAPPING HUB - PERMANENTLY LOCKED DESIGN ⛔⛔⛔

**DO NOT CHANGE THE HANDICAPPING HUB DESIGN. EVER.**

### The ONLY Script to Use:
```
python C:\Users\Nima\nimadamus.github.io\scripts\handicapping_hub_production.py
```

### LOCKED 4-SECTION LAYOUT (December 14, 2025):

Each game card has exactly 4 sections:

**SECTION 1: BETTING LINES**
```
| TEAM              | SPREAD | ML   | O/U     |
| Logo + Abbr + Rec | +/-X.X | +XXX | O XX.X  |
| Logo + Abbr + Rec | +/-X.X | -XXX | U XX.X  |
```

**SECTION 2: OFFENSE vs DEFENSE (side-by-side grid)**
```
OFFENSE                          | DEFENSE
NFL: PPG|YPG|PASS|RUSH|3RD%     | OPP|OYPG|SACK|INT|TFL
NBA: PPG|FG%|3P%|FT%|AST        | OPP|REB|STL|BLK|DREB
NHL: GF|SOG|PP%|PPG|S%          | GA|GD|PK%|SV%|SA
```

**SECTION 3: EFFICIENCY vs SITUATIONAL (side-by-side grid)**
```
EFFICIENCY                       | SITUATIONAL/POWER
NFL: YPP|COMP%|YPA|YPR|QBR      | RZ%|4TH%|TO+/-|TOP|PWR
NBA: TO|A/TO|OREB|2P%|PF        | PWR|PPG|OPP|DIFF|REC
NHL: FO%|PIM|SHG|GWG|OTL        | PWR|GF|GA|GD|REC
```

**SECTION 4: TRENDS BAR**
- Light blue background (#e3f2fd)
- Injury alerts for both teams

### LOCKED Visual Design:
- **Background**: Light gray (#f0f2f5)
- **Header**: Dark blue gradient (#1a365d to #2d4a7c)
- **Game Cards**: White (#fff), rounded corners, shadow
- **Section Titles**: Orange underline (#fd5000)
- **Font**: Inter
- **5 Sport Tabs**: NBA, NFL, NHL, NCAAB, NCAAF

### DAILY AUTOMATION:
- GitHub Actions runs daily at 10:00 AM ET
- Generates fresh data from ESPN + Odds API
- Auto-commits and pushes to main branch
- Old days are archived automatically

### IF USER ASKS TO UPDATE THE HUB:
1. Run `handicapping_hub_production.py` - that's it
2. DO NOT create new scripts
3. DO NOT modify the CSS or HTML structure
4. DO NOT change the 4-section layout
5. DO NOT remove any stat columns

---

## ⛔⛔⛔ ZERO TOLERANCE: NO PLACEHOLDER CONTENT. EVER. ⛔⛔⛔

### PERMANENTLY LOCKED - DECEMBER 20, 2025

**EVERY GAME on sports pages MUST have REAL, substantive written analysis.**

### BANNED PLACEHOLDER CONTENT (NEVER USE):
- ❌ "Matchup analysis coming soon"
- ❌ "Analysis coming soon"
- ❌ "Preview coming soon"
- ❌ "[Team] vs [Team]" with no analysis
- ❌ Single-sentence game descriptions
- ❌ ANY one-liner that isn't real analysis
- ❌ Template filler content
- ❌ Generic text that could apply to any game

### MINIMUM REQUIREMENTS PER GAME:
- ✅ **2-3 paragraphs minimum** of substantive written analysis
- ✅ Specific details about THIS matchup (players, stats, storylines)
- ✅ Real context (team records, recent form, key injuries)
- ✅ Something unique that makes this game interesting
- ✅ Human-sounding editorial content

### THE RULE IS ABSOLUTE:
```
IF a game exists on the page → IT MUST HAVE REAL WRITTEN ANALYSIS
IF you cannot write real analysis → DO NOT ADD THE GAME
BETTER to have fewer games with quality content than all games with placeholder garbage
```

### WHY THIS MATTERS:
- Placeholder content makes the site look LAZY and UNPROFESSIONAL
- Users come to BetLegend for ANALYSIS, not empty shells
- One page of placeholders destroys credibility for the entire site
- This happened December 19, 2025 - NEVER AGAIN

### IF YOU'RE ABOUT TO WRITE "Coming soon" - STOP:
1. Research the actual matchup
2. Find real storylines, stats, and context
3. Write 2-3 paragraphs of genuine analysis
4. If you can't do that, don't add the game at all

**ZERO TOLERANCE. NO EXCEPTIONS. EVER.**

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
- **Featured Game of the Day**: featured-game-of-the-day-page20.html (current - Dec 18, 2025)
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

## ⛔⛔⛔ LOCKED: CALENDAR STYLE ARCHIVE PAGES (December 14, 2025) ⛔⛔⛔

**ALL archive pages MUST match the main sports page format (nba.html style).**

### REQUIRED FORMAT:
```html
<article class="game-preview">
  <div class="game-header">
    <img class="team-logo" src="ESPN_CDN_URL"/>
    <div class="matchup-info">
      <h2>Away @ Home</h2>
      <span class="game-time">Day, Time ET | Venue</span>
    </div>
    <img class="team-logo" src="ESPN_CDN_URL"/>
  </div>
  <!-- For completed games: result section here (green/orange) -->
  <div class="preview-content">
    <p>[3-5 paragraphs of REAL written content]</p>
  </div>
</article>
```

### BANNED - NEVER USE:
- ❌ stat-row divs with spread/ML boxes
- ❌ deep-analysis sections
- ❌ game-card class (use game-preview)
- ❌ "Both defenses have been comparable..."

**Full documentation:** See POSTING_PROTOCOL.md

---

## CRITICAL REMINDERS

1. **ACCURACY OVER SPEED** - It's better to take time and verify than to publish errors
2. **NEVER GUESS** - If you can't verify, ask the user or omit the detail
3. **COUNT ALL GAMES** - Never claim "X-game slate" without verifying exact count
4. **CHECK ROSTERS** - Players change teams; always verify current team
5. **VERIFY INJURIES** - ACL and Achilles are different; details matter

---

**One false claim destroys credibility. Verify everything.**
