@echo off
REM Auto-Content Generation System - Daily Run Script
REM Run this to update all sports pages with today's content

echo ============================================================
echo BetLegend Auto-Content Generation System
echo ============================================================
echo.

REM Check for API key
if "%ANTHROPIC_API_KEY%"=="" (
    echo WARNING: ANTHROPIC_API_KEY not set!
    echo Set it with: set ANTHROPIC_API_KEY=your-key-here
    echo.
    echo Running in fallback mode without AI-generated articles...
    echo.
)

REM Navigate to script directory
cd /d "%~dp0"

REM Run the main script
python main.py --sport all

echo.
echo ============================================================
echo Done! Press any key to exit...
pause >nul
