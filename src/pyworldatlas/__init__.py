"""PyWorldAtlas: an offline world atlas for Python, with no dependencies.

Everything starts with :class:`Atlas`::

    from pyworldatlas import Atlas

    atlas = Atlas()
    atlas["Japan"].capital.name       # 'Tokyo'
    atlas.distance_between("Paris", "Tokyo")
    atlas.help()                      # a dozen more things to try

Every result is an immutable model that prints as one readable line. Call
:func:`show_details` to print every field instead. Optional data packs add
maps, landmarks, places, and statistics; see :mod:`pyworldatlas.packs`.
"""

from ._version import SCHEMA_VERSION, __version__
from .atlas import Atlas
from .exceptions import (AmbiguousCountryError, AmbiguousPlaceError, AtlasClosedError,
                         AtlasError, CapitalNotFoundError, CountryNotFoundError,
                         DatasetError, DatasetIntegrityError, DatasetNotFoundError,
                         DatasetVersionError, MapSupportNotInstalledError,
                         PackNotInstalledError, PlaceNotFoundError)
from .models import (Airport, Antipode, Area, Distance, Indicator, StatisticSeries, StatisticValue, BorderPathResult, Capital, CapitalDistance, City,
                     CityDistance, ClimateProfile, ClimateZone, Coordinate, Country,
                     CountryCodes, CountryDiscoveryCard, CountryMatch,
                     CountryRanking, CountryReference, Currency, DatasetInfo,
                     Demonym, ElevationPoint, Flashcard, Geography, Lake,
                     Language, LocalizedName, NationalAnthem, NationalMotto,
                     PhysicalGeography, Place, PlaceDistance, PlaceQuestion, PostalCodeFormat, QuizQuestion, River,
                     SiteDistance, SourceReference, SunTimes, Timezone, TravelBasics,
                     WorldHeritageSite)

from .models._display import show_details
from ._console import ensure_printable as _ensure_printable

_ensure_printable()

__all__ = [
    "show_details",
    "Atlas", "Country", "CountryCodes", "CountryReference", "CountryDiscoveryCard",
    "BorderPathResult", "CountryRanking", "CapitalDistance", "CityDistance",
    "LocalizedName", "Flashcard", "QuizQuestion", "PlaceQuestion",
    "Coordinate", "Antipode", "Area", "Geography", "Capital", "City", "Place", "PlaceDistance",
    "Airport", "WorldHeritageSite", "SiteDistance", "Currency", "Language", "CountryMatch",
    "PhysicalGeography", "ElevationPoint", "River", "Lake", "ClimateProfile", "ClimateZone",
    "NationalAnthem", "NationalMotto", "Demonym", "Timezone", "PostalCodeFormat", "TravelBasics",
    "DatasetInfo", "Distance", "SourceReference", "SunTimes", "Indicator", "StatisticSeries", "StatisticValue", "AtlasError", "AtlasClosedError",
    "DatasetError", "DatasetNotFoundError", "DatasetVersionError",
    "DatasetIntegrityError", "CountryNotFoundError", "AmbiguousCountryError",
    "PlaceNotFoundError", "AmbiguousPlaceError", "CapitalNotFoundError",
    "MapSupportNotInstalledError", "PackNotInstalledError",
    "SCHEMA_VERSION", "__version__",
]


def __getattr__(name: str) -> object:
    """Load the ``packs`` and ``maps`` submodules on first use."""
    if name in {"maps", "packs"}:
        from importlib import import_module

        return import_module(f".{name}", __name__)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
