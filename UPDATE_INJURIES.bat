@echo off
cd /d C:\Users\Nima\nimadamus.github.io

echo ========================================
echo HANDICAPPING HUB AUTO-UPDATER
echo ========================================
echo.

echo [1/3] Updating Injury Reports from ESPN...
python scrape_injuries.py

echo.
echo [2/3] Detecting Sharp Action from Action Network...
python scrape_sharp_action.py

echo.
echo [3/3] Pushing to GitHub...
git add handicapping-hub.html injuries_data.json sharp_action_data.json
git commit -m "Auto-update: injuries + sharp action"
git push

echo.
echo ========================================
echo DONE - All updates complete!
echo ========================================
pause
