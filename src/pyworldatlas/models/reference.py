"""Identity, naming, source, and practical reference models."""

from __future__ import annotations

from dataclasses import dataclass

from ._display import friendly_repr


@dataclass(frozen=True, slots=True)
class DatasetInfo:
    """Independent library, schema, and dataset version metadata."""

    library_version: str
    schema_version: int
    dataset_version: str
    country_count: int
    built_at: str

    def __str__(self) -> str:
        return f"PyWorldAtlas {self.library_version}, dataset {self.dataset_version}, {self.country_count} countries"

    def __repr__(self) -> str:
        return friendly_repr(self, f"{str(self)!r}")


@dataclass(frozen=True, slots=True)
class CountryCodes:
    """Standard identifiers for a country or area."""

    alpha2: str
    alpha3: str | None
    numeric: str | None
    geonames: int | None = None

    def __repr__(self) -> str:
        return friendly_repr(self, f"alpha2={self.alpha2!r}, alpha3={self.alpha3!r}, numeric={self.numeric!r}")


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

    def __str__(self) -> str:
        return f"{self.name} ({self.license_name})" if self.license_name else self.name

    def __repr__(self) -> str:
        return friendly_repr(self, f"{self.id!r}")


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

    def __str__(self) -> str:
        return self.text

    def __repr__(self) -> str:
        return friendly_repr(self, f"{self.text!r}, language_code={self.language_code!r}, kind={self.kind!r}")

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

    def __str__(self) -> str:
        details = ", ".join(part for part in (self.code, self.symbol) if part and part != self.name)
        return f"{self.name} ({details})" if self.name else self.code

    def __repr__(self) -> str:
        return friendly_repr(self, f"{str(self)!r}")


@dataclass(frozen=True, slots=True)
class Language:
    """A language associated with a country in the captured sources."""

    code: str
    primary_code: str | None = None
    name: str | None = None
    script_code: str | None = None
    source: SourceReference | None = None

    def __str__(self) -> str:
        return f"{self.name} ({self.code})" if self.name else self.code

    def __repr__(self) -> str:
        return friendly_repr(self, f"{str(self)!r}")


@dataclass(frozen=True, slots=True)
class Timezone:
    """A country timezone and its captured January, July, and raw offsets."""

    id: str
    january_utc_offset_hours: float
    july_utc_offset_hours: float
    raw_utc_offset_hours: float
    source: SourceReference | None = None

    def __str__(self) -> str:
        offset = self.raw_utc_offset_hours
        sign = "+" if offset >= 0 else "-"
        hours, minutes = divmod(round(abs(offset) * 60), 60)
        return f"{self.id}, UTC{sign}{hours}" + (f":{minutes:02d}" if minutes else "")

    def __repr__(self) -> str:
        return friendly_repr(self, f"{str(self)!r}")


@dataclass(frozen=True, slots=True)
class PostalCodeFormat:
    """A source-provided postal-code display format and validation expression."""

    format: str
    regex: str | None = None
    source: SourceReference | None = None

    def __str__(self) -> str:
        return self.format

    def __repr__(self) -> str:
        return friendly_repr(self, f"{self.format!r}")


@dataclass(frozen=True, slots=True)
class TravelBasics:
    """Everyday facts a visitor needs: plugs, mains electricity, and driving side.

    ``plug_types`` are IEC World Plugs letters such as ``"A"`` or ``"G"``.
    ``voltages_v`` and ``frequencies_hz`` list the household mains supply; a
    country can use more than one. ``driving_side`` is ``"left"`` or ``"right"``,
    or ``None`` when the source does not agree on one side.
    """

    plug_types: tuple[str, ...]
    voltages_v: tuple[int, ...]
    frequencies_hz: tuple[int, ...]
    driving_side: str | None
    source: SourceReference | None = None

    def __str__(self) -> str:
        return self.summary

    def __repr__(self) -> str:
        return friendly_repr(self, f"{self.summary!r}")

    @property
    def summary(self) -> str:
        """Return one readable line, such as ``"Plugs A, B · 100 V, 50/60 Hz · drives on the left"``."""
        parts = []
        if self.plug_types:
            parts.append(f"Plug{'s' if len(self.plug_types) > 1 else ''} {', '.join(self.plug_types)}")
        if self.voltages_v:
            supply = "/".join(str(volts) for volts in self.voltages_v) + " V"
            if self.frequencies_hz:
                supply += ", " + "/".join(str(hertz) for hertz in self.frequencies_hz) + " Hz"
            parts.append(supply)
        if self.driving_side:
            parts.append(f"drives on the {self.driving_side}")
        return " · ".join(parts)


@dataclass(frozen=True, slots=True)
class NationalAnthem:
    """A national-anthem title without lyrics, audio, or contributor data."""

    title: str
    english_title: str | None
    source: SourceReference
    source_locator: str

    def __str__(self) -> str:
        return f"{self.title} ({self.english_title})" if self.english_title and self.english_title != self.title else self.title

    def __repr__(self) -> str:
        return friendly_repr(self, f"{self.title!r}")


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

    def __str__(self) -> str:
        return f"{self.text} ({self.english_text})" if self.english_text and self.english_text != self.text else self.text

    def __repr__(self) -> str:
        return friendly_repr(self, f"{self.text!r}")


@dataclass(frozen=True, slots=True)
class Demonym:
    """Source-preserved noun and adjective forms for a country or area."""

    noun: str | None
    adjective: str | None
    language_code: str
    source: SourceReference
    source_locator: str

    def __str__(self) -> str:
        return self.noun or self.adjective or ""

    def __repr__(self) -> str:
        return friendly_repr(self, f"noun={self.noun!r}, adjective={self.adjective!r}")
