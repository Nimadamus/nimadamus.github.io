# PROTOCOL PAGE 2 - QUICK EXECUTION COMMANDS

## HOW TO USE

Simply tell Claude: **"Run Protocol #X"** and the task will be executed with 100% accuracy.

Each protocol includes ALL required steps, verification, and deployment.

---

## MASTER VERIFICATION RULES (APPLIES TO ALL PROTOCOLS)

**BEFORE including ANY information, I MUST:**
1. WebSearch to verify it
2. Find a reliable source confirming the fact
3. Only THEN include it

**IF I cannot verify something:**
- DO NOT INCLUDE IT
- DO NOT GUESS
- DO NOT USE MEMORY
- Leave it out or ask user

**WHAT MUST BE VERIFIED:**
| Category | What to Verify |
|----------|---------------|
| Players | Current team, injury status, trade history |
| Stats | PPG, APG, RPG, yards, TDs, goals, assists - with SPECIFIC NUMBERS |
| Advanced Analytics | ORtg, DRtg, DVOA, xG%, Corsi, EPA - with LEAGUE RANKINGS |
| Records | W-L, ATS record, home/road splits |
| Rankings | League rankings, conference standings |
| Trends | Win streaks, ATS trends, O/U trends - with SPECIFIC NUMBERS |
| Injuries | EXACT injury type (ACL vs Achilles), status |
| Historical Claims | Championships, records, milestones |
| Betting Lines | Current spread, total, moneyline |
| Game Details | Date, time, venue |

**2025 KEY CHANGES TO REMEMBER:**
- Kevin Durant → Houston Rockets
- Brandon Ingram → Toronto Raptors
- Mitch Marner → Vegas Golden Knights
- Jayson Tatum → ACHILLES injury (NOT ACL)
- Fred VanVleet → torn ACL, out for season
- OKC Thunder = 2025 NBA Champions
- Florida Panthers = back-to-back Stanley Cup champs (2024, 2025)

---

## PROTOCOL #1: COVERS CONSENSUS FULL UPDATE

**Command:** "Run Protocol #1" or "Covers Consensus"

### STEP 1: Scrape Latest Consensus Data
1. Navigate to `C:\Users\Nima\sportsbettingprime`
2. Fetch latest data from Covers.com for ALL active sports:
   - NFL, NBA, NHL, NCAAB, NCAAF (whatever has games today)
3. For EACH game, get:
   - Consensus % for spread
   - Consensus % for moneyline
   - Consensus % for total (O/U)
   - Current line/spread values
   - Game time

### STEP 2: Verify Data Accuracy (CRITICAL)
1. Cross-reference EVERY game against Covers.com live data
2. Verify consensus percentages match source EXACTLY
3. Verify lines/spreads are current (lines move - must be accurate)
4. Verify game times are correct
5. Fix ANY discrepancies - 100% accuracy required
6. If data doesn't match source, DO NOT POST - fix it first

### STEP 3: Update the Page
1. Update `covers-consensus.html` with fresh data
2. Add today's date/timestamp
3. Include ALL games for each sport - no partial data
4. Archive old content if needed

### STEP 4: Verify Site Navigation
1. Ensure main page shows NEW content
2. Check pagination/archive links work
3. Verify sport filter tabs work (NFL, NBA, NHL, CBB, CFB)

### STEP 5: Deploy
1. `git add covers-consensus.html`
2. `git commit -m "Update Covers Consensus - [DATE]"`
3. `git push`
4. Verify live at sportsbettingprime.com/covers-consensus.html
5. Spot-check 3-5 games on live site against source

### Files:
- `C:\Users\Nima\sportsbettingprime\covers-consensus.html`

---

## PROTOCOL #2: UPDATE HANDICAPPING HUB

**Command:** "Run Protocol #2" or "Handicapping Hub"

### STEP 1: Fetch Latest Data
1. Navigate to `C:\Users\Nima\nimadamus.github.io`
2. Run `C:\Users\Nima\HANDICAPPING_HUB_AUTO.bat`
3. Fetch latest for ALL sports:
   - Betting lines (spread, ML, total)
   - Power ratings
   - Team statistics
   - Injury reports

### STEP 2: Verify Data
1. Cross-reference lines with current sportsbook data
2. Verify injury reports are current
3. Check power ratings calculated correctly

### STEP 3: Update Page
1. Update `handicapping-hub.html`
2. Ensure all data displays correctly

### STEP 4: Deploy
1. `git add handicapping-hub.html`
2. `git commit -m "Update Handicapping Hub - [DATE]"`
3. `git push`
4. Verify live at betlegendpicks.com/handicapping-hub.html

### Files:
- `C:\Users\Nima\nimadamus.github.io\handicapping-hub.html`

---

## PROTOCOL #3: NEW FEATURED GAME OF THE DAY

**Command:** "Run Protocol #3" or "New Featured Game"

### STEP 1: Get Game Info
1. Ask user which game to feature (or user provides it)
2. WebSearch to verify ALL info about the game:
   - Both teams' current records
   - Key injuries
   - Current betting lines
   - Recent form
   - Head-to-head history

### STEP 2: Write Analysis
Following POSTING_PROTOCOL.md style:
- Human-sounding, passionate, conversational tone
- Use contractions naturally ("don't", "it's", "you're")
- Casual transitions ("Look", "Here's the thing", "And get this")
- Show emotion ("This is huge", "I love this spot")
- NO robotic or AI-sounding language
- NO bold words in content paragraphs
- NO bullet points in content - flowing paragraphs only
- Gold-colored section headers
- 3-5 sentences per paragraph

**Required Stats (verify ALL via search):**
- Current records with W-L
- Offensive/defensive ratings with LEAGUE RANKINGS
- ATS record with specific numbers
- O/U trends with specific numbers
- Key player stats with context
- Injury impact analysis

### STEP 3: Create New Page
1. Check current page number (currently page 15 as of Dec 8, 2025)
2. Create `featured-game-of-the-day-page[XX].html` with incremented number
3. Include:
   - Post header with game title
   - Timestamp (current time)
   - Featured image
   - Full analysis
   - Verdict section with pick

### STEP 4: Update ALL Site Links (CRITICAL - DO NOT SKIP)
Run this Python script to update ALL 300+ pages:
```python
import os, re
REPO = r'C:\Users\Nima\nimadamus.github.io'
NEW = 'featured-game-of-the-day-page[XX].html'  # UPDATE NUMBER

for root, dirs, files in os.walk(REPO):
    dirs[:] = [d for d in dirs if d != '.git']
    for f in files:
        if f.endswith('.html'):
            path = os.path.join(root, f)
            with open(path, 'r', encoding='utf-8', errors='ignore') as file:
                c = file.read()
            orig = c
            c = re.sub(r'featured-game-of-the-day-page\d+\.html', NEW, c)
            c = re.sub(r'featured-game-of-the-day\.html', NEW, c)
            if c != orig:
                with open(path, 'w', encoding='utf-8') as file:
                    file.write(c)
                print(f'Updated: {f}')
```

### STEP 5: Deploy
1. `git add .` (all changed files)
2. `git commit -m "Add Featured Game [TEAMS] - [DATE]"`
3. `git push`
4. **VERIFY:** Click Featured Game link on live site - must show NEW game, not old one

### Why This Matters:
On Dec 8, 2025, users clicked Featured Game and saw Detroit vs Dallas from Dec 4 - FOUR DAYS OLD. This is unacceptable. Links MUST be updated.

---

## PROTOCOL #4: ALL SPORTS SLATE POSTS

**Command:** "Run Protocol #4" or "All Slates"

Creates slate posts for ALL active sports with 100% accuracy.

### STEP 1: Determine Active Sports
Check what sports have games TODAY:
- NBA (October - June)
- NHL (October - June)
- NFL (September - February, specific game days)
- NCAAB (November - April)
- NCAAF (August - January)
- MLB (March - October)
- Soccer (year-round)

### STEP 2: For EACH Sport - MANDATORY VERIFICATION

#### A. Verify EXACT Game Count (DO NOT SKIP)
1. WebSearch: "[Sport] schedule [DATE] all games"
2. COUNT every single game
3. Write down the exact number
4. NEVER say "X-game slate" until verified
5. If search incomplete, search AGAIN with different terms

#### B. List ALL Games
- Every single game, no exceptions
- Not 50%, not 80% - ALL of them

#### C. For EACH Game, Verify:
**Teams:**
- [ ] Both teams' current records (W-L or W-L-OT)
- [ ] Verify players are on correct teams (check 2025 trades!)

**Injuries:**
- [ ] Search "[Player] injury [Month] 2025"
- [ ] Verify EXACT injury type (ACL vs Achilles matters!)
- [ ] Verify status (out, questionable, probable)

**Stats (with SPECIFIC NUMBERS and LEAGUE RANKINGS):**

*NBA:*
- [ ] Offensive rating with rank (e.g., "125.7 ORtg, 1st in NBA")
- [ ] Defensive rating with rank
- [ ] Net rating
- [ ] Pace factor
- [ ] PPG and PPG allowed with ranks
- [ ] Key player stats with context

*NHL:*
- [ ] Goals for/against per game with rank
- [ ] Power play % with rank
- [ ] Penalty kill % with rank
- [ ] Corsi For % at 5v5
- [ ] Expected Goals % at 5v5
- [ ] Goaltender stats (GAA, SV%, record)
- [ ] Recent form (e.g., "7-2-1 in last 10")

*NFL:*
- [ ] Points for/against per game
- [ ] DVOA or EPA rankings
- [ ] Red zone efficiency
- [ ] Turnover differential
- [ ] Key player stats

*NCAAB:*
- [ ] Current record and ranking
- [ ] KenPom/NET rankings
- [ ] Offensive/defensive efficiency
- [ ] Key player stats

**Betting Trends (with SPECIFIC NUMBERS):**
- [ ] ATS record (e.g., "12-7 ATS, 8-3 as favorites")
- [ ] O/U record (e.g., "OVER 11-8 this season")
- [ ] Home/road splits
- [ ] Recent ATS trend (e.g., "4-1 ATS last 5")

#### D. Write Analysis for EACH Game
Following POSTING_PROTOCOL.md style:

**WRITE LIKE THIS (passionate, human):**
"Look, I get it. The Celtics are struggling without Tatum, but here's the thing - this team's defensive identity doesn't disappear just because one guy is out. They're still holding opponents to 108.2 points per game, 5th in the league. And get this: they're 7-2 ATS at home this season."

**NOT LIKE THIS (robotic, AI):**
"The Boston Celtics present a compelling opportunity. Analysis indicates defensive metrics remain strong. Several factors support consideration of this matchup."

**Required Elements:**
- Human-sounding, passionate tone
- Specific numbers with league rankings
- Betting angles with specific ATS/O/U records
- Injury impact analysis
- NO bullet points in content
- NO bold words in paragraphs
- Gold section headers
- 3-5 sentences per paragraph

### STEP 3: Update Each Sport Page
Add new content to TOP of each page:
- NBA → `nba.html`
- NHL → `nhl.html`
- NFL → `nfl.html`
- NCAAB → `ncaab.html`
- NCAAF → `ncaaf.html`
- MLB → `mlb.html`
- Soccer → `soccer.html`

Include timestamp for each slate.

### STEP 4: Deploy
1. `git add [all changed files]`
2. `git commit -m "[DATE] Slate Posts - NBA, NHL, NCAAB"` (list sports)
3. `git push`
4. Verify each page is live and displays correctly

### FINAL CHECKLIST (NON-NEGOTIABLE):
- [ ] Verified EXACT game count for each sport
- [ ] Covered ALL games - not partial
- [ ] Every player verified on correct team
- [ ] Every injury verified (exact type and status)
- [ ] Every stat has specific number AND league ranking
- [ ] Every betting trend has specific record
- [ ] Writing is human/passionate, not robotic
- [ ] No information was guessed or assumed

---

## PROTOCOL #5: NEW BLOG PICK

**Command:** "Run Protocol #5" or "New Blog Pick"

### STEP 1: Get Pick Details
Ask user for: team, line, sport (or user provides it)

### STEP 2: Verify Everything via WebSearch
- [ ] Current betting line is accurate
- [ ] Team records are current
- [ ] Player-team associations are correct
- [ ] Injury statuses are current
- [ ] Stats are verified with specific numbers
- [ ] ATS/O/U trends are verified

### STEP 3: Write Analysis (2000+ words)
Following POSTING_PROTOCOL.md exactly:

**Writing Style:**
- Extremely human, passionate, conversational
- Use contractions ("don't", "it's", "won't")
- Casual transitions ("Look", "Here's the thing", "Listen")
- Show emotion ("This is huge", "I love this spot", "This line is a gift")
- Be opinionated - take strong stances
- NO robotic/AI language
- NO corporate speak
- NO bold words in paragraphs
- NO bullet points in content
- Flowing paragraphs, 3-5 sentences each

**Required HTML Structure:**
```html
<div class="blog-post" id="post-[YYYYMMDD]-[slug]">
<meta name="title" content="[SEO title 50-60 chars]"/>
<meta name="description" content="[SEO description 145-160 chars]"/>

<div class="post-header" style="text-align: center;">[TITLE]</div>
<div class="post-time" style="text-align: center;">Posted: [TIME], [DATE]</div>

<figure style="margin: 20px auto; max-width: 1140px;">
<img alt="[Descriptive SEO alt text]" loading="lazy" src="images/[IMAGE].png" style="display:block; margin: 0 auto; width:85%; border-radius: 8px;"/>
</figure>

[CONTENT WITH GOLD SECTION HEADERS]

<div class="verdict">
<p class="verdict-title">The Pick</p>
<p class="the-pick">[TEAM] [LINE]</p>
</div>
</div>
```

**Gold Section Headers:**
```html
<p><span style="color: gold; font-weight: 700; font-size: 22px;">[Header Text]</span></p>
```

### STEP 4: Add to Blog
1. Add to TOP of `blog-page10.html`
2. Verify formatting displays correctly

### STEP 5: Deploy
1. `git add blog-page10.html`
2. `git commit -m "Add [TEAM] [LINE] pick - [DATE]"`
3. `git push`
4. Verify live at betlegendpicks.com/blog-page10.html

---

## PROTOCOL #6: NEW MONEYLINE PARLAY

**Command:** "Run Protocol #6" or "New ML Parlay"

### STEP 1: Get Parlay Legs
Ask user for parlay legs (or user provides them)

### STEP 2: Verify Each Leg
For EACH leg:
- [ ] Team is correct
- [ ] Moneyline odds are current
- [ ] Verify team/player info
- [ ] Check injuries
- [ ] Research relevant stats

### STEP 3: Write Analysis
For each leg, include:
- Why this team wins
- Key stats supporting the pick
- Injury considerations
- Risk factors

Calculate combined parlay odds.

### STEP 4: Update Page
Update `moneyline-parlay-of-the-day.html` with:
- New parlay at TOP
- Timestamp
- Each leg's analysis
- Combined odds

### STEP 5: Deploy
1. `git add moneyline-parlay-of-the-day.html`
2. `git commit -m "Add ML Parlay - [DATE]"`
3. `git push`
4. Verify live

---

## PROTOCOL #7: UPDATE SPORTS BETTING PRIME (FULL SITE)

**Command:** "Run Protocol #7" or "Update SBP"

### STEP 1: Navigate to Repo
`C:\Users\Nima\sportsbettingprime`

### STEP 2: Update All Content
1. **Covers Consensus** (`covers-consensus.html`):
   - Run Protocol #1 steps
   - Verify all data matches source

2. **Index Page** (`index.html`):
   - Update if any content needs refreshing
   - Verify links work

3. **Any Other Pages**:
   - Check for stale content
   - Update as needed

### STEP 3: Verify Data Accuracy
- Cross-reference all data with sources
- 100% accuracy required

### STEP 4: Deploy
1. `git add .`
2. `git commit -m "Update Sports Betting Prime - [DATE]"`
3. `git push`
4. Verify live at sportsbettingprime.com

### Files:
- Repo: `C:\Users\Nima\sportsbettingprime`
- Key pages: `index.html`, `covers-consensus.html`

---

## PROTOCOL #8: FIX PAGINATION

**Command:** "Run Protocol #8" or "Fix Pagination"

### Pagination Rules:
- `sport.html` = NEWEST content (e.g., Page 14 of 14)
- `sport-page2.html` = Second newest
- `sport-pageN.html` = OLDEST content

### STEP 1: Check All Sport Pages
For each sport (nba, nhl, nfl, ncaab, ncaaf, mlb, soccer):
- [ ] `sport.html` "Older" links to `sport-page2.html`
- [ ] `sport-page2.html` "Newer" links to `sport.html`
- [ ] Page numbers are correct throughout chain
- [ ] No broken links

### STEP 2: Fix Issues
Correct any:
- Broken links
- Wrong page numbers
- Missing pagination

### STEP 3: Deploy
1. `git add [fixed files]`
2. `git commit -m "Fix pagination - [sport pages fixed]"`
3. `git push`
4. Click through pagination on live site to verify

---

## PROTOCOL #9: VERIFY LIVE SITE

**Command:** "Run Protocol #9" or "Check Site"

### STEP 1: Check BetLegend (betlegendpicks.com)
1. Load homepage
2. Click "Featured Game" - verify it shows CURRENT game (not old)
3. Click through main nav:
   - NBA page loads
   - NHL page loads
   - NFL page loads
   - NCAAB page loads
   - Blog page loads
4. Check latest content appears
5. Test pagination on one sport page

### STEP 2: Check Sports Betting Prime (sportsbettingprime.com)
1. Load homepage
2. Load covers-consensus.html
3. Verify sport tabs work
4. Check data looks current

### STEP 3: Report
Report any issues found:
- Broken links
- Stale content
- Missing pages
- Display errors

---

## PROTOCOL #10: EMERGENCY ROLLBACK

**Command:** "Run Protocol #10" or "Rollback"

### STEP 1: Identify Problem
Ask user what needs to be rolled back

### STEP 2: Find Commit
```bash
git log --oneline -10
```
Identify the commit to revert

### STEP 3: Revert
```bash
git revert [commit-hash]
git push
```

### STEP 4: Verify
Check live site is restored to working state

---

## KEY REMINDERS FOR ALL PROTOCOLS

1. **100% ACCURACY** - Verify EVERYTHING via WebSearch. No guessing. No memory.
2. **COMPLETE COVERAGE** - All games, all sports, no partial work.
3. **HUMAN WRITING** - Passionate, conversational, emotional. Never robotic.
4. **SPECIFIC NUMBERS** - Stats must have exact numbers AND league rankings.
5. **ALWAYS PUSH** - Every protocol ends with git push.
6. **ALWAYS VERIFY** - Check live site after pushing.
7. **CHECK 2025 TRADES** - Durant to Rockets, Marner to Vegas, Ingram to Raptors.
8. **INJURY DETAILS MATTER** - ACL vs Achilles is different. Verify exact type.

**One false claim destroys credibility. Verify EVERYTHING.**

---

**Last Updated:** December 9, 2025
