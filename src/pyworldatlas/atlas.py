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
from .models import (Area, BorderPathResult, Capital, City, Coordinate, Country,
                     CountryCodes, CountryMatch, CountryStatus, Currency,
                     DatasetInfo, Flashcard, Geography, Language, LocalizedName,
                     SourceReference)


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


_FLASHCARD_TOPICS = (
    "alpha_2_codes",
    "alpha_3_codes",
    "areas",
    "border_counts",
    "calling_codes",
    "capitals",
    "continents",
    "countries_from_capitals",
    "currencies",
    "flags",
    "language_codes",
    "local_names",
    "m49_codes",
    "neighbors",
    "population_density",
    "populations",
    "regions",
    "top_level_domains",
)


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
        ``border_counts``, ``calling_codes``, ``capitals``, ``continents``,
        ``countries_from_capitals``, ``currencies``, ``flags``,
        ``language_codes``, ``local_names``, ``m49_codes``, ``neighbors``,
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

    def _has_flashcard_answer(self, country: Country, topic: str) -> bool:
        if topic in {"capitals", "countries_from_capitals"}:
            return country.capital is not None
        if topic == "alpha_3_codes":
            return country.alpha3 is not None
        if topic == "areas":
            return country.area_km2 is not None
        if topic == "calling_codes":
            return bool(country.calling_codes)
        if topic == "continents":
            return country.continent is not None
        if topic == "currencies":
            return country.currency is not None
        if topic == "flags":
            return country.flag_emoji is not None
        if topic == "language_codes":
            return bool(country.language_codes)
        if topic == "local_names":
            return bool(country.local_names)
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
        """Return major cities for a country, ordered by population and name."""
        result = self.country(country).major_cities
        return result if limit is None else result[:limit]

    def city(self, query: str, *, country: str | None = None) -> City:
        """Resolve an exact city name, optionally constrained to a country."""
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
        """Return coordinates for an exact city lookup."""
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

        String inputs are exact bundled-city names. Pass :class:`Country`
        objects for capital-to-capital country distance.
        """
        start = self._coordinates_of(first, country=first_country)
        finish = self._coordinates_of(second, country=second_country)
        return start.distance_to(finish, unit=unit)

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
        sources = tuple(SourceReference(s["id"], s["name"], s["homepage"], s["retrieved_at"]) for s in source_rows)
        local_names = self._load_local_names().get(country_id, ())
        geography = Geography(row["continent"], row["region"], row["subregion"], Area(row["total_area_km2"]))
        currency = Currency(row["currency_code"], row["currency_name"]) if row["currency_code"] else None
        languages = tuple(Language(code) for code in json.loads(row["language_codes"]))
        calling_codes = tuple(json.loads(row["calling_codes"]))
        observed_timezones = tuple(sorted({city.timezone_id for city in cities if city.timezone_id}))
        formal_name = next((name.text for name in names if name.kind == "formal"), None)
        return Country(row["name"], row["official_name"], names, aliases, CountryCodes(row["alpha2"], row["alpha3"], row["numeric_code"], None, row["geonames_id"]), _flag(row["alpha2"]), CountryStatus(row["status"]), geography, capitals, cities, sources, local_names, row["population"], currency, languages, calling_codes, row["top_level_domain"], observed_timezones, formal_name)

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
        """Close the atlas connection."""
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
