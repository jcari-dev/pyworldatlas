"""Compact place files and the local index that makes them searchable.

A place file (``places.pwpl``) stores hundreds of thousands of places in a few
bytes each. Places are ordered along a Hilbert curve so neighbours sit side by
side, then stored column by column: coordinates as zigzag varint deltas, kinds
and countries as small table indexes, numbers only where known, and names as
plain text. Each column is compressed with LZMA or bz2, whichever is smaller.

Compact files are small to download but slow to search, so the first search
unpacks each file once into a SQLite index next to the packs (or in memory when
that folder cannot be written). Later searches read only the index.

The encoder ships with the package so tests and the maintainer pipeline share
one implementation; the library itself only decodes.
"""

from __future__ import annotations

import bz2
from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass
from functools import lru_cache
from hashlib import sha256
import json
import lzma
from math import asin, cos, radians, sin, sqrt
import os
from pathlib import Path
import sqlite3
import struct
import tempfile

from ._normalization import normalize_name

MAGIC = b"PWPL"
FORMAT = 1
INDEX_FORMAT = 2
_LZMA = [{"id": lzma.FILTER_LZMA2, "preset": 9 | lzma.PRESET_EXTREME}]
_COLUMNS = ("coords", "kinds", "numbers", "names", "english", "fame")
_NO_ELEVATION = -32768
EARTH_RADIUS_KM = 6371.0088


@dataclass(frozen=True, slots=True)
class PlaceRecord:
    """One place as stored in a place file."""

    name: str
    english: str
    code: str
    country: str
    latitude: float
    longitude: float
    population: int | None
    elevation_m: int | None
    fame: int


class PlaceFileError(ValueError):
    """Raised when a place file is damaged or has an unknown format."""


# --- small integer codecs -----------------------------------------------------


def _varint(value: int, out: bytearray) -> None:
    while True:
        byte = value & 0x7F
        value >>= 7
        if value:
            out.append(byte | 0x80)
        else:
            out.append(byte)
            return


def _zigzag(value: int) -> int:
    return value * 2 if value >= 0 else -value * 2 - 1


def _unzigzag(value: int) -> int:
    return value >> 1 if not value & 1 else -(value >> 1) - 1


def _varints(data: bytes) -> Iterator[int]:
    value = shift = 0
    for byte in data:
        value |= (byte & 0x7F) << shift
        if byte & 0x80:
            shift += 7
        else:
            yield value
            value = shift = 0


# --- encoding -----------------------------------------------------------------


def hilbert_key(latitude: float, longitude: float, order: int = 16) -> int:
    """Return a place's position along a Hilbert curve covering the globe."""
    side = (1 << order) - 1
    x = int((longitude + 180.0) / 360.0 * side)
    y = int((latitude + 90.0) / 180.0 * side)
    d = 0
    s = 1 << (order - 1)
    while s:
        rx = 1 if x & s else 0
        ry = 1 if y & s else 0
        d += s * s * ((3 * rx) ^ ry)
        if ry == 0:
            if rx == 1:
                x, y = s - 1 - x, s - 1 - y
            x, y = y, x
        s >>= 1
    return d


def _pack(name: str, data: bytes) -> tuple[str, bytes]:
    best = ("lzma", lzma.compress(data, format=lzma.FORMAT_RAW, filters=_LZMA))
    if name in {"names", "english"}:
        alternative = bz2.compress(data, 9)
        if len(alternative) < len(best[1]):
            best = ("bz2", alternative)
    return best


def encode(records: Sequence[PlaceRecord], *, precision: int, meta: dict[str, str]) -> bytes:
    """Encode records, kept in the given order, as a place file.

    ``precision`` is the number of coordinate steps per degree (1,000 is about
    110 m). Callers sort records with :func:`hilbert_key` for the best result.
    """
    codes = sorted({record.code for record in records})
    countries = sorted({record.country for record in records})
    code_ids = {code: index for index, code in enumerate(codes)}
    country_ids = {country: index for index, country in enumerate(countries)}
    coords, kinds, numbers, fame = bytearray(), bytearray(), bytearray(), bytearray()
    names, english = [], []
    last_lat = last_lon = 0
    for record in records:
        lat, lon = round(record.latitude * precision), round(record.longitude * precision)
        _varint(_zigzag(lat - last_lat), coords)
        _varint(_zigzag(lon - last_lon), coords)
        last_lat, last_lon = lat, lon
        _varint(code_ids[record.code], kinds)
        _varint(country_ids[record.country], kinds)
        has_population = bool(record.population)
        has_elevation = record.elevation_m is not None
        numbers.append(int(has_population) | int(has_elevation) << 1)
        if has_population:
            _varint(int(record.population or 0), numbers)
        if has_elevation:
            _varint(_zigzag(int(record.elevation_m or 0)), numbers)
        fame.append(max(0, min(255, record.fame)))
        names.append(record.name.replace("\n", " "))
        english.append("" if record.english == record.name else record.english.replace("\n", " "))
    raw = {
        "coords": bytes(coords),
        "kinds": bytes(kinds),
        "numbers": bytes(numbers),
        "names": "\n".join(names).encode("utf-8"),
        "english": "\n".join(english).encode("utf-8"),
        "fame": bytes(fame),
    }
    packed = {name: _pack(name, data) for name, data in raw.items()}
    header = {
        "format": FORMAT,
        "count": len(records),
        "precision": precision,
        "codes": codes,
        "countries": countries,
        "meta": dict(sorted(meta.items())),
        "columns": [
            {"name": name, "codec": packed[name][0], "size": len(packed[name][1])}
            for name in _COLUMNS
        ],
    }
    header_bytes = json.dumps(header, sort_keys=True, separators=(",", ":")).encode("utf-8")
    body = b"".join(packed[name][1] for name in _COLUMNS)
    return MAGIC + struct.pack("<I", len(header_bytes)) + header_bytes + body


# --- decoding -----------------------------------------------------------------


def read_header(data: bytes) -> dict[str, object]:
    """Return the header of a place file."""
    if data[:4] != MAGIC or len(data) < 8:
        raise PlaceFileError("not a PyWorldAtlas place file")
    (length,) = struct.unpack_from("<I", data, 4)
    try:
        header = json.loads(data[8:8 + length])
    except ValueError as error:
        raise PlaceFileError("damaged place file header") from error
    if not isinstance(header, dict) or header.get("format") != FORMAT:
        raise PlaceFileError("unsupported place file format")
    header["_offset"] = 8 + length
    return header


def decode(data: bytes) -> Iterator[PlaceRecord]:
    """Yield every record in a place file, in stored order."""
    header = read_header(data)
    offset = int(header["_offset"])  # type: ignore[call-overload]
    columns: dict[str, bytes] = {}
    for column in header["columns"]:  # type: ignore[attr-defined]
        payload = data[offset:offset + column["size"]]
        offset += column["size"]
        try:
            if column["codec"] == "lzma":
                columns[column["name"]] = lzma.decompress(payload, format=lzma.FORMAT_RAW, filters=_LZMA)
            elif column["codec"] == "bz2":
                columns[column["name"]] = bz2.decompress(payload)
            else:
                raise PlaceFileError(f"unknown codec {column['codec']!r}")
        except (lzma.LZMAError, OSError, EOFError, ValueError) as error:
            raise PlaceFileError(f"damaged {column['name']} column") from error
    count = int(header["count"])  # type: ignore[call-overload]
    precision = float(header["precision"])  # type: ignore[arg-type]
    codes: list[str] = header["codes"]  # type: ignore[assignment]
    countries: list[str] = header["countries"]  # type: ignore[assignment]
    names = columns["names"].decode("utf-8").split("\n")
    english = columns["english"].decode("utf-8").split("\n")
    fame = columns["fame"]
    if not (len(names) == len(english) == len(fame) == count):
        raise PlaceFileError("place file columns disagree")
    coords = _varints(columns["coords"])
    kinds = _varints(columns["kinds"])
    numbers = columns["numbers"]
    position = lat = lon = 0
    for index in range(count):
        lat += _unzigzag(next(coords))
        lon += _unzigzag(next(coords))
        code, country = next(kinds), next(kinds)
        flags = numbers[position]
        position += 1
        values: list[int | None] = []
        for present in (flags & 1, flags & 2):
            if present:
                value = shift = 0
                while True:
                    byte = numbers[position]
                    position += 1
                    value |= (byte & 0x7F) << shift
                    if byte < 0x80:
                        break
                    shift += 7
                values.append(value)
            else:
                values.append(None)
        population, elevation = values
        yield PlaceRecord(
            names[index],
            english[index] or names[index],
            codes[code],
            countries[country],
            lat / precision,
            lon / precision,
            population,
            _unzigzag(elevation) if elevation is not None else None,
            fame[index],
        )


# --- the local index ------------------------------------------------------------


def cell_of(latitude: float, longitude: float) -> int:
    """Return the 1 by 1 degree grid cell that holds a coordinate."""
    row = min(179, max(0, int(latitude + 90.0)))
    column = min(359, max(0, int(longitude + 180.0)))
    return row * 360 + column


# Leading words people often leave out: "Everest" for "Mount Everest".
_GENERIC = frozenset({
    "the", "mount", "mt", "lake", "river", "isle", "island", "cape", "gulf", "bay",
    "lago", "rio", "monte", "mont", "cerro", "lac", "loch", "pico", "sierra",
})
# Trailing words people often leave out: "Nile" for "Nile River".
_GENERIC_LAST = frozenset({"river", "lake", "mountain", "mountains", "desert", "volcano", "falls", "canyon"})


# ASCII punctuation and spaces become word breaks, exactly as in normalize_name.
_ASCII_BREAKS = {code: " " for code in range(128) if not chr(code).isalnum()}


@lru_cache(maxsize=1 << 16)
def _accented_key(name: str) -> str:
    return normalize_name(name)


def _key(name: str) -> str:
    """Return ``normalize_name(name)``, much faster for the common ASCII case."""
    if name.isascii():
        return " ".join(name.translate(_ASCII_BREAKS).casefold().split())
    return _accented_key(name)


def _keys(*names: str) -> set[str]:
    """Return the lookup keys of a place: each name, also without a generic first word."""
    keys = set()
    for key in map(_key, set(names)):
        if key:
            keys.add(key)
            first, _, rest = key.partition(" ")
            if rest and first in _GENERIC:
                keys.add(rest)
            rest, _, last = key.rpartition(" ")
            if rest and last in _GENERIC_LAST:
                keys.add(rest)
    return keys


_SCHEMA = """
CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE place (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    english TEXT,
    code TEXT NOT NULL,
    country TEXT NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    population INTEGER,
    elevation_m INTEGER,
    fame INTEGER NOT NULL,
    cell INTEGER NOT NULL
);
CREATE TEMP TABLE staged_key (key TEXT NOT NULL, place INTEGER NOT NULL);
"""


def build_index(data: bytes, connection: sqlite3.Connection) -> None:
    """Unpack a place file into an empty SQLite database."""
    header = read_header(data)
    connection.executescript(_SCHEMA)
    rows: list[tuple[object, ...]] = []
    keys: list[tuple[str, int]] = []

    def flush() -> None:
        connection.executemany("INSERT INTO place VALUES (?,?,?,?,?,?,?,?,?,?,?)", rows)
        connection.executemany("INSERT INTO staged_key VALUES (?,?)", keys)
        rows.clear()
        keys.clear()

    # Insert in batches so even the largest pack unpacks in modest memory, and
    # build the indexes afterwards, when SQLite can sort each one in one pass.
    for number, record in enumerate(decode(data), 1):
        rows.append((
            number, record.name, record.english if record.english != record.name else None,
            record.code, record.country,
            record.latitude, record.longitude, record.population, record.elevation_m,
            record.fame, cell_of(record.latitude, record.longitude),
        ))
        keys.extend((key, number) for key in _keys(record.name, record.english))
        if len(rows) == 50_000:
            flush()
    flush()
    connection.execute("CREATE INDEX place_cell ON place(cell)")
    # Keys are staged in a temporary table, then copied in sorted order into a
    # clustered table, so each key is stored once and the file stays small.
    connection.executescript("""
        CREATE TABLE place_key (key TEXT NOT NULL, place INTEGER NOT NULL, PRIMARY KEY (key, place))
            WITHOUT ROWID;
        INSERT OR IGNORE INTO place_key SELECT key, place FROM staged_key ORDER BY key, place;
        DROP TABLE staged_key;
    """)
    meta = {"index_format": str(INDEX_FORMAT), "count": str(header["count"])}
    meta.update({str(k): str(v) for k, v in dict(header["meta"]).items()})  # type: ignore[call-overload]
    connection.executemany("INSERT INTO meta VALUES (?,?)", sorted(meta.items()))
    connection.commit()


def open_index(source: Path, cache: Path | None) -> sqlite3.Connection:
    """Return a read-only connection to the index of a place file.

    The index is built once and kept in ``cache`` under the file's checksum.
    When ``cache`` is ``None`` or cannot be written, it is built in memory.
    """
    data = source.read_bytes()
    digest = sha256(data).hexdigest()[:20]
    if cache is not None:
        target = cache / f"places-{digest}-v{INDEX_FORMAT}.sqlite3"
        if not target.is_file():
            try:
                cache.mkdir(parents=True, exist_ok=True)
                handle, temporary = tempfile.mkstemp(prefix=".places-", suffix=".sqlite3", dir=cache)
                os.close(handle)
                try:
                    with sqlite3.connect(temporary) as connection:
                        connection.execute("PRAGMA journal_mode=OFF")
                        connection.execute("PRAGMA synchronous=OFF")
                        build_index(data, connection)
                    connection.close()
                    os.replace(temporary, target)
                finally:
                    if os.path.exists(temporary):
                        os.remove(temporary)
            except OSError:
                target = None  # type: ignore[assignment]
        if target is not None and target.is_file():
            connection = sqlite3.connect(f"file:{target.resolve().as_posix()}?mode=ro", uri=True)
            connection.row_factory = sqlite3.Row
            return connection
    connection = sqlite3.connect(":memory:")
    build_index(data, connection)
    connection.row_factory = sqlite3.Row
    return connection


# --- searches -------------------------------------------------------------------


_PREFIX_SCAN = 2_000


def find(
    connection: sqlite3.Connection,
    query: str,
    limit: int,
    where: str = "",
    params: Sequence[object] = (),
) -> list[tuple[int, sqlite3.Row]]:
    """Return ``(match score, row)`` pairs for a name: 2 for exact, 1 for prefix.

    Prefix matches read at most a few thousand index entries, so a one-letter
    query stays as fast as a full name.
    """
    key = normalize_name(query)
    if not key:
        return []
    exact = connection.execute(
        f"SELECT p.* FROM place_key k JOIN place p ON p.id = k.place WHERE k.key = ?{where}",
        (key, *params),
    ).fetchall()
    found = [(2, row) for row in exact]
    if len(found) < limit:
        seen = {row["id"] for row in exact}
        prefix = connection.execute(
            f"""SELECT p.* FROM (SELECT place FROM place_key WHERE key > ? AND key < ? LIMIT ?) k
                JOIN place p ON p.id = k.place WHERE 1{where}""",
            (key, key + "\uffff", _PREFIX_SCAN, *params),
        ).fetchall()
        found += [(1, row) for row in prefix if row["id"] not in seen]
    return found


def distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return the great-circle distance between two coordinates in kilometres."""
    p1, p2 = radians(lat1), radians(lat2)
    h = sin((p2 - p1) / 2) ** 2 + cos(p1) * cos(p2) * sin(radians(lon2 - lon1) / 2) ** 2
    return 2 * EARTH_RADIUS_KM * asin(min(1.0, sqrt(h)))


def _cells_around(latitude: float, longitude: float, span: float) -> Iterable[tuple[int, int]]:
    """Yield ``(first, last)`` cell ranges covering a box of +/- span degrees."""
    low = max(0, int(latitude - span + 90.0))
    high = min(179, int(latitude + span + 90.0))
    edge = min(89.9, abs(latitude) + span)
    width = span / max(cos(radians(edge)), 1e-3)
    for row in range(low, high + 1):
        if width >= 180:
            yield row * 360, row * 360 + 359
            continue
        west = int(longitude - width + 180.0)
        east = int(longitude + width + 180.0)
        if west < 0:
            yield row * 360 + west % 360, row * 360 + 359
            yield row * 360, row * 360 + east
        elif east > 359:
            yield row * 360 + west, row * 360 + 359
            yield row * 360, row * 360 + east % 360
        else:
            yield row * 360 + west, row * 360 + east


def near(
    connections: Sequence[sqlite3.Connection],
    latitude: float,
    longitude: float,
    limit: int,
    where: str = "",
    params: Sequence[object] = (),
) -> list[tuple[float, sqlite3.Row]]:
    """Return the ``limit`` nearest ``(distance_km, row)`` pairs across indexes.

    All indexes share one search box, so a large pack lets the search stop
    early for the smaller ones too. The search box doubles until the farthest kept place is closer than any
    place outside the box could be, so the answer is exact.
    """
    span = 0.05
    while True:
        width = span / max(cos(radians(min(89.9, abs(latitude) + span))), 1e-3)
        box = " AND latitude BETWEEN ? AND ?"
        bounds: list[object] = [latitude - span, latitude + span]
        west, east = longitude - width, longitude + width
        if width < 180:
            if west < -180:
                box += " AND (longitude >= ? OR longitude <= ?)"
                bounds += [west + 360, east]
            elif east > 180:
                box += " AND (longitude >= ? OR longitude <= ?)"
                bounds += [west, east - 360]
            else:
                box += " AND longitude BETWEEN ? AND ?"
                bounds += [west, east]
        found: list[tuple[float, sqlite3.Row]] = []
        for first, last in _cells_around(latitude, longitude, span):
            for connection in connections:
                rows = connection.execute(
                    f"SELECT * FROM place WHERE cell BETWEEN ? AND ?{box}{where}",
                    (first, last, *bounds, *params),
                ).fetchall()
                found.extend(
                    (distance_km(latitude, longitude, row["latitude"], row["longitude"]), row) for row in rows
                )
        found.sort(key=lambda item: (item[0], -item[1]["fame"], item[1]["name"]))
        # A place outside the box is more than ``span`` degrees of latitude
        # away, or (for the same latitude band) past a longitude edge widened by
        # 1 / cos(latitude), so it is at least ``span`` degrees of arc away.
        reach = span * 111.19 * 0.999
        if span >= 180 or (len(found) >= limit and found[limit - 1][0] <= reach):
            return found[:limit]
        if len(found) >= limit:
            # The farthest kept place bounds the answer: one box that reaches
            # it is enough, which saves many doublings over open ocean.
            span = max(span * 2, found[limit - 1][0] / (111.19 * 0.999) * 1.001)
        else:
            span *= 2
