"""Parse pages captured from the live site *after* bergfex restyled it.

Every other fixture was captured mid-winter, so it can only prove the parser
reads the site as it *was* - which is how the dropped Tailwind ``tw-`` prefix
broke resort-name parsing for months with the suite green throughout.

These three were captured on 21 September 2026 and carry no ``tw-`` class. They
cover the shapes the winter fixtures cannot show at once: a running resort
(Hintertux on its glacier), one between its seasons (Serfaus, every lift turning
for hikers), and a country overview, the page a country's sensors all share.

Deliberately not refreshed with the rest: re-capturing the winter fixtures in
September would replace a populated snow report with an empty one and delete the
coverage that caught the eighteen-language keyword bugs.
"""

from datetime import date, datetime
from pathlib import Path

import pytest

from custom_components.bergfex.parser import (
    evaluate_status,
    parse_overview_data,
    parse_resort_page,
)

FIXTURES = Path(__file__).parent / "fixtures"

LIVE_MARKUP_FIXTURES = (
    "hintertux-glacier-open.html",
    "serfaus-off-season.html",
    "overview-at-off-season.html",
)


def _fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8", errors="replace")


# --- The restyle itself -----------------------------------------------------


@pytest.mark.parametrize("name", LIVE_MARKUP_FIXTURES)
def test_the_tailwind_prefix_is_gone_from_the_live_pages(name):
    """Pins the finding these fixtures exist to record.

    The parser no longer accepts the prefixed spelling, so this is a real alarm:
    if bergfex brought `tw-` back, resort-name parsing would break again. It also
    stops anyone re-capturing these three from an archive of the old markup.
    """
    assert "tw-" not in _fixture(name)


def test_the_resort_name_survives_the_restyle():
    """The exact regression: the heading splits into two spans, and reading the
    whole ``<h1>`` glues the page label onto the name - "SchneeberichtSerfaus -
    Fiss - Ladis". The winter fixtures cannot catch it; this one can.
    """
    data = parse_resort_page(
        _fixture("serfaus-off-season.html"), "/serfaus-fiss-ladis/schneebericht/", "at"
    )

    assert data["resort_name"] == "Serfaus - Fiss - Ladis"
    assert "Schneebericht" not in data["resort_name"]


# --- A resort that is actually running --------------------------------------


def test_the_running_glacier_reports_snow_lifts_and_pistes():
    """Hintertux on 21 September: the first populated snow report of the season.

    Until this fixture the suite had no page showing a resort *running* outside
    midwinter, so nothing proved the restyled page still yields a full reading.
    """
    data = parse_resort_page(
        _fixture("hintertux-glacier-open.html"), "/hintertux/schneebericht/", "at"
    )

    assert data["resort_name"] == "Hintertuxer Gletscher / Hintertux / Zillertal"
    assert data["snow_mountain"] == "25"
    assert data["elevation_mountain"] == 3250
    assert data["lifts_open_count"] == 4
    assert data["lifts_total_count"] == 21
    assert data["operation_status"] == "täglich"
    assert isinstance(data["last_update"], datetime)
    assert data["status"] == "Open"


def test_the_running_glacier_names_its_open_pistes():
    data = parse_resort_page(
        _fixture("hintertux-glacier-open.html"), "/hintertux/schneebericht/", "at"
    )

    names = [piste["name"] for piste in data["open_pistes"]]
    assert names == ["Bichlalm", "Höllensteinhütte"]


def test_a_glacier_with_no_prepared_piste_still_reads_as_open():
    """No ``slopes_open_count`` on the page at all, which is not the same as a
    reported zero: the piste row is absent, so lifts and snow decide.
    """
    data = parse_resort_page(
        _fixture("hintertux-glacier-open.html"), "/hintertux/schneebericht/", "at"
    )

    assert "slopes_open_count" not in data
    assert data["status"] == "Open"


# --- A resort between its two seasons ---------------------------------------


def test_the_off_season_resort_runs_every_lift_and_is_still_closed():
    """Serfaus in September: eleven of eleven lifts for hikers, no snow behind
    them. Open lifts alone must not read as skiable - the case the status rule
    was rewritten for, now shown against a real page rather than a built one.
    """
    data = parse_resort_page(
        _fixture("serfaus-off-season.html"), "/serfaus-fiss-ladis/schneebericht/", "at"
    )

    assert data["lifts_open_count"] == 11
    assert data["lifts_total_count"] == 11
    assert "snow_mountain" not in data
    assert "snow_valley" not in data
    assert data["status"] == "Closed"


def test_the_off_season_resort_keeps_the_year_round_fields():
    """bergfex drops the snow block out of season but not the rest of the page.

    If these go missing too the site was restructured, which is a different
    problem from the season ending - and the one the parser cannot survive.
    """
    data = parse_resort_page(
        _fixture("serfaus-off-season.html"), "/serfaus-fiss-ladis/schneebericht/", "at"
    )

    assert data["region_path"] == "/tirol/"
    assert data["elevation_mountain"] == 2700
    assert data["slopes_total_count"] == 110
    assert isinstance(data["last_update"], datetime)


# --- The page every sensor in a country shares ------------------------------


def test_the_country_overview_parses_a_real_page():
    """``parse_overview_data`` feeds every sensor of a country from one request,
    and had only a hand-written six-row table to prove it worked. This is the
    real Austrian page: 109 resorts, several of them running.
    """
    overview = parse_overview_data(_fixture("overview-at-off-season.html"), lang="at")

    assert len(overview) == 109
    assert all(key.startswith("/") for key in overview)


def test_the_country_overview_reads_the_running_glaciers():
    overview = parse_overview_data(_fixture("overview-at-off-season.html"), lang="at")

    hintertux = overview["/hintertux/schneebericht/"]
    assert hintertux["snow_mountain"] == "25"
    assert hintertux["lifts_open_count"] == 4
    assert hintertux["lifts_total_count"] == 21

    soelden = overview["/soelden/schneebericht/"]
    assert soelden["snow_mountain"] == "22"
    assert soelden["lifts_open_count"] == 7


def test_the_overview_and_the_resort_page_agree_on_the_numbers():
    """The two parsers read the same resort from different pages. The figures
    have to match; the *status* deliberately need not, and the next test says so.
    """
    overview = parse_overview_data(_fixture("overview-at-off-season.html"), lang="at")
    resort = parse_resort_page(
        _fixture("hintertux-glacier-open.html"), "/hintertux/schneebericht/", "at"
    )

    assert (
        overview["/hintertux/schneebericht/"]["snow_mountain"]
        == resort["snow_mountain"]
    )
    assert (
        overview["/hintertux/schneebericht/"]["lifts_open_count"]
        == resort["lifts_open_count"]
    )
    assert (
        overview["/hintertux/schneebericht/"]["lifts_total_count"]
        == resort["lifts_total_count"]
    )


def test_the_overview_status_is_coarser_and_never_reaches_the_sensor():
    """Serfaus is "Open" on the overview and "Closed" on its own page, at the
    same moment: the overview has only the lift icon to go on, while the resort
    page applies the seasonal rule. That disagreement is harmless *because* the
    coordinator takes only ``new_snow`` from the overview - see the merge in
    ``__init__.py``. This test fails if anything ever starts copying the
    overview's status across, which would undo the seasonal rule wholesale.
    """
    overview = parse_overview_data(_fixture("overview-at-off-season.html"), lang="at")
    resort = parse_resort_page(
        _fixture("serfaus-off-season.html"), "/serfaus-fiss-ladis/schneebericht/", "at"
    )

    assert overview["/serfaus-fiss-ladis/schneebericht/"]["status"] == "Open"
    assert resort["status"] == "Closed"


# --- The gap the live instance exposed --------------------------------------


def test_a_running_glacier_reads_closed_once_the_stale_season_is_attached():
    """Hintertux on 21 September 2026: 4 of 21 lifts, 25 cm, two pistes bergfex
    marks open - and the integration calls it Closed.

    The fixture alone reads Open: the season dates live on the main page, and the
    integration only merges them in afterwards.

    What this pins is that a *published* winter window decides, even one that has
    already ended - the page is the authority on its own season. bergfex dropped
    this window hours after the fixture was captured; what happens then is the
    summer-operation step, covered in test_seasonal_status.py.
    """
    data = parse_resort_page(
        _fixture("hintertux-glacier-open.html"), "/hintertux/schneebericht/", "at"
    )
    assert len(data["open_pistes"]) == 2
    assert evaluate_status(data) == "Open"

    # What the coordinator actually hands the rule, season dates included.
    data["winter_season_start"] = date(2025, 9, 27)
    data["winter_season_end"] = date(2026, 7, 19)

    assert evaluate_status(data) == "Closed"
