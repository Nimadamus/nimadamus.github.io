# CLAUDE.md - MANDATORY INSTRUCTIONS FOR EVERY SESSION

## CRITICAL: READ BEFORE DOING ANYTHING

**This file is automatically loaded at the start of every Claude Code session in this repository.**

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
- **Featured Game of the Day**: featured-game-of-the-day-page15.html (current - Dec 8, 2025)
- **Moneyline Parlay**: moneyline-parlay-of-the-day.html

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

3. Push changes immediately
4. Verify on live site

**DO NOT skip this step. On Dec 8, 2025, users saw a 4-day-old game because links weren't updated.**

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
