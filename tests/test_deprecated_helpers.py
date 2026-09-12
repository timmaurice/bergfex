"""Home Assistant helpers this integration must not go back to.

These are source checks rather than behaviour tests on purpose: a deprecation
is announced by the Home Assistant version the user runs, and the core pinned
in this repository's test environment is older than the one that warns. So the
suite cannot observe the warning, and without something like this the call
comes back unnoticed and users see it in their log instead - which is exactly
how `device_registry.async_get_device` got shipped.

Each entry names the replacement, so a failure says what to do rather than only
what not to.
"""

from pathlib import Path

import pytest

COMPONENT = Path(__file__).resolve().parents[1] / "custom_components" / "bergfex"

# call fragment -> what to use instead
FORBIDDEN = {
    ".async_get_device(": (
        "device identifiers are not unique across config entries; look the "
        "device up within the entry via dr.async_entries_for_config_entry()"
    ),
    ".devices[": (
        "device_registry.devices is deprecated as a mapping; use async_get() "
        "or async_entries_for_config_entry()"
    ),
    "via_device=": "pass via_device_id= instead",
}


@pytest.mark.parametrize("call,replacement", sorted(FORBIDDEN.items()))
def test_the_integration_avoids_a_deprecated_helper(call: str, replacement: str):
    offenders = [
        f"{path.name}:{number}"
        for path in sorted(COMPONENT.glob("*.py"))
        for number, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), start=1
        )
        if call in line
    ]

    assert not offenders, f"{offenders}: {replacement}"
