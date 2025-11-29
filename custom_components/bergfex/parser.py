"""Parse data from Bergfex."""

from __future__ import annotations

import logging
from typing import Any

from bs4 import BeautifulSoup

_LOGGER = logging.getLogger(__name__)


def parse_overview_data(html: str) -> dict[str, dict[str, Any]]:
    """Parse the HTML of the overview page and return a dict of all ski areas."""
    soup = BeautifulSoup(html, "lxml")
    results = {}

    table = soup.find("table", class_="snow")
    if not table:
        _LOGGER.warning("Could not find overview data table with class 'snow'")
        return {}

    for row in table.find_all("tr")[1:]:  # Skip header row
        cols = row.find_all("td")
        if len(cols) < 6:
            continue

        link = cols[0].find("a")
        if not (link and link.get("href")):
            continue

        area_path = link["href"]
        area_data = {}

        # Snow Depths (Valley, Mountain) and New Snow from data-value
        area_data["snow_valley"] = cols[1].get("data-value")
        area_data["snow_mountain"] = cols[2].get("data-value")
        area_data["new_snow"] = cols[3].get("data-value")

        # Lifts and Status (from column 4)
        lifts_cell = cols[4]
        status_div = lifts_cell.find("div", class_="icon-status")
        if status_div:
            classes = status_div.get("class", [])
            if "icon-status1" in classes:
                area_data["status"] = "Open"
            elif "icon-status0" in classes:
                area_data["status"] = "Closed"
            else:
                area_data["status"] = "Unknown"

        lifts_raw = lifts_cell.text.strip()
        lifts_open = None
        lifts_total = None

        if "/" in lifts_raw:
            parts = lifts_raw.split("/")
            if len(parts) == 2:
                try:
                    lifts_open = int(parts[0].strip())
                except ValueError:
                    _LOGGER.debug(
                        "Could not parse lifts_open_count: %s", parts[0].strip()
                    )
                try:
                    lifts_total = int(parts[1].strip())
                except ValueError:
                    _LOGGER.debug(
                        "Could not parse lifts_total_count: %s", parts[1].strip()
                    )
        elif lifts_raw.isdigit():
            try:
                lifts_open = int(lifts_raw)
            except ValueError:
                _LOGGER.debug("Could not parse lifts_open_count: %s", lifts_raw)

        if lifts_open is not None:
            area_data["lifts_open_count"] = lifts_open
        if lifts_total is not None:
            area_data["lifts_total_count"] = lifts_total

        # Last Update - Get timestamp from data-value on the <td> if available
        if "data-value" in cols[5].attrs:
            area_data["last_update"] = cols[5]["data-value"]
        else:
            area_data["last_update"] = cols[5].text.strip()  # Fallback to text

        # Clean up "-" values
        results[area_path] = {k: v for k, v in area_data.items() if v not in ("-", "")}

    return results


def get_text_from_dd(soup: BeautifulSoup, text: str) -> str | None:
    """Get the text from a dd element based on the text of the preceding dt element."""
    dt = soup.find("dt", string=lambda t: t and text in t)
    if dt and (dd := dt.find_next_sibling("dd")):
        return dd.text.strip()
    return None


def parse_resort_page(html: str) -> dict[str, Any]:
    """Parse the HTML of a single resort page."""
    soup = BeautifulSoup(html, "lxml")
    area_data = {}

    # Resort Name
    h1_tag = soup.find("h1", class_="tw-text-4xl")
    if h1_tag:
        spans = h1_tag.find_all("span")
        if len(spans) > 1:
            area_data["resort_name"] = spans[1].text.strip()

    # Snow depths and elevations
    all_big_dts = soup.find_all("dt", class_="big")
    for dt in all_big_dts:
        dt_text = dt.text.strip()
        if "Berg" in dt_text:
            if dd := dt.find_next_sibling("dd", class_="big"):
                area_data["snow_mountain"] = dd.text.strip().replace("cm", "").strip()
            # Extract mountain elevation from the text like "(Piste, 3.250m)"
            if "(" in dt_text and "m)" in dt_text:
                elevation_text = (
                    dt_text.split("(")[1].split("m)")[0].split(",")[-1].strip()
                )
                # Remove dots from elevation (3.250 -> 3250)
                elevation_clean = elevation_text.replace(".", "")
                try:
                    area_data["elevation_mountain"] = int(elevation_clean)
                except ValueError:
                    _LOGGER.debug(
                        "Could not parse mountain elevation: %s", elevation_text
                    )
        elif "Tal" in dt_text:
            if dd := dt.find_next_sibling("dd", class_="big"):
                area_data["snow_valley"] = dd.text.strip().replace("cm", "").strip()
            # Extract valley elevation from the text like "(Piste, 1.500m)"
            if "(" in dt_text and "m)" in dt_text:
                elevation_text = (
                    dt_text.split("(")[1].split("m)")[0].split(",")[-1].strip()
                )
                # Remove dots from elevation (1.500 -> 1500)
                elevation_clean = elevation_text.replace(".", "")
                try:
                    area_data["elevation_valley"] = int(elevation_clean)
                except ValueError:
                    _LOGGER.debug(
                        "Could not parse valley elevation: %s", elevation_text
                    )

    # Last update
    h2_sub = soup.find("div", class_="h2-sub")
    if h2_sub:
        area_data["last_update"] = h2_sub.text.strip()

    # Snow condition (Schneezustand)
    snow_condition = get_text_from_dd(soup, "Schneezustand")
    if snow_condition:
        area_data["snow_condition"] = snow_condition

    # Last snowfall (Letzter Schneefall Region)
    last_snowfall = get_text_from_dd(soup, "Letzter Schneefall")
    if last_snowfall:
        area_data["last_snowfall"] = last_snowfall

    # Avalanche warning (Lawinenwarnstufe)
    avalanche_warning = get_text_from_dd(soup, "Lawinenwarnstufe")
    if avalanche_warning:
        # Remove the link text if present
        area_data["avalanche_warning"] = avalanche_warning.replace(
            "Lawinenwarndienst", ""
        ).strip()

    # Lifts
    lifts_text = get_text_from_dd(soup, "Offene Lifte")
    if lifts_text and "von" in lifts_text:
        parts = lifts_text.split("von")
        if len(parts) == 2:
            try:
                area_data["lifts_open_count"] = int(parts[0].strip())
                area_data["lifts_total_count"] = int(
                    parts[1].strip().split(" ")[0].strip()
                )
            except ValueError:
                _LOGGER.debug("Could not parse lifts: %s", lifts_text)

    # Slopes - find all dd elements after "Offene Pisten" dt
    slopes_dt = soup.find("dt", string=lambda t: t and "Offene Pisten" in t)
    if slopes_dt:
        # The first dd after "Offene Pisten" contains km info
        dd_km = slopes_dt.find_next_sibling("dd", class_="big")
        if dd_km:
            km_text = dd_km.text.strip()
            # Extract numbers like "46 km von 64 km"
            if "von" in km_text:
                parts = km_text.replace("km", "").split("von")
                if len(parts) == 2:
                    try:
                        area_data["slopes_open_km"] = int(parts[0].strip())
                        area_data["slopes_total_km"] = int(parts[1].strip())
                    except ValueError:
                        _LOGGER.debug("Could not parse slope km: %s", km_text)

        # The next dd contains count info
        if dd_km:
            dd_count = dd_km.find_next_sibling("dd", class_="big")
            if dd_count:
                count_text = dd_count.text.strip()
                # Extract numbers like "19 von 29"
                if "von" in count_text:
                    parts = count_text.split("von")
                    if len(parts) == 2:
                        try:
                            area_data["slopes_open_count"] = int(parts[0].strip())
                            area_data["slopes_total_count"] = int(parts[1].strip())
                        except ValueError:
                            _LOGGER.debug("Could not parse slope count: %s", count_text)

    # Slope condition (Pistenzustand)
    slope_condition = get_text_from_dd(soup, "Pistenzustand")
    if slope_condition:
        area_data["slope_condition"] = slope_condition

    # New snow
    new_snow_div = soup.find("div", class_="heading heading-ne desktop-only")
    if new_snow_div and (h1_div := new_snow_div.find("div", class_="h1")):
        area_data["new_snow"] = (
            h1_div.find("span").text.strip().replace("cm", "").strip()
        )

    # Status
    if area_data.get("lifts_open_count", 0) > 0:
        area_data["status"] = "Open"
    else:
        area_data["status"] = "Closed"

    return {k: v for k, v in area_data.items() if v not in ("-", "")}
