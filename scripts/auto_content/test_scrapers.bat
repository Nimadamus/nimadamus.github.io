@echo off
REM Test all scrapers without updating files

echo ============================================================
echo Testing Scrapers (No files will be modified)
echo ============================================================
echo.

cd /d "%~dp0"

REM Test each scraper
echo Testing NBA Scraper...
python -c "from scrapers import NBAScraper; s=NBAScraper(); print(f'NBA: {len(s.get_todays_games())} games')"

echo.
echo Testing NHL Scraper...
python -c "from scrapers import NHLScraper; s=NHLScraper(); print(f'NHL: {len(s.get_todays_games())} games')"

echo.
echo Testing NFL Scraper...
python -c "from scrapers import NFLScraper; s=NFLScraper(); print(f'NFL: {len(s.get_todays_games())} games')"

echo.
echo Testing NCAAB Scraper...
python -c "from scrapers import NCAABScraper; s=NCAABScraper(); print(f'NCAAB: {len(s.get_todays_games())} games')"

echo.
echo Testing NCAAF Scraper...
python -c "from scrapers import NCAAFScraper; s=NCAAFScraper(); print(f'NCAAF: {len(s.get_todays_games())} games')"

echo.
echo Testing MLB Scraper...
python -c "from scrapers import MLBScraper; s=MLBScraper(); print(f'MLB: {len(s.get_todays_games())} games')"

echo.
echo Testing Soccer Scraper...
python -c "from scrapers import SoccerScraper; s=SoccerScraper(); games=s.get_full_game_data(leagues=['eng.1','esp.1']); print(f'Soccer: {len(games)} games')"

echo.
echo ============================================================
echo Scraper test complete!
pause
