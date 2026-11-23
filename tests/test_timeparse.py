"""Characterisation tests for timestamp parsing."""

from datetime import datetime

import pytest

from logtool.timeparse import TS_FORMAT, parse_timestamp


@pytest.mark.parametrize(
    "value",
    [
        "10/Oct/2024:13:55:36 +0000",
        "01/Jan/2023:00:00:00 -0530",
        "29/Feb/2024:23:59:59 +1400",
        "31/Dec/2024:23:59:59 -0800",
        "15/Jun/2024:12:30:45 +0545",
    ],
)
def test_matches_reference(value):
    expected = datetime.strptime(value, TS_FORMAT)
    actual = parse_timestamp(value)
    assert actual == expected
    assert actual.utcoffset() == expected.utcoffset()


@pytest.mark.parametrize(
    "value",
    [
        "10/Oct/2024 13:55:36 +0000",
        "10/Xyz/2024:13:55:36 +0000",
        "garbage",
        "31/Feb/2024:13:55:36 +0000",
        "10/Oct/2024:25:55:36 +0000",
        "10/Oct/2024:13:55:36 *0000",
        "10/Oct/2024:13:55:36 +2500",
    ],
)
def test_invalid_timestamp(value):
    with pytest.raises(ValueError):
        parse_timestamp(value)
