#!/bin/bash

files_missing_ncaab=(
"affiliates.html"
"bankroll.html"
"best-bets-today.html"
"bestbook.html"
"bestonlinesportsbook.html"
"best-online-sportsbook-old.html"
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
"kelly-criterion.html"
"live-odds.html"
"matchups.html"
"mlb.html"
"mlb-historical.html"
"mlb-page2.html"
"nba.html"
"ncaaf.html"
"ncaaf-page2.html"
"news.html"
"news-page2.html"
"news-page3.html"
"new-york-sports-betting.html"
"nfl.html"
"nhl.html"
"odds.html"
"odds-converter.html"
"parlay-calculator.html"
"picks.html"
"proofofpicks.html"
"records.html"
"screenshots.html"
"smartbets.html"
"soccer.html"
"subscribe.html"
"upcomingpicks.html"
)

echo "FILES WITH NO INDENTATION:"
for file in "${files_missing_ncaab[@]}"; do
  if [ -f "$file" ]; then
    nba_line=$(grep -n "href=\"nba.html\">NBA</a>" "$file" | head -1)
    if echo "$nba_line" | grep -q "^[0-9]*:<a href="; then
      echo "  $file"
    fi
  fi
done

echo ""
echo "FILES WITH INDENTATION (spaces):"
for file in "${files_missing_ncaab[@]}"; do
  if [ -f "$file" ]; then
    nba_line=$(grep -n "href=\"nba.html\">NBA</a>" "$file" | head -1)
    if echo "$nba_line" | grep -q "^[0-9]*:[[:space:]]*<a href="; then
      echo "  $file"
    fi
  fi
done
