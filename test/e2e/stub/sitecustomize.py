"""Answers bergfex from the repository's HTML fixtures, inside the e2e container.

Python imports this module on start-up when /stub is on PYTHONPATH (see
docker-compose.yml). It replaces `aiohttp.ClientSession.get` for bergfex hosts
only; every other host is fetched for real.

Why: the suite needs a configured bergfex entry with sensors, and bergfex
refuses (HTTP 429) the shared addresses CI runs on - the same reason the live
site checks treat a refusing runner as "unverified". Fixtures make the run
deterministic and keep the suite from hitting the site on every pull request.
The card specs overwrite the sensor states anyway; what the entry has to supply
is a real resort device in the entity registry.

Served pages:
  /oesterreich/schneebericht/   the Austrian overview (the config flow's resort list)
  /<resort>/schneebericht/      one resort page, whichever resort is asked for
Everything else answers 404, which the integration treats as "page not there".
"""

from __future__ import annotations

import logging
import os
import re
from pathlib import Path
from urllib.parse import urlsplit

_FIXTURES = Path(os.environ.get("E2E_FIXTURES", "/stub-fixtures"))
_BERGFEX_HOST = re.compile(r"(^|\.)bergfex\.[a-z]+$")
_OVERVIEW_PATH = "/oesterreich/schneebericht/"
_OVERVIEW = "overview-at-off-season.html"
_RESORT = "serfaus-at.html"
_LOGGER = logging.getLogger("e2e.bergfex_stub")


class _Content:
    async def read(self, _size: int = -1) -> bytes:
        return b""


class _Response:
    def __init__(self, url: str, status: int, body: str = "") -> None:
        self.url = url
        self.status = status
        self.headers: dict[str, str] = {}
        self.content = _Content()
        self._body = body

    async def text(self, *_args, **_kwargs) -> str:
        return self._body

    async def read(self) -> bytes:
        return self._body.encode("utf-8")


class _Context:
    def __init__(self, response: _Response) -> None:
        self._response = response

    async def __aenter__(self) -> _Response:
        return self._response

    async def __aexit__(self, *_exc) -> None:
        return None

    def __await__(self):
        async def _done() -> _Response:
            return self._response

        return _done().__await__()


def _answer(url: str) -> _Response:
    path = urlsplit(url).path
    if path == _OVERVIEW_PATH:
        name = _OVERVIEW
    elif re.fullmatch(r"/[^/]+/schneebericht/", path):
        name = _RESORT
    else:
        _LOGGER.debug("no fixture for %s", url)
        return _Response(url, 404)
    return _Response(url, 200, (_FIXTURES / name).read_text(encoding="utf-8"))


def _install() -> None:
    try:
        import aiohttp
    except ImportError:
        return

    original = aiohttp.ClientSession.get

    def get(self, url, *args, **kwargs):
        host = urlsplit(str(url)).hostname or ""
        if _BERGFEX_HOST.search(host):
            return _Context(_answer(str(url)))
        return original(self, url, *args, **kwargs)

    aiohttp.ClientSession.get = get


_install()
