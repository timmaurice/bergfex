import logging
from typing import Any

import voluptuous as vol
from bs4 import BeautifulSoup
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import BASE_URL, CONF_COUNTRY, CONF_SKI_AREA, COUNTRIES, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def get_ski_areas(hass: HomeAssistant, country_path: str) -> dict[str, str]:
    """Fetch the list of ski areas from Bergfex."""
    try:
        session = async_get_clientsession(hass)
        async with session.get(
            f"{BASE_URL}{country_path}", allow_redirects=True
        ) as response:
            response.raise_for_status()
            html = await response.text()
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("table", class_="snow")
        if not table:
            _LOGGER.error(
                "Could not find ski area table with class 'snow' on overview page."
            )
            return {}

        ski_areas = {}
        for row in table.find_all("tr")[1:]:  # Skip header row
            link = row.find("a")
            if link and link.get("href"):
                name = link.text.strip()
                # The URL path is the unique identifier
                url_path = link["href"]
                if name and url_path:
                    ski_areas[url_path] = name
        return ski_areas
    except Exception as exc:
        _LOGGER.error("Error fetching ski areas: %s", exc)
        return {}


class BergfexConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Bergfex."""

    VERSION = 1
    _data: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step (country selection)."""
        if user_input is not None:
            self._data[CONF_COUNTRY] = user_input[CONF_COUNTRY]
            return await self.async_step_ski_area()

        country_schema = vol.Schema(
            {vol.Required(CONF_COUNTRY): vol.In(list(COUNTRIES.keys()))}
        )

        return self.async_show_form(
            step_id="user",
            data_schema=country_schema,
        )

    async def async_step_ski_area(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the ski area selection step."""
        errors = {}
        country_name = self._data[CONF_COUNTRY]
        country_path = COUNTRIES[country_name]
        ski_areas = await get_ski_areas(self.hass, country_path)

        if user_input is not None:
            ski_area_path = user_input.get(CONF_SKI_AREA)
            manual_path = user_input.get("manual_path")

            if not ski_area_path and not manual_path:
                errors["base"] = "config.error.no_selection"
            else:
                if manual_path:
                    ski_area_path = manual_path
                    if not ski_area_path.startswith("/"):
                        ski_area_path = f"/{ski_area_path}"
                    if not ski_area_path.endswith("/schneebericht/"):
                        ski_area_path = f"/{ski_area_path.strip('/')}/schneebericht/"

                # Keep ski_area_path as the unique ID
                ski_area_name = ski_areas.get(
                    ski_area_path, ski_area_path.strip("/").split("/")[-2]
                )

                return self.async_create_entry(
                    title=ski_area_name,
                    data={
                        CONF_SKI_AREA: ski_area_path,  # URL path as key
                        CONF_COUNTRY: country_name,
                        "name": ski_area_name,  # Human-readable
                        "url": f"{BASE_URL}{ski_area_path}",
                    },
                )

        if not ski_areas:
            errors["base"] = "config.error.no_areas_found"
            return self.async_show_form(
                step_id="ski_area",
                errors=errors,
            )

        data_schema = vol.Schema(
            {
                vol.Optional(CONF_SKI_AREA): vol.In(ski_areas),
                vol.Optional("manual_path"): str,
            }
        )

        return self.async_show_form(
            step_id="ski_area",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={"country": country_name},
        )
