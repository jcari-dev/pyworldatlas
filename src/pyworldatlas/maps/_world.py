"""A flat world map that colors each country by one statistic, as plain SVG.

The outlines are the generalized display outlines already shipped in the map
packs. They are drawn on the Equal Earth projection, which keeps every
country's area in proportion, and colored in five classes that each hold about
the same number of countries.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from hashlib import sha256
import html
import json
import math
from pathlib import Path
import sqlite3
import tempfile
from typing import TYPE_CHECKING
import webbrowser
import zlib

from .. import packs
from ._scene import MapDataError

if TYPE_CHECKING:
    from ..models import Indicator, StatisticValue

WIDTH = 1000
HEIGHT = 487
COLORS = ("#e7f2f8", "#a9d3e6", "#5fa8cc", "#2b78a8", "#0b4a73")
"""Light to dark blue, one per class; lighter means a smaller number, not a worse one."""

_A1, _A2, _A3, _A4 = 1.340264, -0.081106, 0.000893, 0.003796
_M = math.sqrt(3) / 2
_X_EXTENT = 2.70663
_Y_EXTENT = 1.31731


def _project(longitude: float, latitude: float) -> tuple[float, float]:
    """Return SVG coordinates on the Equal Earth projection (Šavrič et al., 2018)."""
    theta = math.asin(_M * math.sin(math.radians(latitude)))
    t2 = theta * theta
    t6 = t2 * t2 * t2
    x = (
        2 * math.sqrt(3) * math.radians(longitude) * math.cos(theta)
        / (3 * (9 * _A4 * t6 * t2 + 7 * _A3 * t6 + 3 * _A2 * t2 + _A1))
    )
    y = theta * (_A4 * t6 * t2 + _A3 * t6 + _A2 * t2 + _A1)
    return WIDTH / 2 + x * WIDTH / (2 * _X_EXTENT), HEIGHT / 2 - y * HEIGHT / (2 * _Y_EXTENT)


def _ring_path(ring: list[list[float]], shift: float) -> str:
    points: list[tuple[float, float]] = []
    for longitude, latitude in ring:
        x, y = _project(longitude + shift, latitude)
        x, y = round(x, 1), round(y, 1)
        if points and abs(x - points[-1][0]) + abs(y - points[-1][1]) < 1.2:
            continue  # closer than about a pixel to the last point kept
        points.append((x, y))
    if len(points) < 3:
        return ""
    return "M" + "L".join(f"{x:g} {y:g}" for x, y in points) + "Z"


def _close_around_pole(ring: list[list[float]]) -> list[list[float]]:
    """Give a ring that circles a pole a full turn of coastline on each side.

    Outlines are stored with continuous longitudes, so a ring around a pole
    covers just under 360 degrees and its last coast edge crosses the seam.
    Repeating the neighbouring coast points one turn away keeps that edge.
    """
    coast = [point for point in ring if abs(point[1]) < 89.99]
    if len(coast) < 2:
        return ring
    start = min(range(len(coast)), key=lambda index: coast[index][0])
    coast = coast[start:] + coast[:start]
    first, last = coast[0], coast[-1]
    if last[0] < first[0]:
        coast.reverse()
        first, last = coast[0], coast[-1]
    pole = -90.0 if ring[0][1] < 0 or min(point[1] for point in ring) < -89.99 else 90.0
    return [
        [last[0] - 360, last[1]], *coast, [first[0] + 360, first[1]],
        [first[0] + 360, pole], [last[0] - 360, pole],
    ]


def _country_path(rings: list[list[list[float]]]) -> str:
    parts: list[str] = []
    for ring in rings:
        longitudes = [point[0] for point in ring]
        if max(longitudes) - min(longitudes) > 350:
            ring = _close_around_pole(ring)
            longitudes = [point[0] for point in ring]
        low, high = min(longitudes), max(longitudes)
        for shift in (-360.0, 0.0, 360.0):  # draw the copies that reach the visible world
            if low + shift < 180 and high + shift > -180:
                parts.append(_ring_path(ring, shift))
    return "".join(parts)


def _globe_path() -> str:
    edge = [(180.0, float(lat)) for lat in range(-90, 91, 2)]
    edge += [(-180.0, float(lat)) for lat in range(90, -91, -2)]
    return "M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in (_project(*p) for p in edge)) + "Z"


@lru_cache(maxsize=2)
def _outlines(database: str, modified: int) -> dict[str, str]:
    """Return each country's SVG path, read once per installed map pack file."""
    del modified  # part of the cache key only, so a replaced pack is read again
    connection = sqlite3.connect(f"file:{Path(database).as_posix()}?mode=ro", uri=True)
    try:
        if dict(connection.execute("SELECT key, value FROM metadata")).get("format_version") != "1":
            raise MapDataError("The installed map pack is incompatible")
        rows = connection.execute(
            "SELECT alpha2, payload, uncompressed_bytes, sha256 FROM country_map ORDER BY alpha2"
        ).fetchall()
    finally:
        connection.close()
    outlines: dict[str, str] = {}
    for alpha2, compressed, size, expected in rows:
        try:
            raw = zlib.decompress(compressed)
            if len(raw) != size or sha256(raw).hexdigest() != expected:
                raise MapDataError(f"The installed map record for {alpha2} failed its integrity check")
            outlines[alpha2] = _country_path(json.loads(raw)["boundary"])
        except (KeyError, ValueError, zlib.error) as error:
            raise MapDataError(f"The installed map record for {alpha2} could not be read") from error
    return outlines


def _class_edges(values: list[float]) -> tuple[float, ...]:
    """Return up to four rising boundaries that split the values into equal-count classes."""
    ordered = sorted(values)
    edges: list[float] = []
    for step in range(1, len(COLORS)):
        edge = ordered[len(ordered) * step // len(COLORS)]
        if edge > ordered[0] and (not edges or edge > edges[-1]):
            edges.append(edge)
    return tuple(edges)


def _short(value: float, decimals: int) -> str:
    """Return a legend-sized number, such as ``"1.4 billion"`` or ``"72.5"``."""
    for size, word in ((1e9, "billion"), (1e6, "million"), (1e3, "thousand")):
        if abs(value) >= size:
            scaled = value / size
            return f"{scaled:,.{0 if abs(scaled) >= 10 else 1}f} {word}"
    return f"{value:,.{decimals}f}"


@dataclass(frozen=True, slots=True)
class WorldMap:
    """A world map with every country colored by one statistic.

    Countries fall into five classes that each hold about the same number of
    countries, from light (smaller numbers) to dark (larger numbers). The
    colors order the published numbers only; they do not say which is better.
    Countries without a value are hatched and labelled "No data".
    """

    indicator: Indicator
    values: tuple[StatisticValue, ...]
    """The value drawn for each country, in alphabetical order of country name."""
    names: tuple[tuple[str, str], ...]
    """Every country on the map as ``(alpha2, name)``, alphabetical by name."""
    year: int | None
    """The requested year, or ``None`` for each country's latest value."""
    database: str
    """The map pack file the outlines are read from."""

    @property
    def title(self) -> str:
        """Return the map title, such as ``"Life expectancy at birth (years), latest year"``."""
        when = f"in {self.year}" if self.year is not None else "latest year"
        return f"{self.indicator.name} ({self.indicator.unit}), {when}"

    @property
    def class_edges(self) -> tuple[float, ...]:
        """Return the boundaries between color classes, lowest first."""
        return _class_edges([item.value for item in self.values])

    def description(self) -> str:
        """Return a plain-language summary of the map for screen readers."""
        if not self.values:
            return f"{self.title}. No country has a value."
        low = min(item.value for item in self.values)
        high = max(item.value for item in self.values)
        return (
            f"World map of {self.indicator.name.lower()}. {len(self.values)} of "
            f"{len(self.names)} countries have a value, from {self.indicator.format(low)} "
            f"to {self.indicator.format(high)}. The table lists every value. "
            f"Source: {self.indicator.source}."
        )

    def _legend(self) -> list[tuple[str, str]]:
        decimals = self.indicator.decimals
        edges = self.class_edges
        if not self.values:
            return []
        bounds = [min(item.value for item in self.values), *edges, max(item.value for item in self.values)]
        return [
            (COLORS[index], f"{_short(bounds[index], decimals)} to {_short(bounds[index + 1], decimals)}")
            for index in range(len(bounds) - 1)
        ]

    def to_svg(self) -> str:
        """Return the map as a standalone SVG image with a title, legend, and source line.

        Each country carries a hover title with its value and year. The image
        follows the reader's light or dark color scheme.
        """
        path = Path(self.database)
        outlines = _outlines(str(path), path.stat().st_mtime_ns)
        prefix = f"pwa-{self.indicator.key}"
        edges = self.class_edges
        by_area = {item.area: item for item in self.values}
        shapes: list[str] = []
        for alpha2, name in self.names:
            outline = outlines.get(alpha2)
            if not outline:
                continue
            item = by_area.get(alpha2)
            if item is None:
                fill, label = f"url(#{prefix}-none)", f"{name}: no data"
            else:
                fill = COLORS[sum(item.value >= edge for edge in edges)]
                label = f"{name}: {item}"
            shapes.append(f'<path d="{outline}" fill="{fill}"><title>{html.escape(label)}</title></path>')
        top = HEIGHT + 12
        legend = [
            f'<text x="16" y="{top + 8}" class="t">{html.escape(self.title)}</text>',
        ]
        x, row = 16.0, top + 18
        for color, label in [*self._legend(), (f"url(#{prefix}-none)", "No data")]:
            width = 19 + 7.4 * len(label) + 18
            if x + width > WIDTH - 16:  # wrap onto the next line
                x, row = 16.0, row + 22
            legend.append(
                f'<rect x="{x:g}" y="{row}" width="14" height="14" fill="{color}" class="k"/>'
                f'<text x="{x + 19:g}" y="{row + 12}">{html.escape(label)}</text>'
            )
            x += width
        legend.append(
            f'<text x="16" y="{row + 36}" class="s">Source: {html.escape(self.indicator.source)}. '
            "Outlines: Natural Earth, for display only.</text>"
        )
        globe = _globe_path()
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {row + 46}" '
            f'role="img" aria-labelledby="{prefix}-title {prefix}-desc" '
            'font-family="system-ui, sans-serif" font-size="13">'
            f'<title id="{prefix}-title">{html.escape(self.title)}</title>'
            f'<desc id="{prefix}-desc">{html.escape(self.description())}</desc>'
            "<style>text{fill:#1f2933}.t{font-weight:600;font-size:15px}.s{font-size:11px;fill:#52606d}"
            ".g{fill:#f4f8fb;stroke:#9aa5b1}.c{stroke:#33414e;stroke-width:.4;stroke-linejoin:round}"
            ".k{stroke:#33414e;stroke-width:.6}"
            "@media (prefers-color-scheme:dark){text{fill:#e4e7eb}.s{fill:#b0b8c1}"
            ".g{fill:#1c2630;stroke:#7b8794}.c,.k{stroke:#d9e2ec}}</style>"
            f'<defs><pattern id="{prefix}-none" width="6" height="6" patternUnits="userSpaceOnUse" '
            'patternTransform="rotate(45)"><rect width="6" height="6" fill="#eceff1"/>'
            '<line y2="6" stroke="#8a96a3" stroke-width="1.5"/></pattern>'
            f'<clipPath id="{prefix}-globe"><path d="{globe}"/></clipPath></defs>'
            f'<path d="{globe}" class="g"/>'
            f'<g clip-path="url(#{prefix}-globe)" class="c">{"".join(shapes)}</g>'
            f'{"".join(legend)}</svg>'
        )

    def _repr_html_(self) -> str:
        return self.to_svg()

    def to_html(self) -> str:
        """Return a complete offline HTML page with the map and a table of every value.

        The table lists each country in alphabetical order with its value and
        year, so the map can be read without seeing it.
        """
        named = dict(self.names)
        rows = "".join(
            f"<tr><th scope=row>{html.escape(named[item.area])}</th>"
            f"<td>{html.escape(item.indicator.format(item.value))}</td><td>{item.year}</td></tr>"
            for item in self.values
        )
        missing = [name for alpha2, name in self.names if alpha2 not in {i.area for i in self.values}]
        no_data = (
            f"<p>No data: {html.escape(', '.join(missing))}.</p>" if missing else ""
        )
        return (
            "<!doctype html><html lang=en><meta charset=utf-8>"
            '<meta name=viewport content="width=device-width,initial-scale=1">'
            f"<title>{html.escape(self.title)}</title>"
            "<style>:root{color-scheme:light dark}body{margin:0 auto;max-width:1100px;padding:16px;"
            "font:16px/1.5 system-ui,sans-serif;background:#fff;color:#1f2933}"
            "@media (prefers-color-scheme:dark){body{background:#111820;color:#e4e7eb}}"
            "h1{font-size:1.4rem}svg{width:100%;height:auto}table{border-collapse:collapse}"
            "th,td{padding:2px 12px 2px 0;text-align:left}td{font-variant-numeric:tabular-nums}"
            "summary{cursor:pointer;font-weight:600}</style>"
            f"<h1>{html.escape(self.title)}</h1>{self.to_svg()}"
            f"<p>{html.escape(self.description())}</p>"
            "<details><summary>Show every value as a table</summary>"
            f"<table><caption>{html.escape(self.title)}</caption>"
            "<thead><tr><th scope=col>Country</th><th scope=col>Value</th><th scope=col>Year</th></tr></thead>"
            f"<tbody>{rows}</tbody></table>{no_data}</details></html>"
        )

    def write_html(self, path: str | Path) -> Path:
        """Write the offline HTML page and return its resolved path."""
        target = Path(path).expanduser().resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(self.to_html(), encoding="utf-8", newline="\n")
        return target

    def write_svg(self, path: str | Path) -> Path:
        """Write the SVG image and return its resolved path."""
        target = Path(path).expanduser().resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(self.to_svg(), encoding="utf-8", newline="\n")
        return target

    def show(self) -> Path:
        """Open the map in the default browser and return the page's path."""
        target = self.write_html(
            Path(tempfile.gettempdir()) / "pyworldatlas-maps" / f"world-{self.indicator.key}.html"
        )
        webbrowser.open(target.as_uri(), new=2)
        return target


def outline_database(data_dir: str | Path | None) -> Path:
    """Return the installed map pack file to draw outlines from, preferring the smaller one."""
    for pack in ("maps-lite", "maps"):
        folder = packs.pack_path(pack, data_dir)
        if folder is not None and (folder / "maps.sqlite3").is_file():
            return folder / "maps.sqlite3"
    raise MapDataError("World maps need a map pack. Run: pyworldatlas get maps-lite")
