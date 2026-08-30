"""Tests for the season watcher.

Its whole job is to not fire early. A false alarm every autumn would train the
maintainer to ignore it, at which point it is worse than nothing.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import check_season_start as watcher  # noqa: E402

from custom_components.bergfex.parser import parse_resort_page  # noqa: E402


def test_reference_resorts_exclude_glaciers():
    """Glaciers report all summer, so they cannot signal the season starting."""
    glaciers = ("hintertux", "soelden", "sölden", "stubai", "pitztal", "schnalstal", "kaunertal")
    for name, path in watcher.REFERENCE_RESORTS.items():
        haystack = f"{name} {path}".lower()
        assert not any(g in haystack for g in glaciers), name


def test_reference_resorts_have_fixtures_or_a_test_entry():
    """The point is to know when refreshing the fixtures pays off."""
    assert len(watcher.REFERENCE_RESORTS) >= 3
    for path in watcher.REFERENCE_RESORTS.values():
        assert path.startswith("/") and path.endswith("/schneebericht/")


def test_a_summer_page_does_not_count_as_open():
    """Serfaus in August: every lift running for hikers, one piste, no snow."""
    html = """
    <h1 class="tw-text-4xl"><span>Schneebericht</span><span>Serfaus</span></h1>
    <dd><div class="status-lifte" title="open lift"></div>11 von 11</dd>
    <dd><div class="status-lifte" title="open piste"></div>1 von 110</dd>
    """
    assert parse_resort_page(html, "/serfaus/", "at")["status"] == "Closed"


def test_a_winter_page_counts_as_open():
    html = """
    <h1 class="tw-text-4xl"><span>Schneebericht</span><span>Serfaus</span></h1>
    <dt class="big">Berg (Piste, 2.700m)</dt>
    <dd class="big">75 cm</dd>
    <dd><div class="status-lifte" title="open lift"></div>37 von 38</dd>
    <dd><div class="status-lifte" title="open piste"></div>71 von 104</dd>
    """
    assert parse_resort_page(html, "/serfaus/", "at")["status"] == "Open"


def test_describe_survives_a_page_with_nothing_on_it():
    assert "?" in watcher.describe("Nowhere", {})
