"""Turn a map record into a plotly.js figure description, using only the standard library.

The output is plain ``dict``/``list`` data in the plotly.js figure format, so it
can be drawn by the plotly.js file shipped in a map pack without any Python
plotting dependency.
"""

from __future__ import annotations

from array import array
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
import sys
from typing import TYPE_CHECKING, Any
import zlib

if TYPE_CHECKING:
    from . import CountryMap


class MapDataError(RuntimeError):
    """Raised when map data is missing, incompatible, or damaged."""


_TERRAIN_HEIGHTS = (
    ("0.5×", 0.08),
    ("1×", 0.16),
    ("1.5×", 0.24),
    ("2×", 0.32),
    ("3×", 0.48),
)

_ELEVATION_SCALE = (
    (0.00, "#16796f"),
    (0.12, "#55a868"),
    (0.34, "#a6bd72"),
    (0.55, "#d2b06b"),
    (0.76, "#9a7556"),
    (0.90, "#74675d"),
    (1.00, "#f1f3f4"),
)

# Place layers: (category, layer name, marker symbol, color). Each layer has its
# own shape as well as its own color, so it can be told apart without color.
PLACE_LAYERS = (
    ("town", "Towns", "circle", "#ffffff"),
    ("landform", "Mountains and islands", "square", "#c2410c"),
    ("water", "Water and ice", "diamond", "#0284c7"),
    ("landmark", "Landmarks", "x", "#7c3aed"),
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


def load_payload(database: Path, alpha2: str, quality: str) -> dict[str, Any]:
    """Read and verify one country's map record from a map pack database."""
    connection = sqlite3.connect(f"file:{database.resolve().as_posix()}?mode=ro", uri=True)
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
        payload: dict[str, Any] = json.loads(raw)
        return payload
    except (OSError, ValueError, zlib.error) as error:
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


def _marker_height(
    longitude: float,
    latitude: float,
    own_height: int | None,
    longitudes: list[float],
    latitudes: list[float],
    elevation: list[list[int | None]],
    lift: float,
) -> float:
    """Return the height to draw a place marker: just above the ground under it.

    A place over the sea, such as a small island, has no terrain cell, so it
    sits at its own known height, or at sea level, instead of borrowing the
    height of the nearest land.
    """
    x = min(len(longitudes) - 1, max(0, round((longitude - longitudes[0]) / (longitudes[1] - longitudes[0]))))
    y = min(len(latitudes) - 1, max(0, round((latitude - latitudes[0]) / (latitudes[1] - latitudes[0]))))
    ground = elevation[y][x]
    if ground is None:
        ground = max(own_height or 0, 0)
    return ground + lift


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


def _trace(kind: str, **properties: Any) -> dict[str, Any]:
    return {"type": kind, **properties}


def build_figure(
    request: CountryMap,
    payload: dict[str, Any],
    quality: str,
    template: dict[str, Any],
) -> dict[str, Any]:
    """Return the complete figure: terrain, outline, rivers, capital, places, and controls."""

    rows, columns = int(payload["rows"]), int(payload["columns"])
    longitudes = _axis(float(payload["west"]), float(payload["longitudeStep"]), columns)
    latitudes = _axis(float(payload["south"]), float(payload["latitudeStep"]), rows)
    elevation = _decode_elevation(payload["elevation"], rows, columns)
    climate, climate_labels = _decode_climate(
        payload["climate"], rows, columns, payload["climateLegend"]
    )
    minimum = int(payload["minimumElevationM"] or 0)
    maximum = int(payload["maximumElevationM"] or 1)
    surface = _trace(
        "surface",
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
    traces: list[dict[str, Any]] = [
        surface,
        _trace(
            "scatter3d",
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
    river_annotations: list[dict[str, object]] = []
    if river_parts:
        river_x, river_y, river_z = _flatten_lines(
            river_parts, longitudes, latitudes, elevation, 55
        )
        river_text: list[str | None] = []
        for river in payload["rivers"]:
            river_text.extend([river["name"]] * len(river["points"]))
            river_text.append(None)
        traces.append(
            _trace(
            "scatter3d",
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
        longest_river_parts: dict[str, list[list[float]]] = {}
        for river in payload["rivers"]:
            name = str(river["name"])
            points = river["points"]
            if not points:
                continue
            if len(points) > len(longest_river_parts.get(name, [])):
                longest_river_parts[name] = points
        for name, points in longest_river_parts.items():
            longitude, latitude = points[len(points) // 2]
            river_annotations.append(
                {
                    "x": longitude,
                    "y": latitude,
                    "z": _nearest_elevation(
                        longitude,
                        latitude,
                        longitudes,
                        latitudes,
                        elevation,
                    )
                    + 110,
                    "text": f"<b>{name}</b>",
                    "showarrow": False,
                    "visible": False,
                    "bgcolor": "rgba(255, 255, 255, 0.88)",
                    "bordercolor": "#168aad",
                    "borderpad": 3,
                    "font": {"color": "#075985", "size": 12},
                }
            )
    capital_annotation: dict[str, object] | None = None
    if request.capital_latitude is not None and request.capital_longitude is not None:
        capital_longitude = request.capital_longitude
        while capital_longitude < longitudes[0]:
            capital_longitude += 360.0
        while capital_longitude > longitudes[-1]:
            capital_longitude -= 360.0
        capital_elevation = _nearest_elevation(
            capital_longitude,
            request.capital_latitude,
            longitudes,
            latitudes,
            elevation,
        )
        traces.append(
            _trace(
            "scatter3d",
                x=[capital_longitude],
                y=[request.capital_latitude],
                z=[capital_elevation + 125],
                mode="markers",
                marker={
                    "color": "#ff3b68",
                    "size": 8,
                    "symbol": "diamond",
                    "line": {"color": "#ffffff", "width": 3},
                },
                hovertemplate=(
                    f"<b>{request.capital_name}</b><br>Capital of {request.country_name}"
                    "<extra></extra>"
                ),
                name="Capital",
                showlegend=False,
            )
        )
        capital_annotation = {
            "x": capital_longitude,
            "y": request.capital_latitude,
            "z": capital_elevation + 125,
            "text": f"<b>{request.capital_name}</b>",
            "showarrow": True,
            "arrowhead": 2,
            "arrowcolor": "#b42346",
            "ax": 0,
            "ay": -34,
            "visible": True,
            "bgcolor": "rgba(255, 255, 255, 0.94)",
            "bordercolor": "#ff3b68",
            "borderpad": 4,
            "font": {"color": "#7f1734", "size": 13},
        }
    # Lift markers only a hair above the ground (1.5% of the height range), so
    # they rest on the terrain instead of floating above it.
    lift = max(10.0, 0.015 * (maximum - minimum))
    for category, layer, symbol, color in PLACE_LAYERS:
        members = [place for place in request.places if place[2] == category]
        if not members:
            continue
        xs: list[float] = []
        ys: list[float] = []
        zs: list[float] = []
        details: list[str] = []
        for _name, kind, _, latitude, longitude, height in members:
            while longitude < longitudes[0]:
                longitude += 360.0
            while longitude > longitudes[-1]:
                longitude -= 360.0
            xs.append(longitude)
            ys.append(latitude)
            zs.append(_marker_height(longitude, latitude, height, longitudes, latitudes, elevation, lift))
            details.append(f"{kind}, {height:,} m" if height is not None else kind)
        traces.append(
            _trace(
                "scatter3d",
                x=xs,
                y=ys,
                z=zs,
                text=[place[0] for place in members],
                customdata=details,
                mode="markers",
                marker={
                    "color": color,
                    "size": 6,
                    "symbol": symbol,
                    "line": {"color": "#1f2937" if color == "#ffffff" else "#ffffff", "width": 1.5},
                },
                hovertemplate="<b>%{text}</b><br>%{customdata}<extra></extra>",
                name=layer,
                meta="places",
                showlegend=True,
            )
        )
    present = sorted(int(index) for index in payload["climateLegend"])
    map_annotations = (
        ([capital_annotation] if capital_annotation is not None else [])
        + river_annotations
    )
    capital_annotation_index = 0 if capital_annotation is not None else None
    river_annotation_indexes = tuple(
        range(1 if capital_annotation is not None else 0, len(map_annotations))
    )

    def label_visibility(
        *, capital: bool, rivers: bool
    ) -> dict[str, bool]:
        visibility: dict[str, bool] = {}
        if capital_annotation_index is not None:
            visibility[
                f"scene.annotations[{capital_annotation_index}].visible"
            ] = capital
        for index in river_annotation_indexes:
            visibility[f"scene.annotations[{index}].visible"] = rivers
        return visibility

    label_buttons: list[dict[str, object]] = []
    if capital_annotation_index is not None:
        label_buttons.extend(
            [
                {
                    "label": "Capital only",
                    "method": "relayout",
                    "args": [label_visibility(capital=True, rivers=False)],
                },
                {
                    "label": "All names",
                    "method": "relayout",
                    "args": [label_visibility(capital=True, rivers=True)],
                },
                {
                    "label": "River names",
                    "method": "relayout",
                    "args": [label_visibility(capital=False, rivers=True)],
                },
                {
                    "label": "Hide names",
                    "method": "relayout",
                    "args": [label_visibility(capital=False, rivers=False)],
                },
            ]
        )
    elif river_annotation_indexes:
        label_buttons.extend(
            [
                {
                    "label": "Hide names",
                    "method": "relayout",
                    "args": [label_visibility(capital=False, rivers=False)],
                },
                {
                    "label": "River names",
                    "method": "relayout",
                    "args": [label_visibility(capital=False, rivers=True)],
                },
            ]
        )

    update_menus: list[dict[str, object]] = [
        {
            "type": "buttons",
            "direction": "right",
            "x": 0.03,
            "y": 0.99,
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
                            "colorbar": [
                                {
                                    "title": {"text": "Elevation (m)"},
                                    "thickness": 14,
                                    "len": 0.68,
                                }
                            ],
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
                                    "ticktext": [
                                        payload["climateLegend"][str(index)]["code"]
                                        for index in present
                                    ],
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
    ]
    if label_buttons:
        update_menus.append(
            {
                "type": "dropdown",
                "direction": "down",
                "x": 0.03,
                "y": 0.89,
                "showactive": True,
                "active": 0,
                "buttons": label_buttons,
            }
        )
    layout: dict[str, Any] = dict(
        title={
            "text": f"{request.country_name} · {quality.title()} 3D map",
            "x": 0.03,
            "xanchor": "left",
        },
        template=template,
        margin={"l": 0, "r": 20, "t": 122, "b": 66},
        legend={"orientation": "h", "y": 1.08, "x": 0.76},
        uirevision=f"pyworldatlas-{request.alpha2}-{quality}",
        scene={
            "aspectmode": "manual",
            "aspectratio": {"x": 1, "y": 0.92, "z": 0.16},
            "annotations": map_annotations,
            "camera": {
                "eye": {"x": 0.35, "y": -0.55, "z": 0.68},
                "projection": {"type": "orthographic"},
            },
            "xaxis": {"title": {"text": "Longitude"}, "showbackground": False},
            "yaxis": {"title": {"text": "Latitude"}, "showbackground": False},
            "zaxis": {"title": {"text": ""}, "showticklabels": False, "showbackground": False},
        },
        updatemenus=update_menus,
        sliders=[
            {
                "active": 1,
                "x": 0.35,
                "y": 1.08,
                "len": 0.3,
                "currentvalue": {
                    "prefix": "Terrain height: ",
                    "font": {"size": 12, "color": "#334e68"},
                },
                "pad": {"t": 22},
                "steps": [
                    {
                        "label": label,
                        "method": "relayout",
                        "args": [{"scene.aspectratio.z": height}],
                    }
                    for label, height in _TERRAIN_HEIGHTS
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
    if not map_annotations:
        del layout["scene"]["annotations"]  # plotly.js treats [] and absent alike
    return {"data": traces, "layout": layout}


def _share(count: int, total: int) -> str:
    percent = round(count * 100 / total)
    return f"{percent}%" if percent >= 1 else "under 1%"


def describe(request: CountryMap, payload: dict[str, Any], quality: str) -> list[str]:
    """Return plain-language sentences that describe a map for screen-reader users."""
    rows, columns = int(payload["rows"]), int(payload["columns"])
    climate, _ = _decode_climate(payload["climate"], rows, columns, payload["climateLegend"])
    counts: dict[int, int] = {}
    for row in climate:
        for value in row:
            if value is not None:
                counts[value] = counts.get(value, 0) + 1
    total = sum(counts.values())

    def metres(value: int) -> str:
        text = f"{abs(value):,} m"
        return f"{text} below sea level" if value < 0 else text

    sentences = [
        f"{request.country_name}, shown as a {quality} 3D terrain map sampled every "
        f"{payload['resolutionArcMinutes']} arc-minutes.",
    ]
    lowest = int(payload["minimumElevationM"] or 0)
    highest = int(payload["maximumElevationM"] or 0)
    if lowest == highest:
        sentences.append(
            f"At this resolution the land appears flat, at {metres(lowest)}; "
            "it is too small to show differences in height."
        )
    else:
        sentences.append(
            f"Elevation on the map ranges from {metres(lowest)} to {metres(highest)}."
        )
    if request.capital_name and request.capital_latitude is not None:
        sentences.append(f"The capital, {request.capital_name}, is marked with a pink diamond.")
    if total:
        ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
        legend = payload["climateLegend"]
        parts = [
            f"{legend[str(index)]['name']} ({legend[str(index)]['code']}), "
            f"{_share(count, total)}"
            for index, count in ranked[:4]
        ]
        extra = f", and {len(ranked) - 4} more" if len(ranked) > 4 else ""
        sentences.append("Climate classes by area: " + "; ".join(parts) + extra + ".")
    rivers = [
        name
        for name in dict.fromkeys(str(river["name"]) for river in payload["rivers"])
        if name.casefold() != "river"  # unnamed source records
    ]
    sentences.append(
        f"Rivers shown: {', '.join(rivers)}." if rivers else "No major rivers are shown."
    )
    for category, layer, symbol, _ in PLACE_LAYERS:
        names = [place[0] for place in request.places if place[2] == category]
        if names:
            shape = {"circle": "white circle", "square": "orange square", "diamond": "blue diamond", "x": "purple cross"}[symbol]
            sentences.append(f"{layer}, marked with a {shape}: {', '.join(names)}.")
    sentences.append("Outlines and rivers are simplified. The map is not for navigation.")
    return sentences
