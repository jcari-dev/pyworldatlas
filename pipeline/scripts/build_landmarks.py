"""Build the landmarks pack: airports with scheduled flights and World Heritage sites.

Reads two pinned snapshots and writes ``packs/landmarks/landmarks.json.xz``:

- OurAirports ``airports.csv`` (public domain): every airport with scheduled
  passenger service and an IATA code.
- A Wikidata query for World Heritage sites (CC0): one record per World
  Heritage list number, with its English name, location, year of
  inscription, and whether its criteria are cultural, natural, or both.

Usage: python pipeline/scripts/build_landmarks.py
Only the Python standard library is used.
"""

from __future__ import annotations

from collections import defaultdict
import csv
from hashlib import sha256
import json
import lzma
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
AIRPORTS = ROOT / "build_data/raw/ourairports/2026-10-28/airports.csv"
HERITAGE = ROOT / "build_data/raw/wikidata/2026-10-28/world-heritage.json"
OUTPUT = ROOT / "packs/landmarks/landmarks.json.xz"
SIZES = {"large_airport": "large", "medium_airport": "medium", "small_airport": "small"}
CULTURAL = {"(i)", "(ii)", "(iii)", "(iv)", "(v)", "(vi)"}
NATURAL = {"(vii)", "(viii)", "(ix)", "(x)"}
POINT = re.compile(r"^Point\(([-0-9.eE]+) ([-0-9.eE]+)\)$")


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def airports() -> list[list[object]]:
    """Return [iata, icao, name, municipality, country, lat, lon, elevation m, size] rows."""
    pinned = json.loads((AIRPORTS.parent / "manifest.json").read_text(encoding="utf-8"))["files"][0]["sha256"]
    if _sha(AIRPORTS) != pinned:
        raise SystemExit(f"{AIRPORTS} does not match the checksum pinned in its manifest")
    rows = []
    with AIRPORTS.open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            if row["scheduled_service"] != "yes" or not row["iata_code"] or row["type"] not in SIZES:
                continue
            elevation = round(float(row["elevation_ft"]) * 0.3048) if row["elevation_ft"] else None
            rows.append([
                row["iata_code"], row["icao_code"] or None, row["name"], row["municipality"] or None,
                row["iso_country"], round(float(row["latitude_deg"]), 4), round(float(row["longitude_deg"]), 4),
                elevation, SIZES[row["type"]],
            ])
    rows.sort(key=lambda item: str(item[0]))
    return rows


def world_heritage() -> list[list[object]]:
    """Return [list number, name, lat, lon, year, category] rows."""
    bindings = json.loads(HERITAGE.read_text(encoding="utf-8"))["results"]["bindings"]
    items: dict[str, dict[str, object]] = defaultdict(
        lambda: {"ids": set(), "criteria": set(), "points": [], "years": set(), "name": ""}
    )
    for row in bindings:
        item = items[row["site"]["value"].rsplit("/", 1)[-1]]
        item["ids"].add(row["whsId"]["value"])  # type: ignore[union-attr]
        item["name"] = row["siteLabel"]["value"]
        if "criterionLabel" in row:
            item["criteria"].add(row["criterionLabel"]["value"])  # type: ignore[union-attr]
        if "coordinates" in row and row["coordinates"]["value"] not in item["points"]:
            item["points"].append(row["coordinates"]["value"])  # type: ignore[union-attr]
        if "inscribed" in row:
            item["years"].add(int(row["inscribed"]["value"][:4]))  # type: ignore[union-attr]
    by_number: dict[int, list[tuple[str, dict[str, object]]]] = defaultdict(list)
    for qid, item in items.items():
        for value in item["ids"]:  # type: ignore[union-attr]
            match = re.match(r"^(\d+)", value)
            if match:
                by_number[int(match.group(1))].append((qid, item))
    rows = []
    for number, candidates in sorted(by_number.items()):
        # Prefer the item that carries this exact list number, its inscription
        # year, and its criteria; then the most complete name; then the oldest item.
        def rank(entry: tuple[str, dict[str, object]], number: int = number) -> tuple[object, ...]:
            qid, item = entry
            return (
                str(number) in item["ids"], bool(item["years"]), len(item["criteria"]),  # type: ignore[arg-type,operator]
                len(str(item["name"])), -int(qid[1:]),
            )
        _, best = max(candidates, key=rank)
        criteria = set().union(*(item["criteria"] for _, item in candidates))  # type: ignore[arg-type]
        category = (
            "mixed" if criteria & CULTURAL and criteria & NATURAL
            else "cultural" if criteria & CULTURAL
            else "natural" if criteria & NATURAL
            else None
        )
        points = [point for _, item in candidates for point in item["points"]]  # type: ignore[attr-defined]
        latitude = longitude = None
        for point in best["points"] or points:  # type: ignore[operator]
            match = POINT.match(point)
            if match:
                longitude, latitude = round(float(match.group(1)), 4), round(float(match.group(2)), 4)
                break
        years = set().union(*(item["years"] for _, item in candidates))  # type: ignore[arg-type]
        rows.append([number, best["name"], latitude, longitude, min(years) if years else None, category])
    return rows


def main() -> None:
    document = {
        "format": 1,
        "sources": {
            "airports": {
                "name": "OurAirports", "file": "airports.csv", "retrieved": "2026-10-28",
                "sha256": _sha(AIRPORTS), "license": "Public domain",
            },
            "world_heritage": {
                "name": "Wikidata World Heritage statements", "file": "world-heritage.json",
                "retrieved": "2026-10-28", "sha256": _sha(HERITAGE), "license": "CC0 1.0",
            },
        },
        "airports": airports(),
        "world_heritage": world_heritage(),
    }
    data = json.dumps(document, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    packed = lzma.compress(data, format=lzma.FORMAT_XZ, preset=9 | lzma.PRESET_EXTREME)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_bytes(packed)
    print(
        f"{len(document['airports']):,} airports, {len(document['world_heritage']):,} World Heritage sites, "
        f"{len(packed):,} bytes -> {OUTPUT.relative_to(ROOT)}"
    )


if __name__ == "__main__":
    main()
