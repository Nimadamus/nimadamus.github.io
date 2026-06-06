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

REM Re-bake rolling sport preview hubs from the newest standalone previews.
REM Needs no API. Added June 6, 2026 after hubs froze on the May 19 bake:
REM main.py has been failing every Anthropic call (credit balance) and SLATE
REM no longer hand-overwrites hubs, so this is the deterministic backstop.
python ..\refresh_preview_hubs.py --commit >> auto_content_log.txt 2>&1

REM Log completion
echo [%date% %time%] Update complete >> auto_content_log.txt
echo. >> auto_content_log.txt
