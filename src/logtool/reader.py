"""Lazy generator pipelines for reading, parsing and filtering logs."""

from __future__ import annotations

import logging
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from logtool.models import LogRecord, ParseError
from logtool.utils import open_log

log = logging.getLogger(__name__)


@dataclass
class ParseStats:
    """Mutable counters updated as the parsing generator is consumed."""

    lines: int = 0
    malformed: int = 0


def read_lines(paths: Iterable[str | Path]) -> Iterator[str]:
    """Yield non-empty lines from one or more plain/gzip log files."""
    for path in paths:
        with open_log(path) as fh:
            for raw in fh:
                line = raw.rstrip("\r\n")
                if line:
                    yield line


def parse_records(
    lines: Iterable[str], stats: ParseStats | None = None
) -> Iterator[LogRecord]:
    """Parse lines lazily, skipping malformed entries."""
    for line in lines:
        if stats is not None:
            stats.lines += 1
        try:
            yield LogRecord.from_line(line)
        except ParseError as exc:
            if stats is not None:
                stats.malformed += 1
            log.debug("skipping line: %s", exc)


def filter_records(
    records: Iterable[LogRecord],
    *,
    status: int | None = None,
    min_status: int | None = None,
    path_prefix: str | None = None,
) -> Iterator[LogRecord]:
    """Yield records matching all supplied filter criteria."""
    for record in records:
        if status is not None and record.status != status:
            continue
        if min_status is not None and record.status < min_status:
            continue
        if path_prefix is not None and not record.path.startswith(path_prefix):
            continue
        yield record


def between(
    records: Iterable[LogRecord],
    *,
    since: datetime | None = None,
    until: datetime | None = None,
) -> Iterator[LogRecord]:
    """Yield records within inclusive timestamp boundaries."""
    for record in records:
        if since is not None and record.timestamp < since:
            continue
        if until is not None and record.timestamp > until:
            continue
        yield record
