@echo off
cd /d C:\Users\Nima\nimadamus.github.io

echo ========================================
echo Updating Injury Reports from ESPN
echo ========================================
echo.

python scrape_injuries.py

echo.
echo ========================================
echo Pushing to GitHub...
echo ========================================

git add handicapping-hub.html injuries_data.json
git commit -m "Auto-update injury reports from ESPN"
git push

echo.
echo ========================================
echo DONE - Injuries updated and pushed!
echo ========================================
pause
