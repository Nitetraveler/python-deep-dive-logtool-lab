"""Polymorphic text and JSON report rendering."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from collections.abc import Mapping


class Reporter(ABC):
    """Abstract base class for all report formats."""

    name = "base"

    @abstractmethod
    def render(self, data: Mapping[str, object]) -> str:
        """Render report data into a string."""
        ...


class TextReporter(Reporter):
    """Human-readable text reports."""

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


class JsonReporter(Reporter):
    """Machine-readable JSON reports."""

    name = "json"

    def render(self, data: Mapping[str, object]) -> str:
        return json.dumps(data, indent=2)


REPORTERS: dict[str, type[Reporter]] = {
    cls.name: cls for cls in (TextReporter, JsonReporter)
}


def get_reporter(name: str) -> Reporter:
    """Construct a reporter by its registered name."""
    try:
        return REPORTERS[name]()
    except KeyError:
        raise ValueError(
            f"unknown format {name!r}; use one of {sorted(REPORTERS)}"
        ) from None
