"""Read-only access to the bundled SQLite database."""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path
import sqlite3

from .exceptions import DatasetNotFoundError


class Database:
    """A small read-only SQLite connection wrapper."""

    def __init__(self, path: str | Path | None = None) -> None:
        selected = Path(path) if path else Path(str(files("pyworldatlas.data").joinpath("atlas.sqlite3")))
        if not selected.is_file():
            raise DatasetNotFoundError(f"Atlas dataset not found: {selected}")
        uri = f"file:{selected.resolve().as_posix()}?mode=ro&immutable=1"
        self.connection = sqlite3.connect(uri, uri=True)
        self.connection.row_factory = sqlite3.Row

    def close(self) -> None:
        """Close the database connection."""
        self.connection.close()

