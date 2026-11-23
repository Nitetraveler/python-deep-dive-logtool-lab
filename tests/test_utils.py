"""Tests for context managers and decorators."""

import inspect
import logging
import time

import pytest

from logtool.utils import Timer, deprecated, open_log, timed


def test_open_plain(log_file):
    with open_log(log_file) as fh:
        assert not fh.closed
        assert "10.0.0.1" in next(fh)
    assert fh.closed


def test_open_gzip(gz_log_file):
    with open_log(gz_log_file) as fh:
        assert "10.0.0.1" in next(fh)
    assert fh.closed


def test_missing_file(tmp_path):
    with (
        pytest.raises(FileNotFoundError, match="log file not found"),
        open_log(tmp_path / "missing.log"),
    ):
        pass


def test_file_closed_on_exception(log_file):
    with pytest.raises(RuntimeError, match="boom"), open_log(log_file) as fh:
        raise RuntimeError("boom")
    assert fh.closed


def test_timer(caplog):
    with caplog.at_level(logging.INFO), Timer("test block") as timer:
        time.sleep(0.01)
    assert timer.elapsed >= 0.009
    assert "test block took" in caplog.text


def test_timer_exception(caplog):
    with (
        caplog.at_level(logging.INFO),
        pytest.raises(RuntimeError, match="boom"),
        Timer() as timer,
    ):
        raise RuntimeError("boom")
    assert timer.elapsed >= 0
    assert "block took" in caplog.text


def test_timed_metadata_and_result(caplog):
    @timed
    def add(a: int, b: int = 2) -> int:
        """Add two numbers."""
        return a + b

    with caplog.at_level(logging.INFO):
        assert add(3, b=4) == 7
    assert add.__name__ == "add"
    assert add.__doc__ == "Add two numbers."
    assert hasattr(add, "__wrapped__")
    assert inspect.signature(add) == inspect.signature(add.__wrapped__)
    assert "add took" in caplog.text


def test_timed_exception(caplog):
    @timed
    def fail():
        raise ValueError("failure")

    with caplog.at_level(logging.INFO), pytest.raises(ValueError, match="failure"):
        fail()
    assert "fail took" in caplog.text


def test_deprecated_warning():
    @deprecated("use new function")
    def old(x):
        return x + 1

    with pytest.warns(DeprecationWarning, match="use new function"):
        assert old(6) == 7
    assert old.__name__ == "old"
    assert hasattr(old, "__wrapped__")
