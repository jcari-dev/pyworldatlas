"""Immutable public data models returned by :class:`pyworldatlas.Atlas`.

The models live in small topic modules; every public model is importable from
``pyworldatlas.models`` and from the top-level ``pyworldatlas`` package.
"""

from __future__ import annotations

from .reference import CountryCodes, Currency, DatasetInfo, Demonym, Language, LocalizedName, NationalAnthem, NationalMotto, PostalCodeFormat, SourceReference, Timezone, TravelBasics
from .geography import Area, ClimateProfile, ClimateZone, Coordinate, ElevationPoint, Geography, Lake, PhysicalGeography, River
from .places import Capital, City, Place
from .results import BorderPathResult, CapitalDistance, CityDistance, CountryMatch, CountryRanking, CountryReference, PlaceDistance, SunTimes
from .learning import CountryDiscoveryCard, Flashcard, QuizQuestion
from .country import Country

__all__ = [
    "Area",
    "BorderPathResult",
    "Capital",
    "CapitalDistance",
    "City",
    "CityDistance",
    "ClimateProfile",
    "ClimateZone",
    "Coordinate",
    "Country",
    "CountryCodes",
    "CountryDiscoveryCard",
    "CountryMatch",
    "CountryRanking",
    "CountryReference",
    "Currency",
    "DatasetInfo",
    "Demonym",
    "ElevationPoint",
    "Flashcard",
    "Geography",
    "Lake",
    "Language",
    "LocalizedName",
    "NationalAnthem",
    "NationalMotto",
    "PhysicalGeography",
    "Place",
    "PlaceDistance",
    "PostalCodeFormat",
    "QuizQuestion",
    "River",
    "SourceReference",
    "SunTimes",
    "Timezone",
    "TravelBasics",
]
