"""Primary offline atlas interface."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Iterator

from ._normalization import normalize_name
from ._version import SCHEMA_VERSION, __version__
from .database import Database
from .exceptions import AtlasClosedError, CountryNotFoundError, DatasetVersionError
from .models import (Area, Capital, City, Coordinate, Country, CountryCodes,
                     CountryMatch, CountryStatus, DatasetInfo, Geography,
                     LocalizedName, SourceReference)


def _flag(alpha2: str) -> str:
    return "".join(chr(0x1F1E6 + ord(letter) - ord("A")) for letter in alpha2)


class Atlas:
    """Explore the bundled atlas without network access or runtime dependencies."""

    def __init__(self, database_path: str | Path | None = None) -> None:
        self._db = Database(database_path)
        self._closed = False
        found = int(self._meta("schema_version"))
        if found != SCHEMA_VERSION:
            self.close()
            raise DatasetVersionError(f"Dataset schema {found} is incompatible with runtime schema {SCHEMA_VERSION}")

    def _ensure_open(self) -> None:
        if self._closed:
            raise AtlasClosedError("This Atlas has been closed")

    def _meta(self, key: str) -> str:
        row = self._db.connection.execute("SELECT value FROM schema_meta WHERE key = ?", (key,)).fetchone()
        return str(row[0]) if row else ""

    def dataset_info(self) -> DatasetInfo:
        """Return independent library, schema, and dataset versions."""
        self._ensure_open()
        return DatasetInfo(__version__, SCHEMA_VERSION, self._meta("dataset_version"), len(self), self._meta("built_at"))

    def _country_id(self, query: str) -> int | None:
        self._ensure_open()
        normalized = normalize_name(query)
        row = self._db.connection.execute(
            """SELECT id FROM country WHERE upper(alpha2)=upper(?) OR upper(alpha3)=upper(?)
               OR numeric_code=? OR id IN (SELECT country_id FROM country_name WHERE normalized_name=?)
               ORDER BY id LIMIT 2""", (query, query, query, normalized)).fetchall()
        return int(row[0][0]) if len(row) == 1 else None

    def country(self, query: str) -> Country:
        """Resolve a country by common name, alias, alpha-2, alpha-3, or M49 code."""
        self._ensure_open()
        country_id = self._country_id(query)
        if country_id is None:
            suggestions = ", ".join(match.country.name for match in self.search_countries(query, limit=3))
            hint = f" Try: {suggestions}." if suggestions else ""
            raise CountryNotFoundError(f"No unambiguous country matches {query!r}.{hint}")
        return self._load_country(country_id)

    def get(self, query: str, default: Country | None = None) -> Country | None:
        """Safely resolve a country, returning ``default`` when it is absent."""
        try:
            return self.country(query)
        except CountryNotFoundError:
            return default

    def search_countries(self, query: str, *, limit: int = 20) -> tuple[CountryMatch, ...]:
        """Return deterministic ranked partial-name matches."""
        self._ensure_open()
        normalized = normalize_name(query)
        rows = self._db.connection.execute(
            """SELECT country_id, name, normalized_name FROM country_name
               WHERE normalized_name LIKE ? ORDER BY normalized_name, country_id""", (f"%{normalized}%",)).fetchall()
        best: dict[int, tuple[int, str]] = {}
        for row in rows:
            score = 100 if row["normalized_name"] == normalized else 80 if row["normalized_name"].startswith(normalized) else 50
            old = best.get(row["country_id"])
            if old is None or score > old[0]:
                best[row["country_id"]] = (score, row["name"])
        ranked = sorted(best.items(), key=lambda item: (-item[1][0], self._load_country(item[0]).name))[:limit]
        return tuple(CountryMatch(self._load_country(cid), matched, score) for cid, (score, matched) in ranked)

    def countries(self, *, continent: str | None = None, region: str | None = None) -> tuple[Country, ...]:
        """Return countries alphabetically, optionally filtered by UN classifications."""
        self._ensure_open()
        clauses, params = [], []
        if continent:
            clauses.append("continent = ?")
            params.append(continent)
        if region:
            clauses.append("(region = ? OR subregion = ?)")
            params.extend((region, region))
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        rows = self._db.connection.execute(f"SELECT id FROM country{where} ORDER BY name", params).fetchall()
        return tuple(self._load_country(int(row[0])) for row in rows)

    def major_cities(self, country: str, *, limit: int | None = None) -> tuple[City, ...]:
        """Return major cities for a country, ordered by population and name."""
        result = self.country(country).major_cities
        return result if limit is None else result[:limit]

    @lru_cache(maxsize=64)
    def _load_country(self, country_id: int) -> Country:
        row = self._db.connection.execute("SELECT * FROM country WHERE id=?", (country_id,)).fetchone()
        names_rows = self._db.connection.execute("SELECT * FROM country_name WHERE country_id=? ORDER BY preferred DESC, kind, name", (country_id,)).fetchall()
        names = tuple(LocalizedName(n["name"], n["language_code"], n["kind"], bool(n["preferred"])) for n in names_rows)
        aliases = tuple(n.text for n in names if n.kind == "alias")
        capital_rows = self._db.connection.execute("SELECT * FROM capital WHERE country_id=? ORDER BY is_primary DESC, name", (country_id,)).fetchall()
        capitals = tuple(Capital(c["name"], row["alpha2"], Coordinate(c["latitude"], c["longitude"]), c["role"], bool(c["is_primary"]), None, c["population"], c["elevation_m"], c["timezone_id"], (), c["geonames_id"]) for c in capital_rows)
        city_rows = self._db.connection.execute("SELECT * FROM city WHERE country_id=? ORDER BY population DESC, name", (country_id,)).fetchall()
        cities = tuple(City(c["name"], row["alpha2"], Coordinate(c["latitude"], c["longitude"]), c["population"], c["elevation_m"], c["timezone_id"], ("official",) if c["is_capital"] else (), (), c["geonames_id"]) for c in city_rows)
        source_rows = self._db.connection.execute("SELECT DISTINCT s.* FROM source s JOIN field_source f ON f.source_id=s.id WHERE f.country_id=? ORDER BY s.id", (country_id,)).fetchall()
        sources = tuple(SourceReference(s["id"], s["name"], s["homepage"], s["retrieved_at"]) for s in source_rows)
        geography = Geography(row["continent"], row["region"], row["subregion"], Area(row["total_area_km2"]))
        return Country(row["name"], row["official_name"], names, aliases, CountryCodes(row["alpha2"], row["alpha3"], row["numeric_code"], None, row["geonames_id"]), _flag(row["alpha2"]), CountryStatus(row["status"]), geography, capitals, cities, sources)

    def __getitem__(self, query: str) -> Country:
        return self.country(query)

    def __contains__(self, query: object) -> bool:
        return isinstance(query, str) and self._country_id(query) is not None

    def __len__(self) -> int:
        self._ensure_open()
        return int(self._db.connection.execute("SELECT count(*) FROM country").fetchone()[0])

    def __iter__(self) -> Iterator[Country]:
        return iter(self.countries())

    def close(self) -> None:
        """Close the atlas connection."""
        if not self._closed:
            self._db.close()
            self._closed = True
            self._load_country.cache_clear()

    def __enter__(self) -> "Atlas":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
