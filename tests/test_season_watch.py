"""Tests for the season watcher.

Its whole job is to not fire early. A false alarm every autumn would train the
maintainer to ignore it, at which point it is worse than nothing.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import check_season_start as watcher  # noqa: E402

from custom_components.bergfex.parser import parse_resort_page  # noqa: E402

GLACIER_WORDS = (
    "hintertux",
    "soelden",
    "sölden",
    "stubai",
    "pitztal",
    "kitzstein",
    "kaunertal",
)


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


# --- A resort it cannot judge must not be called open -----------------------
#
# Issue #37: the scheduled run hit 429 on /hintertux/, so the operating panel
# never merged and evaluate_status never re-ran. The verdict left standing came
# from the snow report alone - three lifts turning and 305 cm of old snow - and
# the watcher announced that glacier skiing had started while the same page
# showed no prepared piste at all.

SUBPAGE = """
<html><body>
  <h1 class="text-4xl"><span>Skigebiet</span><span>Hintertux</span></h1>
  <dl>
    <dt>Berg (Piste)</dt><dd>305 cm</dd>
    <dt>Offene Lifte</dt><dd>3 von 20</dd>
  </dl>
</body></html>
"""

MAIN = """
<html><body>
  <h1 class="text-4xl"><span>Skigebiet</span><span>Hintertux</span></h1>
  <div class="pt-6">
    <div class="block" x-show="tab == 'winter'">
      <h3>Saison</h3><div class="txt_markup"><p>19.09.2026 - 10.05.2027</p></div>
      <h3>Betrieb</h3><div class="txt_markup"><p>08:15 - 16:00</p></div>
    </div>
  </div>
</body></html>
"""


def _with_pages(monkeypatch, pages):
    """Serve `pages` by path; anything absent fetches as a failure."""
    monkeypatch.setattr(watcher, "fetch", lambda path, **kw: pages.get(path))


def test_a_resort_whose_main_page_fails_is_not_judged(monkeypatch):
    """The reported bug: a 429 on the main page produced a false Open."""
    _with_pages(monkeypatch, {"/hintertux/schneebericht/": SUBPAGE})

    assert watcher.resort_status("/hintertux/schneebericht/") is None


def test_such_a_resort_is_left_out_of_the_started_list(monkeypatch):
    """open_resorts is what the workflow turns into an issue."""
    _with_pages(monkeypatch, {"/hintertux/schneebericht/": SUBPAGE})

    started = watcher.open_resorts({"Hintertux": "/hintertux/schneebericht/"})

    assert started == []


def test_the_panel_is_still_used_when_both_pages_load(monkeypatch):
    """The guard must not cost the normal path its season data."""
    _with_pages(
        monkeypatch,
        {"/hintertux/schneebericht/": SUBPAGE, "/hintertux/": MAIN},
    )

    data = watcher.resort_status("/hintertux/schneebericht/")

    assert data is not None
    assert "winter_season_start" in data


def test_a_missing_subpage_is_still_skipped(monkeypatch):
    _with_pages(monkeypatch, {"/hintertux/": MAIN})

    assert watcher.resort_status("/hintertux/schneebericht/") is None
