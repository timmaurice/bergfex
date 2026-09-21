"""Parse pages captured from the live site *after* bergfex restyled it.

Every other fixture in ``tests/fixtures/`` was captured mid-winter, and that is
what made the suite blind: bergfex dropped the Tailwind ``tw-`` class prefix
site-wide, resort-name parsing broke for months, and all 300-odd tests stayed
green because the saved markup still carried the old classes. A frozen fixture
can only ever prove the parser reads the site as it *was*.

These three were captured on 21 September 2026, once the glaciers had started
running, and they carry no ``tw-`` class anywhere - the prefix is gone from
every page bergfex serves. They cover the three shapes the integration meets,
which the winter fixtures cannot show at once:

* a **running resort** - Hintertux on its glacier, reporting snow, lifts and
  open pistes outside the main season;
* an **off-season resort** - Serfaus between its two seasons, running every lift
  for hikers with no snow report behind them;
* a **country overview** - the one page a country's sensors all share, and which
  until now had no captured page at all, only a six-row table written by hand.

They are deliberately *not* refreshed with the rest. Re-capturing the winter
fixtures in September would replace a populated snow report with an empty one
and silently delete the coverage that caught the eighteen-language keyword bugs.
Refresh those when the valley resorts are running - ``scripts/refresh_fixtures.py``
does it - and keep these as the record of what the restyled page looks like.
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

    The parser no longer accepts the prefixed spelling at all, so this is now a
    real alarm rather than a note: if bergfex brought `tw-` back, resort-name
    parsing would break again and this is where it shows. It also stops anyone
    "helpfully" re-capturing these three from an archive of the old markup,
    which would quietly restore the blind spot.
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

    The fixture alone reads Open, because the season dates are not on the snow
    report; the integration fetches them from the main page and caches them, and
    only then does the rule see them. bergfex was still publishing the *finished*
    2025/26 winter period, 27.09.2025 - 19.07.2026, because the new one is not
    announced yet - so "today is outside the winter season" is drawn from last
    season's dates.

    ``evaluate_status`` says in its own docstring that "where bergfex reports
    open pistes, those decide - that is prepared terrain", but it reads only the
    "x of y" summary row, which this page does not print. The two open piste rows
    it does print are ignored.

    What this pins is that a *published* winter window decides, even one that has
    already ended - the page is the authority on its own season, and a resort
    outside it is not skiing. bergfex dropped this particular window hours after
    the fixture was captured, and the same rule then read Open, which was wrong
    for a different reason; that case is the summer-operation step, covered in
    test_seasonal_status.py. The two tests are the two halves of the same rule:
    here a season is published and decides, there none is and the summer period
    answers instead.
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
