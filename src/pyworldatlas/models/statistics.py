"""Official statistics: indicators, yearly values, and time series."""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any

from ._serialize import _jsonable
from ._display import friendly_repr

_BARS = "▁▂▃▄▅▆▇█"


@dataclass(frozen=True, slots=True)
class Indicator:
    """One statistic, such as life expectancy, with its unit and source.

    ``key`` is the short name used by the atlas (``"life_expectancy"``) and
    ``code`` the World Bank indicator code (``"SP.DYN.LE00.IN"``).
    """

    key: str
    name: str
    unit: str
    code: str
    source: str
    decimals: int = 1

    def format(self, value: float) -> str:
        """Return a value with its unit, such as ``"84.7 years"``."""
        number = f"{value:,.{self.decimals}f}"
        return f"{number}{self.unit}" if self.unit.startswith("%") else f"{number} {self.unit}"

    def __str__(self) -> str:
        return f"{self.name} ({self.unit})"

    def __repr__(self) -> str:
        return friendly_repr(self, f"key={self.key!r}, unit={self.unit!r}")


@dataclass(frozen=True, slots=True)
class StatisticValue:
    """One published value: an indicator for a country (or the world) in a year."""

    indicator: Indicator
    area: str
    year: int
    value: float

    @property
    def country_code(self) -> str | None:
        """Return the two-letter country code, or ``None`` for the world total."""
        return None if self.area == "world" else self.area

    def __str__(self) -> str:
        return f"{self.indicator.format(self.value)} ({self.year})"

    def __repr__(self) -> str:
        return friendly_repr(
            self, f"indicator={self.indicator.key!r}, area={self.area!r}, year={self.year}, value={self.value!r}"
        )

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-compatible primitives for this value."""
        data: dict[str, Any] = _jsonable(self)
        return data

    def to_json(self, indent: int | None = None) -> str:
        """Serialize this value as JSON."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)


@dataclass(frozen=True, slots=True)
class StatisticSeries:
    """Yearly values of one indicator for one country, or ``"world"``.

    ``values`` runs from ``first_year`` one year at a time; a year the
    publisher has no value for is ``None`` and is never filled in.
    """

    indicator: Indicator
    area: str
    area_name: str
    first_year: int
    values: tuple[float | None, ...]

    @property
    def country_code(self) -> str | None:
        """Return the two-letter country code, or ``None`` for the world total."""
        return None if self.area == "world" else self.area

    def __str__(self) -> str:
        return self.summary

    def __repr__(self) -> str:
        years = f"{self.first_year}-{self.last_year}" if self.values else "no values"
        return friendly_repr(self, f"indicator={self.indicator.key!r}, area={self.area!r}, years={years!r}")

    @property
    def last_year(self) -> int:
        """Return the last year in the series."""
        return self.first_year + len(self.values) - 1

    @property
    def points(self) -> tuple[tuple[int, float], ...]:
        """Return ``(year, value)`` pairs for every year with a value."""
        return tuple(
            (self.first_year + offset, value)
            for offset, value in enumerate(self.values)
            if value is not None
        )

    def value(self, year: int) -> float | None:
        """Return the value for ``year``, or ``None`` when there is none."""
        offset = year - self.first_year
        return self.values[offset] if 0 <= offset < len(self.values) else None

    @property
    def latest(self) -> StatisticValue | None:
        """Return the most recent published value."""
        points = self.points
        if not points:
            return None
        year, value = points[-1]
        return StatisticValue(self.indicator, self.area, year, value)

    def sparkline(self, width: int = 30) -> str:
        """Return a one-line text chart, such as ``"▁▂▃▄▅▆▇█"``.

        The series is shown in at most ``width`` steps, each the average of
        its years; years with no value show as a space.
        """
        if isinstance(width, bool) or not isinstance(width, int) or width < 1:
            raise ValueError("width must be a positive integer")
        known = [value for value in self.values if value is not None]
        if not known:
            return ""
        low, high = min(known), max(known)
        size = max(1, -(-len(self.values) // width))
        line = []
        for start in range(0, len(self.values), size):
            chunk = [value for value in self.values[start:start + size] if value is not None]
            if not chunk:
                line.append(" ")
                continue
            average = sum(chunk) / len(chunk)
            level = 0 if high == low else round((average - low) / (high - low) * (len(_BARS) - 1))
            line.append(_BARS[level])
        return "".join(line)

    @property
    def summary(self) -> str:
        """Return a plain-language sentence about the first and latest values."""
        points = self.points
        if not points:
            return f"No {self.indicator.name.lower()} values are published for {self.area_name}."
        (first_year, first), (last_year, last) = points[0], points[-1]
        name = f"{self.indicator.name} in {self.area_name}"
        if first_year == last_year or first == last:
            return f"{name} was {self.indicator.format(last)} in {last_year}."
        change = "rose" if last > first else "fell"
        return (
            f"{name} {change} from {self.indicator.format(first)} in {first_year} "
            f"to {self.indicator.format(last)} in {last_year}."
        )

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-compatible primitives for this series."""
        data: dict[str, Any] = _jsonable(self)
        return data

    def to_json(self, indent: int | None = None) -> str:
        """Serialize this series as JSON."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)
