#!/bin/sh
# Install the tracked pre-commit hook into .git/hooks/.
# Run this once after cloning the repo so the calendar/canonical/etc. guards activate.
set -e
SRC="$(cd "$(dirname "$0")" && pwd)"
DEST="$SRC/../.git/hooks"
mkdir -p "$DEST"
cp "$SRC/pre-commit" "$DEST/pre-commit"
chmod +x "$DEST/pre-commit"
echo "[ok] Installed pre-commit hook to $DEST/pre-commit"
