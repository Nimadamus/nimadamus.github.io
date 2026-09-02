#!/bin/bash
# PRE-COMMIT HOOK - Blocks bad content before it reaches GitHub
# This runs automatically before every commit
# ENHANCED: December 31, 2025 - Added pagination check for sports pages

echo "=========================================="
echo "PRE-COMMIT VALIDATION"
echo "=========================================="

# Get the repo root
REPO_ROOT=$(git rev-parse --show-toplevel)
cd "$REPO_ROOT"

# ============================================================
# CHECK 1: PLACEHOLDER CONTENT IN ALL SPORTS PAGES
# ============================================================
echo "Checking for placeholder content..."

PLACEHOLDER_FOUND=""
for prefix in nba nhl nfl ncaab ncaaf mlb soccer; do
    for file in ${prefix}*.html; do
        if [ -f "$file" ]; then
            # Skip records and calendar files
            if [[ "$file" == *"records"* ]] || [[ "$file" == *"calendar"* ]]; then
                continue
            fi

            if grep -qi -E "coming soon|analysis coming|matchup analysis coming|preview coming|\bTBD\b|\bTBA\b" "$file" 2>/dev/null; then
                if [ -z "$PLACEHOLDER_FOUND" ]; then
                    PLACEHOLDER_FOUND="$file"
                else
                    PLACEHOLDER_FOUND="$PLACEHOLDER_FOUND
$file"
                fi
            fi
        fi
    done
done

if [ -n "$PLACEHOLDER_FOUND" ]; then
    echo ""
    echo "[X] COMMIT BLOCKED - PLACEHOLDER CONTENT FOUND:"
    echo "$PLACEHOLDER_FOUND"
    echo ""
    echo "Fix these files before committing!"
    exit 1
fi
echo "  ✓ No placeholder content found"

# ============================================================
# CHECK 2: NON-NUMERIC COLLEGE LOGOS IN STAGED FILES
# ============================================================
echo "Checking college logo URLs..."
STAGED_HTML=$(git diff --cached --name-only | grep '\.html$')
if [ -n "$STAGED_HTML" ]; then
    BAD_LOGOS=$(echo "$STAGED_HTML" | xargs grep -l -E "teamlogos/ncaa/500/[a-zA-Z][a-zA-Z0-9-]+\.png" 2>/dev/null | head -5)

    if [ -n "$BAD_LOGOS" ]; then
        echo ""
        echo "[X] COMMIT BLOCKED - BAD COLLEGE LOGOS:"
        echo "$BAD_LOGOS"
        echo ""
        echo "Run: python scripts/college_logo_ids.py"
        exit 1
    fi
fi
echo "  ✓ College logos OK"

# ============================================================
# CHECK 3: BROKEN SOCCER LOGOS
# ============================================================
echo "Checking for broken soccer logos..."
BROKEN_SOCCER=""

# Known broken ESPN IDs that must be corrected
BROKEN_IDS="355 3199 3282 5168 108"

for file in soccer*.html; do
    if [ -f "$file" ]; then
        # Skip calendar and records
        if [[ "$file" == *"calendar"* ]] || [[ "$file" == *"records"* ]]; then
            continue
        fi

        for bad_id in $BROKEN_IDS; do
            if grep -q "teamlogos/soccer/500/${bad_id}\.png" "$file" 2>/dev/null; then
                BROKEN_SOCCER="$BROKEN_SOCCER
  $file: Uses broken ID $bad_id"
            fi
        done
    fi
done

if [ -n "$BROKEN_SOCCER" ]; then
    echo ""
    echo "[X] COMMIT BLOCKED - BROKEN SOCCER LOGOS:"
    echo "$BROKEN_SOCCER"
    echo ""
    echo "Run: python scripts/soccer_logo_ids.py"
    echo ""
    echo "Known corrections:"
    echo "  355 -> 397 (Barnsley)"
    echo "  3199 -> 3263 (Genoa)"
    echo "  3282 -> 4050 (Cremonese)"
    echo "  5168 -> 6851 (Paris FC)"
    echo "  108 -> 2925 (Cagliari)"
    exit 1
fi
echo "  ✓ Soccer logos OK"

# ============================================================
# CHECK 4: NAVIGATION TEXT
# ============================================================
echo "Checking navigation text..."
if [ -n "$STAGED_HTML" ]; then
    BAD_NAV=$(echo "$STAGED_HTML" | xargs grep -l ">Overview<" 2>/dev/null)

    if [ -n "$BAD_NAV" ]; then
        echo ""
        echo "[X] COMMIT BLOCKED - BAD NAV TEXT (Overview instead of Detailed Breakdown):"
        echo "$BAD_NAV"
        exit 1
    fi
fi
echo "  ✓ Navigation text OK"

# ============================================================
# CHECK 5: NO PAGINATION ON SPORTS OR FEATURED GAME PAGES - EVER
# These pages use CALENDAR SIDEBAR ONLY - no archive-link pagination
# Updated January 8, 2026 - Now also blocks featured game pagination
# ============================================================
echo "Checking for forbidden pagination..."
PAGINATION_FOUND=""

# Check all sports pages
for prefix in nba nhl nfl ncaab ncaaf mlb soccer; do
    for file in ${prefix}.html ${prefix}-page*.html; do
        if [ -f "$file" ]; then
            if [[ "$file" == *"records"* ]]; then
                continue
            fi
            if grep -q 'class="archive-link"' "$file" 2>/dev/null; then
                PAGINATION_FOUND="$PAGINATION_FOUND $file"
            fi
        fi
    done
done

# Also check featured game pages
for file in featured-game*.html; do
    if [ -f "$file" ]; then
        if grep -q 'class="archive-link"' "$file" 2>/dev/null; then
            PAGINATION_FOUND="$PAGINATION_FOUND $file"
        fi
    fi
done

if [ -n "$PAGINATION_FOUND" ]; then
    echo ""
    echo "[X] COMMIT BLOCKED - PAGINATION FOUND:"
    echo "$PAGINATION_FOUND"
    echo ""
    echo "These pages use calendar sidebar only, not pagination!"
    echo "Remove the archive-link divs before committing."
    exit 1
fi
echo "  ✓ No forbidden pagination found"

# ============================================================
# CHECK 6: SPORTS PAGE TITLES MUST HAVE DATES - BLOCKING!
# Updated January 11, 2026 - Now BLOCKS commits with generic titles
# ============================================================
echo "Checking sports page titles for dates..."
MISSING_DATES=""
GENERIC_TITLES=""
for prefix in nba nhl nfl ncaab ncaaf mlb soccer; do
    for file in ${prefix}-page*.html ${prefix}.html; do
        if [ -f "$file" ]; then
            # Skip records and calendar files
            if [[ "$file" == *"records"* ]] || [[ "$file" == *"calendar"* ]] || [[ "$file" == *"archive"* ]]; then
                continue
            fi

            # BLOCK: Check for generic "Archive - Page X" titles - THESE ARE BANNED
            if grep -q -E "<title>.*Archive - Page [0-9]+" "$file" 2>/dev/null; then
                GENERIC_TITLES="$GENERIC_TITLES $file"
            fi

            # Check if title contains a date pattern (December, November, etc. with year)
            if ! grep -q -E "<title>.*((January|February|March|April|May|June|July|August|September|October|November|December)[^<]*20[0-9]{2})" "$file" 2>/dev/null; then
                # Also accept YYYY-MM-DD format in title
                if ! grep -q -E "<title>.*20[0-9]{2}-[0-9]{2}-[0-9]{2}" "$file" 2>/dev/null; then
                    MISSING_DATES="$MISSING_DATES $file"
                fi
            fi
        fi
    done
done

# BLOCK if generic "Archive - Page X" titles found
if [ -n "$GENERIC_TITLES" ]; then
    echo ""
    echo "[X] COMMIT BLOCKED - GENERIC PAGE TITLES FOUND:"
    echo "$GENERIC_TITLES"
    echo ""
    echo "These pages have 'Archive - Page X' titles which break the calendar!"
    echo ""
    echo "FIX: Change each title to include the date:"
    echo "  <title>NBA Analysis - January 12, 2026 | BetLegend</title>"
    echo ""
    echo "This is MANDATORY. Generic titles cause calendar gaps."
    exit 1
fi

if [ -n "$MISSING_DATES" ]; then
    echo ""
    echo "[!] WARNING: These sports pages may be missing dates in titles:"
    echo "$MISSING_DATES"
    echo ""
    echo "Page titles should include the date, e.g.:"
    echo "  'NBA Analysis - December 31, 2025 | BetLegend'"
    echo "  'NCAAF Bowl Games - December 29, 2025 | BetLegend'"
    echo ""
    echo "This ensures the calendar sync works correctly."
    echo "Run: python scripts/sync_calendars.py after fixing."
fi
echo "  ✓ Sports page titles checked"

# ============================================================
# CHECK 7: DUPLICATE GAMES ACROSS PAGES
# Added January 13, 2026 - Prevents same game appearing on multiple date pages
# ============================================================
echo "Checking for duplicate games across pages..."

# Only run this check if soccer, nba, nhl, nfl, ncaab, ncaaf, or mlb pages are staged
SPORTS_STAGED=$(git diff --cached --name-only | grep -E "^(soccer|nba|nhl|nfl|ncaab|ncaaf|mlb).*\.html$")
if [ -n "$SPORTS_STAGED" ]; then
    # Determine which sports have staged files
    for sport in soccer nba nhl nfl ncaab ncaaf mlb; do
        if echo "$SPORTS_STAGED" | grep -q "^${sport}"; then
            # Run duplicate detection for this sport
            if python scripts/detect_duplicate_games.py "$sport" > /dev/null 2>&1; then
                # Check exit code
                if ! python scripts/detect_duplicate_games.py "$sport" --quiet 2>/dev/null; then
                    echo ""
                    echo "[!] WARNING: Possible duplicate games in $sport pages"
                    echo "    Run: python scripts/detect_duplicate_games.py $sport"
                    echo "    to see details and fix before pushing."
                fi
            fi
        fi
    done
fi
echo "  ✓ Duplicate game check complete"

# ============================================================

echo ""
echo "[OK] All pre-commit checks passed!"
echo "=========================================="
exit 0
