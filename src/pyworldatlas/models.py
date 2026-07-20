"""Immutable public data models returned by :class:`pyworldatlas.Atlas`."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from enum import Enum
import json
from typing import Any


class CountryStatus(str, Enum):
    """Political/entity classification used by the bundled dataset."""

    SOVEREIGN_STATE = "sovereign_state"
    DEPENDENCY = "dependency"
    TERRITORY = "territory"
    SPECIAL_AREA = "special_area"
    DISPUTED = "disputed"
    OTHER = "other"


@dataclass(frozen=True, slots=True)
class DatasetInfo:
    """Independent library, schema, and dataset version metadata."""

    library_version: str
    schema_version: int
    dataset_version: str
    country_count: int
    built_at: str


@dataclass(frozen=True, slots=True)
class CountryCodes:
    """Standard identifiers for a country or area."""

    alpha2: str
    alpha3: str | None
    numeric: str | None
    wikidata: str | None = None
    geonames: int | None = None


@dataclass(frozen=True, slots=True)
class LocalizedName:
    """A sourced country name or alias."""

    text: str
    language_code: str | None
    kind: str
    preferred: bool


@dataclass(frozen=True, slots=True)
class Coordinate:
    """A signed WGS84 coordinate in decimal degrees."""

    latitude: float
    longitude: float

    def as_tuple(self) -> tuple[float, float]:
        """Return ``(latitude, longitude)``."""
        return (self.latitude, self.longitude)


@dataclass(frozen=True, slots=True)
class Area:
    """Country area measurements in square kilometres."""

    total_km2: float | None = None
    land_km2: float | None = None
    water_km2: float | None = None
    water_percent: float | None = None
    disputed_km2: float | None = None


@dataclass(frozen=True, slots=True)
class Geography:
    """Core geographic classification and measurements."""

    continent: str | None
    region: str | None
    subregion: str | None
    area: Area = Area()
    centroid: Coordinate | None = None
    landlocked: bool | None = None


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
    """A major populated place sourced from GeoNames."""

    name: str
    country_code: str
    coordinates: Coordinate
    population: int | None = None
    elevation_m: float | None = None
    timezone_id: str | None = None
    capital_roles: tuple[str, ...] = ()
    alternate_names: tuple[str, ...] = ()
    geonames_id: int | None = None


@dataclass(frozen=True, slots=True)
class SourceReference:
    """A source used for fields in a country profile."""

    id: str
    name: str
    homepage: str
    retrieved_at: str


def _jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {field.name: _jsonable(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    return value


@dataclass(frozen=True, slots=True)
class Country:
    """A sourced, immutable country profile from the offline atlas."""

    name: str
    official_name: str | None
    names: tuple[LocalizedName, ...]
    aliases: tuple[str, ...]
    codes: CountryCodes
    flag: str
    status: CountryStatus
    geography: Geography
    capitals: tuple[Capital, ...]
    major_cities: tuple[City, ...]
    sources: tuple[SourceReference, ...]

    @property
    def alpha2(self) -> str:
        """Return the ISO alpha-2 code."""
        return self.codes.alpha2

    @property
    def alpha3(self) -> str | None:
        """Return the ISO alpha-3 code."""
        return self.codes.alpha3

    @property
    def continent(self) -> str | None:
        """Return the broad continent classification."""
        return self.geography.continent

    @property
    def region(self) -> str | None:
        """Return the UN region classification."""
        return self.geography.region

    @property
    def subregion(self) -> str | None:
        """Return the UN subregion classification."""
        return self.geography.subregion

    @property
    def area_km2(self) -> float | None:
        """Return sourced total area in square kilometres, when available."""
        return self.geography.area.total_km2

    @property
    def capital(self) -> Capital | None:
        """Return the primary capital, or ``None`` when unavailable."""
        return next((capital for capital in self.capitals if capital.primary), None)

    def to_dict(self, include_history: bool = False) -> dict[str, Any]:
        """Serialize this profile to JSON-compatible primitives."""
        del include_history
        return _jsonable(self)

    def to_json(self, indent: int | None = None, include_history: bool = False) -> str:
        """Serialize this profile as JSON."""
        return json.dumps(self.to_dict(include_history), ensure_ascii=False, indent=indent)

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"Country(name={self.name!r}, alpha2={self.alpha2!r})"


@dataclass(frozen=True, slots=True)
class CountryMatch:
    """A ranked country-search result."""

    country: Country
    matched_name: str
    score: int

