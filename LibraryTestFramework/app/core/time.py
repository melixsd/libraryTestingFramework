"""
Shared time helper.

datetime.utcnow() is deprecated (scheduled for removal). The recommended
replacement is datetime.now(timezone.utc), but that returns a timezone-AWARE
datetime, while every DateTime column in our models (see app/models/*.py) is
naive (no timezone=True). Mixing aware and naive datetimes in comparisons or
subtractions raises TypeError, so we strip the tzinfo back off here to keep
exact behavioral parity with the old datetime.utcnow() while silencing the
deprecation warning.
"""
from datetime import datetime, timezone


def utc_now() -> datetime:
    """Current UTC time as a naive datetime (no tzinfo), matching the
    naive DateTime columns used throughout the models."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
