import logging
from datetime import datetime, timedelta
from typing import Any, cast
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

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

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(minutes=30)


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
            BergfexSensor(
                coordinator, entry, "Status", "status", icon="mdi:ski-cross-country"
            ),
            BergfexSensor(
                coordinator,
                entry,
                "Operation Status",
                "operation_status",
                icon="mdi:check-circle-outline",
            ),
            BergfexSensor(
                coordinator,
                entry,
                "Classical Trails Open",
                "classical_open_km",
                total_key="classical_total_km",
                icon="mdi:ski-cross-country",
                unit="km",
                state_class=SensorStateClass.MEASUREMENT,
            ),
            BergfexSensor(
                coordinator,
                entry,
                "Classical Condition",
                "classical_condition",
                icon="mdi:snowflake-variant",
            ),
            BergfexSensor(
                coordinator,
                entry,
                "Skating Trails Open",
                "skating_open_km",
                total_key="skating_total_km",
                icon="mdi:ski-cross-country",
                unit="km",
                state_class=SensorStateClass.MEASUREMENT,
            ),
            BergfexSensor(
                coordinator,
                entry,
                "Skating Condition",
                "skating_condition",
                icon="mdi:snowflake-variant",
            ),
            BergfexSensor(
                coordinator,
                entry,
                "Last Update",
                "last_update",
                icon="mdi:clock-outline",
                device_class=SensorDeviceClass.TIMESTAMP,
            ),
        ]
    else:
        sensors = [
            BergfexSensor(coordinator, entry, "Status", "status", icon="mdi:ski"),
            BergfexSensor(
                coordinator,
                entry,
                "Snow Valley",
                "snow_valley",
                icon="mdi:snowflake",
                unit="cm",
                state_class=SensorStateClass.MEASUREMENT,
            ),
            BergfexSensor(
                coordinator,
                entry,
                "Snow Mountain",
                "snow_mountain",
                icon="mdi:snowflake",
                unit="cm",
                state_class=SensorStateClass.MEASUREMENT,
            ),
            BergfexSensor(
                coordinator,
                entry,
                "New Snow",
                "new_snow",
                icon="mdi:weather-snowy-heavy",
                unit="cm",
                state_class=SensorStateClass.MEASUREMENT,
            ),
            BergfexSensor(
                coordinator,
                entry,
                "Snow Condition",
                "snow_condition",
                icon="mdi:snowflake-alert",
            ),
            BergfexSensor(
                coordinator,
                entry,
                "Last Snowfall",
                "last_snowfall",
                icon="mdi:calendar-clock",
            ),
            BergfexSensor(
                coordinator,
                entry,
                "Avalanche Warning",
                "avalanche_warning",
                icon="mdi:alert-octagon",
            ),
            BergfexSensor(
                coordinator,
                entry,
                "Lifts Open",
                "lifts_open_count",
                total_key="lifts_total_count",
                icon="mdi:gondola",
                state_class=SensorStateClass.MEASUREMENT,
            ),
            BergfexSensor(
                coordinator,
                entry,
                "Slopes Open (km)",
                "slopes_open_km",
                total_key="slopes_total_km",
                icon="mdi:ski",
                unit="km",
                state_class=SensorStateClass.MEASUREMENT,
            ),
            BergfexSensor(
                coordinator,
                entry,
                "Slopes Open",
                "slopes_open_count",
                total_key="slopes_total_count",
                icon="mdi:ski",
                state_class=SensorStateClass.MEASUREMENT,
            ),
            BergfexSensor(
                coordinator,
                entry,
                "Slope Condition",
                "slope_condition",
                icon="mdi:snowflake-variant",
            ),
            BergfexSensor(
                coordinator,
                entry,
                "Last Update",
                "last_update",
                icon="mdi:clock-outline",
                device_class=SensorDeviceClass.TIMESTAMP,
            ),
        ]

    async_add_entities(sensors)


class BergfexSensor(SensorEntity):
    """Representation of a Bergfex Sensor."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        entry: ConfigEntry,
        sensor_name: str,
        data_key: str,
        total_key: str | None = None,
        icon: str | None = None,
        unit: str | None = None,
        state_class: SensorStateClass | None = None,
        device_class: SensorDeviceClass | None = None,
    ):
        """Initialize the sensor."""
        self.coordinator = coordinator
        self._resort_type = entry.data.get(CONF_TYPE, TYPE_ALPINE)
        self._initial_area_name = entry.data["name"]  # Store initial name as fallback
        self._area_name = self._initial_area_name  # Current name, can be updated
        self._area_path = entry.data[CONF_SKI_AREA]
        self._domain = entry.data.get(CONF_DOMAIN, BASE_URL)
        self._config_url = urljoin(self._domain, self._area_path)
        self._sensor_name = sensor_name
        self._data_key = data_key
        self._total_key = total_key
        self._attr_icon = icon
        self._attr_native_unit_of_measurement = unit
        self._attr_state_class = state_class
        self._attr_device_class = device_class
        # Initialize Unique ID and name here
        self._attr_unique_id = f"bergfex_{self._initial_area_name.lower().replace(' ', '_')}_{self._sensor_name.lower().replace(' ', '_')}"
        self._attr_name = f"{self._initial_area_name} {self._sensor_name}"
        _LOGGER.debug(
            "BergfexSensor __init__ - Area Path: %s, Initial Area Name: %s, Unique ID: %s, Name: %s",
            self._area_path,
            self._initial_area_name,
            self._attr_unique_id,
            self._attr_name,
        )

    def _update_names(self) -> None:
        """Update the area name, unique ID, and entity name based on coordinator data."""
        if self.coordinator.data and self._area_path in self.coordinator.data:
            area_data = self.coordinator.data[self._area_path]
            if "resort_name" in area_data:
                self._area_name = area_data["resort_name"]
            else:
                self._area_name = self._initial_area_name
        else:
            self._area_name = self._initial_area_name

        # Always update unique_id and name after _area_name might have changed
        self._attr_unique_id = f"bergfex_{self._area_path.replace('/', '_')}_{self._sensor_name.lower().replace(' ', '_')}"
        self._attr_name = f"{self._area_name} {self._sensor_name}"

        _LOGGER.debug(
            "BergfexSensor _update_names - Coordinator Data: %s, Area Path: %s, Resulting Area Name: %s, Unique ID: %s, Name: %s",
            self.coordinator.data,
            self._area_path,
            self._area_name,
            self._attr_unique_id,
            self._attr_name,
        )

    @property
    def native_value(self) -> str | int | datetime | None:
        """Return the state of the sensor."""
        # Data for this specific ski area
        if self.coordinator.data is None:
            return None
        all_areas_data = cast(dict, self.coordinator.data)
        area_data = all_areas_data.get(self._area_path)

        if area_data and self._data_key in area_data:
            value = area_data[self._data_key]
            _LOGGER.debug(
                "BergfexSensor native_value - Coordinator Data: %s, Area Data: %s, Data Key: %s, Value: %s",
                self.coordinator.data,
                area_data,
                self._data_key,
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

        if self._data_key == "status":
            attrs["link"] = self._config_url

        if self.coordinator.data and self._area_path in self.coordinator.data:
            area_data = self.coordinator.data[self._area_path]

            if self._data_key == "snow_mountain" and "elevation_mountain" in area_data:
                attrs["elevation"] = area_data["elevation_mountain"]

            if self._data_key == "snow_valley" and "elevation_valley" in area_data:
                attrs["elevation"] = area_data["elevation_valley"]

            if self._total_key and self._total_key in area_data:
                attrs["total"] = area_data[self._total_key]

            # Add caption for image sensors
            if self._data_key.endswith("_url"):
                caption_key = self._data_key.replace("_url", "_caption")
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
