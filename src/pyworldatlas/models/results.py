"""Compact result models returned by searches, rankings, and routes."""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import TYPE_CHECKING, Any

from ._serialize import _jsonable
from .places import Capital, City

if TYPE_CHECKING:
    from .country import Country


@dataclass(frozen=True, slots=True)
class CountryReference:
    """A compact, immutable country identifier used in educational results.

    The reference contains display and lookup identifiers only. It deliberately
    avoids nesting a complete :class:`Country` profile inside flashcards and
    discovery results.
    """

    name: str
    alpha2: str
    alpha3: str | None
    numeric: str | None


@dataclass(frozen=True, slots=True)
class CountryRanking:
    """One deterministic position in a country ranking."""

    position: int
    country: CountryReference
    metric: str
    value: int | float
    unit: str

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-compatible primitives for this ranking row."""
        data: dict[str, Any] = _jsonable(self)
        return data

    def to_json(self, indent: int | None = None) -> str:
        """Serialize this ranking row as JSON."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)


@dataclass(frozen=True, slots=True)
class CapitalDistance:
    """A capital ordered by great-circle distance from an origin."""

    country: CountryReference
    capital: Capital
    distance: float
    unit: str

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-compatible primitives for this distance result."""
        data: dict[str, Any] = _jsonable(self)
        return data

    def to_json(self, indent: int | None = None) -> str:
        """Serialize this distance result as JSON."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)


@dataclass(frozen=True, slots=True)
class CityDistance:
    """A nearby populated place and its great-circle distance from an origin.

    The compact country reference disambiguates city names. ``unit`` records
    the unit requested from :meth:`pyworldatlas.Atlas.nearest_cities`.
    """

    country: CountryReference
    city: City
    distance: float
    unit: str

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-compatible primitives for this nearby-city result."""
        data: dict[str, Any] = _jsonable(self)
        return data

    def to_json(self, indent: int | None = None) -> str:
        """Serialize this nearby-city result without escaping Unicode text."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)


@dataclass(frozen=True, slots=True)
class BorderPathResult:
    """A shortest path through the reviewed land-border graph.

    ``countries`` includes both endpoints in travel order. ``crossings`` is
    therefore one fewer than the number of country references. The value is
    detached from the database and remains usable after its :class:`Atlas`
    closes.
    """

    countries: tuple[CountryReference, ...]
    crossings: int

    def __post_init__(self) -> None:
        if not self.countries:
            raise ValueError("a border path must contain at least one country")
        if self.crossings != len(self.countries) - 1:
            raise ValueError("crossings must be one fewer than the country count")

    @property
    def origin(self) -> CountryReference:
        """Return the first country in the path."""
        return self.countries[0]

    @property
    def destination(self) -> CountryReference:
        """Return the last country in the path."""
        return self.countries[-1]

    @property
    def names(self) -> tuple[str, ...]:
        """Return country display names in path order."""
        return tuple(country.name for country in self.countries)

    @property
    def alpha2_codes(self) -> tuple[str, ...]:
        """Return alpha-2 country codes in path order."""
        return tuple(country.alpha2 for country in self.countries)

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-compatible primitives for this path."""
        data: dict[str, Any] = _jsonable(self)
        return data

    def to_json(self, indent: int | None = None) -> str:
        """Serialize this path as JSON without escaping Unicode text."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)


@dataclass(frozen=True, slots=True)
class CountryMatch:
    """A ranked country-search result."""

    country: Country
    matched_name: str
    score: int
