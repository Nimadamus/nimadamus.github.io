#!/usr/bin/env python3
from daily_slate_analyzer import insert_analysis_into_page, generate_example_nfl_analysis
import os

# Generate the analysis
print("Generating NFL Week 11 analysis...")
analysis_html = generate_example_nfl_analysis()

# Insert into nfl.html
nfl_path = r"C:\Users\Nima\Desktop\betlegendpicks\nfl.html"
print(f"Inserting analysis into {nfl_path}...")

success = insert_analysis_into_page(nfl_path, analysis_html)

if success:
    print('[OK] Successfully inserted NFL Week 11 analysis into nfl.html')
    print('The page now has fresh, comprehensive game analysis at the top!')
else:
    print('[ERROR] Failed to insert analysis')
