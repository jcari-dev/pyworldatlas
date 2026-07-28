"""Public exception hierarchy for PyWorldAtlas."""


class AtlasError(Exception):
    """Base class for atlas errors."""


class AtlasClosedError(AtlasError):
    """Raised when a closed atlas is used."""


class DatasetError(AtlasError):
    """Base class for bundled-dataset errors."""


class DatasetNotFoundError(DatasetError):
    """Raised when the bundled SQLite database cannot be found."""


class DatasetVersionError(DatasetError):
    """Raised when runtime and dataset schema versions disagree."""


class DatasetIntegrityError(DatasetError):
    """Raised when the bundled dataset fails an integrity check."""


class CountryNotFoundError(AtlasError, LookupError):
    """Raised when a country query has no match."""


class AmbiguousCountryError(AtlasError, LookupError):
    """Raised when a country query has multiple equally valid matches."""


class PlaceNotFoundError(AtlasError, LookupError):
    """Raised when a place query has no match."""


class AmbiguousPlaceError(AtlasError, LookupError):
    """Raised when a place query is ambiguous."""


class CapitalNotFoundError(PlaceNotFoundError):
    """Raised when a capital query has no match."""


class MapSupportNotInstalledError(AtlasError):
    """Raised when an optional map viewer or map-data pack is unavailable."""
