"""Build interactive country maps from an installed PyWorldAtlas map pack."""

from __future__ import annotations

from array import array
from dataclasses import dataclass
from hashlib import sha256
import importlib.util
from importlib import resources
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
from typing import Any
import webbrowser
import zlib


_PACKAGES = {
    "overview": "pyworldatlas_mapdata_overview",
    "standard": "pyworldatlas_mapdata_standard",
}

_ELEVATION_SCALE = (
    (0.00, "#16796f"),
    (0.12, "#55a868"),
    (0.34, "#a6bd72"),
    (0.55, "#d2b06b"),
    (0.76, "#9a7556"),
    (0.90, "#74675d"),
    (1.00, "#f1f3f4"),
)

_CLIMATE_COLORS = {
    1: "#166534", 2: "#228b22", 3: "#65a30d",
    4: "#dc2626", 5: "#f97316", 6: "#eab308", 7: "#facc15",
    8: "#7c3aed", 9: "#8b5cf6", 10: "#a78bfa",
    11: "#0891b2", 12: "#06b6d4", 13: "#67e8f9",
    14: "#2563eb", 15: "#60a5fa", 16: "#93c5fd",
    17: "#9333ea", 18: "#a855f7", 19: "#c084fc", 20: "#d8b4fe",
    21: "#4f46e5", 22: "#6366f1", 23: "#818cf8", 24: "#a5b4fc",
    25: "#1d4ed8", 26: "#3b82f6", 27: "#60a5fa", 28: "#93c5fd",
    29: "#94a3b8", 30: "#e2e8f0",
}


class MapDataError(RuntimeError):
    """Raised when map data is missing, incompatible, or damaged."""


def available_map_qualities() -> tuple[str, ...]:
    """Return installed map qualities from least to most detailed."""
    return tuple(quality for quality, package in _PACKAGES.items() if importlib.util.find_spec(package))


def _select_quality(requested: str) -> str:
    if requested not in {"auto", *_PACKAGES}:
        raise ValueError("quality must be 'auto', 'overview', or 'standard'")
    available = available_map_qualities()
    if requested == "auto":
        if "standard" in available:
            return "standard"
        if "overview" in available:
            return "overview"
    elif requested in available:
        return requested
    command = (
        'pip install "pyworldatlas[maps]"'
        if requested in {"auto", "standard"}
        else 'pip install "pyworldatlas[maps-overview]"'
    )
    raise MapDataError(f"The {requested} map data is not installed. Run: {command}")


def _load_payload(alpha2: str, quality: str) -> dict[str, Any]:
    package = _PACKAGES[quality]
    database = resources.files(package).joinpath("data/maps.sqlite3")
    with resources.as_file(database) as path:
        connection = sqlite3.connect(path)
        try:
            metadata = dict(connection.execute("SELECT key, value FROM metadata"))
            row = connection.execute(
                "SELECT payload, uncompressed_bytes, sha256 FROM country_map WHERE alpha2 = ?",
                (alpha2,),
            ).fetchone()
        finally:
            connection.close()
    if metadata.get("format_version") != "1" or metadata.get("quality") != quality:
        raise MapDataError(f"The installed {quality} map pack is incompatible")
    if row is None:
        raise MapDataError(f"The installed {quality} map pack has no profile for {alpha2}")
    try:
        raw = zlib.decompress(row[0])
        if len(raw) != row[1] or sha256(raw).hexdigest() != row[2]:
            raise MapDataError(f"The installed map record for {alpha2} failed its integrity check")
        return json.loads(raw)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        raise MapDataError(f"The installed map record for {alpha2} could not be read") from error


def _decode_elevation(encoded: str, rows: int, columns: int) -> list[list[int | None]]:
    values = array("h")
    values.frombytes(bytes.fromhex(encoded))
    if sys.byteorder != "little":
        values.byteswap()
    expected = rows * columns
    if len(values) != expected:
        raise MapDataError("The elevation grid has an invalid size")
    return [
        [None if value == -32768 else int(value) for value in values[offset : offset + columns]]
        for offset in range(0, expected, columns)
    ]


def _decode_climate(
    encoded: str,
    rows: int,
    columns: int,
    legend: dict[str, dict[str, str]],
) -> tuple[list[list[int | None]], list[list[str | None]]]:
    values = bytes.fromhex(encoded)
    expected = rows * columns
    if len(values) != expected:
        raise MapDataError("The climate grid has an invalid size")
    numeric: list[list[int | None]] = []
    labels: list[list[str | None]] = []
    for offset in range(0, expected, columns):
        numeric_row: list[int | None] = []
        label_row: list[str | None] = []
        for value in values[offset : offset + columns]:
            details = legend.get(str(value))
            numeric_row.append(value or None)
            label_row.append(f"{details['code']} · {details['name']}" if details else None)
        numeric.append(numeric_row)
        labels.append(label_row)
    return numeric, labels


def _axis(start: float, step: float, count: int) -> list[float]:
    return [round(start + step * index, 8) for index in range(count)]


def _nearest_elevation(
    longitude: float,
    latitude: float,
    longitudes: list[float],
    latitudes: list[float],
    elevation: list[list[int | None]],
) -> int:
    while longitude < longitudes[0]:
        longitude += 360.0
    while longitude > longitudes[-1]:
        longitude -= 360.0
    x = min(len(longitudes) - 1, max(0, round((longitude - longitudes[0]) / (longitudes[1] - longitudes[0]))))
    y = min(len(latitudes) - 1, max(0, round((latitude - latitudes[0]) / (latitudes[1] - latitudes[0]))))
    for radius in range(5):
        for row in range(max(0, y - radius), min(len(latitudes), y + radius + 1)):
            for column in range(max(0, x - radius), min(len(longitudes), x + radius + 1)):
                value = elevation[row][column]
                if value is not None:
                    return value
    return 0


def _flatten_lines(
    parts: list[list[list[float]]],
    longitudes: list[float],
    latitudes: list[float],
    elevation: list[list[int | None]],
    offset: int,
) -> tuple[list[float | None], list[float | None], list[int | None]]:
    x: list[float | None] = []
    y: list[float | None] = []
    z: list[int | None] = []
    for part in parts:
        for longitude, latitude in part:
            x.append(longitude)
            y.append(latitude)
            z.append(_nearest_elevation(longitude, latitude, longitudes, latitudes, elevation) + offset)
        x.append(None)
        y.append(None)
        z.append(None)
    return x, y, z


def _climate_scale() -> list[list[float | str]]:
    scale: list[list[float | str]] = []
    for index in range(1, 31):
        color = _CLIMATE_COLORS[index]
        scale.extend([[(index - 1) / 30, color], [index / 30, color]])
    return scale


@dataclass(frozen=True, slots=True)
class CountryMap:
    """A lazily loaded interactive 3D country map.

    Use :meth:`show` to open a standalone offline browser view. Use
    :meth:`figure` when direct Plotly customization or notebook display is
    preferred.
    """

    alpha2: str
    country_name: str
    flag: str | None = None
    capital_name: str | None = None
    capital_latitude: float | None = None
    capital_longitude: float | None = None
    requested_quality: str = "auto"

    @classmethod
    def from_country(cls, country: object, *, quality: str = "auto") -> "CountryMap":
        """Create a map request from a PyWorldAtlas country profile."""
        capital = getattr(country, "capital", None)
        coordinates = getattr(capital, "coordinates", None) if capital else None
        return cls(
            alpha2=str(getattr(country, "alpha2")),
            country_name=str(getattr(country, "name")),
            flag=getattr(country, "flag", None),
            capital_name=getattr(capital, "name", None) if capital else None,
            capital_latitude=getattr(coordinates, "latitude", None) if coordinates else None,
            capital_longitude=getattr(coordinates, "longitude", None) if coordinates else None,
            requested_quality=quality,
        )

    @property
    def quality(self) -> str:
        """Return the installed map quality this request will use."""
        return _select_quality(self.requested_quality)

    @property
    def resolution_arc_minutes(self) -> int:
        """Return the nominal elevation sampling interval in arc-minutes."""
        return int(_load_payload(self.alpha2, self.quality)["resolutionArcMinutes"])

    def figure(self) -> object:
        """Return a ready-to-display ``plotly.graph_objects.Figure``.

        The figure contains elevation and climate surface controls, a country
        outline, source-provided river centerlines, and the primary capital
        when coordinates are available.
        """
        import plotly.graph_objects as go

        payload = _load_payload(self.alpha2, self.quality)
        rows, columns = int(payload["rows"]), int(payload["columns"])
        longitudes = _axis(float(payload["west"]), float(payload["longitudeStep"]), columns)
        latitudes = _axis(float(payload["south"]), float(payload["latitudeStep"]), rows)
        elevation = _decode_elevation(payload["elevation"], rows, columns)
        climate, climate_labels = _decode_climate(
            payload["climate"], rows, columns, payload["climateLegend"]
        )
        minimum = int(payload["minimumElevationM"] or 0)
        maximum = int(payload["maximumElevationM"] or 1)
        surface = go.Surface(
            x=longitudes,
            y=latitudes,
            z=elevation,
            surfacecolor=elevation,
            customdata=climate_labels,
            colorscale=list(_ELEVATION_SCALE),
            cmin=minimum,
            cmax=maximum,
            colorbar={"title": {"text": "Elevation (m)"}, "thickness": 14, "len": 0.68},
            lighting={"ambient": 0.58, "diffuse": 0.88, "roughness": 0.82, "specular": 0.18},
            lightposition={"x": -80, "y": -20, "z": 9000},
            hovertemplate=(
                "Longitude %{x:.2f}°<br>Latitude %{y:.2f}°<br>"
                "Elevation %{z:,.0f} m<br>Climate %{customdata}<extra></extra>"
            ),
            name="Terrain",
            showscale=True,
        )
        boundary_x, boundary_y, boundary_z = _flatten_lines(
            payload["boundary"], longitudes, latitudes, elevation, 40
        )
        traces: list[object] = [
            surface,
            go.Scatter3d(
                x=boundary_x,
                y=boundary_y,
                z=boundary_z,
                mode="lines",
                line={"color": "#17202a", "width": 4},
                hoverinfo="skip",
                name="Country outline",
                showlegend=False,
            ),
        ]
        river_parts = [river["points"] for river in payload["rivers"]]
        if river_parts:
            river_x, river_y, river_z = _flatten_lines(
                river_parts, longitudes, latitudes, elevation, 55
            )
            river_text: list[str | None] = []
            for river in payload["rivers"]:
                river_text.extend([river["name"]] * len(river["points"]))
                river_text.append(None)
            traces.append(
                go.Scatter3d(
                    x=river_x,
                    y=river_y,
                    z=river_z,
                    text=river_text,
                    mode="lines",
                    line={"color": "#168aad", "width": 5},
                    hovertemplate="%{text}<extra>River</extra>",
                    name="Rivers",
                    showlegend=True,
                )
            )
        if self.capital_latitude is not None and self.capital_longitude is not None:
            capital_longitude = self.capital_longitude
            while capital_longitude < longitudes[0]:
                capital_longitude += 360.0
            while capital_longitude > longitudes[-1]:
                capital_longitude -= 360.0
            traces.append(
                go.Scatter3d(
                    x=[capital_longitude],
                    y=[self.capital_latitude],
                    z=[
                        _nearest_elevation(
                            capital_longitude,
                            self.capital_latitude,
                            longitudes,
                            latitudes,
                            elevation,
                        )
                        + 120
                    ],
                    text=[self.capital_name],
                    mode="markers+text",
                    textposition="top center",
                    marker={"color": "#d1495b", "size": 5, "symbol": "diamond"},
                    hovertemplate=f"{self.capital_name}<extra>Capital</extra>",
                    name="Capital",
                    showlegend=False,
                )
            )
        present = sorted(int(index) for index in payload["climateLegend"])
        figure = go.Figure(data=traces)
        figure.update_layout(
            title={
                "text": f"{self.country_name} · {self.quality.title()} 3D map",
                "x": 0.03,
                "xanchor": "left",
            },
            template="plotly_white",
            margin={"l": 0, "r": 20, "t": 88, "b": 58},
            legend={"orientation": "h", "y": 1.02, "x": 0.72},
            uirevision=f"pyworldatlas-{self.alpha2}-{self.quality}",
            scene={
                "aspectmode": "manual",
                "aspectratio": {"x": 1, "y": 0.92, "z": 0.16},
                "camera": {
                    "eye": {"x": 0.35, "y": -0.55, "z": 0.68},
                    "projection": {"type": "orthographic"},
                },
                "xaxis": {"title": "Longitude", "showbackground": False},
                "yaxis": {"title": "Latitude", "showbackground": False},
                "zaxis": {"title": "", "showticklabels": False, "showbackground": False},
            },
            updatemenus=[
                {
                    "type": "buttons",
                    "direction": "right",
                    "x": 0.03,
                    "y": 1.02,
                    "showactive": True,
                    "buttons": [
                        {
                            "label": "Elevation",
                            "method": "restyle",
                            "args": [
                                {
                                    "surfacecolor": [elevation],
                                    "colorscale": [list(_ELEVATION_SCALE)],
                                    "cmin": [minimum],
                                    "cmax": [maximum],
                                    "colorbar": [{"title": {"text": "Elevation (m)"}, "thickness": 14, "len": 0.68}],
                                },
                                [0],
                            ],
                        },
                        {
                            "label": "Climate",
                            "method": "restyle",
                            "args": [
                                {
                                    "surfacecolor": [climate],
                                    "colorscale": [_climate_scale()],
                                    "cmin": [0.5],
                                    "cmax": [30.5],
                                    "colorbar": [
                                        {
                                            "title": {"text": "Climate"},
                                            "tickvals": present,
                                            "ticktext": [payload["climateLegend"][str(index)]["code"] for index in present],
                                            "thickness": 14,
                                            "len": 0.68,
                                        }
                                    ],
                                },
                                [0],
                            ],
                        },
                    ],
                }
            ],
            annotations=[
                {
                    "text": (
                        f"{payload['resolutionArcMinutes']} arc-minute elevation · "
                        "NOAA ETOPO 2022 · Natural Earth · Beck et al. climate · Not for navigation"
                    ),
                    "showarrow": False,
                    "xref": "paper",
                    "yref": "paper",
                    "x": 0.5,
                    "y": -0.06,
                    "xanchor": "center",
                    "font": {"size": 11, "color": "#5f6b76"},
                }
            ],
        )
        return figure

    def to_html(self) -> str:
        """Return a complete standalone HTML document with Plotly embedded."""
        import plotly.io as pio

        html = pio.to_html(
            self.figure(),
            include_plotlyjs=True,
            full_html=True,
            config={"responsive": True, "displaylogo": False, "scrollZoom": True},
        )
        title = f"{self.country_name} 3D map · PyWorldAtlas"
        return html.replace("<head>", f"<head><title>{title}</title>", 1)

    def write_html(self, path: str | Path) -> Path:
        """Write a standalone offline HTML map and return its resolved path."""
        target = Path(path).expanduser().resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(self.to_html(), encoding="utf-8", newline="\n")
        return target

    def show(self) -> Path:
        """Open the interactive map in the default browser and return its path."""
        directory = Path(tempfile.gettempdir()) / "pyworldatlas-maps"
        target = self.write_html(directory / f"{self.alpha2.casefold()}-{self.quality}.html")
        webbrowser.open(target.as_uri(), new=2)
        return target
