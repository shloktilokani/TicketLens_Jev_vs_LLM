"""Strip credentials from provider payloads before they are stored or shown."""

REDACTED = "[REDACTED]"

# Matched case-insensitively against every key, at any depth.
SECRET_KEYS = {
    "authorization",
    "api_key",
    "apikey",
    "x-api-key",
    "cookie",
    "set-cookie",
    "password",
    "secret",
    "token",
    "access_token",
    "refresh_token",
}


def redact(value):
    """A copy of `value` with every secret-looking key's value replaced. The input is untouched."""
    if isinstance(value, dict):
        return {
            k: REDACTED if str(k).lower() in SECRET_KEYS else redact(v) for k, v in value.items()
        }
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value
