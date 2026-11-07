from datetime import UTC, datetime


def utc_now() -> datetime:
    """Current UTC time, cut to milliseconds: the precision BSON dates keep.

    Without this, a value returned at creation would differ from the same value read back later.
    """
    now = datetime.now(UTC)
    return now.replace(microsecond=now.microsecond // 1000 * 1000)
