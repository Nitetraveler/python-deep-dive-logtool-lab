"""Test-driven challenge extension requirements."""

import csv
import io
import json
from datetime import UTC, datetime

import pytest

from logtool.analyzer import hourly_counts
from logtool.cli import main
from logtool.reader import between, parse_records, read_lines
from logtool.reporters import REPORTERS, Reporter, get_reporter, register


def records(log_file):
    return parse_records(read_lines([log_file]))


def test_between_no_bounds(log_file):
    assert len(list(between(records(log_file)))) == 5


def test_between_since(log_file):
    since = datetime(2024, 10, 10, 14, tzinfo=UTC)
    assert len(list(between(records(log_file), since=since))) == 2


def test_between_until(log_file):
    until = datetime(2024, 10, 10, 13, 55, 37, tzinfo=UTC)
    assert len(list(between(records(log_file), until=until))) == 2


def test_between_inclusive(log_file):
    boundary = datetime(2024, 10, 10, 13, 56, tzinfo=UTC)
    result = list(between(records(log_file), since=boundary, until=boundary))
    assert len(result) == 1
    assert result[0].status == 500


def test_hourly_counts(log_file):
    assert hourly_counts(records(log_file)) == [
        ("2024-10-10 13:00", 3),
        ("2024-10-10 14:00", 2),
    ]


def test_hourly_empty():
    assert hourly_counts([]) == []


def test_reporter_registration():
    class DemoReporter(Reporter):
        name = "demo"

        def render(self, data):
            return "demo"

    try:
        assert register(DemoReporter) is DemoReporter
        assert isinstance(get_reporter("demo"), DemoReporter)
    finally:
        REPORTERS.pop("demo", None)


def test_csv_reporter():
    reporter = get_reporter("csv")
    output = reporter.render({"top_ip": [("10.0.0.1", 3)]})
    assert list(csv.reader(io.StringIO(output))) == [
        ["key", "value"],
        ["10.0.0.1", "3"],
    ]


def test_csv_mapping_and_scalar():
    output = get_reporter("csv").render({"records": 5, "status_classes": {"2xx": 1}})
    assert list(csv.reader(io.StringIO(output))) == [
        ["key", "value"],
        ["records", "5"],
        ["2xx", "1"],
    ]


def test_hourly_cli(log_file, capsys):
    assert main(["hourly", str(log_file), "-f", "json"]) == 0

    result = json.loads(capsys.readouterr().out)
    assert result["hourly"] == [
        ["2024-10-10 13:00", 3],
        ["2024-10-10 14:00", 2],
    ]


def test_hourly_cli_range(log_file, capsys):
    assert (
        main(
            [
                "hourly",
                str(log_file),
                "--since",
                "2024-10-10T14:00:00",
                "--until",
                "2024-10-10T14:59:59",
                "-f",
                "json",
            ]
        )
        == 0
    )

    result = json.loads(capsys.readouterr().out)
    assert result["hourly"] == [["2024-10-10 14:00", 2]]


def test_invalid_date(log_file):
    with pytest.raises(SystemExit) as exc:
        main(["hourly", str(log_file), "--since", "yesterday"])

    assert exc.value.code == 2


def test_csv_cli(log_file, capsys):
    assert main(["top", str(log_file), "--by", "ip", "-f", "csv"]) == 0

    rows = list(csv.reader(io.StringIO(capsys.readouterr().out)))
    assert rows[0] == ["key", "value"]
    assert rows[1] == ["10.0.0.1", "3"]


def test_hourly_cli_explicit_timezone(log_file, capsys):
    assert (
        main(
            [
                "hourly",
                str(log_file),
                "--since",
                "2024-10-10T16:00:00+02:00",
                "--until",
                "2024-10-10T16:59:59+02:00",
                "-f",
                "json",
            ]
        )
        == 0
    )

    result = json.loads(capsys.readouterr().out)
    assert result["hourly"] == [["2024-10-10 14:00", 2]]
