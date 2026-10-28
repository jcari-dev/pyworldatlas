"""Primary offline atlas interface."""

from __future__ import annotations

from collections import deque
from datetime import date, datetime
import heapq
from math import asin, cos, radians, sin, sqrt
from pathlib import Path
import sqlite3
from typing import TYPE_CHECKING, Any
from collections.abc import Iterable, Iterator

from ._normalization import normalize_name
from ._version import SCHEMA_VERSION, __version__
from .database import Database
from ._learning import (FLASHCARD_TOPICS, build_flashcard, has_flashcard_answer,
                        stable_country_sample, stable_text_order)
from ._rankings import METRIC_UNITS, metric_value, normalize_metric
from ._profiles import build_country, city_from_row, read_local_names
from ._placekinds import CATEGORIES, KINDS, category_of, kind_of
from ._sun import sun_times
from .exceptions import (AmbiguousCountryError, AmbiguousPlaceError,
                         AtlasClosedError, CapitalNotFoundError,
                         CountryNotFoundError, DatasetVersionError,
                         PackNotInstalledError, PlaceNotFoundError)
from .models import (Airport, Antipode, BorderPathResult, Capital, CapitalDistance, City,
                     CityDistance, Coordinate, Country, Indicator, StatisticSeries, StatisticValue,
                     CountryMatch, CountryRanking, DatasetInfo, Flashcard, LocalizedName, Place,
                     PlaceDistance, PlaceQuestion, QuizQuestion, SiteDistance, SunTimes, WorldHeritageSite)

if TYPE_CHECKING:
    from . import _placefile, packs
    from ._landmarks import Landmarks
    from ._statistics import Statistics
    from .maps import CountryMap
else:
    from ._lazy import LazyModule

    # Place files, packs, and landmarks need compression, hashing, and zip
    # modules. They load on first use, so ``import pyworldatlas`` stays quick
    # on small computers such as a Raspberry Pi.
    _placefile = LazyModule("pyworldatlas._placefile")
    packs = LazyModule("pyworldatlas.packs")


def _name_variants(key: str) -> tuple[str, ...]:
    """Return the exact lookup key, then common spelling variants of it.

    People often add or drop a leading "the" ("The Gambia", "Netherlands") and
    shorten "Saint" to "St" ("St Lucia"). Variants are tried only when the exact
    key has no match, so they never change an existing result.
    """
    words = key.split()
    variants = [key]
    if words and words[0] == "the":
        variants.append(" ".join(words[1:]))
    elif words:
        variants.append(f"the {key}")
    if "st" in words:
        variants.append(" ".join("saint" if word == "st" else word for word in words))
    return tuple(dict.fromkeys(variant for variant in variants if variant))


# GeoNames codes for whole countries and territories, shown as Country profiles.
_COUNTRY_CODES = frozenset({"A.PCL", "A.PCLD", "A.PCLF", "A.PCLI", "A.PCLS", "A.TERR"})


class Atlas:
    """Open and explore the bundled, read-only world atlas.

    With no arguments, :class:`Atlas` uses the SQLite dataset shipped inside
    the package. Pass ``database_path`` only when working with a compatible
    database built by the PyWorldAtlas pipeline. A context manager closes the
    database promptly; already materialized immutable models remain usable.
    Runtime lookups and calculations require no network access.

    ``data_dir`` selects the folder of optional data packs, such as 3D maps.
    It defaults to ``PYWORLDATLAS_DATA`` or a per-user folder; see
    :mod:`pyworldatlas.packs`.
    """

    def __init__(
        self,
        database_path: str | Path | None = None,
        *,
        data_dir: str | Path | None = None,
    ) -> None:
        self._db = Database(database_path)
        self._data_dir = data_dir
        self._closed = False
        self._country_cache: dict[int, Country] = {}
        self._local_names_cache: dict[int, tuple[LocalizedName, ...]] | None = None
        self._border_cache: dict[int, tuple[int, ...]] | None = None
        self._bulk_rows: dict[str, dict[int, list[sqlite3.Row]]] | None = None
        self._query_cache: dict[str, tuple[int, ...]] = {}
        self._code_cache: dict[str, tuple[int, ...]] | None = None
        self._city_cache: list[tuple[sqlite3.Row, float, float, float]] | None = None
        self._place_indexes: list[sqlite3.Connection] | None = None
        self._landmarks: Landmarks | None = None
        self._statistics: Statistics | None = None
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
        """Return the installed library, database schema, and dataset versions.

        Record these values when a lesson or calculation must be reproducible.
        """
        self._ensure_open()
        return DatasetInfo(__version__, SCHEMA_VERSION, self._meta("dataset_version"), len(self), self._meta("built_at"))

    def _country_ids(self, query: str) -> tuple[int, ...]:
        self._ensure_open()
        if not isinstance(query, str):
            return self._read_country_ids(query)
        ids = self._query_cache.get(query)
        if ids is None:
            if len(self._query_cache) >= 4096:
                self._query_cache.clear()
            ids = self._query_cache[query] = self._read_country_ids(query)
        return ids

    def _read_country_ids(self, query: str) -> tuple[int, ...]:
        if isinstance(query, str) and query.isascii():
            code_ids = self._code_ids().get(query.upper())
            if code_ids:
                return code_ids
        elif not isinstance(query, str):
            code_rows = self._db.connection.execute(
                """SELECT id FROM country
                   WHERE upper(alpha2)=upper(?) OR upper(alpha3)=upper(?)
                      OR numeric_code=?
                   ORDER BY id""",
                (query, query, query),
            ).fetchall()
            if code_rows:
                return tuple(int(row[0]) for row in code_rows)

        for key in _name_variants(normalize_name(query)):
            name_rows = self._db.connection.execute(
                """SELECT DISTINCT country_id FROM country_name
                   WHERE normalized_name=? ORDER BY country_id""",
                (key,),
            ).fetchall()
            if name_rows:
                return tuple(int(row[0]) for row in name_rows)
        return ()

    def _code_ids(self) -> dict[str, tuple[int, ...]]:
        """Map upper-case alpha-2, alpha-3, and numeric codes to country ids."""
        if self._code_cache is None:
            grouped: dict[str, set[int]] = {}
            rows = self._db.connection.execute(
                "SELECT id, alpha2, alpha3, numeric_code FROM country"
            )
            for row in rows:
                for code in (row["alpha2"], row["alpha3"], row["numeric_code"]):
                    if code is not None:
                        grouped.setdefault(str(code).upper(), set()).add(int(row["id"]))
            self._code_cache = {
                code: tuple(sorted(ids)) for code, ids in grouped.items()
            }
        return self._code_cache

    def _country_id(self, query: str) -> int | None:
        ids = self._country_ids(query)
        return ids[0] if len(ids) == 1 else None

    def country(self, query: str) -> Country:
        """Return one country profile resolved from a name or standard code.

        ``query`` may be a familiar English name, indexed alias, alpha-2 code,
        alpha-3 code, or three-digit M49 code. Matching is case-insensitive and
        accent-tolerant. Missing queries raise :class:`CountryNotFoundError`,
        with suggestions when available. A name shared by multiple profiles
        raises :class:`AmbiguousCountryError` and lists the matches.
        """
        self._ensure_open()
        if not isinstance(query, str):
            raise TypeError("query must be a string")
        if not normalize_name(query):
            raise ValueError("query must contain at least one letter or number")
        country_ids = self._country_ids(query)
        if not country_ids:
            suggestions = ", ".join(match.country.name for match in self.search_countries(query, limit=3))
            hint = f" Try: {suggestions}." if suggestions else ""
            raise CountryNotFoundError(f"No country matches {query!r}.{hint}")
        if len(country_ids) > 1:
            matches = ", ".join(
                f"{country.name} ({country.alpha2})"
                for country in (self._load_country(item) for item in country_ids)
            )
            raise AmbiguousCountryError(
                f"Country name {query!r} is ambiguous; matches include {matches}"
            )
        return self._load_country(country_ids[0])

    def get(self, query: str, default: Country | None = None) -> Country | None:
        """Return a matching country, or ``default`` instead of raising.

        Use :meth:`country` when a missing profile should be treated as an
        error. ``default`` is returned for both missing and non-unique queries.
        """
        try:
            return self.country(query)
        except (CountryNotFoundError, AmbiguousCountryError):
            return default

    def map(
        self,
        country: str | Country,
        *,
        quality: str = "auto",
        places: int = 8,
    ) -> CountryMap:
        """Return an interactive offline 3D map for a country profile.

        ``country`` accepts the same names and codes as :meth:`country`, or an
        already loaded :class:`Country`. ``quality="auto"`` prefers Standard
        map data when installed and otherwise uses Overview data.

        The map marks the ``places`` best-known towns, mountains and islands,
        lakes and seas, and landmarks of the country, each kind as a layer
        that can be shown or hidden. Pass ``places=0`` for terrain only.

        The returned map opens in the default browser when its ``show()``
        method is called. Maps need a map pack, installed once with
        ``pyworldatlas get maps`` (Standard) or ``pyworldatlas get maps-lite``
        (Overview). Packs are read from this atlas's ``data_dir``.
        """
        self._ensure_open()
        if isinstance(country, str):
            profile = self.country(country)
        elif isinstance(country, Country):
            profile = country
        else:
            raise TypeError("country must be a country name, code, or Country")
        from .exceptions import MapSupportNotInstalledError
        from .maps import CountryMap, MapDataError

        if isinstance(places, bool) or not isinstance(places, int) or places < 0:
            raise ValueError("places must be zero or a positive integer")
        marked: list[Place] = []
        if places:
            for category in ("town", "landform", "water", "landmark"):
                marked.extend(self.places_in(profile, category=category, limit=places))
        result = CountryMap.from_country(
            profile, quality=quality, data_dir=self._data_dir, places=tuple(marked)
        )
        try:
            _ = result.quality  # find the map pack now so a missing pack fails here
        except MapDataError as error:
            raise MapSupportNotInstalledError(str(error)) from error
        return result

    def search_countries(self, query: str, *, limit: int = 20) -> tuple[CountryMatch, ...]:
        """Return ranked partial-name matches for human-entered text.

        Matching is case-insensitive and accent-tolerant. Exact matches rank
        before prefixes and substrings. The returned tuple is empty when no
        indexed name matches; use :meth:`country` for exact resolution.
        """
        self._ensure_open()
        if not isinstance(query, str):
            raise TypeError("query must be a string")
        normalized = normalize_name(query)
        if not normalized:
            raise ValueError("query must contain at least one letter or number")
        if isinstance(limit, bool) or not isinstance(limit, int) or limit <= 0:
            raise ValueError("limit must be a positive integer")
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

    def countries(
        self,
        *,
        continent: str | None = None,
        region: str | None = None,
        currency_code: str | None = None,
        language_code: str | None = None,
        script_code: str | None = None,
        timezone_id: str | None = None,
        coastal: bool | None = None,
        koppen_geiger_code: str | None = None,
        has_rivers: bool | None = None,
        has_lakes: bool | None = None,
    ) -> tuple[Country, ...]:
        """Return countries alphabetically with optional exact profile filters.

        Filters can be combined and use AND semantics. With no filters, every
        bundled profile is returned in display-name order.

        Physical-data filters only include profiles covered by the relevant
        source layer. For example, ``coastal=False`` means a sourced coastline
        of zero kilometres; it does not treat missing coastline data as zero.
        """
        self._ensure_open()
        clauses, params = [], []
        if continent:
            clauses.append("continent = ?")
            params.append(continent)
        if region:
            clauses.append("(region = ? OR subregion = ?)")
            params.extend((region, region))
        if currency_code:
            clauses.append("upper(currency_code) = upper(?)")
            params.append(currency_code)
        if language_code:
            clauses.append(
                "id IN (SELECT country_id FROM country_language "
                "WHERE lower(code)=lower(?) OR lower(primary_code)=lower(?))"
            )
            params.extend((language_code, language_code))
        if script_code:
            clauses.append(
                "id IN (SELECT country_id FROM country_language WHERE lower(script_code)=lower(?))"
            )
            params.append(script_code)
        if timezone_id:
            clauses.append(
                "id IN (SELECT country_id FROM country_timezone WHERE lower(timezone_id)=lower(?))"
            )
            params.append(timezone_id)
        if coastal is not None:
            if not isinstance(coastal, bool):
                raise TypeError("coastal must be bool or None")
            comparison = "> 0" if coastal else "= 0"
            clauses.append(
                "id IN (SELECT country_id FROM country_physical "
                f"WHERE coastline_km {comparison})"
            )
        if koppen_geiger_code:
            clauses.append(
                "id IN (SELECT country_id FROM country_climate_zone "
                "WHERE upper(code)=upper(?))"
            )
            params.append(koppen_geiger_code)
        for requested, table, label in (
            (has_rivers, "country_river", "has_rivers"),
            (has_lakes, "country_lake", "has_lakes"),
        ):
            if requested is not None:
                if not isinstance(requested, bool):
                    raise TypeError(f"{label} must be bool or None")
                operator = "IN" if requested else "NOT IN"
                clauses.append(f"id {operator} (SELECT country_id FROM {table})")
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        rows = self._db.connection.execute(f"SELECT id FROM country{where} ORDER BY name", params).fetchall()
        return self._load_countries(int(row[0]) for row in rows)

    def rank_countries(
        self,
        metric: str,
        *,
        limit: int | None = None,
        descending: bool = True,
        continent: str | None = None,
        region: str | None = None,
    ) -> tuple[CountryRanking, ...]:
        """Rank countries by a documented sourced or directly derived metric.

        Supported physical metrics include ``"land_area"``, ``"water_area"``,
        ``"water_percent"``, ``"coastline"``, ``"mean_elevation"``,
        ``"highest_elevation"``, ``"lowest_elevation"``, ``"river_count"``,
        ``"lake_count"``, and ``"climate_zone_count"``. Existing population,
        total area, density, border, and city metrics remain available. Missing
        values are excluded.
        """
        normalized_metric = normalize_metric(metric)
        if limit is not None and (
            isinstance(limit, bool) or not isinstance(limit, int) or limit <= 0
        ):
            raise ValueError("limit must be a positive integer or None")

        ranked: list[tuple[Country, int | float]] = []
        for country in self.countries(continent=continent, region=region):
            value = metric_value(
                country, normalized_metric, lambda item: len(self.neighbors(item.alpha2))
            )
            if value is not None:
                ranked.append((country, value))
        ranked.sort(
            key=lambda item: (
                -float(item[1]) if descending else float(item[1]),
                item[0].name,
            )
        )
        if limit is not None:
            ranked = ranked[:limit]
        return tuple(
            CountryRanking(position, country.reference(), normalized_metric, value, METRIC_UNITS[normalized_metric])
            for position, (country, value) in enumerate(ranked, 1)
        )

    def rank(self, metric: str, **kwargs: Any) -> tuple[CountryRanking, ...]:
        """Alias for :meth:`rank_countries` suited to exploratory sessions."""
        return self.rank_countries(metric, **kwargs)

    def climate_zone_codes(self) -> tuple[str, ...]:
        """Return every represented Köppen-Geiger code in source legend order."""
        self._ensure_open()
        rows = self._db.connection.execute(
            "SELECT DISTINCT code FROM country_climate_zone"
        ).fetchall()
        # SQLite row order is not a scientific legend. The explicit class
        # sequence makes the public result stable across database rebuilds.
        order = (
            "Af", "Am", "Aw", "BWh", "BWk", "BSh", "BSk", "Csa", "Csb",
            "Csc", "Cwa", "Cwb", "Cwc", "Cfa", "Cfb", "Cfc", "Dsa", "Dsb",
            "Dsc", "Dsd", "Dwa", "Dwb", "Dwc", "Dwd", "Dfa", "Dfb", "Dfc",
            "Dfd", "ET", "EF",
        )
        present = {str(row[0]) for row in rows}
        return tuple(code for code in order if code in present)

    def countries_in_climate_zone(self, code: str) -> tuple[Country, ...]:
        """Return profiles containing the exact Köppen-Geiger class ``code``."""
        if code.casefold() not in {
            item.casefold() for item in self.climate_zone_codes()
        }:
            raise ValueError(
                f"Unknown or unrepresented Köppen-Geiger code {code!r}"
            )
        return self.countries(koppen_geiger_code=code)

    def countries_with_river(self, name: str | None = None) -> tuple[Country, ...]:
        """Return profiles with source-listed major rivers.

        When ``name`` is supplied, it is matched case-insensitively against the
        concise feature name and retained source label. Results are alphabetical.
        """
        self._ensure_open()
        if name is None:
            return self.countries(has_rivers=True)
        query = f"%{name.casefold()}%"
        rows = self._db.connection.execute(
            """SELECT DISTINCT c.id FROM country c
               JOIN country_river r ON r.country_id=c.id
               WHERE lower(r.name) LIKE ? OR lower(r.source_label) LIKE ?
               ORDER BY c.name""",
            (query, query),
        ).fetchall()
        return self._load_countries(int(row[0]) for row in rows)

    def countries_with_lake(self, name: str | None = None) -> tuple[Country, ...]:
        """Return profiles with source-listed major lakes.

        When ``name`` is supplied, it is matched case-insensitively against the
        concise feature name and retained source label. Results are alphabetical.
        """
        self._ensure_open()
        if name is None:
            return self.countries(has_lakes=True)
        query = f"%{name.casefold()}%"
        rows = self._db.connection.execute(
            """SELECT DISTINCT c.id FROM country c
               JOIN country_lake l ON l.country_id=c.id
               WHERE lower(l.name) LIKE ? OR lower(l.source_label) LIKE ?
               ORDER BY c.name""",
            (query, query),
        ).fetchall()
        return self._load_countries(int(row[0]) for row in rows)

    def countries_with_local_names(
        self,
        *,
        language_code: str | None = None,
        script_code: str | None = None,
        name_kind: str | None = None,
    ) -> tuple[Country, ...]:
        """Return countries with sourced local-language name records.

        Results are alphabetical. ``language_code`` and ``script_code`` are
        optional, case-insensitive exact filters such as ``"es"``, ``"hi"``,
        ``"Deva"``, or ``"Jpan"``. Every UN M49 record has one selected local
        identity. Inspect ``LocalizedName.kind`` to distinguish reviewed
        national official forms from CLDR locale display names, or pass
        ``name_kind="national_official"`` or ``"locale_display"`` directly.
        """
        self._ensure_open()
        clauses: list[str] = []
        params: list[str] = []
        if language_code is not None:
            clauses.append("lower(n.language_code) = lower(?)")
            params.append(language_code)
        if script_code is not None:
            clauses.append("lower(n.script_code) = lower(?)")
            params.append(script_code)
        if name_kind is not None:
            normalized_kind = name_kind.casefold()
            if normalized_kind not in {"national_official", "locale_display"}:
                raise ValueError(
                    "name_kind must be 'national_official' or 'locale_display'"
                )
            clauses.append("n.name_kind = ?")
            params.append(normalized_kind)
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        rows = self._db.connection.execute(
            f"""SELECT DISTINCT c.id
                FROM country c JOIN country_local_name n ON n.country_id = c.id
                {where}
                ORDER BY c.name""",
            params,
        ).fetchall()
        return self._load_countries(int(row[0]) for row in rows)

    def countries_with_formal_names(self) -> tuple[Country, ...]:
        """Return countries and areas with a sourced English formal name.

        Results are alphabetical. Some countries use the same sourced text for
        their short and formal forms; check ``Country.has_distinct_formal_name``
        when an application needs only distinct long forms.
        """
        self._ensure_open()
        rows = self._db.connection.execute(
            """SELECT DISTINCT c.id
               FROM country c JOIN country_name n ON n.country_id = c.id
               WHERE n.kind = 'formal'
               ORDER BY c.name"""
        ).fetchall()
        return self._load_countries(int(row[0]) for row in rows)

    def _border_adjacency(self) -> dict[int, tuple[int, ...]]:
        """Load the undirected border graph once for graph operations."""
        if self._border_cache is None:
            self._border_cache = self._read_border_adjacency()
        return self._border_cache

    def _read_border_adjacency(self) -> dict[int, tuple[int, ...]]:
        self._ensure_open()
        country_rows = self._db.connection.execute(
            "SELECT id, name FROM country ORDER BY name"
        ).fetchall()
        names = {int(row["id"]): str(row["name"]) for row in country_rows}
        graph: dict[int, list[int]] = {country_id: [] for country_id in names}
        rows = self._db.connection.execute(
            "SELECT country1_id, country2_id FROM country_border"
        ).fetchall()
        for row in rows:
            first, second = int(row["country1_id"]), int(row["country2_id"])
            graph[first].append(second)
            graph[second].append(first)
        return {
            country_id: tuple(sorted(neighbors, key=lambda item: names[item]))
            for country_id, neighbors in graph.items()
        }

    def _border_country_id(self, query: str) -> int:
        """Resolve a public country query for an internal graph operation."""
        country_id = self._country_id(query)
        if country_id is None:
            self.country(query)  # raises the public error with ranked suggestions
            raise CountryNotFoundError(f"No unambiguous country matches {query!r}")  # pragma: no cover
        return country_id

    def neighbors(self, country: str) -> tuple[Country, ...]:
        """Return countries sharing a reviewed land border with ``country``.

        Results are alphabetized and immutable. Maritime neighbors, proximity,
        and mere point contacts are excluded. Countries and areas without an
        accepted land-border relationship return an empty tuple.
        """
        country_id = self._border_country_id(country)
        return tuple(self._load_country(item) for item in self._border_adjacency()[country_id])

    def shares_border(self, country1: str, country2: str) -> bool:
        """Return whether two countries share a reviewed land border."""
        first = self._border_country_id(country1)
        second = self._border_country_id(country2)
        return second in self._border_adjacency()[first]

    def shared_neighbors(self, country1: str, country2: str) -> tuple[Country, ...]:
        """Return alphabetized land neighbors shared by two countries."""
        first = self._border_country_id(country1)
        second = self._border_country_id(country2)
        common = set(self._border_adjacency()[first]) & set(self._border_adjacency()[second])
        return tuple(sorted((self._load_country(item) for item in common), key=lambda item: item.name))

    def border_path(self, origin: str, destination: str) -> BorderPathResult | None:
        """Return a deterministic shortest land-border path, or ``None``.

        The path uses breadth-first search over the reviewed undirected graph.
        Both endpoints are included. Equal-length alternatives are resolved by
        alphabetic neighbor order. ``None`` means the two entities have no path
        through accepted land-border relationships; it is not an error.
        """
        start = self._border_country_id(origin)
        finish = self._border_country_id(destination)
        parents: dict[int, int | None] = {start: None}
        queue = deque([start])
        graph = self._border_adjacency()
        while queue and finish not in parents:
            current = queue.popleft()
            for neighbor in graph[current]:
                if neighbor not in parents:
                    parents[neighbor] = current
                    queue.append(neighbor)
        if finish not in parents:
            return None
        path = [finish]
        parent = parents[finish]
        while parent is not None:
            path.append(parent)
            parent = parents[parent]
        path.reverse()
        references = tuple(self._load_country(item).reference() for item in path)
        return BorderPathResult(references, len(references) - 1)

    def border_crossings(self, origin: str, destination: str) -> int | None:
        """Return the fewest land-border crossings, or ``None`` if unreachable."""
        path = self.border_path(origin, destination)
        return path.crossings if path else None

    def has_land_route(self, origin: str, destination: str) -> bool:
        """Return whether ``origin`` and ``destination`` are land-connected.

        This is derived at query time from the reviewed border graph; it does
        not use road, rail, ferry, maritime, or travel-access data. Identical
        endpoints return ``True`` because their shortest graph path has zero
        border crossings. Unknown country queries raise
        :class:`~pyworldatlas.CountryNotFoundError`.
        """
        return self.border_path(origin, destination) is not None

    def countries_reachable_by_land(self, country: str) -> tuple[Country, ...]:
        """Return every other entity in ``country``'s land-connected component.

        The starting country is excluded. Results are alphabetized; an island
        or otherwise borderless entity returns an empty tuple.
        """
        start = self._border_country_id(country)
        graph = self._border_adjacency()
        reached = {start}
        queue = deque([start])
        while queue:
            for neighbor in graph[queue.popleft()]:
                if neighbor not in reached:
                    reached.add(neighbor)
                    queue.append(neighbor)
        reached.remove(start)
        return tuple(sorted((self._load_country(item) for item in reached), key=lambda item: item.name))

    def countries_with_no_land_borders(self) -> tuple[Country, ...]:
        """Return all bundled entities with no accepted land-border relation."""
        return tuple(
            self._load_country(country_id)
            for country_id, neighbors in self._border_adjacency().items()
            if not neighbors
        )

    def sample_countries(
        self,
        *,
        count: int,
        continent: str | None = None,
        region: str | None = None,
        seed: int | str = 0,
    ) -> tuple[Country, ...]:
        """Return a reproducible educational sample of country profiles.

        Candidates are ranked with a versioned SHA-256 algorithm using their
        stable M49 identifiers. Results therefore do not depend on SQLite row
        order, global random state, or implementation details of
        ``random.sample()``. The same dataset, filters, count, and seed produce the
        same ordered result across supported Python versions.

        ``count`` must be positive and cannot exceed the filtered population.
        ``continent`` and ``region`` follow :meth:`countries` semantics.
        """
        return stable_country_sample(
            self.countries(continent=continent, region=region), count, seed
        )

    def learning_topics(self) -> tuple[str, ...]:
        """Return topics supported by :meth:`flashcards` and :meth:`quiz`.

        The tuple is stable, alphabetized, and safe to use for menus, lesson
        builders, or playground controls.
        """
        self._ensure_open()
        return FLASHCARD_TOPICS

    def flashcards(
        self,
        *,
        topic: str,
        count: int,
        continent: str | None = None,
        region: str | None = None,
        seed: int | str = 0,
    ) -> tuple[Flashcard, ...]:
        """Return deterministic, immutable geography flashcards.

        Supported topics are ``alpha_2_codes``, ``alpha_3_codes``, ``areas``,
        ``border_counts``, ``calling_codes``, ``capitals``, ``climate_zones``,
        ``coastlines``, ``continents``,
        ``countries_from_capitals``, ``currencies``, ``driving_sides``, ``flags``,
        ``highest_points``, ``language_codes``, ``lakes``, ``local_names``,
        ``m49_codes``, ``mains_electricity``, ``neighbors``, ``plug_types``, ``rivers``,
        ``population_density``, ``populations``, ``regions``, and
        ``top_level_domains``. Countries missing the answer required by a topic
        are excluded before sampling. An impossible count raises
        :class:`ValueError` rather than silently returning fewer cards.

        Population, area, and density answers describe the captured source
        snapshot. Neighbor and border-count answers are derived from the
        reviewed land-border graph. Local-name cards use the selected CLDR or
        UNGEGN identity record for every country and area.
        Flashcards are structured values, not an interactive game.
        """
        if topic not in FLASHCARD_TOPICS:
            allowed = ", ".join(FLASHCARD_TOPICS)
            raise ValueError(f"unsupported flashcard topic {topic!r}; choose from {allowed}")
        candidates = tuple(
            country
            for country in self.countries(continent=continent, region=region)
            if self._has_flashcard_answer(country, topic)
        )
        selected = stable_country_sample(candidates, count, seed)
        return tuple(self._flashcard(country, topic) for country in selected)

    def quiz(
        self,
        *,
        topic: str,
        count: int,
        choices: int = 4,
        continent: str | None = None,
        region: str | None = None,
        seed: int | str = 0,
    ) -> tuple[QuizQuestion, ...]:
        """Build deterministic multiple-choice questions from sourced facts.

        ``topic`` accepts every value returned by :meth:`learning_topics`.
        ``choices`` must be an integer from 2 through 6. Questions, distractors,
        and answer positions remain stable for the same dataset, filters, and
        seed, making answer keys reproducible across supported Python versions.

        The method raises :class:`ValueError` when the filtered profiles do not
        provide enough distinct answers for the requested number of choices.
        No scoring, learner data, or session state is stored.
        """
        if topic not in FLASHCARD_TOPICS:
            allowed = ", ".join(FLASHCARD_TOPICS)
            raise ValueError(f"unsupported quiz topic {topic!r}; choose from {allowed}")
        if isinstance(choices, bool) or not isinstance(choices, int):
            raise TypeError("choices must be an integer")
        if not 2 <= choices <= 6:
            raise ValueError("choices must be between 2 and 6")

        candidates = tuple(
            country
            for country in self.countries(continent=continent, region=region)
            if self._has_flashcard_answer(country, topic)
        )
        selected = stable_country_sample(candidates, count, seed)
        cards = tuple(self._flashcard(country, topic) for country in candidates)
        distinct_answers: dict[str, str] = {}
        for card in cards:
            distinct_answers.setdefault(card.answer.casefold(), card.answer)
        if len(distinct_answers) < choices:
            raise ValueError(
                f"topic {topic!r} has only {len(distinct_answers)} distinct answers "
                f"for the selected filters; {choices} choices were requested"
            )

        questions = []
        for country in selected:
            card = self._flashcard(country, topic)
            distractors = tuple(
                answer
                for normalized, answer in distinct_answers.items()
                if normalized != card.answer.casefold()
            )
            namespace = f"quiz-distractors:{topic}:{country.alpha2}"
            picked = stable_text_order(
                distractors, seed=seed, namespace=namespace
            )[: choices - 1]
            ordered_choices = stable_text_order(
                (card.answer, *picked),
                seed=seed,
                namespace=f"quiz-choices:{topic}:{country.alpha2}",
            )
            questions.append(
                QuizQuestion(
                    topic=topic,
                    prompt=card.prompt,
                    choices=ordered_choices,
                    answer=card.answer,
                    country=card.country,
                )
            )
        return tuple(questions)

    def _has_flashcard_answer(self, country: Country, topic: str) -> bool:
        return has_flashcard_answer(country, topic, self._has_neighbors)

    def _has_neighbors(self, country: Country) -> bool:
        country_id = self._country_id(country.alpha2)
        return country_id is not None and bool(self._border_adjacency()[country_id])

    def _flashcard(self, country: Country, topic: str) -> Flashcard:
        return build_flashcard(
            country, topic, lambda item: self.neighbors(item.alpha2)
        )

    def major_cities(self, country: str, *, limit: int | None = None) -> tuple[City, ...]:
        """Return populated places for a country, ordered by population and name.

        ``limit=None`` returns every bundled place for the country. The records
        come from the package snapshot and are not live population estimates.
        """
        result = self.country(country).major_cities
        if limit is None:
            return result
        if isinstance(limit, bool) or not isinstance(limit, int) or limit <= 0:
            raise ValueError("limit must be a positive integer or None")
        return result[:limit]

    def search_cities(
        self,
        query: str,
        *,
        country: str | None = None,
        limit: int = 20,
    ) -> tuple[City, ...]:
        """Return ranked city-name matches from the bundled place table.

        Matching is case-insensitive and accent-tolerant. Exact names rank
        first, followed by prefix and substring matches; population breaks
        ties. Pass ``country`` as a familiar country name or code to narrow the
        search. An empty result is returned when nothing matches.
        """
        self._ensure_open()
        if not isinstance(query, str):
            raise TypeError("query must be a string")
        normalized = normalize_name(query)
        if not normalized:
            raise ValueError("query must contain at least one letter or number")
        if isinstance(limit, bool) or not isinstance(limit, int) or limit <= 0:
            raise ValueError("limit must be a positive integer")

        params: list[object] = [f"%{normalized}%"]
        where = "c.normalized_name LIKE ?"
        if country is not None:
            country_id = self._country_id(self.country(country).alpha2)
            where += " AND c.country_id = ?"
            params.append(country_id)
        rows = self._db.connection.execute(
            f"""SELECT c.*, co.alpha2 FROM city c
                JOIN country co ON co.id = c.country_id
                WHERE {where}""",
            params,
        ).fetchall()

        def rank(row: sqlite3.Row) -> tuple[object, ...]:
            candidate = row["normalized_name"]
            score = 100 if candidate == normalized else 80 if candidate.startswith(normalized) else 50
            population = row["population"] if row["population"] is not None else -1
            return (-score, -population, row["name"].casefold(), row["alpha2"], row["geonames_id"])

        return tuple(self._city_from_row(row) for row in sorted(rows, key=rank)[:limit])

    def city(self, query: str, *, country: str | None = None) -> City:
        """Return one exact bundled city, optionally limited to a country.

        Matching is case-insensitive and accent-tolerant. Pass a familiar
        country name or code when the city name is shared. Missing names raise
        :class:`PlaceNotFoundError`; ambiguous names raise
        :class:`AmbiguousPlaceError` with example matches.
        """
        self._ensure_open()
        normalized = normalize_name(query)
        params: list[object] = [normalized]
        where = "c.normalized_name=?"
        if country is not None:
            country_id = self._country_id(country)
            if country_id is None:
                raise CountryNotFoundError(f"No unambiguous country matches {country!r}")
            where += " AND c.country_id=?"
            params.append(country_id)
        rows = self._db.connection.execute(
            f"""SELECT c.*, co.alpha2 FROM city c JOIN country co ON co.id=c.country_id
                WHERE {where} ORDER BY c.population DESC, c.geonames_id""", params,
        ).fetchall()
        if not rows:
            suffix = f" in {country!r}" if country else ""
            raise PlaceNotFoundError(f"No city matches {query!r}{suffix}")
        if len(rows) > 1:
            options = ", ".join(f"{row['name']} ({row['alpha2']})" for row in rows[:5])
            raise AmbiguousPlaceError(f"City {query!r} is ambiguous. Specify country; matches include {options}")
        return self._city_from_row(rows[0])

    def coordinates(self, query: str, *, country: str | None = None) -> Coordinate:
        """Return WGS84 coordinates for an exact bundled city lookup.

        This is shorthand for ``atlas.city(query, country=country).coordinates``.
        """
        return self.city(query, country=country).coordinates

    def distance_between(
        self,
        first: str | Country | Capital | City | Coordinate | tuple[float, float],
        second: str | Country | Capital | City | Coordinate | tuple[float, float],
        *,
        unit: str = "km",
        first_country: str | None = None,
        second_country: str | None = None,
    ) -> float:
        """Return great-circle distance between city, model, or coordinate inputs.

        Accepted inputs are exact bundled-city names, :class:`City`,
        :class:`Capital`, :class:`Country`, :class:`Coordinate`, or
        ``(latitude, longitude)`` tuples. Country objects use their primary
        capitals. ``unit`` accepts ``"km"``, ``"mi"``, or ``"nmi"``.
        The result is a surface measurement, not a road or flight route.
        """
        start = self._coordinates_of(first, country=first_country)
        finish = self._coordinates_of(second, country=second_country)
        return start.distance_to(finish, unit=unit)

    def nearest_capitals(
        self,
        origin: str | Country | Capital | City | Coordinate | tuple[float, float],
        *,
        limit: int = 5,
        unit: str = "km",
        country: str | None = None,
        include_origin: bool = False,
    ) -> tuple[CapitalDistance, ...]:
        """Return primary capitals nearest to a city, country, or coordinate.

        String origins use the exact city lookup and may be constrained with
        ``country``. Pass a :class:`Country` to measure from its primary
        capital or a :class:`Coordinate` for an arbitrary starting point.
        ``unit`` accepts ``"km"``, ``"mi"``, or ``"nmi"``. Results are ordered
        nearest first with deterministic name tie-breaking.
        """
        if isinstance(limit, bool) or not isinstance(limit, int) or limit <= 0:
            raise ValueError("limit must be a positive integer")
        start = self._coordinates_of(origin, country=country)
        results: list[CapitalDistance] = []
        for candidate in self.countries():
            capital = candidate.capital
            if capital is None:
                continue
            distance = start.distance_to(capital.coordinates, unit=unit)
            if not include_origin and distance <= 1e-9:
                continue
            results.append(
                CapitalDistance(candidate.reference(), capital, distance, unit)
            )
        results.sort(key=lambda result: (result.distance, result.country.name))
        return tuple(results[:limit])

    def nearest_cities(
        self,
        origin: str | Country | Capital | City | Coordinate | tuple[float, float],
        *,
        limit: int = 5,
        unit: str = "km",
        origin_country: str | None = None,
        within_country: str | None = None,
        include_origin: bool = False,
    ) -> tuple[CityDistance, ...]:
        """Return bundled populated places nearest to an origin.

        String origins are exact city names and can be disambiguated with
        ``origin_country``. ``within_country`` limits results to one country or
        area. By default, records at the origin's exact coordinates are omitted.
        Distances are great-circle surface measurements, not road distances.
        """
        if isinstance(limit, bool) or not isinstance(limit, int) or limit <= 0:
            raise ValueError("limit must be a positive integer")
        if not isinstance(include_origin, bool):
            raise TypeError("include_origin must be a bool")
        start = self._coordinates_of(origin, country=origin_country)
        start.distance_to(start, unit=unit)

        country_filter = None
        if within_country is not None:
            country_filter = self._country_id(self.country(within_country).alpha2)

        # Rank cached raw rows first and build models only for the returned places.
        # The arithmetic mirrors Coordinate.distance_to step for step, so the
        # distances are identical to the public method's results.
        factor = {"km": 1.0, "mi": 0.621371192237334, "nmi": 0.539956803455724}[unit]
        lat1, lon1 = radians(start.latitude), radians(start.longitude)
        cos_lat1 = cos(lat1)
        ranked = []
        for row, lat2, lon2, cos_lat2 in self._city_positions():
            if country_filter is not None and row["country_id"] != country_filter:
                continue
            delta_lat, delta_lon = lat2 - lat1, lon2 - lon1
            haversine = sin(delta_lat / 2) ** 2 + cos_lat1 * cos_lat2 * sin(delta_lon / 2) ** 2
            distance = 2 * 6371.0088 * asin(min(1.0, sqrt(haversine))) * factor
            if not include_origin and distance <= 1e-9:
                continue
            key = (distance, row["country_name"], row["name"], row["geonames_id"] or 0)
            ranked.append((key, row))
        return tuple(
            CityDistance(
                self._load_country(int(row["country_id"])).reference(),
                self._city_from_row(row),
                key[0],
                unit,
            )
            for key, row in heapq.nsmallest(limit, ranked, key=lambda item: item[0])
        )

    # --- every place on Earth -----------------------------------------------------

    PLACE_PACKS = ("places-explorer", "places-world")
    """Data packs that add places to the bundled school atlas, smallest first."""

    def _places(self) -> list[sqlite3.Connection]:
        """Open the place indexes once: the school atlas plus any installed place packs."""
        self._ensure_open()
        if self._place_indexes is None:
            sources = [Path(__file__).resolve().parent / "data" / "places.pwpl"]
            for name in self.PLACE_PACKS:
                folder = packs.pack_path(name, self._data_dir)
                if folder is not None and (folder / "places.pwpl").is_file():
                    sources.append(folder / "places.pwpl")
            cache = packs.data_dir(self._data_dir) / "index"
            self._place_indexes = [_placefile.open_index(source, cache) for source in sources if source.is_file()]
        return self._place_indexes

    @staticmethod
    def _place_from_row(row: sqlite3.Row) -> Place:
        code = row["code"]
        return Place(
            row["name"], row["english"] or row["name"], kind_of(code), category_of(code), row["country"],
            Coordinate(row["latitude"], row["longitude"]), row["population"], row["elevation_m"],
            code, row["fame"],
        )

    def _place_filter(
        self, kind: str | None, category: str | None, country: str | None
    ) -> tuple[str, list[object]]:
        """Return an SQL condition (starting with AND) and its parameters."""
        where = ""
        params: list[object] = []
        if kind is not None:
            label = " ".join(str(kind).casefold().split())
            codes = sorted(code for code, name in KINDS.items() if name == label)
            if not codes:
                raise ValueError(f"Unknown place kind {kind!r}; see Atlas.place_kinds()")
            where += f" AND code IN ({','.join('?' * len(codes))})"
            params += codes
        if category is not None:
            letters = [letter for letter, name in CATEGORIES.items() if name == str(category).casefold()]
            if not letters:
                choices = ", ".join(sorted(CATEGORIES.values()))
                raise ValueError(f"Unknown place category {category!r}; choose from {choices}")
            where += " AND code LIKE ?"
            params.append(f"{letters[0]}.%")
        if country is not None:
            where += " AND country = ?"
            params.append(self.country(country).alpha2)
        return where, params

    @staticmethod
    def place_kinds() -> tuple[str, ...]:
        """Return every place kind accepted by place searches, such as ``"volcano"``."""
        return tuple(sorted(set(KINDS.values())))

    @staticmethod
    def place_categories() -> tuple[str, ...]:
        """Return the general place categories, such as ``"water"`` and ``"landform"``."""
        return tuple(sorted(CATEGORIES.values()))

    def search_places(
        self,
        query: str,
        *,
        kind: str | None = None,
        category: str | None = None,
        country: str | None = None,
        limit: int = 10,
    ) -> tuple[Place, ...]:
        """Find places on Earth by name, best known first.

        Searches the bundled school atlas (about 200,000 places: every country,
        region, town of 5,000 people or more, and well-known mountain, lake, river,
        island, and landmark) plus any installed place packs. Local and English
        names both match, without regard to case or accents: ``"Lake Titicaca"``
        finds ``"Lago Titicaca"``. Exact names come first, then names that start
        with the query; better-known places break ties.

        Narrow results with ``kind`` (see :meth:`place_kinds`), ``category``
        (see :meth:`place_categories`), or ``country``.
        """
        if not isinstance(query, str):
            raise TypeError("query must be a string")
        if not normalize_name(query):
            raise ValueError("query must contain at least one letter or number")
        if isinstance(limit, bool) or not isinstance(limit, int) or limit <= 0:
            raise ValueError("limit must be a positive integer")
        where, params = self._place_filter(kind, category, country)
        ranked = []
        for index in self._places():
            for score, row in _placefile.find(index, query, limit, where, params):
                name = row["english"] or row["name"]
                order = (-score, -row["fame"], -(row["population"] or 0), name, row["country"])
                ranked.append((order, row))
        ranked.sort(key=lambda item: item[0])
        seen: set[tuple[object, ...]] = set()
        result: list[Place] = []
        for _, row in ranked:
            key = (row["name"], row["code"], round(row["latitude"], 2), round(row["longitude"], 2))
            if key not in seen:
                seen.add(key)
                result.append(self._place_from_row(row))
                if len(result) == limit:
                    break
        return tuple(result)

    def place(self, query: str, *, kind: str | None = None, country: str | None = None) -> Place:
        """Return the best-known place with exactly this name.

        ``atlas.place("Kilimanjaro")`` is the mountain and ``atlas.place("Lake
        Victoria")`` the African lake. Narrow with ``kind`` or ``country`` to pick
        a less famous namesake. Raises :class:`PlaceNotFoundError` when no place
        has this exact name.
        """
        key = normalize_name(query) if isinstance(query, str) else ""
        for match in self.search_places(query, kind=kind, country=country, limit=10):
            if key in {normalize_name(match.name), normalize_name(match.english_name)}:
                return match
        suffix = f" in {country!r}" if country else ""
        raise PlaceNotFoundError(f"No place is named {query!r}{suffix}")

    def places_in(
        self,
        country: str | Country,
        *,
        kind: str | None = None,
        category: str | None = None,
        limit: int = 20,
    ) -> tuple[Place, ...]:
        """Return the best-known places in a country from the school atlas.

        Towns, mountains, lakes, landmarks, and more, best known first. Narrow
        with ``kind`` (see :meth:`place_kinds`) or ``category`` (see
        :meth:`place_categories`). The capital, whole regions, schools,
        airports, and river points are left out unless asked for by ``kind``.
        """
        if isinstance(limit, bool) or not isinstance(limit, int) or limit <= 0:
            raise ValueError("limit must be a positive integer")
        profile = country if isinstance(country, Country) else self.country(country)
        where, params = self._place_filter(kind, category, None)
        if kind is None:
            where += " AND code NOT IN ('P.PPLC', 'S.SCH', 'S.SCHC', 'S.AIRP', 'H.STM')"
            if category is None:
                where += " AND substr(code, 1, 1) NOT IN ('A', 'L', 'R', 'U')"
        rows = self._places()[0].execute(
            f"""SELECT * FROM place WHERE country = ?{where}
                ORDER BY fame DESC, population DESC, id LIMIT ?""",
            (profile.alpha2, *params, limit),
        ).fetchall()
        return tuple(self._place_from_row(row) for row in rows)

    def lookup(self, query: str, *, limit: int = 10) -> tuple[Country | Place, ...]:
        """Find anything by name: countries, cities, regions, and landmarks.

        One search for human-entered text. A country that the query names
        exactly (by name, alias, or code) comes first as a full
        :class:`Country` profile; then come the best-known places from
        :meth:`search_places`, where a country-level place is replaced by its
        :class:`Country` profile. ``atlas.lookup("Georgia")`` gives the country
        and then the US state.
        """
        if isinstance(limit, bool) or not isinstance(limit, int) or limit <= 0:
            raise ValueError("limit must be a positive integer")
        found: list[Country | Place] = []
        countries: set[str] = set()
        exact = self.get(query)
        if exact is not None:
            found.append(exact)
            countries.add(exact.alpha2)
        for place in self.search_places(query, limit=limit + 2):
            if place.feature_code in _COUNTRY_CODES:
                country = self.get(place.country_code) if place.country_code else None
                if country is not None:
                    if country.alpha2 not in countries:
                        countries.add(country.alpha2)
                        found.append(country)
                    continue
            found.append(place)
        return tuple(found[:limit])

    def places_near(
        self,
        origin: str | Country | Capital | City | Place | Coordinate | tuple[float, float],
        *,
        limit: int = 10,
        kind: str | None = None,
        category: str | None = None,
        unit: str = "km",
        include_origin: bool = False,
        origin_country: str | None = None,
    ) -> tuple[PlaceDistance, ...]:
        """Return the places nearest to an origin, nearest first.

        The origin can be a city name, any place or country model, a
        :class:`Coordinate`, or a ``(latitude, longitude)`` tuple. Filter with
        ``kind`` or ``category`` (``category="water"`` finds the nearest lakes
        and rivers). Distances are great-circle surface measurements in
        ``"km"``, ``"mi"``, or ``"nmi"``.
        """
        if isinstance(limit, bool) or not isinstance(limit, int) or limit <= 0:
            raise ValueError("limit must be a positive integer")
        if unit not in {"km", "mi", "nmi"}:
            raise ValueError('unit must be "km", "mi", or "nmi"')
        start = self._coordinates_of(origin, country=origin_country)
        where, params = self._place_filter(kind, category, None)
        factor = {"km": 1.0, "mi": 0.621371192237334, "nmi": 0.539956803455724}[unit]
        found = _placefile.near(self._places(), start.latitude, start.longitude, limit + 1, where, params)
        result: list[PlaceDistance] = []
        for distance, row in found:
            if not include_origin and distance <= 1e-6:
                continue
            result.append(PlaceDistance(self._place_from_row(row), distance * factor, unit))
            if len(result) == limit:
                break
        return tuple(result)

    def _city_positions(self) -> list[tuple[sqlite3.Row, float, float, float]]:
        """Load every populated place once, with radians precomputed for distances."""
        if self._city_cache is None:
            self._ensure_open()
            rows = self._db.connection.execute(
                """SELECT c.*, co.alpha2, co.name AS country_name FROM city c
                   JOIN country co ON co.id = c.country_id"""
            ).fetchall()
            self._city_cache = []
            for row in rows:
                latitude = radians(row["latitude"])
                self._city_cache.append(
                    (row, latitude, radians(row["longitude"]), cos(latitude))
                )
        return self._city_cache

    def _statistics_pack(self) -> Statistics:
        """Load the statistics pack once, or explain how to install it."""
        self._ensure_open()
        if self._statistics is None:
            from ._statistics import FILE, Statistics

            folder = packs.pack_path("statistics", self._data_dir)
            if folder is None or not (folder / FILE).is_file():
                raise PackNotInstalledError(
                    "Statistics need the statistics pack. Run: pyworldatlas get statistics"
                )
            self._statistics = Statistics(folder / FILE)
        return self._statistics

    def indicators(self) -> tuple[Indicator, ...]:
        """Return every statistic in the statistics pack, such as ``life_expectancy``.

        Needs the statistics pack (``pyworldatlas get statistics``).
        """
        return tuple(self._statistics_pack().indicators.values())

    def _indicator(self, key: str) -> Indicator:
        found = self._statistics_pack().indicators.get(str(key).strip().casefold().replace(" ", "_").replace("-", "_"))
        if found is None:
            choices = ", ".join(self._statistics_pack().indicators)
            raise ValueError(f"Unknown indicator {key!r}; choose from {choices}")
        return found

    def time_series(self, country: str | Country, indicator: str) -> StatisticSeries:
        """Return the yearly values of an indicator for a country, from 1960.

        ``country`` is a country name, code, or profile, or ``"world"`` for the
        World Bank's world total. Years without a published value are ``None``.
        Needs the statistics pack (``pyworldatlas get statistics``).
        """
        found = self._indicator(indicator)
        if isinstance(country, str) and country.strip().casefold() == "world":
            area, area_name = "world", "the world"
        else:
            profile = country if isinstance(country, Country) else self.country(country)
            area, area_name = profile.alpha2, profile.name
        first, values = self._statistics_pack().series[found.key].get(area, (0, ()))
        return StatisticSeries(found, area, area_name, first, values)

    def statistic(self, country: str | Country, indicator: str, year: int | None = None) -> StatisticValue | None:
        """Return one published value, the latest unless ``year`` is given.

        Returns ``None`` when the publisher has no value; missing values are
        never estimated. Needs the statistics pack.
        """
        series = self.time_series(country, indicator)
        if year is None:
            return series.latest
        value = series.value(year)
        return None if value is None else StatisticValue(series.indicator, series.area, year, value)

    def sort_by_statistic(
        self, indicator: str, *, year: int | None = None, descending: bool = True, limit: int | None = 10
    ) -> tuple[StatisticValue, ...]:
        """List countries sorted by one indicator, for a year or each one's latest.

        Sorting only orders the published numbers; it says nothing about which
        is better. Countries without a value are left out. Needs the
        statistics pack.
        """
        found = self._indicator(indicator)
        if limit is not None and (isinstance(limit, bool) or not isinstance(limit, int) or limit <= 0):
            raise ValueError("limit must be a positive integer or None")
        rows: list[StatisticValue] = []
        for area, (first, values) in self._statistics_pack().series[found.key].items():
            if area == "world":
                continue
            series = StatisticSeries(found, area, area, first, values)
            item = series.latest if year is None else (
                None if series.value(year) is None else StatisticValue(found, area, year, series.value(year) or 0.0)
            )
            if item is not None:
                rows.append(item)
        rows.sort(key=lambda item: (-item.value if descending else item.value, item.area))
        return tuple(rows if limit is None else rows[:limit])

    def _landmark_pack(self) -> Landmarks:
        """Load the landmarks pack once, or explain how to install it."""
        self._ensure_open()
        if self._landmarks is None:
            from ._landmarks import FILE, Landmarks

            folder = packs.pack_path("landmarks", self._data_dir)
            if folder is None or not (folder / FILE).is_file():
                raise PackNotInstalledError(
                    "Airports and World Heritage sites need the landmarks pack. "
                    "Run: pyworldatlas get landmarks"
                )
            self._landmarks = Landmarks(folder / FILE)
        return self._landmarks

    def airport(self, code: str) -> Airport:
        """Return the airport with this IATA (``"LHR"``) or ICAO (``"EGLL"``) code.

        Needs the landmarks pack (``pyworldatlas get landmarks``). Raises
        :class:`PlaceNotFoundError` for an unknown code.
        """
        if not isinstance(code, str):
            raise TypeError("code must be a string")
        found = self._landmark_pack().by_code.get(code.strip().upper())
        if found is None:
            raise PlaceNotFoundError(f"No airport with scheduled flights has the code {code!r}")
        return found

    def airports(
        self, country: str | Country | None = None, *, size: str | None = None
    ) -> tuple[Airport, ...]:
        """Return airports with scheduled flights, largest first, then by name.

        Narrow with ``country`` and ``size`` (``"large"``, ``"medium"``, or
        ``"small"``). Needs the landmarks pack (``pyworldatlas get landmarks``).
        """
        if size is not None and size not in {"large", "medium", "small"}:
            raise ValueError("size must be 'large', 'medium', or 'small'")
        found = self._landmark_pack().airports
        if country is not None:
            code = (country if isinstance(country, Country) else self.country(country)).alpha2
            found = tuple(airport for airport in found if airport.country_code == code)
        if size is not None:
            found = tuple(airport for airport in found if airport.size == size)
        order = {"large": 0, "medium": 1, "small": 2}
        return tuple(sorted(found, key=lambda airport: (order[airport.size], airport.name.casefold())))

    def world_heritage_sites(self, *, category: str | None = None) -> tuple[WorldHeritageSite, ...]:
        """Return UNESCO World Heritage sites in list order.

        Narrow with ``category`` (``"cultural"``, ``"natural"``, or ``"mixed"``).
        Use :meth:`world_heritage_sites_near` to find the sites around a place.
        Needs the landmarks pack (``pyworldatlas get landmarks``).
        """
        if category is not None and category not in {"cultural", "natural", "mixed"}:
            raise ValueError("category must be 'cultural', 'natural', or 'mixed'")
        found = self._landmark_pack().world_heritage
        if category is not None:
            found = tuple(site for site in found if site.category == category)
        return found

    def world_heritage_sites_near(
        self,
        origin: str | Country | Capital | City | Place | Coordinate | tuple[float, float],
        *,
        limit: int = 10,
        category: str | None = None,
        unit: str = "km",
    ) -> tuple[SiteDistance, ...]:
        """Return the World Heritage sites nearest to a place, nearest first.

        ``origin`` is a city or place name, a country (its capital), a model
        with coordinates, or a ``(latitude, longitude)`` tuple. ``unit`` is
        ``"km"`` or ``"mi"``. Needs the landmarks pack.
        """
        if isinstance(limit, bool) or not isinstance(limit, int) or limit <= 0:
            raise ValueError("limit must be a positive integer")
        if unit not in {"km", "mi"}:
            raise ValueError("unit must be 'km' or 'mi'")
        point = self._point_of(origin)
        scale = 1.0 if unit == "km" else 1 / 1.609344
        ranked = sorted(
            (
                (_placefile.distance_km(point.latitude, point.longitude,
                                        site.coordinates.latitude, site.coordinates.longitude), site.site_id, site)
                for site in self.world_heritage_sites(category=category)
                if site.coordinates is not None
            ),
            key=lambda item: (item[0], item[1]),
        )
        return tuple(SiteDistance(site, round(km * scale, 3), unit) for km, _, site in ranked[:limit])

    def world_heritage_site(self, query: str | int) -> WorldHeritageSite:
        """Return one World Heritage site by list number or name.

        Names match without regard to case or accents: an exact name first,
        then the one site whose name contains the query. Raises
        :class:`PlaceNotFoundError` or :class:`AmbiguousPlaceError`.
        """
        sites = self._landmark_pack().world_heritage
        if isinstance(query, int) and not isinstance(query, bool):
            for site in sites:
                if site.site_id == query:
                    return site
            raise PlaceNotFoundError(f"No World Heritage site has the list number {query}")
        if not isinstance(query, str):
            raise TypeError("query must be a name or a list number")
        key = normalize_name(query)
        if not key:
            raise ValueError("query must contain at least one letter or number")
        exact = [site for site in sites if normalize_name(site.name) == key]
        matches = exact or [site for site in sites if key in normalize_name(site.name)]
        if not matches:
            raise PlaceNotFoundError(f"No World Heritage site is named {query!r}")
        if len(matches) > 1:
            names = "; ".join(site.name for site in matches[:5])
            raise AmbiguousPlaceError(f"{query!r} matches several World Heritage sites: {names}")
        return matches[0]

    def sun(
        self,
        where: str | Country | Capital | City | Place | Coordinate | tuple[float, float],
        on: date | None = None,
    ) -> SunTimes:
        """Return sunrise, sunset, day length, and the noon sun height for a place.

        ``where`` is a city or place name, a country (its capital), a model with
        coordinates, or a ``(latitude, longitude)`` tuple. ``on`` defaults to
        today. Times are in UTC and agree with almanac times to about a minute
        between latitudes 72° north and south. Compare ``atlas.sun("Oslo",
        date(2026, 6, 21))`` with December to see why seasons happen.
        """
        point = self._point_of(where)
        day = on if on is not None else date.today()
        if not isinstance(day, date):
            raise TypeError("on must be a datetime.date")
        if isinstance(day, datetime):
            day = day.date()
        noon, sunrise, sunset, hours, height = sun_times(point.latitude, point.longitude, day)
        return SunTimes(point, day, noon, sunrise, sunset, round(hours, 4), round(height, 2))

    PLACE_QUIZ_TOPICS = ("closer_to_equator", "higher", "kinds")
    """Topics accepted by :meth:`place_quiz`."""

    _QUIZ_KINDS = (
        "atoll", "bay", "cape", "desert", "glacier", "gulf", "island", "lake", "mountain",
        "mountain range", "ocean", "peninsula", "plateau", "river", "sea", "strait", "valley",
        "volcano", "waterfall",
    )

    def place_quiz(self, topic: str, *, count: int = 5, seed: int | str = 0) -> tuple[PlaceQuestion, ...]:
        """Return multiple-choice questions about famous natural places.

        Topics are ``"kinds"`` (what kind of place is it?), ``"higher"`` (which
        of two mountains is higher?), and ``"closer_to_equator"`` (which of two
        places is closer to the equator?). Questions come from the best-known
        mountains, islands, lakes, rivers, and seas in the school atlas, and the
        same ``seed`` always gives the same questions.
        """
        if topic not in self.PLACE_QUIZ_TOPICS:
            raise ValueError(f"topic must be one of {', '.join(self.PLACE_QUIZ_TOPICS)}")
        if isinstance(count, bool) or not isinstance(count, int) or not 1 <= count <= 50:
            raise ValueError("count must be an integer from 1 through 50")
        from hashlib import sha256

        # The best-known natural places, with a plain English name.
        rows = self._places()[0].execute(
            "SELECT * FROM place WHERE substr(code, 1, 1) IN ('T', 'H', 'V') ORDER BY fame DESC, id LIMIT 300"
        ).fetchall()
        pool = [
            place for place in map(self._place_from_row, rows)
            if place.english_name.isascii() and "," not in place.english_name
        ]

        def shuffled(items: list[Place], salt: str) -> list[Place]:
            def rank(place: Place) -> bytes:
                key = f"pyworldatlas:place-quiz:{topic}:{seed}:{salt}:{place.english_name}:{place.coordinates}"
                return sha256(key.encode()).digest()
            return sorted(items, key=rank)

        questions: list[PlaceQuestion] = []
        if topic == "kinds":
            kinds = [place for place in pool if place.kind in self._QUIZ_KINDS]
            for place in shuffled(kinds, "pick")[:count]:
                others = [kind for kind in self._QUIZ_KINDS if kind != place.kind]
                wrong = stable_text_order(tuple(others), seed=seed, namespace=f"place-kinds:{place.english_name}")[:3]
                choices = stable_text_order((place.kind, *wrong), seed=seed, namespace=f"place-order:{place.english_name}")
                questions.append(PlaceQuestion(topic, f"What kind of place is {place.english_name}?", choices, place.kind, (place,)))
        else:
            if topic == "higher":
                candidates = [p for p in pool if p.kind in {"mountain", "volcano", "peak"} and p.elevation_m]
            else:  # compact places only: an ocean or a mountain range has no single latitude
                compact = {"mountain", "volcano", "peak", "island", "atoll", "lake", "waterfall"}
                candidates = [p for p in pool if p.kind in compact]
            order = shuffled(candidates, "pick")
            for first, second in zip(order[0::2], order[1::2], strict=False):
                if len(questions) == count:
                    break
                if first.english_name == second.english_name:
                    continue
                if topic == "higher":
                    assert first.elevation_m is not None and second.elevation_m is not None
                    if first.elevation_m == second.elevation_m:
                        continue
                    winner = first if first.elevation_m > second.elevation_m else second
                    prompt = f"Which is higher: {first.english_name} or {second.english_name}?"
                else:
                    a, b = abs(first.coordinates.latitude), abs(second.coordinates.latitude)
                    if abs(a - b) < 1:
                        continue
                    winner = first if a < b else second
                    prompt = f"Which is closer to the equator: {first.english_name} or {second.english_name}?"
                questions.append(PlaceQuestion(
                    topic, prompt, (first.english_name, second.english_name), winner.english_name, (first, second)
                ))
        if len(questions) < count:
            raise ValueError(f"only {len(questions)} {topic!r} questions are available")
        return tuple(questions)

    def antipode(
        self,
        where: str | Country | Capital | City | Place | Coordinate | tuple[float, float],
        *,
        limit: int = 3,
    ) -> Antipode:
        """Return the point on the opposite side of the Earth, and the places nearest it.

        Dig straight down through the centre of the Earth and you come out at
        the antipode: the latitude flips north and south, and the longitude
        moves halfway around the world. ``where`` is a city or place name, a
        country (its capital), a model with coordinates, or a ``(latitude,
        longitude)`` tuple. Most antipodes are at sea.
        """
        point = self._point_of(where)
        longitude = point.longitude + 180 if point.longitude <= 0 else point.longitude - 180
        opposite = Coordinate(round(-point.latitude, 6), round(longitude, 6))
        return Antipode(point, opposite, self.places_near(opposite, limit=limit))

    def _point_of(
        self, where: str | Country | Capital | City | Place | Coordinate | tuple[float, float]
    ) -> Coordinate:
        """Resolve a place-like value; a name that is not one city is looked up as a place."""
        if isinstance(where, str):
            try:
                return self._coordinates_of(where, country=None)
            except (PlaceNotFoundError, AmbiguousPlaceError):
                return self.place(where).coordinates
        return self._coordinates_of(where, country=None)

    def _coordinates_of(
        self,
        value: str | Country | Capital | City | Place | Coordinate | tuple[float, float],
        *,
        country: str | None,
    ) -> Coordinate:
        if isinstance(value, Coordinate):
            return value
        if isinstance(value, (Capital, City, Place)):
            return value.coordinates
        if isinstance(value, Country):
            if value.capital_coordinates is None:
                raise CapitalNotFoundError(f"{value.name} has no primary-capital coordinates")
            return value.capital_coordinates
        if isinstance(value, str):
            return self.coordinates(value, country=country)
        if isinstance(value, tuple) and len(value) == 2:
            return Coordinate(float(value[0]), float(value[1]))
        raise TypeError("place must be a city name, country or place model, Coordinate, or (latitude, longitude) tuple")

    @staticmethod
    def _city_from_row(row: sqlite3.Row) -> City:
        return city_from_row(row)

    def _load_countries(self, country_ids: Iterable[int]) -> tuple[Country, ...]:
        """Return several country models, reading missing ones in bulk."""
        ids = tuple(country_ids)
        missing = [item for item in ids if item not in self._country_cache]
        if len(missing) > 1:
            self._bulk_rows = {}
            try:
                for item in missing:
                    self._load_country(item)
            finally:
                self._bulk_rows = None
        return tuple(self._load_country(item) for item in ids)

    def _child_rows(self, sql: str, country_id: int) -> list[sqlite3.Row]:
        """Run one per-country query, or serve it from a bulk read of all countries."""
        if self._bulk_rows is None:
            return self._db.connection.execute(sql, (country_id,)).fetchall()
        grouped = self._bulk_rows.get(sql)
        if grouped is None:
            grouped = self._bulk_rows[sql] = {}
            bulk_sql = sql.replace("country_id=?", "country_id IS NOT NULL")
            for row in self._db.connection.execute(bulk_sql):
                grouped.setdefault(int(row["country_id"]), []).append(row)
        return grouped.get(country_id, [])

    def _load_country(self, country_id: int) -> Country:
        """Return one immutable country model, reading it at most once per atlas."""
        country = self._country_cache.get(country_id)
        if country is None:
            country = self._country_cache[country_id] = self._read_country(country_id)
        return country

    def _read_country(self, country_id: int) -> Country:
        row = self._db.connection.execute("SELECT * FROM country WHERE id=?", (country_id,)).fetchone()
        return build_country(
            row,
            lambda sql: self._child_rows(sql, country_id),
            self._load_local_names().get(country_id, ()),
        )

    def _load_local_names(self) -> dict[int, tuple[LocalizedName, ...]]:
        """Load local names once so collection iteration never creates an N+1 query."""
        if self._local_names_cache is None:
            self._local_names_cache = self._read_local_names()
        return self._local_names_cache

    def _read_local_names(self) -> dict[int, tuple[LocalizedName, ...]]:
        return read_local_names(self._db.connection)

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
        """Close the read-only database connection.

        Calling ``close()`` more than once is safe. Queries on a closed atlas
        raise :class:`AtlasClosedError`; models returned earlier remain usable.
        """
        if not self._closed:
            self._db.close()
            self._closed = True
            self._country_cache.clear()
            self._local_names_cache = None
            self._border_cache = None
            self._query_cache.clear()
            self._code_cache = None
            self._city_cache = None
            for index in self._place_indexes or ():
                index.close()
            self._place_indexes = None

    def __enter__(self) -> Atlas:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
