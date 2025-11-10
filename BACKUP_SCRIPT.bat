@echo off
REM Daily Backup Script for BetLegend Picks
REM Run this daily to create timestamped backups

set BACKUP_DIR=C:\Users\Nima\Desktop\BETLEGEND_BACKUPS
set TIMESTAMP=%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%
set TIMESTAMP=%TIMESTAMP: =0%

echo Creating backup at %TIMESTAMP%...

REM Create backup directory if it doesn't exist
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"

REM Create timestamped subfolder
mkdir "%BACKUP_DIR%\backup_%TIMESTAMP%"

REM Copy all files except .git
xcopy "C:\Users\Nima\betlegendpicks\*" "%BACKUP_DIR%\backup_%TIMESTAMP%\" /E /I /H /Y /EXCLUDE:C:\Users\Nima\betlegendpicks\.gitignore

echo Backup completed: %BACKUP_DIR%\backup_%TIMESTAMP%
echo.
echo Also creating a git commit...
cd C:\Users\Nima\betlegendpicks
git add -A
git commit -m "Auto-backup %TIMESTAMP%"
git push origin main

echo Done!
pause
