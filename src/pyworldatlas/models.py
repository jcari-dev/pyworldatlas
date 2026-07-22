"""Immutable public data models returned by :class:`pyworldatlas.Atlas`."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
import json
from math import asin, atan2, cos, degrees, isclose, radians, sin, sqrt
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
    """A sourced country or area name in a selected local language.

    ``kind`` is ``"national_official"`` for reviewed UNGEGN short/formal
    names and ``"locale_display"`` for Unicode CLDR territory display names.
    ``official_name`` and the romanized fields remain ``None`` unless their
    source explicitly supplies those values. ``language_status`` records why
    the language was selected, such as ``"official"`` or
    ``"de_facto_official"``.
    """

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
    source_locator: str | None = None
    language_status: str | None = None

    @property
    def short_name(self) -> str:
        """Return the short local-language form."""
        return self.text

    @property
    def formal_name(self) -> str | None:
        """Return the formal local-language form supplied by the source."""
        return self.official_name

    @property
    def is_national_official(self) -> bool:
        """Whether UNGEGN supplies a reviewed national official name."""
        return self.kind == "national_official"


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

    def _relative_position(self, other: Coordinate) -> tuple[bool, bool]:
        """Return whether two coordinates are coincident or antipodal."""
        def unit_vector(coordinate: Coordinate) -> tuple[float, float, float]:
            latitude = radians(coordinate.latitude)
            longitude = radians(coordinate.longitude)
            return (
                cos(latitude) * cos(longitude),
                cos(latitude) * sin(longitude),
                sin(latitude),
            )

        first = unit_vector(self)
        second = unit_vector(other)
        coincident = all(
            isclose(left, right, rel_tol=0.0, abs_tol=1e-12)
            for left, right in zip(first, second)
        )
        antipodal = all(
            isclose(left, -right, rel_tol=0.0, abs_tol=1e-12)
            for left, right in zip(first, second)
        )
        return coincident, antipodal

    def bearing_to(self, other: Coordinate) -> float:
        """Return the initial bearing to ``other`` in degrees from true north."""
        coincident, antipodal = self._relative_position(other)
        if coincident:
            raise ValueError("initial bearing is undefined for coincident coordinates")
        if antipodal:
            raise ValueError("initial bearing is undefined for antipodal coordinates")
        lat1, lat2 = radians(self.latitude), radians(other.latitude)
        delta_lon = radians(other.longitude - self.longitude)
        y = sin(delta_lon) * cos(lat2)
        x = cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(delta_lon)
        return (degrees(atan2(y, x)) + 360.0) % 360.0

    def midpoint_to(self, other: Coordinate) -> Coordinate:
        """Return the spherical midpoint on the great-circle path to ``other``."""
        _, antipodal = self._relative_position(other)
        if antipodal:
            raise ValueError("great-circle midpoint is undefined for antipodal coordinates")
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
        return _jsonable(self)

    def to_json(self, indent: int | None = None) -> str:
        """Serialize this path as JSON without escaping Unicode text."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)


@dataclass(frozen=True, slots=True)
class Flashcard:
    """A deterministic geography study prompt and answer.

    Flashcards contain no scoring, session state, or hidden random state. The
    ``topic`` value identifies the documented generator used by
    :meth:`pyworldatlas.Atlas.flashcards`.
    """

    topic: str
    prompt: str
    answer: str
    country: CountryReference

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-compatible primitives for this flashcard."""
        return _jsonable(self)

    def to_json(self, indent: int | None = None) -> str:
        """Serialize this flashcard as JSON without escaping Unicode text."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)


@dataclass(frozen=True, slots=True)
class CountryDiscoveryCard:
    """A compact, serializable teaching view of one materialized country.

    Every value is copied from, or calculated directly from, an existing
    :class:`Country`. Creating a card never queries the database or network.
    """

    country: CountryReference
    flag_emoji: str | None
    official_name: str | None
    formal_name: str | None
    capital: str | None
    capital_coordinates: Coordinate | None
    continent: str | None
    region: str | None
    subregion: str | None
    population: int | None
    area_km2: float | None
    population_density: float | None
    currency: Currency | None
    language_codes: tuple[str, ...]
    calling_codes: tuple[str, ...]
    top_level_domain: str | None
    observed_timezones: tuple[str, ...]
    local_names: tuple[LocalizedName, ...]
    major_city_count: int
    source_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-compatible primitives for this discovery card."""
        return _jsonable(self)

    def to_json(self, indent: int | None = None) -> str:
        """Serialize this discovery card as JSON without escaping Unicode text."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)


@dataclass(frozen=True, slots=True)
class Country:
    """A sourced, immutable country profile from the offline atlas.

    ``official_name`` is the canonical English identity from UN M49.
    ``formal_name`` is the sourced English long or formal form when the
    country or area is covered by the formal-name source layer.
    """

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
    formal_name: str | None = None

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
    def flag_emoji(self) -> str | None:
        """Return the regional-indicator flag derived from the alpha-2 code.

        Emoji appearance depends on the operating system, font, and application.
        ``None`` is returned if a profile ever lacks a valid two-letter code.
        The existing ``flag`` attribute is the same value.
        """
        return self.flag if len(self.alpha2) == 2 and self.alpha2.isalpha() else None

    @property
    def has_distinct_formal_name(self) -> bool:
        """Return whether the sourced English formal form differs from ``name``.

        ``False`` also covers records outside the current formal-name source
        scope. Inspect ``formal_name`` directly when that distinction matters.
        """
        return bool(self.formal_name and self.formal_name.casefold() != self.name.casefold())

    @property
    def population_density(self) -> float | None:
        """Return snapshot population per square kilometre when calculable.

        This is a transparent ratio of ``population`` to ``area_km2``,
        not a separately sourced official statistic. ``None`` represents a
        missing population, missing area, or non-positive area.
        """
        area = self.area_km2
        if self.population is None or area is None or area <= 0:
            return None
        return self.population / area

    @property
    def language_codes(self) -> tuple[str, ...]:
        """Return the captured country language codes as an immutable tuple."""
        return tuple(language.code for language in self.languages)

    @property
    def currency_code(self) -> str | None:
        """Return the captured currency code, or ``None`` when unavailable."""
        return self.currency.code if self.currency else None

    @property
    def major_city_count(self) -> int:
        """Return the number of populated-place records bundled for this profile."""
        return len(self.major_cities)

    @property
    def capital(self) -> Capital | None:
        """Return the primary capital, or ``None`` when unavailable."""
        return next((capital for capital in self.capitals if capital.primary), None)

    @property
    def capital_coordinates(self) -> Coordinate | None:
        """Return the primary capital's coordinates, when a capital is available."""
        return self.capital.coordinates if self.capital else None

    @property
    def local_name_languages(self) -> tuple[str, ...]:
        """Return language codes represented by sourced local identity records."""
        return tuple(name.language_code for name in self.local_names if name.language_code)

    def local_name(self, language_code: str) -> LocalizedName | None:
        """Return the complete sourced local record for ``language_code``.

        Matching is case-insensitive. ``None`` means that this dataset does not
        contain a selected record for that language; it does not mean the
        language or local name does not exist. No translation, English
        fallback, or romanization is invented.
        """
        normalized = language_code.casefold()
        return next((name for name in self.local_names if name.language_code == normalized), None)

    def name_in(self, language_code: str) -> str | None:
        """Return the sourced short local name, without fallback."""
        match = self.local_name(language_code)
        return match.short_name if match else None

    def official_name_in(self, language_code: str) -> str | None:
        """Return the reviewed formal local name, without fallback.

        This is populated only for ``national_official`` local records. It is
        separate from the English ``formal_name`` profile field.
        """
        match = self.local_name(language_code)
        return match.formal_name if match else None

    def romanized_name_in(self, language_code: str) -> str | None:
        """Return a source-provided romanized short name, without generating one."""
        match = self.local_name(language_code)
        return match.romanized_short_name if match else None

    def romanized_official_name_in(self, language_code: str) -> str | None:
        """Return a source-provided romanized formal name, without generating one."""
        match = self.local_name(language_code)
        return match.romanized_official_name if match else None

    def reference(self) -> CountryReference:
        """Return a compact immutable reference suitable for results and prompts."""
        return CountryReference(self.name, self.alpha2, self.alpha3, self.codes.numeric)

    def discovery_card(self) -> CountryDiscoveryCard:
        """Return a compact educational view built entirely from this profile.

        The card is safe to retain after the originating :class:`Atlas` closes
        and can be serialized with :meth:`CountryDiscoveryCard.to_dict` or
        :meth:`CountryDiscoveryCard.to_json`.
        """
        capital = self.capital
        return CountryDiscoveryCard(
            country=self.reference(),
            flag_emoji=self.flag_emoji,
            official_name=self.official_name,
            formal_name=self.formal_name,
            capital=capital.name if capital else None,
            capital_coordinates=capital.coordinates if capital else None,
            continent=self.continent,
            region=self.region,
            subregion=self.subregion,
            population=self.population,
            area_km2=self.area_km2,
            population_density=self.population_density,
            currency=self.currency,
            language_codes=self.language_codes,
            calling_codes=self.calling_codes,
            top_level_domain=self.top_level_domain,
            observed_timezones=self.observed_timezones,
            local_names=self.local_names,
            major_city_count=self.major_city_count,
            source_ids=tuple(source.id for source in self.sources),
        )

    def to_dict(self, include_history: bool = False) -> dict[str, Any]:
        """Serialize this profile to JSON-compatible primitives.

        ``include_history`` is reserved for compatibility and currently has no
        effect because the bundled dataset has no historical series.
        """
        del include_history
        return _jsonable(self)

    def to_json(self, indent: int | None = None, include_history: bool = False) -> str:
        """Serialize this profile as JSON.

        ``include_history`` is reserved for compatibility and currently has no
        effect because the bundled dataset has no historical series.
        """
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
