#!/usr/bin/env python3
"""Re-capture the HTML fixtures in ``tests/fixtures/`` from the live pages.

A frozen fixture is only evidence for as long as it resembles what the site
serves. The url to re-fetch each one from is already in the file - bergfex stamps
every page with a canonical link - so this reads it back out rather than keeping
a second list that could drift. A fixture with no canonical link was written by
hand rather than captured, and is left alone.

Usage::

    python scripts/refresh_fixtures.py --dry-run   # what would be fetched
    python scripts/refresh_fixtures.py             # fetch and overwrite
    python scripts/refresh_fixtures.py serfaus-at  # just these

Run the suite afterwards and read the failures as a report on parser drift.
"""

from __future__ import annotations

import argparse
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

FIXTURES = Path(__file__).resolve().parents[1] / "tests" / "fixtures"

# A real browser string. bergfex serves a reduced page to obvious robots, and a
# fixture captured from the reduced page would quietly weaken every test built
# on it.
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)

_CANONICAL = re.compile(
    r"""<link[^>]*\brel=["']canonical["'][^>]*\bhref=["']([^"']+)["']""",
    re.IGNORECASE,
)

# Polite spacing between requests. Nothing here is urgent and this runs against
# somebody else's site.
DELAY_SECONDS = 1.0


def canonical_url(html: str) -> str | None:
    """The url bergfex stamped on the page, or None for a hand-written fixture."""
    match = _CANONICAL.search(html)
    return match.group(1) if match else None


def fetch(url: str, retries: int = 3) -> str:
    """Fetch a page, retrying transient failures."""
    last: Exception | None = None
    for attempt in range(retries):
        if attempt:
            time.sleep(2**attempt)
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "de,en;q=0.7",
                "Cache-Control": "no-cache",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                charset = response.headers.get_content_charset() or "utf-8"
                return response.read().decode(charset, errors="replace")
        except (urllib.error.URLError, OSError) as err:  # noqa: PERF203
            last = err
    raise RuntimeError(f"{url}: {last}")


def selected(names: list[str]) -> list[Path]:
    """The fixtures to work on - all of them, or the ones named on the command line."""
    everything = sorted(FIXTURES.glob("*.html"))
    if not names:
        return everything
    wanted = {name.removesuffix(".html") for name in names}
    chosen = [path for path in everything if path.stem in wanted]
    missing = wanted - {path.stem for path in chosen}
    if missing:
        sys.exit(f"no such fixture: {', '.join(sorted(missing))}")
    return chosen


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "names", nargs="*", help="fixture names; default is all of them"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="resolve and report the urls without fetching anything",
    )
    args = parser.parse_args()

    captured: list[tuple[Path, str]] = []
    handwritten: list[Path] = []

    for path in selected(args.names):
        url = canonical_url(path.read_text(encoding="utf-8", errors="replace"))
        if url is None:
            handwritten.append(path)
        else:
            captured.append((path, url))

    for path in handwritten:
        print(f"skip  {path.name:24} hand-written, no canonical link")

    if args.dry_run:
        for path, url in captured:
            print(f"would fetch {path.name:24} {url}")
        return 0

    failures: list[str] = []
    for index, (path, url) in enumerate(captured):
        if index:
            time.sleep(DELAY_SECONDS)
        before = len(path.read_bytes())
        try:
            html = fetch(url)
        except RuntimeError as err:
            failures.append(str(err))
            print(f"FAIL  {path.name:24} {err}")
            continue
        path.write_text(html, encoding="utf-8")
        after = len(path.read_bytes())
        print(f"ok    {path.name:24} {before:>7} -> {after:>7} bytes  {url}")

    print(
        f"\n{len(captured) - len(failures)}/{len(captured)} refreshed, "
        f"{len(handwritten)} hand-written left alone"
    )
    if failures:
        print("Nothing was written for the failures above; rerun to retry them.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
