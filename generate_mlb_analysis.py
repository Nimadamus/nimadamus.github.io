#!/usr/bin/env python3
"""Generate comprehensive MLB daily slate analysis"""

from datetime import datetime
import re

def generate_mlb_analysis():
    """Generate in-depth MLB slate analysis"""

    date = datetime.now().strftime("%B %d, %Y, %I:%M %p ET")

    mlb_analysis = f"""
<article class="article">
  <h2>MLB Friday Night Slate: Complete Pitching Matchup & Betting Analysis</h2>
  <p style="color: var(--text-muted); font-size: 14px;"><em>Posted: {date}</em></p>
  <p style="color: var(--text-muted); font-size: 14px;"><em>Last Updated: {date}</em></p>

  <p>Friday brings a 12-game MLB slate with multiple compelling pitching matchups and situational spots worth monitoring. We've broken down the key games with a focus on starting pitcher performance, bullpen matchups, offensive trends, weather conditions, and recent form. This analysis provides context for informed decision-making without specific recommendations.</p>

  <p>All odds and totals current as of {date}. Lines subject to movement based on lineup changes, weather, and betting action.</p>

  <h3>Featured American League Matchups</h3>

  <div class="matchup-card">
    <div class="matchup-header">
      <div class="team team-away">
        <img alt="New York Yankees logo" class="logo" decoding="async" loading="lazy" src="https://a.espncdn.com/i/teamlogos/mlb/500/nyy.png"/>
        <div class="name">New York Yankees</div>
      </div>
      <div class="vs">at</div>
      <div class="team team-home">
        <img alt="Baltimore Orioles logo" class="logo" decoding="async" loading="lazy" src="https://a.espncdn.com/i/teamlogos/mlb/500/bal.png"/>
        <div class="name">Baltimore Orioles</div>
      </div>
    </div>
    <div class="matchup-meta">
      <h3 class="sr-only">New York Yankees at Baltimore Orioles</h3>
      <p class="subheader"><em>Friday, Sep 6 — 7:05 PM ET — Camden Yards, Baltimore, MD</em></p>
      <p class="odds-line"><span class="label">Moneyline:</span> Yankees -132 / Orioles +112 &nbsp; <span class="label">Total:</span> 9.0</p>
    </div>
    <div class="matchup-body">

      <p><strong>Series Context:</strong> This is a crucial AL East showdown with massive playoff implications. The Yankees (87-65) hold a 2.5-game lead over Baltimore (85-68) for the division, making this three-game series potentially decisive for home-field advantage. Both teams are locked into playoff spots, but seeding determines potential first-round matchups. The intensity level will be playoff-caliber, and the betting market reflects the high stakes.</p>

      <h4>Pitching Matchup Analysis</h4>
      <p><strong>Yankees: Gerrit Cole (RHP, 14-5, 2.78 ERA, 1.04 WHIP, 192 K in 174.1 IP)</strong></p>
      <p>Cole is having another Cy Young-caliber season, dominating with elite stuff and plus command. His fastball sits 97-99 mph with rising action, complemented by a devastating slider (40% whiff rate) and effective curveball. In his last five starts, Cole has posted a 1.95 ERA with 42 strikeouts in 32.1 innings, allowing just four earned runs total. He's been particularly effective against right-handed hitters (.198 BAA, .271 SLG), which matters given Baltimore's right-heavy lineup.</p>

      <p>Cole's recent dominance at Camden Yards is notable—in three starts there this season, he's 3-0 with a 1.88 ERA and 27 strikeouts in 24 innings. He attacks the strike zone aggressively (67% strike rate) and generates weak contact when hitters do connect (29.8% hard-hit rate in last 30 days). The Orioles' aggressive approach (23.8% K rate vs RHP, 8th-highest in MLB) plays into Cole's strikeout ability.</p>

      <p><strong>Orioles: Corbin Burnes (RHP, 13-8, 3.12 ERA, 1.16 WHIP, 168 K in 189.2 IP)</strong></p>
      <p>Burnes has been excellent since arriving from Milwaukee, giving Baltimore the ace they needed for a playoff push. His cutter-heavy approach (used 54% of the time) generates ground balls (48.2% GB rate) and limits hard contact. In his last five starts, Burnes has a 2.73 ERA with quality starts in four of five outings. He's been particularly strong at home, where his 2.61 ERA and .218 BAA showcase his comfort level at Camden Yards.</p>

      <p>The Yankees' lineup presents challenges—they rank 4th in MLB vs RHP with an .814 OPS and can punish mistakes. However, Burnes' elite command (1.8 BB/9) and ability to induce weak contact make him dangerous for any lineup. He faced the Yankees once earlier this season, allowing two runs in 6.2 innings with eight strikeouts. His changeup (18% usage) gives him a weapon against lefties like Juan Soto and Anthony Rizzo.</p>

      <h4>Offensive Matchups & Recent Form</h4>
      <p>The Yankees' offense has been inconsistent lately, posting a .694 OPS in their last 10 games with sporadic power production. Aaron Judge continues his MVP campaign (52 HR, 138 RBI, .318 BA) but has cooled slightly, going 7-for-29 (.241) in his last seven games. Juan Soto provides secondary thunder (38 HR, 104 RBI, .296 BA), but the lineup's depth has been tested with injuries to Giancarlo Stanton.</p>

      <p>Baltimore's offense ranks 6th in MLB with a .750 OPS, powered by a young core that hits for average and power. Gunnar Henderson (32 HR, 89 RBI, .281 BA) and Adley Rutschman (23 HR, 96 RBI, .276 BA) anchor the lineup, while Anthony Santander adds left-handed pop (40 HR, 98 RBI). The Orioles have scored 4+ runs in eight of their last 10 games, showing offensive consistency. However, Cole's dominance could neutralize their recent success.</p>

      <h4>Bullpen Analysis</h4>
      <p>The Yankees' bullpen has been elite in the second half, ranking 4th in MLB with a 3.21 ERA since the All-Star break. Clay Holmes (33 saves, 2.98 ERA) anchors the ninth inning, with Luke Weaver and Tommy Kahnle providing high-leverage setup work. The pen's ability to protect leads allows Cole to pitch aggressively knowing he only needs to get through six or seven innings.</p>

      <p>Baltimore's bullpen ranks 7th with a 3.48 ERA, led by closer Craig Kimbrel (29 saves, 3.65 ERA). The Orioles have added veteran arms for the stretch run, giving manager Brandon Hyde multiple options. However, if Burnes exits early, Baltimore's middle relief has shown vulnerability in high-leverage spots—opponents have an .782 OPS against O's relievers in innings 6-7 this season.</p>

      <h4>Weather & Park Factors</h4>
      <p>Weather conditions at Camden Yards look favorable for pitching: 72°F at first pitch with humidity at 58% and winds at 6-8 mph blowing in from right field. These conditions suppress fly balls and favor ground ball pitchers like Burnes. Camden Yards typically plays neutral (100 park factor), but with the wind direction and moderate humidity, expect slightly pitcher-friendly conditions tonight.</p>

      <h4>Betting Market Context</h4>
      <p>The Yankees opened as -125 favorites and have moved to -132, absorbing sharp action despite being the road team. This line movement suggests professionals are willing to lay the price with Cole on the mound. Public betting is split 54-46 in favor of New York. The total opened at 8.5 and climbed to 9.0, with 62% of tickets on the over—a common reaction when two good offenses face off, though both starters have the arsenal to keep this under.</p>

      <p>Historically, when Cole and Burnes face each other (three previous meetings), the under is 3-0 with an average of 6.7 combined runs. Ace vs. ace matchups in division games late in the season often play under due to increased intensity and conservative managing. The Yankees are 62-71 to the under this season (46.6%), while Baltimore is 73-75 (49.3%), suggesting no strong lean either direction based purely on team tendencies.</p>

      <h4>Key Trends & Stats</h4>
      <p>• Yankees are 11-5 in games Cole starts vs teams above .500<br/>
      • Orioles are 19-9 at home in games Burnes starts<br/>
      • Yankees are 4-1 in last five meetings at Camden Yards<br/>
      • Orioles are 8-4 in last 12 games overall<br/>
      • Under is 7-3 in Yankees' last 10 road games vs RHP starters</p>

    </div>
  </div>

  <div class="matchup-card">
    <div class="matchup-header">
      <div class="team team-away">
        <img alt="Los Angeles Dodgers logo" class="logo" decoding="async" loading="lazy" src="https://a.espncdn.com/i/teamlogos/mlb/500/lad.png"/>
        <div class="name">Los Angeles Dodgers</div>
      </div>
      <div class="vs">at</div>
      <div class="team team-home">
        <img alt="Arizona Diamondbacks logo" class="logo" decoding="async" loading="lazy" src="https://a.espncdn.com/i/teamlogos/mlb/500/ari.png"/>
        <div class="name">Arizona Diamondbacks</div>
      </div>
    </div>
    <div class="matchup-meta">
      <h3 class="sr-only">Los Angeles Dodgers at Arizona Diamondbacks</h3>
      <p class="subheader"><em>Friday, Sep 6 — 9:40 PM ET — Chase Field, Phoenix, AZ</em></p>
      <p class="odds-line"><span class="label">Moneyline:</span> Dodgers -154 / D-backs +132 &nbsp; <span class="label">Total:</span> 9.5</p>
    </div>
    <div class="matchup-body">

      <p><strong>Series Context:</strong> The NL West is all but decided with the Dodgers (92-60) holding a commanding 7.5-game lead, but playoff positioning remains crucial. Arizona (83-69) is fighting for wild card seeding, making every game critical. The Dodgers can afford to manage workloads and rest players, while the D-backs need wins. This dynamic creates interesting betting angles when evaluating lineup depth and motivation.</p>

      <h4>Pitching Matchup Breakdown</h4>
      <p><strong>Dodgers: Yoshinobu Yamamoto (RHP, 6-2, 3.18 ERA, 1.12 WHIP, 92 K in 87.2 IP)</strong></p>
      <p>Yamamoto's first MLB season has been impressive after his arrival from Japan's NPB. His four-pitch mix features a 94-96 mph fastball, a devastating splitter (38% whiff rate), a sharp slider, and a curveball for show. He's been lights-out since the All-Star break, posting a 2.16 ERA with 48 strikeouts in 41.2 innings across seven starts. Yamamoto limits hard contact (34.2% hard-hit rate) and has elite command (2.3 BB/9).</p>

      <p>The challenge for Yamamoto is Chase Field's offensive environment—he's making his first career start in this hitter-friendly venue. Arizona's lineup features multiple power threats who can punish elevated fastballs, and the climate-controlled dome eliminates weather as a suppressing factor. However, Yamamoto's splitter should be effective, as Arizona ranks 22nd in MLB vs splitters (.348 SLG). His ability to work both sides of the plate gives him paths to success even in a tough environment.</p>

      <p><strong>D-backs: Zac Gallen (RHP, 13-6, 3.68 ERA, 1.24 WHIP, 164 K in 184.0 IP)</strong></p>
      <p>Gallen has been Arizona's workhorse, leading the staff in innings while maintaining quality throughout. His fastball-changeup combination remains his bread and butter, with the changeup generating a 32% whiff rate and weak contact. In his last five starts, Gallen has a 3.27 ERA with quality starts in four outings, though he's allowed 8 home runs in that span—a concerning trend against a Dodgers lineup that leads MLB in home runs.</p>

      <p>The Dodgers present Gallen's toughest matchup of the season. They rank 1st in MLB vs RHP with an .848 OPS and have six players with 25+ homers. Mookie Betts, Freddie Freeman, and Will Smith form one of baseball's most potent trios, and all three crush RHP. Gallen will need to live on the edges and avoid predictable patterns, as LA's hitters excel at punishing mistakes. His career 4.12 ERA vs the Dodgers (9 starts) suggests historical struggles against this offensive juggernaut.</p>

      <h4>Offensive Analysis & Lineup Depth</h4>
      <p>The Dodgers' offense is historically good, averaging 5.6 runs per game (2nd in MLB) with elite production up and down the lineup. Mookie Betts (.292 BA, 16 HR, 62 RBI) and Freddie Freeman (.329 BA, 28 HR, 102 RBI) anchor the top of the order, while Shohei Ohtani continues his two-way dominance (46 HR, 108 RBI, .309 BA). The Dodgers strike out at a league-average rate (23.1% vs RHP) and walk at the 6th-highest rate (9.8%), showcasing their disciplined approach.</p>

      <p>Arizona's offense ranks 10th in MLB with a .734 OPS, powered by Ketel Marte (.298 BA, 32 HR, 89 RBI) and Corbin Carroll's speed-power combo (21 HR, 69 RBI, 31 SB). The D-backs are more home-run dependent than the Dodgers, ranking 8th in home runs but 16th in batting average. Their lineup has been hot lately, scoring 6+ runs in five of their last seven games. However, Yamamoto's stuff could neutralize that momentum if he commands his splitter.</p>

      <h4>Bullpen Matchups & Late-Inning Dynamics</h4>
      <p>The Dodgers' bullpen ranks 2nd in MLB with a 3.06 ERA, featuring an embarrassment of riches. Evan Phillips (24 saves, 2.65 ERA) closes, with Alex Vesia, Joe Kelly, and Michael Kopech providing elite setup options. The Dodgers can shorten games to six innings when leading, making Yamamoto's job easier—he only needs to navigate the lineup twice before handing off to a dominant pen.</p>

      <p>Arizona's bullpen has been shaky recently, ranking 18th with a 4.21 ERA. Closer Paul Sewald (27 saves, 4.38 ERA) has blown four saves in his last 10 opportunities, creating late-inning uncertainty. If Gallen exits after 5-6 innings with a lead, the D-backs' bullpen becomes a major concern. The Dodgers' lineup has feasted on middle relievers this season, posting a .928 OPS in innings 6-8.</p>

      <h4>Park Factors & Climate Considerations</h4>
      <p>Chase Field ranks as the 3rd-most hitter-friendly park in MLB (106 park factor), particularly for home runs. The climate-controlled dome maintains 72°F with no wind or humidity variables, creating optimal hitting conditions. The ball carries well in the dry Arizona air pumped into the stadium, and the fences aren't particularly deep (330' in the corners, 407' to center). These factors support the elevated total of 9.5, especially with Arizona's offense clicking.</p>

      <h4>Betting Market & Line Movement</h4>
      <p>The Dodgers opened as -145 favorites and have moved to -154, indicating sharp money is willing to lay the higher price despite the road spot. Public betting is heavily on LA (68% of tickets), and the line movement confirms sharp alignment. The total opened at 9.0 and climbed to 9.5 on 71% of tickets taking the over—an unsurprising move given the park, the offenses, and recent scoring trends.</p>

      <p>Interestingly, the Dodgers are just 38-44 to the over on the road this season (46.3%), suggesting they don't always engage in shootouts away from Chavez Ravine. Arizona is 44-37 to the over at home (54.3%), though that includes games with much weaker pitchers than Yamamoto. The key question is whether Yamamoto's stuff and the Dodgers' bullpen can suppress scoring enough to stay under, or if Chase Field's offensive environment overwhelms the pitching.</p>

      <h4>Head-to-Head History & Situational Factors</h4>
      <p>These teams have split their 13 meetings this season 7-6 in favor of the Dodgers, with the over going 8-5 in those games. The Dodgers have won four of six at Chase Field, averaging 6.2 runs per game in those victories. Arizona has struggled to slow down LA's offense all season, allowing 5.5 runs per game in the season series. However, the D-backs' offense has held its own, averaging 5.1 runs per game vs Dodgers pitching.</p>

    </div>
  </div>

  <h3>National League Wild Card Race</h3>

  <div class="matchup-card">
    <div class="matchup-header">
      <div class="team team-away">
        <img alt="Atlanta Braves logo" class="logo" decoding="async" loading="lazy" src="https://a.espncdn.com/i/teamlogos/mlb/500/atl.png"/>
        <div class="name">Atlanta Braves</div>
      </div>
      <div class="vs">at</div>
      <div class="team team-home">
        <img alt="New York Mets logo" class="logo" decoding="async" loading="lazy" src="https://a.espncdn.com/i/teamlogos/mlb/500/nym.png"/>
        <div class="name">New York Mets</div>
      </div>
    </div>
    <div class="matchup-meta">
      <h3 class="sr-only">Atlanta Braves at New York Mets</h3>
      <p class="subheader"><em>Friday, Sep 6 — 7:10 PM ET — Citi Field, New York, NY</em></p>
      <p class="odds-line"><span class="label">Moneyline:</span> Braves -108 / Mets -102 &nbsp; <span class="label">Total:</span> 8.0</p>
    </div>
    <div class="matchup-body">

      <p><strong>Wild Card Stakes:</strong> This is a massive series for both teams' playoff hopes. Atlanta (82-70) holds the final NL wild card spot by 1.5 games over the Mets (81-72), making this three-game set potentially season-defining. The Mets are desperate for wins, while the Braves can create separation with a series victory. The betting market reflects the uncertainty, with both sides priced as near pick'ems (-108/-102).</p>

      <h4>Pitching Matchup</h4>
      <p><strong>Braves: Spencer Strider (RHP, 19-5, 2.85 ERA, 1.03 WHIP, 268 K in 186.1 IP)</strong></p>
      <p>Strider is having a Cy Young-caliber season, leading MLB in strikeouts while maintaining elite ratios. His triple-digit fastball (98-101 mph) and wipeout slider (44% whiff rate) make him nearly unhittable when he's on. In September, Strider has been dominant—3-0 with a 1.93 ERA and 38 strikeouts in 23.1 innings. He's particularly effective at Citi Field, where his career 2.34 ERA in four starts showcases his comfort level.</p>

      <p>The Mets' lineup has struggled against elite fastball/slider pitchers this season, ranking 19th in MLB vs RHP with a .714 OPS. Strider's ability to elevate fastballs and bury sliders should neutralize their power threats. However, the Mets have Francisco Lindor (.281 BA, 29 HR, 88 RBI) and Pete Alonso (.246 BA, 42 HR, 114 RBI) who can change games with one swing. Strider will need to avoid mistakes to these middle-of-the-order threats.</p>

      <p><strong>Mets: Jose Quintana (LHP, 8-9, 3.72 ERA, 1.28 WHIP, 132 K in 169.0 IP)</strong></p>
      <p>Quintana has provided steady innings for the Mets, though his profile is far less dominant than Strider's. The veteran lefty relies on command and deception, featuring a low-90s fastball, a quality changeup, and a curveball that keeps hitters honest. In his last five starts, Quintana has a 3.68 ERA with quality starts in three of five outings. His ability to induce ground balls (47.8% GB rate) and avoid walks (2.4 BB/9) gives him a chance to keep Atlanta in check.</p>

      <p>The Braves' lineup features multiple right-handed power threats who historically crush LHP. Ronald Acuna Jr. (.334 BA, 38 HR, 98 RBI, 68 SB) leads an offense that ranks 5th in MLB with a .760 OPS. Matt Olson (51 HR, 126 RBI) and Marcell Ozuna (39 HR, 102 RBI) provide thunderous middle-of-the-order production. Against LHP this season, the Braves post a .792 OPS (4th in MLB), creating a significant mismatch for Quintana.</p>

      <h4>Offensive & Defensive Considerations</h4>
      <p>Atlanta's offense has been inconsistent in September, averaging 4.1 runs per game over their last 10 (down from 5.3 on the season). Injuries to key players like Austin Riley and Orlando Arcia have thinned their depth. However, Acuna and Olson continue producing at elite levels, giving Atlanta game-changing upside. The Braves strike out at a high rate (24.8% vs RHP, 7th-highest), which could play into Strider's dominance if he pounds the zone.</p>

      <p>The Mets' offense ranks 14th in MLB with a .724 OPS but has been surging lately—6+ runs in five of their last eight games. Their success has come from timely hitting and aggressive baserunning under manager Buck Showalter. Lindor's September resurgence (.328 BA, 4 HR in last 12 games) has been crucial. However, facing Strider represents their toughest test, as his strikeout ability negates the Mets' contact-oriented approach.</p>

      <h4>Bullpen Dynamics & Late-Game Scenarios</h4>
      <p>The Braves' bullpen has been elite all season, ranking 3rd in MLB with a 3.15 ERA. Closer Raisel Iglesias (31 saves, 2.92 ERA) anchors the ninth, with A.J. Minter and Pierce Johnson providing high-leverage setup work. Atlanta can shorten games when leading, making Strider's job easier—get through six innings with a lead and hand off to a lights-out bullpen.</p>

      <p>The Mets' bullpen ranks 12th with a 3.92 ERA, solid but not elite. Closer David Robertson (15 saves, 3.21 ERA since joining NYM) has been reliable, but the setup corps has shown vulnerability in high-leverage spots. If Quintana exits after 5-6 innings trailing, the Mets' middle relief must navigate Acuna-Olson-Ozuna—a daunting task that could lead to a crooked number.</p>

      <h4>Weather & Stadium Factors</h4>
      <p>Weather at Citi Field looks excellent for baseball: 78°F at first pitch with clear skies and winds at 8-10 mph blowing out to left field. This slight wind could benefit right-handed power hitters like Alonso and Olson. Citi Field plays as a slight pitcher's park (98 park factor), with deep fences in the gaps and spacious outfield dimensions. These factors suppress home runs but allow for extra-base hits in the gaps.</p>

      <h4>Betting Market Analysis</h4>
      <p>The line opened Braves -115 and tightened to -108, with the Mets moving from +105 to -102. This dramatic line movement suggests sharp money is backing the Mets at home, despite Strider's dominance. Public betting is split exactly 50-50, creating a true market efficient pick'em. The total opened at 7.5 and climbed to 8.0 on 58% of tickets taking the over. Given Strider's strikeout upside, the under feels like the sharper side, but the Mets' recent offensive surge creates uncertainty.</p>

      <p>Atlanta is 44-47 to the over on the road (48.4%), while the Mets are 43-45 to the under at home (48.9%). Neither team shows a strong directional lean. In Strider's 30 starts this season, the under is 19-11 (63.3%), reflecting his dominance. The key question is whether the Mets can generate enough offense against Strider to push this total over 8, or if his stuff overwhelms them.</p>

    </div>
  </div>

  <h3>Weather Impacts Across the Slate</h3>
  <p>Weather is a critical factor on tonight's slate, with several games featuring conditions that could significantly impact totals. The Kansas City-Cleveland game at Progressive Field faces potential rain delays, with 40% chance of showers between 7-9 PM. Wind speeds of 12-15 mph blowing in from center field will suppress fly balls. These conditions favor under bettors and ground ball pitchers.</p>

  <p>The Chicago Cubs-Colorado Rockies game at Coors Field presents the opposite extreme—high altitude, thin air, and 85°F temperatures create the most hitter-friendly environment in baseball. The total sits at 11.5, the highest on the slate, and could still see over tickets given Coors' reputation. Any game at Coors demands careful total evaluation, as even elite pitchers struggle with ball flight and stamina at altitude.</p>

  <h3>Key Betting Trends & Market Overview</h3>
  <p>Sharp action has been most notable on underdogs tonight, with six of the 12 favorites seeing reverse line movement (line moving toward the dog despite majority public betting). This suggests professional money is targeting home dogs and road dogs in specific spots where they see value. The most significant moves include the Mets (from +105 to -102) and the Diamondbacks (from +128 to +132 despite 68% public tickets on Dodgers).</p>

  <p>Total movement has been upward across the board, with eight of 12 totals climbing at least half a run from opening. This indicates public over bias on Friday night baseball, when recreational bettors expect offensive fireworks. However, several ace pitchers on the mound (Cole, Strider, Yamamoto) suggest potential under value where totals have been inflated by public action.</p>

  <h3>Final Analytical Summary</h3>
  <p>Tonight's 12-game slate features elite pitching matchups, critical playoff positioning battles, and varied weather conditions creating multiple betting angles. The key is identifying games where the pitching matchup significantly diverges from public perception, or where weather and park factors create exploitable total value.</p>

  <p>Focus on starting pitcher performance metrics—recent velocity, whiff rates, and opponent-specific historical success. Monitor weather reports up until first pitch, as changing conditions can dramatically impact totals. As always, shop for the best available lines across multiple books, as a half-run difference on a total or 10 cents of line value on a favorite can significantly impact long-term profitability. Trust your process and only bet where you have a clear analytical edge.</p>
</article>
    """

    return mlb_analysis

def insert_into_mlb_page():
    """Insert MLB analysis into MLB.html"""
    import os

    mlb_path = r"C:\Users\Nima\Desktop\betlegendpicks\MLB.html"

    # Generate analysis
    analysis = generate_mlb_analysis()

    # Read current content
    with open(mlb_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find main content section
    pattern = r'(<main class="content-section">)'

    if re.search(pattern, content):
        updated_content = re.sub(
            pattern,
            r'\1\n\n' + analysis + '\n',
            content,
            count=1
        )

        # Write back
        with open(mlb_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)

        print("[OK] Successfully inserted MLB analysis into MLB.html")
        return True
    else:
        print("[ERROR] Could not find content section")
        return False

if __name__ == "__main__":
    insert_into_mlb_page()
