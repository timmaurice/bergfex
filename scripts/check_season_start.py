#!/usr/bin/env python3
"""Watch for the point at which refreshing the HTML fixtures becomes worthwhile.

The fixtures were captured mid-winter, so through the summer they describe a page
shape the live site no longer serves. Refreshing them only pays off once resorts
are running properly - not merely reporting, which glaciers do year round.

The test for "running properly" is the integration's own ``evaluate_status``: open
pistes where they are published, and lifts plus snow behind that. Reusing it means
the watcher cannot drift away from what the integration considers open.

Run directly to see where the glaciers and the valley resorts stand:

    PYTHONPATH=. python3 scripts/check_season_start.py
"""

import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from custom_components.bergfex.parser import (  # noqa: E402
    evaluate_status,
    parse_resort_page,
)

# Two questions, two groups, because they are answered weeks apart.
#
# Glaciers start skiing on the first real snowfall, which no calendar predicts -
# late September in a good year, well into October in a poor one. They report snow
# all summer, so only prepared piste tells them apart from summer operation.
#
# Valley resorts follow in late November or December, and only then does a full
# fixture refresh cover the page shape ordinary users see.
GLACIER_RESORTS = {
    "Hintertuxer Gletscher": "/hintertux/schneebericht/",
    "Sölden": "/soelden/schneebericht/",
    "Stubaier Gletscher": "/stubaier-gletscher/schneebericht/",
    "Pitztaler Gletscher": "/pitztalergletscher/schneebericht/",
    "Kitzsteinhorn": "/kitzsteinhorn-kaprun/schneebericht/",
    "Kaunertaler Gletscher": "/kaunertal/schneebericht/",
}

# The resorts we hold fixtures for.
VALLEY_RESORTS = {
    "Serfaus - Fiss - Ladis": "/serfaus-fiss-ladis/schneebericht/",
    "Ankogel": "/ankogel/schneebericht/",
    "Les Saisies": "/les-saisies/schneebericht/",
    "Warth / Schröcken": "/warth-schroecken/schneebericht/",
    "Axamer Lizum": "/axamer-lizum/schneebericht/",
}

RESORT_GROUPS = {"glacier": GLACIER_RESORTS, "valley": VALLEY_RESORTS}

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


# Copied from the snow report's parent page, which is where bergfex puts the
# operating panel. The integration does the same; without it a resort looks
# season-less and the status falls back to lifts and snow alone, which reads a
# summer glacier as open.
PANEL_KEYS = (
    "winter_season_start",
    "winter_season_end",
    "winter_operating_hours_start",
    "winter_operating_hours_end",
    "summer_season_start",
    "summer_season_end",
    "operating_hours_start",
    "operating_hours_end",
)


def resort_status(path: str) -> dict | None:
    """Parse one resort the way the integration does, main page included."""
    html = fetch(path)
    if html is None:
        return None

    data = parse_resort_page(html, path, "at")

    main_path = "/" + "/".join(path.strip("/").split("/")[:-1]) + "/"
    if main_path != path and (main_html := fetch(main_path)):
        main_data = parse_resort_page(main_html, main_path, "at")
        for key in PANEL_KEYS:
            if key in main_data and key not in data:
                data[key] = main_data[key]
        evaluate_status(data)

    return data


def open_resorts(resorts: dict[str, str]) -> list[str]:
    """Names of the resorts in ``resorts`` that are skiable right now."""
    running = []
    for name, path in resorts.items():
        data = resort_status(path)
        if data is None:
            continue
        print(describe(name, data))
        if data.get("status") == "Open":
            running.append(name)
    return running


def main() -> None:
    results = {}
    for group, resorts in RESORT_GROUPS.items():
        print(f"{group.capitalize()} resorts")
        results[group] = open_resorts(resorts)
        print()

    for group, running in results.items():
        if running:
            print(f"{group}: skiing has started at {', '.join(running)}")
        else:
            print(f"{group}: nothing running yet")

    if output := os.environ.get("GITHUB_OUTPUT"):
        with open(output, "a", encoding="utf-8") as handle:
            for group, running in results.items():
                handle.write(f"{group}_started={'true' if running else 'false'}\n")
                handle.write(f"{group}_resorts={', '.join(running)}\n")


if __name__ == "__main__":
    main()
