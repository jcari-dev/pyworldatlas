"""Capital and populated-place models."""

from __future__ import annotations

from dataclasses import dataclass

from .geography import Coordinate


@dataclass(frozen=True, slots=True)
class Capital:
    """A national capital sourced from GeoNames."""

    name: str
    country_code: str
    coordinates: Coordinate
    role: str = "official"
    primary: bool = True
    largest_city: bool | None = None
    population: int | None = None
    elevation_m: float | None = None
    timezone_id: str | None = None
    alternate_names: tuple[str, ...] = ()
    geonames_id: int | None = None

    def __repr__(self) -> str:
        return f"Capital(name={self.name!r}, country_code={self.country_code!r})"


@dataclass(frozen=True, slots=True)
class City:
    """An immutable bundled populated place.

    Every city has a display name, country code, and WGS84 coordinates.
    Population, elevation, timezone, capital roles, alternate names, and the
    GeoNames identifier are optional snapshot fields.
    """

    name: str
    country_code: str
    coordinates: Coordinate
    population: int | None = None
    elevation_m: float | None = None
    timezone_id: str | None = None
    capital_roles: tuple[str, ...] = ()
    alternate_names: tuple[str, ...] = ()
    geonames_id: int | None = None

    @property
    def label(self) -> str:
        """Return a compact place label such as ``"Tokyo (JP)"``."""
        return f"{self.name} ({self.country_code})"

    def __str__(self) -> str:
        return self.label


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
