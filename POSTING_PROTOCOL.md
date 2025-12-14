# BetLegend Posting Protocol

## MANDATORY REQUIREMENTS FOR ALL POSTS

This protocol MUST be followed for every blog post and news article uploaded to betlegendpicks.com.

---

## ⚠️ CRITICAL WARNING: 100% VERIFICATION OR DON'T POST ⚠️

### ONE FALSE CLAIM DESTROYS CREDIBILITY

**NOTHING goes live without 100% verification. NOTHING.**

Before ANY content is posted to BetLegend, you MUST verify:

| Category | What to Verify | Why It Matters |
|----------|---------------|----------------|
| **Players** | Current team, injury status, trade history | Players change teams constantly - Kevin Durant to Rockets, Marner to Vegas, etc. |
| **Stats** | PPG, APG, RPG, yards, TDs, goals, assists | One wrong stat makes readers question everything |
| **Advanced Analytics** | ORtg, DRtg, DVOA, xG%, Corsi, EPA | These are the backbone of credible analysis |
| **Records** | W-L, ATS record, home/road splits | Easy to verify, inexcusable to get wrong |
| **Rankings** | League rankings, conference standings | Changes daily - always search current data |
| **Trends** | Win streaks, ATS trends, O/U trends | Must have specific numbers, not guesses |
| **Injuries** | Exact injury type (ACL vs Achilles), status | Tatum has ACHILLES not ACL - details matter |
| **Historical Claims** | Championships, records, milestones | OKC = 2025 NBA Champs, Panthers = back-to-back |
| **Betting Lines** | Current spread, total, moneyline | Lines move - verify before posting |
| **Game Details** | Date, time, venue, broadcast | Simple facts that must be correct |

### THE VERIFICATION RULE IS ABSOLUTE

```
IF you cannot verify it with a search → DO NOT INCLUDE IT
IF you're "pretty sure" but can't confirm → DO NOT INCLUDE IT
IF your memory says one thing but you can't find a source → DO NOT INCLUDE IT
IF the information is outdated → DO NOT INCLUDE IT
```

### WHY THIS MATTERS

- One wrong player-team association = readers lose trust
- One fabricated stat = entire article becomes suspect
- One incorrect injury detail = you look like you don't do research
- One made-up trend = credibility destroyed permanently

**The internet remembers everything. False information spreads. Your reputation is on the line with every single claim.**

### VERIFICATION IS NOT OPTIONAL

This is not a suggestion. This is not a guideline. This is an ABSOLUTE REQUIREMENT.

Every player. Every stat. Every trend. Every record. Every injury. Every analytical claim. Every historical reference. Every betting line. Every single piece of information.

**100% verified or it doesn't go live. Period.**

---

## ⛔ CRITICAL WARNING: FEATURED GAME LINKS MUST BE UPDATED DAILY ⛔

### BROKEN LINKS = BROKEN SITE

**EVERY TIME a new Featured Game of the Day is posted, ALL 300+ pages on the site MUST be updated.**

This is NOT optional. This is NOT something to "get around to later." This happens IMMEDIATELY.

### THE DECEMBER 8, 2025 INCIDENT

On December 8, 2025, users clicking "Featured Game of the Day" were taken to the Detroit vs Dallas game from December 4th - FOUR DAYS OLD. The actual featured game was Eagles vs Chargers. This is UNACCEPTABLE.

### THE RULE

```
NEW Featured Game posted → IMMEDIATELY run batch update script → PUSH → VERIFY LIVE
```

**There is NO excuse for outdated Featured Game links. NONE.**

### HOW TO UPDATE (Takes 30 seconds)

```python
# Run this EVERY TIME a new Featured Game is created
import os, re
REPO = r'C:\Users\Nima\nimadamus.github.io'
NEW = 'featured-game-of-the-day-pageXX.html'  # ← UPDATE THIS NUMBER

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
```

### DAILY CHECKLIST

- [ ] New Featured Game created? → Run script immediately
- [ ] Script updated all files? → Verify count
- [ ] **Calendar data updated?** → Add entry to `featured-games-data.js`
- [ ] Pushed to GitHub? → Do it NOW
- [ ] Checked live site? → Click the link yourself

**If the Featured Game link ever shows an old game, someone screwed up. Don't let it be you.**

### CALENDAR AUTO-UPDATE (NEW - December 2025)

The Featured Game Calendar now auto-populates from `featured-games-data.js`. When creating a new featured game:

**Add ONE line to `featured-games-data.js`:**
```javascript
{ date: "2025-12-14", page: "featured-game-of-the-day-page19.html", title: "Game Title" },
```

The calendar will automatically:
- Show the new date as clickable
- Link to the correct page
- Display the game title on hover
- Update "Today" marker based on current date
- Show the latest game in stats bar

**NO MORE manual calendar HTML editing required!**

---

## 1. ACCURACY & VERIFICATION

### ⛔ ABSOLUTE RULE: 100% ONLINE VERIFICATION REQUIRED ⛔

**EFFECTIVE DECEMBER 1, 2025 - ZERO TOLERANCE POLICY**

**EVERY SINGLE PIECE OF INFORMATION MUST BE VERIFIED WITH AN ONLINE SEARCH BEFORE POSTING. NO EXCEPTIONS.**

This includes but is not limited to:
- Every number (stats, records, scores, percentages, rankings)
- Every player name and their current team
- Every stat (PPG, APG, RPG, goals, assists, yards, touchdowns, etc.)
- Every trend (winning streaks, ATS records, head-to-head history)
- Every matchup detail
- Every location (arena, stadium, city)
- Every date and time
- Every injury (type, status, timeline)
- Every trade or roster move
- Every historical claim
- Every championship or award reference

### THE VERIFICATION PROCESS

**BEFORE writing ANY claim, you MUST:**
1. Run a WebSearch to verify the information
2. Find a reliable source confirming the fact
3. Only THEN include it in the content

**If you cannot verify something with a search:**
- DO NOT INCLUDE IT
- DO NOT GUESS
- DO NOT USE MEMORY
- Either find a verifiable alternative or leave it out entirely

### WHY THIS RULE EXISTS

This rule was implemented after repeated incidents of fabricated information being posted, including:
- Fake player statistics
- Wrong team records
- Incorrect division standings
- Made-up historical claims
- Future dates presented as past events

**One false claim destroys credibility. This site's reputation depends on accuracy.**

### VERIFICATION SOURCES
- WebSearch for current stats and news
- ESPN, official league websites for schedules and standings
- Team official websites for rosters
- User-provided information (considered verified)

### CONSEQUENCES OF VIOLATING THIS RULE
- Content with unverified information damages the site's credibility
- All unverified claims must be removed immediately upon discovery
- There is NO acceptable excuse for posting fabricated information

---

## 1A. MANDATORY SLATE POST VERIFICATION CHECKLIST

### ⚠️ CRITICAL: COMPLETE THIS CHECKLIST BEFORE WRITING ANY SLATE POST ⚠️

**This section was added after errors were made claiming "5-game slates" when there were actually 15 games. This is UNACCEPTABLE and damages credibility.**

### STEP 1: VERIFY TOTAL GAME COUNT (MANDATORY)
Before writing ANY slate post, you MUST:
1. Search ESPN/official league schedule for the EXACT date
2. COUNT every single game scheduled for that date
3. WRITE DOWN the total number of games
4. NEVER use phrases like "full slate" or "[X]-game slate" until you have verified the exact count
5. If search results are incomplete, search AGAIN with different terms

**Example Searches Required:**
- "NBA schedule November 26 2025 all games"
- "NHL schedule November 26 2025 complete"
- "College basketball November 26 2025 full schedule"

### STEP 2: VERIFY EVERY PLAYER-TEAM ASSOCIATION (MANDATORY)
Before mentioning ANY player, you MUST verify they currently play for that team:
- [ ] Search "[Player Name] [Team Name] 2025 roster"
- [ ] Confirm they were not traded, released, or injured out for season
- [ ] If player was traded in 2025, verify the CURRENT team

**Common Errors to Avoid:**
- Players traded mid-season (e.g., Kevin Durant to Rockets, Brandon Ingram to Raptors, Mitch Marner to Vegas)
- Players with season-ending injuries still listed on old rosters
- Assuming a player is still with their 2024 team

### STEP 3: VERIFY ALL INJURIES (MANDATORY)
Before mentioning ANY injury, you MUST:
- [ ] Search "[Player Name] injury November 2025"
- [ ] Verify the EXACT injury type (ACL vs Achilles, knee vs ankle, etc.)
- [ ] Verify current status (out, questionable, probable)
- [ ] Verify expected return timeline if mentioned

**Recent Examples of Injury Errors:**
- Jayson Tatum has an ACHILLES injury, NOT ACL
- Tyrese Haliburton has an ACHILLES injury from 2025 Finals
- Connor Hellebuyck - knee surgery, 4-6 weeks (November 2025)
- Fred VanVleet - torn ACL, out for 2025-26 season

### STEP 4: VERIFY ALL TEAM RECORDS (MANDATORY)
Before stating ANY team record:
- [ ] Search "[Team Name] record November 2025"
- [ ] Cross-reference with official standings
- [ ] If exact record unavailable, use general terms ("struggling," "hot streak") instead of specific numbers
- [ ] NEVER guess a record - verify or omit

### STEP 5: VERIFY ALL STATISTICS (MANDATORY)
Before citing ANY player stats:
- [ ] Search "[Player Name] stats 2025-26 season"
- [ ] Verify PPG, RPG, APG, or other metrics from official sources
- [ ] Round to one decimal place and use approximate language if needed
- [ ] If stats vary by source, use the most conservative/common number

### STEP 6: VERIFY CHAMPIONSHIP/HISTORICAL CLAIMS (MANDATORY)
Before stating any championship or historical information:
- [ ] Search "[Team Name] championship [year]"
- [ ] Verify titles, streaks, records are accurate
- [ ] Example: OKC Thunder ARE 2025 NBA Champions (beat Pacers in 7 games)
- [ ] Example: Florida Panthers ARE back-to-back Stanley Cup champions (2024, 2025)

### SLATE POST FINAL CHECKLIST

**BEFORE hitting save/commit on ANY slate post:**

- [ ] I verified the EXACT number of games on the schedule
- [ ] I covered ALL games in the slate (not 33%, not 50% - ALL of them)
- [ ] I verified every player mentioned is on the correct team
- [ ] I verified every injury type and status mentioned
- [ ] I verified every team record mentioned
- [ ] I verified every statistic mentioned
- [ ] I did NOT make up ANY information
- [ ] I did NOT assume ANY information from memory
- [ ] I searched and verified EVERYTHING

### IF IN DOUBT

If you cannot verify information:
1. DO NOT INCLUDE IT
2. Use general language instead of specific claims
3. Ask the user to provide/verify the information
4. It is better to have LESS content that is 100% accurate than MORE content with errors

**Remember: One false claim destroys credibility. Every fact must be verified.**

---

## 1B. MANDATORY ADVANCED STATS & BETTING TRENDS

### ⚠️ CRITICAL: ALL ANALYSIS MUST BE DATA-DRIVEN WITH VERIFIED NUMBERS ⚠️

**EFFECTIVE DECEMBER 3, 2025 - ZERO TOLERANCE FOR CONJECTURE**

Every game analysis MUST include VERIFIED advanced statistics with SPECIFIC NUMBERS from trusted sources. NO OPINIONS OR GUESSES. ALL NUMBERS MUST BE SOURCED AND VERIFIED.

**THE DIFFERENCE:**
- **WRONG:** "The Nuggets have a great offense" ← UNACCEPTABLE
- **RIGHT:** "The Nuggets rank 1st in offensive rating at 125.7 points per 100 possessions" ← CORRECT

### VERIFICATION SOURCES (MANDATORY)
- **NBA:** NBA.com/stats, Basketball-Reference, NBAstuffer, StatMuse, FOX Sports
- **NHL:** MoneyPuck, Natural Stat Trick, NHL.com/stats, Hockey-Reference
- **Betting:** Covers.com, OddsShark, TeamRankings, Action Network, VegasInsider

### REQUIRED STATS BY SPORT

#### NHL (Hockey)
For EVERY team mentioned, include SPECIFIC NUMBERS:
- [ ] Current record (W-L-OT) in game header
- [ ] Goals for/against per game WITH LEAGUE RANKING (e.g., "3.26 GF/G, 10th in NHL")
- [ ] Power play % WITH LEAGUE RANKING (e.g., "23.7% PP, 10th in NHL")
- [ ] Penalty kill % WITH LEAGUE RANKING (e.g., "81.2% PK, 15th in NHL")
- [ ] Corsi For % at 5v5 (e.g., "52% CF%, indicating possession dominance")
- [ ] Expected Goals % at 5v5 (e.g., "48.5% xG%, slightly underperforming possession")
- [ ] Goaltender stats (GAA, SV%, record) - MUST be current
- [ ] Recent form with SPECIFIC NUMBERS (e.g., "7-2-1 in last 10")
- [ ] Key player point totals WITH LEAGUE RANKING

#### NBA (Basketball)
For EVERY team mentioned, include SPECIFIC NUMBERS:
- [ ] Current record in game header
- [ ] Offensive rating WITH LEAGUE RANKING (e.g., "125.7 ORtg, 1st in NBA")
- [ ] Defensive rating WITH LEAGUE RANKING (e.g., "115.9 DRtg, 18th in NBA")
- [ ] Net rating (e.g., "+9.8 NetRtg, 3rd in NBA")
- [ ] Pace factor (e.g., "102.3 possessions per game")
- [ ] Points per game WITH LEAGUE RANKING
- [ ] Points allowed per game WITH LEAGUE RANKING
- [ ] eFG% or True Shooting % where relevant
- [ ] Key player stats WITH CONTEXT (e.g., "Jokic: 29.0/12.8/11.1, leads league in triple-doubles")

#### NFL (Football)
For EVERY team mentioned, include:
- [ ] Current record in game header
- [ ] Points for/against per game
- [ ] Offensive/defensive DVOA or EPA rankings
- [ ] Red zone efficiency (TD %)
- [ ] Turnover differential
- [ ] ATS record (home, road, as favorite/underdog)
- [ ] Recent O/U trends
- [ ] Key player stats with league context

#### College Basketball (NCAAB)
For EVERY team mentioned, include:
- [ ] Current record and ranking
- [ ] Conference record where applicable
- [ ] KenPom/NET rankings if available
- [ ] Offensive/defensive efficiency
- [ ] Key player stats
- [ ] ATS and O/U trends

#### College Football (NCAAF)
For EVERY team mentioned, include:
- [ ] Current record and ranking
- [ ] Conference record
- [ ] Points for/against per game
- [ ] Key offensive/defensive stats
- [ ] ATS and O/U trends

#### MLB (Baseball)
For EVERY team mentioned, include:
- [ ] Current record
- [ ] Starting pitcher stats (ERA, WHIP, K/9, recent form)
- [ ] Team batting average, OPS, runs per game
- [ ] Bullpen ERA and save conversion rate
- [ ] Home/road splits
- [ ] O/U trends and run line history

#### Soccer
For EVERY team mentioned, include:
- [ ] Current league position and record
- [ ] Goals for/against
- [ ] Home/away form
- [ ] Key player availability
- [ ] Head-to-head history

### BETTING TRENDS TO INCLUDE (WITH SPECIFIC NUMBERS)

Every article MUST include relevant betting trends WITH SPECIFIC RECORDS:
- ATS record (e.g., "Nuggets are 12-7 ATS this season, 8-3 ATS as favorites")
- Over/Under record (e.g., "OVER is 11-8 in Nuggets games this season")
- Home/road betting splits (e.g., "7-2 ATS at home, 5-5 ATS on the road")
- Recent ATS trend (e.g., "4-1 ATS in last 5 games")
- Line movement if significant (e.g., "Line moved from -6.5 to -7.5")

### ANALYTICAL INSIGHTS REQUIRED

Every game analysis MUST include:
1. **The Matchup Edge:** Identify specific statistical advantages (e.g., "Denver's 125.7 ORtg vs Indiana's 122.3 DRtg creates a +3.4 efficiency gap")
2. **Key Number Analysis:** Why the spread matters (e.g., "7 is a key number in basketball, hitting X% of games")
3. **Trend Convergence:** Multiple trends pointing same direction (e.g., "ATS record + O/U trend + head-to-head history all favor...")
4. **Pace Analysis:** How pace affects totals (e.g., "Both teams in top 10 in pace, expect 230+ total")
5. **Rest/Schedule Spots:** Back-to-backs, travel, rest advantages with specific context

### VERIFICATION PROCESS FOR STATS

1. Search for current team stats on ESPN, official league sites, Sports Reference, or StatMuse
2. Cross-reference with betting sites (Covers, OddsShark, Action Network) for trends
3. Verify player stats are current (within last 1-2 days)
4. Include league rankings to provide context (e.g., "25.0% PP, 5th in NHL")
5. Note injury impacts with specific player names and replacement options
6. **NEVER USE MEMORY** - Always search to verify even if you think you know the stat

### EXAMPLES OF PROPER DATA-DRIVEN ANALYSIS

**EXCELLENT:**
"Denver enters with the NBA's best offensive rating at 125.7 points per 100 possessions (1st), while Indiana allows 118.6 points per 100 (22nd) - a +7.1 efficiency differential. The Nuggets are 12-7 ATS this season (63.2%), including 8-3 ATS as road favorites. The OVER has hit in 11 of Denver's 19 games (57.9%), and with Indiana's pace (99.1, 8th in NBA) creating extra possessions, the 235.5 total looks live. Jokic's 29.0/12.8/11.1 stat line leads all players in PER (32.1) and BPM (+12.4)."

**GOOD:**
"The Stars are averaging 3.37 goals per game (3rd in NHL, 91 GF) while allowing just 2.56 goals against (7th, 69 GA). Their power play is operating at 33.3%, ranking 2nd in the entire league. At 5v5, Dallas owns a 52.1% Corsi For and 51.8% xG%, indicating sustainable possession dominance."

**UNACCEPTABLE:**
"The Stars have been playing great hockey and their offense is clicking."
"Denver's offense should dominate Indiana's weak defense."
"This feels like a good spot for the Nuggets."

---

## 1C. CONTENT TYPES - HANDICAPPING HUB VS SPORTS PAGES VS BLOG

### ⚠️ UNDERSTAND THE DIFFERENCE BETWEEN PAGE TYPES ⚠️

---

### HANDICAPPING HUB (handicapping-hub.html)
**Purpose:** Stats dashboard for quick reference and data lookup

The Handicapping Hub is a DATA-FOCUSED page containing:
- ✅ Power ratings (calculated from win %, point differential, efficiency)
- ✅ Team statistics (offensive and defensive stats side by side)
- ✅ Betting lines (spread, moneyline, totals)
- ✅ Injury reports (names and status)
- ✅ Quick comparison data

**The Hub is NOT for:**
- ❌ Written analysis or commentary
- ❌ Picks or recommendations
- ❌ Long-form content

---

### SPORTS PAGES (nba.html, nhl.html, nfl.html, ncaab.html, ncaaf.html, mlb.html, soccer.html)
**Purpose:** Human-written article-style analysis for each game

**SPORTS PAGES MUST HAVE FOR EACH GAME:**
- ✅ **Article-style writeup** (3-5 paragraphs per game, conversational tone)
- ✅ **Human-sounding commentary** - Write like a real sports analyst, not a robot
- ✅ **Narrative and storytelling** - What's the storyline of this matchup?
- ✅ **Key matchup breakdown** - What to watch for
- ✅ **Injury impact analysis** - How injuries affect the game
- ✅ **Betting angles** - ATS trends, O/U tendencies, sharp money indicators
- ✅ **Stats WITH context** - Don't just list numbers, explain why they matter
- ✅ **Historical context** - Relevant head-to-head history

**EXAMPLE SPORTS PAGE ARTICLE FORMAT:**
```
### [Team] @ [Team] - [Time] ET

The [Away Team] head into [City] riding a [X]-game winning streak,
but they'll face a tough test against a [Home Team] squad that's
been dominant at home this season.

**The Matchup:** [Away Team] ranks [X]th in offensive efficiency (115.2 ORtg),
but [Home Team]'s defense has been suffocating opponents, holding them to
just [X] points per game at home. This is a classic strength vs. strength
matchup that could go either way.

**Injury Impact:** [Player] being out hurts the [Team]'s spacing, as they'll
miss his 18.5 PPG and floor-stretching ability. Look for [Other Player] to
see increased usage.

**The Angle:** [Team] is 7-2 ATS as home favorites this season, and the sharp
money has been hammering them early. The line moved from -3 to -5 since open.

**The Verdict:** This feels like a grind-it-out game that stays Under the total.
The pace will be slow, and both defenses are clicking.
```

**SPORTS PAGES ARE NOT:**
- ❌ Just a list of stats (that's what the Handicapping Hub is for)
- ❌ Robotic or template-sounding content
- ❌ Generic analysis that could apply to any game

---

### BLOG POSTS (blog-pageX.html)
**Purpose:** Official picks with specific recommendations

Blog posts contain:
- ❌ Picks or predictions
- ❌ "Take [Team]" language
- ❌ "I'm betting..." or "My pick is..."
- ❌ Verdict sections
- ❌ Explicit gambling recommendations

**BLOG POSTS (blog-page*.html):**

These pages ARE for picks. They contain:
- ✅ Everything from sports pages PLUS
- ✅ Explicit picks with lines (e.g., "Lakers -4.5")
- ✅ Verdict sections with final pick
- ✅ "Take [Team]" language
- ✅ Conviction and gambling recommendations

### SPORTS PAGE WRITING STYLE

**DO write like this:**
"The matchup favors Denver's elite offense against Indiana's struggling defense. The efficiency gap of +7.1 points per 100 possessions is significant. Denver's 8-3 ATS record as road favorites and the OVER hitting in 11 of 19 games creates an interesting narrative for bettors to consider."

**DON'T write like this:**
"Take Denver here. The Nuggets are the play tonight. I'm betting the Nuggets -6.5."

### TONE FOR SPORTS PAGES

- Present data and let readers draw conclusions
- Use analytical, informative language
- Be enthusiastic about the matchups and stats
- Sound human and conversational, not robotic
- Provide context and insights without explicit picks
- Phrases like "creates value," "interesting spot," "worth monitoring" are acceptable
- Phrases like "my pick," "take this," "bet this" are NOT acceptable

---

## 2. CONTENT STYLE

### Writing Tone - CRITICAL
- ALWAYS extremely human sounding, analytical, conversational style
- Write like an ENTHUSIASTIC, EMOTIONAL, PASSIONATE human journalist
- NEVER robotic, AI-sounding, or formulaic writing
- Write like a knowledgeable friend who is fired up about their analysis
- Use contractions naturally - "don't" not "do not", "it's" not "it is", "you're" not "you are"
- Be opinionated and take strong stances - show personality and passion
- Use casual transitions - "Look", "Here's the thing", "Let me tell you", "And get this", "Listen"
- Vary sentence structure - mix short punchy sentences with longer analytical ones
- Show emotion and conviction - "This is huge", "I love this spot", "This line is a gift", "This excites me"
- Express enthusiasm and excitement naturally throughout the writing
- NEVER use corporate speak, formal language, or academic tone
- No fluff, no filler - every sentence should add value
- NEVER use bold words in content paragraphs
- NEVER use dashes or bullet points in content (write in flowing paragraphs)
- NEVER reference other websites or external sources

### Content Structure
- Clear sections with gold-colored headers (span style with color gold, font-weight 700, font-size 22px)
- Short paragraphs - 3-5 sentences max per paragraph
- No bold words within content paragraphs
- No plagiarism - Original content only, rewrite everything in your own words
- Write in flowing paragraph format, no lists or bullet points in content

### Writing Style Examples

GOOD - Passionate, human, conversational:
"Look, I get it. Nobody likes laying -195. It feels expensive, and when you run the numbers you see that you need the Dodgers to win 66% of the time just to break even. But here's the reality: sometimes you just have to pay for quality. And that's exactly what we're getting tonight."

BAD - Robotic, AI-sounding, formulaic:
"The Los Angeles Dodgers present a compelling betting opportunity despite the high juice of -195. Analysis indicates that the implied probability may be undervalued. Several factors support this thesis."

GOOD - Emotional and analytical:
"This is the kind of spot that gets me fired up. You've got a dominant pitcher going against a lineup that can't hit breaking balls, and you're getting TWO POINTS as an underdog. Are you kidding me? This is a gift."

BAD - Dry and corporate:
"The statistical analysis suggests a favorable matchup. The underdog status provides additional value. Bettors should consider this opportunity."

---

## 3. FORMATTING REQUIREMENTS

### Every Post MUST Include:

#### A. Post Header
```html
<div class="post-header" style="text-align: center;">[TITLE]</div>
```

#### B. Timestamp
```html
<div class="post-time" style="text-align: center;">Posted: [TIME], [DATE]</div>
```
- Format: `12:51 PM, October 27, 2025`
- Get current date/time automatically using: `date '+%-I:%M %p, %B %d, %Y'`
- Always use real-time timestamp unless user specifies otherwise

#### C. Featured Image
```html
<figure style="margin: 20px auto; max-width: 1140px;">
<img alt="[Descriptive alt text]" loading="lazy" src="images/[IMAGE].png" style="display:block; margin: 0 auto; width:85%; border-radius: 8px;"/>
</figure>
```
- Image must be placed AFTER timestamp, BEFORE first paragraph
- Alt text must be descriptive for SEO
- Image file must be in `/images/` folder

#### D. Verdict Section (Blog Posts Only)
```html
<div class="verdict">
<p class="verdict-title">The Pick</p>
<p class="the-pick">[TEAM] [LINE]</p>
</div>
```
- Place at the END of every betting pick post
- Clear, bold display of the final pick

---

## 3. IMAGE REQUIREMENTS

### Image Sourcing
- User will provide image filename (e.g., `1027a.png`, `1027b.png`)
- Images must be copied to `/images/` folder if not already there
- Use relative path: `images/[filename].png`

### Image Placement
- Always AFTER timestamp
- Always BEFORE first paragraph of content
- Wrapped in `<figure>` tag for proper spacing

---

## 4. SEO OPTIMIZATION REQUIREMENTS

### CRITICAL: Every Post MUST Include SEO Meta Tags

#### A. Per-Post Meta Tags (Inside blog-post div)
Every single post MUST include these meta tags immediately after the opening `<div class="blog-post">` tag:

```html
<div class="blog-post" id="post-[DATE]-[SLUG]">
<meta name="title" content="[SEO-OPTIMIZED TITLE WITH KEYWORDS]"/>
<meta name="description" content="[145-160 character meta description with keywords and value proposition]"/>
```

**Meta Title Requirements:**
- 50-60 characters optimal length
- Include primary keywords: team names, bet type, sport, date/context
- Format: `[Team] [Line] [Sport] [Context] - [Value Proposition]`
- Example: `"New York Islanders +1.5 at -195 NHL Betting Pick - November 10 Analysis"`
- Include betting terms: "betting pick", "analysis", "prediction", "odds"

**Meta Description Requirements:**
- 145-160 characters optimal length (strict limit for Google display)
- Include: main pick, odds, 2-3 key analysis points
- Call to action or value statement
- Example: `"Expert NHL betting pick for Islanders +1.5 at -195. Detailed analysis on goalie matchup, team form, special teams, defensive structure, and why the puck line offers value today."`

#### B. Primary Keywords to Target

**Every post should naturally incorporate:**
- Sport name (NFL, NBA, NHL, MLB, etc.)
- Team names (full names, not just city)
- Bet type (spread, moneyline, over/under, puck line, etc.)
- Odds (exact numbers with minus/plus signs)
- Date context (today, Week 10, November 10, etc.)
- Analysis terms (betting analysis, expert pick, prediction, odds analysis)
- Results terms (betting insights, picks and analysis, sports betting)

**Keyword Density Guidelines:**
- Primary keyword phrase: 2-3% density
- Secondary keywords: 1-2% density each
- Natural placement - NEVER stuff keywords awkwardly
- Use variations and synonyms

#### C. Post ID Slug Format
```html
id="post-[YYYYMMDD]-[team-sport-context-slug]"
```
Examples:
- `id="post-20251110-islanders-puck-line-pick"`
- `id="post-20251109-bucs-patriots-spread-pick"`
- `id="post-20251108-falcons-colts-berlin"`

**Slug Requirements:**
- All lowercase
- Hyphens between words (no underscores)
- Include key identifiers: team, sport/league, or key context
- Keep under 50 characters
- Make it descriptive and SEO-friendly

#### D. Image Alt Text SEO
Every image MUST have descriptive, keyword-rich alt text:

**Format:**
```
[Team Names] [Sport/League] [content type] [bet type/context] [date]
```

**Examples:**
- `"New York Islanders NHL betting pick puck line analysis November 10 2025"`
- `"Tampa Bay Buccaneers New England Patriots NFL Week 10 betting pick analysis spread prediction"`
- `"Los Angeles Dodgers MLB World Series betting analysis moneyline odds"`

**Alt Text Requirements:**
- 120-150 characters optimal
- Include team names, sport, bet type, date
- Natural sentence structure (not comma-separated keywords)
- Descriptive of actual image content

#### E. Header Keyword Optimization

**Post Header (Title):**
- Include primary keyword phrase
- Format varies by post type:
  - Betting picks: `[Team] [Line] - [Context/Hook]`
  - News: `[Event/Player] - [Key Detail]`
- Examples:
  - `"New York Islanders +1.5 at -195"` (concise)
  - `"Tampa Bay Buccaneers -2.5 vs New England Patriots - NFL Week 10 Betting Pick"` (detailed)

**Section Headers (gold headers):**
- Use semantic HTML structure (even though styled with spans)
- Include related keywords naturally
- Examples:
  - "Why Tampa Bay Covers"
  - "The Maye Factor and How Tampa Bay Defends It"
  - "Home Field Advantage and the Spread"

#### F. Content SEO Best Practices

**Keyword Placement Priority:**
1. Post title (highest weight)
2. Meta description
3. First paragraph (critical)
4. Image alt text
5. Section headers
6. Throughout body naturally
7. Final pick line

**First Paragraph Requirements:**
- Include primary keyword phrase in first 100 words
- Include the exact bet and odds
- Set context for SEO (team names, sport, situation)
- Example: "The New York Islanders have quietly put together one of the more defensively structured teams in the Eastern Conference this season, and today's puck line at +1.5 for -195 offers solid value..."

**Internal Linking Opportunities:**
- Link to relevant past picks when appropriate
- Link to records pages
- Link to related analysis
- Use descriptive anchor text with keywords

### Content Length for SEO
- Blog posts (picks): Minimum 1500 words, optimal 2000-2500 words
- News articles: Minimum 500 words, optimal 700-1000 words
- Longer content ranks better - be comprehensive
- Break up long content with section headers

### Semantic Keywords & LSI Terms

Include related terms naturally:
- Betting: "wager", "bet", "value", "edge", "line", "odds", "juice"
- Analysis: "breakdown", "deep dive", "insight", "angle", "matchup"
- Teams: Include conference, division, record when relevant
- Sports: Include league names, season context, week numbers

---

## 5. POSTING LOCATIONS

### Blog Posts (Picks/Analysis)
- Add to **blog-page10.html** (current picks page)
- Place NEW post at the TOP, above existing posts
- Never delete old posts - they stay on the page
- **When page gets too large**: Create a new page (e.g., blog-page11.html), update pagination, and update ALL site navigation links

### News Articles
- Add to **news-page3.html** (current news page)
- Place NEW article at the TOP, above existing articles
- Wrap in news-post div with gold border styling

### Featured Game of the Day
- Add to **featured-game-of-the-day-page17.html** (current page - December 11, 2025)
- **IMPORTANT**: Every time you add a new Featured Game of the Day post, you MUST:
  1. Create a NEW page (increment the page number)
  2. Update the OLD page's pagination to link to the new page
  3. **⚠️ CRITICAL: Update ALL site navigation links to point to the new page (see 1D below)**
  4. The new page becomes the "newest" page in the pagination

### ⛔ FEATURED GAME OF THE DAY - NO PICKS RULE ⛔

**CRITICAL: Featured Game of the Day pages are ANALYSIS and STATS ONLY. NO PICKS.**

**These pages MUST NOT include:**
- ❌ "BetLegend's Pick" or any pick section
- ❌ "The Verdict" with a specific pick
- ❌ "Take [Team]" language
- ❌ Any explicit betting recommendation
- ❌ "My pick is..." or similar

**These pages MUST include:**
- ✅ Team logos next to team names (use ESPN CDN: https://a.espncdn.com/i/teamlogos/nfl/500/[abbrev].png)
- ✅ Deep statistical analysis with verified numbers
- ✅ Injury reports (verified current status)
- ✅ Betting lines (spread, total, moneyline)
- ✅ Key matchup breakdowns
- ✅ ATS trends and betting trends (with specific numbers)
- ✅ "Final Thoughts" section analyzing the matchup (no picks)
- ✅ "Keys To Victory" for both teams

**Purpose:** Featured Game pages are DATA and ANALYSIS resources for bettors to make their own decisions. They are NOT for giving explicit picks.

---

## 1D. MANDATORY DAILY FEATURED GAME LINK UPDATE

### ⚠️ CRITICAL: EVERY PAGE ON THE SITE MUST LINK TO THE CURRENT FEATURED GAME ⚠️

**EFFECTIVE DECEMBER 8, 2025 - MANDATORY DAILY TASK**

When a new Featured Game of the Day is posted, ALL links across the ENTIRE site must be updated to point to the new page. This includes:
- Every sport page (nba.html, nfl.html, nhl.html, ncaab.html, etc.)
- Every archive page (nba-page2.html, nfl-page3.html, etc.)
- Every navigation dropdown on every page
- Every featured game archive page itself

### WHY THIS MATTERS
- Broken or outdated links destroy user experience
- Users clicking "Featured Game" should ALWAYS see TODAY's featured game
- Old links (e.g., page12 when page15 is current) make the site look unmaintained
- **This happened December 8, 2025: Links pointed to Detroit vs Dallas (Dec 4) instead of Eagles vs Chargers (Dec 8)**

### DAILY UPDATE PROCESS

**Every time a new Featured Game of the Day is created:**

1. **Note the new page number** (e.g., `featured-game-of-the-day-page16.html`)

2. **Run a batch update script** to replace ALL old links:
   ```python
   import os, re
   REPO_PATH = r'C:\Users\Nima\nimadamus.github.io'
   NEW_PAGE = 'featured-game-of-the-day-page16.html'  # Update this number

   for root, dirs, files in os.walk(REPO_PATH):
       dirs[:] = [d for d in dirs if d != '.git']  # Skip .git
       for f in files:
           if f.endswith('.html'):
               path = os.path.join(root, f)
               with open(path, 'r', encoding='utf-8', errors='ignore') as file:
                   content = file.read()
               original = content
               content = re.sub(r'featured-game-of-the-day-page\d+\.html', NEW_PAGE, content)
               content = re.sub(r'featured-game-of-the-day\.html', NEW_PAGE, content)
               if content != original:
                   with open(path, 'w', encoding='utf-8') as file:
                       file.write(content)
                   print(f'Fixed: {f}')
   ```

3. **Commit and push** the changes immediately

4. **Verify** by clicking the Featured Game link on the live site

### AUTOMATION REMINDER

This update MUST happen EVERY TIME a new Featured Game is posted. Add this to the end-of-day checklist:

- [ ] New Featured Game created
- [ ] ALL site links updated to point to new page
- [ ] Changes committed and pushed
- [ ] Live site verified

### Pagination Update Process (For ALL Paginated Sections)
When creating a new page for any section (blog, featured game, etc.):
1. Create the new page with the next page number
2. Update the previous page's pagination:
   - Change "← Next" from disabled to linking to the new page
   - Update the page number display
3. Run a site-wide update to change ALL navigation links to point to the new page
4. Verify all links work before pushing

---

## 6. POST TYPES & TEMPLATES

### Type A: Betting Pick (Blog Post)
**Required Elements:**
1. Title explaining the pick
2. Timestamp
3. Featured image
4. Introduction paragraph explaining why this pick
5. Multiple analysis sections with gold headers
6. Stats, trends, matchup analysis
7. Verdict section with final pick

**Example Structure:**
```
Title: "LA Dodgers ML -195: Sometimes You Just Have to Pay the Price for Quality"
Timestamp: 12:51 PM, October 27, 2025
Image: 1027b.png
Content:
  - Introduction (why this pick)
  - Pitching matchup analysis
  - Offense analysis
  - Home field advantage
  - Bullpen comparison
  - Line movement discussion
  - Risk management
Verdict: Dodgers ML -195
```

### Type B: News Article
**Required Elements:**
1. News headline
2. Timestamp
3. Featured image
4. Lead paragraph (who, what, when, where)
5. Background/context
6. Analysis/implications
7. Quotes if available
8. Conclusion

**Example Structure:**
```
Title: "NFL Legend Adrian Peterson Arrested on DWI, Weapon Charges"
Timestamp: 11:45 AM, October 27, 2025
Image: 1027a.png
Content:
  - Breaking news lead
  - Details of arrest
  - Previous incidents/context
  - Career background
  - Legal implications
  - What's next
```

---

## 7. COMMIT & DEPLOY PROCESS

### Git Workflow
After creating/editing post:
```bash
cd "C:\Users\Nima\Desktop\betlegendpicks"
git add [filename].html
git commit -m "[Brief description of post]"
git push
```

### Commit Message Format
- Blog posts: `"Add [TEAM] [LINE] pick to blog-page8"`
- News posts: `"Add [HEADLINE] to news-page3"`
- Example: `"Add LA Dodgers ML -195 pick to blog-page8"`

---

## 8. QUALITY CHECKLIST

Before pushing ANY post, verify:

### Content Quality
- [ ] Human-written tone (no AI language)
- [ ] Timestamp included with current date/time
- [ ] Verdict section included (blog posts only)
- [ ] No plagiarism - original content
- [ ] Proper HTML formatting
- [ ] Post placed at TOP of page
- [ ] Gold section headers used
- [ ] Conversational, opinionated writing
- [ ] Minimum word count met (1500+ for blog, 500+ for news)

### SEO Optimization
- [ ] Meta title tag included (50-60 chars, keyword-rich)
- [ ] Meta description tag included (145-160 chars)
- [ ] Post ID slug is SEO-friendly and descriptive
- [ ] Image alt text is descriptive and keyword-rich
- [ ] Primary keywords in first paragraph
- [ ] Keywords naturally distributed throughout
- [ ] Section headers include relevant keywords
- [ ] Image filename is SEO-optimized (not generic)

### Image Requirements
- [ ] Featured image added with proper alt text
- [ ] Image file exists in `/images/` folder
- [ ] Image filename is SEO-optimized (descriptive, not generic like "1110.png")
- [ ] Image properly sized and compressed

### Technical
- [ ] Git committed with clear message
- [ ] Changes pushed to live site
- [ ] Live site verified after deployment

---

## 9. COMMON MISTAKES TO AVOID

❌ **DON'T:**
- Use robotic, AI-sounding language
- Forget to add timestamp
- Place image in wrong location
- Forget verdict section on picks
- Use generic alt text
- Add post to bottom of page
- Use overly formal language
- Write short, thin content

✅ **DO:**
- Write conversationally
- Include all required elements
- Place new posts at TOP
- Use descriptive alt text
- Show personality and opinions
- Provide detailed analysis
- Commit and push immediately

---

## 10. EMERGENCY OVERRIDES

If user provides conflicting instructions, ALWAYS:
1. Confirm with user which protocol to follow
2. Document the exception
3. Return to standard protocol for next post

---

## PROTOCOL VERSION
Version: 1.0
Last Updated: October 27, 2025
Created by: Claude Code for BetLegend

---

**This protocol is MANDATORY for all future posts. No exceptions unless explicitly stated by user.**
