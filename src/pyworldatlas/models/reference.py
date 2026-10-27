"""Identity, naming, source, and practical reference models."""

from __future__ import annotations

from dataclasses import dataclass


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
class SourceReference:
    """A source used for fields in a country profile."""

    id: str
    name: str
    homepage: str
    retrieved_at: str
    version: str | None = None
    license_name: str | None = None
    license_url: str | None = None
    notes: str | None = None


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
class Currency:
    """A country's currency as identified by the captured source snapshot."""

    code: str
    name: str | None = None
    symbol: str | None = None
    minor_unit_digits: int | None = None
    source: SourceReference | None = None


@dataclass(frozen=True, slots=True)
class Language:
    """A language associated with a country in the captured sources."""

    code: str
    primary_code: str | None = None
    name: str | None = None
    script_code: str | None = None
    source: SourceReference | None = None


@dataclass(frozen=True, slots=True)
class Timezone:
    """A country timezone and its captured January, July, and raw offsets."""

    id: str
    january_utc_offset_hours: float
    july_utc_offset_hours: float
    raw_utc_offset_hours: float
    source: SourceReference | None = None


@dataclass(frozen=True, slots=True)
class PostalCodeFormat:
    """A source-provided postal-code display format and validation expression."""

    format: str
    regex: str | None = None
    source: SourceReference | None = None


@dataclass(frozen=True, slots=True)
class NationalAnthem:
    """A national-anthem title without lyrics, audio, or contributor data."""

    title: str
    english_title: str | None
    source: SourceReference
    source_locator: str


@dataclass(frozen=True, slots=True)
class NationalMotto:
    """A reviewed source-listed national motto and selected language label.

    The record does not infer a legal status. ``english_text`` is the captured
    English label when the source supplies one; it may preserve the original
    phrase instead of translating it.
    """

    text: str
    language_code: str
    english_text: str | None
    source: SourceReference
    source_locator: str


@dataclass(frozen=True, slots=True)
class Demonym:
    """Source-preserved noun and adjective forms for a country or area."""

    noun: str | None
    adjective: str | None
    language_code: str
    source: SourceReference
    source_locator: str
