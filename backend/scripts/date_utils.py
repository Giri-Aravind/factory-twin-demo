"""
Date utilities for the parameter extractor.

- expand_period_boundaries: (from, until) -> list of monthly boundary timestamps.
- The LLM never generates boundary lists. Python does.
"""

from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta


def _to_datetime(iso_str: str) -> datetime:
    """Parse an ISO 8601 string into a UTC datetime."""
    # Strip 'Z' and parse; treat as UTC.
    s = iso_str.rstrip("Z")
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _to_iso(dt: datetime) -> str:
    """Format a datetime as an ISO 8601 Instant the GraphQL backend expects."""
    return dt.strftime("%Y-%m-%dT00:00:00Z")


def expand_period_boundaries(from_iso: str, until_iso: str) -> list[str]:
    """
    Return a list of monthly boundary timestamps from `from_iso` (inclusive)
    through `until_iso` (inclusive).

    Each consecutive pair of boundaries forms one bucket on the histogram.
    Boundaries are normalized to the first day of the month at 00:00:00 UTC.

    Example:
        from_iso = "2025-01-01T00:00:00Z"
        until_iso = "2025-04-01T00:00:00Z"
        returns:
        ["2025-01-01T00:00:00Z",
         "2025-02-01T00:00:00Z",
         "2025-03-01T00:00:00Z",
         "2025-04-01T00:00:00Z"]
        (= 3 monthly buckets: Jan, Feb, Mar)
    """
    start = _to_datetime(from_iso).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    end = _to_datetime(until_iso).replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    if end < start:
        # Defensive: if user/LLM gives reversed range, swap.
        start, end = end, start

    boundaries = []
    cursor = start
    while cursor <= end:
        boundaries.append(_to_iso(cursor))
        cursor += relativedelta(months=1)

    return boundaries