"""Primary offline atlas interface."""

from __future__ import annotations

from collections import deque
from functools import lru_cache
from hashlib import sha256
import json
from pathlib import Path
from typing import Iterator

from ._normalization import normalize_name
from ._version import SCHEMA_VERSION, __version__
from .database import Database
from .exceptions import (AmbiguousPlaceError, AtlasClosedError, CapitalNotFoundError,
                         CountryNotFoundError, DatasetVersionError, PlaceNotFoundError)
from .models import (Area, BorderPathResult, Capital, CapitalDistance, City,
                     CityDistance, ClimateProfile, ClimateZone, Coordinate, Country,
                     CountryCodes, CountryMatch, CountryRanking, Currency,
                     DatasetInfo, Demonym, ElevationPoint, Flashcard, Geography,
                     Lake, Language, LocalizedName, NationalAnthem,
                     NationalMotto, PhysicalGeography, PostalCodeFormat, QuizQuestion, River,
                     SourceReference, Timezone)


def _flag(alpha2: str) -> str:
    return "".join(chr(0x1F1E6 + ord(letter) - ord("A")) for letter in alpha2)


def _stable_country_sample(
    candidates: tuple[Country, ...], count: int, seed: int | str
) -> tuple[Country, ...]:
    """Select countries by a versioned SHA-256 ranking, independent of row order."""
    if isinstance(count, bool) or not isinstance(count, int) or count <= 0:
        raise ValueError("count must be a positive integer")
    if count > len(candidates):
        raise ValueError(f"count {count} exceeds the {len(candidates)} available countries")

    def rank(country: Country) -> tuple[bytes, str]:
        identifier = country.codes.numeric or country.alpha3 or country.alpha2
        payload = f"pyworldatlas:0.2:{seed}:{identifier}".encode("utf-8")
        return sha256(payload).digest(), identifier

    return tuple(sorted(candidates, key=rank)[:count])


def _stable_text_order(
    values: tuple[str, ...], *, seed: int | str, namespace: str
) -> tuple[str, ...]:
    """Order text deterministically without depending on global random state."""

    def rank(value: str) -> tuple[bytes, str]:
        payload = f"pyworldatlas:0.8:{namespace}:{seed}:{value}".encode("utf-8")
        return sha256(payload).digest(), value

    return tuple(sorted(values, key=rank))


_FLASHCARD_TOPICS = (
    "alpha_2_codes",
    "alpha_3_codes",
    "areas",
    "border_counts",
    "calling_codes",
    "capitals",
    "climate_zones",
    "coastlines",
    "continents",
    "countries_from_capitals",
    "currencies",
    "flags",
    "highest_points",
    "language_codes",
    "local_names",
    "lakes",
    "m49_codes",
    "neighbors",
    "population_density",
    "populations",
    "regions",
    "rivers",
    "top_level_domains",
)


class Atlas:
    """Open and explore the bundled, read-only world atlas.

    With no arguments, :class:`Atlas` uses the SQLite dataset shipped inside
    the package. Pass ``database_path`` only when working with a compatible
    database built by the PyWorldAtlas pipeline. A context manager closes the
    database promptly; already materialized immutable models remain usable.
    Runtime lookups and calculations require no network access.
    """

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
        """Return the installed library, database schema, and dataset versions.

        Record these values when a lesson or calculation must be reproducible.
        """
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
        """Return one country profile resolved from a name or standard code.

        ``query`` may be a familiar English name, indexed alias, alpha-2 code,
        alpha-3 code, or three-digit M49 code. Matching is case-insensitive and
        accent-tolerant. A missing or non-unique query raises
        :class:`CountryNotFoundError`, with suggestions when available.
        """
        self._ensure_open()
        country_id = self._country_id(query)
        if country_id is None:
            suggestions = ", ".join(match.country.name for match in self.search_countries(query, limit=3))
            hint = f" Try: {suggestions}." if suggestions else ""
            raise CountryNotFoundError(f"No unambiguous country matches {query!r}.{hint}")
        return self._load_country(country_id)

    def get(self, query: str, default: Country | None = None) -> Country | None:
        """Return a matching country, or ``default`` instead of raising.

        Use :meth:`country` when a missing profile should be treated as an
        error. ``default`` is returned for both missing and non-unique queries.
        """
        try:
            return self.country(query)
        except CountryNotFoundError:
            return default

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
        return tuple(self._load_country(int(row[0])) for row in rows)

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
        ``"water_percent"``, ``"coastline"`, ``"mean_elevation"``,
        ``"highest_elevation"``, ``"lowest_elevation"`, ``"river_count"``,
        ``"lake_count"``, and ``"climate_zone_count"``. Existing population,
        total area, density, border, and city metrics remain available. Missing
        values are excluded.
        """
        aliases = {
            "area_km2": "area",
            "density": "population_density",
            "land_area_km2": "land_area",
            "water_area_km2": "water_area",
            "coastline_km": "coastline",
            "mean_elevation_m": "mean_elevation",
            "highest_point": "highest_elevation",
            "lowest_point": "lowest_elevation",
        }
        normalized_metric = aliases.get(metric.casefold(), metric.casefold())
        units = {
            "population": "people",
            "area": "km²",
            "population_density": "people/km²",
            "border_count": "countries",
            "major_city_count": "places",
            "land_area": "km²",
            "water_area": "km²",
            "water_percent": "%",
            "coastline": "km",
            "mean_elevation": "m",
            "highest_elevation": "m",
            "lowest_elevation": "m",
            "river_count": "rivers",
            "lake_count": "lakes",
            "climate_zone_count": "classes",
        }
        if normalized_metric not in units:
            raise ValueError(
                "metric must be a documented population, area, border, city, "
                "coastline, elevation, physical-feature, or climate-zone metric"
            )
        if limit is not None and (
            isinstance(limit, bool) or not isinstance(limit, int) or limit <= 0
        ):
            raise ValueError("limit must be a positive integer or None")

        ranked: list[tuple[Country, int | float]] = []
        for country in self.countries(continent=continent, region=region):
            if normalized_metric == "population":
                value = country.population
            elif normalized_metric == "area":
                value = country.area_km2
            elif normalized_metric == "population_density":
                value = country.population_density
            elif normalized_metric == "border_count":
                value = len(self.neighbors(country.alpha2))
            elif normalized_metric == "major_city_count":
                value = country.major_city_count
            elif normalized_metric == "land_area":
                value = country.land_area_km2
            elif normalized_metric == "water_area":
                value = country.water_area_km2
            elif normalized_metric == "water_percent":
                value = country.water_percent
            elif normalized_metric == "coastline":
                value = country.coastline_km
            elif normalized_metric == "mean_elevation":
                value = country.mean_elevation_m
            elif normalized_metric == "highest_elevation":
                value = (
                    country.highest_point.elevation_m if country.highest_point else None
                )
            elif normalized_metric == "lowest_elevation":
                value = country.lowest_point.elevation_m if country.lowest_point else None
            elif normalized_metric == "river_count":
                value = len(country.rivers) if country.rivers else None
            elif normalized_metric == "lake_count":
                value = len(country.lakes) if country.lakes else None
            else:
                value = (
                    len(country.climate.koppen_geiger_zones)
                    if country.climate.koppen_geiger_zones
                    else None
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
            CountryRanking(position, country.reference(), normalized_metric, value, units[normalized_metric])
            for position, (country, value) in enumerate(ranked, 1)
        )

    def rank(self, metric: str, **kwargs: object) -> tuple[CountryRanking, ...]:
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
        return tuple(self._load_country(int(row[0])) for row in rows)

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
        return tuple(self._load_country(int(row[0])) for row in rows)

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
        return tuple(self._load_country(int(row[0])) for row in rows)

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
        return tuple(self._load_country(int(row[0])) for row in rows)

    @lru_cache(maxsize=1)
    def _border_adjacency(self) -> dict[int, tuple[int, ...]]:
        """Load the undirected border graph once for graph operations."""
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
        while parents[path[-1]] is not None:
            path.append(parents[path[-1]])
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
        return _stable_country_sample(
            self.countries(continent=continent, region=region), count, seed
        )

    def learning_topics(self) -> tuple[str, ...]:
        """Return topics supported by :meth:`flashcards` and :meth:`quiz`.

        The tuple is stable, alphabetized, and safe to use for menus, lesson
        builders, or playground controls.
        """
        self._ensure_open()
        return _FLASHCARD_TOPICS

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
        ``countries_from_capitals``, ``currencies``, ``flags``,
        ``highest_points``, ``language_codes``, ``lakes``, ``local_names``,
        ``m49_codes``, ``neighbors``, ``rivers``,
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
        if topic not in _FLASHCARD_TOPICS:
            allowed = ", ".join(_FLASHCARD_TOPICS)
            raise ValueError(f"unsupported flashcard topic {topic!r}; choose from {allowed}")
        candidates = tuple(
            country
            for country in self.countries(continent=continent, region=region)
            if self._has_flashcard_answer(country, topic)
        )
        selected = _stable_country_sample(candidates, count, seed)
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
        if topic not in _FLASHCARD_TOPICS:
            allowed = ", ".join(_FLASHCARD_TOPICS)
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
        selected = _stable_country_sample(candidates, count, seed)
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
            picked = _stable_text_order(
                distractors, seed=seed, namespace=namespace
            )[: choices - 1]
            ordered_choices = _stable_text_order(
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
        if topic in {"capitals", "countries_from_capitals"}:
            return country.capital is not None
        if topic == "alpha_3_codes":
            return country.alpha3 is not None
        if topic == "areas":
            return country.area_km2 is not None
        if topic == "calling_codes":
            return bool(country.calling_codes)
        if topic == "climate_zones":
            return country.climate.dominant_zone is not None
        if topic == "coastlines":
            return country.coastline_km is not None
        if topic == "continents":
            return country.continent is not None
        if topic == "currencies":
            return country.currency is not None
        if topic == "flags":
            return country.flag_emoji is not None
        if topic == "highest_points":
            return country.highest_point is not None
        if topic == "language_codes":
            return bool(country.language_codes)
        if topic == "local_names":
            return bool(country.local_names)
        if topic == "lakes":
            return bool(country.lakes)
        if topic == "m49_codes":
            return country.codes.numeric is not None
        if topic == "neighbors":
            country_id = self._country_id(country.alpha2)
            return country_id is not None and bool(self._border_adjacency()[country_id])
        if topic == "population_density":
            return country.population_density is not None
        if topic == "populations":
            return country.population is not None
        if topic == "regions":
            return country.region is not None
        if topic == "rivers":
            return bool(country.rivers)
        if topic == "top_level_domains":
            return country.top_level_domain is not None
        return True

    def _flashcard(self, country: Country, topic: str) -> Flashcard:
        reference = country.reference()
        if topic == "capitals":
            prompt, answer = f"What is the capital of {country.name}?", country.capital.name
        elif topic == "countries_from_capitals":
            prompt, answer = (
                f"{country.capital.name} is the capital of which country or area?",
                country.name,
            )
        elif topic == "flags":
            prompt, answer = f"Which country or area uses the flag {country.flag_emoji}?", country.name
        elif topic == "alpha_2_codes":
            prompt, answer = f"What is the alpha-2 code for {country.name}?", country.alpha2
        elif topic == "alpha_3_codes":
            prompt, answer = f"What is the alpha-3 code for {country.name}?", country.alpha3
        elif topic == "m49_codes":
            prompt, answer = f"What is the M49 code for {country.name}?", country.codes.numeric
        elif topic == "border_counts":
            prompt = f"How many reviewed land neighbors does {country.name} have?"
            answer = str(len(self.neighbors(country.alpha2)))
        elif topic == "neighbors":
            prompt = f"Which countries or areas share a reviewed land border with {country.name}?"
            answer = ", ".join(neighbor.name for neighbor in self.neighbors(country.alpha2))
        elif topic == "currencies":
            label = country.currency.name or country.currency.code
            answer = f"{label} ({country.currency.code})" if label != country.currency.code else label
            prompt = f"Which currency is listed for {country.name}?"
        elif topic == "calling_codes":
            prompt, answer = f"Which calling code is listed for {country.name}?", ", ".join(country.calling_codes)
        elif topic == "top_level_domains":
            prompt, answer = f"What is the country-code top-level domain for {country.name}?", country.top_level_domain
        elif topic == "language_codes":
            prompt, answer = f"Which language codes are listed for {country.name}?", ", ".join(country.language_codes)
        elif topic == "continents":
            prompt, answer = f"Which continent contains {country.name}?", country.continent
        elif topic == "regions":
            prompt, answer = f"Which UN region contains {country.name}?", country.region
        elif topic == "climate_zones":
            zone = country.climate.dominant_zone
            prompt = (
                f"Which Köppen-Geiger class has the largest represented share "
                f"of {country.name}?"
            )
            answer = f"{zone.code} — {zone.name}"
        elif topic == "coastlines":
            prompt = f"What coastline length is listed for {country.name}?"
            answer = f"{country.coastline_km:g} km"
        elif topic == "highest_points":
            point = country.highest_point
            prompt = f"What is the highest point listed for {country.name}?"
            answer = f"{point.name} ({point.elevation_m:g} m)"
        elif topic == "rivers":
            river = country.rivers[0]
            prompt = f"Name a source-listed major river associated with {country.name}."
            answer = (
                f"{river.name} ({river.length_km:g} km)"
                if river.length_km is not None else river.name
            )
        elif topic == "lakes":
            lake = country.lakes[0]
            prompt = f"Name a source-listed major lake associated with {country.name}."
            answer = (
                f"{lake.name} ({lake.area_km2:g} km²)"
                if lake.area_km2 is not None else lake.name
            )
        elif topic == "local_names":
            local_name = next(
                (name for name in country.local_names if name.language_code != "en"),
                country.local_names[0],
            )
            prompt = f"What is a locally official short name for {country.name} in {local_name.language_name}?"
            answer = local_name.short_name
        elif topic == "areas":
            prompt, answer = f"What area is listed for {country.name}?", f"{country.area_km2:g} km²"
        elif topic == "populations":
            prompt, answer = f"What snapshot population is listed for {country.name}?", f"{country.population:,}"
        else:
            prompt = f"What snapshot population density is calculated for {country.name}?"
            answer = f"{country.population_density:.2f} people per km²"
        return Flashcard(topic, prompt, str(answer), reference)

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

        def rank(row: object) -> tuple[object, ...]:
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

        params: list[object] = []
        where = ""
        if within_country is not None:
            country_id = self._country_id(self.country(within_country).alpha2)
            where = "WHERE c.country_id = ?"
            params.append(country_id)
        rows = self._db.connection.execute(
            f"""SELECT c.*, co.alpha2 FROM city c
                JOIN country co ON co.id = c.country_id
                {where}""",
            params,
        ).fetchall()

        results = []
        for row in rows:
            city = self._city_from_row(row)
            distance = start.distance_to(city.coordinates, unit=unit)
            if not include_origin and distance <= 1e-9:
                continue
            country = self._load_country(int(row["country_id"])).reference()
            results.append(CityDistance(country, city, distance, unit))
        results.sort(
            key=lambda result: (
                result.distance,
                result.country.name,
                result.city.name,
                result.city.geonames_id or 0,
            )
        )
        return tuple(results[:limit])

    def _coordinates_of(
        self,
        value: str | Country | Capital | City | Coordinate | tuple[float, float],
        *,
        country: str | None,
    ) -> Coordinate:
        if isinstance(value, Coordinate):
            return value
        if isinstance(value, (Capital, City)):
            return value.coordinates
        if isinstance(value, Country):
            if value.capital_coordinates is None:
                raise CapitalNotFoundError(f"{value.name} has no primary-capital coordinates")
            return value.capital_coordinates
        if isinstance(value, str):
            return self.coordinates(value, country=country)
        if isinstance(value, tuple) and len(value) == 2:
            return Coordinate(float(value[0]), float(value[1]))
        raise TypeError("place must be a city name, country/place model, Coordinate, or (latitude, longitude) tuple")

    @staticmethod
    def _city_from_row(row: object) -> City:
        return City(row["name"], row["alpha2"], Coordinate(row["latitude"], row["longitude"]), row["population"], row["elevation_m"], row["timezone_id"], ("official",) if row["is_capital"] else (), (), row["geonames_id"])

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
        sources = tuple(
            SourceReference(
                s["id"], s["name"], s["homepage"], s["retrieved_at"],
                s["version"], s["license_name"], s["license_url"], s["notes"],
            )
            for s in source_rows
        )
        source_by_id = {source.id: source for source in sources}
        local_names = self._load_local_names().get(country_id, ())
        physical_row = self._db.connection.execute(
            "SELECT * FROM country_physical WHERE country_id=?", (country_id,)
        ).fetchone()
        river_rows = self._db.connection.execute(
            "SELECT * FROM country_river WHERE country_id=? ORDER BY length_km DESC, name",
            (country_id,),
        ).fetchall()
        lake_rows = self._db.connection.execute(
            "SELECT * FROM country_lake WHERE country_id=? ORDER BY area_km2 DESC, name",
            (country_id,),
        ).fetchall()
        climate_rows = self._db.connection.execute(
            "SELECT * FROM country_climate_zone WHERE country_id=? ORDER BY position",
            (country_id,),
        ).fetchall()
        zones = tuple(
            ClimateZone(
                item["code"], item["name"], item["climate_group"],
                item["share_percent"],
            )
            for item in climate_rows
        )
        climate = ClimateProfile(
            summary=physical_row["climate_summary"] if physical_row else None,
            koppen_geiger_zones=zones,
            reference_period=climate_rows[0]["reference_period"] if climate_rows else None,
            resolution_degrees=climate_rows[0]["resolution_degrees"] if climate_rows else None,
            minimum_share_percent=(
                climate_rows[0]["minimum_share_percent"] if climate_rows else None
            ),
            summary_source=source_by_id.get("cia-world-factbook-2025"),
            classification_source=source_by_id.get("koppen-geiger-1991-2020"),
        )
        highest_point = (
            ElevationPoint(
                physical_row["highest_point_name"],
                physical_row["highest_point_elevation_m"],
                bool(physical_row["highest_point_is_approximate"]),
                physical_row["highest_point_source_label"],
            )
            if physical_row and physical_row["highest_point_name"]
            else None
        )
        lowest_point = (
            ElevationPoint(
                physical_row["lowest_point_name"],
                physical_row["lowest_point_elevation_m"],
                bool(physical_row["lowest_point_is_approximate"]),
                physical_row["lowest_point_source_label"],
            )
            if physical_row and physical_row["lowest_point_name"]
            else None
        )
        physical = PhysicalGeography(
            coastline_km=physical_row["coastline_km"] if physical_row else None,
            mean_elevation_m=(
                physical_row["mean_elevation_m"] if physical_row else None
            ),
            highest_point=highest_point,
            lowest_point=lowest_point,
            rivers=tuple(
                River(item["name"], item["length_km"], item["source_label"])
                for item in river_rows
            ),
            lakes=tuple(
                Lake(
                    item["name"], item["area_km2"], item["water_type"],
                    item["source_label"],
                )
                for item in lake_rows
            ),
            climate=climate,
            source=source_by_id.get("cia-world-factbook-2025"),
            source_locator=physical_row["source_locator"] if physical_row else None,
        )
        land_area = physical_row["land_area_km2"] if physical_row else None
        water_area = physical_row["water_area_km2"] if physical_row else None
        total_area = row["total_area_km2"]
        water_percent = (
            water_area / total_area * 100
            if water_area is not None
            and total_area is not None
            and total_area > 0
            and water_area <= total_area
            else None
        )
        geography = Geography(
            continent=row["continent"],
            region=row["region"],
            subregion=row["subregion"],
            area=Area(total_area, land_area, water_area, water_percent),
            landlocked=physical.is_landlocked,
            physical=physical,
        )
        currency = (
            Currency(
                row["currency_code"], row["currency_name"], row["currency_symbol"],
                row["currency_minor_unit_digits"],
                source_by_id.get("unicode-cldr-48.2-reference"),
            )
            if row["currency_code"] else None
        )
        language_rows = self._db.connection.execute(
            "SELECT * FROM country_language WHERE country_id=? ORDER BY code",
            (country_id,),
        ).fetchall()
        languages = tuple(
            Language(
                item["code"], item["primary_code"], item["name"], item["script_code"],
                source_by_id.get(item["source_id"]),
            )
            for item in language_rows
        )
        calling_codes = tuple(json.loads(row["calling_codes"]))
        observed_timezones = tuple(sorted({city.timezone_id for city in cities if city.timezone_id}))
        timezone_rows = self._db.connection.execute(
            "SELECT * FROM country_timezone WHERE country_id=? ORDER BY timezone_id",
            (country_id,),
        ).fetchall()
        timezones = tuple(
            Timezone(
                item["timezone_id"], item["january_utc_offset_hours"],
                item["july_utc_offset_hours"], item["raw_utc_offset_hours"],
                source_by_id.get(item["source_id"]),
            )
            for item in timezone_rows
        )
        anthem_rows = self._db.connection.execute(
            "SELECT * FROM country_anthem WHERE country_id=? ORDER BY title",
            (country_id,),
        ).fetchall()
        anthems = tuple(
            NationalAnthem(
                item["title"], item["english_title"], source_by_id[item["source_id"]],
                item["source_locator"],
            )
            for item in anthem_rows
        )
        motto_rows = self._db.connection.execute(
            "SELECT * FROM country_motto WHERE country_id=? ORDER BY text",
            (country_id,),
        ).fetchall()
        mottos = tuple(
            NationalMotto(
                item["text"], item["language_code"], item["english_text"],
                source_by_id[item["source_id"]], item["source_locator"],
            )
            for item in motto_rows
        )
        demonym_rows = self._db.connection.execute(
            "SELECT * FROM country_demonym WHERE country_id=? ORDER BY language_code",
            (country_id,),
        ).fetchall()
        demonyms = tuple(
            Demonym(
                item["noun"], item["adjective"], item["language_code"],
                source_by_id[item["source_id"]], item["source_locator"],
            )
            for item in demonym_rows
        )
        postal_code = (
            PostalCodeFormat(
                row["postal_code_format"], row["postal_code_regex"],
                source_by_id.get("geonames"),
            )
            if row["postal_code_format"] else None
        )
        formal_name = next((name.text for name in names if name.kind == "formal"), None)
        return Country(
            name=row["name"],
            official_name=row["official_name"],
            names=names,
            aliases=aliases,
            codes=CountryCodes(row["alpha2"], row["alpha3"], row["numeric_code"], None, row["geonames_id"]),
            flag=_flag(row["alpha2"]),
            geography=geography,
            capitals=capitals,
            major_cities=cities,
            sources=sources,
            local_names=local_names,
            population=row["population"],
            currency=currency,
            languages=languages,
            calling_codes=calling_codes,
            top_level_domain=row["top_level_domain"],
            observed_timezones=observed_timezones,
            formal_name=formal_name,
            anthems=anthems,
            mottos=mottos,
            demonyms=demonyms,
            timezones=timezones,
            postal_code=postal_code,
        )

    @lru_cache(maxsize=1)
    def _load_local_names(self) -> dict[int, tuple[LocalizedName, ...]]:
        """Load local names once so collection iteration never creates an N+1 query."""
        rows = self._db.connection.execute(
            """SELECT n.*, s.name AS source_name, s.homepage, s.retrieved_at
               FROM country_local_name n JOIN source s ON s.id=n.source_id
               ORDER BY n.country_id, n.language_code"""
        ).fetchall()
        grouped: dict[int, list[LocalizedName]] = {}
        for row in rows:
            source = SourceReference(row["source_id"], row["source_name"], row["homepage"], row["retrieved_at"])
            grouped.setdefault(int(row["country_id"]), []).append(
                LocalizedName(
                    text=row["short_name"],
                    language_code=row["language_code"],
                    kind=row["name_kind"],
                    preferred=True,
                    language_name=row["language_name"],
                    script_code=row["script_code"],
                    official_name=row["official_name"],
                    romanized_short_name=row["romanized_short_name"],
                    romanized_official_name=row["romanized_official_name"],
                    is_official_language=bool(row["is_official_language"]),
                    source=source,
                    source_locator=row["source_locator"],
                    language_status=row["language_status"],
                )
            )
        return {country_id: tuple(names) for country_id, names in grouped.items()}

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
            self._load_country.cache_clear()
            self._load_local_names.cache_clear()
            self._border_adjacency.cache_clear()

    def __enter__(self) -> "Atlas":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
