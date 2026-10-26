"""Fetch bergfex pages the way a guest should: slowly, and taking no for an answer.

The live checks used to retry a 429 up to fifty times a page with a fraction of a
second in between, which put five to six hundred refused requests into every
daily run. bergfex is scraped without an API and has started turning clients
away, so the scripts that watch it must stay well inside what it tolerates:

- one request at a time, with a fixed gap between any two of them;
- on 429, wait for as long as ``Retry-After`` asks - or back off exponentially
  when it does not say - and give up after a few attempts;
- a 403 or 451 is never retried, and nothing here pretends to be a browser.

A wait after a 429 holds back every request, not only the one that was refused,
so a refusal slows the whole run down rather than being worked around.
"""

from __future__ import annotations

import asyncio
import datetime
import email.utils
import random

import aiohttp

# What Home Assistant's shared session sends, which is what the integration is
# stuck with: async_get_clientsession freezes the User-Agent and refuses to let
# an integration override it ("It's important that we identify as Home
# Assistant"). A check that sends anything else asks a different question than
# the integration does.
USER_AGENT = "HomeAssistant/2026.10.0 aiohttp/3.12.15 Python/3.13"

# Statuses that mean we were turned away rather than missed, as in fetch.py.
REFUSAL_STATUSES = frozenset({403, 429, 451})

# Seconds between the start of any two requests in a run.
REQUEST_INTERVAL = 2.0

# Attempts per URL, the first included. Only a 429 or a network error earns a
# second one.
MAX_ATTEMPTS = 3

# Without a Retry-After, wait BACKOFF_BASE, then twice that, and so on.
BACKOFF_BASE = 15.0

# A Retry-After longer than this is taken as "not today": the page is given up
# rather than the run being held for it.
MAX_RETRY_AFTER = 120.0


class Pacer:
    """Spaces requests out, and holds all of them back after a refusal."""

    def __init__(self, interval: float) -> None:
        self.interval = interval
        self._lock = asyncio.Lock()
        self._next = 0.0

    async def wait(self) -> None:
        async with self._lock:
            loop = asyncio.get_running_loop()
            delay = self._next - loop.time()
            if delay > 0:
                await asyncio.sleep(delay)
            self._next = loop.time() + self.interval

    def hold(self, seconds: float) -> None:
        """Let no request through for ``seconds`` from now."""
        until = asyncio.get_running_loop().time() + seconds
        self._next = max(self._next, until)


PACER = Pacer(REQUEST_INTERVAL)


def retry_after_seconds(value: str | None, now: datetime.datetime | None = None):
    """Read a Retry-After header, which is either seconds or an HTTP date."""
    if not value:
        return None
    value = value.strip()
    if value.isdigit():
        return float(value)
    try:
        when = email.utils.parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None
    if when.tzinfo is None:
        when = when.replace(tzinfo=datetime.timezone.utc)
    now = now or datetime.datetime.now(datetime.timezone.utc)
    return max(0.0, (when - now).total_seconds())


def backoff_delay(attempt: int, retry_after: str | None) -> float | None:
    """How long to wait before attempt ``attempt + 1``, or None to give up."""
    asked = retry_after_seconds(retry_after)
    if asked is not None:
        return asked if asked <= MAX_RETRY_AFTER else None
    return BACKOFF_BASE * 2 ** (attempt - 1) * random.uniform(1.0, 1.25)


async def fetch_html(session, url, *, on_refusal=None, attempts=MAX_ATTEMPTS):
    """Return the page's HTML, or None when it could not be had politely.

    ``on_refusal`` is called with each refused response, so a refusal cannot
    disappear inside the retry loop.
    """
    headers = {"User-Agent": USER_AGENT}
    for attempt in range(1, attempts + 1):
        await PACER.wait()
        try:
            async with session.get(url, headers=headers, timeout=15) as response:
                if response.status == 200:
                    return await response.text()
                if response.status in REFUSAL_STATUSES and on_refusal:
                    on_refusal(response)
                if response.status != 429:
                    # A 404 is a wrong path, a 403 a refusal; neither becomes a
                    # yes by being asked again.
                    return None
                delay = backoff_delay(attempt, response.headers.get("retry-after"))
        except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
            print(f"    ! {url}: {type(exc).__name__} {exc}")
            delay = backoff_delay(attempt, None)

        # Held even when giving up, so the next page does not walk straight
        # into the same limit.
        PACER.hold(MAX_RETRY_AFTER if delay is None else delay)
        if delay is None:
            return None
    return None
