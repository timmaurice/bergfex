"""Tests for the season watcher.

Its whole job is to not fire early. A false alarm every autumn would train the
maintainer to ignore it, at which point it is worse than nothing.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import check_season_start as watcher  # noqa: E402

from custom_components.bergfex.parser import parse_resort_page  # noqa: E402


GLACIER_WORDS = ("hintertux", "soelden", "sölden", "stubai", "pitztal", "kitzstein", "kaunertal")


def test_the_two_groups_are_kept_apart():
    """They answer different questions weeks apart.

    A glacier in the valley list would fire the fixture-refresh issue in
    September, when ordinary resorts are still on grass.
    """
    for name, path in watcher.VALLEY_RESORTS.items():
        assert not any(word in f"{name} {path}".lower() for word in GLACIER_WORDS), name

    for name, path in watcher.GLACIER_RESORTS.items():
        assert any(word in f"{name} {path}".lower() for word in GLACIER_WORDS), name


def test_both_groups_are_worth_checking():
    assert len(watcher.GLACIER_RESORTS) >= 3
    assert len(watcher.VALLEY_RESORTS) >= 3
    for resorts in watcher.RESORT_GROUPS.values():
        for path in resorts.values():
            assert path.startswith("/") and path.endswith("/schneebericht/")


def test_the_panel_keys_carry_the_season():
    """Without them a summer glacier parses season-less and reads as open."""
    assert "winter_season_start" in watcher.PANEL_KEYS
    assert "winter_season_end" in watcher.PANEL_KEYS


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
