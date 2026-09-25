from __future__ import annotations

import logging
import re
from typing import Any
from urllib.parse import urlsplit

import aiohttp
import voluptuous as vol
from bs4 import BeautifulSoup
from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.core import HomeAssistant, callback
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
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
    MIN_UPDATE_INTERVAL,
    MAX_UPDATE_INTERVAL,
)
from .coordinator import detail_page_url

_LOGGER = logging.getLogger(__name__)


SNOW_REPORT_SEGMENT = "schneebericht"

# A bergfex host, with or without a scheme and with any subdomain: "bergfex.at",
# "www.bergfex.at", "de.bergfex.at". Anything else is left alone, so a resort
# path is never mistaken for a host.
_BERGFEX_HOST = re.compile(r"^(?:[\w-]+\.)*bergfex\.[a-z]{2,}(?::\d+)?$", re.IGNORECASE)

# Pages that hang off a resort path rather than naming a resort. A path made of
# nothing but these names no resort, and the resort's own name is the segment in
# front of them.
_SUBPAGE_SEGMENTS = frozenset({SNOW_REPORT_SEGMENT, "loipen", "langlaufen"})

# How long the reconfigure step waits for the area page on the new domain. The
# user is looking at a spinner meanwhile, so this is far shorter than a poll's.
_PAGE_CHECK_TIMEOUT = aiohttp.ClientTimeout(total=15)


def language_options() -> dict[str, str]:
    """Return the language selector's choices: {code: name in that language}."""
    return {code: lang["name"] for code, lang in SUPPORTED_LANGUAGES.items()}


async def async_page_loads(hass: HomeAssistant, url: str) -> bool:
    """Return whether bergfex serves `url`, following redirects.

    Any failure counts - no connection, a timeout, or a status that is not a
    success, which is how bergfex answers a path it does not know.
    """
    session = async_get_clientsession(hass)
    try:
        async with session.get(
            url, allow_redirects=True, timeout=_PAGE_CHECK_TIMEOUT
        ) as response:
            response.raise_for_status()
    except (aiohttp.ClientError, TimeoutError) as err:
        _LOGGER.debug("Area page %s did not load: %s", url, err)
        return False
    return True


class InvalidWebhookUrl(ValueError):
    """Raised for a webhook that is not an http(s) url with a host.

    The field is free text and whatever lands in it is POSTed to on every single
    poll. A typo therefore does not surface in the flow, where the user could
    still fix it, but as an error line in the log every few minutes forever.
    """


def validate_webhook_url(webhook_url: str) -> str:
    """Return the webhook url, or raise if it is not one.

    Deliberately strict about the scheme: aiohttp will happily be handed a
    "file://" or "ftp://" target, and the resort data is posted outward, so the
    destination should be one the user meant.
    """
    candidate = webhook_url.strip()
    parts = urlsplit(candidate)
    if parts.scheme not in ("http", "https") or not parts.netloc:
        raise InvalidWebhookUrl(webhook_url)
    return candidate


class InvalidSkiAreaPath(ValueError):
    """Raised for hand-entered input that names no resort.

    "bergfex.at", "/" or a bare domain are a valid address, just not one that
    points at a resort - there is nothing to complete them into, so the flow has
    to say so instead of building a path that 404s.
    """


def normalize_ski_area_path(manual_path: str, is_cross_country: bool = False) -> str:
    """Turn hand-entered input into the path the ski area list would have produced.

    Users usually paste a full bergfex URL. Only the path is portable - it is
    identical on every domain - so it is what the entry stores and what
    identifies the resort. Everything that can differ between two ways of naming
    one resort has to be folded away here, or the duplicate check the unique id
    exists for is defeated: the host, the query string and fragment, the trailing
    slash a
    copied url routinely lacks, and case - bergfex serves every resort path in
    lower case (see the hrefs in tests/fixtures), so folding it is safe.

    Raises InvalidSkiAreaPath if what is left names no resort.
    """
    candidate = manual_path.strip()

    # A query string or fragment belongs to the address bar, not to the path -
    # and it can be present with or without a host, so strip it either way.
    candidate = candidate.split("#", 1)[0]
    candidate = candidate.split("?", 1)[0]

    if "//" in candidate:
        candidate = urlsplit(candidate).path
    else:
        # urlsplit only splits off a host after a "//", so a pasted
        # "de.bergfex.at/ischgl/" would otherwise keep the host in the path.
        host, _, rest = candidate.partition("/")
        if _BERGFEX_HOST.match(host):
            candidate = f"/{rest}"

    segments = [segment for segment in candidate.lower().split("/") if segment]

    # Compare the last segment, not the whole string: "/ischgl/schneebericht"
    # already names the snow report, it is only missing its trailing slash.
    if not is_cross_country and segments[-1:] != [SNOW_REPORT_SEGMENT]:
        segments.append(SNOW_REPORT_SEGMENT)

    if not segments or all(segment in _SUBPAGE_SEGMENTS for segment in segments):
        raise InvalidSkiAreaPath(manual_path)

    return f"/{'/'.join(segments)}/"


def ski_area_name_from_path(ski_area_path: str) -> str:
    """Fall back to the resort slug when the list has no name for a path.

    A hand-entered resort is not in the fetched list, so this is the only name
    the entry gets. Guarded because a short path used to raise IndexError mid-flow.
    """
    segments = [segment for segment in ski_area_path.split("/") if segment]
    while len(segments) > 1 and segments[-1] in _SUBPAGE_SEGMENTS:
        segments.pop()
    return segments[-1] if segments else ski_area_path.strip("/")


def entry_area_name(entry: config_entries.ConfigEntry) -> str:
    """Return the resort name an entry was created with.

    Every entry the flow writes carries "name", so this only falls back for one
    hand-edited or restored from a backup predating the key.

    The fallback is the slug from the resort path, which is what the flow itself
    writes when the list has no name - exact for a hand-entered resort, not
    necessarily for one taken from the list ("Solden" vs "soelden"). Since
    legacy_unique_id_prefixes derives migration prefixes from this name, a
    prefix that misses simply
    matches no entity and leaves it under its old id, untouched - the same place
    an un-migrated entity sits today. Guessing wrong therefore costs nothing,
    while the alternative, the raw path, would match no legacy prefix at all and
    would also surface in the log and the device name as "/oesterreich/ischgl/".
    """
    name = entry.data.get("name")
    if name:
        return name
    return ski_area_name_from_path(entry.data.get(CONF_SKI_AREA, ""))


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

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return OptionsFlowHandler()

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

        language_schema = vol.Schema(
            {vol.Required(CONF_LANGUAGE, default="at"): vol.In(language_options())}
        )

        return self.async_show_form(
            step_id="user",
            data_schema=language_schema,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Move an existing entry to another bergfex language.

        The language picks the bergfex domain, and both live in the entry's data.
        The options flow used to write them, which is what an options flow is
        not for, and relied on an update listener for the reload.

        Only the language, the domain and the url cached from them move. The
        resort path is identical on every bergfex domain, and the country is
        stored under its German key (the one COUNTRIES is keyed on), whatever
        language it was picked in - so neither is language-dependent. The path is
        also what the entry's unique id, every entity's unique id and the
        device's identifier are built from, which is why none of them change.
        The stored name is left alone too: it is the entry's title and seeded the
        entity ids, and the device name follows the parsed page after the reload
        anyway, unless the user renamed it.
        """
        try:
            entry = self._get_reconfigure_entry()
        except config_entries.UnknownEntry:
            # The entry was deleted while this form was open.
            return self.async_abort(reason="unknown_entry")

        errors: dict[str, str] = {}
        language = entry.data.get(CONF_LANGUAGE, "at")

        if user_input is not None:
            language = user_input[CONF_LANGUAGE]
            domain = SUPPORTED_LANGUAGES[language]["domain"]
            area_path = entry.data[CONF_SKI_AREA]

            # Check the page the coordinator is about to poll, so a resort that
            # one domain does not list leaves the entry working on the old one
            # instead of reloading into a setup that keeps failing.
            page_url = detail_page_url(
                domain, area_path, entry.data.get(CONF_TYPE, TYPE_ALPINE)
            )
            if not await async_page_loads(self.hass, page_url):
                errors["base"] = "cannot_connect"
            else:
                _LOGGER.debug(
                    "Switching %s to language %s (%s)", entry.title, language, domain
                )
                return self.async_update_reload_and_abort(
                    entry,
                    data_updates={
                        CONF_LANGUAGE: language,
                        CONF_DOMAIN: domain,
                        "url": f"{domain}{area_path}",
                    },
                    # Submitting the current language changes nothing, and a
                    # reload would only cost bergfex a round of requests.
                    reload_even_if_entry_is_unchanged=False,
                )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_LANGUAGE, default=language): vol.In(
                        language_options()
                    )
                }
            ),
            errors=errors,
            description_placeholders={"name": entry.title},
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
                # Plain key: Home Assistant prefixes config.error.<key> itself, so prefixing
                # here printed the raw key on the form.
                errors["base"] = "no_selection"
            else:
                if manual_path:
                    try:
                        ski_area_path = normalize_ski_area_path(
                            manual_path, is_cross_country=is_cross_country
                        )
                    except InvalidSkiAreaPath:
                        # Nothing to complete "bergfex.at" or "/" into. Say so on
                        # the form instead of letting it fail somewhere later.
                        errors["base"] = "invalid_path"

                if webhook_url:
                    try:
                        webhook_url = validate_webhook_url(webhook_url)
                    except InvalidWebhookUrl:
                        errors["base"] = "invalid_webhook"
                else:
                    # An empty string is not a webhook; storing it would have the
                    # update loop treat "" as falsy anyway, so normalise it.
                    webhook_url = None

            if not errors:
                # A resort's path is identical on every bergfex domain, so it is the one
                # stable id an entry has, and what lets Home Assistant refuse a second entry
                # for the same resort. It does not deduplicate the sensor unique ids, which
                # live in a separate namespace - see unique_id.py.
                await self.async_set_unique_id(ski_area_path)
                self._abort_if_unique_id_configured()

                # Keep ski_area_path as the unique ID
                ski_area_name = ski_areas.get(ski_area_path) or ski_area_name_from_path(
                    ski_area_path
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


class OptionsFlowHandler(config_entries.OptionsFlowWithReload):
    """Handle options.

    Only the update interval is an option. The language lives in the entry's
    data and is changed through the reconfigure step. Core reloads the entry
    once the options change, which is what applies a new interval.
    """

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(
                title="",
                data={CONF_UPDATE_INTERVAL: user_input[CONF_UPDATE_INTERVAL]},
            )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_UPDATE_INTERVAL,
                        default=self.config_entry.options.get(
                            CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
                        ),
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=MIN_UPDATE_INTERVAL, max=MAX_UPDATE_INTERVAL),
                    ),
                }
            ),
        )
