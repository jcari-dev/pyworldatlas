"""Read-only access to the bundled SQLite database.

The database ships inside the package, so the atlas works offline. It is
opened read-only with ``mode=ro`` so nothing can change it by accident. The
atlas then checks the schema version, so the code and the data always match.
"""

from __future__ import annotations

from pathlib import Path
import sqlite3

from .exceptions import DatasetNotFoundError


def _bundled_path() -> Path:
    """Locate the bundled dataset, importing ``importlib.resources`` only if needed."""
    bundled = Path(__file__).resolve().parent / "data" / "atlas.sqlite3"
    if bundled.is_file():
        return bundled
    from importlib.resources import files

    return Path(str(files("pyworldatlas.data").joinpath("atlas.sqlite3")))


class Database:
    """A small read-only SQLite connection wrapper."""

    def __init__(self, path: str | Path | None = None) -> None:
        selected = Path(path) if path else _bundled_path()
        if not selected.is_file():
            raise DatasetNotFoundError(f"Atlas dataset not found: {selected}")
        uri = f"file:{selected.resolve().as_posix()}?mode=ro&immutable=1"
        self.connection = sqlite3.connect(uri, uri=True)
        self.connection.row_factory = sqlite3.Row

    def close(self) -> None:
        """Close the database connection."""
        self.connection.close()

