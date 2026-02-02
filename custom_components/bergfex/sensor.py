from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, cast
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import slugify

from .const import (
    BASE_URL,
    CONF_COUNTRY,
    CONF_DOMAIN,
    CONF_LANGUAGE,
    CONF_SKI_AREA,
    CONF_TYPE,
    COORDINATORS,
    COUNTRIES,
    DOMAIN,
    TYPE_ALPINE,
    TYPE_CROSS_COUNTRY,
)
from .parser import parse_overview_data, parse_resort_page

@dataclass
class BergfexSensorEntityDescription(SensorEntityDescription):
    """Class describing Bergfex sensor entities."""

    total_key: str | None = None


ALPINE_SENSORS: tuple[BergfexSensorEntityDescription, ...] = (
    BergfexSensorEntityDescription(
        key="status",
        name="Status",
        translation_key="status",
        icon="mdi:ski",
    ),
    BergfexSensorEntityDescription(
        key="snow_valley",
        name="Snow Valley",
        translation_key="snow_valley",
        icon="mdi:snowflake",
        native_unit_of_measurement="cm",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    BergfexSensorEntityDescription(
        key="snow_mountain",
        name="Snow Mountain",
        translation_key="snow_mountain",
        icon="mdi:snowflake",
        native_unit_of_measurement="cm",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    BergfexSensorEntityDescription(
        key="new_snow",
        name="New Snow",
        translation_key="new_snow",
        icon="mdi:weather-snowy-heavy",
        native_unit_of_measurement="cm",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    BergfexSensorEntityDescription(
        key="snow_condition",
        name="Snow Condition",
        translation_key="snow_condition",
        icon="mdi:snowflake-alert",
    ),
    BergfexSensorEntityDescription(
        key="last_snowfall",
        name="Last Snowfall",
        translation_key="last_snowfall",
        icon="mdi:calendar-clock",
    ),
    BergfexSensorEntityDescription(
        key="avalanche_warning",
        name="Avalanche Warning",
        translation_key="avalanche_warning",
        icon="mdi:alert-octagon",
    ),
    BergfexSensorEntityDescription(
        key="lifts_open_count",
        name="Lifts Open",
        translation_key="lifts_open_count",
        total_key="lifts_total_count",
        icon="mdi:gondola",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    BergfexSensorEntityDescription(
        key="slopes_open_km",
        name="Slopes Open (km)",
        translation_key="slopes_open_km",
        total_key="slopes_total_km",
        icon="mdi:ski",
        native_unit_of_measurement="km",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    BergfexSensorEntityDescription(
        key="slopes_open_count",
        name="Slopes Open",
        translation_key="slopes_open_count",
        total_key="slopes_total_count",
        icon="mdi:ski",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    BergfexSensorEntityDescription(
        key="slope_condition",
        name="Slope Condition",
        translation_key="slope_condition",
        icon="mdi:snowflake-variant",
    ),
    BergfexSensorEntityDescription(
        key="last_update",
        name="Last Update",
        translation_key="last_update",
        icon="mdi:clock-outline",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
)

CROSS_COUNTRY_SENSORS: tuple[BergfexSensorEntityDescription, ...] = (
    BergfexSensorEntityDescription(
        key="status",
        name="Status",
        translation_key="status",
        icon="mdi:ski-cross-country",
    ),
    BergfexSensorEntityDescription(
        key="operation_status",
        name="Operation Status",
        translation_key="operation_status",
        icon="mdi:check-circle-outline",
    ),
    BergfexSensorEntityDescription(
        key="classical_open_km",
        name="Classical Trails Open",
        translation_key="classical_open_km",
        total_key="classical_total_km",
        icon="mdi:ski-cross-country",
        native_unit_of_measurement="km",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    BergfexSensorEntityDescription(
        key="classical_condition",
        name="Classical Condition",
        translation_key="classical_condition",
        icon="mdi:snowflake-variant",
    ),
    BergfexSensorEntityDescription(
        key="skating_open_km",
        name="Skating Trails Open",
        translation_key="skating_open_km",
        total_key="skating_total_km",
        icon="mdi:ski-cross-country",
        native_unit_of_measurement="km",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    BergfexSensorEntityDescription(
        key="skating_condition",
        name="Skating Condition",
        translation_key="skating_condition",
        icon="mdi:snowflake-variant",
    ),
    BergfexSensorEntityDescription(
        key="last_update",
        name="Last Update",
        translation_key="last_update",
        icon="mdi:clock-outline",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
)


SCAN_INTERVAL = timedelta(minutes=30)
_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Bergfex sensor entry."""
    # Get the coordinator stored in hass.data by the integration setup
    resort_coordinator_name = f"bergfex_{entry.data.get('name')}"
    coordinator = hass.data[DOMAIN][COORDINATORS].get(resort_coordinator_name)
    if coordinator is None:
        _LOGGER.error("Coordinator not found for %s", resort_coordinator_name)
        return
    _LOGGER.debug(
        "Sensor async_setup_entry - Coordinator: %s, Entry data: %s",
        coordinator,
        entry.data,
    )

    resort_type = entry.data.get(CONF_TYPE, TYPE_ALPINE)

    if resort_type == TYPE_CROSS_COUNTRY:
        sensors = [
            BergfexSensor(coordinator, entry, description)
            for description in CROSS_COUNTRY_SENSORS
        ]
    else:
        sensors = [
            BergfexSensor(coordinator, entry, description)
            for description in ALPINE_SENSORS
        ]

    async_add_entities(sensors)


class BergfexSensor(SensorEntity):
    """Representation of a Bergfex Sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        entry: ConfigEntry,
        description: BergfexSensorEntityDescription,
    ):
        """Initialize the sensor."""
        self.coordinator = coordinator
        self.entity_description = description
        self._resort_type = entry.data.get(CONF_TYPE, TYPE_ALPINE)
        self._initial_area_name = entry.data["name"]  # Store initial name as fallback
        self._area_name = self._initial_area_name  # Current name, can be updated
        self._area_path = entry.data[CONF_SKI_AREA]
        self._domain = entry.data.get(CONF_DOMAIN, BASE_URL)
        self._config_url = urljoin(self._domain, self._area_path)
        
        # Use slugified name for a stable prefix that matches typical HA defaults
        # This helps in "reusing" IDs that were automatically generated from the name
        resort_prefix = slugify(self._initial_area_name)
        
        # unique_id should be stable and English-keyed
        # We use the resort_prefix to stay compatible with earlier registry entries if possible
        self._attr_unique_id = f"bergfex_{resort_prefix}_{description.key}"
        
        # Explicitly set entity_id to the desired English format
        self.entity_id = f"sensor.{resort_prefix}_{description.key}"
        
        # suggested_object_id provides a hint for new entity creation
        self._attr_suggested_object_id = description.key

        _LOGGER.debug(
            "BergfexSensor __init__ - Area Path: %s, Initial Area Name: %s, Unique ID: %s",
            self._area_path,
            self._initial_area_name,
            self._attr_unique_id,
        )

    def _update_names(self) -> None:
        """Update the area name and device info based on coordinator data."""
        if self.coordinator.data and self._area_path in self.coordinator.data:
            area_data = self.coordinator.data[self._area_path]
            if "resort_name" in area_data:
                self._area_name = area_data["resort_name"]
            else:
                self._area_name = self._initial_area_name
        else:
            self._area_name = self._initial_area_name

        _LOGGER.debug(
            "BergfexSensor _update_names - Coordinator Data: %s, Area Path: %s, Resulting Area Name: %s",
            self.coordinator.data,
            self._area_path,
            self._area_name,
        )

    @property
    def native_value(self) -> str | int | datetime | None:
        """Return the state of the sensor."""
        # Data for this specific ski area
        if self.coordinator.data is None:
            return None
        all_areas_data = cast(dict, self.coordinator.data)
        area_data = all_areas_data.get(self._area_path)
        data_key = self.entity_description.key

        if area_data and data_key in area_data:
            value = area_data[data_key]
            _LOGGER.debug(
                "BergfexSensor native_value - Coordinator Data: %s, Area Data: %s, Data Key: %s, Value: %s",
                self.coordinator.data,
                area_data,
                data_key,
                value,
            )
            # Return datetime objects as-is for timestamp sensors
            if isinstance(value, datetime):
                return value
            # Try to convert to integer if it's a number
            if isinstance(value, str):
                if value.isdigit():
                    return int(value)
                try:
                    return float(value)
                except ValueError:
                    pass
            return value

        _LOGGER.debug(
            "BergfexSensor native_value - Coordinator Data: %s, Area Data: %s, Data Key: %s, Returning None",
            self.coordinator.data,
            area_data,
            self._data_key,
        )
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return the state attributes."""
        attrs = {}

        data_key = self.entity_description.key
        total_key = self.entity_description.total_key

        if data_key == "status":
            attrs["link"] = self._config_url
            if self.coordinator.data and self._area_path in self.coordinator.data:
                area_data = self.coordinator.data[self._area_path]
                if "price" in area_data:
                    attrs["price"] = area_data["price"]

        if self.coordinator.data and self._area_path in self.coordinator.data:
            area_data = self.coordinator.data[self._area_path]

            if data_key == "snow_mountain" and "elevation_mountain" in area_data:
                attrs["elevation"] = area_data["elevation_mountain"]

            if data_key == "snow_valley" and "elevation_valley" in area_data:
                attrs["elevation"] = area_data["elevation_valley"]

            if total_key and total_key in area_data:
                attrs["total"] = area_data[total_key]

            # Add caption for image sensors
            if data_key.endswith("_url"):
                caption_key = data_key.replace("_url", "_caption")
                if caption_key in area_data:
                    attrs["caption"] = area_data[caption_key]

        return attrs if attrs else None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success

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

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        self._update_names()  # Set initial names based on available data
        self.async_on_remove(
            self.coordinator.async_add_listener(
                lambda: self.hass.async_create_task(self._handle_coordinator_update())
            )
        )

    async def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._update_names()
        self.async_write_ha_state()
