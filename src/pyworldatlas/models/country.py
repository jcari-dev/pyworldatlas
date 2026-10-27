"""The complete immutable country profile."""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any

from ._serialize import _jsonable
from .reference import CountryCodes, Currency, Demonym, Language, LocalizedName, NationalAnthem, NationalMotto, PostalCodeFormat, SourceReference, Timezone
from .geography import ClimateProfile, Coordinate, ElevationPoint, Geography, Lake, PhysicalGeography, River
from .places import Capital, City
from .results import CountryReference
from .learning import CountryDiscoveryCard


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
    anthems: tuple[NationalAnthem, ...] = ()
    mottos: tuple[NationalMotto, ...] = ()
    demonyms: tuple[Demonym, ...] = ()
    timezones: tuple[Timezone, ...] = ()
    postal_code: PostalCodeFormat | None = None

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
    def land_area_km2(self) -> float | None:
        """Return sourced land area in square kilometres, when available."""
        return self.geography.area.land_km2

    @property
    def water_area_km2(self) -> float | None:
        """Return sourced inland-water area in square kilometres, when available."""
        return self.geography.area.water_km2

    @property
    def water_percent(self) -> float | None:
        """Return the derived percentage of total area recorded as water."""
        return self.geography.area.water_percent

    @property
    def physical(self) -> PhysicalGeography:
        """Return structured physical-geography facts for this profile."""
        return self.geography.physical

    @property
    def coastline_km(self) -> float | None:
        """Return sourced coastline length in kilometres, when available."""
        return self.physical.coastline_km

    @property
    def mean_elevation_m(self) -> float | None:
        """Return sourced mean elevation above sea level, when available."""
        return self.physical.mean_elevation_m

    @property
    def highest_point(self) -> ElevationPoint | None:
        """Return the sourced named highest point, when available."""
        return self.physical.highest_point

    @property
    def lowest_point(self) -> ElevationPoint | None:
        """Return the sourced named lowest point, when available."""
        return self.physical.lowest_point

    @property
    def rivers(self) -> tuple[River, ...]:
        """Return source-listed major rivers; this is not an exhaustive inventory."""
        return self.physical.rivers

    @property
    def lakes(self) -> tuple[Lake, ...]:
        """Return source-listed major lakes; this is not an exhaustive inventory."""
        return self.physical.lakes

    @property
    def climate(self) -> ClimateProfile:
        """Return the climate summary and represented Köppen-Geiger classes."""
        return self.physical.climate

    @property
    def is_coastal(self) -> bool | None:
        """Return whether the source reports a positive coastline, or ``None``."""
        return self.physical.is_coastal

    @property
    def is_landlocked(self) -> bool | None:
        """Return whether the source reports zero coastline, or ``None``."""
        return self.physical.is_landlocked

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
    def anthem(self) -> NationalAnthem | None:
        """Return the first sourced anthem-title record, when available."""
        return self.anthems[0] if self.anthems else None

    @property
    def motto(self) -> NationalMotto | None:
        """Return the first reviewed source-listed motto, when available."""
        return self.mottos[0] if self.mottos else None

    @property
    def demonym(self) -> Demonym | None:
        """Return the English demonym record, when available."""
        return next(
            (record for record in self.demonyms if record.language_code == "en"),
            self.demonyms[0] if self.demonyms else None,
        )

    @property
    def timezone_ids(self) -> tuple[str, ...]:
        """Return all captured country timezone identifiers."""
        return tuple(timezone.id for timezone in self.timezones)

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
            anthem_title=self.anthem.title if self.anthem else None,
            motto_text=self.motto.text if self.motto else None,
            demonym=self.demonym.noun if self.demonym else None,
            timezone_ids=self.timezone_ids,
            coastline_km=self.coastline_km,
            highest_point=self.highest_point,
            climate_zone_codes=self.climate.zone_codes,
        )

    def summary(self, *, local_language: str | None = None) -> str:
        """Return a readable, multiline introduction to this country profile.

        The summary favors useful classroom facts and omits unavailable values.
        Pass a language code to request a particular bundled local name; with
        no code, the selected non-English local identity is used when present.
        This is a presentation helper rather than a serialization format; use
        :meth:`to_dict` when field names and machine-readable values matter.
        """
        local_name = (
            self.local_name(local_language)
            if local_language is not None
            else next(
                (
                    name
                    for name in self.local_names
                    if name.short_name.casefold() != self.name.casefold()
                ),
                None,
            )
        )
        heading = f"{self.flag_emoji or ''} {self.name}".strip()
        if local_name is not None and local_name.short_name.casefold() != self.name.casefold():
            heading += f" · {local_name.short_name}"
        lines = [heading]

        if self.has_distinct_formal_name:
            lines.append(f"Formal name: {self.formal_name}")
        if self.capital is not None:
            lines.append(f"Capital: {self.capital.name}")
        location = tuple(
            value for value in (self.continent, self.subregion) if value
        )
        if location:
            lines.append(f"Location: {' · '.join(dict.fromkeys(location))}")
        if self.population is not None:
            lines.append(f"Population snapshot: {self.population:,}")
        if self.currency is not None:
            currency = self.currency.name or self.currency.code
            details = [self.currency.code]
            if self.currency.symbol and self.currency.symbol != self.currency.code:
                details.append(self.currency.symbol)
            lines.append(f"Currency: {currency} ({', '.join(details)})")
        if self.languages:
            languages = ", ".join(
                f"{language.name} ({language.code})"
                if language.name and language.name != language.code
                else language.code
                for language in self.languages
            )
            lines.append(f"Languages: {languages}")
        if self.anthem is not None:
            anthem = self.anthem.title
            if self.anthem.english_title and self.anthem.english_title != anthem:
                anthem += f" · {self.anthem.english_title}"
            lines.append(f"Anthem title: {anthem}")
        if self.motto is not None:
            motto = self.motto.text
            if self.motto.english_text and self.motto.english_text != motto:
                motto += f" · {self.motto.english_text}"
            lines.append(f"Motto: {motto}")
        if self.highest_point is not None:
            lines.append(
                f"Highest point: {self.highest_point.name} "
                f"({self.highest_point.elevation_m:,.0f} m)"
            )
        if self.climate.dominant_zone is not None:
            zone = self.climate.dominant_zone
            lines.append(f"Dominant climate class: {zone.code} · {zone.name}")
        if self.rivers:
            lines.append(
                "Source-listed rivers: "
                + ", ".join(river.name for river in self.rivers[:3])
            )
        if self.lakes:
            lines.append(
                "Source-listed lakes: "
                + ", ".join(lake.name for lake in self.lakes[:3])
            )
        return "\n".join(lines)

    def to_dict(self, include_history: bool = False) -> dict[str, Any]:
        """Serialize this profile to JSON-compatible primitives.

        ``include_history`` is reserved for compatibility and currently has no
        effect because the bundled dataset has no historical series.
        """
        del include_history
        data: dict[str, Any] = _jsonable(self)
        return data

    def to_json(self, indent: int | None = None, include_history: bool = False) -> str:
        """Serialize this profile as JSON.

        ``include_history`` is reserved for compatibility and currently has no
        effect because the bundled dataset has no historical series.
        """
        return json.dumps(self.to_dict(include_history), ensure_ascii=False, indent=indent)

    def _repr_html_(self) -> str:
        """Show the profile as a fact card in Jupyter and other notebook tools.

        The card is the :meth:`summary` as an accessible table. It sets no colors,
        so it follows the notebook's light or dark theme.
        """
        from html import escape

        heading, *lines = self.summary().splitlines()
        rows = "".join(
            '<tr><th scope="row" style="text-align:left;padding:2px 14px 2px 0;'
            f'font-weight:600;vertical-align:top">{escape(label)}</th>'
            f'<td style="text-align:left;padding:2px 0">{escape(value)}</td></tr>'
            for label, _, value in (line.partition(": ") for line in lines)
        )
        return (
            '<div class="pyworldatlas-country" style="font-family:system-ui,sans-serif;'
            'line-height:1.45;max-width:46em">'
            f'<p style="font-size:1.25em;font-weight:650;margin:0 0 6px">{escape(heading)}</p>'
            f'<table style="border-collapse:collapse;margin:0">'
            f"<caption style=\"text-align:left;opacity:0.75;padding-bottom:4px\">"
            f"Country profile for {escape(self.name)} ({escape(self.alpha2)})</caption>"
            f"{rows}</table></div>"
        )

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"Country(name={self.name!r}, alpha2={self.alpha2!r})"
