"""PyWorldAtlas public API."""

from ._version import SCHEMA_VERSION, __version__
from .atlas import Atlas
from .exceptions import (AmbiguousCountryError, AmbiguousPlaceError, AtlasClosedError,
                         AtlasError, CapitalNotFoundError, CountryNotFoundError,
                         DatasetError, DatasetIntegrityError, DatasetNotFoundError,
                         DatasetVersionError, PlaceNotFoundError)
from .models import (Area, Capital, City, Coordinate, Country, CountryCodes,
                     CountryMatch, CountryStatus, DatasetInfo, Geography,
                     LocalizedName, SourceReference)

__all__ = [
    "Atlas", "Country", "CountryCodes", "CountryStatus", "LocalizedName",
    "Coordinate", "Area", "Geography", "Capital", "City", "CountryMatch",
    "DatasetInfo", "SourceReference", "AtlasError", "AtlasClosedError",
    "DatasetError", "DatasetNotFoundError", "DatasetVersionError",
    "DatasetIntegrityError", "CountryNotFoundError", "AmbiguousCountryError",
    "PlaceNotFoundError", "AmbiguousPlaceError", "CapitalNotFoundError",
    "SCHEMA_VERSION", "__version__",
]

