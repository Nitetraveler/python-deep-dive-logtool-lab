"""Tests for polymorphic report rendering."""

import json

import pytest

from logtool.reporters import (
    JsonReporter,
    Reporter,
    TextReporter,
    get_reporter,
)

DATA = {
    "records": 5,
    "error_rate": 0.6,
    "status_classes": {"2xx": 1, "5xx": 4},
    "top_ip": [("10.0.0.1", 3)],
}


def test_text_reporter():
    text = TextReporter().render(DATA)
    assert f"{'records':<18} 5" in text
    assert f"{'error_rate':<18} 60.00%" in text
    assert "status_classes:" in text
    assert f"  {'2xx':<16} 1" in text
    assert f"  {'10.0.0.1':<16} 3" in text


def test_json_reporter():
    result = json.loads(JsonReporter().render(DATA))
    assert result["records"] == 5
    assert result["error_rate"] == 0.6
    assert result["status_classes"] == DATA["status_classes"]
    assert result["top_ip"] == [["10.0.0.1", 3]]


@pytest.mark.parametrize(
    "name,expected_type",
    [("text", TextReporter), ("json", JsonReporter)],
)
def test_factory(name, expected_type):
    assert isinstance(get_reporter(name), expected_type)


def test_unknown_format():
    with pytest.raises(ValueError, match="unknown format"):
        get_reporter("invalid")


def test_abstract_reporter():
    with pytest.raises(TypeError):
        Reporter()
