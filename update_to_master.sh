#!/bin/bash

MASTER_URL="https://docs.google.com/spreadsheets/d/e/2PACX-1vQjW2l6hBUafumAiOdJblACLIx3GTtdJDcytUcN1nu2QHJmHnUMN9_5Tp2v7VqMTZaATfdmcJ-SK4jD/pub?output=csv"

# Update all records pages to master sheet
for file in nfl-records.html nhl-records.html nba-records.html betlegend-verified-records.html soccer-records.html ncaaf-records.html; do
  if [ -f "$file" ]; then
    sed -i "s|https://docs.google.com/spreadsheets/d/e/2PACX-[^']*pub?output=csv|$MASTER_URL|g" "$file"
    echo "Updated $file to master sheet"
  fi
done
