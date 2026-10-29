"""Compact result models returned by searches, rankings, and routes."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
import json
from typing import TYPE_CHECKING, Any

from ._serialize import _jsonable
from ._display import friendly_repr
from .geography import Coordinate
from .places import Capital, City, Place, WorldHeritageSite
from .units import Distance

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

    @property
    def country_code(self) -> str:
        """Return the two-letter code, the same value other results call ``country_code``."""
        return self.alpha2

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return friendly_repr(self, f"name={self.name!r}, alpha2={self.alpha2!r}")


@dataclass(frozen=True, slots=True)
class CountryRanking:
    """One deterministic position in a country ranking."""

    position: int
    country: CountryReference
    metric: str
    value: int | float
    unit: str

    def __str__(self) -> str:
        value = f"{self.value:,}" if float(self.value).is_integer() else f"{self.value:,.2f}"
        return f"#{self.position} {self.country.name}: {value} {self.unit}"

    def __repr__(self) -> str:
        return friendly_repr(self, f"{str(self)!r}")

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

    def __post_init__(self) -> None:
        # Store the distance as a Distance, a float that prints as "1,153 km".
        object.__setattr__(self, "distance", Distance(self.distance, self.unit))

    def __str__(self) -> str:
        return f"{self.capital.name}, {self.country.name} · {self.distance}"

    def __repr__(self) -> str:
        return friendly_repr(self, f"{str(self)!r}")

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

    def __post_init__(self) -> None:
        # Store the distance as a Distance, a float that prints as "1,153 km".
        object.__setattr__(self, "distance", Distance(self.distance, self.unit))

    def __str__(self) -> str:
        return f"{self.city.label} · {self.distance}"

    def __repr__(self) -> str:
        return friendly_repr(self, f"{str(self)!r}")

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-compatible primitives for this nearby-city result."""
        data: dict[str, Any] = _jsonable(self)
        return data

    def to_json(self, indent: int | None = None) -> str:
        """Serialize this nearby-city result without escaping Unicode text."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)


@dataclass(frozen=True, slots=True)
class PlaceDistance:
    """A nearby place and its great-circle distance from an origin.

    ``unit`` records the unit requested from :meth:`pyworldatlas.Atlas.places_near`.
    """

    place: Place
    distance: float
    unit: str

    def __post_init__(self) -> None:
        # Store the distance as a Distance, a float that prints as "1,153 km".
        object.__setattr__(self, "distance", Distance(self.distance, self.unit))

    def __str__(self) -> str:
        return f"{self.place.label} · {self.distance}"

    def __repr__(self) -> str:
        return friendly_repr(self, f"{str(self)!r}")

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-compatible primitives for this nearby-place result."""
        data: dict[str, Any] = _jsonable(self)
        return data

    def to_json(self, indent: int | None = None) -> str:
        """Serialize this nearby-place result without escaping Unicode text."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)


@dataclass(frozen=True, slots=True)
class SiteDistance:
    """A World Heritage site and its great-circle distance from an origin."""

    site: WorldHeritageSite
    distance: float
    unit: str

    def __post_init__(self) -> None:
        # Store the distance as a Distance, a float that prints as "1,153 km".
        object.__setattr__(self, "distance", Distance(self.distance, self.unit))

    def __str__(self) -> str:
        return f"{self.site.label} · {self.distance}"

    def __repr__(self) -> str:
        return friendly_repr(self, f"{str(self)!r}")

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-compatible primitives for this nearby-site result."""
        data: dict[str, Any] = _jsonable(self)
        return data

    def to_json(self, indent: int | None = None) -> str:
        """Serialize this nearby-site result without escaping Unicode text."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)


@dataclass(frozen=True, slots=True)
class Antipode:
    """The point on the exact opposite side of the Earth from an origin.

    ``nearest`` lists the known places closest to the antipode, nearest first;
    most antipodes are at sea, so the nearest place can be far away.
    """

    origin: Coordinate
    antipode: Coordinate
    nearest: tuple[PlaceDistance, ...]

    @property
    def summary(self) -> str:
        """Return a plain-language description of the antipode."""
        text = (
            f"Straight through the centre of the Earth from {self.origin.format(precision=2)} "
            f"you would come out at {self.antipode.format(precision=2)}."
        )
        if self.nearest:
            first = self.nearest[0]
            text += f" The nearest known place there is {first.place}, {first.distance} away."
        return text

    def __str__(self) -> str:
        return self.summary

    def __repr__(self) -> str:
        return friendly_repr(self, f"{self.antipode.format(precision=2)!r}")

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-compatible primitives for this antipode."""
        data: dict[str, Any] = _jsonable(self)
        return data

    def to_json(self, indent: int | None = None) -> str:
        """Serialize this antipode as JSON."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)


@dataclass(frozen=True, slots=True)
class SunTimes:
    """Sunrise, sunset, and daylight for one place on one date.

    ``sunrise``, ``sunset``, and ``solar_noon`` are in UTC. When the place's
    time zone is known (``timezone_id``, such as ``"Europe/Paris"``) and the
    computer has time zone data, :attr:`local_sunrise` and
    :attr:`local_sunset` give the local clock times and the summary uses them.
    ``sunrise`` and ``sunset`` are ``None`` during the midnight sun (day length
    24 hours) and the polar night (day length 0). A UTC time can fall on the
    day before or after ``date`` far from Greenwich. ``noon_sun_height`` is the
    sun's angle above the horizon at solar noon, in degrees; it is negative
    when the sun stays below the horizon.
    """

    coordinates: Coordinate
    date: date
    solar_noon: datetime
    sunrise: datetime | None
    sunset: datetime | None
    day_length_hours: float
    noon_sun_height: float
    timezone_id: str | None = None

    def _local(self, moment: datetime | None) -> datetime | None:
        if moment is None or self.timezone_id is None:
            return None
        try:
            from zoneinfo import ZoneInfo
            # Windows has no built-in time zone data unless the optional
            # tzdata package is installed, so a missing zone means "unknown".
            return moment.astimezone(ZoneInfo(self.timezone_id))
        except (ImportError, LookupError, ValueError):
            return None

    @property
    def local_sunrise(self) -> datetime | None:
        """Return sunrise on the local clock, or ``None`` when the time zone is unknown."""
        return self._local(self.sunrise)

    @property
    def local_sunset(self) -> datetime | None:
        """Return sunset on the local clock, or ``None`` when the time zone is unknown."""
        return self._local(self.sunset)

    @property
    def daylight(self) -> str:
        """Return the day length as text, such as ``"16 h 38 min"``."""
        minutes = round(self.day_length_hours * 60)
        return f"{minutes // 60} h {minutes % 60:02d} min"

    @property
    def summary(self) -> str:
        """Return a plain-language description of the day."""
        when = f"{self.date.day} {self.date:%B %Y}"
        if self.sunrise is None or self.sunset is None:
            if self.day_length_hours >= 24:
                return f"On {when} the sun does not set: this is the midnight sun."
            return f"On {when} the sun does not rise: this is the polar night."
        local = self.local_sunrise is not None and self.local_sunset is not None

        def clock(moment: datetime) -> str:
            shown = self._local(moment) if local else moment
            assert shown is not None
            text = f"{shown:%H:%M} {'local time' if local else 'UTC'}"
            if shown.date() != self.date:
                text += f" on {shown.day} {shown:%B}"
            return text

        return (
            f"On {when} the sun rises at {clock(self.sunrise)} and sets at "
            f"{clock(self.sunset)}, giving {self.daylight} of daylight. At noon "
            f"it is {self.noon_sun_height:.0f}° above the horizon."
        )

    def __str__(self) -> str:
        return self.summary

    def __repr__(self) -> str:
        if self.sunrise is None or self.sunset is None:
            return friendly_repr(self, f"{self.date.isoformat()}, daylight={self.daylight!r}")
        return friendly_repr(
            self,
            f"{self.date.isoformat()}, sunrise='{self.sunrise:%H:%M} UTC', "
            f"sunset='{self.sunset:%H:%M} UTC', daylight={self.daylight!r}",
        )

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-compatible primitives for these sun times."""
        data: dict[str, Any] = _jsonable(self)
        return data

    def to_json(self, indent: int | None = None) -> str:
        """Serialize these sun times as JSON."""
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

    def __str__(self) -> str:
        crossings = "crossing" if self.crossings == 1 else "crossings"
        return f"{' → '.join(self.names)} ({self.crossings} border {crossings})"

    def __repr__(self) -> str:
        return friendly_repr(self, f"{str(self)!r}")

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

    def __str__(self) -> str:
        if self.matched_name == self.country.name:
            return self.country.name
        return f"{self.country.name} (matched {self.matched_name!r})"

    def __repr__(self) -> str:
        return friendly_repr(self, f"{str(self)!r}")
