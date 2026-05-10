# Git Safeguards for BetLegend Picks

## Daily Backup Schedule
Run `BACKUP_SCRIPT.bat` every day before making changes. This will:
1. Create a timestamped backup on your Desktop
2. Commit and push to GitHub

## Protection Rules

### NEVER Use These Commands Without Backup First:
- `git reset --hard` - This deletes uncommitted work
- `git push --force` - This can overwrite GitHub history
- `git clean -fd` - This deletes untracked files

### Safe Workflow:
1. Make changes to files
2. Run: `git add -A`
3. Run: `git commit -m "Description of changes"`
4. Run: `git push origin main` (NO --force flag)

### If You Need to Restore:
1. Check `~/Documents/GitHub/nimadamus.github.io` - This is your backup clone
2. Or check `~/Desktop/BETLEGEND_BACKUPS` for timestamped backups
3. Or use: `git reflog` to find lost commits

### Branch Protection (Recommended):
Go to: https://github.com/Nimadamus/nimadamus.github.io/settings/branches
- Enable "Require pull request reviews before merging"
- Enable "Require status checks to pass"
- This prevents accidental force pushes

## Recovery Commands

### To find lost commits:
```bash
git reflog
git show <commit-hash>
```

### To restore a lost commit:
```bash
git cherry-pick <commit-hash>
```

### To create a backup branch before risky operations:
```bash
git branch backup-$(date +%Y%m%d)
git push origin backup-$(date +%Y%m%d)
```
