#!/usr/bin/env python3
"""
Trim overly long meta descriptions across all HTML files in the repo root.

Rules:
- Only processes .html files in repo root (not subdirectories, not .git)
- Skips redirect stubs (files containing "Page Moved" in first 500 chars)
- Only trims descriptions OVER 170 characters (not 160-170 range)
- Target length: 155-165 characters
- Tries sentence boundary (period + space) first, then last word boundary + "..."
- Also updates og:description and twitter:description to match
- Minimum result length: 120 characters
"""

import os
import re
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def trim_description(desc, max_len=165, min_len=120):
    """Trim a description to fit within target range.

    Strategy:
    1. Try to cut at a sentence boundary (period + space) before max_len
    2. If no sentence boundary, cut at last space before 160 chars and add "..."
    3. Ensure result is at least min_len chars
    """
    if len(desc) <= 170:
        return desc  # Don't touch descriptions 170 or under

    # Strategy 1: Find last sentence boundary (". ") before max_len
    search_text = desc[:max_len]
    last_period = -1
    for i in range(len(search_text) - 1, min_len - 1, -1):
        if search_text[i] == '.' and (i + 1 >= len(search_text) or search_text[i + 1] == ' '):
            last_period = i
            break

    if last_period >= min_len:
        result = desc[:last_period + 1].strip()
        if min_len <= len(result) <= max_len:
            return result

    # Strategy 2: Cut at last space before 160 chars and add "..."
    cut_point = 157  # 157 + "..." = 160
    search_text = desc[:cut_point]
    last_space = search_text.rfind(' ')

    if last_space >= min_len:
        result = desc[:last_space].rstrip(',;:-') + "..."
        if min_len <= len(result) <= max_len:
            return result

    # Strategy 3: Fallback - hard cut at 160 and add "..."
    result = desc[:157].rstrip() + "..."
    return result


def extract_meta_description(html_content):
    """Extract meta description from HTML, handling both attribute orders.

    Uses separate patterns for double-quoted and single-quoted attributes,
    to avoid issues with apostrophes inside descriptions.
    """
    # Pattern 1a: <meta name="description" content="..."> (double quotes)
    m = re.search(r'<meta\s+name="description"\s+content="([^"]*)"', html_content, re.IGNORECASE)
    if m:
        return m.group(1), m.group(0)

    # Pattern 1b: <meta name='description' content='...'> (single quotes)
    m = re.search(r"<meta\s+name='description'\s+content='([^']*)'", html_content, re.IGNORECASE)
    if m:
        return m.group(1), m.group(0)

    # Pattern 2a: <meta content="..." name="description"> (double quotes)
    m = re.search(r'<meta\s+content="([^"]*)"\s+name="description"', html_content, re.IGNORECASE)
    if m:
        return m.group(1), m.group(0)

    # Pattern 2b: <meta content='...' name='description'> (single quotes)
    m = re.search(r"<meta\s+content='([^']*)'\s+name='description'", html_content, re.IGNORECASE)
    if m:
        return m.group(1), m.group(0)

    return None, None


def update_og_description(html_content, new_desc_unused):
    """Update og:description if it exists and is over 170 chars.

    Trims independently based on its own content.
    """
    # Pattern: <meta content="..." property="og:description">
    m = re.search(r'(<meta\s+content=")([^"]*?)("\s+property="og:description")', html_content, re.IGNORECASE)
    if m and len(m.group(2)) > 170:
        trimmed = trim_description(m.group(2))
        if trimmed != m.group(2):
            old_tag = m.group(0)
            new_tag = m.group(1) + trimmed + m.group(3)
            html_content = html_content.replace(old_tag, new_tag, 1)
            return html_content, True

    # Pattern: <meta property="og:description" content="...">
    m = re.search(r'(<meta\s+property="og:description"\s+content=")([^"]*?)(")', html_content, re.IGNORECASE)
    if m and len(m.group(2)) > 170:
        trimmed = trim_description(m.group(2))
        if trimmed != m.group(2):
            old_tag = m.group(0)
            new_tag = m.group(1) + trimmed + m.group(3)
            html_content = html_content.replace(old_tag, new_tag, 1)
            return html_content, True

    return html_content, False


def update_twitter_description(html_content, new_desc_unused):
    """Update twitter:description if it exists and is over 170 chars.

    Trims independently based on its own content.
    """
    # Pattern: <meta content="..." name="twitter:description">
    m = re.search(r'(<meta\s+content=")([^"]*?)("\s+name="twitter:description")', html_content, re.IGNORECASE)
    if m and len(m.group(2)) > 170:
        trimmed = trim_description(m.group(2))
        if trimmed != m.group(2):
            old_tag = m.group(0)
            new_tag = m.group(1) + trimmed + m.group(3)
            html_content = html_content.replace(old_tag, new_tag, 1)
            return html_content, True

    # Pattern: <meta name="twitter:description" content="...">
    m = re.search(r'(<meta\s+name="twitter:description"\s+content=")([^"]*?)(")', html_content, re.IGNORECASE)
    if m and len(m.group(2)) > 170:
        trimmed = trim_description(m.group(2))
        if trimmed != m.group(2):
            old_tag = m.group(0)
            new_tag = m.group(1) + trimmed + m.group(3)
            html_content = html_content.replace(old_tag, new_tag, 1)
            return html_content, True

    return html_content, False


def process_file(filepath):
    """Process a single HTML file. Returns dict with results or None if skipped."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
    except Exception as e:
        return {'file': filepath, 'error': str(e)}

    # Skip redirect stubs
    if 'Page Moved' in content[:500]:
        return None

    # Extract meta description
    desc, full_tag = extract_meta_description(content)
    if desc is None:
        return None  # No meta description found

    original_len = len(desc)
    if original_len <= 170:
        return None  # Within acceptable range, skip

    # Trim the description
    new_desc = trim_description(desc)
    new_len = len(new_desc)

    if new_desc == desc:
        return None  # No change needed (shouldn't happen if > 170, but safety check)

    # Replace in file content - rebuild the tag with new description
    new_tag = full_tag.replace(desc, new_desc)
    new_content = content.replace(full_tag, new_tag, 1)

    # Also update og:description and twitter:description independently
    og_updated = False
    twitter_updated = False
    new_content, og_updated = update_og_description(new_content, new_desc)
    new_content, twitter_updated = update_twitter_description(new_content, new_desc)

    # Write back
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
    except Exception as e:
        return {'file': filepath, 'error': f'Write failed: {e}'}

    return {
        'file': os.path.basename(filepath),
        'old_len': original_len,
        'new_len': new_len,
        'old_desc': desc,
        'new_desc': new_desc,
        'og_updated': og_updated,
        'twitter_updated': twitter_updated,
    }


def main():
    # Get all .html files in repo root only (not subdirectories)
    html_files = []
    for fname in os.listdir(REPO_ROOT):
        if fname.endswith('.html'):
            fpath = os.path.join(REPO_ROOT, fname)
            if os.path.isfile(fpath):
                html_files.append(fpath)

    html_files.sort()

    print(f"Scanning {len(html_files)} HTML files in {REPO_ROOT}...")
    print(f"Threshold: Only trimming descriptions OVER 170 characters")
    print(f"Target range: 155-165 characters")
    print("=" * 80)

    total_scanned = 0
    total_over_170 = 0
    total_trimmed = 0
    total_skipped_redirect = 0
    total_no_meta = 0
    results = []
    errors = []

    for fpath in html_files:
        total_scanned += 1
        result = process_file(fpath)

        if result is None:
            # Check why it was skipped for stats
            try:
                with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
                if 'Page Moved' in content[:500]:
                    total_skipped_redirect += 1
                else:
                    desc, _ = extract_meta_description(content)
                    if desc is None:
                        total_no_meta += 1
                    elif len(desc) > 170:
                        total_over_170 += 1  # Over 170 but couldn't trim
                        print(f"WARNING: Could not process {os.path.basename(fpath)} ({len(desc)} chars)")
            except:
                pass
            continue

        if 'error' in result:
            errors.append(result)
            continue

        total_over_170 += 1
        total_trimmed += 1
        results.append(result)

    # Print summary
    print(f"\nSUMMARY")
    print(f"=" * 80)
    print(f"Total HTML files scanned:     {total_scanned}")
    print(f"Redirect stubs skipped:       {total_skipped_redirect}")
    print(f"Files without meta desc:      {total_no_meta}")
    print(f"Descriptions over 170 chars:  {total_over_170}")
    print(f"Descriptions trimmed:         {total_trimmed}")
    if errors:
        print(f"Errors:                       {len(errors)}")
        for e in errors:
            print(f"  - {e['file']}: {e['error']}")

    # Print examples
    if results:
        print(f"\n\nEXAMPLES (first 15 of {len(results)} trimmed):")
        print("=" * 80)
        for r in results[:15]:
            print(f"\nFile: {r['file']}")
            print(f"  BEFORE ({r['old_len']} chars): {r['old_desc'][:100]}...")
            print(f"  AFTER  ({r['new_len']} chars): {r['new_desc']}")
            extras = []
            if r['og_updated']:
                extras.append("og:description")
            if r['twitter_updated']:
                extras.append("twitter:description")
            if extras:
                print(f"  Also updated: {', '.join(extras)}")

    # Print length distribution of trimmed results
    if results:
        print(f"\n\nLENGTH DISTRIBUTION OF TRIMMED DESCRIPTIONS:")
        print("=" * 80)
        ranges = {
            '120-130': 0, '131-140': 0, '141-150': 0,
            '151-155': 0, '156-160': 0, '161-165': 0,
        }
        for r in results:
            l = r['new_len']
            if 120 <= l <= 130:
                ranges['120-130'] += 1
            elif 131 <= l <= 140:
                ranges['131-140'] += 1
            elif 141 <= l <= 150:
                ranges['141-150'] += 1
            elif 151 <= l <= 155:
                ranges['151-155'] += 1
            elif 156 <= l <= 160:
                ranges['156-160'] += 1
            elif 161 <= l <= 165:
                ranges['161-165'] += 1

        for rng, count in ranges.items():
            bar = '#' * min(count, 80)
            print(f"  {rng}: {count:3d} {bar}")

    # Full list
    if results:
        print(f"\n\nFULL LIST OF ALL {len(results)} TRIMMED FILES:")
        print("=" * 80)
        for r in results:
            print(f"  {r['file']}: {r['old_len']} -> {r['new_len']} chars")

    return 0 if not errors else 1


if __name__ == '__main__':
    sys.exit(main())
