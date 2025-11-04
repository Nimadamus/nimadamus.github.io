#!/bin/bash

# Find current URLs in each file
echo "Checking current URLs..."
grep -n "pub?output=csv" nba-records.html | head -1
grep -n "pub?output=csv" mlb-records.html | head -1  
grep -n "pub?output=csv" soccer-records.html | head -1
grep -n "pub?output=csv" ncaab-records.html | head -1

echo "Records pages need individual sport sheet URLs"
echo "Please provide the URLs for NBA, MLB, Soccer, NCAAB sheets"
