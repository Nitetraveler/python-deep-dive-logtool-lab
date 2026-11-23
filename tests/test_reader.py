"""Tests for streaming generator pipelines."""

from itertools import islice
from types import GeneratorType

from logtool.reader import (
    ParseStats,
    filter_records,
    parse_records,
    read_lines,
)


def test_read_lines_skips_blank(log_file):
    lines = list(read_lines([log_file]))
    assert len(lines) == 6
    assert "" not in lines


def test_multiple_files(log_file, gz_log_file):
    assert len(list(read_lines([log_file, gz_log_file]))) == 12


def test_lazy_pipeline(log_file):
    stats = ParseStats()
    lines = read_lines([log_file])
    records = parse_records(lines, stats)
    assert isinstance(lines, GeneratorType)
    assert isinstance(records, GeneratorType)
    assert stats.lines == 0
    assert next(records).status == 200
    assert stats.lines == 1
    records.close()
    lines.close()


def test_parse_statistics(log_file):
    stats = ParseStats()
    records = list(parse_records(read_lines([log_file]), stats))
    assert len(records) == 5
    assert stats.lines == 6
    assert stats.malformed == 1


def test_generator_exhaustion(log_file):
    records = parse_records(read_lines([log_file]))
    assert len(list(records)) == 5
    assert list(records) == []


def test_islice(log_file):
    records = parse_records(read_lines([log_file]))
    assert [r.status for r in islice(records, 2)] == [200, 401]
    records.close()


def test_exact_status(log_file):
    records = parse_records(read_lines([log_file]))
    assert [r.status for r in filter_records(records, status=500)] == [500]


def test_combined_filter(log_file):
    records = parse_records(read_lines([log_file]))
    filtered = filter_records(
        records, min_status=400, path_prefix="/api"
    )
    assert [r.status for r in filtered] == [500, 404]


def test_no_filter(log_file):
    records = parse_records(read_lines([log_file]))
    assert len(list(filter_records(records))) == 5
