"""Fast timestamp parsing for Apache/Nginx access logs."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from functools import lru_cache

TS_FORMAT = "%d/%b/%Y:%H:%M:%S %z"

_MONTH_NAMES = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()

MONTHS = {name: number for number, name in enumerate(_MONTH_NAMES, start=1)}

_SEPARATORS = "//::: "


@lru_cache(maxsize=64)
def _tz(text: str) -> timezone:
    """Reuse timezone objects for repeated numeric UTC offsets."""
    offset = timedelta(
        hours=int(text[1:3]),
        minutes=int(text[3:5]),
    )
    return timezone(offset if text[0] == "+" else -offset)


def parse_timestamp(value: str) -> datetime:
    """Parse a fixed-format access-log timestamp efficiently."""
    if (
        len(value) != 26
        or value[2] + value[6] + value[11] + value[14] + value[17] + value[20]
        != _SEPARATORS
        or value[21] not in "+-"
    ):
        raise ValueError(f"bad timestamp: {value!r}")

    try:
        return datetime(
            int(value[7:11]),
            MONTHS[value[3:6]],
            int(value[0:2]),
            int(value[12:14]),
            int(value[15:17]),
            int(value[18:20]),
            tzinfo=_tz(value[21:26]),
        )
    except (KeyError, ValueError) as exc:
        raise ValueError(f"bad timestamp: {value!r}") from exc
