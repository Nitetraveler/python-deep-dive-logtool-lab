"""Polymorphic reporters and decorator-based registration."""

import csv
import io
import json
from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import TypeVar


class Reporter(ABC):
    name = "base"

    @abstractmethod
    def render(self, data: Mapping[str, object]) -> str:
        """Render report data."""


REPORTERS: dict[str, type[Reporter]] = {}

ReporterType = TypeVar("ReporterType", bound=Reporter)


def register(cls: type[ReporterType]) -> type[ReporterType]:
    """Register a reporter class and return it unchanged."""
    REPORTERS[cls.name] = cls
    return cls


@register
class TextReporter(Reporter):
    name = "text"

    def render(self, data: Mapping[str, object]) -> str:
        lines: list[str] = []

        for key, value in data.items():
            if isinstance(value, Mapping):
                lines.append(f"{key}:")
                for k, v in value.items():
                    lines.append(f"  {k!s:<16} {v}")
            elif isinstance(value, list):
                lines.append(f"{key}:")
                for item, count in value:
                    lines.append(f"  {item!s:<16} {count}")
            elif isinstance(value, float):
                lines.append(f"{key:<18} {value:.2%}")
            else:
                lines.append(f"{key:<18} {value}")

        return "\n".join(lines)


@register
class JsonReporter(Reporter):
    name = "json"

    def render(self, data: Mapping[str, object]) -> str:
        return json.dumps(data, indent=2)


@register
class CsvReporter(Reporter):
    name = "csv"

    def render(self, data: Mapping[str, object]) -> str:
        buffer = io.StringIO()
        writer = csv.writer(buffer, lineterminator="\n")
        writer.writerow(["key", "value"])

        for key, value in data.items():
            if isinstance(value, Mapping):
                writer.writerows(value.items())
            elif isinstance(value, list):
                writer.writerows(value)
            else:
                writer.writerow([key, value])

        return buffer.getvalue().rstrip("\n")


def get_reporter(name: str) -> Reporter:
    try:
        return REPORTERS[name]()
    except KeyError:
        raise ValueError(
            f"unknown format {name!r}; use one of {sorted(REPORTERS)}"
        ) from None
