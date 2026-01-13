from custom_components.bergfex.parser import (
    parse_cross_country_resort_page,
    parse_cross_country_overview_data,
)
from custom_components.bergfex.const import KEYWORDS
from datetime import datetime
import aiohttp
import pytest


def test_parse_cross_country_achensee_overview():
    html = """
    <div class="tailwind">
    <h1 class="tw-text-4xl">
    <span class="tw-font-normal">Langlaufen</span>
    <span>Achensee - Tirols Sport & Vital Park</span>
    </h1>
    </div>
    <div class="contentbox box-container">
    <div class="box-header">Loipen Bericht</div>
    <div class="box-content">
    <div class="report-info">
    <div class="report-value"><span class="big">58,5</span> km</div>
    <div class="report-label">Klassisch</div>
    </div>
    <div class="report-info">
    <div class="report-value"><span class="big">82,5</span> km</div>
    <div class="report-label">Skating</div>
    </div>
    </div>
    """
    data = parse_cross_country_resort_page(html, lang="at")
    assert data["resort_name"] == "Langlaufen Achensee - Tirols Sport & Vital Park"
    assert data["classical_open_km"] == 58.5
    assert data["skating_open_km"] == 82.5
    assert data["status"] == "Open"


def test_parse_cross_country_detailed():
    html = """
    <dl class="dl-horizontal dt-large loipen-bericht">
        <dt>Loipenbericht</dt>
        <dd>Heute, 11:52</dd>
        
        <dt>Betrieb</dt>
        <dd>täglich</dd>
        
        <dt class="big">Loipen klassisch</dt>
        <dd class="big">
            58,5 km
            <span class="default-size">gespurt</span>
            <span class="default-size">(sehr gut)</span>
        </dd>
        
        <dt class="big">Loipen Skating</dt>
        <dd class="big">
            82,5 km 
            <span class="default-size">gespurt</span>
            <span class="default-size">(sehr gut)</span>
        </dd>
    </dl>
    """
    data = parse_cross_country_resort_page(html, lang="at")
    assert data["classical_open_km"] == 58.5
    assert data["classical_condition"] == "gespurt (sehr gut)"
    assert data["skating_open_km"] == 82.5
    assert data["skating_condition"] == "gespurt (sehr gut)"
    assert data["operation_status"] == "täglich"
    assert isinstance(data["last_update"], datetime)
    assert data["status"] == "Open"


@pytest.mark.parametrize("lang", list(KEYWORDS.keys()))
def test_parse_cross_country_all_languages(lang):
    """Test parsing cross country data for all supported languages."""
    kw = KEYWORDS[lang]

    # Use fallback if keyword missing (shouldn't happen with our recent update)
    trail_report = kw.get("trail_report", "Loipenbericht")
    operation = kw.get("operation", "Betrieb")
    classical = kw.get("classical", "klassisch")
    # Add some text around to simulate real headers like "Loipen klassisch" vs "klassisch"
    # But for the test, we want to ensure the KEYWORD matches.
    # If the regex in parser is `classical_kw.lower() in dt.text.lower()`,
    # then putting the keyword directly in DT is sufficient.
    classical_header = f"Prefix {classical} Suffix"
    skating = kw.get("skating", "Skating")
    skating_header = f"Prefix {skating} Suffix"
    today = kw.get("today", "heute")

    html = f"""
    <dl class="dl-horizontal dt-large loipen-bericht">
        <dt>{trail_report}</dt>
        <dd>{today}, 09:30</dd>
        
        <dt>{operation}</dt>
        <dd>Open</dd>
        
        <dt class="big">{classical_header}</dt>
        <dd class="big">12.5 km</dd>
        
        <dt class="big">{skating_header}</dt>
        <dd class="big">15,0 km</dd>
    </dl>
    """

    data = parse_cross_country_resort_page(html, lang=lang)

    assert data["classical_open_km"] == 12.5, f"Failed classical open for {lang}"
    assert data["skating_open_km"] == 15.0, f"Failed skating open for {lang}"
    assert isinstance(data.get("last_update"), datetime), f"Failed date for {lang}"
    assert data.get("operation_status"), f"Failed operation for {lang}"


def test_parse_cross_country_overview_page():
    """Test parsing the cross-country overview page for total trail lengths."""
    html = """
    <table class="status-table">
        <tbody>
            <tr>
                <td><a href="/deutschland/bayrischzell/">Bayrischzell</a></td>
                <td>...</td>
                <td>14,7 / 30,0 km</td>
                <td>14,7 / 30,0 km</td>
                <td>...</td>
            </tr>
            <tr>
                <td><a href="/oesterreich/achensee/">Achensee</a></td>
                <td>...</td>
                <td>58,5 / 100 km</td>
                <td>82,5 / 120 km</td>
                <td>...</td>
            </tr>
            <tr>
                <td><a href="/deutschland/another-resort/">Another Resort</a></td>
                <td>...</td>
                <td>10 km</td>
                <td>...</td>
            </tr>
        </tbody>
    </table>
    """
    data = parse_cross_country_overview_data(html, lang="at")
    assert "/deutschland/bayrischzell/" in data
    assert data["/deutschland/bayrischzell/"]["classical_total_km"] == 30.0
    assert data["/deutschland/bayrischzell/"]["name"] == "Bayrischzell"
    assert data["/deutschland/bayrischzell/"]["skating_total_km"] == 30.0
    assert "/oesterreich/achensee/" in data
    assert data["/oesterreich/achensee/"]["classical_total_km"] == 100.0
    assert data["/oesterreich/achensee/"]["skating_total_km"] == 120.0
    assert "/deutschland/another-resort/" in data
    assert data["/deutschland/another-resort/"]["classical_total_km"] == 10.0
    assert "skating_total_km" not in data["/deutschland/another-resort/"]


def test_merged_cross_country_parsing():
    """Test merging data from resort and overview pages."""
    detail_html = """
    <dl class="dl-horizontal dt-large loipen-bericht">
        <dt>Loipenbericht</dt>
        <dd>Heute, 11:52</dd>
        <dt class="big">Loipen klassisch</dt>
        <dd class="big">14,7 km</dd>
        <dt class="big">Loipen Skating</dt>
        <dd class="big">14,7 km</dd>
    </dl>
    """
    overview_html = """
    <table class="status-table">
        <tbody>
            <tr>
                <td><a href="/deutschland/bayrischzell/">Bayrischzell</a></td>
                <td>...</td>
                <td>14,7 / 30,0 km</td>
                <td>14,7 / 30,0 km</td>
                <td>...</td>
            </tr>
        </tbody>
    </table>
    """
    area_path = "/deutschland/bayrischzell/"

    # Parse detail page
    parsed_data = parse_cross_country_resort_page(detail_html, lang="de")
    assert "classical_open_km" in parsed_data

    # Parse overview page and merge
    overview_data = parse_cross_country_overview_data(overview_html, lang="de")

    # Manually find the matching key, since overview might have more entries
    matching_key = None
    for key in overview_data:
        if area_path in key:
            matching_key = key
            break

    assert matching_key is not None, f"Area path {area_path} not found in overview data"

    parsed_data.update(overview_data[matching_key])

    assert "classical_total_km" in parsed_data
    assert "skating_total_km" in parsed_data
    assert parsed_data["classical_open_km"] == 14.7
    assert parsed_data["skating_open_km"] == 14.7
    assert parsed_data["classical_total_km"] == 30.0
    assert parsed_data["skating_total_km"] == 30.0
