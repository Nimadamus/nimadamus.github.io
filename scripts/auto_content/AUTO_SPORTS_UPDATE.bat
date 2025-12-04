@echo off
REM ============================================================
REM BetLegend Auto-Content Daily Update
REM This script runs automatically via Windows Task Scheduler
REM ============================================================

REM Set the working directory
cd /d "C:\Users\Nima\nimadamus.github.io\scripts\auto_content"

REM Log start time
echo [%date% %time%] Starting auto-content update >> auto_content_log.txt

REM Run the main script for all sports
python main.py --sport all >> auto_content_log.txt 2>&1

REM Log completion
echo [%date% %time%] Update complete >> auto_content_log.txt
echo. >> auto_content_log.txt
