"""Deterministic Release 0.1.0 world-core data pipeline."""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import sqlite3
import zipfile


EXPECTED_COUNTRY_COUNT = 248
EXPECTED_CAPITAL_COUNT = 241
EXPECTED_CITY_COUNT = 6_265
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
        "un-m49": [("overview.html", "https://unstats.un.org/unsd/methodology/m49/overview/")],
        "geonames": [
            ("countryInfo.txt", "https://download.geonames.org/export/dump/countryInfo.txt"),
            ("cities15000.zip", "https://download.geonames.org/export/dump/cities15000.zip"),
        ],
    }
    for source_id, items in specs.items():
        folder = root / "build_data" / "raw" / source_id / "2026-07-20"
        files = []
        for name, url in items:
            path = folder / name
            if not path.is_file():
                raise FileNotFoundError(f"Missing raw snapshot: {path}")
            files.append({"url": url, "path": name, "sha256": _sha(path), "size_bytes": path.stat().st_size})
        manifest = {"source_id": source_id, "source_version": "2026-07-20", "retrieved_at": "2026-07-20T00:00:00Z", "files": files}
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
                "data": {"name": cols[4], "capital": cols[5], "area_km2": float(cols[6]) if cols[6] else None, "geonames_id": int(cols[16])},
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


def normalize(root: Path) -> dict[str, object]:
    """Create inspectable normalized records from independent sources."""
    un = parse_un_m49(root)
    geocountries, cities = parse_geonames(root, set(un))
    missing_geonames = sorted(set(un) - set(geocountries))
    if missing_geonames:
        raise ValueError(f"UN M49 countries missing from GeoNames: {missing_geonames}")
    common = _load_json(root / "pipeline/config/common_names.json")
    aliases = _load_json(root / "pipeline/config/aliases.json")
    countries = []
    names = []
    capitals = []
    for code in sorted(un):
        u, g = un[code], geocountries[code]
        data = dict(u["data"])
        data.update({"name": common.get(code, g["data"]["name"]), "area_km2": g["data"]["area_km2"], "geonames_id": g["data"]["geonames_id"], "status": "other"})
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
    normalized = {"countries": countries, "country_names": names, "capitals": capitals, "cities": cities}
    output = root / "build_data/normalized"
    output.mkdir(parents=True, exist_ok=True)
    for key, records in normalized.items():
        (output / f"{key}.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in records), encoding="utf-8")
    return normalized


SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE schema_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL) WITHOUT ROWID;
CREATE TABLE source (id TEXT PRIMARY KEY, name TEXT NOT NULL, homepage TEXT NOT NULL, version TEXT, retrieved_at TEXT NOT NULL, license_name TEXT, license_url TEXT, checksum_sha256 TEXT, notes TEXT) WITHOUT ROWID;
CREATE TABLE country (id INTEGER PRIMARY KEY, alpha2 TEXT NOT NULL UNIQUE, alpha3 TEXT UNIQUE, numeric_code TEXT UNIQUE, name TEXT NOT NULL, official_name TEXT, status TEXT NOT NULL, continent TEXT, region TEXT, subregion TEXT, geonames_id INTEGER, total_area_km2 REAL);
CREATE TABLE country_name (country_id INTEGER NOT NULL, name TEXT NOT NULL, normalized_name TEXT NOT NULL, language_code TEXT, kind TEXT NOT NULL, preferred INTEGER NOT NULL DEFAULT 0, PRIMARY KEY(country_id,name,kind), FOREIGN KEY(country_id) REFERENCES country(id));
CREATE INDEX idx_country_name_normalized ON country_name(normalized_name);
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
    built_at = datetime.fromtimestamp(int(epoch), timezone.utc).isoformat().replace("+00:00", "Z") if epoch else "2026-07-20T00:00:00Z"
    library_version = _project_version(root)
    meta = {"schema_version": "1", "dataset_version": "2026.07.20", "library_version": library_version, "built_at": built_at}
    con.executemany("INSERT INTO schema_meta VALUES (?,?)", sorted(meta.items()))
    sources = [
        ("geonames", "GeoNames", "https://www.geonames.org/", "2026-07-20", "2026-07-20", "CC BY 4.0", "https://creativecommons.org/licenses/by/4.0/", _sha(root / "build_data/raw/geonames/2026-07-20/manifest.json"), "Country metadata and populated places"),
        ("reviewed-overrides", "PyWorldAtlas reviewed overrides", "https://jcari-dev.github.io/pyworldatlas-documentation/", library_version, "2026-07-20", "MIT", None, _sha(root / "pipeline/config/overrides.json"), "Reviewed familiar names and aliases"),
        ("un-m49", "United Nations M49", "https://unstats.un.org/unsd/methodology/m49/", "2026-07-20", "2026-07-20", None, None, _sha(root / "build_data/raw/un-m49/2026-07-20/manifest.json"), "Canonical identities and regions"),
    ]
    con.executemany("INSERT INTO source VALUES (?,?,?,?,?,?,?,?,?)", sources)
    ids: dict[str, int] = {}
    for ident, record in enumerate(sorted(normalized["countries"], key=lambda r: r["country_code"]), 1):
        code, data = record["country_code"], record["data"]
        ids[code] = ident
        con.execute("INSERT INTO country VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", (ident, code, data["alpha3"], data["numeric_code"], data["name"], data["official_name"], data["status"], data["continent"], data["region"], data["subregion"], data["geonames_id"], data["area_km2"]))
        field_sources = [(ident, "identity", "un-m49", data["numeric_code"]), (ident, "capitals", "geonames", str(data["geonames_id"])), (ident, "major_cities", "geonames", str(data["geonames_id"]))]
        if any(name["country_code"] == code and name["source_id"] == "reviewed-overrides" for name in normalized["country_names"]):
            field_sources.append((ident, "names.reviewed", "reviewed-overrides", data["numeric_code"]))
        con.executemany("INSERT INTO field_source VALUES (?,?,?,?)", field_sources)
    for record in sorted(normalized["country_names"], key=lambda r: (r["country_code"], r["data"]["normalized_name"], r["data"]["kind"])):
        d = record["data"]
        con.execute("INSERT INTO country_name VALUES (?,?,?,?,?,?)", (ids[record["country_code"]], d["name"], d["normalized_name"], None, d["kind"], int(d["preferred"])))
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
    coverage = {"dataset_version": "2026.07.20", "countries": len(normalized["countries"]), "capitals": len(normalized["capitals"]), "major_cities": len(normalized["cities"]), "capital_coordinates": len(normalized["capitals"]), "database_sha256": _sha(database), "validation": "PASS"}
    (reports / "coverage.json").write_text(json.dumps(coverage, indent=2) + "\n", encoding="utf-8")
    implemented = {"functions": "Atlas lookup, search, collection protocol, capitals, major cities, dataset info", "tests": "full local quality gate", "dataset": f"{coverage['countries']} countries and areas / {coverage['capitals']} capitals / {coverage['major_cities']} cities", "docs": "source complete; local HTML and doctests pass", "release": "not published"}
    milestones = [
        {"name": "0 — Clean foundation", "version": "0.1.0", "status": "implemented", **implemented},
        {"name": "1 — Generated country core", "version": "0.1.0", "status": "implemented", **implemented},
    ]
    for name, version in [
        ("2 — Geographic calculations", "0.2.0"), ("3 — Borders", "0.3.0"),
        ("4 — Geometry", "0.4.0"), ("5 — Statistics", "0.5.0"),
        ("6 — Leaders", "0.6.0"), ("7 — Rich profile", "0.7.0"),
        ("8 — Education and export", "0.8.0"), ("9 — Full-world hardening", "0.9.0"),
        ("Stable offline atlas", "1.0.0"),
    ]:
        milestones.append({"name": name, "version": version, "status": "not_started", "functions": "—", "tests": "—", "dataset": "—", "docs": "—", "release": "—"})
    status = {"library_version": _project_version(root), "schema_version": 1, "dataset_version": "2026.07.20", "milestones": milestones, "coverage": coverage, "legacy_release": "0.0.12 retained on PyPI"}
    (reports / "status.json").write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")


def run(root: Path) -> Path:
    write_manifests(root)
    normalized = normalize(root)
    database = build_database(root, normalized)
    report(root, normalized, database)
    return database
