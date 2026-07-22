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
import unicodedata
import zipfile


EXPECTED_COUNTRY_COUNT = 248
EXPECTED_CAPITAL_COUNT = 241
EXPECTED_CITY_COUNT = 6_265
EXPECTED_REVIEWED_LOCAL_NAME_COUNT = 14
EXPECTED_LOCAL_NAME_COUNT = 248
EXPECTED_ENGLISH_FORMAL_NAME_COUNT = 240
EXPECTED_FORMAL_NAME_OVERRIDE_COUNT = 8
EXPECTED_ANTHEM_COUNT = 234
EXPECTED_DEMONYM_COUNT = 227
EXPECTED_MOTTO_COUNT = 32
EXPECTED_TIMEZONE_COUNTRY_COUNT = 246
EXPECTED_PHYSICAL_PROFILE_COUNT = 240
EXPECTED_PHYSICAL_TOTAL_AREA_COUNT = 238
EXPECTED_PHYSICAL_LAND_AREA_COUNT = 238
EXPECTED_PHYSICAL_WATER_AREA_COUNT = 233
EXPECTED_COASTLINE_COUNT = 238
EXPECTED_ELEVATION_EXTREME_COUNT = 240
EXPECTED_MEAN_ELEVATION_COUNT = 166
EXPECTED_RIVER_PROFILE_COUNT = 80
EXPECTED_RIVER_COUNT = 188
EXPECTED_LAKE_PROFILE_COUNT = 69
EXPECTED_LAKE_COUNT = 187
EXPECTED_CLIMATE_SUMMARY_COUNT = 240
EXPECTED_KOPPEN_PROFILE_COUNT = 241
EXPECTED_KOPPEN_GAPS = {"BV", "GI", "MH", "MV", "TK", "TV", "UM"}
EXPECTED_ENGLISH_FORMAL_NAME_GAPS = {
    "AX", "BQ", "GF", "GP", "MQ", "RE", "UM", "YT",
}
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
        (folder / "manifest.json").write_text(
            json.dumps(manifest, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )

    cldr_folder = root / "build_data" / "raw" / "unicode-cldr" / "48.2"
    cldr_snapshot_path = cldr_folder / "country_identity.json"
    cldr_reference_path = cldr_folder / "country_reference.json"
    if not cldr_snapshot_path.is_file():
        raise FileNotFoundError(f"Missing raw snapshot: {cldr_snapshot_path}")
    if not cldr_reference_path.is_file():
        raise FileNotFoundError(f"Missing raw snapshot: {cldr_reference_path}")
    cldr_snapshot = _load_json(cldr_snapshot_path)
    cldr_manifest = {
        "source_id": "unicode-cldr-48.2",
        "source_version": "48.2",
        "retrieved_at": "2026-07-21T00:00:00Z",
        "source_archive": {
            "url": cldr_snapshot["archive_url"],
            "sha256": cldr_snapshot["archive_sha256"],
        },
        "derived_file": {
            "path": "country_identity.json",
            "sha256": _sha(cldr_snapshot_path),
            "size_bytes": cldr_snapshot_path.stat().st_size,
        },
        "reference_file": {
            "path": "country_reference.json",
            "sha256": _sha(cldr_reference_path),
            "size_bytes": cldr_reference_path.stat().st_size,
        },
        "extractor": "pipeline/scripts/extract_cldr_country_identity.py",
        "reference_extractor": "pipeline/scripts/extract_cldr_reference_data.py",
        "license_name": cldr_snapshot["license_name"],
        "license_url": cldr_snapshot["license_url"],
    }
    (cldr_folder / "manifest.json").write_text(
        json.dumps(cldr_manifest, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    additional_manifests = [
        (
            root / "build_data/raw/geonames/2026-07-22",
            {
                "source_id": "geonames-timezones-2026-07-22",
                "source_version": "2026-07-22",
                "retrieved_at": "2026-07-22T00:00:00Z",
                "license_name": "CC BY 4.0",
                "license_url": "https://creativecommons.org/licenses/by/4.0/",
                "files": [{
                    "url": "https://download.geonames.org/export/dump/timeZones.txt",
                    "path": "timeZones.txt",
                    "sha256": _sha(root / "build_data/raw/geonames/2026-07-22/timeZones.txt"),
                    "size_bytes": (root / "build_data/raw/geonames/2026-07-22/timeZones.txt").stat().st_size,
                }],
            },
        ),
        (
            root / "build_data/raw/iana/2026-07-22",
            {
                "source_id": "iana-language-subtags-2026-06-14",
                "source_version": "File-Date 2026-06-14",
                "retrieved_at": "2026-07-22T00:00:00Z",
                "license_name": "CC0 1.0",
                "license_url": "https://www.iana.org/help/licensing-terms",
                "files": [{
                    "url": "https://www.iana.org/assignments/language-subtag-registry/language-subtag-registry",
                    "path": "language-subtag-registry.txt",
                    "sha256": _sha(root / "build_data/raw/iana/2026-07-22/language-subtag-registry.txt"),
                    "size_bytes": (root / "build_data/raw/iana/2026-07-22/language-subtag-registry.txt").stat().st_size,
                }],
            },
        ),
        (
            root / "build_data/raw/wikidata/2026-07-22",
            {
                "source_id": "wikidata-national-mottos-2026-07-22",
                "source_version": "2026-07-22 query snapshot",
                "retrieved_at": "2026-07-22T00:00:00Z",
                "endpoint": "https://query.wikidata.org/sparql",
                "query": {
                    "path": "pipeline/queries/wikidata_national_mottos.rq",
                    "sha256": _sha(root / "pipeline/queries/wikidata_national_mottos.rq"),
                },
                "file": {
                    "path": "national-mottos.json",
                    "sha256": _sha(root / "build_data/raw/wikidata/2026-07-22/national-mottos.json"),
                    "size_bytes": (root / "build_data/raw/wikidata/2026-07-22/national-mottos.json").stat().st_size,
                },
                "rights": "Creative Commons CC0 1.0",
                "rights_url": "https://www.wikidata.org/wiki/Wikidata:Licensing",
            },
        ),
    ]
    for folder, manifest in additional_manifests:
        (folder / "manifest.json").write_text(
            json.dumps(manifest, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )


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
                    "postal_code_format": cols[13] or None,
                    "postal_code_regex": cols[14] or None,
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


def _parse_reviewed_country_local_names(
    root: Path, country_codes: set[str]
) -> list[dict[str, object]]:
    """Read reviewed formal-name transcriptions from the UNGEGN artifact."""
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
            required = ("language_code", "language_name", "script_code", "short_name", "official_name", "source_id", "source_locator")
            if not all(row[field] for field in required):
                raise ValueError(f"Incomplete local name on {path}:{line_number}")
            if re.fullmatch(r"[a-z]{2,3}", language_code) is None:
                raise ValueError(f"Invalid language code on {path}:{line_number}: {language_code}")
            if re.fullmatch(r"[A-Z][a-z]{3}", row["script_code"]) is None:
                raise ValueError(f"Invalid ISO 15924 script code on {path}:{line_number}: {row['script_code']}")
            if "PDF page " not in row["source_locator"]:
                raise ValueError(f"Missing PDF page locator on {path}:{line_number}")
            if row["is_official_language"].casefold() not in {"true", "false"}:
                raise ValueError(f"Invalid official-language flag on {path}:{line_number}")
            unicode_fields = (
                "short_name", "official_name", "romanized_short_name",
                "romanized_official_name",
            )
            if any(
                value and unicodedata.normalize("NFC", value) != value
                for field in unicode_fields
                if (value := row[field])
            ):
                raise ValueError(f"Local name is not Unicode NFC on {path}:{line_number}")
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
                    "name_kind": "national_official",
                    "language_status": "official",
                    "source_locator": row["source_locator"],
                },
            })
    if len(records) != EXPECTED_REVIEWED_LOCAL_NAME_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_REVIEWED_LOCAL_NAME_COUNT} reviewed formal names, "
            f"found {len(records)}"
        )
    return records


def parse_country_local_names(root: Path, country_codes: set[str]) -> list[dict[str, object]]:
    """Build one sourced local identity record for every country or area.

    Unicode CLDR supplies complete localized display-name coverage and the
    selected official-language metadata. A matching reviewed UNGEGN record
    replaces the display name with national official short and formal forms.
    """
    reviewed = _parse_reviewed_country_local_names(root, country_codes)
    reviewed_by_key = {
        (record["country_code"], record["data"]["language_code"]): record
        for record in reviewed
    }
    path = root / "build_data/raw/unicode-cldr/48.2/country_identity.json"
    snapshot = _load_json(path)
    source_id = snapshot.get("source_id")
    if source_id != "unicode-cldr-48.2":
        raise ValueError(f"Unexpected CLDR source identifier in {path}: {source_id}")
    rows = snapshot.get("records")
    if not isinstance(rows, list) or len(rows) != EXPECTED_LOCAL_NAME_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_LOCAL_NAME_COUNT} CLDR identity rows, "
            f"found {len(rows) if isinstance(rows, list) else 'invalid data'}"
        )

    records: list[dict[str, object]] = []
    seen_countries: set[str] = set()
    for row in rows:
        code = row["country_code"].upper()
        language_code = row["language_code"].casefold()
        if code not in country_codes:
            raise ValueError(f"Unknown country code in {path}: {code}")
        if code in seen_countries:
            raise ValueError(f"Duplicate CLDR identity row in {path}: {code}")
        if re.fullmatch(r"[a-z]{2,3}(?:-[a-z0-9]{2,8})*", language_code) is None:
            raise ValueError(f"Invalid CLDR language code in {path}: {language_code}")
        if re.fullmatch(r"[A-Z][a-z]{3}", row["script_code"]) is None:
            raise ValueError(f"Invalid CLDR script code in {path}: {row['script_code']}")
        if unicodedata.normalize("NFC", row["local_name"]) != row["local_name"]:
            raise ValueError(f"CLDR local name is not Unicode NFC in {path}: {code}")
        seen_countries.add(code)
        reviewed_record = reviewed_by_key.get((code, language_code))
        if reviewed_record is not None:
            records.append(reviewed_record)
            continue
        records.append({
            "country_code": code,
            "source_id": source_id,
            "source_record_id": row["source_locator"],
            "retrieved_at": "2026-07-21",
            "data": {
                "language_code": language_code,
                "language_name": row["language_name"],
                "script_code": row["script_code"],
                "short_name": row["local_name"],
                "official_name": None,
                "romanized_short_name": None,
                "romanized_official_name": None,
                "is_official_language": bool(row["is_official_language"]),
                "name_kind": "locale_display",
                "language_status": row["language_status"],
                "source_locator": row["source_locator"],
            },
        })
    missing = sorted(country_codes - seen_countries)
    extra = sorted(seen_countries - country_codes)
    if missing or extra:
        raise ValueError(f"CLDR identity scope mismatch; missing={missing}, extra={extra}")
    return records


def parse_english_formal_names(
    root: Path, country_codes: set[str]
) -> list[dict[str, object]]:
    """Build reviewed English formal-name records from reusable sources.

    The public-domain World Factbook snapshot supplies the base layer. A small
    reviewed override file resolves source conflicts with current CC0 Wikidata
    statements or short, credited excerpts from the UN Protocol membership
    list. Areas absent from the Factbook scope remain explicitly uncovered.
    """
    factbook_path = (
        root / "build_data/raw/cia-world-factbook/2025/country_identity.json"
    )
    snapshot = _load_json(factbook_path)
    if snapshot.get("source_id") != "cia-world-factbook-2025":
        raise ValueError(f"Unexpected Factbook source identifier in {factbook_path}")
    rows = snapshot.get("records")
    if not isinstance(rows, list) or len(rows) != EXPECTED_ENGLISH_FORMAL_NAME_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_ENGLISH_FORMAL_NAME_COUNT} Factbook identity rows, "
            f"found {len(rows) if isinstance(rows, list) else 'invalid data'}"
        )

    wikidata_path = root / "build_data/raw/wikidata/2026-07-21/official-names.json"
    wikidata_rows = _load_json(wikidata_path)["results"]["bindings"]
    wikidata_by_statement = {
        row["statement"]["value"].rsplit("/", 1)[-1]: row
        for row in wikidata_rows
    }

    override_path = root / "build_data/reviewed/english_formal_name_overrides.csv"
    overrides: dict[str, dict[str, str]] = {}
    with override_path.open(encoding="utf-8", newline="") as stream:
        for line_number, row in enumerate(csv.DictReader(stream), 2):
            code = row["country_code"].upper()
            if code not in country_codes:
                raise ValueError(
                    f"Unknown country code on {override_path}:{line_number}: {code}"
                )
            if code in overrides:
                raise ValueError(
                    f"Duplicate formal-name override on {override_path}:{line_number}: {code}"
                )
            required = (
                "formal_name", "source_id", "source_record_id",
                "source_locator", "review_note",
            )
            if not all(row[field] for field in required):
                raise ValueError(
                    f"Incomplete formal-name override on {override_path}:{line_number}"
                )
            if row["source_id"] == "wikidata-official-names-2026-07-21":
                statement = wikidata_by_statement.get(row["source_record_id"])
                if statement is None:
                    raise ValueError(
                        f"Unknown Wikidata statement on {override_path}:{line_number}"
                    )
                if statement["alpha2"]["value"] != code:
                    raise ValueError(
                        f"Wikidata country mismatch on {override_path}:{line_number}"
                    )
                if statement["officialName"]["value"] != row["formal_name"]:
                    raise ValueError(
                        f"Wikidata value mismatch on {override_path}:{line_number}"
                    )
                if statement["rank"]["value"].endswith("DeprecatedRank"):
                    raise ValueError(
                        f"Deprecated Wikidata statement on {override_path}:{line_number}"
                    )
            elif row["source_id"] == "un-protocol-country-names-2025":
                if "PDF page " not in row["source_locator"]:
                    raise ValueError(
                        f"Missing UN PDF locator on {override_path}:{line_number}"
                    )
            else:
                raise ValueError(
                    f"Unsupported override source on {override_path}:{line_number}"
                )
            overrides[code] = row
    if len(overrides) != EXPECTED_FORMAL_NAME_OVERRIDE_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_FORMAL_NAME_OVERRIDE_COUNT} formal-name overrides, "
            f"found {len(overrides)}"
        )

    records: list[dict[str, object]] = []
    seen: set[str] = set()
    applied_overrides: set[str] = set()
    for row in rows:
        code = row["country_code"].upper()
        if code not in country_codes:
            raise ValueError(f"Unknown country code in {factbook_path}: {code}")
        if code in seen:
            raise ValueError(f"Duplicate Factbook identity row in {factbook_path}: {code}")
        seen.add(code)

        override = overrides.get(code)
        if override is not None:
            formal_name = override["formal_name"]
            source_id = override["source_id"]
            source_record_id = override["source_record_id"]
            source_locator = override["source_locator"]
            name_status = "source_provided"
            applied_overrides.add(code)
        else:
            formal_name = row["conventional_formal_name"]
            if code == "GB" and formal_name:
                formal_name = formal_name.split("; note -", 1)[0].strip()
            if formal_name and "disputed" in formal_name.casefold():
                raise ValueError(
                    f"Unresolved disputed Factbook formal name for {code}"
                )
            if formal_name is None:
                formal_name = row["conventional_short_name"]
                name_status = "same_as_short"
            else:
                name_status = "source_provided"
            source_id = "cia-world-factbook-2025"
            source_record_id = row["source_path"]
            source_locator = row["source_locator"]

        if not formal_name:
            raise ValueError(f"Missing formal-name fallback for {code} in {factbook_path}")
        if unicodedata.normalize("NFC", formal_name) != formal_name:
            raise ValueError(f"Formal name is not Unicode NFC for {code}")
        records.append({
            "country_code": code,
            "source_id": source_id,
            "source_record_id": source_record_id,
            "retrieved_at": "2026-07-21",
            "data": {
                "formal_name": formal_name,
                "formal_name_status": name_status,
                "source_locator": source_locator,
            },
        })

    if applied_overrides != set(overrides):
        raise ValueError(
            f"Unused formal-name overrides: {sorted(set(overrides) - applied_overrides)}"
        )
    gaps = country_codes - seen
    if gaps != EXPECTED_ENGLISH_FORMAL_NAME_GAPS:
        raise ValueError(
            "Unexpected English formal-name scope; "
            f"missing={sorted(gaps)}, expected={sorted(EXPECTED_ENGLISH_FORMAL_NAME_GAPS)}"
        )
    return records


def parse_factbook_reference_facts(
    root: Path, country_codes: set[str]
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    """Read anthem titles and English demonyms from the compact Factbook layer."""
    path = root / "build_data/raw/cia-world-factbook/2025/country_identity.json"
    snapshot = _load_json(path)
    rows = snapshot.get("records")
    if not isinstance(rows, list) or len(rows) != EXPECTED_ENGLISH_FORMAL_NAME_COUNT:
        raise ValueError(f"Unexpected Factbook reference scope in {path}")
    anthems: list[dict[str, object]] = []
    demonyms: list[dict[str, object]] = []
    for row in rows:
        code = row["country_code"].upper()
        if code not in country_codes:
            raise ValueError(f"Unknown country code in {path}: {code}")
        locators = row.get("source_locators", {})
        anthem_title = row.get("anthem_title")
        if anthem_title:
            if unicodedata.normalize("NFC", anthem_title) != anthem_title:
                raise ValueError(f"Anthem title is not Unicode NFC for {code}")
            anthems.append({
                "country_code": code,
                "source_id": "cia-world-factbook-2025",
                "source_record_id": row["source_path"],
                "retrieved_at": "2026-07-21",
                "data": {
                    "title": anthem_title,
                    "english_title": row.get("anthem_english_title"),
                    "source_text": row.get("anthem_source_text"),
                    "source_locator": locators.get(
                        "anthem", "Government > National anthem(s) > title"
                    ),
                },
            })
        noun = row.get("demonym_noun")
        adjective = row.get("demonym_adjective")
        if noun or adjective:
            demonyms.append({
                "country_code": code,
                "source_id": "cia-world-factbook-2025",
                "source_record_id": row["source_path"],
                "retrieved_at": "2026-07-21",
                "data": {
                    "noun": noun,
                    "adjective": adjective,
                    "language_code": "en",
                    "source_locator": locators.get(
                        "demonym", "People and Society > Nationality"
                    ),
                },
            })
    if len(anthems) != EXPECTED_ANTHEM_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_ANTHEM_COUNT} anthem records, found {len(anthems)}"
        )
    if len(demonyms) != EXPECTED_DEMONYM_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_DEMONYM_COUNT} demonym records, found {len(demonyms)}"
        )
    return anthems, demonyms


def parse_factbook_physical_geography(
    root: Path, country_codes: set[str]
) -> list[dict[str, object]]:
    """Read structured physical facts from the compact Factbook snapshot."""
    path = root / "build_data/raw/cia-world-factbook/2025/country_identity.json"
    snapshot = _load_json(path)
    rows = snapshot.get("records")
    if not isinstance(rows, list) or len(rows) != EXPECTED_PHYSICAL_PROFILE_COUNT:
        raise ValueError(f"Unexpected Factbook physical scope in {path}")
    records: list[dict[str, object]] = []
    seen: set[str] = set()
    for row in rows:
        code = row["country_code"].upper()
        if code not in country_codes or code in seen:
            raise ValueError(f"Unknown or duplicate country code in {path}: {code}")
        physical = row.get("physical_geography")
        if not isinstance(physical, dict):
            raise ValueError(f"Missing physical-geography object for {code}")
        for point_name in ("highest_point", "lowest_point"):
            point = physical.get(point_name)
            if point is not None and (
                not point.get("name")
                or not isinstance(point.get("elevation_m"), (int, float))
                or not point.get("source_label")
            ):
                raise ValueError(f"Invalid {point_name} for {code}")
        for collection, feature_type in (("rivers", "river"), ("lakes", "lake")):
            features = physical.get(collection)
            if not isinstance(features, list):
                raise ValueError(f"Invalid {collection} collection for {code}")
            feature_names: set[str] = set()
            for feature in features:
                name = feature.get("name")
                if (
                    not name
                    or feature.get("feature_type") != feature_type
                    or not feature.get("source_label")
                    or name.casefold() in feature_names
                ):
                    raise ValueError(f"Invalid or duplicate {collection} record for {code}")
                feature_names.add(name.casefold())
        seen.add(code)
        locators = row.get("source_locators", {})
        records.append({
            "country_code": code,
            "source_id": "cia-world-factbook-2025",
            "source_record_id": row["source_path"],
            "retrieved_at": "2026-07-22",
            "data": {
                **physical,
                "source_locator": locators.get("physical_geography", "Geography"),
                "source_locators": {
                    name: locators.get(name)
                    for name in (
                        "area", "coastline", "climate", "elevation", "lakes", "rivers"
                    )
                },
            },
        })

    checks = {
        "total area": (
            sum(record["data"]["total_area_km2"] is not None for record in records),
            EXPECTED_PHYSICAL_TOTAL_AREA_COUNT,
        ),
        "land area": (
            sum(record["data"]["land_area_km2"] is not None for record in records),
            EXPECTED_PHYSICAL_LAND_AREA_COUNT,
        ),
        "water area": (
            sum(record["data"]["water_area_km2"] is not None for record in records),
            EXPECTED_PHYSICAL_WATER_AREA_COUNT,
        ),
        "coastline": (
            sum(record["data"]["coastline_km"] is not None for record in records),
            EXPECTED_COASTLINE_COUNT,
        ),
        "highest point": (
            sum(record["data"]["highest_point"] is not None for record in records),
            EXPECTED_ELEVATION_EXTREME_COUNT,
        ),
        "lowest point": (
            sum(record["data"]["lowest_point"] is not None for record in records),
            EXPECTED_ELEVATION_EXTREME_COUNT,
        ),
        "mean elevation": (
            sum(record["data"]["mean_elevation_m"] is not None for record in records),
            EXPECTED_MEAN_ELEVATION_COUNT,
        ),
        "climate summary": (
            sum(record["data"]["climate_summary"] is not None for record in records),
            EXPECTED_CLIMATE_SUMMARY_COUNT,
        ),
        "river profiles": (
            sum(bool(record["data"]["rivers"]) for record in records),
            EXPECTED_RIVER_PROFILE_COUNT,
        ),
        "rivers": (
            sum(len(record["data"]["rivers"]) for record in records),
            EXPECTED_RIVER_COUNT,
        ),
        "lake profiles": (
            sum(bool(record["data"]["lakes"]) for record in records),
            EXPECTED_LAKE_PROFILE_COUNT,
        ),
        "lakes": (
            sum(len(record["data"]["lakes"]) for record in records),
            EXPECTED_LAKE_COUNT,
        ),
    }
    failures = {
        name: {"found": found, "expected": expected}
        for name, (found, expected) in checks.items()
        if found != expected
    }
    if failures:
        raise ValueError(f"Factbook physical coverage changed: {failures}")
    return records


def parse_koppen_climate_profiles(
    root: Path, country_codes: set[str]
) -> list[dict[str, object]]:
    """Read reviewed country classifications derived from the pinned CC0 map."""
    path = root / "build_data/raw/koppen-geiger/2023/country_zones.json"
    snapshot = _load_json(path)
    if snapshot.get("source_id") != "koppen-geiger-1991-2020":
        raise ValueError(f"Unexpected Köppen-Geiger source identifier in {path}")
    rows = snapshot.get("records")
    if not isinstance(rows, list) or len(rows) != EXPECTED_KOPPEN_PROFILE_COUNT:
        raise ValueError(f"Unexpected Köppen-Geiger profile scope in {path}")
    if set(snapshot.get("coverage_gaps", [])) != EXPECTED_KOPPEN_GAPS:
        raise ValueError(f"Unexpected Köppen-Geiger coverage gaps in {path}")
    records: list[dict[str, object]] = []
    seen: set[str] = set()
    valid_groups = {"Tropical", "Arid", "Temperate", "Cold", "Polar"}
    for row in rows:
        code = row["country_code"].upper()
        zones = row.get("zones")
        if code not in country_codes or code in seen or not isinstance(zones, list) or not zones:
            raise ValueError(f"Invalid Köppen-Geiger profile for {code}")
        previous = float("inf")
        zone_codes: set[str] = set()
        for zone in zones:
            share = zone.get("share_percent")
            zone_code = zone.get("code")
            if (
                not isinstance(share, (int, float))
                or share < snapshot["minimum_share_percent"]
                or share > previous
                or not isinstance(zone_code, str)
                or re.fullmatch(r"[A-E][A-Za-z]{1,2}", zone_code) is None
                or zone_code in zone_codes
                or zone.get("group") not in valid_groups
                or not zone.get("name")
            ):
                raise ValueError(f"Invalid Köppen-Geiger zone for {code}: {zone}")
            previous = share
            zone_codes.add(zone_code)
        if row.get("dominant_code") != zones[0]["code"]:
            raise ValueError(f"Dominant Köppen-Geiger code is not first for {code}")
        seen.add(code)
        records.append({
            "country_code": code,
            "source_id": "koppen-geiger-1991-2020",
            "source_record_id": row["source_record_id"],
            "retrieved_at": "2026-07-22",
            "data": {
                "zones": zones,
                "dominant_code": row["dominant_code"],
                "represented_share_percent": row["represented_share_percent"],
                "reference_period": "1991-2020",
                "resolution_degrees": snapshot["resolution_degrees"],
                "minimum_share_percent": snapshot["minimum_share_percent"],
                "source_locator": row["source_locator"],
            },
        })
    if country_codes - seen != EXPECTED_KOPPEN_GAPS:
        raise ValueError(
            "Köppen-Geiger runtime scope mismatch; "
            f"missing={sorted(country_codes - seen)}"
        )
    return records


def parse_reviewed_mottos(
    root: Path, country_codes: set[str]
) -> list[dict[str, object]]:
    """Apply explicit decisions to the captured Wikidata motto statements."""
    snapshot_path = root / "build_data/raw/wikidata/2026-07-22/national-mottos.json"
    bindings = _load_json(snapshot_path)["results"]["bindings"]
    statements: dict[str, dict[str, object]] = {}
    for row in bindings:
        code = row["alpha2"]["value"].upper()
        if code not in country_codes or row["rank"]["value"].endswith("DeprecatedRank"):
            continue
        statement_id = row["statement"]["value"].rsplit("/", 1)[-1]
        item_id = row["mottoItem"]["value"].rsplit("/", 1)[-1]
        statement = statements.setdefault(statement_id, {
            "country_code": code,
            "item_id": item_id,
            "rank": row["rank"]["value"].rsplit("#", 1)[-1],
            "labels": {},
        })
        if statement["country_code"] != code or statement["item_id"] != item_id:
            raise ValueError(f"Inconsistent Wikidata motto statement: {statement_id}")
        language = row["motto"].get("xml:lang")
        if language:
            statement["labels"][language.casefold()] = row["motto"]["value"]

    decision_path = root / "build_data/reviewed/national_motto_decisions.csv"
    decisions: dict[str, dict[str, str]] = {}
    with decision_path.open(encoding="utf-8", newline="") as stream:
        for line_number, row in enumerate(csv.DictReader(stream), 2):
            statement_id = row["statement_id"]
            statement = statements.get(statement_id)
            if statement is None:
                raise ValueError(
                    f"Unknown motto statement on {decision_path}:{line_number}"
                )
            if statement_id in decisions or row["decision"] not in {"include", "exclude"}:
                raise ValueError(
                    f"Duplicate or invalid motto decision on {decision_path}:{line_number}"
                )
            if (
                statement["country_code"] != row["country_code"].upper()
                or statement["item_id"] != row["motto_item_id"]
                or not row["review_note"]
            ):
                raise ValueError(
                    f"Motto decision mismatch on {decision_path}:{line_number}"
                )
            decisions[statement_id] = row
    if set(decisions) != set(statements):
        raise ValueError(
            "Motto decisions do not cover the captured source statements; "
            f"missing={sorted(set(statements) - set(decisions))}, "
            f"stale={sorted(set(decisions) - set(statements))}"
        )

    records: list[dict[str, object]] = []
    for statement_id, decision in sorted(decisions.items()):
        if decision["decision"] == "exclude":
            continue
        statement = statements[statement_id]
        language_code = decision["preferred_language_code"].casefold()
        labels = statement["labels"]
        text = labels.get(language_code)
        if text is None:
            raise ValueError(
                f"Missing reviewed motto label {language_code!r} for {statement_id}"
            )
        records.append({
            "country_code": statement["country_code"],
            "source_id": "wikidata-national-mottos-2026-07-22",
            "source_record_id": statement_id,
            "retrieved_at": "2026-07-22",
            "data": {
                "text": text,
                "english_text": labels.get("en"),
                "language_code": language_code,
                "motto_item_id": statement["item_id"],
                "source_locator": f"Wikidata statement {statement_id}",
            },
        })
    if len(records) != EXPECTED_MOTTO_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_MOTTO_COUNT} reviewed mottos, found {len(records)}"
        )
    return records


def parse_reference_metadata(
    root: Path,
    country_codes: set[str],
    geonames_countries: dict[str, dict[str, object]],
) -> tuple[dict[str, dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    """Read CLDR currency/language metadata and complete GeoNames timezones."""
    reference_path = root / "build_data/raw/unicode-cldr/48.2/country_reference.json"
    snapshot = _load_json(reference_path)
    if snapshot.get("source_id") != "unicode-cldr-48.2-reference":
        raise ValueError(f"Unexpected CLDR reference source in {reference_path}")
    currencies = {row["code"]: row for row in snapshot["currencies"]}
    languages = {row["code"]: row for row in snapshot["languages"]}

    country_currencies: dict[str, dict[str, object]] = {}
    language_records: list[dict[str, object]] = []
    for code in sorted(country_codes):
        country = geonames_countries[code]
        currency_code = country["data"]["currency_code"]
        if currency_code:
            metadata = currencies.get(currency_code)
            if metadata is None:
                raise ValueError(f"Missing CLDR currency metadata for {currency_code}")
            country_currencies[code] = metadata
        for language_code in country["data"]["language_codes"]:
            metadata = languages.get(language_code)
            if metadata is None or metadata["name"] is None:
                raise ValueError(
                    f"Missing language metadata for {code}:{language_code}"
                )
            language_records.append({
                "country_code": code,
                "source_id": metadata["name_source_id"],
                "source_record_id": metadata["primary_code"],
                "retrieved_at": "2026-07-22",
                "data": metadata,
            })

    timezone_path = root / "build_data/raw/geonames/2026-07-22/timeZones.txt"
    timezone_records: list[dict[str, object]] = []
    with timezone_path.open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream, delimiter="\t"):
            code = row["CountryCode"].upper()
            if code not in country_codes:
                continue
            timezone_records.append({
                "country_code": code,
                "source_id": "geonames-timezones-2026-07-22",
                "source_record_id": row["TimeZoneId"],
                "retrieved_at": "2026-07-22",
                "data": {
                    "timezone_id": row["TimeZoneId"],
                    "january_utc_offset_hours": float(row["GMT offset 1. Jan 2026"]),
                    "july_utc_offset_hours": float(row["DST offset 1. Jul 2026"]),
                    "raw_utc_offset_hours": float(row["rawOffset (independant of DST)"]),
                },
            })
    timezone_countries = {record["country_code"] for record in timezone_records}
    if len(timezone_countries) != EXPECTED_TIMEZONE_COUNTRY_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_TIMEZONE_COUNTRY_COUNT} timezone profiles, "
            f"found {len(timezone_countries)}"
        )
    return country_currencies, language_records, timezone_records


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
    formal_names = parse_english_formal_names(root, set(un))
    anthems, demonyms = parse_factbook_reference_facts(root, set(un))
    physical_profiles = parse_factbook_physical_geography(root, set(un))
    climate_profiles = parse_koppen_climate_profiles(root, set(un))
    mottos = parse_reviewed_mottos(root, set(un))
    currency_metadata, language_profiles, timezones = parse_reference_metadata(
        root, set(un), geocountries
    )
    formal_names_by_country = {
        record["country_code"]: record for record in formal_names
    }
    physical_by_country = {
        record["country_code"]: record for record in physical_profiles
    }
    borders = parse_land_borders(root, un, geocountries)
    countries = []
    names = []
    capitals = []
    for code in sorted(un):
        u, g = un[code], geocountries[code]
        data = dict(u["data"])
        data.update({
            "name": common.get(code, g["data"]["name"]),
            "area_km2": (
                physical_by_country[code]["data"]["total_area_km2"]
                if code in physical_by_country
                and physical_by_country[code]["data"]["total_area_km2"] is not None
                else g["data"]["area_km2"]
            ),
            "population": g["data"]["population"],
            "top_level_domain": g["data"]["top_level_domain"],
            "currency_code": g["data"]["currency_code"],
            "currency_name": (
                currency_metadata[code]["name"]
                if code in currency_metadata
                else g["data"]["currency_name"]
            ),
            "currency_symbol": (
                currency_metadata[code]["symbol"]
                if code in currency_metadata
                else None
            ),
            "currency_minor_unit_digits": (
                currency_metadata[code]["minor_unit_digits"]
                if code in currency_metadata
                else None
            ),
            "calling_codes": g["data"]["calling_codes"],
            "postal_code_format": g["data"]["postal_code_format"],
            "postal_code_regex": g["data"]["postal_code_regex"],
            "language_codes": g["data"]["language_codes"],
            "geonames_id": g["data"]["geonames_id"],
        })
        formal_record = formal_names_by_country.get(code)
        if formal_record is None:
            data.update({
                "formal_name": None,
                "formal_name_status": "not_in_source_scope",
                "formal_name_source_id": None,
                "formal_name_source_record_id": None,
            })
        else:
            data.update({
                "formal_name": formal_record["data"]["formal_name"],
                "formal_name_status": formal_record["data"]["formal_name_status"],
                "formal_name_source_id": formal_record["source_id"],
                "formal_name_source_record_id": formal_record["source_record_id"],
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
        if formal_record is not None:
            formal_name = formal_record["data"]["formal_name"]
            names.append({
                "country_code": code,
                "source_id": formal_record["source_id"],
                "source_record_id": formal_record["source_record_id"],
                "retrieved_at": formal_record["retrieved_at"],
                "data": {
                    "name": formal_name,
                    "normalized_name": normalize_name(formal_name),
                    "kind": "formal",
                    "preferred": False,
                },
            })
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
        "formal_names": formal_names,
        "anthems": anthems,
        "mottos": mottos,
        "demonyms": demonyms,
        "physical_profiles": physical_profiles,
        "climate_profiles": climate_profiles,
        "language_profiles": language_profiles,
        "timezones": timezones,
        "capitals": capitals,
        "cities": cities,
        "borders": borders,
    }
    output = root / "build_data/normalized"
    output.mkdir(parents=True, exist_ok=True)
    for key, records in normalized.items():
        (output / f"{key}.jsonl").write_text(
            "".join(
                json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
                for row in records
            ),
            encoding="utf-8",
            newline="\n",
        )
    return normalized


SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE schema_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL) WITHOUT ROWID;
CREATE TABLE source (id TEXT PRIMARY KEY, name TEXT NOT NULL, homepage TEXT NOT NULL, version TEXT, retrieved_at TEXT NOT NULL, license_name TEXT, license_url TEXT, checksum_sha256 TEXT, notes TEXT) WITHOUT ROWID;
CREATE TABLE country (id INTEGER PRIMARY KEY, alpha2 TEXT NOT NULL UNIQUE, alpha3 TEXT UNIQUE, numeric_code TEXT UNIQUE, name TEXT NOT NULL, official_name TEXT, continent TEXT, region TEXT, subregion TEXT, geonames_id INTEGER, total_area_km2 REAL, population INTEGER, top_level_domain TEXT, currency_code TEXT, currency_name TEXT, currency_symbol TEXT, currency_minor_unit_digits INTEGER, postal_code_format TEXT, postal_code_regex TEXT, calling_codes TEXT NOT NULL, language_codes TEXT NOT NULL);
CREATE TABLE country_border (country1_id INTEGER NOT NULL, country2_id INTEGER NOT NULL, review_status TEXT NOT NULL, evidence_sources TEXT NOT NULL, review_note TEXT, PRIMARY KEY(country1_id,country2_id), FOREIGN KEY(country1_id) REFERENCES country(id), FOREIGN KEY(country2_id) REFERENCES country(id), CHECK(country1_id < country2_id)) WITHOUT ROWID;
CREATE INDEX idx_country_border_second ON country_border(country2_id);
CREATE TABLE country_name (country_id INTEGER NOT NULL, name TEXT NOT NULL, normalized_name TEXT NOT NULL, language_code TEXT, kind TEXT NOT NULL, preferred INTEGER NOT NULL DEFAULT 0, PRIMARY KEY(country_id,name,kind), FOREIGN KEY(country_id) REFERENCES country(id));
CREATE INDEX idx_country_name_normalized ON country_name(normalized_name);
CREATE TABLE country_local_name (country_id INTEGER NOT NULL, language_code TEXT NOT NULL, language_name TEXT NOT NULL, script_code TEXT NOT NULL, short_name TEXT NOT NULL, name_kind TEXT NOT NULL CHECK(name_kind IN ('national_official','locale_display')), official_name TEXT, romanized_short_name TEXT, romanized_official_name TEXT, is_official_language INTEGER NOT NULL, language_status TEXT NOT NULL, source_id TEXT NOT NULL, source_locator TEXT NOT NULL, PRIMARY KEY(country_id,language_code), FOREIGN KEY(country_id) REFERENCES country(id), FOREIGN KEY(source_id) REFERENCES source(id)) WITHOUT ROWID;
CREATE INDEX idx_country_local_name_country ON country_local_name(country_id);
CREATE TABLE country_anthem (country_id INTEGER NOT NULL, title TEXT NOT NULL, english_title TEXT, source_text TEXT, source_id TEXT NOT NULL, source_record_id TEXT NOT NULL, source_locator TEXT NOT NULL, PRIMARY KEY(country_id,title), FOREIGN KEY(country_id) REFERENCES country(id), FOREIGN KEY(source_id) REFERENCES source(id)) WITHOUT ROWID;
CREATE TABLE country_motto (country_id INTEGER NOT NULL, text TEXT NOT NULL, english_text TEXT, language_code TEXT NOT NULL, motto_item_id TEXT NOT NULL, source_id TEXT NOT NULL, source_record_id TEXT NOT NULL, source_locator TEXT NOT NULL, PRIMARY KEY(country_id,source_record_id), FOREIGN KEY(country_id) REFERENCES country(id), FOREIGN KEY(source_id) REFERENCES source(id)) WITHOUT ROWID;
CREATE TABLE country_demonym (country_id INTEGER NOT NULL, noun TEXT, adjective TEXT, language_code TEXT NOT NULL, source_id TEXT NOT NULL, source_record_id TEXT NOT NULL, source_locator TEXT NOT NULL, PRIMARY KEY(country_id,language_code), FOREIGN KEY(country_id) REFERENCES country(id), FOREIGN KEY(source_id) REFERENCES source(id)) WITHOUT ROWID;
CREATE TABLE country_language (country_id INTEGER NOT NULL, code TEXT NOT NULL, primary_code TEXT NOT NULL, name TEXT NOT NULL, script_code TEXT, source_id TEXT NOT NULL, source_locator TEXT NOT NULL, PRIMARY KEY(country_id,code), FOREIGN KEY(country_id) REFERENCES country(id), FOREIGN KEY(source_id) REFERENCES source(id)) WITHOUT ROWID;
CREATE TABLE country_timezone (country_id INTEGER NOT NULL, timezone_id TEXT NOT NULL, january_utc_offset_hours REAL NOT NULL, july_utc_offset_hours REAL NOT NULL, raw_utc_offset_hours REAL NOT NULL, source_id TEXT NOT NULL, PRIMARY KEY(country_id,timezone_id), FOREIGN KEY(country_id) REFERENCES country(id), FOREIGN KEY(source_id) REFERENCES source(id)) WITHOUT ROWID;
CREATE TABLE country_physical (country_id INTEGER PRIMARY KEY, land_area_km2 REAL, water_area_km2 REAL, coastline_km REAL, mean_elevation_m REAL, highest_point_name TEXT, highest_point_elevation_m REAL, highest_point_is_approximate INTEGER, highest_point_source_label TEXT, lowest_point_name TEXT, lowest_point_elevation_m REAL, lowest_point_is_approximate INTEGER, lowest_point_source_label TEXT, climate_summary TEXT, source_id TEXT NOT NULL, source_record_id TEXT NOT NULL, source_locator TEXT NOT NULL, FOREIGN KEY(country_id) REFERENCES country(id), FOREIGN KEY(source_id) REFERENCES source(id)) WITHOUT ROWID;
CREATE TABLE country_river (country_id INTEGER NOT NULL, name TEXT NOT NULL, length_km REAL, source_label TEXT NOT NULL, source_id TEXT NOT NULL, source_locator TEXT NOT NULL, PRIMARY KEY(country_id,name), FOREIGN KEY(country_id) REFERENCES country(id), FOREIGN KEY(source_id) REFERENCES source(id)) WITHOUT ROWID;
CREATE TABLE country_lake (country_id INTEGER NOT NULL, name TEXT NOT NULL, area_km2 REAL, water_type TEXT, source_label TEXT NOT NULL, source_id TEXT NOT NULL, source_locator TEXT NOT NULL, PRIMARY KEY(country_id,name), FOREIGN KEY(country_id) REFERENCES country(id), FOREIGN KEY(source_id) REFERENCES source(id)) WITHOUT ROWID;
CREATE TABLE country_climate_zone (country_id INTEGER NOT NULL, code TEXT NOT NULL, name TEXT NOT NULL, climate_group TEXT NOT NULL, share_percent REAL NOT NULL, position INTEGER NOT NULL, reference_period TEXT NOT NULL, resolution_degrees REAL NOT NULL, minimum_share_percent REAL NOT NULL, source_id TEXT NOT NULL, source_locator TEXT NOT NULL, PRIMARY KEY(country_id,code), FOREIGN KEY(country_id) REFERENCES country(id), FOREIGN KEY(source_id) REFERENCES source(id)) WITHOUT ROWID;
CREATE TABLE capital (id INTEGER PRIMARY KEY, country_id INTEGER NOT NULL, name TEXT NOT NULL, normalized_name TEXT NOT NULL, role TEXT NOT NULL, is_primary INTEGER NOT NULL, latitude REAL NOT NULL, longitude REAL NOT NULL, population INTEGER, elevation_m REAL, timezone_id TEXT, geonames_id INTEGER UNIQUE, FOREIGN KEY(country_id) REFERENCES country(id));
CREATE TABLE city (id INTEGER PRIMARY KEY, country_id INTEGER NOT NULL, name TEXT NOT NULL, normalized_name TEXT NOT NULL, latitude REAL NOT NULL, longitude REAL NOT NULL, population INTEGER, elevation_m REAL, timezone_id TEXT, geonames_id INTEGER UNIQUE, is_capital INTEGER NOT NULL DEFAULT 0, FOREIGN KEY(country_id) REFERENCES country(id));
CREATE INDEX idx_city_country ON city(country_id);
CREATE TABLE field_source (country_id INTEGER NOT NULL, field_path TEXT NOT NULL, source_id TEXT NOT NULL, source_record_id TEXT, PRIMARY KEY(country_id,field_path), FOREIGN KEY(country_id) REFERENCES country(id), FOREIGN KEY(source_id) REFERENCES source(id)) WITHOUT ROWID;
"""


def build_database(
    root: Path,
    normalized: dict[str, object],
    *,
    install: bool = True,
) -> Path:
    """Build the deterministic SQLite database and optionally install it."""
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
    meta = {"schema_version": "7", "dataset_version": "2026.07.22.7", "library_version": library_version, "built_at": built_at}
    con.executemany("INSERT INTO schema_meta VALUES (?,?)", sorted(meta.items()))
    sources = [
        ("geonames", "GeoNames", "https://www.geonames.org/", "2026-07-20", "2026-07-20", "CC BY 4.0", "https://creativecommons.org/licenses/by/4.0/", _sha(root / "build_data/raw/geonames/2026-07-20/manifest.json"), "Country metadata and populated places"),
        ("natural-earth", "Natural Earth", "https://www.naturalearthdata.com/", "5.1.0/5.1.1", "2026-07-21", "Public domain", "https://www.naturalearthdata.com/about/terms-of-use/", _sha(root / "build_data/raw/natural-earth/2026-07-21/manifest.json"), "Map-unit topology used to cross-check land-border relationships"),
        ("reviewed-borders", "PyWorldAtlas reviewed border decisions", "https://jcari-dev.github.io/pyworldatlas-documentation/borders.html", library_version, "2026-07-21", "MIT", None, _sha(root / "build_data/reviewed/border_decisions.csv"), "Explicit decisions for every difference between the pinned GeoNames and Natural Earth border inputs"),
        ("reviewed-overrides", "PyWorldAtlas reviewed overrides", "https://jcari-dev.github.io/pyworldatlas-documentation/", library_version, "2026-07-20", "MIT", None, _sha(root / "pipeline/config/overrides.json"), "Reviewed familiar names and aliases"),
        ("un-m49", "United Nations M49", "https://unstats.un.org/unsd/methodology/m49/", "2026-07-20", "2026-07-20", None, None, _sha(root / "build_data/raw/un-m49/2026-07-20/manifest.json"), "Canonical identities and regions"),
        ("ungegn-country-names-2017", "UNGEGN List of Country Names", "https://unstats.un.org/unsd/ungegn/working_groups/wg1.cshtml", "E/CONF.105/13/CRP.13 (2017-07-17)", "2026-07-20", None, None, _sha(root / "build_data/raw/ungegn-country-names/2017-07-17/manifest.json"), "Approved national official short and formal country names; reviewed entries transcribed with page locators"),
        ("unicode-cldr-48.2", "Unicode Common Locale Data Repository", "https://cldr.unicode.org/", "48.2", "2026-07-21", "Unicode License v3", "https://www.unicode.org/license.txt", _sha(root / "build_data/raw/unicode-cldr/48.2/manifest.json"), "Localized territory display names and official-language metadata used for complete local identity coverage"),
        ("cia-world-factbook-2025", "CIA World Factbook structured country profiles", "https://www.cia.gov/the-world-factbook/", "factbook.json@8662a8b17a784841ab4528631b04090eb2f183eb", "2026-07-22", "Public domain", "https://www.cia.gov/site-policies/", _sha(root / "build_data/raw/cia-world-factbook/2025/manifest.json"), "Country names, anthem titles, English nationality terms, and structured physical-geography fields; no lyrics or political narrative"),
        ("koppen-geiger-1991-2020", "Beck et al. Köppen-Geiger climate classification maps", "https://www.gloh2o.org/koppen/", "1991-2020 historical climatology; dataset version 1", "2026-07-22", "CC0 1.0", "https://creativecommons.org/publicdomain/zero/1.0/", _sha(root / "build_data/raw/koppen-geiger/2023/manifest.json"), "Area-weighted country climate-zone shares derived from the 0.1-degree source raster and pinned Natural Earth map units"),
        ("wikidata-official-names-2026-07-21", "Wikidata official-name statements", "https://www.wikidata.org/", "2026-07-21 query snapshot", "2026-07-21", "CC0 1.0", "https://www.wikidata.org/wiki/Wikidata:Licensing", _sha(root / "build_data/raw/wikidata/2026-07-21/manifest.json"), "Three reviewed English formal-name statements used where the public-domain Factbook differs from current UN usage"),
        ("un-protocol-country-names-2025", "UN Protocol official names of United Nations membership", "https://www.un.org/dgacm/en/content/protocol", "2025-02-05", "2026-07-21", "Credited excerpts under UN reuse guidance", "https://shop.un.org/rights-permissions", _sha(root / "build_data/raw/un-protocol/2025-02-05/manifest.json"), "Five short English formal-name excerpts used to resolve current-name differences; source PDF is not redistributed"),
        ("unicode-cldr-48.2-reference", "Unicode CLDR currency and language metadata", "https://cldr.unicode.org/", "48.2", "2026-07-22", "Unicode License v3", "https://www.unicode.org/license.txt", _sha(root / "build_data/raw/unicode-cldr/48.2/manifest.json"), "English currency names and symbols, minor-unit digits, language names, and likely scripts"),
        ("iana-language-subtags-2026-06-14", "IANA Language Subtag Registry", "https://www.iana.org/assignments/language-subtag-registry/", "File-Date 2026-06-14", "2026-07-22", "CC0 1.0", "https://www.iana.org/help/licensing-terms", _sha(root / "build_data/raw/iana/2026-07-22/manifest.json"), "Fallback names for registered language subtags not labelled by CLDR"),
        ("geonames-timezones-2026-07-22", "GeoNames timezone table", "https://download.geonames.org/export/dump/", "2026-07-22", "2026-07-22", "CC BY 4.0", "https://creativecommons.org/licenses/by/4.0/", _sha(root / "build_data/raw/geonames/2026-07-22/manifest.json"), "Country timezone identifiers and January, July, and raw UTC offsets"),
        ("wikidata-national-mottos-2026-07-22", "Wikidata national-motto statements", "https://www.wikidata.org/", "2026-07-22 query snapshot", "2026-07-22", "CC0 1.0", "https://www.wikidata.org/wiki/Wikidata:Licensing", _sha(root / "build_data/raw/wikidata/2026-07-22/manifest.json"), "Reviewed national-motto item statements and selected labels"),
        ("reviewed-national-mottos", "PyWorldAtlas reviewed motto decisions", "https://jcari-dev.github.io/pyworldatlas-documentation/country_reference.html", library_version, "2026-07-22", "MIT", None, _sha(root / "build_data/reviewed/national_motto_decisions.csv"), "Explicit inclusion and exclusion decisions for every captured motto statement"),
    ]
    con.executemany("INSERT INTO source VALUES (?,?,?,?,?,?,?,?,?)", sources)
    anthem_codes = {record["country_code"] for record in normalized["anthems"]}
    demonym_codes = {record["country_code"] for record in normalized["demonyms"]}
    motto_codes = {record["country_code"] for record in normalized["mottos"]}
    timezone_codes = {record["country_code"] for record in normalized["timezones"]}
    language_sources: dict[str, set[str]] = defaultdict(set)
    for record in normalized["language_profiles"]:
        language_sources[record["country_code"]].add(record["source_id"])
    physical_by_code = {
        record["country_code"]: record for record in normalized["physical_profiles"]
    }
    climate_by_code = {
        record["country_code"]: record for record in normalized["climate_profiles"]
    }

    ids: dict[str, int] = {}
    for ident, record in enumerate(sorted(normalized["countries"], key=lambda r: r["country_code"]), 1):
        code, data = record["country_code"], record["data"]
        ids[code] = ident
        con.execute("INSERT INTO country VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (ident, code, data["alpha3"], data["numeric_code"], data["name"], data["official_name"], data["continent"], data["region"], data["subregion"], data["geonames_id"], data["area_km2"], data["population"], data["top_level_domain"], data["currency_code"], data["currency_name"], data["currency_symbol"], data["currency_minor_unit_digits"], data["postal_code_format"], data["postal_code_regex"], json.dumps(data["calling_codes"], ensure_ascii=False), json.dumps(data["language_codes"], ensure_ascii=False)))
        field_sources = [
            (ident, "identity", "un-m49", data["numeric_code"]),
            (ident, "capitals", "geonames", str(data["geonames_id"])),
            (ident, "major_cities", "geonames", str(data["geonames_id"])),
            (ident, "land_borders.geonames", "geonames", str(data["geonames_id"])),
            (ident, "land_borders.natural_earth", "natural-earth", "admin-0-map-units-50m"),
            (ident, "land_borders.review", "reviewed-borders", data["alpha2"]),
        ]
        if data["formal_name_source_id"] is not None:
            field_sources.append((
                ident,
                "formal_name",
                data["formal_name_source_id"],
                data["formal_name_source_record_id"],
            ))
        if any(name["country_code"] == code and name["source_id"] == "reviewed-overrides" for name in normalized["country_names"]):
            field_sources.append((ident, "names.reviewed", "reviewed-overrides", data["numeric_code"]))
        if data["postal_code_format"]:
            field_sources.append((ident, "postal_code", "geonames", str(data["geonames_id"])))
        if data["currency_code"]:
            field_sources.append((ident, "currency.metadata", "unicode-cldr-48.2-reference", data["currency_code"]))
        for language_source in sorted(language_sources[code]):
            field_sources.append((ident, f"languages.metadata.{language_source}", language_source, code))
        if code in timezone_codes:
            field_sources.append((ident, "timezones", "geonames-timezones-2026-07-22", code))
        if code in anthem_codes:
            field_sources.append((ident, "anthem", "cia-world-factbook-2025", code))
        if code in demonym_codes:
            field_sources.append((ident, "demonyms", "cia-world-factbook-2025", code))
        if code in physical_by_code:
            physical_record = physical_by_code[code]
            field_sources.append((
                ident,
                "physical_geography",
                "cia-world-factbook-2025",
                physical_record["source_record_id"],
            ))
        if code in climate_by_code:
            climate_record = climate_by_code[code]
            field_sources.append((
                ident,
                "physical_geography.climate.koppen_geiger",
                "koppen-geiger-1991-2020",
                climate_record["source_record_id"],
            ))
        if code in motto_codes:
            field_sources.extend([
                (ident, "mottos", "wikidata-national-mottos-2026-07-22", code),
                (ident, "mottos.review", "reviewed-national-mottos", code),
            ])
        local_record = next(
            name for name in normalized["local_names"] if name["country_code"] == code
        )
        field_sources.append(
            (
                ident,
                "local_names",
                local_record["source_id"],
                local_record["source_record_id"],
            )
        )
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
            "INSERT INTO country_local_name VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (ids[record["country_code"]], d["language_code"], d["language_name"], d["script_code"], d["short_name"], d["name_kind"], d["official_name"], d["romanized_short_name"], d["romanized_official_name"], int(d["is_official_language"]), d["language_status"], record["source_id"], d["source_locator"]),
        )
    for record in sorted(normalized["anthems"], key=lambda r: r["country_code"]):
        d = record["data"]
        con.execute(
            "INSERT INTO country_anthem VALUES (?,?,?,?,?,?,?)",
            (ids[record["country_code"]], d["title"], d["english_title"], d["source_text"], record["source_id"], record["source_record_id"], d["source_locator"]),
        )
    for record in sorted(normalized["mottos"], key=lambda r: (r["country_code"], r["source_record_id"])):
        d = record["data"]
        con.execute(
            "INSERT INTO country_motto VALUES (?,?,?,?,?,?,?,?)",
            (ids[record["country_code"]], d["text"], d["english_text"], d["language_code"], d["motto_item_id"], record["source_id"], record["source_record_id"], d["source_locator"]),
        )
    for record in sorted(normalized["demonyms"], key=lambda r: r["country_code"]):
        d = record["data"]
        con.execute(
            "INSERT INTO country_demonym VALUES (?,?,?,?,?,?,?)",
            (ids[record["country_code"]], d["noun"], d["adjective"], d["language_code"], record["source_id"], record["source_record_id"], d["source_locator"]),
        )
    for record in sorted(normalized["language_profiles"], key=lambda r: (r["country_code"], r["data"]["code"])):
        d = record["data"]
        con.execute(
            "INSERT INTO country_language VALUES (?,?,?,?,?,?,?)",
            (ids[record["country_code"]], d["code"], d["primary_code"], d["name"], d["script_code"], record["source_id"], d["source_locator"]),
        )
    for record in sorted(normalized["timezones"], key=lambda r: (r["country_code"], r["data"]["timezone_id"])):
        d = record["data"]
        con.execute(
            "INSERT INTO country_timezone VALUES (?,?,?,?,?,?)",
            (ids[record["country_code"]], d["timezone_id"], d["january_utc_offset_hours"], d["july_utc_offset_hours"], d["raw_utc_offset_hours"], record["source_id"]),
        )
    for record in sorted(normalized["physical_profiles"], key=lambda r: r["country_code"]):
        d = record["data"]
        highest, lowest = d["highest_point"], d["lowest_point"]
        con.execute(
            "INSERT INTO country_physical VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                ids[record["country_code"]],
                d["land_area_km2"],
                d["water_area_km2"],
                d["coastline_km"],
                d["mean_elevation_m"],
                highest["name"] if highest else None,
                highest["elevation_m"] if highest else None,
                int(highest["is_approximate"]) if highest else None,
                highest["source_label"] if highest else None,
                lowest["name"] if lowest else None,
                lowest["elevation_m"] if lowest else None,
                int(lowest["is_approximate"]) if lowest else None,
                lowest["source_label"] if lowest else None,
                d["climate_summary"],
                record["source_id"],
                record["source_record_id"],
                d["source_locator"],
            ),
        )
        for river in d["rivers"]:
            con.execute(
                "INSERT INTO country_river VALUES (?,?,?,?,?,?)",
                (
                    ids[record["country_code"]],
                    river["name"],
                    river["length_km"],
                    river["source_label"],
                    record["source_id"],
                    d["source_locators"]["rivers"],
                ),
            )
        for lake in d["lakes"]:
            con.execute(
                "INSERT INTO country_lake VALUES (?,?,?,?,?,?,?)",
                (
                    ids[record["country_code"]],
                    lake["name"],
                    lake["area_km2"],
                    lake["subtype"],
                    lake["source_label"],
                    record["source_id"],
                    d["source_locators"]["lakes"],
                ),
            )
    for record in sorted(normalized["climate_profiles"], key=lambda r: r["country_code"]):
        d = record["data"]
        for position, zone in enumerate(d["zones"], 1):
            con.execute(
                "INSERT INTO country_climate_zone VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (
                    ids[record["country_code"]],
                    zone["code"],
                    zone["name"],
                    zone["group"],
                    zone["share_percent"],
                    position,
                    d["reference_period"],
                    d["resolution_degrees"],
                    d["minimum_share_percent"],
                    record["source_id"],
                    d["source_locator"],
                ),
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
    if install:
        target = root / "src/pyworldatlas/data/atlas.sqlite3"
        target.write_bytes(path.read_bytes())
        return target
    return path


def report(root: Path, normalized: dict[str, object], database: Path) -> None:
    reports = root / "build_data/reports"
    reports.mkdir(parents=True, exist_ok=True)
    countries = normalized["countries"]
    coverage = {
        "dataset_version": "2026.07.22.7",
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
        "timezone_profiles": len({record["country_code"] for record in normalized["timezones"]}),
        "timezone_records": len(normalized["timezones"]),
        "postal_code_formats": sum(record["data"]["postal_code_format"] is not None for record in countries),
        "currency_symbols": sum(record["data"]["currency_symbol"] is not None for record in countries),
        "currency_minor_units": sum(record["data"]["currency_minor_unit_digits"] is not None for record in countries),
        "language_metadata_records": len(normalized["language_profiles"]),
        "language_metadata_countries": len({record["country_code"] for record in normalized["language_profiles"]}),
        "language_script_records": sum(record["data"]["script_code"] is not None for record in normalized["language_profiles"]),
        "anthem_titles": len(normalized["anthems"]),
        "anthem_countries": len({record["country_code"] for record in normalized["anthems"]}),
        "mottos": len(normalized["mottos"]),
        "motto_countries": len({record["country_code"] for record in normalized["mottos"]}),
        "demonyms": len(normalized["demonyms"]),
        "demonym_countries": len({record["country_code"] for record in normalized["demonyms"]}),
        "local_names": len(normalized["local_names"]),
        "local_name_countries": len({record["country_code"] for record in normalized["local_names"]}),
        "local_name_languages": len({record["data"]["language_code"] for record in normalized["local_names"]}),
        "local_name_scripts": len({record["data"]["script_code"] for record in normalized["local_names"]}),
        "romanized_local_names": sum(
            record["data"]["romanized_short_name"] is not None
            for record in normalized["local_names"]
        ),
        "national_official_local_names": sum(
            record["data"]["name_kind"] == "national_official"
            for record in normalized["local_names"]
        ),
        "locale_display_names": sum(
            record["data"]["name_kind"] == "locale_display"
            for record in normalized["local_names"]
        ),
        "official_language_local_names": sum(
            record["data"]["is_official_language"]
            for record in normalized["local_names"]
        ),
        "countries_without_local_names": sorted(
            {record["country_code"] for record in countries}
            - {record["country_code"] for record in normalized["local_names"]}
        ),
        "countries_without_official_language_local_names": sorted(
            record["country_code"]
            for record in normalized["local_names"]
            if not record["data"]["is_official_language"]
        ),
        "english_formal_names": len(normalized["formal_names"]),
        "distinct_english_formal_names": sum(
            record["data"]["formal_name_status"] == "source_provided"
            for record in normalized["formal_names"]
        ),
        "english_formal_names_same_as_short": sum(
            record["data"]["formal_name_status"] == "same_as_short"
            for record in normalized["formal_names"]
        ),
        "countries_without_english_formal_names": sorted(
            {record["country_code"] for record in countries}
            - {record["country_code"] for record in normalized["formal_names"]}
        ),
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
        "physical_profiles": len(normalized["physical_profiles"]),
        "physical_total_area_profiles": sum(
            record["data"]["total_area_km2"] is not None
            for record in normalized["physical_profiles"]
        ),
        "land_area_profiles": sum(
            record["data"]["land_area_km2"] is not None
            for record in normalized["physical_profiles"]
        ),
        "water_area_profiles": sum(
            record["data"]["water_area_km2"] is not None
            for record in normalized["physical_profiles"]
        ),
        "coastline_profiles": sum(
            record["data"]["coastline_km"] is not None
            for record in normalized["physical_profiles"]
        ),
        "mean_elevation_profiles": sum(
            record["data"]["mean_elevation_m"] is not None
            for record in normalized["physical_profiles"]
        ),
        "elevation_extreme_profiles": sum(
            record["data"]["highest_point"] is not None
            and record["data"]["lowest_point"] is not None
            for record in normalized["physical_profiles"]
        ),
        "river_profiles": sum(
            bool(record["data"]["rivers"])
            for record in normalized["physical_profiles"]
        ),
        "river_records": sum(
            len(record["data"]["rivers"])
            for record in normalized["physical_profiles"]
        ),
        "lake_profiles": sum(
            bool(record["data"]["lakes"])
            for record in normalized["physical_profiles"]
        ),
        "lake_records": sum(
            len(record["data"]["lakes"])
            for record in normalized["physical_profiles"]
        ),
        "climate_summary_profiles": sum(
            record["data"]["climate_summary"] is not None
            for record in normalized["physical_profiles"]
        ),
        "koppen_geiger_profiles": len(normalized["climate_profiles"]),
        "koppen_geiger_zone_records": sum(
            len(record["data"]["zones"])
            for record in normalized["climate_profiles"]
        ),
        "koppen_geiger_coverage_gaps": sorted(
            {record["country_code"] for record in countries}
            - {record["country_code"] for record in normalized["climate_profiles"]}
        ),
        "database_sha256": _sha(database),
        "validation": "PASS",
    }
    (reports / "coverage.json").write_text(
        json.dumps(coverage, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
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
        {
            "name": "3.1 — Border API and learning polish",
            "version": "0.3.1",
            "status": "complete",
            "functions": "Land-route reachability, path name/code conveniences, neighbor flashcards, and border-count flashcards",
            "tests": "Deterministic flashcard fixtures, reachability edge cases, examples, and complete release gate",
            "dataset": "No dataset change; derives from the 319 reviewed relationships",
            "docs": "API provenance, connectivity semantics, serialization, flashcards, and examples",
            "release": "Publication state is tracked on GitHub Releases and PyPI",
        },
        {
            "name": "4 — Official country identity",
            "version": "0.4.0",
            "status": "complete",
            "functions": "Complete local display names, English formal names, reviewed local official forms, language/script lookup, romanization, and coverage discovery",
            "tests": "30 unit/pipeline tests, 221 doctests, clean-wheel examples, and release audit passed",
            "dataset": f"{coverage['local_names']} local identities / {coverage['english_formal_names']} English formal names / {coverage['national_official_local_names']} reviewed local official forms",
            "docs": "Identity guide, fun multilingual examples, evidence levels, source rules, and complete coverage metrics",
            "release": "Included in published v0.5.0",
        },
        {
            "name": "5 — Educational scope and publication safety",
            "version": "0.5.0",
            "status": "complete",
            "functions": "Editorial policy, public-field scope audit, respectful contribution and correction process, and policy release checks",
            "tests": "Policy-document integrity, public-model scope, source-role, example-language, documentation, and release audits",
            "dataset": "Reviewed geographic dataset with updated provenance and policy metadata; no new narrative fields",
            "docs": "Educational purpose, source scope, geographic conventions, community standards, and correction guidance",
            "release": "Published as v0.5.0",
        },
        {
            "name": "6 — Country reference and discovery",
            "version": "0.6.0",
            "status": "complete",
            "functions": "Anthem titles, reviewed mottos, demonyms, complete timezone profiles, postal formats, richer currency and language metadata, profile filters, rankings, and nearest capitals",
            "tests": "Source-scope, review-decision, typed-model, ranking, filtering, serialization, documentation, and clean-wheel release gates",
            "dataset": "234 anthem profiles / 32 reviewed mottos / 227 demonym profiles / 246 timezone profiles / 176 postal formats / 722 country-language records",
            "docs": "Reference-facts guide, example gallery, rankings, filters, provenance, coverage boundaries, and runnable examples",
            "release": "Published as v0.6.0",
        },
        {
            "name": "7 — Physical geography",
            "version": "0.7.0",
            "status": "complete",
            "functions": "Land and water area, coastline, elevation extremes, major rivers and lakes, climate summaries, Köppen-Geiger classes, physical filters, and rankings",
            "tests": "Pinned-source coverage, typed-model, physical discovery, ranking, serialization, documentation, and release gates",
            "dataset": f"{coverage['physical_profiles']} physical profiles / {coverage['river_records']} rivers / {coverage['lake_records']} lakes / {coverage['koppen_geiger_profiles']} Köppen-Geiger profiles",
            "docs": "Physical profile guide, climate methodology, coverage rules, rankings, API reference, and runnable examples",
            "release": "Published as v0.7.0",
        },
    ]
    for name, version in [
        ("8 — Boundary geometry and spatial queries", "0.8.0"),
        ("9 — Advanced education and full-world hardening", "0.9.0"),
        ("Stable offline atlas", "1.0.0"),
    ]:
        milestones.append({"name": name, "version": version, "status": "planned", "functions": "—", "tests": "—", "dataset": "—", "docs": "—", "release": "—"})
    status = {
        "library_version": _project_version(root),
        "schema_version": 7,
        "dataset_version": "2026.07.22.7",
        "milestones": milestones,
        "coverage": coverage,
    }
    (reports / "status.json").write_text(
        json.dumps(status, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def run(root: Path) -> Path:
    write_manifests(root)
    normalized = normalize(root)
    database = build_database(root, normalized)
    report(root, normalized, database)
    return database
