from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from bs4 import BeautifulSoup
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    BASE_URL,
    CONF_COUNTRY,
    CONF_DOMAIN,
    CONF_LANGUAGE,
    CONF_SKI_AREA,
    CONF_WEBHOOK_URL,
    CONF_TYPE,
    COUNTRIES,
    COUNTRIES_CROSS_COUNTRY,
    DOMAIN,
    KEYWORDS,
    SUPPORTED_LANGUAGES,
    TYPE_ALPINE,
    TYPE_CROSS_COUNTRY,
)

_LOGGER = logging.getLogger(__name__)


async def get_ski_areas(
    hass: HomeAssistant, country_path: str, domain: str = BASE_URL
) -> dict[str, str]:
    """Fetch the list of ski areas from Bergfex."""
    try:
        session = async_get_clientsession(hass)
        url = f"{domain}{country_path}"
        async with session.get(url, allow_redirects=True) as response:
            response.raise_for_status()
            html = await response.text()
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("table", class_="snow") or soup.find(
            "table", class_="status-table"
        )
        if not table:
            _LOGGER.error(
                "Could not find ski area table with class 'snow' or 'status-table' on overview page."
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
        """Handle the initial step (language selection)."""
        if user_input is not None:
            self._data[CONF_LANGUAGE] = user_input[CONF_LANGUAGE]
            self._data[CONF_DOMAIN] = SUPPORTED_LANGUAGES[user_input[CONF_LANGUAGE]][
                "domain"
            ]
            return await self.async_step_type()

        language_options = {
            code: lang["name"] for code, lang in SUPPORTED_LANGUAGES.items()
        }
        language_schema = vol.Schema(
            {vol.Required(CONF_LANGUAGE, default="at"): vol.In(language_options)}
        )

        return self.async_show_form(
            step_id="user",
            data_schema=language_schema,
        )

    async def async_step_type(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the type selection step."""
        if user_input is not None:
            self._data[CONF_TYPE] = user_input[CONF_TYPE]
            return await self.async_step_country()

        return self.async_show_form(
            step_id="type",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_TYPE, default=TYPE_ALPINE
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[TYPE_ALPINE, TYPE_CROSS_COUNTRY],
                            mode=selector.SelectSelectorMode.LIST,
                            translation_key="report_type",
                        )
                    )
                }
            ),
        )

    async def async_step_country(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the country selection step."""
        lang = self._data.get(CONF_LANGUAGE, "at")
        keywords = KEYWORDS.get(lang, KEYWORDS["at"])
        translated_countries = keywords.get("countries", {})

        # Create localized mapping: { "Translated Name": "Original Key" }
        country_options = {
            translated_countries.get(name, name): name for name in COUNTRIES.keys()
        }

        if user_input is not None:
            # Map back to original country name
            self._data[CONF_COUNTRY] = country_options[user_input[CONF_COUNTRY]]
            return await self.async_step_ski_area_list()

        country_schema = vol.Schema(
            {
                vol.Required(
                    CONF_COUNTRY,
                    default=translated_countries.get("Österreich", "Österreich"),
                ): vol.In(list(country_options.keys()))
            }
        )

        return self.async_show_form(
            step_id="country",
            data_schema=country_schema,
        )

    async def async_step_ski_area_list(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the ski area selection step (list) - router."""
        if self._data.get(CONF_TYPE) == TYPE_CROSS_COUNTRY:
            return await self.async_step_ski_area_list_cross_country(user_input)
        return await self.async_step_ski_area_list_alpine(user_input)

    async def async_step_ski_area_list_alpine(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle alpine ski area selection."""
        return await self._async_step_ski_area_list_logic(
            user_input, step_id="ski_area_list_alpine"
        )

    async def async_step_ski_area_list_cross_country(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle cross country ski area selection."""
        return await self._async_step_ski_area_list_logic(
            user_input, step_id="ski_area_list_cross_country"
        )

    async def _async_step_ski_area_list_logic(
        self, user_input: dict[str, Any] | None = None, step_id: str = "ski_area_list"
    ) -> FlowResult:
        """Handle the ski area selection step (list) logic."""
        errors = {}
        country_name = self._data[CONF_COUNTRY]

        # Get localized country name for display
        lang = self._data.get(CONF_LANGUAGE, "at")
        keywords = KEYWORDS.get(lang, KEYWORDS["at"])
        translated_countries = keywords.get("countries", {})
        display_country_name = translated_countries.get(country_name, country_name)

        is_cross_country = self._data.get(CONF_TYPE) == TYPE_CROSS_COUNTRY
        country_path = (
            COUNTRIES_CROSS_COUNTRY[country_name]
            if is_cross_country
            else COUNTRIES[country_name]
        )
        domain = self._data[CONF_DOMAIN]
        ski_areas = await get_ski_areas(self.hass, country_path, domain)

        if user_input is not None:
            ski_area_path = user_input.get(CONF_SKI_AREA)
            manual_path = user_input.get("manual_path")
            webhook_url = user_input.get("webhook_url")

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
                        CONF_LANGUAGE: self._data[CONF_LANGUAGE],
                        CONF_DOMAIN: domain,
                        CONF_WEBHOOK_URL: webhook_url,
                        CONF_TYPE: self._data.get(CONF_TYPE, TYPE_ALPINE),
                        "name": ski_area_name,  # Human-readable
                        "url": f"{domain}{ski_area_path}",
                    },
                )

        if not ski_areas:
            errors["base"] = "no_areas_found"
            return self.async_show_form(
                step_id=step_id,
                errors=errors,
                description_placeholders={
                    "country": display_country_name,
                    "url": f"{domain}{country_path}",
                },
            )

        data_schema = vol.Schema(
            {
                vol.Optional(CONF_SKI_AREA): vol.In(ski_areas),
                vol.Optional("manual_path"): str,
                vol.Optional("webhook_url"): str,
            }
        )

        return self.async_show_form(
            step_id=step_id,
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "country": display_country_name,
                "url": f"{domain}{country_path}",
            },
        )
