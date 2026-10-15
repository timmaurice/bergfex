"""Fetching bergfex pages, and keeping the evidence when one is refused.

Its own module because both the coordinator and the setup in __init__.py need
it, and __init__.py imports the coordinator - anything they share has to sit
below both. The same reason unique_id.py exists.

The evidence is the point. bergfex sits behind Cloudflare, and a refusal carries
its reason in the body and a ray id in the headers; both were discarded, because
raise_for_status() fires before anything is read. A user could only report
"403, message='Forbidden'", which does not say whether an address was blocked, a
rate limit hit, or a rule matched - and names the end of a redirect chain
without saying what was asked for.
"""

from __future__ import annotations

import logging
import re
from typing import Any

_LOGGER = logging.getLogger(__name__)

# Enough of a Cloudflare block page to recognise which rule answered, short
# enough to sit in a log line and a diagnostics download.
EXCERPT_BYTES = 512

# Statuses that mean the other side is turning us away, as opposed to the page
# being gone or bergfex being broken. Only these raise the repair issue: a 404
# is a wrong path and a 500 is not about us.
REFUSAL_STATUSES = frozenset({403, 429, 451})

_WHITESPACE = re.compile(r"\s+")


class BergfexRefused(Exception):
    """A bergfex page answered with something other than 200.

    Carries what the status line alone cannot say, so the same report does not
    have to be chased twice.
    """

    def __init__(
        self,
        *,
        status: int,
        requested_url: str,
        final_url: str,
        cf_ray: str | None = None,
        server: str | None = None,
        retry_after: str | None = None,
        excerpt: str = "",
    ) -> None:
        self.status = status
        self.requested_url = requested_url
        self.final_url = final_url
        self.cf_ray = cf_ray
        self.server = server
        self.retry_after = retry_after
        self.excerpt = excerpt
        super().__init__(str(self))

    @property
    def is_refusal(self) -> bool:
        """True when the status means we were turned away rather than missed."""
        return self.status in REFUSAL_STATUSES

    @property
    def host(self) -> str:
        """The host that answered, which is not always the one we asked."""
        from urllib.parse import urlparse

        return urlparse(self.final_url).netloc

    def __str__(self) -> str:
        parts = [f"{self.status} for {self.final_url}"]
        if self.final_url != self.requested_url:
            # bergfex redirects German resorts from .at to .de, so the url in the
            # error is not the one that was configured. Saying only the final one
            # sent a reporter looking for a host the integration never chose.
            parts.append(f"requested {self.requested_url}")
        if self.cf_ray:
            parts.append(f"cf-ray={self.cf_ray}")
        if self.server:
            parts.append(f"server={self.server}")
        if self.retry_after:
            parts.append(f"retry-after={self.retry_after}")
        return f"{parts[0]} ({'; '.join(parts[1:])})" if len(parts) > 1 else parts[0]


async def _async_refusal(response: Any, requested_url: str) -> BergfexRefused:
    """Build the exception, reading just enough of the body to explain it.

    `text()` is never called here: a bergfex page is around 200 KB and none of it
    belongs in a log line, while a block page says what matters in its first
    paragraph.
    """
    try:
        raw = await response.content.read(EXCERPT_BYTES)
    except Exception:  # pragma: no cover - a torn-off body is not the story
        raw = b""

    excerpt = _WHITESPACE.sub(" ", raw.decode("utf-8", errors="replace")).strip()

    return BergfexRefused(
        status=response.status,
        requested_url=requested_url,
        final_url=str(response.url),
        cf_ray=response.headers.get("cf-ray"),
        server=response.headers.get("server"),
        retry_after=response.headers.get("retry-after"),
        excerpt=excerpt,
    )


async def async_fetch_text(session: Any, url: str) -> str:
    """Return a bergfex page, or raise BergfexRefused saying why not."""
    async with session.get(url, allow_redirects=True) as response:
        if response.status != 200:
            raise await _async_refusal(response, url)
        return await response.text()


async def async_fetch_text_or_none(
    session: Any, url: str, *, context: str
) -> str | None:
    """Return a page, or None after saying what came back instead.

    For the fetches a poll can do without - the forecast pages, the region
    report, the main page read for a price. They used to log a bare status
    integer, which could not be told apart from any other failure.
    """
    try:
        return await async_fetch_text(session, url)
    except BergfexRefused as err:
        _LOGGER.warning("Could not fetch %s: %s", context, err)
        return None
