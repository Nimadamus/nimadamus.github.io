# BetLegend Posting Protocol

## MANDATORY REQUIREMENTS FOR ALL POSTS

This protocol MUST be followed for every blog post and news article uploaded to betlegendpicks.com.

---

## 1. ACCURACY & VERIFICATION

### CRITICAL RULE: 100% ACCURACY REQUIRED
- Every piece of information posted MUST be 100% accurate and verified
- Do NOT make up stats, scores, or facts
- Do NOT fabricate player names, team records, or game details
- If information cannot be verified, ASK USER for details
- When in doubt, leave out specific numbers and use general statements

### Verification Sources
- User-provided information is considered verified
- Ask user to confirm any stats, records, or specific details before posting
- If writing about real games/players, verify accuracy before posting

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

## 4. SEO REQUIREMENTS

### Alt Text
- Every image MUST have descriptive alt text
- Include: sport, teams, type of content, date
- Example: `"LA Dodgers MLB betting analysis October 27 2025"`

### Content Length
- Blog posts: Minimum 1500 words
- News articles: Minimum 500 words
- Break up long content with section headers

---

## 5. POSTING LOCATIONS

### Blog Posts (Picks/Analysis)
- Add to **blog-page8.html** (current picks page)
- Place NEW post at the TOP, above existing posts
- Never delete old posts - they stay on the page

### News Articles
- Add to **news-page3.html** (current news page)
- Place NEW article at the TOP, above existing articles
- Wrap in news-post div with gold border styling

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

- [ ] Human-written tone (no AI language)
- [ ] Timestamp included with current date/time
- [ ] Featured image added with proper alt text
- [ ] Image file exists in `/images/` folder
- [ ] Verdict section included (blog posts only)
- [ ] No plagiarism - original content
- [ ] Proper HTML formatting
- [ ] Post placed at TOP of page
- [ ] Gold section headers used
- [ ] Conversational, opinionated writing
- [ ] Git committed with clear message
- [ ] Changes pushed to live site

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
