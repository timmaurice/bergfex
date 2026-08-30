#!/usr/bin/env python3
"""Watch for the point at which refreshing the HTML fixtures becomes worthwhile.

The fixtures were captured mid-winter, so through the summer they describe a page
shape the live site no longer serves. Refreshing them only pays off once resorts
are running properly - not merely reporting, which glaciers do year round.

The test for "running properly" is the integration's own ``evaluate_status``: open
pistes where they are published, and lifts plus snow behind that. Reusing it means
the watcher cannot drift away from what the integration considers open.

Run directly to see where each reference resort stands:

    PYTHONPATH=. python3 scripts/check_season_start.py
"""

import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from custom_components.bergfex.parser import parse_resort_page  # noqa: E402

# The resorts we hold fixtures for. Deliberately no glaciers: they report all
# summer, and the question here is whether the ordinary season has begun.
REFERENCE_RESORTS = {
    "Serfaus - Fiss - Ladis": "/serfaus-fiss-ladis/schneebericht/",
    "Ankogel": "/ankogel/schneebericht/",
    "Les Saisies": "/les-saisies/schneebericht/",
    "Warth / Schröcken": "/warth-schroecken/schneebericht/",
    "Axamer Lizum": "/axamer-lizum/schneebericht/",
}

BASE_URL = "https://www.bergfex.at"
USER_AGENT = "Mozilla/5.0 (compatible; bergfex-integration-season-watch/1.0)"


def fetch(path: str) -> str | None:
    request = urllib.request.Request(BASE_URL + path, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read().decode("utf-8", "ignore")
    except (urllib.error.URLError, TimeoutError) as err:
        print(f"  ! {path}: {err}")
        return None


def describe(name: str, data: dict) -> str:
    return (
        f"  {name:<24} {data.get('status', '?'):<7} "
        f"lifts={data.get('lifts_open_count')}/{data.get('lifts_total_count')} "
        f"pistes={data.get('slopes_open_count')}/{data.get('slopes_total_count')} "
        f"snow={data.get('snow_mountain')}"
    )


def main() -> None:
    print("Checking whether the reference resorts have opened\n")

    open_resorts = []
    for name, path in REFERENCE_RESORTS.items():
        html = fetch(path)
        if html is None:
            continue
        data = parse_resort_page(html, path, "at")
        print(describe(name, data))
        if data.get("status") == "Open":
            open_resorts.append(name)

    started = bool(open_resorts)
    print()
    if started:
        print(f"Season has started at: {', '.join(open_resorts)}")
        print("Time to refresh the fixtures.")
    else:
        print("No reference resort is running yet.")

    # Consumed by the workflow, which decides whether to raise an issue.
    if summary := os.environ.get("GITHUB_OUTPUT"):
        with open(summary, "a", encoding="utf-8") as handle:
            handle.write(f"season_started={'true' if started else 'false'}\n")
            handle.write(f"open_resorts={', '.join(open_resorts)}\n")


if __name__ == "__main__":
    main()
