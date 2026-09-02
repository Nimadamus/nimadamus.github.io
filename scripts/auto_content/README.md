# BetLegend Auto-Content Generation System

Automated daily sports content generation for betlegendpicks.com. This system fetches game data from ESPN, generates human-sounding analysis articles using Claude AI, and updates the website HTML automatically.

## Features

- **Multi-Sport Support**: NBA, NHL, NFL, NCAAB, NCAAF, MLB, and Soccer
- **Real-Time Data**: Fetches schedules, records, standings, and odds from ESPN
- **AI-Generated Content**: Uses Claude to write conversational, analytical articles
- **Automatic HTML Updates**: Inserts new content and manages archive rotation
- **Git Integration**: Auto-commits and pushes changes to GitHub

## Quick Start

### 1. Install Dependencies

```bash
cd scripts/auto_content
pip install -r requirements.txt
```

### 2. Set Your API Key

```bash
# Windows Command Prompt
set ANTHROPIC_API_KEY=your-api-key-here

# Windows PowerShell
$env:ANTHROPIC_API_KEY="your-api-key-here"

# Or set permanently in System Environment Variables
```

### 3. Run the System

**Update all sports:**
```bash
python main.py --sport all
```

**Update a specific sport:**
```bash
python main.py --sport nba
```

**Dry run (preview without changes):**
```bash
python main.py --sport all --dry-run
```

## Batch Files (Windows)

- `run_daily.bat` - Run full update for all sports
- `run_single_sport.bat [sport]` - Run update for one sport
- `test_scrapers.bat` - Test data scrapers without making changes

## Command Line Options

```
python main.py [options]

Options:
  --sport, -s     Sport to process: nba, nhl, nfl, ncaab, ncaaf, mlb, soccer, all
  --date, -d      Date to process (YYYYMMDD format, default: today)
  --dry-run       Run without writing files or pushing to git
  --no-push       Skip git push (still commits)
  --api-key       Anthropic API key (or use ANTHROPIC_API_KEY env var)
```

## Architecture

```
auto_content/
├── config.py              # Configuration settings
├── main.py                # Main orchestrator
├── html_updater.py        # HTML file management
├── scrapers/
│   ├── base_scraper.py    # Base ESPN scraper
│   ├── nba_scraper.py     # NBA-specific scraper
│   ├── nhl_scraper.py     # NHL-specific scraper
│   ├── nfl_scraper.py     # NFL-specific scraper
│   ├── ncaab_scraper.py   # College basketball scraper
│   ├── ncaaf_scraper.py   # College football scraper
│   ├── mlb_scraper.py     # MLB-specific scraper
│   └── soccer_scraper.py  # Multi-league soccer scraper
├── generators/
│   └── content_generator.py  # Claude AI content generation
└── templates/             # HTML templates (future use)
```

## How It Works

1. **Data Collection**: Scrapers fetch today's games from ESPN API
   - Game times, venues, broadcasts
   - Team records and standings
   - Betting lines (spreads, totals)
   - Recent form (last 10 games)

2. **Content Generation**: Claude AI generates for each game:
   - Stat grids with key metrics
   - 200-300 word analytical articles
   - Conversational, human-sounding tone

3. **HTML Updates**:
   - New content inserted at top of sport page
   - Old content archived to paginated pages
   - Pagination links updated across all pages

4. **Deployment**:
   - Changes committed to git
   - Pushed to GitHub
   - GitHub Pages deploys automatically

## Scheduling Daily Updates

### Windows Task Scheduler

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger: Daily at your preferred time (e.g., 8:00 AM)
4. Action: Start a program
5. Program: `C:\Users\Nima\nimadamus.github.io\scripts\auto_content\run_daily.bat`

### GitHub Actions (Alternative)

Add `.github/workflows/auto-content.yml`:

```yaml
name: Auto Content Update
on:
  schedule:
    - cron: '0 14 * * *'  # 2 PM UTC daily
  workflow_dispatch:  # Manual trigger

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r scripts/auto_content/requirements.txt
      - run: python scripts/auto_content/main.py --sport all
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
      - run: |
          git config user.name "GitHub Actions"
          git config user.email "actions@github.com"
          git add -A
          git commit -m "Auto-update sports content" || exit 0
          git push
```

## Configuration

Edit `config.py` to customize:

- **SPORTS**: Enable/disable sports, set page counts
- **POSTS_PER_PAGE**: How many days of content per page
- **MAX_GAMES_PER_SPORT**: Limit games for college sports
- **GIT_AUTO_COMMIT/PUSH**: Toggle git automation

## API Costs

Approximate Claude API costs per daily run:
- 5-10 games/sport × 7 sports = 35-70 articles
- ~$0.50-2.00/day depending on model and article length

## Troubleshooting

**"ANTHROPIC_API_KEY not set"**
- Set the environment variable before running
- Or pass `--api-key your-key` to main.py

**"No games found"**
- Sport may be out of season
- Check ESPN is accessible
- Verify date format (YYYYMMDD)

**"Failed to update HTML"**
- Ensure HTML file exists and is readable
- Check file permissions
- Verify HTML structure hasn't changed

## Notes

- Content is generated based on real ESPN data
- Articles are AI-generated - review for accuracy before high-stakes use
- System respects sport seasons (won't generate MLB content in winter)
- Archive pages are created automatically as content accumulates
