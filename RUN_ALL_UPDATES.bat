@echo off
REM ============================================
REM BETLEGEND COMPLETE DAILY UPDATE
REM Runs ALL automated updates:
REM   1. Sports pages (NBA, NHL, NFL, NCAAB, NCAAF)
REM   2. Covers Consensus (SportsBettingPrime)
REM ============================================

echo.
echo ========================================
echo BETLEGEND COMPLETE DAILY UPDATE
echo %date% %time%
echo ========================================
echo.

cd /d "C:\Users\Nima\nimadamus.github.io"

REM Update sports pages
echo [1/2] UPDATING SPORTS PAGES...
echo ----------------------------------------
python daily_sports_update.py --no-push

echo.
echo [2/2] UPDATING COVERS CONSENSUS...
echo ----------------------------------------
python daily_covers_update.py

echo.
echo ========================================
echo ALL UPDATES COMPLETE!
echo ========================================
echo.

REM Keep window open if run manually
pause
