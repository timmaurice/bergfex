"""Parse data from Bergfex."""

from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta
from typing import Any

from bs4 import BeautifulSoup

from .const import KEYWORDS

_LOGGER = logging.getLogger(__name__)


def _translate_value(value: str, lang: str) -> str:
    """Translate common Bergfex strings from German to the target language."""
    if not value or lang == "at":
        return value

    keywords = KEYWORDS.get(lang, KEYWORDS["at"])
    translations = keywords.get("values", {})

    translated_value = value
    for de_val, target_val in translations.items():
        if de_val in translated_value:
            translated_value = translated_value.replace(de_val, target_val)

    return translated_value


def parse_bergfex_datetime(date_str: str, lang: str = "at") -> datetime | None:
    """Parse Bergfex date/time strings to datetime objects.

    Handles formats like:
    - "Heute, 11:14" (Today, 11:14)
    - "Gestern, 11:14" (Yesterday, 11:14)
    - "Fr, 28.11., 09:33" (Fri, 28.11., 09:33)
    """
    if not date_str:
        return None

    date_str = date_str.strip()
    # Use Europe/Vienna as default timezone for Bergfex
    try:
        from zoneinfo import ZoneInfo
    except ImportError:
        from backports.zoneinfo import ZoneInfo  # type: ignore

    tz = ZoneInfo("Europe/Vienna")
    now = datetime.now(tz)

    keywords = KEYWORDS.get(lang, KEYWORDS["at"])
    today_kw = keywords.get("today", "heute").lower()
    yesterday_kw = keywords.get("yesterday", "gestern").lower()

    # Handle "Heute" / "Today"
    if date_str.lower().startswith(today_kw):
        time_match = re.search(r"(\d{1,2}):(\d{2})", date_str)
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2))
            return now.replace(hour=hour, minute=minute, second=0, microsecond=0)

    # Handle "Gestern" / "Yesterday"
    elif date_str.lower().startswith(yesterday_kw):
        time_match = re.search(r"(\d{1,2}):(\d{2})", date_str)
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2))
            yesterday = now - timedelta(days=1)
            return yesterday.replace(hour=hour, minute=minute, second=0, microsecond=0)

    # Handle specific date format like "Fr, 28.11., 09:33" or "05.11.2025, 14:40"
    else:
        # Match pattern: optional day name, day.month.[year][.,] time
        # Tries to match dd.mm.yyyy, HH:MM or dd.mm., HH:MM
        date_match = re.search(
            r"(\d{1,2})\.(\d{1,2})\.(?:\s*(\d{4})|\s*(\d{2}))?(?:,|\.)?\s*(\d{1,2}):(\d{2})",
            date_str,
        )
        if date_match:
            day = int(date_match.group(1))
            month = int(date_match.group(2))

            # Check if year is present (group 3 for 4-digit, group 4 for 2-digit)
            year_str = date_match.group(3) or date_match.group(4)

            if year_str:
                year = int(year_str)
                if len(year_str) == 2:
                    year += 2000
            else:
                # Determine the year - if the date is in the future, use current year, otherwise use current year
                year = now.year

            hour = int(date_match.group(5))
            minute = int(date_match.group(6))

            try:
                result = datetime(year, month, day, hour, minute, 0, 0, tzinfo=tz)
                # If no year was parsed and the date is more than 6 months in the future, it's probably from last year
                if not year_str and result > now + timedelta(days=180):
                    result = datetime(
                        year - 1, month, day, hour, minute, 0, 0, tzinfo=tz
                    )
                return result
            except ValueError:
                _LOGGER.debug("Could not parse date: %s", date_str)
                return None

    _LOGGER.debug("Could not parse date string: %s", date_str)
    return None


def parse_overview_data(html: str, lang: str = "at") -> dict[str, dict[str, Any]]:
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

        # Snow Depths (Valley, Mountain) and New Snow from data-value with fallback to text
        def get_val(cell):
            if cell.get("data-value") and cell.get("data-value") != "-":
                return cell["data-value"]
            return cell.text.strip().replace("cm", "").strip()

        area_data["snow_valley"] = _translate_value(get_val(cols[1]), lang)
        area_data["snow_mountain"] = _translate_value(get_val(cols[2]), lang)
        area_data["new_snow"] = _translate_value(get_val(cols[3]), lang)

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
        last_update_text = None
        if "data-value" in cols[5].attrs:
            last_update_text = cols[5]["data-value"]
        else:
            last_update_text = cols[5].text.strip()  # Fallback to text

        # Convert to datetime
        if last_update_text:
            last_update_dt = parse_bergfex_datetime(last_update_text, lang)
            if last_update_dt:
                area_data["last_update"] = last_update_dt

        # Clean up "-" values
        results[area_path] = {k: v for k, v in area_data.items() if v not in ("-", "")}

    return results


def get_text_from_dd(soup: BeautifulSoup, text: str) -> str | None:
    """Get the text from a dd element based on the text of the preceding dt element."""
    dt = soup.find("dt", string=lambda t: t and text in t)
    if dt and (dd := dt.find_next_sibling("dd")):
        return dd.text.strip()
    return None


def parse_resort_page(
    html: str, area_path: str | None = None, lang: str = "at"
) -> dict[str, Any]:
    """Parse the HTML of a single resort page."""
    soup = BeautifulSoup(html, "lxml")
    area_data = {}

    keywords = KEYWORDS.get(lang, KEYWORDS["at"])

    # Resort Name
    h1_tag = soup.find("h1", class_="tw-text-4xl")
    if h1_tag:
        spans = h1_tag.find_all("span")
        if len(spans) > 1:
            area_data["resort_name"] = spans[1].text.strip()

    # Region path from breadcrumbs
    # Try finding by aria-label "Breadcrumb" (newer design)
    breadcrumb_ul = soup.find("ul", attrs={"aria-label": "Breadcrumb"})
    links = []
    if breadcrumb_ul:
        links = breadcrumb_ul.find_all("a")
    else:
        # Fallback to old class if aria-label not found
        breadcrumb_wrapper = soup.find("div", class_="breadcrumb-wrapper")
        if breadcrumb_wrapper:
            links = breadcrumb_wrapper.find_all("a")

    if len(links) >= 3:  # Home, Country, Region, (Resort)
        # Default: Region is second to last link
        region_link = links[-2]

        # If area_path is provided, check if links[-2] is actually the resort link
        # This happens on subpages like /resort/schneebericht/
        if area_path:
            link_href = region_link.get("href", "")
            # If the link href is a prefix of area_path (e.g. /hintertux/ in /hintertux/schneebericht/)
            # then links[-2] is the resort, so region must be links[-3]
            if link_href and link_href != "/" and link_href in area_path:
                if len(links) >= 4:
                    region_link = links[-3]
                    _LOGGER.debug(
                        "Adjusted region link to %s because %s is in area_path %s",
                        region_link.get("href"),
                        link_href,
                        area_path,
                    )

        region_path = region_link.get("href")
        if region_path and region_path.startswith("/") and region_path != "/":
            # Get the part between the first and second slash if it exists, or just after first slash
            parts = region_path.strip("/").split("/")
            if len(parts) > 0:
                area_data["region_path"] = f"/{parts[0]}/"
                _LOGGER.debug("Found region path: %s", area_data["region_path"])

    # Extract keywords
    mountain_kw = keywords.get("mountain")
    valley_kw = keywords.get("valley")
    snow_depth_kw = keywords.get("snow_depth")

    # Snow depths and elevations
    all_big_dts = soup.find_all("dt", class_="big")
    for dt in all_big_dts:
        dt_text = dt.text.strip()
        if keywords["mountain"] in dt_text:
            if dd := dt.find_next_sibling("dd", class_="big"):
                area_data["snow_mountain"] = dd.text.strip().replace("cm", "").strip()
            # Extract mountain elevation from the text like "(Piste, 3.250m)"
            if "(" in dt_text and "m)" in dt_text:
                elevation_text = (
                    dt_text.split("(")[1].split("m)")[0].split(",")[-1].strip()
                )
                # Remove dots from elevation (3.250 -> 3250)
                elevation_clean = elevation_text.replace(".", "").replace(",", "")
                try:
                    area_data["elevation_mountain"] = int(elevation_clean)
                except ValueError:
                    _LOGGER.debug(
                        "Could not parse mountain elevation: %s", elevation_text
                    )
        elif keywords["valley"] in dt_text:
            if dd := dt.find_next_sibling("dd", class_="big"):
                area_data["snow_valley"] = dd.text.strip().replace("cm", "").strip()
            # Extract valley elevation from the text like "(Piste, 1.500m)"
            if "(" in dt_text and "m)" in dt_text:
                elevation_text = (
                    dt_text.split("(")[1].split("m)")[0].split(",")[-1].strip()
                )
                # Remove dots/commas from elevation (1.500 or 1,500 -> 1500)
                elevation_clean = elevation_text.replace(".", "").replace(",", "")
                try:
                    area_data["elevation_valley"] = int(elevation_clean)
                except ValueError:
                    _LOGGER.debug(
                        "Could not parse valley elevation: %s", elevation_text
                    )
        elif keywords["snow_depth"] in dt_text:
            # Fallback for resorts that don't satisfy "Tal" but have "Schneehöhe" (often higher altitude)
            if "snow_valley" not in area_data:
                if dd := dt.find_next_sibling("dd", class_="big"):
                    area_data["snow_valley"] = dd.text.strip().replace("cm", "").strip()
                # Extract elevation from text like "Schneehöhe 1.850m"
                match = re.search(r"(\d+(?:[\.,]\d+)*)m", dt_text)
                if match:
                    elevation_clean = (
                        match.group(1).replace(".", "").replace(",", "").strip()
                    )
                    try:
                        area_data["elevation_valley"] = int(elevation_clean)
                    except ValueError:
                        _LOGGER.debug(
                            "Could not parse fallback valley elevation: %s",
                            match.group(1),
                        )

    # Fallback for snow depths if not found by keywords
    if "snow_mountain" not in area_data or "snow_valley" not in area_data:
        # If we have exactly 2 big DTs, assume 1=Mountain, 2=Valley
        if len(all_big_dts) == 2:
            if "snow_mountain" not in area_data:
                if dd := all_big_dts[0].find_next_sibling("dd", class_="big"):
                    area_data["snow_mountain"] = (
                        dd.text.strip().replace("cm", "").strip()
                    )
            if "snow_valley" not in area_data:
                if dd := all_big_dts[1].find_next_sibling("dd", class_="big"):
                    area_data["snow_valley"] = dd.text.strip().replace("cm", "").strip()
        # If only 1, assume Valley (or only one peak altitude)
        elif len(all_big_dts) == 1 and "snow_valley" not in area_data:
            if dd := all_big_dts[0].find_next_sibling("dd", class_="big"):
                area_data["snow_valley"] = dd.text.strip().replace("cm", "").strip()

    # Last update
    h2_sub = soup.find("div", class_="h2-sub")
    if h2_sub:
        last_update_text = h2_sub.text.strip()
        last_update_dt = parse_bergfex_datetime(last_update_text, lang)
        if last_update_dt:
            area_data["last_update"] = last_update_dt

    # Snow condition (Schneezustand)
    snow_condition = get_text_from_dd(soup, keywords["snow_condition"])
    if snow_condition:
        area_data["snow_condition"] = _translate_value(snow_condition, lang)

    # Last snowfall (Letzter Schneefall Region)
    last_snowfall = get_text_from_dd(soup, keywords["last_snowfall"])
    if last_snowfall:
        area_data["last_snowfall"] = last_snowfall

    # Avalanche warning (Lawinenwarnstufe)
    avalanche_warning = get_text_from_dd(soup, keywords["avalanche"])
    if avalanche_warning:
        # Remove common service names if present
        cleaned = (
            avalanche_warning.replace("Lawinenwarndienst", "")
            .replace("Avalanche Warning Service", "")
            .strip()
        )
        area_data["avalanche_warning"] = _translate_value(cleaned, lang)
    # Lifts & Slopes parsing
    from_kw = keywords.get("from", "von")

    def _parse_counts(text: str, f_kw: str) -> tuple[int | None, int | None]:
        if f_kw in text:
            parts = text.split(f_kw)
            if len(parts) == 2:
                try:
                    open_c = int(parts[0].strip())
                    total_c = int(parts[1].strip().split(" ")[0].strip())
                    return open_c, total_c
                except ValueError:
                    pass
        return None, None

    # Try Lifts by keyword
    lifts_text = get_text_from_dd(soup, keywords.get("lifts", "Offene Lifte"))
    if lifts_text:
        o, t = _parse_counts(lifts_text, from_kw)
        if o is not None:
            area_data["lifts_open_count"] = o
            area_data["lifts_total_count"] = t

    # Try Slopes by keyword
    slopes_dt = soup.find(
        "dt", string=lambda t: t and keywords.get("pistes", "Offene Pisten") in t
    )
    if slopes_dt:
        curr = slopes_dt.next_sibling
        while curr:
            if curr.name == "dt":
                break
            if curr.name == "dd" and "big" in curr.get("class", []):
                text = curr.text.strip()
                if "km" in text:
                    if from_kw in text:
                        parts = text.replace("km", "").replace(",", ".").split(from_kw)
                        if len(parts) == 2:
                            try:
                                o_km = float(parts[0].strip())
                                t_km = float(parts[1].strip())
                                area_data["slopes_open_km"] = (
                                    int(o_km) if o_km.is_integer() else o_km
                                )
                                area_data["slopes_total_km"] = (
                                    int(t_km) if t_km.is_integer() else t_km
                                )
                            except ValueError:
                                pass
                else:
                    o, t = _parse_counts(text, from_kw)
                    if o is not None:
                        area_data["slopes_open_count"] = o
                        area_data["slopes_total_count"] = t
            curr = curr.next_sibling

    # Fallback for Lifts/Slopes using status-lifte divs
    if "lifts_open_count" not in area_data or "slopes_open_count" not in area_data:
        for div in soup.find_all("div", class_="status-lifte"):
            title = div.get("title", "").lower()
            dd = div.find_parent("dd")
            if not dd:
                continue
            text = dd.text.strip()
            is_lift = any(
                w in title for w in ["lift", "remont", "impiant", "open lift"]
            )
            is_slope = any(w in title for w in ["pist", "piste", "open pist"])

            for f_kw in [from_kw, "von", "of", "de", "di"]:
                o, t = _parse_counts(text, f_kw)
                if o is not None:
                    if is_lift and "lifts_open_count" not in area_data:
                        area_data["lifts_open_count"] = o
                        area_data["lifts_total_count"] = t
                    elif is_slope and "slopes_open_count" not in area_data:
                        area_data["slopes_open_count"] = o
                        area_data["slopes_total_count"] = t
                    break

    # Slope condition (Pistenzustand)
    slope_condition = get_text_from_dd(soup, keywords["slope_condition"])
    if slope_condition:
        area_data["slope_condition"] = _translate_value(slope_condition, lang)

    # Status
    if area_data.get("lifts_open_count", 0) > 0:
        area_data["status"] = "Open"
    else:
        area_data["status"] = "Closed"

    return {k: v for k, v in area_data.items() if v not in ("-", "")}


def parse_snow_forecast_images(html: str, page_num: int) -> dict[str, str]:
    """
    Parse snow forecast page to extract image URLs.

    Args:
        html: HTML content of the page
        page_num: Page number (0-5)

    Returns:
        dict with 'daily_forecast_url', 'daily_caption' and optionally 'summary_url', 'summary_caption'
    """
    soup = BeautifulSoup(html, "lxml")
    forecast_imgs = soup.find_all(class_="snowforecast-img")

    result = {}

    # First image is always the daily forecast (24h)
    if forecast_imgs:
        first_a = forecast_imgs[0].find("a")
        if first_a and first_a.get("href"):
            result["daily_forecast_url"] = first_a["href"]
            result["daily_caption"] = first_a.get("data-caption", "")

    # Last image is summary (for pages 1-5)
    if page_num > 0 and len(forecast_imgs) > 1:
        last_a = forecast_imgs[-1].find("a")
        if last_a and last_a.get("href"):
            result["summary_url"] = last_a["href"]
            result["summary_caption"] = last_a.get("data-caption", "")

    return result
