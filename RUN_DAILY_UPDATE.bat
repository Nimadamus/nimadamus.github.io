@echo off
REM ============================================
REM BETLEGEND DAILY SPORTS UPDATE
REM Run this manually or schedule with Task Scheduler
REM ============================================

echo.
echo ========================================
echo BETLEGEND DAILY UPDATE
echo %date% %time%
echo ========================================
echo.

cd /d "C:\Users\Nima\nimadamus.github.io"

REM Run the Python script
python daily_sports_update.py

echo.
echo ========================================
echo UPDATE COMPLETE
echo ========================================
echo.

REM Keep window open if run manually
pause
