@echo off
REM Auto-Content Generation System - Single Sport Run Script
REM Run this to update a specific sport page

echo ============================================================
echo BetLegend Auto-Content Generation System
echo ============================================================
echo.

if "%1"=="" (
    echo Usage: run_single_sport.bat [sport]
    echo.
    echo Available sports:
    echo   nba     - NBA Basketball
    echo   nhl     - NHL Hockey
    echo   nfl     - NFL Football
    echo   ncaab   - College Basketball
    echo   ncaaf   - College Football
    echo   mlb     - MLB Baseball
    echo   soccer  - Soccer ^(Multiple Leagues^)
    echo.
    echo Example: run_single_sport.bat nba
    goto :end
)

REM Navigate to script directory
cd /d "%~dp0"

REM Run the main script for specified sport
python main.py --sport %1

:end
echo.
echo ============================================================
echo Done! Press any key to exit...
pause >nul
