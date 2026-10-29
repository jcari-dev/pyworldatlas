"""Capital and populated-place models."""

from __future__ import annotations

from dataclasses import dataclass

from .geography import Coordinate
from ._display import friendly_repr


@dataclass(frozen=True, slots=True)
class Capital:
    """A national capital sourced from GeoNames."""

    name: str
    country_code: str
    coordinates: Coordinate
    role: str = "official"
    primary: bool = True
    population: int | None = None
    elevation_m: float | None = None
    timezone_id: str | None = None
    geonames_id: int | None = None

    def __repr__(self) -> str:
        return friendly_repr(self, f"name={self.name!r}, country_code={self.country_code!r}")


@dataclass(frozen=True, slots=True)
class City:
    """An immutable bundled populated place.

    Every city has a display name, country code, and WGS84 coordinates.
    Population, elevation, timezone, capital roles, and the GeoNames
    identifier are optional snapshot fields.
    """

    name: str
    country_code: str
    coordinates: Coordinate
    population: int | None = None
    elevation_m: float | None = None
    timezone_id: str | None = None
    capital_roles: tuple[str, ...] = ()
    geonames_id: int | None = None

    @property
    def label(self) -> str:
        """Return a compact place label such as ``"Tokyo (JP)"``."""
        return f"{self.name} ({self.country_code})"

    def __str__(self) -> str:
        return self.label

    def __repr__(self) -> str:
        return friendly_repr(self, f"name={self.name!r}, country_code={self.country_code!r}")


@dataclass(frozen=True, slots=True)
class Airport:
    """An airport with scheduled passenger flights, from OurAirports.

    ``iata_code`` is the three-letter code on tickets and bags (``"LHR"``);
    ``icao_code`` the four-letter code pilots use (``"EGLL"``). ``size`` is
    ``"large"``, ``"medium"``, or ``"small"``. ``country_code`` is the
    two-letter code as published by OurAirports.
    """

    iata_code: str
    icao_code: str | None
    name: str
    municipality: str | None
    country_code: str
    coordinates: Coordinate
    elevation_m: int | None
    size: str

    @property
    def label(self) -> str:
        """Return a compact label such as ``"LHR · London Heathrow Airport (GB)"``."""
        return f"{self.iata_code} · {self.name} ({self.country_code})"

    def __str__(self) -> str:
        return self.label

    def __repr__(self) -> str:
        return friendly_repr(self, f"iata_code={self.iata_code!r}, name={self.name!r}")


@dataclass(frozen=True, slots=True)
class WorldHeritageSite:
    """A site on the UNESCO World Heritage List, from Wikidata.

    ``site_id`` is the list number. ``category`` is ``"cultural"``,
    ``"natural"``, or ``"mixed"`` from the site's selection criteria.
    ``coordinates`` marks one representative point and ``inscribed`` the year
    the site was added, when known. Find sites by name, number, category, or
    distance from any place.
    """

    site_id: int
    name: str
    coordinates: Coordinate | None
    inscribed: int | None
    category: str | None

    @property
    def label(self) -> str:
        """Return a compact label such as ``"Taj Mahal, cultural"``."""
        return f"{self.name}, {self.category}" if self.category else self.name

    def __str__(self) -> str:
        return self.label

    def __repr__(self) -> str:
        return friendly_repr(self, f"site_id={self.site_id!r}, name={self.name!r}")


@dataclass(frozen=True, slots=True)
class Place:
    """Any named place on Earth: a town, mountain, lake, ruin, island, and more.

    Places come from the GeoNames gazetteer. ``kind`` is a plain-English label
    such as ``"mountain"`` and ``category`` its general group such as
    ``"landform"``. ``english_name`` equals ``name`` unless the place has a
    different English name (``"Lago Titicaca"`` is ``"Lake Titicaca"``).
    ``fame`` (0 to 255) estimates how widely a place is known and orders
    search results; it is not a measure of importance.
    """

    name: str
    english_name: str
    kind: str
    category: str
    country_code: str
    coordinates: Coordinate
    population: int | None = None
    elevation_m: int | None = None
    feature_code: str = ""
    fame: int = 0

    @property
    def label(self) -> str:
        """Return a compact label such as ``"Lake Titicaca, lake (PE)"``."""
        country = f" ({self.country_code})" if self.country_code else ""
        return f"{self.english_name}, {self.kind}{country}"

    def __str__(self) -> str:
        return self.label

    def __repr__(self) -> str:
        return friendly_repr(
            self, f"english_name={self.english_name!r}, kind={self.kind!r}, country_code={self.country_code!r}"
        )
