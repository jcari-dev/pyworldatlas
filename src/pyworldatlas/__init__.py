"""PyWorldAtlas public API."""

from ._version import SCHEMA_VERSION, __version__
from .atlas import Atlas
from .exceptions import (AmbiguousCountryError, AmbiguousPlaceError, AtlasClosedError,
                         AtlasError, CapitalNotFoundError, CountryNotFoundError,
                         DatasetError, DatasetIntegrityError, DatasetNotFoundError,
                         DatasetVersionError, MapSupportNotInstalledError,
                         PlaceNotFoundError)
from .models import (Antipode, Area, BorderPathResult, Capital, CapitalDistance, City,
                     CityDistance, ClimateProfile, ClimateZone, Coordinate, Country,
                     CountryCodes, CountryDiscoveryCard, CountryMatch,
                     CountryRanking, CountryReference, Currency, DatasetInfo,
                     Demonym, ElevationPoint, Flashcard, Geography, Lake,
                     Language, LocalizedName, NationalAnthem, NationalMotto,
                     PhysicalGeography, Place, PlaceDistance, PlaceQuestion, PostalCodeFormat, QuizQuestion, River,
                     SourceReference, SunTimes, Timezone, TravelBasics)

__all__ = [
    "Atlas", "Country", "CountryCodes", "CountryReference", "CountryDiscoveryCard",
    "BorderPathResult", "CountryRanking", "CapitalDistance", "CityDistance",
    "LocalizedName", "Flashcard", "QuizQuestion", "PlaceQuestion",
    "Coordinate", "Antipode", "Area", "Geography", "Capital", "City", "Place", "PlaceDistance", "Currency", "Language", "CountryMatch",
    "PhysicalGeography", "ElevationPoint", "River", "Lake", "ClimateProfile", "ClimateZone",
    "NationalAnthem", "NationalMotto", "Demonym", "Timezone", "PostalCodeFormat", "TravelBasics",
    "DatasetInfo", "SourceReference", "SunTimes", "AtlasError", "AtlasClosedError",
    "DatasetError", "DatasetNotFoundError", "DatasetVersionError",
    "DatasetIntegrityError", "CountryNotFoundError", "AmbiguousCountryError",
    "PlaceNotFoundError", "AmbiguousPlaceError", "CapitalNotFoundError",
    "MapSupportNotInstalledError",
    "SCHEMA_VERSION", "__version__",
]
