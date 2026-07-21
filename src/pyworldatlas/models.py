"""Immutable public data models returned by :class:`pyworldatlas.Atlas`."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from enum import Enum
import json
from math import asin, atan2, cos, degrees, radians, sin, sqrt
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
    """A sourced country name, alias, or official local-language form."""

    text: str
    language_code: str | None
    kind: str
    preferred: bool
    language_name: str | None = None
    script_code: str | None = None
    official_name: str | None = None
    romanized_short_name: str | None = None
    romanized_official_name: str | None = None
    is_official_language: bool = False
    source: SourceReference | None = None

    @property
    def short_name(self) -> str:
        """Return the short local-language form."""
        return self.text


@dataclass(frozen=True, slots=True)
class Coordinate:
    """A signed WGS84 coordinate in decimal degrees."""

    latitude: float
    longitude: float

    def __post_init__(self) -> None:
        if not -90 <= self.latitude <= 90:
            raise ValueError("latitude must be between -90 and 90")
        if not -180 <= self.longitude <= 180:
            raise ValueError("longitude must be between -180 and 180")

    def as_tuple(self) -> tuple[float, float]:
        """Return ``(latitude, longitude)``."""
        return (self.latitude, self.longitude)

    def distance_to(self, other: Coordinate, *, unit: str = "km") -> float:
        """Return the great-circle distance to ``other`` using WGS84 mean radius."""
        lat1, lon1, lat2, lon2 = map(radians, (self.latitude, self.longitude, other.latitude, other.longitude))
        delta_lat, delta_lon = lat2 - lat1, lon2 - lon1
        haversine = sin(delta_lat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(delta_lon / 2) ** 2
        kilometers = 2 * 6371.0088 * asin(min(1.0, sqrt(haversine)))
        factors = {"km": 1.0, "mi": 0.621371192237334, "nmi": 0.539956803455724}
        if unit not in factors:
            raise ValueError("unit must be 'km', 'mi', or 'nmi'")
        return kilometers * factors[unit]

    def bearing_to(self, other: Coordinate) -> float:
        """Return the initial bearing to ``other`` in degrees from true north."""
        lat1, lat2 = radians(self.latitude), radians(other.latitude)
        delta_lon = radians(other.longitude - self.longitude)
        y = sin(delta_lon) * cos(lat2)
        x = cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(delta_lon)
        return (degrees(atan2(y, x)) + 360.0) % 360.0

    def midpoint_to(self, other: Coordinate) -> Coordinate:
        """Return the spherical midpoint on the great-circle route to ``other``."""
        lat1, lon1, lat2 = map(radians, (self.latitude, self.longitude, other.latitude))
        delta_lon = radians(other.longitude - self.longitude)
        bx, by = cos(lat2) * cos(delta_lon), cos(lat2) * sin(delta_lon)
        latitude = atan2(sin(lat1) + sin(lat2), sqrt((cos(lat1) + bx) ** 2 + by**2))
        longitude = lon1 + atan2(by, cos(lat1) + bx)
        normalized_longitude = (degrees(longitude) + 540.0) % 360.0 - 180.0
        return Coordinate(degrees(latitude), normalized_longitude)


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


@dataclass(frozen=True, slots=True)
class Currency:
    """A country's currency as identified by the captured source snapshot."""

    code: str
    name: str | None = None


@dataclass(frozen=True, slots=True)
class Language:
    """A language code associated with a country in the captured source."""

    code: str


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
    local_names: tuple[LocalizedName, ...] = ()
    population: int | None = None
    currency: Currency | None = None
    languages: tuple[Language, ...] = ()
    calling_codes: tuple[str, ...] = ()
    top_level_domain: str | None = None
    observed_timezones: tuple[str, ...] = ()

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

    @property
    def capital_coordinates(self) -> Coordinate | None:
        """Return the primary capital's coordinates, when a capital is available."""
        return self.capital.coordinates if self.capital else None

    def name_in(self, language_code: str) -> str | None:
        """Return the short local name for ``language_code``, without fallback."""
        match = next((name for name in self.local_names if name.language_code == language_code.casefold()), None)
        return match.short_name if match else None

    def official_name_in(self, language_code: str) -> str | None:
        """Return the formal local name for ``language_code``, without fallback."""
        match = next((name for name in self.local_names if name.language_code == language_code.casefold()), None)
        return match.official_name if match else None

    def romanized_name_in(self, language_code: str) -> str | None:
        """Return a source-provided romanized short name, without generating one."""
        match = next((name for name in self.local_names if name.language_code == language_code.casefold()), None)
        return match.romanized_short_name if match else None

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
