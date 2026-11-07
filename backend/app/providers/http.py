"""The one HTTP call both provider adapters use: timeouts, error mapping, JSON parsing.

No automatic retries: provider calls can cost money (AGENTS.md section 3).
"""

import httpx

from app.providers.base import ProviderFailure, failure_for_status


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
    own = client is None
    client = client or httpx.Client(timeout=timeout)
    try:
        response = client.post(url, json=body, headers=headers or {})
    except httpx.TimeoutException:
        raise ProviderFailure(
            "timeout", f"{label} did not answer within {timeout:g} s.", request_payload=body
        ) from None
    except httpx.HTTPError:
        raise ProviderFailure(
            "network", f"Could not reach {label} at {url}. Is it running?", request_payload=body
        ) from None
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
