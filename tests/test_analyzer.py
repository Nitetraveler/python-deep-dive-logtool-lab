"""Tests for single-pass log aggregation."""

import pytest

from logtool.analyzer import LogAnalyzer, count_errors
from logtool.reader import parse_records, read_lines


@pytest.fixture
def analyzer(log_file):
    return LogAnalyzer(parse_records(read_lines([log_file])))


def test_totals(analyzer):
    assert len(analyzer) == analyzer.total == 5
    assert analyzer.total_bytes == 3030
    assert len(analyzer.ip_counts) == 3
    assert analyzer.error_count == 3
    assert analyzer.error_rate == 0.6


def test_status_classes(analyzer):
    assert analyzer.status_classes() == {
        "2xx": 1,
        "3xx": 1,
        "4xx": 2,
        "5xx": 1,
    }


@pytest.mark.parametrize(
    "field,expected",
    [
        ("ip", [("10.0.0.1", 3), ("10.0.0.2", 1)]),
        ("path", [("/index.html", 2), ("/api/v1/items", 2)]),
        ("status", [("200", 1), ("401", 1)]),
    ],
)
def test_top(analyzer, field, expected):
    assert analyzer.top(field, 2) == expected


def test_unknown_top_field(analyzer):
    with pytest.raises(ValueError, match="unknown field"):
        analyzer.top("unknown")


def test_summary_and_repr(analyzer):
    summary = analyzer.summary()
    assert summary["records"] == 5
    assert summary["total_bytes"] == 3030
    assert summary["unique_ips"] == 3
    assert summary["error_rate"] == 0.6
    assert summary["first_seen"] == "2024-10-10T13:55:36+00:00"
    assert summary["last_seen"] == "2024-10-10T14:05:00+00:00"
    assert repr(analyzer) == (
        "LogAnalyzer(records=5, errors=3, unique_ips=3)"
    )


def test_empty_analyzer():
    a = LogAnalyzer()
    assert len(a) == 0
    assert a.error_count == 0
    assert a.error_rate == 0.0
    assert a.total_bytes == 0
    assert a.status_classes() == {}
    assert a.top("ip") == []
    assert a.summary()["first_seen"] is None
    assert a.summary()["last_seen"] is None


def test_feed_and_out_of_order(log_file):
    records = list(parse_records(read_lines([log_file])))
    a = LogAnalyzer()
    assert a.feed(reversed(records)) is a
    assert len(a) == 5
    assert a.first_seen == records[0].timestamp
    assert a.last_seen == records[-1].timestamp


def test_deprecated_count_errors(log_file):
    with pytest.warns(DeprecationWarning, match="LogAnalyzer"):
        assert count_errors(parse_records(read_lines([log_file]))) == 3
