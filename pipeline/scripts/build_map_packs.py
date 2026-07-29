"""Build deterministic optional map-data packages from pinned source snapshots."""

from __future__ import annotations

import argparse
from array import array
from dataclasses import dataclass
from hashlib import sha256
import json
import math
from pathlib import Path
import re
import sqlite3
import struct
import sys
import zipfile
import zlib

from PIL import Image, ImageChops, ImageDraw


ROOT = Path(__file__).resolve().parents[2]
ATLAS_DATABASE = ROOT / "src/pyworldatlas/data/atlas.sqlite3"
ELEVATION = ROOT / "build_data/raw/etopo-2022/2026-07-28/etopo-2022-5arcmin.nc"
BOUNDARIES = ROOT / "build_data/raw/natural-earth/2026-07-28/ne_10m_admin_0_map_units.zip"
RIVERS_STANDARD = ROOT / "build_data/raw/natural-earth/2026-07-28/ne_10m_rivers_lake_centerlines.zip"
RIVERS_OVERVIEW = ROOT / "build_data/raw/natural-earth/2026-07-21/ne_50m_rivers_lake_centerlines.zip"
CLIMATE = ROOT / "build_data/raw/koppen-geiger/2023/1991_2020/koppen_geiger_0p1.tif"
CLIMATE_LEGEND = ROOT / "build_data/raw/koppen-geiger/2023/legend.txt"

QUALITY = {
    "overview": {
        "arc_minutes": 20,
        "source_stride": 4,
        "boundary_points": 260,
        "river_points": 100,
        "river_source": RIVERS_OVERVIEW,
    },
    "standard": {
        "arc_minutes": 5,
        "source_stride": 1,
        "boundary_points": 700,
        "river_points": 240,
        "river_source": RIVERS_STANDARD,
    },
}

OUTPUTS = {
    "overview": ROOT / "packages/mapdata-overview/src/pyworldatlas_mapdata_overview/data/maps.sqlite3",
    "standard": ROOT / "packages/mapdata-standard/src/pyworldatlas_mapdata_standard/data/maps.sqlite3",
}

_NC_TYPE_WIDTH = {1: 1, 2: 1, 3: 2, 4: 4, 5: 4, 6: 8}
_NC_ARRAY_TYPE = {1: "b", 2: "b", 3: "h", 4: "i", 5: "f", 6: "d"}

# Natural Earth 5.1 labels the downstream Þjórsá feature as "Drau" even
# though its geometry continues the Icelandic river and its dissolve key is
# ``303Thjrs``. The corrected name is verified against Iceland's national
# natural-science institute: https://www.ni.is/en/geology/water/rivers
_RIVER_NAME_CORRECTIONS = {
    "1159116727": "Þjórsá",
}


@dataclass(frozen=True)
class NetCdfVariable:
    name: str
    dimensions: tuple[int, ...]
    data_type: int
    size: int
    offset: int


class ClassicNetCdf:
    """Read the small NetCDF classic subset used by the map-pack builder."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._stream = path.open("rb")
        if self._stream.read(4) != b"CDF\x01":
            raise ValueError(f"{path} is not a NetCDF classic file")
        self._read_u32()  # number of records; the ETOPO subset has none
        self.dimensions = self._read_dimensions()
        self._read_attributes()
        self.variables = self._read_variables()

    def close(self) -> None:
        self._stream.close()

    def __enter__(self) -> "ClassicNetCdf":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def _read_u32(self) -> int:
        return struct.unpack(">I", self._stream.read(4))[0]

    def _read_string(self) -> str:
        length = self._read_u32()
        raw = self._stream.read(length)
        self._stream.read((-length) % 4)
        return raw.decode("utf-8")

    def _read_dimensions(self) -> tuple[tuple[str, int], ...]:
        tag = self._read_u32()
        count = self._read_u32()
        if tag == 0 and count == 0:
            return ()
        if tag != 10:
            raise ValueError("Invalid NetCDF dimension list")
        return tuple((self._read_string(), self._read_u32()) for _ in range(count))

    def _read_attributes(self) -> None:
        tag = self._read_u32()
        count = self._read_u32()
        if tag == 0 and count == 0:
            return
        if tag != 12:
            raise ValueError("Invalid NetCDF attribute list")
        for _ in range(count):
            self._read_string()
            data_type = self._read_u32()
            length = self._read_u32()
            width = _NC_TYPE_WIDTH[data_type] * length
            self._stream.read(width + (-width) % 4)

    def _read_variables(self) -> dict[str, NetCdfVariable]:
        tag = self._read_u32()
        count = self._read_u32()
        if tag == 0 and count == 0:
            return {}
        if tag != 11:
            raise ValueError("Invalid NetCDF variable list")
        variables: dict[str, NetCdfVariable] = {}
        for _ in range(count):
            name = self._read_string()
            dimension_count = self._read_u32()
            dimensions = tuple(self._read_u32() for _ in range(dimension_count))
            self._read_attributes()
            data_type = self._read_u32()
            size = self._read_u32()
            offset = self._read_u32()
            variables[name] = NetCdfVariable(name, dimensions, data_type, size, offset)
        return variables

    def values(self, name: str) -> array:
        variable = self.variables[name]
        count = math.prod(self.dimensions[index][1] for index in variable.dimensions)
        width = _NC_TYPE_WIDTH[variable.data_type]
        self._stream.seek(variable.offset)
        values = array(_NC_ARRAY_TYPE[variable.data_type])
        values.frombytes(self._stream.read(count * width))
        if sys.byteorder == "little" and width > 1:
            values.byteswap()
        return values


def _clean(value: str | None) -> str:
    return (value or "").replace("\x00", "").strip()


def _read_dbf(data: bytes) -> list[dict[str, str]]:
    record_count = struct.unpack_from("<I", data, 4)[0]
    header_length = struct.unpack_from("<H", data, 8)[0]
    record_length = struct.unpack_from("<H", data, 10)[0]
    fields: list[tuple[str, int]] = []
    position = 32
    while position < header_length and data[position] != 0x0D:
        descriptor = data[position : position + 32]
        name = descriptor[:11].split(b"\0", 1)[0].decode("ascii", "ignore")
        fields.append((name, descriptor[16]))
        position += 32
    records: list[dict[str, str]] = []
    for index in range(record_count):
        start = header_length + index * record_length
        raw = data[start : start + record_length]
        if not raw or raw[:1] == b"*":
            continue
        offset = 1
        record: dict[str, str] = {}
        for name, width in fields:
            record[name] = _clean(raw[offset : offset + width].decode("utf-8", "replace"))
            offset += width
        records.append(record)
    return records


def _read_shapes(data: bytes) -> list[list[list[tuple[float, float]]]]:
    shapes: list[list[list[tuple[float, float]]]] = []
    position = 100
    while position + 8 <= len(data):
        _, words = struct.unpack_from(">ii", data, position)
        position += 8
        content = data[position : position + words * 2]
        position += words * 2
        if len(content) < 44 or struct.unpack_from("<i", content, 0)[0] not in (3, 5):
            shapes.append([])
            continue
        part_count, point_count = struct.unpack_from("<ii", content, 36)
        part_starts = list(struct.unpack_from(f"<{part_count}i", content, 44))
        points_offset = 44 + 4 * part_count
        points = [
            struct.unpack_from("<dd", content, points_offset + 16 * point)
            for point in range(point_count)
        ]
        parts: list[list[tuple[float, float]]] = []
        for part_index, start in enumerate(part_starts):
            stop = part_starts[part_index + 1] if part_index + 1 < part_count else point_count
            parts.append(points[start:stop])
        shapes.append(parts)
    return shapes


def _load_shapefile(path: Path) -> list[tuple[dict[str, str], list[list[tuple[float, float]]]]]:
    with zipfile.ZipFile(path) as archive:
        shp = next(name for name in archive.namelist() if name.casefold().endswith(".shp"))
        dbf = next(name for name in archive.namelist() if name.casefold().endswith(".dbf"))
        shapes = _read_shapes(archive.read(shp))
        records = _read_dbf(archive.read(dbf))
    if len(shapes) != len(records):
        raise ValueError(f"Shapefile record mismatch in {path}")
    return list(zip(records, shapes))


def _atlas_profiles() -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    with sqlite3.connect(ATLAS_DATABASE) as connection:
        rows = connection.execute("SELECT alpha2, alpha3, name FROM country ORDER BY alpha2").fetchall()
    names = {alpha2: name for alpha2, _, name in rows}
    by_alpha3 = {alpha3: alpha2 for alpha2, alpha3, _ in rows if alpha3}
    return names, by_alpha3, {alpha2: alpha3 for alpha2, alpha3, _ in rows if alpha3}


def _profile_code(record: dict[str, str], names: dict[str, str], by_alpha3: dict[str, str]) -> str | None:
    alpha2 = _clean(record.get("ISO_A2"))
    if alpha2 in names:
        return alpha2
    for field in ("ISO_A3", "GU_A3", "SU_A3", "ADM0_A3"):
        alpha3 = _clean(record.get(field))
        if alpha3 in by_alpha3:
            return by_alpha3[alpha3]
        if alpha3 == "PSX":
            return "PS"
    return None


def _country_rings() -> dict[str, list[list[tuple[float, float]]]]:
    names, by_alpha3, _ = _atlas_profiles()
    result = {code: [] for code in names}
    for record, parts in _load_shapefile(BOUNDARIES):
        code = _profile_code(record, names, by_alpha3)
        if code:
            result[code].extend(part for part in parts if len(part) >= 3)
    missing = [code for code, rings in result.items() if not rings]
    if missing:
        raise ValueError(f"Natural Earth has no map-unit geometry for: {', '.join(missing)}")
    return result


def _minimum_longitude_domain(rings: list[list[tuple[float, float]]]) -> tuple[float, float]:
    values = sorted({longitude % 360.0 for ring in rings for longitude, _ in ring})
    if len(values) < 2:
        return values[0], values[0]
    gaps = [
        ((values[(index + 1) % len(values)] - values[index]) % 360.0, index)
        for index in range(len(values))
    ]
    _, gap_index = max(gaps)
    start = values[(gap_index + 1) % len(values)]
    unwrapped = [value + (360.0 if value < start else 0.0) for value in values]
    end = max(unwrapped)
    if (start + end) / 2.0 > 180.0:
        start -= 360.0
        end -= 360.0
    return start, end


def _unwrap(longitude: float, west: float) -> float:
    value = longitude
    while value < west:
        value += 360.0
    while value >= west + 360.0:
        value -= 360.0
    return value


def _simplify(points: list[tuple[float, float]], limit: int) -> list[list[float]]:
    if len(points) <= limit:
        selected = points
    else:
        step = max(1, math.ceil(len(points) / limit))
        selected = points[::step]
    if selected and selected[0] != selected[-1]:
        selected = [*selected, selected[0]]
    return [[round(longitude, 5), round(latitude, 5)] for longitude, latitude in selected]


def _mask(
    rings: list[list[tuple[float, float]]],
    longitudes: list[float],
    latitudes: list[float],
) -> Image.Image:
    width, height = len(longitudes), len(latitudes)
    result = Image.new("1", (width, height), 0)
    west, east = longitudes[0], longitudes[-1]
    south, north = latitudes[0], latitudes[-1]
    for ring in rings:
        layer = Image.new("1", (width, height), 0)
        draw = ImageDraw.Draw(layer)
        points = [
            (
                (_unwrap(longitude, west) - west) * (width - 1) / max(east - west, 1e-9),
                (latitude - south) * (height - 1) / max(north - south, 1e-9),
            )
            for longitude, latitude in ring
        ]
        draw.polygon(points, fill=1)
        result = ImageChops.logical_xor(result, layer)
    return result


def _grid_axis(start: float, stop: float, step: float) -> list[float]:
    first = math.floor(start / step) * step
    last = math.ceil(stop / step) * step
    count = max(3, round((last - first) / step) + 1)
    return [round(first + index * step, 8) for index in range(count)]


def _local_step(span: float, source_step: float) -> float:
    if span >= source_step * 2:
        return source_step
    return max(source_step / 20.0, span / 4.0 if span else source_step / 20.0)


def _nearest_index(value: float, origin: float, step: float, count: int) -> int:
    return min(count - 1, max(0, round((value - origin) / step)))


def _climate_legend() -> dict[int, dict[str, str]]:
    pattern = re.compile(r"^\s*(\d+):\s+(\S+)\s+(.+?)\s+\[")
    result: dict[int, dict[str, str]] = {}
    for line in CLIMATE_LEGEND.read_text(encoding="utf-8").splitlines():
        match = pattern.match(line)
        if match:
            code = match.group(2)
            result[int(match.group(1))] = {
                "code": code,
                "name": match.group(3).strip(),
                "family": code[0],
            }
    return result


def _sample_climate(image: Image.Image, longitude: float, latitude: float) -> int:
    normalized = ((longitude + 180.0) % 360.0) - 180.0
    x = min(image.width - 1, max(0, int((normalized + 180.0) * 10)))
    y = min(image.height - 1, max(0, int((90.0 - latitude) * 10)))
    return int(image.getpixel((x, y)))


def _river_parts(path: Path) -> list[tuple[str, list[tuple[float, float]], tuple[float, float, float, float]]]:
    result = []
    for record, parts in _load_shapefile(path):
        name = _RIVER_NAME_CORRECTIONS.get(
            _clean(record.get("ne_id")),
            next(
                (
                    _clean(record.get(field))
                    for field in ("name_en", "NAME_EN", "name", "NAME")
                    if _clean(record.get(field))
                ),
                "River",
            ),
        )
        for part in parts:
            if len(part) < 2:
                continue
            longitudes = [point[0] for point in part]
            latitudes = [point[1] for point in part]
            result.append((name, part, (min(longitudes), min(latitudes), max(longitudes), max(latitudes))))
    return result


def _clip_rivers(
    river_parts: list[tuple[str, list[tuple[float, float]], tuple[float, float, float, float]]],
    mask: Image.Image,
    longitudes: list[float],
    latitudes: list[float],
    point_limit: int,
) -> list[dict[str, object]]:
    west, east = longitudes[0], longitudes[-1]
    south, north = latitudes[0], latitudes[-1]
    width, height = len(longitudes), len(latitudes)

    def inside(longitude: float, latitude: float) -> bool:
        longitude = _unwrap(longitude, west)
        if not (west <= longitude <= east and south <= latitude <= north):
            return False
        x = min(width - 1, max(0, round((longitude - west) * (width - 1) / max(east - west, 1e-9))))
        y = min(height - 1, max(0, round((latitude - south) * (height - 1) / max(north - south, 1e-9))))
        return bool(mask.getpixel((x, y)))

    chunks: list[dict[str, object]] = []
    for name, part, bounds in river_parts:
        raw_west, raw_south, raw_east, raw_north = bounds
        candidates = ((raw_west, raw_east), (raw_west + 360.0, raw_east + 360.0), (raw_west - 360.0, raw_east - 360.0))
        if raw_north < south or raw_south > north or not any(a <= east and b >= west for a, b in candidates):
            continue
        start: int | None = None
        flags = [inside(longitude, latitude) for longitude, latitude in part]
        for index, is_inside in enumerate([*flags, False]):
            if is_inside and start is None:
                start = max(0, index - 1)
            elif not is_inside and start is not None:
                stop = min(len(part), index + 1)
                points = [(_unwrap(lon, west), lat) for lon, lat in part[start:stop]]
                if len(points) >= 2:
                    chunks.append({"name": name, "points": _simplify(points, point_limit)})
                start = None
    return chunks


def _write_database(path: Path, quality: str, rows: list[tuple[str, str, bytes, int, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    connection = sqlite3.connect(path)
    try:
        connection.executescript(
            """
            PRAGMA page_size = 4096;
            CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE country_map (
                alpha2 TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                payload BLOB NOT NULL,
                uncompressed_bytes INTEGER NOT NULL,
                sha256 TEXT NOT NULL
            );
            """
        )
        metadata = {
            "format_version": "1",
            "quality": quality,
            "resolution_arc_minutes": str(QUALITY[quality]["arc_minutes"]),
            "country_count": str(len(rows)),
            "elevation_source": "NOAA NCEI ETOPO 2022 60 arc-second ice-surface elevation, sampled",
            "boundary_source": "Natural Earth 1:10m Admin 0 map units",
            "river_source": f"Natural Earth 1:{10 if quality == 'standard' else 50}m rivers and lake centerlines",
            "climate_source": "Beck et al. 1991-2020 Koppen-Geiger classification",
            "not_for_navigation": "true",
        }
        connection.executemany("INSERT INTO metadata VALUES (?, ?)", sorted(metadata.items()))
        connection.executemany("INSERT INTO country_map VALUES (?, ?, ?, ?, ?)", rows)
        connection.commit()
        connection.execute("VACUUM")
    finally:
        connection.close()


def build(quality: str) -> dict[str, object]:
    settings = QUALITY[quality]
    names, _, _ = _atlas_profiles()
    rings_by_country = _country_rings()
    rivers = _river_parts(settings["river_source"])
    climate_image = Image.open(CLIMATE)
    legend = _climate_legend()
    rows: list[tuple[str, str, bytes, int, str]] = []
    with ClassicNetCdf(ELEVATION) as dataset:
        latitude_name = "latitude" if "latitude" in dataset.variables else "lat"
        longitude_name = "longitude" if "longitude" in dataset.variables else "lon"
        elevation_name = "z" if "z" in dataset.variables else "elevation"
        source_latitudes = dataset.values(latitude_name)
        source_longitudes = dataset.values(longitude_name)
        elevations = dataset.values(elevation_name)
        source_rows = len(source_latitudes)
        source_columns = len(source_longitudes)
        source_lat_step = float(source_latitudes[1] - source_latitudes[0])
        source_lon_step = float(source_longitudes[1] - source_longitudes[0])
        target_step = source_lat_step * int(settings["source_stride"])
        for position, alpha2 in enumerate(sorted(names), 1):
            original_rings = rings_by_country[alpha2]
            west, east = _minimum_longitude_domain(original_rings)
            unwrapped_rings = [
                [(_unwrap(longitude, west), latitude) for longitude, latitude in ring]
                for ring in original_rings
            ]
            south = min(latitude for ring in unwrapped_rings for _, latitude in ring)
            north = max(latitude for ring in unwrapped_rings for _, latitude in ring)
            lon_step = _local_step(east - west, target_step)
            lat_step = _local_step(north - south, target_step)
            longitudes = _grid_axis(west - lon_step, east + lon_step, lon_step)
            latitudes = _grid_axis(south - lat_step, north + lat_step, lat_step)
            country_mask = _mask(unwrapped_rings, longitudes, latitudes)
            packed_elevation = array("h")
            packed_climate = bytearray()
            present_climates: set[int] = set()
            land_cells = 0
            elevation_min: int | None = None
            elevation_max: int | None = None
            for row_index, latitude in enumerate(latitudes):
                source_y = _nearest_index(latitude, float(source_latitudes[0]), source_lat_step, source_rows)
                for column_index, longitude in enumerate(longitudes):
                    if not country_mask.getpixel((column_index, row_index)):
                        packed_elevation.append(-32768)
                        packed_climate.append(0)
                        continue
                    source_longitude = longitude % 360.0
                    source_x = _nearest_index(source_longitude, float(source_longitudes[0]), source_lon_step, source_columns)
                    value = max(-32767, min(32767, round(float(elevations[source_y * source_columns + source_x]))))
                    # Generalized coastlines can include a neighbouring ocean
                    # sample at this resolution. Values below the lowest
                    # plausible exposed land are treated as coastal sea level.
                    if value < -500:
                        value = 0
                    climate = _sample_climate(climate_image, longitude, latitude)
                    packed_elevation.append(value)
                    packed_climate.append(climate)
                    if climate:
                        present_climates.add(climate)
                    land_cells += 1
                    elevation_min = value if elevation_min is None else min(elevation_min, value)
                    elevation_max = value if elevation_max is None else max(elevation_max, value)
            if land_cells == 0:
                center_x = len(longitudes) // 2
                center_y = len(latitudes) // 2
                for y in range(max(0, center_y - 1), min(len(latitudes), center_y + 2)):
                    for x in range(max(0, center_x - 1), min(len(longitudes), center_x + 2)):
                        index = y * len(longitudes) + x
                        source_y = _nearest_index(latitudes[y], float(source_latitudes[0]), source_lat_step, source_rows)
                        source_x = _nearest_index(longitudes[x] % 360.0, float(source_longitudes[0]), source_lon_step, source_columns)
                        value = max(-32767, min(32767, round(float(elevations[source_y * source_columns + source_x]))))
                        if value < -500:
                            value = 0
                        packed_elevation[index] = value
                        packed_climate[index] = _sample_climate(climate_image, longitudes[x], latitudes[y])
                        land_cells += 1
                        elevation_min = value if elevation_min is None else min(elevation_min, value)
                        elevation_max = value if elevation_max is None else max(elevation_max, value)
            if sys.byteorder != "little":
                packed_elevation.byteswap()
            boundary = [_simplify(ring, int(settings["boundary_points"])) for ring in unwrapped_rings]
            river_chunks = _clip_rivers(
                rivers,
                country_mask,
                longitudes,
                latitudes,
                int(settings["river_points"]),
            )
            payload = {
                "alpha2": alpha2,
                "name": names[alpha2],
                "quality": quality,
                "resolutionArcMinutes": int(settings["arc_minutes"]),
                "rows": len(latitudes),
                "columns": len(longitudes),
                "south": latitudes[0],
                "west": longitudes[0],
                "latitudeStep": round(latitudes[1] - latitudes[0], 8),
                "longitudeStep": round(longitudes[1] - longitudes[0], 8),
                "elevation": packed_elevation.tobytes().hex(),
                "climate": bytes(packed_climate).hex(),
                "climateLegend": {str(index): legend[index] for index in sorted(present_climates) if index in legend},
                "boundary": boundary,
                "rivers": river_chunks,
                "landCells": land_cells,
                "minimumElevationM": elevation_min,
                "maximumElevationM": elevation_max,
            }
            raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
            compressed = zlib.compress(raw, 9)
            rows.append((alpha2, names[alpha2], compressed, len(raw), sha256(raw).hexdigest()))
            print(f"[{position:3}/{len(names)}] {quality:8} {alpha2} {len(compressed):>8,} bytes", flush=True)
    output = OUTPUTS[quality]
    _write_database(output, quality, rows)
    return {
        "quality": quality,
        "output": str(output.relative_to(ROOT)),
        "countries": len(rows),
        "size_bytes": output.stat().st_size,
        "sha256": sha256(output.read_bytes()).hexdigest(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("quality", choices=("overview", "standard", "all"), nargs="?", default="all")
    args = parser.parse_args()
    qualities = tuple(QUALITY) if args.quality == "all" else (args.quality,)
    reports = [build(quality) for quality in qualities]
    print(json.dumps(reports, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
