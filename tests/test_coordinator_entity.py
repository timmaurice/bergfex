"""The sensors are CoordinatorEntity subclasses, so the coordinator drives them."""

from unittest.mock import AsyncMock

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.bergfex.const import CONF_SKI_AREA, DOMAIN
from custom_components.bergfex.coordinator import BergfexCoordinator
from custom_components.bergfex.sensor import ALPINE_SENSORS, BergfexSensor

AREA = "/ischgl/"


def _setup(hass: HomeAssistant):
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Ischgl",
        data={CONF_SKI_AREA: AREA, "name": "ischgl"},
        unique_id=AREA,
    )
    entry.add_to_hass(hass)
    coordinator = BergfexCoordinator(hass, entry)
    coordinator.data = {AREA: {"resort_name": "Ischgl"}}
    return entry, coordinator


async def test_sensor_is_a_coordinator_entity(hass: HomeAssistant):
    entry, coordinator = _setup(hass)
    sensor = BergfexSensor(coordinator, entry, ALPINE_SENSORS[0])

    assert isinstance(sensor, CoordinatorEntity)
    assert sensor.coordinator is coordinator
    # Polling stays with the coordinator; update_entity refreshes through it.
    assert sensor.should_poll is False
    assert sensor.unique_id.endswith(ALPINE_SENSORS[0].key)

    coordinator.last_update_success = False
    assert sensor.available is False
    coordinator.last_update_success = True
    assert sensor.available is True


async def test_update_entity_goes_through_the_coordinator(hass: HomeAssistant):
    entry, coordinator = _setup(hass)
    sensor = BergfexSensor(coordinator, entry, ALPINE_SENSORS[0])
    sensor.hass = hass
    coordinator.async_request_refresh = AsyncMock()

    await sensor.async_update()

    coordinator.async_request_refresh.assert_awaited_once()
