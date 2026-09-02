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

REM Rebase onto the remote BEFORE pushing. The hourly-injury-report.yml Action
REM commits injury-report.html straight to main, so by the time this task runs
REM the branch has almost always moved and a bare `git push` is rejected
REM non-fast-forward. It failed silently that way for at least two days: the
REM commits kept stacking up locally and none of this data reached the site.
REM The two writers touch disjoint files, so the rebase applies cleanly.
git pull --rebase
git push

echo.
echo ========================================
echo DONE - All updates complete!
echo ========================================
REM No `pause` here. This script's only caller is the "BetLegend Injury
REM Updates" scheduled task, which runs it hidden through hide_run.vbs -- an
REM interactive prompt in a window nobody can see waits forever and leaves an
REM orphaned cmd.exe behind. Run it by hand from an open console if you want to
REM read the output.
