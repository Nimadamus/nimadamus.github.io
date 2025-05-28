name: Update Odds Page Daily

on:
  schedule:
    - cron: '0 16 * * *'
  workflow_dispatch:

jobs:
  update-odds:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout Repository
        uses: actions/checkout@v3

      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: 18

      - name: Install Axios
        run: npm install axios

      - name: Run Odds Fetch Script
        run: node scripts/fetchOdds.js

      - name: Commit and Push Changes
        run: |
          git config --global user.name "GitHub Actions"
          git config --global user.email "actions@github.com"
          git add odds.html
          git commit -m "Auto-update odds.html [live odds]" || echo "No changes to commit"
          git push https://x-access-token:${{ secrets.PAT }}@github.com/Nimadamus/nimadamus.github.io.git HEAD:main
