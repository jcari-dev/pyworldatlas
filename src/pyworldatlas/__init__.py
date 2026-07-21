"""PyWorldAtlas public API."""

from ._version import SCHEMA_VERSION, __version__
from .atlas import Atlas
from .exceptions import (AmbiguousCountryError, AmbiguousPlaceError, AtlasClosedError,
                         AtlasError, CapitalNotFoundError, CountryNotFoundError,
                         DatasetError, DatasetIntegrityError, DatasetNotFoundError,
                         DatasetVersionError, PlaceNotFoundError)
from .models import (Area, BorderPathResult, Capital, City, Coordinate, Country,
                     CountryCodes, CountryDiscoveryCard, CountryMatch, CountryReference,
                     CountryStatus, Currency, DatasetInfo, Flashcard, Geography,
                     Language, LocalizedName, SourceReference)

__all__ = [
    "Atlas", "Country", "CountryCodes", "CountryReference", "CountryDiscoveryCard",
    "BorderPathResult",
    "CountryStatus", "LocalizedName", "Flashcard",
    "Coordinate", "Area", "Geography", "Capital", "City", "Currency", "Language", "CountryMatch",
    "DatasetInfo", "SourceReference", "AtlasError", "AtlasClosedError",
    "DatasetError", "DatasetNotFoundError", "DatasetVersionError",
    "DatasetIntegrityError", "CountryNotFoundError", "AmbiguousCountryError",
    "PlaceNotFoundError", "AmbiguousPlaceError", "CapitalNotFoundError",
    "SCHEMA_VERSION", "__version__",
]
