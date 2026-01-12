# CLAUDE.md - MANDATORY INSTRUCTIONS FOR EVERY SESSION

## CRITICAL: READ BEFORE DOING ANYTHING

**This file is automatically loaded at the start of every Claude Code session in this repository.**

---

## 🔴🔴🔴 CRITICAL REMINDER - READ EVERY SESSION 🔴🔴🔴

### BETTING LINES: NEVER GUESS. ALWAYS SEARCH.

**Before writing ANY spread, moneyline, or total:**
```
1. SEARCH "[Team A] vs [Team B] betting odds"
2. VERIFY which team is favored
3. WRITE DOWN the exact lines
4. THEN write analysis
5. If you can't find lines → ASK THE USER
```

**JANUARY 9, 2026 ERROR:** I assumed Oregon -11.5 vs Indiana based on their 13-0 record.
**ACTUAL LINE:** Indiana -3.5 favorite. I was completely wrong.
**LESSON:** Records DON'T determine lines. Vegas knows things records don't show.

**IF I GUESS BETTING LINES, I HAVE FAILED. SEARCH FIRST. ALWAYS.**

---

## ⛔⛔⛔ ABSOLUTE RULE: FORCED_PAGE_DATE = POST DATE, NOT GAME DATE ⛔⛔⛔

### PERMANENTLY LOCKED - JANUARY 10, 2026

**The FORCED_PAGE_DATE on Featured Game pages must be the DATE THE POST IS MADE, not when the game is played.**

### THE RULE:
```
FORCED_PAGE_DATE = TODAY'S DATE (when you're creating the post)
NOT the date the game was/is played

Example:
- Today is January 10, 2026
- Writing about a game that was played Jan 1
- FORCED_PAGE_DATE = '2026-01-10' ← POST date (CORRECT)
- NOT '2026-01-01' ← WRONG (game date)
```

### WHY THIS MATTERS:
- The calendar shows when POSTS were made, not when games occurred
- Setting game dates creates gaps in the calendar
- Users browse by post date, not game date

### WHEN CREATING A FEATURED GAME PAGE:
```
1. FORCED_PAGE_DATE = today's date (e.g., '2026-01-10')
2. Calendar entry date = today's date
3. The game can be from any date - past or future - doesn't matter
```

**THE CALENDAR TRACKS POSTS, NOT GAMES. USE TODAY'S DATE. ALWAYS.**

---

## ⛔⛔⛔ ABSOLUTE RULE: SPORTS PAGE TITLES MUST HAVE DATES ⛔⛔⛔

### PERMANENTLY LOCKED - JANUARY 11, 2026

**EVERY sports page title MUST include the full date. NO GENERIC TITLES.**

### THE RULE:
```
CORRECT TITLE FORMAT:
<title>[Sport] Analysis - [Month] [Day], [Year] | BetLegend</title>

Examples:
✅ <title>NBA Analysis - January 12, 2026 | BetLegend</title>
✅ <title>NHL Analysis - January 09, 2026 | BetLegend</title>
✅ <title>NCAAB Analysis - January 11, 2026 | BetLegend</title>
✅ <title>Soccer Analysis - January 08, 2026 | BetLegend</title>

WRONG (BANNED):
❌ <title>NBA Analysis Archive - Page 42 | BetLegend</title>
❌ <title>NHL Analysis Archive - Page 45 | BetLegend</title>
❌ <title>NCAAB Analysis Archive - Page 41 | BetLegend</title>
```

### WHY THIS MATTERS:
- The sync_calendars.py script extracts dates from page titles
- Generic "Page X" titles cause pages to fall back to wrong dates
- This creates GAPS in the calendar where dates appear missing
- Users cannot navigate to content that exists but has wrong titles

### WHAT HAPPENED (January 11, 2026):
- 9 pages had generic "Archive - Page X" titles
- Calendar showed gaps for January 5, 9, and 11
- Pages existed but were invisible in the calendar
- User frustrated because content wasn't navigable

### BEFORE CREATING ANY SPORTS PAGE:
```
1. ALWAYS include the date in the <title> tag
2. Format: "[Sport] Analysis - [Full Date] | BetLegend"
3. NEVER use "Archive - Page X" format
4. Run sync_calendars.py after creating pages
5. Verify the date appears in the calendar
```

### THE PRE-COMMIT HOOK BLOCKS THIS:
The pre-commit hook will BLOCK commits with generic "Archive - Page X" titles.
If a commit is blocked - FIX THE TITLES BEFORE PUSHING.

**GENERIC TITLES = INVISIBLE PAGES. ALWAYS INCLUDE DATES.**

### CALENDAR GAP DETECTION SCRIPT:
Run this script to check for calendar issues BEFORE committing:
```bash
python scripts/detect_calendar_gaps.py
```

This script detects:
1. **CRITICAL**: Pages with generic/missing date titles
2. **WARNING**: Duplicate dates (multiple pages for same date)
3. **INFO**: Recent gaps (may be intentional if no games)

**RUN THIS BEFORE EVERY COMMIT TO SPORTS PAGES.**

---

## ⛔⛔⛔ ABSOLUTE RULE #0: MANDATORY FACT-CHECK BEFORE ANY UPLOAD ⛔⛔⛔

### PERMANENTLY LOCKED - JANUARY 5, 2026

### ⚠️ CLAUDE: READ THIS AT THE START OF EVERY SESSION ⚠️

**I MUST SEARCH TO VERIFY EVERY SINGLE FACT I MENTION. NO EXCEPTIONS.**

### MANDATORY VERIFICATION REPORT (SHOW USER BEFORE UPLOADING):
```
=== VERIFICATION REPORT ===
Date: [today's date]
Content: [what I'm creating]

PLAYERS MENTIONED:
- [Player 1]: Verified on [Team] via [source]
- [Player 2]: Verified on [Team] via [source]

INJURIES CHECKED:
- [Player]: [Status] - confirmed via [source]

✅ VERIFICATION COMPLETE - OK TO UPLOAD
```

### 2025 CHAMPIONSHIP RESULTS (VERIFIED):
- **MLB**: Dodgers beat Blue Jays 4-3 (back-to-back)
- **NBA**: OKC Thunder
- **NHL**: Florida Panthers (back-to-back)
- **NFL Super Bowl LIX**: Eagles beat Bills 38-35
- **CFB**: Ohio State beat Texas

### KEY 2025 ROSTER CHANGES:
| Player | OLD Team | NEW Team |
|--------|----------|----------|
| Leonard Floyd | 49ers | Falcons |
| Deebo Samuel | 49ers | Commanders |
| Nick Bosa | 49ers | OUT (ACL) |
| Kevin Durant | Suns | Rockets |
| Mitch Marner | Maple Leafs | Golden Knights |

**See C:\Users\Nima\CLAUDE.md for complete roster changes tables.**

---

## ⛔⛔⛔ ABSOLUTE RULE #0.5: NEVER GUESS BETTING LINES ⛔⛔⛔

### PERMANENTLY LOCKED - JANUARY 9, 2026

**I MUST SEARCH TO VERIFY BETTING LINES. NEVER ASSUME BASED ON RECORDS OR RANKINGS.**

### THE BETTING LINES RULE:
```
BEFORE WRITING ANY SPREAD, MONEYLINE, OR TOTAL:
1. SEARCH "[Team A] vs [Team B] betting odds" or "[Game] spread"
2. VERIFY which team is favored and by how much
3. VERIFY the moneyline for BOTH teams
4. NEVER assume the "better" team is favored
5. NEVER make up betting lines based on team records
```

### WHAT HAPPENED (January 9, 2026):
- Oregon vs Indiana Rose Bowl CFP Quarterfinal
- Oregon was 13-0, #1 seed, Heisman finalist QB
- I ASSUMED Oregon would be heavy favorites (-11.5)
- I made up moneylines: Oregon -420, Indiana +320
- **ACTUAL LINE: Indiana -3.5 favorite, Oregon +3.5 underdog**
- I was COMPLETELY WRONG because I assumed instead of searching

### WHY THIS HAPPENS:
- Team records DON'T determine betting lines
- Rankings DON'T determine betting lines
- The betting market has information I don't have
- Vegas knows things that records don't show

### THE IRON RULE FOR BETTING CONTENT:
```
STEP 1: SEARCH for actual betting lines FIRST
STEP 2: Write down: [Favorite] -[spread] / [Underdog] +[spread]
STEP 3: Write down: [Favorite] -[ML] / [Underdog] +[ML]
STEP 4: ONLY THEN write any analysis
STEP 5: Double-check analysis matches the correct favorite/underdog
```

### VERIFICATION REPORT MUST NOW INCLUDE:
```
BETTING LINES VERIFIED:
- Spread: [Team] -X.X via [source]
- Moneyline: [Favorite] -XXX / [Underdog] +XXX via [source]
- Total: O/U XX.X via [source]
```

### RED FLAGS THAT MEAN I'M GUESSING:
- ❌ "The spread should be around..."
- ❌ "I'd expect them to be favored by..."
- ❌ "With their record, they're probably -X"
- ❌ Any spread I didn't explicitly search for

### IF I AM ABOUT TO WRITE BETTING CONTENT:
1. STOP
2. SEARCH for actual current betting lines
3. WRITE DOWN the exact spread, ML, and total from the source
4. THEN write the analysis matching those lines
5. If I can't find lines, ASK THE USER for the correct lines

**GUESSING BETTING LINES IS UNACCEPTABLE. ONE WRONG LINE DESTROYS ALL CREDIBILITY.**

**THIS ERROR HAPPENED ONCE. IT WILL NEVER HAPPEN AGAIN.**

---

## ⛔⛔⛔ ABSOLUTE RULE #1: NO PAGINATION ON SPORTS PAGES - EVER ⛔⛔⛔

### PERMANENTLY LOCKED - JANUARY 2, 2026

**SPORTS PAGES USE CALENDAR SIDEBAR ONLY. NEVER ADD PAGINATION LINKS.**

```
BANNED ON ALL SPORTS PAGES:
❌ <div class="archive-link">...</div>
❌ <div class="date-section">...</div>
❌ "← Newer" / "Older →" links
❌ "Page X of Y" indicators
❌ ANY navigation between the last article and footer
```

**THE STRUCTURE IS:**
```html
</article>   <!-- Last game article -->
</main>
<footer>...</footer>
```

**NOTHING ELSE. The calendar sidebar handles all navigation.**

**Pre-commit hook BLOCKS any commit with pagination on sports pages.**

---

## ⛔⛔⛔ MANDATORY POSTING WORKFLOW - FOLLOW EVERY TIME ⛔⛔⛔

### PERMANENTLY LOCKED - DECEMBER 23, 2025

**EVERY time I create or edit sports content, I MUST follow this workflow:**

### BEFORE WRITING:
```
1. SEARCH to verify current info (team records, injuries, rosters)
2. COUNT all games on the schedule for that date
3. VERIFY every player is on the correct team
4. NEVER rely on memory - ALWAYS search first
```

### WHILE WRITING:
```
1. Write 2-3 paragraphs MINIMUM per game
2. Include SPECIFIC stats, players, storylines
3. Use CONVERSATIONAL tone (contractions, opinions)
4. NEVER write "coming soon", "TBD", "TBA", or any placeholder
5. Use NUMERIC ESPN IDs for college logos (not abbreviations)
6. PAGE TITLE MUST INCLUDE THE DATE - e.g., "NBA Analysis - December 31, 2025"
```

### ⛔ CRITICAL: PAGE TITLES MUST HAVE DATES ⛔
**PERMANENTLY LOCKED - DECEMBER 31, 2025**

Every sports page title MUST include the full date so calendars work correctly:
```
✅ CORRECT: <title>NCAAF Bowl Games - December 29, 2025 | BetLegend</title>
✅ CORRECT: <title>NBA Analysis - December 31, 2025 | BetLegend</title>
❌ WRONG: <title>NCAAF Analysis Archive - Page 29 | BetLegend</title>
❌ WRONG: <title>NBA Analysis Archive - Page 26 | BetLegend</title>
```

**WHY:** The sync_calendars.py script extracts dates from page titles. Generic titles like "Page 29"
cause the script to use wrong fallback dates (file modification date), breaking the calendar.

### BEFORE COMMITTING:
```
1. RUN: python scripts/pre_post_check.py
2. RUN: python scripts/validate_content.py
3. FIX any errors found
4. ONLY commit when both scripts pass
```

### AFTER COMMITTING:
```
1. RUN: python scripts/sync_calendars.py
2. COMMIT the calendar updates
3. PUSH to GitHub
4. VERIFY on live site
```

### THE PRE-COMMIT HOOK:
A git pre-commit hook is now installed that will:
- BLOCK commits with placeholder text ("coming soon", etc.)
- BLOCK commits with non-numeric college logos
- BLOCK commits with wrong nav text ("Overview" instead of "Detailed Breakdown")
- BLOCK commits with pagination on sports pages
- WARN if sports page titles are missing dates
- AUTO-RUN sync_calendars.py when sports pages change (auto-stages calendar updates)

**If a commit is blocked, FIX the issues before trying again.**

---

## ⛔⛔⛔ SYNC RECORDS AFTER GRADING PICKS ⛔⛔⛔

### PERMANENTLY LOCKED - JANUARY 9, 2026

**After grading ANY picks in the Pick Tracker spreadsheet, I MUST run the sync scripts to update the records pages.**

### THE SYNC SCRIPTS:
```bash
# For NCAAF picks:
python scripts/sync_ncaaf_records.py

# After running sync scripts, commit and push:
git add .
git commit -m "Sync records from Pick Tracker"
git push
```

### WHEN TO RUN:
- After grading new NCAAF picks in the Pick Tracker
- After adding/modifying any picks in the Pick Tracker
- When user reports records page is out of sync

### WHAT THE SCRIPT DOES:
1. Reads existing picks from the HTML file (preserves historical data)
2. Fetches new picks from the Pick Tracker Google Sheet
3. MERGES new picks with existing data (no data loss)
4. Updates the HTML file with the merged records

**IF I GRADE PICKS AND DON'T SYNC THE RECORDS PAGE, I HAVE FAILED.**

---

## ⛔⛔⛔ SPORTS PAGES = PREGAME ANALYSIS ONLY ⛔⛔⛔

### PERMANENTLY LOCKED - DECEMBER 21, 2025

**ALL sports page articles are PREGAME ANALYSIS. NEVER post-game recaps.**

### THE RULE:
```
- Write PREGAME previews and analysis for upcoming games
- NEVER write post-game recaps or results
- Even if a game has already been played, write it as a preview
- Focus on: matchup analysis, betting lines, key players, storylines
- DO NOT include final scores or game outcomes
```

**Sports pages are for handicapping and betting analysis BEFORE games happen.**

---

## ⛔⛔⛔ BLOG PAGES: INSERT NEW POSTS - NEVER DELETE EXISTING ⛔⛔⛔

### PERMANENTLY LOCKED - JANUARY 1, 2026

**When adding new posts to blog pages (blog-page11.html, etc.), you MUST INSERT at the top and KEEP all existing posts.**

### THE ABSOLUTE RULE:
```
1. READ the current blog page file FIRST
2. FIND where posts start (after <h1>BetLegend Daily Picks and Analysis</h1>)
3. INSERT new post HTML at that location
4. KEEP ALL EXISTING POSTS BELOW - DO NOT DELETE THEM
5. NEVER overwrite the file with just the new post
```

### WHAT KEEPS HAPPENING (AND MUST STOP FOREVER):
1. User asks to add a new pick to blog-page11
2. Claude writes ONLY the new post and overwrites the entire file
3. All previous posts (Alabama, Miami, Sabres, Michigan, TCU, Illinois, Falcons, etc.) get DELETED
4. User loses days of work and content

### THE CORRECT WAY TO ADD A NEW POST:
```python
# 1. Read current file
with open('blog-page11.html', 'r') as f:
    content = f.read()

# 2. Find insertion point (after h1, before first post)
insert_point = content.find('</h1>') + 5

# 3. Create new post HTML
new_post = '''<script type="application/ld+json">...</script>
<div class="blog-post" id="post-YYYYMMDD-name">...</div>
<hr style="...">'''

# 4. INSERT new post, keeping everything else
new_content = content[:insert_point] + new_post + content[insert_point:]

# 5. Write back
with open('blog-page11.html', 'w') as f:
    f.write(new_content)
```

### FORBIDDEN:
- ❌ Writing a new file with just the new post
- ❌ Using Write tool to overwrite the entire blog page
- ❌ Forgetting to read the current file first
- ❌ Deleting ANY existing posts for ANY reason

**IF YOU DELETE EXISTING BLOG POSTS, YOU HAVE FAILED. THIS IS UNACCEPTABLE.**

---

## ⛔⛔⛔ NEVER RESTORE PAGES TO PREVIOUS VERSIONS ⛔⛔⛔

### PERMANENTLY LOCKED - DECEMBER 20, 2025

**DO NOT EVER restore, revert, or replace a page with a previous version unless the user EXPLICITLY asks you to.**

This has caused repeated issues where pages with real analysis get replaced with older versions containing placeholder content.

### THE RULE:
```
WHEN EDITING A PAGE:
- Read the CURRENT version first
- Make ONLY the specific changes needed
- NEVER overwrite good content with old placeholder versions
- If you see real analysis, KEEP IT
- If you see placeholders, REPLACE them with new content
```

### WHAT KEEPS HAPPENING (AND MUST STOP):
1. Page has real analysis (good)
2. Claude reads an old cached/summarized version with placeholders
3. Claude "fixes" the page by restoring the old placeholder version
4. User sees placeholders again and gets frustrated

### THE FIX:
- Always read the LIVE file before editing
- Never use content from conversation history/summaries
- When fixing issues, ADD or MODIFY - don't wholesale replace
- If unsure, ask the user before making major changes

**ZERO TOLERANCE. This destroys the site.**

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

## ⛔⛔⛔ MANDATORY WRITING STYLE: HUMAN, CONVERSATIONAL, ANALYTICAL ⛔⛔⛔

### PERMANENTLY LOCKED - DECEMBER 20, 2025

**ALL blog posts and sports content MUST be written like a passionate, knowledgeable sports fan talking to a friend.**

### THE WRITING STANDARD:
- ✅ **HUMAN-SOUNDING** - Write like a real person, not a robot
- ✅ **CONVERSATIONAL** - Use natural language, contractions, casual transitions
- ✅ **ANALYTICAL** - Back up opinions with real stats and verified data
- ✅ **INFORMATIVE** - Provide genuine insight, not filler content
- ✅ **PASSIONATE** - Show emotion and conviction about picks

### REQUIRED WRITING ELEMENTS:
- Use contractions naturally ("don't", "it's", "you're", "here's")
- Casual transitions ("Look", "Here's the thing", "Let me tell you")
- Show emotion ("This is huge", "I love this spot", "This line is a gift")
- Vary sentence length - mix short punchy sentences with longer analytical ones
- Take strong stances - be opinionated, not wishy-washy
- Include specific verified stats to support analysis

### WHAT GOOD WRITING LOOKS LIKE:
```
"Look, I get it. Laying 17 points in the playoff feels steep. But
sometimes the market gets it exactly right. Ole Miss already destroyed
Tulane 45-10 in September, and I don't care how much they've improved.
You don't overcome a 35-point beatdown in three months."
```

### WHAT BAD WRITING LOOKS LIKE:
```
"The Ole Miss Rebels present a compelling betting opportunity against
the Tulane Green Wave. Analysis indicates favorable conditions for the
home team. Several factors support this thesis."
```

### THE RULE:
```
EVERY sentence should sound like a human wrote it
EVERY paragraph should have personality and conviction
EVERY post should feel like expert analysis, not AI-generated content
```

**If it sounds robotic, rewrite it. No exceptions.**

---

## ⛔⛔⛔ MANDATORY PRE-COMMIT CHECK: NO PLACEHOLDERS ⛔⛔⛔

### PERMANENTLY LOCKED - DECEMBER 20, 2025

**BEFORE pushing ANY sports page to GitHub, you MUST run this check:**

```bash
# Run this BEFORE every commit to a sports page:
grep -r "coming soon\|analysis coming\|Matchup analysis\|preview coming\|TBD\|TBA\|N/A" [filename].html
```

**If ANY matches are found:**
1. DO NOT COMMIT
2. Replace ALL placeholder content with real analysis
3. Re-run the check until it returns ZERO matches
4. Only then commit and push

### THE SYSTEM:
```
EVERY EDIT to a sports page MUST include:
1. Grep check for placeholder patterns
2. If found → FIX THEM FIRST
3. Only push when grep returns ZERO matches
4. This is NON-NEGOTIABLE
```

### BANNED PLACEHOLDER PATTERNS:
- "coming soon" (any variation)
- "Matchup analysis coming"
- "Preview coming"
- "Analysis coming"
- "TBD", "TBA", "N/A"
- Single-sentence game descriptions
- Any generic text that doesn't include specific stats/players

**One placeholder = entire page is REJECTED. Fix it first.**

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

### A. SPORTS PAGES USE CALENDAR SIDEBAR ONLY - NO PAGINATION!

**PERMANENTLY LOCKED - DECEMBER 31, 2025**

**Sports pages (NBA, NHL, NFL, NCAAB, NCAAF, MLB, Soccer) must NOT have pagination links.**

Users navigate via the calendar sidebar on the left. Archive-link pagination divs are BANNED.

**BANNED - DO NOT USE ON SPORTS PAGES:**
- ❌ `<div class="archive-link">` pagination sections
- ❌ "← Newer" / "Older →" links
- ❌ "Page X of Y" indicators

**REQUIRED:**
- ✅ Calendar sidebar (already present in template)
- ✅ Run `python scripts/sync_calendars.py` after creating pages

**The pre-commit hook will BLOCK commits that have pagination on sports pages.**

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
3. Calendar sidebar displays correctly

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
