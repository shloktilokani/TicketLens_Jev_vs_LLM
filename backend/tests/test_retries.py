import httpx
import pytest

from app.core.settings import Settings
from app.providers import http
from app.providers.base import ProviderFailure


def call(replies: list) -> tuple[list[int], dict | ProviderFailure]:
    """POST through a fake server that gives `replies` in order. Returns attempts and the result."""
    attempts = []

    def handler(request: httpx.Request) -> httpx.Response:
        attempts.append(1)
        reply = replies[min(len(attempts) - 1, len(replies) - 1)]
        if isinstance(reply, Exception):
            raise reply
        return reply

    client = httpx.Client(transport=httpx.MockTransport(handler))
    try:
        result = http.post_json("http://x/y", {}, label="Test", timeout=1, client=client)
    except ProviderFailure as failure:
        result = failure
    return attempts, result


OK = httpx.Response(200, json={"ok": True})


@pytest.fixture
def pauses(monkeypatch) -> list[float]:
    seen: list[float] = []
    monkeypatch.setattr(http, "pause", seen.append)
    return seen


@pytest.mark.parametrize("status", [429, 500, 502, 503])
def test_temporary_errors_are_retried_and_can_recover(status, pauses):
    attempts, result = call([httpx.Response(status, json={}), OK])

    assert len(attempts) == 2
    assert result == {"ok": True}
    assert len(pauses) == 1


def test_a_refused_connection_is_retried_because_nothing_was_sent(pauses):
    attempts, result = call([httpx.ConnectError("refused"), OK])

    assert len(attempts) == 2
    assert result == {"ok": True}


def test_retries_stop_after_a_fixed_number_of_attempts(pauses):
    attempts, result = call([httpx.Response(503, json={})])

    assert len(attempts) == 1 + len(http.RETRY_DELAYS_SECONDS)
    assert result.kind == "server_error"
    assert len(pauses) == len(http.RETRY_DELAYS_SECONDS)


def test_backoff_grows_and_has_jitter(pauses):
    call([httpx.Response(500, json={})])

    first, second = http.RETRY_DELAYS_SECONDS
    assert first <= pauses[0] <= first * 1.5
    assert second <= pauses[1] <= second * 1.5


def test_retry_after_is_respected_and_capped(pauses):
    call([httpx.Response(429, json={}, headers={"Retry-After": "2"}), OK])
    call([httpx.Response(429, json={}, headers={"Retry-After": "9999"}), OK])
    call([httpx.Response(429, json={}, headers={"Retry-After": "soon"}), OK])

    assert pauses[0] == 2
    assert pauses[1] == http.MAX_RETRY_AFTER_SECONDS
    assert pauses[2] <= http.RETRY_DELAYS_SECONDS[0] * 1.5


@pytest.mark.parametrize(
    ("status", "kind"),
    [
        (400, "invalid_request"),
        (401, "auth"),
        (402, "insufficient_credits"),
        (403, "auth"),
        (404, "invalid_request"),
        (422, "invalid_request"),
    ],
)
def test_permanent_errors_are_never_retried(status, kind, pauses):
    attempts, result = call([httpx.Response(status, json={})])

    assert len(attempts) == 1
    assert result.kind == kind
    assert pauses == []


@pytest.mark.parametrize(
    "error", [httpx.ReadTimeout("slow"), httpx.ReadError("cut off"), httpx.WriteError("cut off")]
)
def test_a_call_that_may_have_reached_the_provider_is_not_repeated(error, pauses):
    """The provider may already be working on it, and possibly charging for it."""
    attempts, result = call([error])

    assert len(attempts) == 1
    assert isinstance(result, ProviderFailure)
    assert pauses == []


def test_get_requests_share_the_same_rules(pauses):
    attempts = []

    def handler(request: httpx.Request) -> httpx.Response:
        attempts.append(request.method)
        return httpx.Response(500, json={}) if len(attempts) == 1 else OK

    client = httpx.Client(transport=httpx.MockTransport(handler))

    assert http.get_json("http://x", label="Test", timeout=1, client=client) == {"ok": True}
    assert attempts == ["GET", "GET"]


def test_the_api_binds_to_this_computer_only_by_default():
    assert Settings(_env_file=None).api_host == "127.0.0.1"
