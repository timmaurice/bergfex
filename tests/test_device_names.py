"""The device name that never caught up with the parser.

`device_info` is read once, when the first entity registers. An entry created
while bergfex's Tailwind rename had name parsing broken stored a URL slug, so
that is what the device was called - and stayed called, because nothing renames
a device after the fact. The card headed those resorts in lower case.
"""

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.bergfex.__init__ import COORDINATORS, _async_refresh_device_name
from custom_components.bergfex.const import CONF_SKI_AREA, DOMAIN
from custom_components.bergfex.unique_id import coordinator_key

AREA = "/tirol/achensee/"


def _entry(hass: HomeAssistant, name: str = "achensee") -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Achensee",
        data={CONF_SKI_AREA: AREA, "name": name},
        unique_id=AREA,
    )
    entry.add_to_hass(hass)
    return entry


def _device(hass: HomeAssistant, entry: MockConfigEntry, name: str):
    return dr.async_get(hass).async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, AREA)},
        name=name,
    )


def _coordinator(hass: HomeAssistant, data) -> None:
    """Stand in for the resort coordinator, which only its `data` matters here."""
    hass.data.setdefault(DOMAIN, {}).setdefault(COORDINATORS, {})
    hass.data[DOMAIN][COORDINATORS][coordinator_key(AREA)] = type(
        "Coordinator", (), {"data": data}
    )()


async def test_the_slug_is_replaced_by_the_parsed_name(hass: HomeAssistant):
    """The bug: entries created while name parsing was broken stored a slug.

    The entities correct themselves on every coordinator update; the device is
    named once, when the first entity registers, and never again.
    """
    entry = _entry(hass)
    device = _device(hass, entry, "achensee")
    _coordinator(hass, {AREA: {"resort_name": "Achensee"}})

    _async_refresh_device_name(hass, entry)

    assert dr.async_get(hass).async_get(device.id).name == "Achensee"


async def test_a_name_the_user_chose_is_not_touched(hass: HomeAssistant):
    """`name_by_user` is what Home Assistant displays, and it is theirs."""
    entry = _entry(hass)
    device = _device(hass, entry, "achensee")
    dr.async_get(hass).async_update_device(device.id, name_by_user="Hausberg")
    _coordinator(hass, {AREA: {"resort_name": "Achensee"}})

    _async_refresh_device_name(hass, entry)

    updated = dr.async_get(hass).async_get(device.id)
    assert updated.name_by_user == "Hausberg"
    assert updated.name == "Achensee"


async def test_nothing_happens_without_coordinator_data(hass: HomeAssistant):
    """Off-season and mid-outage the name must not be blanked."""
    entry = _entry(hass)
    device = _device(hass, entry, "achensee")
    _coordinator(hass, None)

    _async_refresh_device_name(hass, entry)

    assert dr.async_get(hass).async_get(device.id).name == "achensee"


async def test_a_resort_without_a_parsed_name_keeps_what_it_has(hass: HomeAssistant):
    entry = _entry(hass)
    device = _device(hass, entry, "achensee")
    _coordinator(hass, {AREA: {"snow_mountain": 40}})

    _async_refresh_device_name(hass, entry)

    assert dr.async_get(hass).async_get(device.id).name == "achensee"


async def test_a_correct_name_is_left_alone(hass: HomeAssistant):
    entry = _entry(hass, name="Sölden")
    device = _device(hass, entry, "Sölden")
    _coordinator(hass, {AREA: {"resort_name": "Sölden"}})

    _async_refresh_device_name(hass, entry)

    assert dr.async_get(hass).async_get(device.id).name == "Sölden"
