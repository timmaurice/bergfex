import pytest
from custom_components.bergfex.parser import (
    parse_overview_data,
    parse_resort_page,
    parse_snow_forecast_images,
)
from pathlib import Path
from datetime import datetime


def test_parse_snow_forecast_images():
    """Test parsing of snow forecast images."""
    html = """
    <div class="snowforecast-img">
        <a href="https://vcdn.bergfex.at/images/resized/8b/daily.jpg" data-caption="Daily Caption">
            <img src="..." alt="Daily Alt">
        </a>
    </div>
    <div class="snowforecast-img">
        <a href="https://vcdn.bergfex.at/images/resized/5d/12h.jpg" data-caption="12h Caption">
            <img src="..." alt="12h Alt">
        </a>
    </div>
    <div class="snowforecast-img">
        <a href="https://vcdn.bergfex.at/images/resized/7b/summary.jpg" data-caption="Summary Caption">
            <img src="..." alt="Summary Alt">
        </a>
    </div>
    """
    
    # Test page 0 (no summary expected, but if present it might be parsed if logic allows, 
    # but our logic checks page_num > 0 for summary)
    result_page_0 = parse_snow_forecast_images(html, 0)
    assert result_page_0["daily_forecast_url"] == "https://vcdn.bergfex.at/images/resized/8b/daily.jpg"
    assert result_page_0["daily_caption"] == "Daily Caption"
    assert "summary_url" not in result_page_0
    
    # Test page 1 (summary expected)
    result_page_1 = parse_snow_forecast_images(html, 1)
    assert result_page_1["daily_forecast_url"] == "https://vcdn.bergfex.at/images/resized/8b/daily.jpg"
    assert result_page_1["daily_caption"] == "Daily Caption"
    assert result_page_1["summary_url"] == "https://vcdn.bergfex.at/images/resized/7b/summary.jpg"
    assert result_page_1["summary_caption"] == "Summary Caption"


@pytest.fixture
def lelex_crozet_html():
    fixture_path = Path(__file__).parent / "fixtures" / "lelex-crozet.html"
    with open(fixture_path, "r") as f:
        return f.read()


@pytest.fixture
def les_saisies_at_html():
    fixture_path = Path(__file__).parent / "fixtures" / "les-saisies-at.html"
    with open(fixture_path, "r") as f:
        return f.read()


@pytest.fixture
def les_saisies_en_html():
    fixture_path = Path(__file__).parent / "fixtures" / "les-saisies-en.html"
    with open(fixture_path, "r") as f:
        return f.read()


@pytest.fixture
def les_saisies_fr_html():
    fixture_path = Path(__file__).parent / "fixtures" / "les-saisies-fr.html"
    with open(fixture_path, "r") as f:
        return f.read()


def test_parse_lelex_crozet_snow_data(lelex_crozet_html):
    data = parse_resort_page(lelex_crozet_html, lang="at")

    assert data["resort_name"] == "Lélex - Crozet"
    assert data["snow_mountain"] == "15"
    # Updated to expect timezone-aware datetime (Europe/Vienna)
    try:
        from zoneinfo import ZoneInfo
    except ImportError:
        from backports.zoneinfo import ZoneInfo

    tz = ZoneInfo("Europe/Vienna")
    expected_dt = datetime(2025, 11, 5, 14, 40, tzinfo=tz)
    assert data["snow_valley"] == "5"
    assert data["lifts_open_count"] == 8
    assert data["lifts_total_count"] == 10
    assert data["status"] == "Open"
    assert data["last_update"] == expected_dt


def test_parse_les_saisies_at_snow_data(les_saisies_at_html):
    """Test parsing of German Les Saisies page."""
    data = parse_resort_page(les_saisies_at_html, lang="at")
    assert data["resort_name"] == "Les Saisies"
    assert "snow_mountain" in data
    assert "snow_valley" in data
    assert "lifts_open_count" in data
    assert "lifts_total_count" in data
    assert data["status"] in ["Open", "Closed"]


def test_parse_les_saisies_en_snow_data(les_saisies_en_html):
    """Test parsing of English Les Saisies page."""
    data = parse_resort_page(les_saisies_en_html, lang="en")
    assert data["resort_name"] == "Les Saisies"
    assert "snow_mountain" in data
    assert "snow_valley" in data
    assert "lifts_open_count" in data
    assert "lifts_total_count" in data
    assert data["status"] in ["Open", "Closed"]


def test_parse_les_saisies_fr_snow_data(les_saisies_fr_html):
    """Test parsing of French Les Saisies page."""
    data = parse_resort_page(les_saisies_fr_html, lang="fr")
    assert data["resort_name"] == "Les Saisies"
    assert "snow_mountain" in data
    assert "snow_valley" in data
    assert "lifts_open_count" in data
    assert "lifts_total_count" in data
    assert data["status"] in ["Open", "Closed"]


def test_parse_overview_data_robust():
    """Test that overview data parsing is robust with and without data-value."""
    html = """
    <table class="snow">
        <tr><th>Resort</th><th>Valley</th><th>Mountain</th><th>New</th><th>Lifts</th><th>Update</th></tr>
        <tr>
            <td><a href="/resort1/">Resort 1</a></td>
            <td data-value="10">10 cm</td>
            <td data-value="50">50 cm</td>
            <td data-value="5">5 cm</td>
            <td>5/10 <div class="icon-status icon-status1"></div></td>
            <td data-value="Heute, 10:00">Heute, 10:00</td>
        </tr>
        <tr>
            <td><a href="/resort2/">Resort 2</a></td>
            <td>20 cm</td>
            <td>80 cm</td>
            <td>10 cm</td>
            <td>2/5 <div class="icon-status icon-status0"></div></td>
            <td>Gestern, 09:00</td>
        </tr>
    </table>
    """
    results = parse_overview_data(html)
    
    # Resort 1 (with data-value)
    assert results["/resort1/"]["snow_valley"] == "10"
    assert results["/resort1/"]["snow_mountain"] == "50"
    assert results["/resort1/"]["new_snow"] == "5"
    assert results["/resort1/"]["status"] == "Open"
    
    # Resort 2 (without data-value, using text fallback)
    assert results["/resort2/"]["snow_valley"] == "20"
    assert results["/resort2/"]["snow_mountain"] == "80"
    assert results["/resort2/"]["new_snow"] == "10"
    assert results["/resort2/"]["status"] == "Closed"
