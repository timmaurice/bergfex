import logging
from datetime import timedelta
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
    CONF_SKI_AREA,
    COORDINATORS,
    COUNTRIES,
    DOMAIN,
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

    coordinator = entry.runtime_data
    _LOGGER.debug(
        "Sensor async_setup_entry - Coordinator: %s, Entry runtime data: %s",
        coordinator,
        entry.runtime_data,
    )

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
            "Lifts Open",
            "lifts_open_count",
            icon="mdi:gondola",
            state_class=SensorStateClass.MEASUREMENT,
        ),
        BergfexSensor(
            coordinator,
            entry,
            "Lifts Total",
            "lifts_total_count",
            icon="mdi:map-marker-distance",
        ),
        BergfexSensor(
            coordinator, entry, "Last Update", "last_update", icon="mdi:clock-outline"
        ),
    ]

    async_add_entities(sensors)


from .parser import parse_overview_data, parse_resort_page


class BergfexSensor(SensorEntity):
    """Representation of a Bergfex Sensor."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        entry: ConfigEntry,
        sensor_name: str,
        data_key: str,
        icon: str | None = None,
        unit: str | None = None,
        state_class: SensorStateClass | None = None,
    ):
        """Initialize the sensor."""
        self.coordinator = coordinator
        self._initial_area_name = entry.data["name"]  # Store initial name as fallback
        self._area_name = self._initial_area_name  # Current name, can be updated
        self._area_path = entry.data[CONF_SKI_AREA]
        self._config_url = urljoin(BASE_URL, self._area_path)
        self._sensor_name = sensor_name
        self._data_key = data_key
        self._attr_icon = icon
        self._attr_native_unit_of_measurement = unit
        self._attr_state_class = state_class
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
    def native_value(self) -> str | int | None:
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
            # Try to convert to integer if it's a number
            if isinstance(value, str) and value.isdigit():
                return int(value)
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
        if self._data_key == "status":
            return {"link": self._config_url}
        return None

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
            "model": "Ski Resort",
            "configuration_url": self._config_url,
        }

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        self._update_names()  # Set initial names based on available data
        self.async_on_remove(
            self.coordinator.async_add_listener(
                lambda: self.hass.async_add_job(self._handle_coordinator_update)
            )
        )

    async def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._update_names()
        self.async_write_ha_state()
