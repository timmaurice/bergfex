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
    <h1 class="tw-text-4xl"><span>Ski resort</span><span>Test Resort</span></h1>
    <dt>Saison:</dt>
    <dd>13.12.{start_year} - 11.04.{end_year}</dd>
    <dd>
      <div class="status-lifte" title="open lift"></div>
      5 von 10
    </dd>
    """

    data = parse_resort_page(html)
    assert data["season_start"] == date(start_year, 12, 13)
    assert data["season_end"] == date(end_year, 4, 11)
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
    <h1 class="tw-text-4xl"><span>Ski resort</span><span>Test Resort</span></h1>
    <dt>Saison:</dt>
    <dd>13.12.{start_year} – 11.04.{end_year}</dd>
    <dd>
      <div class="status-lifte" title="open lift"></div>
      5 von 10
    </dd>
    """

    data = parse_resort_page(html)
    assert data["season_start"] == date(start_year, 12, 13)
    assert data["season_end"] == date(end_year, 4, 11)
    assert data["status"] == "Open"


def test_time_based_closure_before():
    """Test that resort is closed before operating hours."""
    import datetime
    from unittest.mock import patch

    # Mock now to be 07:00 AM
    mock_now = datetime.datetime(2026, 1, 1, 7, 0, 0)

    html = f"""
    <h1 class="tw-text-4xl"><span>Ski resort</span><span>Test Resort</span></h1>
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
    <h1 class="tw-text-4xl"><span>Ski resort</span><span>Test Resort</span></h1>
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


def test_parse_season_dates_closed():
    """Test parsing of season dates resulting in Closed status."""
    import datetime

    today = datetime.datetime.now().date()
    start_year = today.year - 2
    end_year = today.year - 1

    html = f"""
    <h1 class="tw-text-4xl"><span>Ski resort</span><span>Test Resort</span></h1>
    <dt>Saison:</dt>
    <dd>13.12.{start_year} - 11.04.{end_year}</dd>
    <dd>
      <div class="status-lifte" title="open lift"></div>
      5 von 10
    </dd>
    """

    data = parse_resort_page(html)
    assert data["season_start"] == date(start_year, 12, 13)
    assert data["season_end"] == date(end_year, 4, 11)
    # Lifts are open, but season is over, so status should be Closed.
    assert data["status"] == "Closed"
