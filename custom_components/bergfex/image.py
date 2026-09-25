from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.image import ImageEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from urllib.parse import urljoin
from homeassistant.util import dt as dt_util
from homeassistant.util import slugify

from .coordinator import BergfexConfigEntry, BergfexCoordinator
from .config_flow import entry_area_name
from .unique_id import build_unique_id
from .const import (
    BASE_URL,
    CONF_DOMAIN,
    CONF_SKI_AREA,
    CONF_TYPE,
    DOMAIN,
    TYPE_CROSS_COUNTRY,
)

_LOGGER = logging.getLogger(__name__)

# The entities read their URLs from the coordinator and have no update method.
# The image bytes are fetched on request, from bergfex's CDN rather than the
# pages its rate limit is about, and only the image.snapshot action would wait
# on this limit - the frontend's image proxy never does.
PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: BergfexConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Bergfex image platform."""
    # The integration setup stores the coordinator on the entry, and only after
    # its first refresh succeeded, so it is always there by now.
    coordinator = entry.runtime_data

    entities = []

    # Check if we have data for this area
    area_path = entry.data[CONF_SKI_AREA]
    if not coordinator.data or area_path not in coordinator.data:
        return

    area_data = coordinator.data[area_path]

    # Add daily forecast image entities
    for i in range(6):
        data_key = f"forecast_image_day_{i}_url"
        if data_key in area_data:
            entities.append(
                BergfexImage(
                    coordinator,
                    entry,
                    data_key,
                )
            )

    # Add summary forecast image entities
    summary_hours = [48, 72, 96, 120, 144]
    for hours in summary_hours:
        data_key = f"summary_image_{hours}h_url"
        if data_key in area_data:
            entities.append(
                BergfexImage(
                    coordinator,
                    entry,
                    data_key,
                )
            )

    if entities:
        async_add_entities(entities)


class BergfexImage(ImageEntity):
    """Representation of a Bergfex Image."""

    _attr_has_entity_name = True
    _attr_name: str | None = None

    def __init__(
        self,
        coordinator: BergfexCoordinator,
        entry: ConfigEntry,
        data_key: str,
    ) -> None:
        """Initialize the image entity."""
        super().__init__(coordinator.hass)
        self.coordinator = coordinator
        self._resort_type = entry.data.get(CONF_TYPE)
        self._initial_area_name = entry_area_name(entry)
        self._area_name = self._initial_area_name
        self._area_path = entry.data[CONF_SKI_AREA]
        self._domain = entry.data.get(CONF_DOMAIN, BASE_URL)
        self._config_url = urljoin(self._domain, self._area_path)
        self._data_key = data_key

        english_key = data_key.replace("_url", "")
        self._attr_translation_key = english_key
        self._attr_suggested_object_id = english_key

        # Keyed on the resort path for the same reason as the sensors: the
        # display name is not unique, so it cannot identify a resort. See
        # unique_id.py.
        self._attr_unique_id = build_unique_id(self._area_path, english_key)

        # Name-keyed entity_id, left alone deliberately - see sensor.py.
        self.entity_id = f"image.{slugify(self._initial_area_name)}_{english_key}"

        self._client = async_get_clientsession(coordinator.hass)

    @property
    def device_info(self):
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self._area_path)},
            "name": self._area_name,
            "manufacturer": "Bergfex",
            "model": (
                "Cross country skiing"
                if self._resort_type == TYPE_CROSS_COUNTRY
                else "Ski Resort"
            ),
            "configuration_url": self._config_url,
        }

    @property
    def available(self) -> bool:
        # ...
        """Return if entity is available."""
        return self.coordinator.last_update_success

    @property
    def image_url(self) -> str | None:
        """Return the URL of the image."""
        if self.coordinator.data and self._area_path in self.coordinator.data:
            area_data = self.coordinator.data[self._area_path]
            return area_data.get(self._data_key)
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return the state attributes."""
        if self.coordinator.data and self._area_path in self.coordinator.data:
            area_data = self.coordinator.data[self._area_path]
            # Add caption if available
            caption_key = self._data_key.replace("_url", "_caption")
            if caption_key in area_data:
                return {"caption": area_data[caption_key]}
        return None

    async def async_image(self) -> bytes | None:
        """Fetch and return bytes of the image."""
        url = self.image_url
        if not url:
            return None

        try:
            async with self._client.get(url) as response:
                response.raise_for_status()
                return await response.read()
        except Exception as err:
            _LOGGER.error("Error fetching image from %s: %s", url, err)
            return None

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        self._update_names()
        # Set initial timestamp if data is available
        if self.image_url:
            self._attr_image_last_updated = dt_util.now()

        self.async_on_remove(
            self.coordinator.async_add_listener(
                lambda: self.hass.async_create_task(self._handle_coordinator_update())
            )
        )

    async def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._update_names()
        self._attr_image_last_updated = dt_util.now()  # Force refresh
        self.async_write_ha_state()

    def _update_names(self) -> None:
        """Update the area name based on coordinator data."""
        if self.coordinator.data and self._area_path in self.coordinator.data:
            area_data = self.coordinator.data[self._area_path]
            if "resort_name" in area_data:
                self._area_name = area_data["resort_name"]
            else:
                self._area_name = self._initial_area_name
        else:
            self._area_name = self._initial_area_name

        # The id is set once, in __init__. Rewriting it after registration cannot
        # move the registry entry, it only makes the entity disagree with its record.
