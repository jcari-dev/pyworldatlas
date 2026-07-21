"""Deterministic PyWorldAtlas data pipeline."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from hashlib import sha256
from html.parser import HTMLParser
import csv
import json
import os
from pathlib import Path
import re
import sqlite3
import struct
import zipfile


EXPECTED_COUNTRY_COUNT = 248
EXPECTED_CAPITAL_COUNT = 241
EXPECTED_CITY_COUNT = 6_265
EXPECTED_LOCAL_NAME_COUNT = 5
EXPECTED_NATURAL_EARTH_BORDER_COUNT = 317
EXPECTED_GEONAMES_BORDER_COUNT = 319
EXPECTED_BORDER_COUNT = 319
CONTINENTS = {"002": "Africa", "019": "Americas", "142": "Asia", "150": "Europe", "009": "Oceania"}


def normalize_name(value: str) -> str:
    import unicodedata
    plain = "".join(ch for ch in unicodedata.normalize("NFKD", value) if not unicodedata.combining(ch))
    return " ".join("".join(ch if ch.isalnum() else " " for ch in plain.casefold()).split())


class M49Parser(HTMLParser):
    """Extract table cells from the official UN M49 overview page."""

    def __init__(self) -> None:
        super().__init__()
        self.rows: list[list[str]] = []
        self._row: list[str] | None = None
        self._cell: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "tr":
            self._row = []
        elif tag == "td" and self._row is not None:
            self._cell = []

    def handle_data(self, data: str) -> None:
        if self._cell is not None:
            self._cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "td" and self._row is not None and self._cell is not None:
            self._row.append(" ".join("".join(self._cell).split()))
            self._cell = None
        elif tag == "tr" and self._row is not None:
            if len(self._row) >= 12:
                self.rows.append(self._row)
            self._row = None


def _load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _project_version(root: Path) -> str:
    text = (root / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', text, flags=re.MULTILINE)
    if match is None:
        raise ValueError("Could not read library version from pyproject.toml")
    return match.group(1)


def write_manifests(root: Path) -> None:
    """Write raw-snapshot manifests without altering source files."""
    specs = {
        "un-m49": ("2026-07-20", "2026-07-20T00:00:00Z", [
            ("overview.html", "https://unstats.un.org/unsd/methodology/m49/overview/"),
        ]),
        "geonames": ("2026-07-20", "2026-07-20T00:00:00Z", [
            ("countryInfo.txt", "https://download.geonames.org/export/dump/countryInfo.txt"),
            ("cities15000.zip", "https://download.geonames.org/export/dump/cities15000.zip"),
        ]),
        "ungegn-country-names": ("2017-07-17", "2026-07-20T00:00:00Z", [(
                "E_CONF.105_13_CRP.13-EN.pdf",
                "https://unstats.un.org/unsd/geoinfo/ungegn/docs/11th-uncsgn-docs/"
                "E_Conf.105_13_CRP.13_15_UNGEGN%20WG%20Country%20Names%20Document.pdf",
        )]),
        "natural-earth": ("2026-07-21", "2026-07-21T00:00:00Z", [
            (
                "ne_50m_admin_0_boundary_lines_land.zip",
                "https://naturalearth.s3.amazonaws.com/50m_cultural/"
                "ne_50m_admin_0_boundary_lines_land.zip",
            ),
            (
                "ne_50m_admin_0_countries.zip",
                "https://naturalearth.s3.amazonaws.com/50m_cultural/"
                "ne_50m_admin_0_countries.zip",
            ),
            (
                "ne_50m_admin_0_map_units.zip",
                "https://naturalearth.s3.amazonaws.com/50m_cultural/"
                "ne_50m_admin_0_map_units.zip",
            ),
        ]),
    }
    for source_id, (version, retrieved_at, items) in specs.items():
        folder = root / "build_data" / "raw" / source_id / version
        files = []
        for name, url in items:
            path = folder / name
            if not path.is_file():
                raise FileNotFoundError(f"Missing raw snapshot: {path}")
            files.append({"url": url, "path": name, "sha256": _sha(path), "size_bytes": path.stat().st_size})
        manifest = {"source_id": source_id, "source_version": version, "retrieved_at": retrieved_at, "files": files}
        (folder / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def parse_un_m49(root: Path) -> dict[str, dict[str, object]]:
    parser = M49Parser()
    parser.feed((root / "build_data/raw/un-m49/2026-07-20/overview.html").read_text(encoding="utf-8-sig"))
    records: dict[str, dict[str, object]] = {}
    for row in parser.rows:
        code = row[10].upper()
        if len(code) != 2 or code in records or row[1] != "World":
            continue
        records[code] = {
            "country_code": code,
            "source_id": "un-m49",
            "source_record_id": row[9],
            "retrieved_at": "2026-07-20",
            "data": {
                "official_name": row[8], "numeric_code": row[9], "alpha2": code,
                "alpha3": row[11], "continent": CONTINENTS.get(row[2]),
                "region": row[5] or row[3] or None, "subregion": row[7] or row[5] or None,
            },
        }
    if len(records) != EXPECTED_COUNTRY_COUNT:
        raise ValueError(f"Expected {EXPECTED_COUNTRY_COUNT} UN M49 countries and areas, found {len(records)}")
    return records


def parse_geonames(root: Path, country_codes: set[str]) -> tuple[dict[str, dict[str, object]], list[dict[str, object]]]:
    countries: dict[str, dict[str, object]] = {}
    path = root / "build_data/raw/geonames/2026-07-20/countryInfo.txt"
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        cols = line.split("\t")
        if cols[0] in country_codes:
            countries[cols[0]] = {
                "country_code": cols[0], "source_id": "geonames", "source_record_id": cols[16], "retrieved_at": "2026-07-20",
                "data": {
                    "name": cols[4], "capital": cols[5],
                    "area_km2": float(cols[6]) if cols[6] else None,
                    "population": int(cols[7]) if cols[7] else None,
                    "top_level_domain": cols[9] or None,
                    "currency_code": cols[10] or None,
                    "currency_name": cols[11] or None,
                    "calling_codes": [f"+{value.strip().lstrip('+')}" for value in cols[12].split(",") if value.strip()],
                    "language_codes": [value.strip() for value in cols[15].split(",") if value.strip()],
                    "geonames_id": int(cols[16]),
                    "neighbor_codes": [value for value in cols[17].split(",") if value in country_codes],
                },
            }
    cities: list[dict[str, object]] = []
    with zipfile.ZipFile(root / "build_data/raw/geonames/2026-07-20/cities15000.zip") as archive:
        with archive.open("cities15000.txt") as stream:
            for raw in stream:
                cols = raw.decode("utf-8").rstrip("\n").split("\t")
                if cols[8] not in countries:
                    continue
                population = int(cols[14]) if cols[14] else 0
                is_capital = cols[7] == "PPLC" or cols[1] == countries[cols[8]]["data"]["capital"]
                if population < 100_000 and not is_capital:
                    continue
                cities.append({
                    "country_code": cols[8], "source_id": "geonames", "source_record_id": cols[0], "retrieved_at": "2026-07-20",
                    "data": {"geonames_id": int(cols[0]), "name": cols[1], "ascii_name": cols[2], "alternate_names": [x for x in cols[3].split(",") if x][:30],
                             "latitude": float(cols[4]), "longitude": float(cols[5]), "population": population or None,
                             "elevation_m": float(cols[15]) if cols[15] else None, "timezone_id": cols[17] or None, "is_capital": is_capital},
                })
    return countries, cities


def parse_country_local_names(root: Path, country_codes: set[str]) -> list[dict[str, object]]:
    """Read the reviewed transcription of the approved UNGEGN source artifact."""
    path = root / "build_data/reviewed/country_local_names.csv"
    records: list[dict[str, object]] = []
    seen: set[tuple[str, str]] = set()
    with path.open(encoding="utf-8", newline="") as stream:
        for line_number, row in enumerate(csv.DictReader(stream), 2):
            code = row["country_code"].upper()
            language_code = row["language_code"].casefold()
            key = (code, language_code)
            if code not in country_codes:
                raise ValueError(f"Unknown country code on {path}:{line_number}: {code}")
            if key in seen:
                raise ValueError(f"Duplicate local name on {path}:{line_number}: {key}")
            required = ("language_name", "script_code", "short_name", "official_name", "source_id", "source_locator")
            if not all(row[field] for field in required):
                raise ValueError(f"Incomplete local name on {path}:{line_number}")
            if row["is_official_language"].casefold() not in {"true", "false"}:
                raise ValueError(f"Invalid official-language flag on {path}:{line_number}")
            seen.add(key)
            records.append({
                "country_code": code,
                "source_id": row["source_id"],
                "source_record_id": row["source_locator"],
                "retrieved_at": "2026-07-20",
                "data": {
                    "language_code": language_code,
                    "language_name": row["language_name"],
                    "script_code": row["script_code"],
                    "short_name": row["short_name"],
                    "official_name": row["official_name"],
                    "romanized_short_name": row["romanized_short_name"] or None,
                    "romanized_official_name": row["romanized_official_name"] or None,
                    "is_official_language": row["is_official_language"].casefold() == "true",
                    "source_locator": row["source_locator"],
                },
            })
    if len(records) != EXPECTED_LOCAL_NAME_COUNT:
        raise ValueError(f"Expected {EXPECTED_LOCAL_NAME_COUNT} pilot local names, found {len(records)}")
    return records


def _read_dbf_records(raw: bytes) -> list[dict[str, str]]:
    """Read the character fields needed from a dBASE file in a source archive."""
    record_count = struct.unpack("<I", raw[4:8])[0]
    header_length, record_length = struct.unpack("<HH", raw[8:12])
    fields: list[tuple[str, int]] = []
    position = 32
    while raw[position] != 0x0D:
        descriptor = raw[position:position + 32]
        name = descriptor[:11].split(b"\0", 1)[0].decode("ascii")
        fields.append((name, descriptor[16]))
        position += 32
    records: list[dict[str, str]] = []
    for index in range(record_count):
        row = raw[
            header_length + index * record_length:
            header_length + (index + 1) * record_length
        ]
        offset = 1
        record: dict[str, str] = {}
        for name, length in fields:
            record[name] = row[offset:offset + length].decode("latin-1").replace("\0", "").strip()
            offset += length
        records.append(record)
    return records


def _read_polygon_parts(raw: bytes) -> list[list[list[tuple[float, float]]]]:
    """Read polygon rings from an ESRI shapefile without a runtime GIS dependency."""
    records: list[list[list[tuple[float, float]]]] = []
    position = 100
    while position < len(raw):
        if position + 8 > len(raw):
            raise ValueError("Truncated Natural Earth shapefile record header")
        _, content_words = struct.unpack(">2i", raw[position:position + 8])
        content_length = content_words * 2
        content = raw[position + 8:position + 8 + content_length]
        position += 8 + content_length
        if len(content) != content_length:
            raise ValueError("Truncated Natural Earth shapefile record")
        shape_type = struct.unpack("<i", content[:4])[0]
        if shape_type == 0:
            records.append([])
            continue
        if shape_type not in {5, 15, 25}:
            raise ValueError(f"Unexpected Natural Earth polygon shape type: {shape_type}")
        part_count, point_count = struct.unpack("<2i", content[36:44])
        part_offset = 44
        starts = list(struct.unpack(
            "<" + "i" * part_count,
            content[part_offset:part_offset + 4 * part_count],
        ))
        point_offset = part_offset + 4 * part_count
        points = [
            struct.unpack("<2d", content[point_offset + index * 16:point_offset + (index + 1) * 16])
            for index in range(point_count)
        ]
        starts.append(point_count)
        records.append([points[starts[index]:starts[index + 1]] for index in range(part_count)])
    return records


def parse_land_borders(
    root: Path,
    countries: dict[str, dict[str, object]],
    geonames_countries: dict[str, dict[str, object]],
) -> list[dict[str, object]]:
    """Build the reviewed undirected land-border graph from two pinned sources.

    Relationships accepted automatically must appear in both GeoNames and
    Natural Earth. Every disagreement must have an explicit reviewed decision
    in ``build_data/reviewed/border_decisions.csv``; an unreviewed difference
    fails the build.
    """
    country_codes = set(countries)
    alpha3_to_alpha2 = {
        str(record["data"]["alpha3"]): code for code, record in countries.items()
    }
    archive_path = (
        root / "build_data/raw/natural-earth/2026-07-21/"
        "ne_50m_admin_0_map_units.zip"
    )
    with zipfile.ZipFile(archive_path) as archive:
        dbf_name = next(name for name in archive.namelist() if name.lower().endswith(".dbf"))
        shp_name = next(name for name in archive.namelist() if name.lower().endswith(".shp"))
        map_units = _read_dbf_records(archive.read(dbf_name))
        geometries = _read_polygon_parts(archive.read(shp_name))
    if len(map_units) != len(geometries):
        raise ValueError("Natural Earth map-unit attributes and geometries do not align")

    # Natural Earth identity codes that do not map directly to the UN M49
    # alpha-3 values used by this package's entity scope.
    equivalents = {"SOL": "SO", "CYN": "CY", "TWN": "TW", "TAI": "TW"}

    def resolve_map_unit(record: dict[str, str]) -> str | None:
        for field in ("ISO_A2", "ISO_A2_EH"):
            if record[field] in country_codes:
                return record[field]
        for field in ("ISO_A3", "GU_A3", "ADM0_A3"):
            code = alpha3_to_alpha2.get(record[field])
            if code in country_codes:
                return code
        return equivalents.get(record["ADM0_A3"])

    segment_owners: dict[
        tuple[tuple[float, float], tuple[float, float]], set[str]
    ] = defaultdict(set)
    unresolved: list[str] = []
    for map_unit, rings in zip(map_units, geometries):
        code = resolve_map_unit(map_unit)
        if code is None:
            unresolved.append(map_unit["NAME"])
            continue
        for ring in rings:
            for start, finish in zip(ring, ring[1:]):
                first = tuple(round(value, 7) for value in start)
                second = tuple(round(value, 7) for value in finish)
                if first != second:
                    segment_owners[tuple(sorted((first, second)))].add(code)
    if unresolved != ["Kosovo", "Siachen Glacier"]:
        raise ValueError(f"Unexpected unresolved Natural Earth map units: {unresolved}")

    natural_earth_edges = {
        tuple(sorted((first, second)))
        for owners in segment_owners.values()
        for first in owners
        for second in owners
        if first < second
    }
    geonames_edges = {
        tuple(sorted((code, neighbor)))
        for code, record in geonames_countries.items()
        for neighbor in record["data"]["neighbor_codes"]
        if code != neighbor
    }
    if len(natural_earth_edges) != EXPECTED_NATURAL_EARTH_BORDER_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_NATURAL_EARTH_BORDER_COUNT} Natural Earth edges, "
            f"found {len(natural_earth_edges)}"
        )
    if len(geonames_edges) != EXPECTED_GEONAMES_BORDER_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_GEONAMES_BORDER_COUNT} GeoNames edges, "
            f"found {len(geonames_edges)}"
        )

    decision_path = root / "build_data/reviewed/border_decisions.csv"
    decisions: dict[tuple[str, str], dict[str, str]] = {}
    with decision_path.open(encoding="utf-8", newline="") as stream:
        for line_number, row in enumerate(csv.DictReader(stream), 2):
            edge = tuple(sorted((row["country_code"].upper(), row["neighbor_code"].upper())))
            if len(set(edge)) != 2 or any(code not in country_codes for code in edge):
                raise ValueError(f"Invalid border decision on {decision_path}:{line_number}")
            if edge in decisions or row["decision"] not in {"include", "exclude"}:
                raise ValueError(f"Duplicate or invalid decision on {decision_path}:{line_number}")
            if not row["reason"] or not row["evidence_sources"]:
                raise ValueError(f"Incomplete border decision on {decision_path}:{line_number}")
            decisions[edge] = row

    disagreements = natural_earth_edges ^ geonames_edges
    if set(decisions) != disagreements:
        missing = sorted(disagreements - set(decisions))
        stale = sorted(set(decisions) - disagreements)
        raise ValueError(f"Border decisions do not match source differences; missing={missing}, stale={stale}")

    accepted = natural_earth_edges & geonames_edges
    accepted.update(edge for edge, row in decisions.items() if row["decision"] == "include")
    if len(accepted) != EXPECTED_BORDER_COUNT:
        raise ValueError(f"Expected {EXPECTED_BORDER_COUNT} reviewed land borders, found {len(accepted)}")
    records = []
    for first, second in sorted(accepted):
        decision = decisions.get((first, second))
        records.append({
            "country_code": first,
            "neighbor_code": second,
            "source_id": "reviewed-borders" if decision else "natural-earth",
            "source_record_id": f"{first}-{second}",
            "retrieved_at": "2026-07-21",
            "data": {
                "review_status": "reviewed_exception" if decision else "cross_checked",
                "evidence_sources": (
                    decision["evidence_sources"].split("|")
                    if decision else ["geonames", "natural-earth"]
                ),
                "review_note": decision["reason"] if decision else None,
            },
        })
    return records


def normalize(root: Path) -> dict[str, object]:
    """Create inspectable normalized records from independent sources."""
    un = parse_un_m49(root)
    geocountries, cities = parse_geonames(root, set(un))
    missing_geonames = sorted(set(un) - set(geocountries))
    if missing_geonames:
        raise ValueError(f"UN M49 countries missing from GeoNames: {missing_geonames}")
    common = _load_json(root / "pipeline/config/common_names.json")
    aliases = _load_json(root / "pipeline/config/aliases.json")
    local_names = parse_country_local_names(root, set(un))
    borders = parse_land_borders(root, un, geocountries)
    countries = []
    names = []
    capitals = []
    for code in sorted(un):
        u, g = un[code], geocountries[code]
        data = dict(u["data"])
        data.update({
            "name": common.get(code, g["data"]["name"]),
            "area_km2": g["data"]["area_km2"],
            "population": g["data"]["population"],
            "top_level_domain": g["data"]["top_level_domain"],
            "currency_code": g["data"]["currency_code"],
            "currency_name": g["data"]["currency_name"],
            "calling_codes": g["data"]["calling_codes"],
            "language_codes": g["data"]["language_codes"],
            "geonames_id": g["data"]["geonames_id"],
            "status": "other",
        })
        countries.append({**u, "data": data})
        all_names = [
            (data["name"], "common", "geonames"),
            (data["official_name"], "official", "un-m49"),
            (g["data"]["name"], "alias", "geonames"),
            *((name, "alias", "reviewed-overrides") for name in aliases.get(code, [])),
        ]
        seen = set()
        for name, kind, source_id in all_names:
            if not name or normalize_name(name) in seen:
                continue
            seen.add(normalize_name(name))
            names.append({"country_code": code, "source_id": source_id, "source_record_id": str(data["numeric_code"]), "retrieved_at": "2026-07-20", "data": {"name": name, "normalized_name": normalize_name(name), "kind": kind, "preferred": kind == "common"}})
        candidate = next((city for city in cities if city["country_code"] == code and city["data"]["name"] == g["data"]["capital"]), None)
        if candidate is None:
            candidate = next((city for city in cities if city["country_code"] == code and city["data"]["is_capital"]), None)
        if candidate:
            capitals.append(candidate)
    if len(capitals) != EXPECTED_CAPITAL_COUNT:
        raise ValueError(f"Expected {EXPECTED_CAPITAL_COUNT} capital records, found {len(capitals)}")
    if len(cities) != EXPECTED_CITY_COUNT:
        raise ValueError(f"Expected {EXPECTED_CITY_COUNT} city records, found {len(cities)}")
    normalized = {
        "countries": countries,
        "country_names": names,
        "local_names": local_names,
        "capitals": capitals,
        "cities": cities,
        "borders": borders,
    }
    output = root / "build_data/normalized"
    output.mkdir(parents=True, exist_ok=True)
    for key, records in normalized.items():
        (output / f"{key}.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in records), encoding="utf-8")
    return normalized


SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE schema_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL) WITHOUT ROWID;
CREATE TABLE source (id TEXT PRIMARY KEY, name TEXT NOT NULL, homepage TEXT NOT NULL, version TEXT, retrieved_at TEXT NOT NULL, license_name TEXT, license_url TEXT, checksum_sha256 TEXT, notes TEXT) WITHOUT ROWID;
CREATE TABLE country (id INTEGER PRIMARY KEY, alpha2 TEXT NOT NULL UNIQUE, alpha3 TEXT UNIQUE, numeric_code TEXT UNIQUE, name TEXT NOT NULL, official_name TEXT, status TEXT NOT NULL, continent TEXT, region TEXT, subregion TEXT, geonames_id INTEGER, total_area_km2 REAL, population INTEGER, top_level_domain TEXT, currency_code TEXT, currency_name TEXT, calling_codes TEXT NOT NULL, language_codes TEXT NOT NULL);
CREATE TABLE country_border (country1_id INTEGER NOT NULL, country2_id INTEGER NOT NULL, review_status TEXT NOT NULL, evidence_sources TEXT NOT NULL, review_note TEXT, PRIMARY KEY(country1_id,country2_id), FOREIGN KEY(country1_id) REFERENCES country(id), FOREIGN KEY(country2_id) REFERENCES country(id), CHECK(country1_id < country2_id)) WITHOUT ROWID;
CREATE INDEX idx_country_border_second ON country_border(country2_id);
CREATE TABLE country_name (country_id INTEGER NOT NULL, name TEXT NOT NULL, normalized_name TEXT NOT NULL, language_code TEXT, kind TEXT NOT NULL, preferred INTEGER NOT NULL DEFAULT 0, PRIMARY KEY(country_id,name,kind), FOREIGN KEY(country_id) REFERENCES country(id));
CREATE INDEX idx_country_name_normalized ON country_name(normalized_name);
CREATE TABLE country_local_name (country_id INTEGER NOT NULL, language_code TEXT NOT NULL, language_name TEXT NOT NULL, script_code TEXT NOT NULL, short_name TEXT NOT NULL, official_name TEXT, romanized_short_name TEXT, romanized_official_name TEXT, is_official_language INTEGER NOT NULL, source_id TEXT NOT NULL, source_locator TEXT NOT NULL, PRIMARY KEY(country_id,language_code), FOREIGN KEY(country_id) REFERENCES country(id), FOREIGN KEY(source_id) REFERENCES source(id)) WITHOUT ROWID;
CREATE INDEX idx_country_local_name_country ON country_local_name(country_id);
CREATE TABLE capital (id INTEGER PRIMARY KEY, country_id INTEGER NOT NULL, name TEXT NOT NULL, normalized_name TEXT NOT NULL, role TEXT NOT NULL, is_primary INTEGER NOT NULL, latitude REAL NOT NULL, longitude REAL NOT NULL, population INTEGER, elevation_m REAL, timezone_id TEXT, geonames_id INTEGER UNIQUE, FOREIGN KEY(country_id) REFERENCES country(id));
CREATE TABLE city (id INTEGER PRIMARY KEY, country_id INTEGER NOT NULL, name TEXT NOT NULL, normalized_name TEXT NOT NULL, latitude REAL NOT NULL, longitude REAL NOT NULL, population INTEGER, elevation_m REAL, timezone_id TEXT, geonames_id INTEGER UNIQUE, is_capital INTEGER NOT NULL DEFAULT 0, FOREIGN KEY(country_id) REFERENCES country(id));
CREATE INDEX idx_city_country ON city(country_id);
CREATE TABLE field_source (country_id INTEGER NOT NULL, field_path TEXT NOT NULL, source_id TEXT NOT NULL, source_record_id TEXT, PRIMARY KEY(country_id,field_path), FOREIGN KEY(country_id) REFERENCES country(id), FOREIGN KEY(source_id) REFERENCES source(id)) WITHOUT ROWID;
"""


def build_database(root: Path, normalized: dict[str, object]) -> Path:
    """Build the deterministic, normalized SQLite runtime database."""
    output = root / "build_data/output"
    output.mkdir(parents=True, exist_ok=True)
    path = output / "atlas.sqlite3"
    if path.exists():
        path.unlink()
    con = sqlite3.connect(path)
    con.executescript(SCHEMA)
    epoch = os.environ.get("SOURCE_DATE_EPOCH")
    built_at = datetime.fromtimestamp(int(epoch), timezone.utc).isoformat().replace("+00:00", "Z") if epoch else "2026-07-21T00:00:00Z"
    library_version = _project_version(root)
    meta = {"schema_version": "3", "dataset_version": "2026.07.21.1", "library_version": library_version, "built_at": built_at}
    con.executemany("INSERT INTO schema_meta VALUES (?,?)", sorted(meta.items()))
    sources = [
        ("geonames", "GeoNames", "https://www.geonames.org/", "2026-07-20", "2026-07-20", "CC BY 4.0", "https://creativecommons.org/licenses/by/4.0/", _sha(root / "build_data/raw/geonames/2026-07-20/manifest.json"), "Country metadata and populated places"),
        ("natural-earth", "Natural Earth", "https://www.naturalearthdata.com/", "5.1.0/5.1.1", "2026-07-21", "Public domain", "https://www.naturalearthdata.com/about/terms-of-use/", _sha(root / "build_data/raw/natural-earth/2026-07-21/manifest.json"), "Map-unit topology used to cross-check land-border relationships"),
        ("reviewed-borders", "PyWorldAtlas reviewed border decisions", "https://jcari-dev.github.io/pyworldatlas-documentation/borders.html", library_version, "2026-07-21", "MIT", None, _sha(root / "build_data/reviewed/border_decisions.csv"), "Explicit decisions for every difference between the pinned GeoNames and Natural Earth border inputs"),
        ("reviewed-overrides", "PyWorldAtlas reviewed overrides", "https://jcari-dev.github.io/pyworldatlas-documentation/", library_version, "2026-07-20", "MIT", None, _sha(root / "pipeline/config/overrides.json"), "Reviewed familiar names and aliases"),
        ("un-m49", "United Nations M49", "https://unstats.un.org/unsd/methodology/m49/", "2026-07-20", "2026-07-20", None, None, _sha(root / "build_data/raw/un-m49/2026-07-20/manifest.json"), "Canonical identities and regions"),
        ("ungegn-country-names-2017", "UNGEGN List of Country Names", "https://unstats.un.org/unsd/ungegn/working_groups/wg1.cshtml", "E/CONF.105/13/CRP.13 (2017-07-17)", "2026-07-20", None, None, _sha(root / "build_data/raw/ungegn-country-names/2017-07-17/manifest.json"), "Approved national official short and formal country names; pilot entries transcribed with page locators"),
    ]
    con.executemany("INSERT INTO source VALUES (?,?,?,?,?,?,?,?,?)", sources)
    ids: dict[str, int] = {}
    for ident, record in enumerate(sorted(normalized["countries"], key=lambda r: r["country_code"]), 1):
        code, data = record["country_code"], record["data"]
        ids[code] = ident
        con.execute("INSERT INTO country VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (ident, code, data["alpha3"], data["numeric_code"], data["name"], data["official_name"], data["status"], data["continent"], data["region"], data["subregion"], data["geonames_id"], data["area_km2"], data["population"], data["top_level_domain"], data["currency_code"], data["currency_name"], json.dumps(data["calling_codes"], ensure_ascii=False), json.dumps(data["language_codes"], ensure_ascii=False)))
        field_sources = [
            (ident, "identity", "un-m49", data["numeric_code"]),
            (ident, "capitals", "geonames", str(data["geonames_id"])),
            (ident, "major_cities", "geonames", str(data["geonames_id"])),
            (ident, "land_borders.geonames", "geonames", str(data["geonames_id"])),
            (ident, "land_borders.natural_earth", "natural-earth", "admin-0-map-units-50m"),
            (ident, "land_borders.review", "reviewed-borders", data["alpha2"]),
        ]
        if any(name["country_code"] == code and name["source_id"] == "reviewed-overrides" for name in normalized["country_names"]):
            field_sources.append((ident, "names.reviewed", "reviewed-overrides", data["numeric_code"]))
        if any(name["country_code"] == code for name in normalized["local_names"]):
            locator = next(name["source_record_id"] for name in normalized["local_names"] if name["country_code"] == code)
            field_sources.append((ident, "local_names", "ungegn-country-names-2017", locator))
        con.executemany("INSERT INTO field_source VALUES (?,?,?,?)", field_sources)
    for record in normalized["borders"]:
        data = record["data"]
        con.execute(
            "INSERT INTO country_border VALUES (?,?,?,?,?)",
            (
                ids[record["country_code"]],
                ids[record["neighbor_code"]],
                data["review_status"],
                json.dumps(data["evidence_sources"], ensure_ascii=False),
                data["review_note"],
            ),
        )
    for record in sorted(normalized["country_names"], key=lambda r: (r["country_code"], r["data"]["normalized_name"], r["data"]["kind"])):
        d = record["data"]
        con.execute("INSERT INTO country_name VALUES (?,?,?,?,?,?)", (ids[record["country_code"]], d["name"], d["normalized_name"], None, d["kind"], int(d["preferred"])))
    for record in sorted(normalized["local_names"], key=lambda r: (r["country_code"], r["data"]["language_code"])):
        d = record["data"]
        con.execute(
            "INSERT INTO country_local_name VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (ids[record["country_code"]], d["language_code"], d["language_name"], d["script_code"], d["short_name"], d["official_name"], d["romanized_short_name"], d["romanized_official_name"], int(d["is_official_language"]), record["source_id"], d["source_locator"]),
        )
    capital_ids = {record["data"]["geonames_id"] for record in normalized["capitals"]}
    for ident, record in enumerate(sorted(normalized["capitals"], key=lambda r: (r["country_code"], r["data"]["name"])), 1):
        d = record["data"]
        con.execute("INSERT INTO capital VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", (ident, ids[record["country_code"]], d["name"], normalize_name(d["name"]), "official", 1, d["latitude"], d["longitude"], d["population"], d["elevation_m"], d["timezone_id"], d["geonames_id"]))
    for ident, record in enumerate(sorted(normalized["cities"], key=lambda r: (r["country_code"], -int(r["data"]["population"] or 0), r["data"]["name"])), 1):
        d = record["data"]
        con.execute("INSERT INTO city VALUES (?,?,?,?,?,?,?,?,?,?,?)", (ident, ids[record["country_code"]], d["name"], normalize_name(d["name"]), d["latitude"], d["longitude"], d["population"], d["elevation_m"], d["timezone_id"], d["geonames_id"], int(d["geonames_id"] in capital_ids)))
    con.commit()
    if con.execute("PRAGMA integrity_check").fetchone()[0] != "ok" or con.execute("PRAGMA foreign_key_check").fetchall():
        raise ValueError("SQLite integrity validation failed")
    con.execute("VACUUM")
    con.close()
    target = root / "src/pyworldatlas/data/atlas.sqlite3"
    target.write_bytes(path.read_bytes())
    return target


def report(root: Path, normalized: dict[str, object], database: Path) -> None:
    reports = root / "build_data/reports"
    reports.mkdir(parents=True, exist_ok=True)
    countries = normalized["countries"]
    coverage = {
        "dataset_version": "2026.07.21.1",
        "countries": len(countries),
        "capitals": len(normalized["capitals"]),
        "major_cities": len(normalized["cities"]),
        "capital_coordinates": len(normalized["capitals"]),
        "population_profiles": sum(record["data"]["population"] is not None for record in countries),
        "currency_profiles": sum(record["data"]["currency_code"] is not None for record in countries),
        "calling_code_profiles": sum(bool(record["data"]["calling_codes"]) for record in countries),
        "language_profiles": sum(bool(record["data"]["language_codes"]) for record in countries),
        "top_level_domain_profiles": sum(record["data"]["top_level_domain"] is not None for record in countries),
        "observed_timezone_profiles": len({
            record["country_code"]
            for record in normalized["cities"]
            if record["data"]["timezone_id"]
        }),
        "local_names": len(normalized["local_names"]),
        "local_name_countries": len({record["country_code"] for record in normalized["local_names"]}),
        "reviewed_land_borders": len(normalized["borders"]),
        "countries_with_land_borders": len({
            code
            for record in normalized["borders"]
            for code in (record["country_code"], record["neighbor_code"])
        }),
        "countries_with_no_land_borders": len(countries) - len({
            code
            for record in normalized["borders"]
            for code in (record["country_code"], record["neighbor_code"])
        }),
        "database_sha256": _sha(database),
        "validation": "PASS",
    }
    (reports / "coverage.json").write_text(json.dumps(coverage, indent=2) + "\n", encoding="utf-8")
    milestones = [
        {
            "name": "0 — Clean foundation",
            "version": "0.1.0",
            "status": "complete",
            "functions": "Standard package layout, generated database, release automation",
            "tests": "Local 0.1.0 release gate passed",
            "dataset": "Captured and checksummed source snapshots",
            "docs": "Sphinx source and maintainer instructions",
            "release": "Rebuilt baseline tagged v0.1.0",
        },
        {
            "name": "1 — Generated country core",
            "version": "0.1.0",
            "status": "complete",
            "functions": "Lookup, search, collection protocol, capitals, populated places, dataset info",
            "tests": "Python 3.10-3.14 CI and local release gate passed",
            "dataset": f"{coverage['countries']} countries and areas / {coverage['capitals']} capitals / {coverage['major_cities']} places",
            "docs": "Core usage and data guides",
            "release": "Included in the v0.1.0 rebuilt baseline",
        },
        {
            "name": "2 — Country profiles, coordinates, and discovery",
            "version": "0.2.1",
            "status": "complete",
            "functions": "Profiles, coordinate tools, flags, discovery cards, stable samples, flashcards",
            "tests": "Unit tests and complete local release gate pass",
            "dataset": "248 profiles / 6,265 coordinate-bearing places / 5 reviewed local names",
            "docs": "Profile, local-name, coordinate, and discovery guides",
            "release": "Publication state is tracked on GitHub Releases and PyPI",
        },
        {
            "name": "3 — Reviewed land borders",
            "version": "0.3.0",
            "status": "complete",
            "functions": "Neighbors, shared borders, shortest land paths, crossings, components, and borderless entities",
            "tests": "Source-difference review gate, graph invariants, API tests, and complete release gate",
            "dataset": f"{coverage['reviewed_land_borders']} reviewed undirected land-border relationships",
            "docs": "Border API, data policy, exceptions, and examples",
            "release": "Publication state is tracked on GitHub Releases and PyPI",
        },
    ]
    for name, version in [
        ("4 — Geometry", "0.4.0"), ("5 — Statistics", "0.5.0"),
        ("6 — Leaders", "0.6.0"), ("7 — Culture and institutions", "0.7.0"),
        ("8 — Advanced education and export", "0.8.0"), ("9 — Full-world hardening", "0.9.0"),
        ("Stable offline atlas", "1.0.0"),
    ]:
        milestones.append({"name": name, "version": version, "status": "planned", "functions": "—", "tests": "—", "dataset": "—", "docs": "—", "release": "—"})
    status = {
        "library_version": _project_version(root),
        "schema_version": 3,
        "dataset_version": "2026.07.21.1",
        "milestones": milestones,
        "coverage": coverage,
    }
    (reports / "status.json").write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")


def run(root: Path) -> Path:
    write_manifests(root)
    normalized = normalize(root)
    database = build_database(root, normalized)
    report(root, normalized, database)
    return database
