import pathlib
import re


ROOT = pathlib.Path(__file__).resolve().parents[1]
SITE_PREFIX = "https://www.betlegendpicks.com/"


CANONICAL_RE = re.compile(
    r'(?P<tag><link[^>]+rel=["\']canonical["\'][^>]+href=["\'](?P<href>[^"\']+)["\'][^>]*>\s*)',
    re.IGNORECASE,
)
OG_URL_RE = re.compile(
    r'(<meta[^>]+property=["\']og:url["\'][^>]+content=["\'])([^"\']+)(["\'][^>]*>)',
    re.IGNORECASE,
)
MAIN_ENTITY_RE = re.compile(
    r'("mainEntityOfPage"\s*:\s*\{\s*"@type"\s*:\s*"WebPage"\s*,\s*"@id"\s*:\s*")([^"]+)(")',
    re.IGNORECASE | re.DOTALL,
)
MAIN_ENTITY_GENERIC_RE = re.compile(
    r'("mainEntityOfPage"\s*:\s*\{.*?"@id"\s*:\s*")([^"]+)(")',
    re.IGNORECASE | re.DOTALL,
)
POSITION_THREE_RE = re.compile(
    r'("@type"\s*:\s*"ListItem"\s*,\s*"position"\s*:\s*3\s*,\s*"name"\s*:\s*"[^"]+"\s*,\s*"item"\s*:\s*")([^"]+)(")',
    re.IGNORECASE | re.DOTALL,
)


def dedupe_self_canonical_tags(text: str, expected_url: str) -> tuple[str, bool]:
    matches = list(CANONICAL_RE.finditer(text))
    self_matches = [m for m in matches if m.group("href") == expected_url]
    if len(self_matches) <= 1:
        return text, False

    changed = False
    kept = False
    rebuilt = []
    last = 0
    for match in matches:
        rebuilt.append(text[last:match.start()])
        tag = match.group("tag")
        if match.group("href") == expected_url:
            if not kept:
                rebuilt.append(tag)
                kept = True
            else:
                changed = True
        else:
            rebuilt.append(tag)
        last = match.end()
    rebuilt.append(text[last:])
    return "".join(rebuilt), changed


def replace_if_needed(pattern: re.Pattern[str], text: str, expected_url: str) -> tuple[str, bool]:
    changed = False

    def repl(match: re.Match[str]) -> str:
        nonlocal changed
        if match.group(2) != expected_url:
            changed = True
            return f"{match.group(1)}{expected_url}{match.group(3)}"
        return match.group(0)

    return pattern.sub(repl, text), changed


def process_file(path: pathlib.Path) -> bool:
    text = path.read_text(encoding="utf-8", errors="ignore")
    expected_url = f"{SITE_PREFIX}{path.relative_to(ROOT).as_posix()}"

    canonical_hrefs = [match.group("href") for match in CANONICAL_RE.finditer(text)]
    if expected_url not in canonical_hrefs:
        return False

    updated = text
    changed_any = False

    updated, changed = dedupe_self_canonical_tags(updated, expected_url)
    changed_any |= changed

    for pattern in (OG_URL_RE, MAIN_ENTITY_RE, POSITION_THREE_RE):
        updated, changed = replace_if_needed(pattern, updated, expected_url)
        changed_any |= changed

    if updated == text:
        # Some files format mainEntityOfPage less predictably; fall back only if needed.
        updated, changed = replace_if_needed(MAIN_ENTITY_GENERIC_RE, updated, expected_url)
        changed_any |= changed

    if changed_any:
        path.write_text(updated, encoding="utf-8", newline="")
    return changed_any


def main() -> None:
    changed_files = []
    for path in ROOT.rglob("*.html"):
        if process_file(path):
            changed_files.append(path.relative_to(ROOT).as_posix())

    print(f"changed_files={len(changed_files)}")
    for rel in changed_files:
        print(rel)


if __name__ == "__main__":
    main()
