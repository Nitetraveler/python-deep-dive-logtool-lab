"""Timestamp parsing for access-log lines."""

from __future__ import annotations

from datetime import datetime

TS_FORMAT = "%d/%b/%Y:%H:%M:%S %z"


def parse_timestamp(value: str) -> datetime:
    """Convert '10/Oct/2024:13:55:36 +0000' into a timezone-aware datetime."""
    return datetime.strptime(value, TS_FORMAT)
