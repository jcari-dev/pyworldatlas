"""Derive country climate-zone shares from a pinned Köppen-Geiger map.

This development-only extractor combines the CC0 Beck et al. (2023)
1991-2020 map with the project's pinned Natural Earth map-unit polygons. It
uses the 0.1-degree majority-resampled layer and keeps zones representing at
least 0.1% of the classified raster cells associated with a profile.

Pillow is required only to regenerate this compact source snapshot. It is not
a runtime dependency and is not needed by the offline database builder.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from hashlib import sha256
import json
from math import ceil, cos, floor, radians
from pathlib import Path
import re
import sys
import zipfile


SOURCE_ID = "koppen-geiger-1991-2020"
SOURCE_DOI = "https://doi.org/10.6084/m9.figshare.21937571.v1"
SOURCE_ARTICLE = "https://doi.org/10.1038/s41597-023-02549-6"
SOURCE_ARCHIVE_MD5 = "544e895588b90ecc5903c27f50f4b761"
SOURCE_ARCHIVE_SHA256 = "0f43cd0c83a781e29c0e9c43e114f690bb84274bfc78b3dc2c879888b0f60df1"
RESOLUTION_DEGREES = 0.1
MINIMUM_SHARE_PERCENT = 0.1
EXPECTED_COUNTRY_COUNT = 241
EXPECTED_GAPS = {"BV", "GI", "MH", "MV", "TK", "TV", "UM"}


def file_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_legend(path: Path) -> dict[int, dict[str, str]]:
    records: dict[int, dict[str, str]] = {}
    pattern = re.compile(r"^\s*(\d+):\s+(\S+)\s+(.+?)\s+\[[\d ]+\]\s*$")
    groups = {
        "A": "Tropical",
        "B": "Arid",
        "C": "Temperate",
        "D": "Cold",
        "E": "Polar",
    }
    for line in path.read_text(encoding="utf-8").splitlines():
        match = pattern.match(line)
        if match is None:
            continue
        identifier, code, description = match.groups()
        records[int(identifier)] = {
            "code": code,
            "name": description.strip(),
            "group": groups[code[0]],
        }
    if set(records) != set(range(1, 31)):
        raise ValueError(f"Expected 30 Köppen-Geiger classes, found {sorted(records)}")
    return records


def ring_area(points: list[tuple[float, float]]) -> float:
    return sum(
        points[index][0] * points[(index + 1) % len(points)][1]
        - points[(index + 1) % len(points)][0] * points[index][1]
        for index in range(len(points))
    ) / 2


def extract(root: Path, map_path: Path, legend_path: Path) -> dict[str, object]:
    try:
        from PIL import Image, ImageDraw
    except ImportError as error:  # pragma: no cover - regeneration dependency
        raise RuntimeError(
            "Regenerating the Köppen-Geiger snapshot requires Pillow"
        ) from error

    sys.path.insert(0, str(root / "pipeline" / "src"))
    from pyworldatlas_builder.core import (  # pylint: disable=import-outside-toplevel
        _read_dbf_records,
        _read_polygon_parts,
        parse_un_m49,
    )

    countries = parse_un_m49(root)
    alpha3_to_alpha2 = {
        str(record["data"]["alpha3"]): code for code, record in countries.items()
    }
    equivalents = {"SOL": "SO", "CYN": "CY", "TWN": "TW", "TAI": "TW"}

    def resolve_map_unit(record: dict[str, str]) -> str | None:
        for field in ("ISO_A2", "ISO_A2_EH"):
            if record[field] in countries:
                return record[field]
        for field in ("ISO_A3", "GU_A3", "ADM0_A3"):
            code = alpha3_to_alpha2.get(record[field])
            if code in countries:
                return code
        return equivalents.get(record["ADM0_A3"])

    archive_path = (
        root
        / "build_data"
        / "raw"
        / "natural-earth"
        / "2026-07-21"
        / "ne_50m_admin_0_map_units.zip"
    )
    with zipfile.ZipFile(archive_path) as archive:
        dbf_name = next(
            name for name in archive.namelist() if name.lower().endswith(".dbf")
        )
        shp_name = next(
            name for name in archive.namelist() if name.lower().endswith(".shp")
        )
        map_units = _read_dbf_records(archive.read(dbf_name))
        geometries = _read_polygon_parts(archive.read(shp_name))
    if len(map_units) != len(geometries):
        raise ValueError("Natural Earth attributes and geometries do not align")

    rings_by_country: dict[str, list[list[tuple[float, float]]]] = defaultdict(list)
    for map_unit, rings in zip(map_units, geometries):
        code = resolve_map_unit(map_unit)
        if code is not None:
            rings_by_country[code].extend(rings)

    legend = parse_legend(legend_path)
    climate = Image.open(map_path)
    climate.load()
    expected_size = (round(360 / RESOLUTION_DEGREES), round(180 / RESOLUTION_DEGREES))
    if climate.size != expected_size or climate.mode != "P":
        raise ValueError(
            f"Unexpected climate raster: size={climate.size}, mode={climate.mode}"
        )

    scale = 1 / RESOLUTION_DEGREES
    records: list[dict[str, object]] = []
    gaps: set[str] = set()
    for code in sorted(countries):
        rings = rings_by_country.get(code, [])
        if not rings:
            gaps.add(code)
            continue
        longitudes = [x for ring in rings for x, _ in ring]
        latitudes = [y for ring in rings for _, y in ring]
        left = max(0, floor((min(longitudes) + 180) * scale))
        right = min(climate.width, ceil((max(longitudes) + 180) * scale))
        top = max(0, floor((90 - max(latitudes)) * scale))
        bottom = min(climate.height, ceil((90 - min(latitudes)) * scale))
        if right <= left or bottom <= top:
            gaps.add(code)
            continue

        mask = Image.new("1", (right - left, bottom - top), 0)
        draw = ImageDraw.Draw(mask)
        for ring in rings:
            points = [
                ((longitude + 180) * scale - left, (90 - latitude) * scale - top)
                for longitude, latitude in ring
            ]
            # The transformed raster coordinate system reverses the vertical
            # axis. Natural Earth exterior rings therefore have positive area;
            # interior rings erase pixels under the shapefile winding rule.
            draw.polygon(points, fill=1 if ring_area(points) > 0 else 0)

        raster = climate.crop((left, top, right, bottom)).tobytes()
        inside = mask.convert("L").tobytes()
        width = right - left
        counts: Counter[int] = Counter()
        for row_index in range(bottom - top):
            latitude = 90 - (top + row_index + 0.5) / scale
            area_weight = cos(radians(latitude))
            start = row_index * width
            for value, is_inside in zip(
                raster[start : start + width], inside[start : start + width]
            ):
                if is_inside and value in legend:
                    counts[value] += area_weight
        if not counts:
            gaps.add(code)
            continue

        total = sum(counts.values())
        zones = []
        for identifier, count in counts.most_common():
            share = count / total * 100
            if share + 1e-12 < MINIMUM_SHARE_PERCENT:
                continue
            zones.append({
                **legend[identifier],
                "share_percent": round(share, 4),
            })
        records.append({
            "country_code": code,
            "source_record_id": f"1991_2020/koppen_geiger_0p1.tif#{code}",
            "source_locator": (
                "1991_2020/koppen_geiger_0p1.tif; Natural Earth 1:50m map units"
            ),
            "dominant_code": zones[0]["code"],
            "represented_share_percent": round(
                sum(zone["share_percent"] for zone in zones), 4
            ),
            "zones": zones,
        })

    if len(records) != EXPECTED_COUNTRY_COUNT or gaps != EXPECTED_GAPS:
        raise ValueError(
            "Unexpected Köppen-Geiger country coverage; "
            f"records={len(records)}, gaps={sorted(gaps)}"
        )
    return {
        "source_id": SOURCE_ID,
        "source_name": "Beck et al. Köppen-Geiger climate classification maps",
        "source_version": "1991-2020 historical climatology; dataset version 1",
        "dataset_doi": SOURCE_DOI,
        "article_doi": SOURCE_ARTICLE,
        "license_name": "CC0 1.0",
        "license_url": "https://creativecommons.org/publicdomain/zero/1.0/",
        "resolution_degrees": RESOLUTION_DEGREES,
        "minimum_share_percent": MINIMUM_SHARE_PERCENT,
        "map_sha256": file_sha256(map_path),
        "legend_sha256": file_sha256(legend_path),
        "source_archive_md5": SOURCE_ARCHIVE_MD5,
        "source_archive_sha256": SOURCE_ARCHIVE_SHA256,
        "method": (
            "Latitude-area-weighted raster-cell shares within pinned Natural Earth "
            "1:50m map-unit polygons; source classes below 0.1% are omitted"
        ),
        "coverage_gaps": sorted(gaps),
        "records": records,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("map", type=Path, help="Pinned 1991-2020 0.1-degree GeoTIFF")
    parser.add_argument("legend", type=Path, help="Pinned source legend.txt")
    parser.add_argument("--output", type=Path, required=True, help="Compact JSON output")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="PyWorldAtlas repository root",
    )
    args = parser.parse_args()
    snapshot = extract(args.root.resolve(), args.map.resolve(), args.legend.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"Wrote {len(snapshot['records'])} records to {args.output}")


if __name__ == "__main__":
    main()
