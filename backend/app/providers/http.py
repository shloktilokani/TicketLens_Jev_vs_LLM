"""The one HTTP call both provider adapters use: timeouts, error mapping, JSON parsing, retries.

Provider calls can cost money, so retries are bounded and narrow (ai-evaluation.md section 12).
Retried: a refused connection (nothing was sent), 429 and 5xx. Never retried: other 4xx, timeouts
and broken connections, because the provider may already have processed and charged for the call.
"""

import logging
import random
import time

import httpx

from app.providers.base import ProviderFailure, failure_for_status

log = logging.getLogger("ticketlens")

RETRY_DELAYS_SECONDS = (1.0, 3.0)  # so at most three attempts in all
RETRY_STATUSES = {429}  # plus every 5xx
MAX_RETRY_AFTER_SECONDS = 10.0


def get_json(
    url: str,
    *,
    label: str,
    timeout: float,
    headers: dict | None = None,
    client: httpx.Client | None = None,
) -> dict:
    """GET JSON, with the same safe errors as post_json."""
    return request_json("GET", url, None, label, timeout, headers, client)


def post_json(
    url: str,
    body: dict,
    *,
    label: str,
    timeout: float,
    headers: dict | None = None,
    client: httpx.Client | None = None,
) -> dict:
    """POST `body` as JSON and return the JSON reply, or raise a safe ProviderFailure."""
    return request_json("POST", url, body, label, timeout, headers, client)


def pause(seconds: float) -> None:
    time.sleep(seconds)


def retry_wait(response: httpx.Response | None, delay: float) -> float:
    """The provider's Retry-After, capped, or the backoff delay with jitter."""
    if response is not None:
        try:
            return min(float(response.headers["Retry-After"]), MAX_RETRY_AFTER_SECONDS)
        except (KeyError, ValueError):
            pass
    return delay * random.uniform(1, 1.5)


def send_once(
    client: httpx.Client,
    method: str,
    url: str,
    body: dict | None,
    label: str,
    timeout: float,
    headers: dict | None,
) -> httpx.Response:
    try:
        return client.request(method, url, json=body, headers=headers or {})
    except httpx.TimeoutException:
        raise ProviderFailure(
            "timeout", f"{label} did not answer within {timeout:g} s.", request_payload=body
        ) from None
    except httpx.ConnectError:
        raise  # nothing was sent, so the caller may safely try again
    except httpx.HTTPError:
        raise ProviderFailure(
            "network", f"Could not reach {label} at {url}. Is it running?", request_payload=body
        ) from None


def send_with_retries(
    client: httpx.Client,
    method: str,
    url: str,
    body: dict | None,
    label: str,
    timeout: float,
    headers: dict | None,
) -> httpx.Response:
    """Retry only a refused connection, 429 and 5xx. See the module note for why."""
    for delay in RETRY_DELAYS_SECONDS:
        try:
            response = send_once(client, method, url, body, label, timeout, headers)
        except httpx.ConnectError:
            response = None
        if (
            response is not None
            and response.status_code not in RETRY_STATUSES
            and response.status_code < 500
        ):
            return response
        log.warning("%s: temporary failure, retrying", label)
        pause(retry_wait(response, delay))
    try:
        return send_once(client, method, url, body, label, timeout, headers)
    except httpx.ConnectError:
        raise ProviderFailure(
            "network", f"Could not reach {label} at {url}. Is it running?", request_payload=body
        ) from None


def request_json(
    method: str,
    url: str,
    body: dict | None,
    label: str,
    timeout: float,
    headers: dict | None,
    client: httpx.Client | None,
) -> dict:
    own = client is None
    client = client or httpx.Client(timeout=timeout)
    try:
        response = send_with_retries(client, method, url, body, label, timeout, headers)
    finally:
        if own:
            client.close()
    try:
        payload = response.json()
    except ValueError:
        payload = None
    if response.status_code >= 400:
        failure = failure_for_status(label, response.status_code)
        failure.request_payload = body
        failure.response_payload = payload if isinstance(payload, dict) else None
        raise failure
    if not isinstance(payload, dict):
        raise ProviderFailure(
            "invalid_response",
            f"{label} returned something that is not JSON.",
            request_payload=body,
        )
    return payload
