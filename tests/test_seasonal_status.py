import pytest
from datetime import date
from custom_components.bergfex.parser import parse_resort_page


def test_parse_season_dates_open():
    """Test parsing of season dates resulting in Open status."""
    import datetime

    today = datetime.datetime.now().date()
    start_year = today.year - 1
    end_year = today.year + 1

    html = f"""
    <h1 class="text-4xl"><span>Ski resort</span><span>Test Resort</span></h1>
    <dt class="big">Berg (Piste, 3.250m)</dt>
    <dd class="big">80 cm</dd>
    <div class="block" x-show="tab == 'winter'">
      <h3>Saison</h3><p>13.12.{start_year} - 11.04.{end_year}</p>
    </div>
    <dd>
      <div class="status-lifte" title="open lift"></div>
      5 von 10
    </dd>
    """

    data = parse_resort_page(html)
    assert data["winter_season_start"] == date(start_year, 12, 13)
    assert data["winter_season_end"] == date(end_year, 4, 11)
    assert data["lifts_open_count"] == 5
    assert data["status"] == "Open"


def test_parse_season_dates_en_dash():
    """Test parsing of season dates with en-dash."""
    import datetime

    today = datetime.datetime.now().date()
    start_year = today.year - 1
    end_year = today.year + 1

    # Using en-dash (–) instead of hyphen (-)
    html = f"""
    <h1 class="text-4xl"><span>Ski resort</span><span>Test Resort</span></h1>
    <dt class="big">Berg (Piste, 3.250m)</dt>
    <dd class="big">80 cm</dd>
    <div class="block" x-show="tab == 'winter'">
      <h3>Saison</h3><p>13.12.{start_year} – 11.04.{end_year}</p>
    </div>
    <dd>
      <div class="status-lifte" title="open lift"></div>
      5 von 10
    </dd>
    """

    data = parse_resort_page(html)
    assert data["winter_season_start"] == date(start_year, 12, 13)
    assert data["winter_season_end"] == date(end_year, 4, 11)
    assert data["status"] == "Open"


def test_time_based_closure_before():
    """Test that resort is closed before operating hours."""
    import datetime
    from unittest.mock import patch

    # Mock now to be 07:00 AM
    mock_now = datetime.datetime(2026, 1, 1, 7, 0, 0)

    html = f"""
    <h1 class="text-4xl"><span>Ski resort</span><span>Test Resort</span></h1>
    <dt>Betrieb:</dt>
    <dd>08:30 - 16:45</dd>
    <dd>
      <div class="status-lifte" title="open lift"></div>
      5 von 10
    </dd>
    """

    with patch("custom_components.bergfex.parser.datetime") as mock_datetime:
        mock_datetime.now.return_value = mock_now
        mock_datetime.strptime = datetime.datetime.strptime
        data = parse_resort_page(html)

    assert data["operating_hours_start"] == "08:30"
    assert data["operating_hours_end"] == "16:45"
    assert data["status"] == "Closed"


def test_time_based_closure_after():
    """Test that resort is closed after operating hours."""
    import datetime
    from unittest.mock import patch

    # Mock now to be 18:00 PM
    mock_now = datetime.datetime(2026, 1, 1, 18, 0, 0)

    html = f"""
    <h1 class="text-4xl"><span>Ski resort</span><span>Test Resort</span></h1>
    <dt>Betrieb:</dt>
    <dd>08:30 - 16:45</dd>
    <dd>
      <div class="status-lifte" title="open lift"></div>
      5 von 10
    </dd>
    """

    with patch("custom_components.bergfex.parser.datetime") as mock_datetime:
        mock_datetime.now.return_value = mock_now
        mock_datetime.strptime = datetime.datetime.strptime
        data = parse_resort_page(html)

    assert data["status"] == "Closed"


def test_out_of_season_without_piste_figures_is_closed():
    """Old snow under a running lift is not skiing; the season is the fallback."""
    import datetime

    today = datetime.datetime.now().date()
    start_year = today.year - 2
    end_year = today.year - 1

    html = f"""
    <h1 class="text-4xl"><span>Ski resort</span><span>Test Resort</span></h1>
    <dt class="big">Berg (Piste, 3.250m)</dt>
    <dd class="big">80 cm</dd>
    <div class="block" x-show="tab == 'winter'">
      <h3>Saison</h3><p>13.12.{start_year} - 11.04.{end_year}</p>
    </div>
    <dd>
      <div class="status-lifte" title="open lift"></div>
      5 von 10
    </dd>
    """

    data = parse_resort_page(html)
    assert data["winter_season_start"] == date(start_year, 12, 13)
    assert data["winter_season_end"] == date(end_year, 4, 11)
    # The Hintertux case: lifts turning, metres of old glacier snow, but no piste
    # figures and the winter period long over. Its operator shows 0 km prepared.
    assert data["status"] == "Closed"


def test_reported_pistes_decide_when_they_exist():
    """The most specific signal wins: prepared terrain beats lifts and snow."""
    html = """
    <h1 class="text-4xl"><span>Ski resort</span><span>Test Resort</span></h1>
    <dt class="big">Berg (Piste, 3.250m)</dt>
    <dd class="big">180 cm</dd>
    <dd><div class="status-lifte" title="open lift"></div>8 von 10</dd>
    <dd><div class="status-lifte" title="open piste"></div>0 von 40</dd>
    """
    assert parse_resort_page(html)["status"] == "Closed"


def test_one_open_piste_is_enough():
    html = """
    <h1 class="text-4xl"><span>Ski resort</span><span>Test Resort</span></h1>
    <dt class="big">Berg (Piste, 3.250m)</dt>
    <dd class="big">180 cm</dd>
    <dd><div class="status-lifte" title="open lift"></div>8 von 10</dd>
    <dd><div class="status-lifte" title="open piste"></div>1 von 40</dd>
    """
    assert parse_resort_page(html)["status"] == "Open"


def test_lifts_without_snow_are_not_open():
    """Summer operation: a lift runs for hikers and there is nothing to ski on."""
    html = """
    <h1 class="text-4xl"><span>Ski resort</span><span>Test Resort</span></h1>
    <dt class="big">Tal (Piste, 1.495m)</dt>
    <dd class="big">0 cm</dd>
    <dd>
      <div class="status-lifte" title="open lift"></div>
      1 von 15
    </dd>
    """

    data = parse_resort_page(html)
    assert data["status"] == "Closed"


def test_snow_without_a_running_lift_is_not_open():
    html = """
    <h1 class="text-4xl"><span>Ski resort</span><span>Test Resort</span></h1>
    <dt class="big">Berg (Piste, 3.250m)</dt>
    <dd class="big">180 cm</dd>
    """

    data = parse_resort_page(html)
    assert data["status"] == "Closed"


def test_valley_snow_alone_is_enough():
    """Some areas only report a valley depth."""
    html = """
    <h1 class="text-4xl"><span>Ski resort</span><span>Test Resort</span></h1>
    <dt class="big">Tal (Piste, 1.400m)</dt>
    <dd class="big">40 cm</dd>
    <dd>
      <div class="status-lifte" title="open lift"></div>
      5 von 10
    </dd>
    """

    data = parse_resort_page(html)
    assert data["status"] == "Open"


# --- Summer operation, where the winter season has no date yet ---------------


def _summer_only_glacier(offset_start: int, offset_end: int) -> str:
    """A glacier running lifts on snow, with a summer period and no winter one.

    What bergfex serves for Hintertux in September: the winter tab carries
    operating hours and the words "Aktuell KEIN Skibetrieb! Start in die
    Wintersaison 2026/27: Sobald es die Schneelage zulaesst" - a season with no
    dates, because the opening depends on snowfall nobody can predict.
    """
    import datetime

    today = datetime.datetime.now().date()
    start = today + datetime.timedelta(days=offset_start)
    end = today + datetime.timedelta(days=offset_end)
    return f"""
    <h1 class="text-4xl"><span>Skigebiet</span><span>Hintertuxer Gletscher</span></h1>
    <dt class="big">Berg (Piste, 3.250m)</dt>
    <dd class="big">25 cm</dd>
    <div class="block" x-show="tab == 'summer'">
      <h3>Saison</h3><p>{start.strftime('%d.%m.%Y')} - {end.strftime('%d.%m.%Y')}</p>
    </div>
    <dd>
      <div class="status-lifte" title="open lift"></div>
      4 von 21
    </dd>
    """


def test_summer_operation_is_not_skiing():
    """Four lifts turning on 25 cm of old glacier snow, inside the summer period.

    bergfex says so itself on the same page - "Aktuell KEIN Skibetrieb" - and
    the card should name the summer season rather than call the resort open.
    """
    data = parse_resort_page(_summer_only_glacier(-135, +12))

    assert "winter_season_start" not in data
    assert data["lifts_open_count"] == 4
    assert data["snow_mountain"] == "25"
    assert data["status"] == "Closed"


def test_a_summer_period_that_has_ended_decides_nothing():
    """Past the summer period with no winter one in sight, there is nothing left
    to judge against, so lifts and snow stand alone - the long-standing fallback.
    """
    data = parse_resort_page(_summer_only_glacier(-200, -10))

    assert data["status"] == "Open"


def test_a_winter_season_still_outranks_the_summer_one():
    """The ordering is the whole safeguard.

    A glacier that skis through the summer publishes a winter period covering
    today, and that has to keep deciding - otherwise this rule would close every
    glacier for the months both periods overlap.
    """
    import datetime

    today = datetime.datetime.now().date()
    winter_start = today - datetime.timedelta(days=30)
    winter_end = today + datetime.timedelta(days=200)
    summer_start = today - datetime.timedelta(days=100)
    summer_end = today + datetime.timedelta(days=12)

    html = f"""
    <h1 class="text-4xl"><span>Skigebiet</span><span>Schnalstal</span></h1>
    <dt class="big">Berg (Piste, 3.200m)</dt>
    <dd class="big">6 cm</dd>
    <div class="block" x-show="tab == 'winter'">
      <h3>Saison</h3><p>{winter_start.strftime('%d.%m.%Y')} - {winter_end.strftime('%d.%m.%Y')}</p>
    </div>
    <div class="block" x-show="tab == 'summer'">
      <h3>Saison</h3><p>{summer_start.strftime('%d.%m.%Y')} - {summer_end.strftime('%d.%m.%Y')}</p>
    </div>
    <dd>
      <div class="status-lifte" title="open lift"></div>
      2 von 11
    </dd>
    """

    data = parse_resort_page(html)

    assert data["winter_season_start"] == winter_start
    assert data["summer_season_end"] == summer_end
    assert data["status"] == "Open"


def test_reported_pistes_still_outrank_both_periods():
    """Prepared terrain is the most specific signal there is and stays first."""
    import datetime

    today = datetime.datetime.now().date()
    summer_start = today - datetime.timedelta(days=100)
    summer_end = today + datetime.timedelta(days=12)

    html = f"""
    <h1 class="text-4xl"><span>Skigebiet</span><span>Hintertuxer Gletscher</span></h1>
    <dt class="big">Berg (Piste, 3.250m)</dt>
    <dd class="big">25 cm</dd>
    <div class="block" x-show="tab == 'summer'">
      <h3>Saison</h3><p>{summer_start.strftime('%d.%m.%Y')} - {summer_end.strftime('%d.%m.%Y')}</p>
    </div>
    <dd><div class="status-lifte" title="open lift"></div>4 von 21</dd>
    <dd><div class="status-lifte" title="open piste"></div>3 von 60</dd>
    """

    data = parse_resort_page(html)

    assert data["slopes_open_count"] == 3
    assert data["status"] == "Open"
