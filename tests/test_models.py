"""Tests for the immutable domain model."""

from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone

import pytest

from logtool.models import LogRecord, ParseError


def test_all_fields(sample_lines):
    r = LogRecord.from_line(sample_lines[0])
    assert r.ip == "10.0.0.1"
    assert r.method == "GET"
    assert r.path == "/index.html"
    assert r.status == 200
    assert r.size == 2326
    assert r.agent == "curl/7.81.0"
    assert r.timestamp == datetime(
        2024, 10, 10, 13, 55, 36, tzinfo=timezone.utc
    )


def test_dash_size(sample_lines):
    r = LogRecord.from_line(sample_lines[4])
    assert r.size == 0
    assert r.status_class == "3xx"


def test_common_format():
    r = LogRecord.from_line(
        '10.0.0.3 - - [10/Oct/2024:14:01:12 +0200] '
        '"GET /x HTTP/1.1" 304 -'
    )
    assert r.agent == ""
    assert r.size == 0
    assert r.timestamp.utcoffset() == timedelta(hours=2)


@pytest.mark.parametrize(
    "line",
    [
        "",
        "corrupted log",
        '10.0.0.1 - - [10/Oct/2024:13:55:36 +0000] '
        '"get / HTTP/1.1" 200 10',
        '10.0.0.1 - - [10/Oct/2024:13:55:36 +0000] '
        '"GET / HTTP/1.1" 2000 10',
    ],
)
def test_invalid_lines(line):
    with pytest.raises(ParseError) as caught:
        LogRecord.from_line(line)
    assert caught.value.line == line
    assert caught.value.reason == "unrecognised log format"


def test_bad_timestamp():
    line = (
        '10.0.0.1 - - [10/Xyz/2024:13:55:36 +0000] '
        '"GET / HTTP/1.1" 200 10'
    )
    with pytest.raises(ParseError) as caught:
        LogRecord.from_line(line)
    assert caught.value.reason == "bad timestamp"
    assert caught.value.line == line
    assert isinstance(caught.value.__cause__, ValueError)


@pytest.mark.parametrize(
    "status,expected_class,expected_error",
    [
        (200, "2xx", False),
        (304, "3xx", False),
        (400, "4xx", True),
        (404, "4xx", True),
        (503, "5xx", True),
    ],
)
def test_status_properties(
    sample_lines, status, expected_class, expected_error
):
    r = LogRecord.from_line(
        sample_lines[0].replace(" 200 ", f" {status} ")
    )
    assert r.status_class == expected_class
    assert r.is_error is expected_error


def test_str_frozen_and_hashable(sample_lines):
    r = LogRecord.from_line(sample_lines[0])
    assert str(r) == (
        "2024-10-10 13:55:36 10.0.0.1 GET /index.html -> 200"
    )
    with pytest.raises(FrozenInstanceError):
        r.status = 500
    assert not hasattr(r, "__dict__")
    assert len({r, LogRecord.from_line(sample_lines[0])}) == 1


def test_timezone_offset_equality(sample_lines):
    a = LogRecord.from_line(sample_lines[0])
    b = LogRecord.from_line(
        sample_lines[0].replace("13:55:36 +0000", "15:55:36 +0200")
    )
    assert a.timestamp == b.timestamp
    assert a == b
