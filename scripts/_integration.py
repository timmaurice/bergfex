"""Reach the integration's pure-Python modules without its runtime.

The scripts want two leaf modules - ``const`` and ``parser`` - which need only
BeautifulSoup, so their workflows install ``requirements.txt`` alone. But the
leaves sit inside the package, and importing one executes
``custom_components/bergfex/__init__.py`` with the whole Home Assistant runtime
behind it.

So take the leaves without the trunk: bind the package name to its directory and
let the submodules load, leaving ``__init__.py`` unexecuted. Relative imports
between the leaves still resolve, because the package is real - it is only its
``__init__`` that is skipped. Nothing has to be faked, and nothing added to
``__init__.py`` can break the scripts again.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from types import ModuleType

_ROOT = Path(__file__).resolve().parents[1]
_PACKAGE = "custom_components.bergfex"


def _bind_package_without_its_init() -> None:
    """Put the package in ``sys.modules`` with a path but no executed ``__init__``."""
    for name, directory in (
        ("custom_components", _ROOT / "custom_components"),
        (_PACKAGE, _ROOT / "custom_components" / "bergfex"),
    ):
        existing = sys.modules.get(name)
        if existing is not None and getattr(existing, "__path__", None):
            continue
        module = ModuleType(name)
        # __path__ is the whole trick: it makes this a package for the import
        # system, so submodules load from the real directory.
        module.__path__ = [str(directory)]
        sys.modules[name] = module


def import_integration_module(name: str) -> ModuleType:
    """Import ``custom_components.bergfex.<name>``, runtime or not.

    Prefers the real package, so that anything running with Home Assistant
    installed - the test suite - gets the same modules it always did, and this
    never shadows the integration it is reading from.
    """
    full_name = f"{_PACKAGE}.{name}"
    try:
        return importlib.import_module(full_name)
    except ImportError:
        # Home Assistant is absent, so the package __init__ cannot run. The leaf
        # itself does not need it. A genuinely missing dependency of the leaf -
        # BeautifulSoup, say - still raises, from the retry below.
        sys.modules.pop(full_name, None)

    _bind_package_without_its_init()
    return importlib.import_module(full_name)
