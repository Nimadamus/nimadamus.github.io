#!/bin/bash

# Files with Sports dropdown
files_with_dropdown=(
"affiliates.html"
"bankroll.html"
"best-bets-today.html"
"bestbook.html"
"bestonlinesportsbook.html"
"best-online-sportsbook-old.html"
"betlegend-verified-records.html"
"betting-101.html"
"betting-calculators.html"
"betting-glossary.html"
"blog.html"
"blog-page2.html"
"blog-page3.html"
"blog-page4.html"
"blog-page5.html"
"blog-page6.html"
"blog-page7.html"
"blog-page8.html"
"contact.html"
"covers-consensus.html"
"email.html"
"expected-value-calculator.html"
"featured-game-of-the-day.html"
"FreeAlerts.html"
"howitworks.html"
"implied-probability-calculator.html"
"index.html"
"kelly-criterion.html"
"live-odds.html"
"matchups.html"
"mlb.html"
"mlb-historical.html"
"mlb-page2.html"
"moneyline-parlay-of-the-day.html"
"nba.html"
"nba-records.html"
"ncaab.html"
"ncaab-page2.html"
"ncaab-records.html"
"ncaaf.html"
"ncaaf-page2.html"
"ncaaf-records.html"
"news.html"
"news-page2.html"
"news-page3.html"
"new-york-sports-betting.html"
"nfl.html"
"nfl-records.html"
"nfl-records-broken-backup.html"
"nhl.html"
"nhl-records.html"
"odds.html"
"odds-converter.html"
"parlay-calculator.html"
"picks.html"
"proofofpicks.html"
"records.html"
"screenshots.html"
"smartbets.html"
"soccer.html"
"soccer-records.html"
"subscribe.html"
"upcomingpicks.html"
)

echo "=== FILES WITH NCAAB LINK IN SPORTS DROPDOWN ==="
for file in "${files_with_dropdown[@]}"; do
  if [ -f "$file" ]; then
    # Extract the Sports dropdown section and check for NCAAB
    sports_section=$(awk '/dropbtn.*Sports|Sports.*dropbtn/,/^[[:space:]]*<\/div>/ {print}' "$file" | head -20)
    if echo "$sports_section" | grep -qi "ncaab"; then
      echo "✓ $file"
    fi
  fi
done

echo ""
echo "=== FILES WITHOUT NCAAB LINK IN SPORTS DROPDOWN ==="
for file in "${files_with_dropdown[@]}"; do
  if [ -f "$file" ]; then
    # Extract the Sports dropdown section and check for NCAAB
    sports_section=$(awk '/dropbtn.*Sports|Sports.*dropbtn/,/^[[:space:]]*<\/div>/ {print}' "$file" | head -20)
    if ! echo "$sports_section" | grep -qi "ncaab"; then
      echo "✗ $file"
    fi
  fi
done
