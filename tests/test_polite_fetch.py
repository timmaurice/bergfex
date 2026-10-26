"""The live checks must take no for an answer.

The daily canary used to retry a 429 up to fifty times a page with a fraction of
a second in between - five to six hundred refused requests a run, from the
project that tells its users to stay well inside bergfex's tolerance.
"""

import asyncio
import datetime
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import _polite  # noqa: E402


class FakeResponse:
    def __init__(self, status, headers=None, body="<html></html>"):
        self.status = status
        self.headers = headers or {}
        self.url = "https://www.bergfex.at/x/"
        self._body = body

    async def text(self):
        return self._body

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False


class FakeSession:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls = 0
        self.user_agents = []

    def get(self, url, headers=None, timeout=None):
        self.calls += 1
        self.user_agents.append((headers or {}).get("User-Agent"))
        return self.responses.pop(0) if len(self.responses) > 1 else self.responses[0]


@pytest.fixture(autouse=True)
def no_waiting(monkeypatch):
    monkeypatch.setattr(_polite, "PACER", _polite.Pacer(0))
    monkeypatch.setattr(_polite, "BACKOFF_BASE", 0.0)


def fetch(session, **kwargs):
    return asyncio.run(
        _polite.fetch_html(session, "https://www.bergfex.at/x/", **kwargs)
    )


def test_a_persistent_429_is_asked_at_most_three_times():
    session = FakeSession(FakeResponse(429))
    assert fetch(session) is None
    assert session.calls == _polite.MAX_ATTEMPTS == 3


def test_a_429_that_clears_returns_the_page():
    session = FakeSession(FakeResponse(429), FakeResponse(200, body="ok"))
    assert fetch(session) == "ok"
    assert session.calls == 2


@pytest.mark.parametrize("status", [403, 404, 451, 500])
def test_anything_but_a_429_is_asked_once(status):
    session = FakeSession(FakeResponse(status))
    assert fetch(session) is None
    assert session.calls == 1


def test_every_refusal_is_reported():
    seen = []
    session = FakeSession(FakeResponse(429))
    fetch(session, on_refusal=lambda r: seen.append(r.status))
    assert seen == [429, 429, 429]


def test_a_long_retry_after_gives_the_page_up():
    session = FakeSession(FakeResponse(429, {"retry-after": "3600"}))
    assert fetch(session) is None
    assert session.calls == 1


def test_identifies_as_home_assistant_not_a_browser():
    session = FakeSession(FakeResponse(200))
    fetch(session)
    assert session.user_agents[0].startswith("HomeAssistant/")
    assert "Mozilla" not in session.user_agents[0]


class TestRetryAfter:
    def test_seconds(self):
        assert _polite.retry_after_seconds("30") == 30.0

    def test_http_date(self):
        now = datetime.datetime(2026, 10, 26, 7, 0, tzinfo=datetime.timezone.utc)
        value = "Mon, 26 Oct 2026 07:00:45 GMT"
        assert _polite.retry_after_seconds(value, now) == 45.0

    @pytest.mark.parametrize("value", [None, "", "soon"])
    def test_unreadable_means_absent(self, value):
        assert _polite.retry_after_seconds(value) is None

    def test_is_honoured(self):
        assert _polite.backoff_delay(1, "20") == 20.0

    def test_without_it_the_wait_doubles(self, monkeypatch):
        monkeypatch.setattr(_polite, "BACKOFF_BASE", 10.0)
        monkeypatch.setattr(_polite.random, "uniform", lambda a, b: 1.0)
        assert [_polite.backoff_delay(n, None) for n in (1, 2)] == [10.0, 20.0]
