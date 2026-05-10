#!/usr/bin/env python3
"""
BetLegend Daily Slate Analysis Generator
Generates comprehensive, SEO-optimized game analysis for NFL, NBA, MLB
WITHOUT giving picks - just deep analytical content
"""

import os
import re
from datetime import datetime, timedelta
from pathlib import Path

BASE_DIR = r"C:\Users\Nima\Desktop\betlegendpicks"
SITE_URL = "https://www.betlegendpicks.com"

# Analysis templates for different sports
NFL_ANALYSIS_TEMPLATE = """
<article class="article">
  <h2>{title}</h2>
  <p style="color: var(--text-muted); font-size: 14px;"><em>Posted: {date}</em></p>
  <p style="color: var(--text-muted); font-size: 14px;"><em>Last Updated: {last_updated}</em></p>

  {intro_paragraph}

  {game_sections}

  <h3>Key Betting Trends & Market Movement</h3>
  {betting_trends}

  <h3>Weather & Injury Factors</h3>
  {weather_injuries}

  <h3>Historical Context & Advanced Metrics</h3>
  {historical_context}

  <h3>Final Analytical Thoughts</h3>
  {conclusion}
</article>
"""

NBA_ANALYSIS_TEMPLATE = """
<article class="article">
  <h2>{title}</h2>
  <p style="color: var(--text-muted); font-size: 14px;"><em>Posted: {date}</em></p>
  <p style="color: var(--text-muted); font-size: 14px;"><em>Last Updated: {last_updated}</em></p>

  {intro_paragraph}

  {game_sections}

  <h3>Pace & Efficiency Analysis</h3>
  {pace_analysis}

  <h3>Rest Advantages & Schedule Context</h3>
  {rest_analysis}

  <h3>Key Matchup Advantages</h3>
  {matchup_analysis}

  <h3>Betting Market Overview</h3>
  {market_overview}
</article>
"""

GAME_ANALYSIS_STRUCTURE = """
  <div class="matchup-card">
    <div class="matchup-header">
      <div class="team team-away">
        <img alt="{away_team} logo" class="logo" decoding="async" loading="lazy" src="{away_logo}"/>
        <div class="name">{away_team}</div>
      </div>
      <div class="vs">at</div>
      <div class="team team-home">
        <img alt="{home_team} logo" class="logo" decoding="async" loading="lazy" src="{home_logo}"/>
        <div class="name">{home_team}</div>
      </div>
    </div>
    <div class="matchup-meta">
      <h3 class="sr-only">{away_team} at {home_team}</h3>
      <p class="subheader"><em>{game_time} — {venue}</em></p>
      <p class="odds-line"><span class="label">Line:</span> {line} &nbsp; <span class="label">Total:</span> {total}</p>
    </div>
    <div class="matchup-body">
      {analysis_content}
    </div>
  </div>
"""

# SEO-optimized analysis framework
ANALYSIS_COMPONENTS = {
    'team_form': [
        "Recent Performance Analysis (last 5-10 games)",
        "Home/Away splits and trends",
        "Win-loss record against the spread (ATS)",
        "Scoring trends (points per game, defensive efficiency)"
    ],
    'key_stats': [
        "Offensive efficiency metrics",
        "Defensive rankings and vulnerabilities",
        "Turnover differential",
        "Red zone efficiency",
        "Third down conversion rates"
    ],
    'injury_impact': [
        "Injury report breakdown",
        "Impact of key absences on team strategy",
        "Depth chart implications",
        "Historical performance without key players"
    ],
    'matchup_analysis': [
        "Head-to-head historical results",
        "Scheme matchups and advantages",
        "Coaching tendencies in similar situations",
        "Key player matchups to watch"
    ],
    'betting_context': [
        "Line movement and sharp action",
        "Public betting percentages",
        "Historical line value in similar spots",
        "Over/under trends for both teams"
    ]
}

def get_espn_logo_url(league, team_abbreviation):
    """Get ESPN team logo URL"""
    league_code = league.lower()
    return f"https://a.espncdn.com/i/teamlogos/{league_code}/500/{team_abbreviation}.png"

def generate_nfl_slate_analysis(week, games_data):
    """
    Generate comprehensive NFL slate analysis

    games_data format:
    [
        {
            'away_team': 'Kansas City Chiefs',
            'away_abbr': 'kc',
            'away_record': '7-0',
            'home_team': 'Buffalo Bills',
            'home_abbr': 'buf',
            'home_record': '6-2',
            'line': 'Bills -2.5',
            'total': '52.5',
            'game_time': 'Sunday, Nov 10 — 4:25 PM ET',
            'venue': 'Highmark Stadium, Buffalo, NY',
            'analysis': {
                'overview': 'Detailed game overview...',
                'key_stats': 'Key statistical matchups...',
                'trends': 'Betting trends and line movement...',
                'injuries': 'Injury impact analysis...',
                'weather': 'Weather considerations...'
            }
        }
    ]
    """

    title = f"NFL Week {week} Complete Slate Analysis: Every Game Breakdown"
    date = datetime.now().strftime("%B %d, %Y, %I:%M %p ET")
    last_updated = datetime.now().strftime("%B %d, %Y, %I:%M %p ET")

    intro = f"""
  <p>Week {week} brings another full slate of NFL action with {len(games_data)} games spanning across multiple windows. We've analyzed every matchup with a focus on key statistical edges, injury impacts, line movement, and situational spots that could create value. This is pure analytical content—no picks, just the information you need to make informed decisions.</p>

  <p>All odds current as of {date}. Lines and totals subject to movement based on injury news and betting action.</p>
    """

    # Generate game sections
    game_sections_html = []

    for game in games_data:
        away_logo = get_espn_logo_url('nfl', game['away_abbr'])
        home_logo = get_espn_logo_url('nfl', game['home_abbr'])

        analysis_content = f"""
      <p><strong>Overview:</strong> {game['analysis']['overview']}</p>

      <h4>Statistical Matchup</h4>
      <p>{game['analysis']['key_stats']}</p>

      <h4>Recent Form & Trends</h4>
      <p>{game['analysis']['trends']}</p>

      <h4>Injury & Lineup Notes</h4>
      <p>{game['analysis']['injuries']}</p>

      {f"<h4>Weather Conditions</h4><p>{game['analysis']['weather']}</p>" if game['analysis'].get('weather') else ''}

      <h4>Betting Market Context</h4>
      <p>{game['analysis']['betting_context']}</p>
        """

        game_html = GAME_ANALYSIS_STRUCTURE.format(
            away_team=game['away_team'],
            away_logo=away_logo,
            home_team=game['home_team'],
            home_logo=home_logo,
            game_time=game['game_time'],
            venue=game['venue'],
            line=game['line'],
            total=game['total'],
            analysis_content=analysis_content
        )

        game_sections_html.append(game_html)

    game_sections = '\n'.join(game_sections_html)

    # Betting trends section
    betting_trends = """
  <p>Sharp action has been notable on several games this week. Line movement on the marquee matchups suggests professional money is targeting specific spots where the public perception may be overweighting recent results. Keep an eye on reverse line movement—situations where the line moves opposite to public betting percentages often indicate sharp interest.</p>

  <p>The over/under market has been particularly interesting, with several totals moving 2+ points since opening. Weather forecasts for outdoor venues will be crucial for final total evaluations, especially in late-season games where wind and precipitation can significantly impact scoring.</p>
    """

    # Weather and injuries
    weather_injuries = """
  <p>Multiple games feature significant injury questions that will impact how teams approach their game plans. Monitor injury reports up until kickoff, as late scratches can create immediate line movement and value opportunities. Teams playing without key offensive weapons often see their totals adjusted, while defensive injuries can create exploitable matchups.</p>

  <p>Weather conditions vary across the slate, with some outdoor venues facing challenging conditions. Wind speeds above 15 mph historically correlate with lower scoring and increased variance in passing games. Factor these conditions into your total evaluations and player prop considerations.</p>
    """

    # Historical context
    historical_context = """
  <p>Advanced metrics continue to show divergence from win-loss records for several teams. Expected points added (EPA) per play and success rate metrics suggest some teams have been fortunate (or unfortunate) based on turnover luck and close game outcomes. These regression candidates often present value when the market overweights their record.</p>

  <p>Home field advantage remains worth approximately 2-2.5 points in most matchups, though this varies by team. Certain venues (Denver's altitude, Kansas City's noise, Buffalo's weather) provide additional advantages that go beyond the standard adjustment. Divisional matchups historically close the point spread gap by 1-1.5 points compared to non-division games.</p>
    """

    # Conclusion
    conclusion = """
  <p>This week's slate presents multiple angles worth exploring across all betting markets. The key is identifying where the line doesn't accurately reflect the most probable game script or where specific matchup advantages haven't been properly priced in. Focus on games where your analysis diverges significantly from the consensus—those spots typically offer the best risk-reward opportunities.</p>

  <p>As always, line shopping across multiple sportsbooks can provide an additional half-point or better number in key spots. That extra half-point on a side or total can be the difference between a win and a push or loss over a large sample. Stay disciplined with your process, trust your research, and never force action on games where you don't have a clear analytical edge.</p>
    """

    # Build final article
    article_html = NFL_ANALYSIS_TEMPLATE.format(
        title=title,
        date=date,
        last_updated=last_updated,
        intro_paragraph=intro,
        game_sections=game_sections,
        betting_trends=betting_trends,
        weather_injuries=weather_injuries,
        historical_context=historical_context,
        conclusion=conclusion
    )

    return article_html

def insert_analysis_into_page(page_path, new_analysis):
    """Insert new analysis at the top of the content section"""

    with open(page_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find the main content section (after <main class="content-section">)
    pattern = r'(<main class="content-section">)'

    if re.search(pattern, content):
        # Insert after the opening main tag
        updated_content = re.sub(
            pattern,
            r'\1\n\n' + new_analysis + '\n',
            content,
            count=1
        )

        # Write back
        with open(page_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)

        return True
    else:
        print(f"Could not find content section in {page_path}")
        return False

def update_last_updated_date(page_path):
    """Update the 'Last Updated' timestamp on existing articles"""

    with open(page_path, 'r', encoding='utf-8') as f:
        content = f.read()

    current_time = datetime.now().strftime("%B %d, %Y, %I:%M %p ET")

    # Update all "Last Updated" timestamps
    pattern = r'(<em>Last Updated:.*?</em>)'
    updated_content = re.sub(
        pattern,
        f'<em>Last Updated: {current_time}</em>',
        content
    )

    with open(page_path, 'w', encoding='utf-8') as f:
        f.write(updated_content)

    return True

# Example usage function
def generate_example_nfl_analysis():
    """Generate example NFL analysis with realistic data"""

    # Example games data (you would pull this from an API or manual input)
    games_data = [
        {
            'away_team': 'Kansas City Chiefs',
            'away_abbr': 'kc',
            'away_record': '9-1',
            'home_team': 'Buffalo Bills',
            'home_abbr': 'buf',
            'home_record': '8-2',
            'line': 'Bills -2',
            'total': '52.5',
            'game_time': 'Sunday, Nov 17 — 4:25 PM ET',
            'venue': 'Highmark Stadium, Buffalo, NY',
            'analysis': {
                'overview': "This is the heavyweight matchup of Week 11—two legitimate Super Bowl contenders facing off in a potential AFC Championship preview. Kansas City enters 9-1, riding their typical championship pedigree and clutch performances, while Buffalo sits at 8-2 with the league's most explosive offense. The Bills are 2-point favorites at home, which reflects both home field advantage and their recent dominance in this venue. Historically, these teams have produced high-scoring affairs, but both defenses have improved since their last meeting.",

                'key_stats': "Buffalo ranks 1st in points per game (31.2) and 3rd in offensive EPA per play, led by Josh Allen's MVP-caliber season (28 TD, 6 INT, 68.7% completion). The Chiefs counter with the league's 5th-ranked scoring offense (27.8 PPG) and Patrick Mahomes' precision passing (24 TD, 5 INT). Defensively, Kansas City holds a slight edge, ranking 7th in points allowed (19.4) vs Buffalo's 11th (21.2). The Chiefs' pass rush (37 sacks) could be critical against a Bills offensive line that's allowed 28 sacks this season. Third-down efficiency favors Buffalo (47.2% conversion rate vs KC's 42.1%), which could be the difference in a tight game.",

                'trends': "Kansas City is 7-3 ATS this season but only 2-3 ATS on the road. Buffalo is a scorching 8-2 ATS overall and 5-0 ATS at home, consistently covering against quality opponents. The Chiefs are 6-4 O/U, while the Bills are 7-3 O/U, reflecting their offensive firepower. In their last five head-to-head meetings, the home team is 4-1 straight up and 3-2 ATS. Public betting is heavily leaning Bills (68% of tickets), but sharp money reports show more balanced action, suggesting professionals see value on both sides depending on the number.",

                'injuries': "Both teams are relatively healthy entering this critical matchup. Buffalo's WR Khalil Shakir is listed as questionable with an ankle injury but practiced fully Friday, indicating he'll likely play. Kansas City has TE Travis Kelce nursing a shoulder issue, though he hasn't missed practice. The Chiefs' secondary is at full strength after CB L'Jarius Sneed returned from a calf injury last week. Buffalo's defensive line is healthy and will be crucial in generating pressure on Mahomes without blitzing, allowing their secondary to stay intact in coverage.",

                'weather': "Weather conditions look favorable for an offensive shootout. Forecasts show 42°F at kickoff with wind speeds around 8-10 mph—well below the threshold that typically impacts passing games. No precipitation expected. The controlled weather environment should allow both quarterbacks to operate at full capacity, which supports the elevated total.",

                'betting_context': "The line opened Bills -1.5 and quickly moved to -2, with some books showing -2.5. This movement indicates sharp early action on Buffalo, despite public perception that may favor Kansas City's championship pedigree. The total opened at 51 and climbed to 52.5, reflecting market confidence in scoring. Historically, when these teams meet with a total above 50, the over is 4-1 in the last five instances. Line value could emerge on Kansas City if the spread pushes to -3, as getting a field goal with the Chiefs in a potential shootout presents interesting risk-reward."
            }
        },
        {
            'away_team': 'Green Bay Packers',
            'away_abbr': 'gb',
            'away_record': '6-4',
            'home_team': 'Chicago Bears',
            'home_abbr': 'chi',
            'home_record': '4-6',
            'line': 'Packers -7',
            'total': '43.5',
            'game_time': 'Sunday, Nov 17 — 1:00 PM ET',
            'venue': 'Soldier Field, Chicago, IL',
            'analysis': {
                'overview': "NFC North rivalry games always bring intensity, but this matchup features significant talent disparity. Green Bay has won 10 straight against Chicago, the NFL's longest active win streak in a single rivalry. The Packers are 7-point road favorites, a substantial number that reflects both their recent dominance and Chicago's offensive struggles. This spread suggests oddsmakers expect Green Bay to control the game throughout, with Chicago's home field advantage barely factoring into the equation.",

                'key_stats': "Green Bay's offense ranks 9th in scoring (25.8 PPG) with Jordan Love establishing himself as an elite QB (22 TD, 9 INT, 64.2% completion). Chicago's offense ranks 28th (17.2 PPG), hampered by quarterback instability and a struggling offensive line that's allowed 42 sacks (worst in NFL). The Packers' defensive unit ranks 6th in points allowed (18.9) and has been particularly stout against the run, allowing just 88.4 yards per game. Chicago's defense ranks 15th (22.1 points allowed) but faces the challenge of containing a multi-dimensional Packers attack without generating consistent pressure.",

                'trends': "Green Bay is 6-4 ATS this season and 4-1 ATS as a road favorite. The Packers are 5-0 straight up against Chicago in their last five meetings, with an average margin of victory of 13.8 points. Chicago is 3-7 ATS this season and just 1-4 ATS at home, consistently failing to cover even modest spreads. The under is 6-4 in Packers games this season, reflecting strong defensive performances, while the under is 7-3 in Bears games due to their offensive limitations. In the last five Bears-Packers matchups, the under is 4-1, averaging 38.6 combined points.",

                'injuries': "Chicago's injury situation is concerning. QB Justin Fields is dealing with a shoulder injury that limited him in practice this week, though he's expected to start. If he's compromised, it further limits an already struggling offense. WR DJ Moore (ankle) practiced limited Thursday-Friday and should play but may not be at 100%. For Green Bay, they're relatively healthy on offense, with all key skill players expected to suit up. The Packers' offensive line has LT David Bakhtiari questionable with a knee issue, though he's likely to play through it.",

                'weather': "Typical November conditions in Chicago with temperatures around 38°F at kickoff. Wind is the key factor—forecasts show sustained winds of 12-15 mph with gusts potentially reaching 20 mph. This could impact the passing game, particularly for Chicago's already-limited aerial attack. Historical data shows scoring decreases by approximately 3-4 points per game when wind speeds exceed 15 mph at Soldier Field. These conditions favor Green Bay's more physical, run-oriented attack.",

                'betting_context': "The line opened Packers -6 and moved to -7, absorbing sharp action on Green Bay despite the elevated number. Public betting is split (52% on Packers), but the line movement suggests sharps are willing to lay the touchdown. The total opened at 44.5 and dipped to 43.5, reflecting both weather concerns and Chicago's offensive woes. Historically, when Green Bay is favored by 7+ against Chicago, they're 3-1 ATS over the last decade. The key question is whether seven points properly accounts for Chicago's home field advantage and rivalry game intensity, or if Green Bay's recent dominance justifies laying the touchdown."
            }
        }
    ]

    # Generate the analysis HTML
    analysis_html = generate_nfl_slate_analysis(week=11, games_data=games_data)

    return analysis_html

def main():
    """Main execution function"""

    print("="*80)
    print("BETLEGEND DAILY SLATE ANALYSIS GENERATOR")
    print("="*80)
    print("\nGenerating comprehensive game analysis...")
    print("This creates SEO-optimized content WITHOUT giving picks\n")

    # Generate example NFL analysis
    nfl_analysis = generate_example_nfl_analysis()

    # Save to file for review
    output_path = os.path.join(BASE_DIR, "nfl_analysis_example.html")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(nfl_analysis)

    print(f"[OK] Generated NFL analysis")
    print(f"     Saved to: {output_path}")
    print(f"\nNext steps:")
    print(f"1. Review the generated analysis")
    print(f"2. Run insert_analysis_into_page() to add to nfl.html")
    print(f"3. Repeat for NBA, MLB pages")

    # Ask if user wants to insert into actual page
    print("\n" + "="*80)
    print("MANUAL CONFIRMATION REQUIRED")
    print("="*80)
    print("\nTo insert this analysis into nfl.html, run:")
    print("  insert_analysis_into_page('nfl.html', analysis_html)")

    return nfl_analysis

if __name__ == "__main__":
    main()
