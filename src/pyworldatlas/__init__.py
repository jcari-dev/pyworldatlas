"""PyWorldAtlas public API."""

from ._version import SCHEMA_VERSION, __version__
from .atlas import Atlas
from .exceptions import (AmbiguousCountryError, AmbiguousPlaceError, AtlasClosedError,
                         AtlasError, CapitalNotFoundError, CountryNotFoundError,
                         DatasetError, DatasetIntegrityError, DatasetNotFoundError,
                         DatasetVersionError, PlaceNotFoundError)
from .models import (Area, BorderPathResult, Capital, CapitalDistance, City,
                     ClimateProfile, ClimateZone, Coordinate, Country,
                     CountryCodes, CountryDiscoveryCard, CountryMatch,
                     CountryRanking, CountryReference, Currency, DatasetInfo,
                     Demonym, ElevationPoint, Flashcard, Geography, Lake,
                     Language, LocalizedName, NationalAnthem, NationalMotto,
                     PhysicalGeography, PostalCodeFormat, River,
                     SourceReference, Timezone)

__all__ = [
    "Atlas", "Country", "CountryCodes", "CountryReference", "CountryDiscoveryCard",
    "BorderPathResult", "CountryRanking", "CapitalDistance",
    "LocalizedName", "Flashcard",
    "Coordinate", "Area", "Geography", "Capital", "City", "Currency", "Language", "CountryMatch",
    "PhysicalGeography", "ElevationPoint", "River", "Lake", "ClimateProfile", "ClimateZone",
    "NationalAnthem", "NationalMotto", "Demonym", "Timezone", "PostalCodeFormat",
    "DatasetInfo", "SourceReference", "AtlasError", "AtlasClosedError",
    "DatasetError", "DatasetNotFoundError", "DatasetVersionError",
    "DatasetIntegrityError", "CountryNotFoundError", "AmbiguousCountryError",
    "PlaceNotFoundError", "AmbiguousPlaceError", "CapitalNotFoundError",
    "SCHEMA_VERSION", "__version__",
]
