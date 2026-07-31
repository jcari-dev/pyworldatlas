"""Build interactive country maps from an installed PyWorldAtlas map pack."""

from __future__ import annotations

from array import array
from dataclasses import dataclass
from hashlib import sha256
import importlib.util
from importlib import resources
import json
import math
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

_VIEWER_CONTROLS_SCRIPT = r"""
(function () {
  const plot = document.getElementById('{plot_id}');
  if (!plot || plot.dataset.pyworldatlasControls === 'ready') {
    return;
  }
  plot.dataset.pyworldatlasControls = 'ready';

  const style = document.createElement('style');
  style.textContent = `
    .pyworldatlas-viewer-controls {
      align-items: center;
      background: rgba(255, 255, 255, 0.94);
      border: 1px solid #b8c9dc;
      border-radius: 7px;
      box-shadow: 0 2px 8px rgba(24, 52, 82, 0.10);
      color: #243b5a;
      display: flex;
      font: 14px/1.2 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      gap: 10px;
      padding: 7px 9px;
      position: absolute;
      right: 28px;
      top: 126px;
      z-index: 1000;
    }
    .pyworldatlas-viewer-controls button {
      background: #f7fbff;
      border: 1px solid #9fb6d0;
      border-radius: 5px;
      color: #243b5a;
      cursor: pointer;
      font: inherit;
      padding: 7px 11px;
    }
    .pyworldatlas-viewer-controls button:hover,
    .pyworldatlas-viewer-controls button:focus-visible {
      background: #eaf4fb;
      border-color: #4c83b6;
      outline: none;
    }
    .pyworldatlas-viewer-controls button[aria-pressed="true"] {
      background: #287aa3;
      border-color: #21698d;
      color: #ffffff;
    }
    .pyworldatlas-speed-control {
      align-items: center;
      display: flex;
      gap: 7px;
      white-space: nowrap;
    }
    .pyworldatlas-speed-control input {
      accent-color: #287aa3;
      cursor: pointer;
      width: 112px;
    }
    .pyworldatlas-speed-control output {
      min-width: 32px;
      text-align: right;
    }
    @media (max-width: 760px) {
      .pyworldatlas-viewer-controls {
        left: 12px;
        right: 12px;
        top: 164px;
      }
      .pyworldatlas-speed-control {
        flex: 1;
      }
      .pyworldatlas-speed-control input {
        min-width: 70px;
        width: 100%;
      }
    }
  `;
  document.head.appendChild(style);

  const controls = document.createElement('div');
  controls.className = 'pyworldatlas-viewer-controls';
  controls.setAttribute('role', 'group');
  controls.setAttribute('aria-label', 'Map motion and export controls');

  const rotateButton = document.createElement('button');
  rotateButton.type = 'button';
  rotateButton.textContent = 'Rotate';
  rotateButton.setAttribute('aria-pressed', 'false');

  const speedLabel = document.createElement('label');
  speedLabel.className = 'pyworldatlas-speed-control';
  speedLabel.append(document.createTextNode('Speed'));
  const speedInput = document.createElement('input');
  speedInput.type = 'range';
  speedInput.min = '0.25';
  speedInput.max = '3';
  speedInput.step = '0.25';
  speedInput.value = String(__ROTATION_SPEED__);
  speedInput.setAttribute('aria-label', 'Rotation speed');
  const speedOutput = document.createElement('output');
  function formatSpeed(value) {
    return `${Number(value).toFixed(2).replace(/\.?0+$/, '')}×`;
  }
  speedOutput.value = formatSpeed(speedInput.value);
  speedOutput.textContent = speedOutput.value;
  speedLabel.append(speedInput, speedOutput);

  const downloadButton = document.createElement('button');
  downloadButton.type = 'button';
  downloadButton.textContent = 'Download PNG';

  controls.append(rotateButton, speedLabel, downloadButton);
  const wrapper = plot.parentElement;
  if (wrapper) {
    wrapper.style.position = 'relative';
    wrapper.appendChild(controls);
  }

  let rotating = false;
  let frameHandle = null;
  let lastFrameTime = 0;
  let applyingCamera = false;
  const degreesPerSecond = 18;
  const reducedMotion = window.matchMedia &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function updateButton() {
    rotateButton.textContent = rotating ? 'Pause' : 'Rotate';
    rotateButton.setAttribute('aria-pressed', String(rotating));
  }

  function setRotating(value) {
    rotating = Boolean(value);
    lastFrameTime = 0;
    if (!rotating && frameHandle !== null) {
      window.cancelAnimationFrame(frameHandle);
      frameHandle = null;
    }
    updateButton();
    if (rotating && frameHandle === null) {
      frameHandle = window.requestAnimationFrame(rotateFrame);
    }
  }

  function rotateFrame(timestamp) {
    frameHandle = null;
    if (!rotating) {
      return;
    }
    const elapsed = lastFrameTime
      ? Math.min((timestamp - lastFrameTime) / 1000, 0.05)
      : 0;
    lastFrameTime = timestamp;
    const camera = (plot.layout.scene && plot.layout.scene.camera) || {};
    const eye = camera.eye || {x: 0.35, y: -0.55, z: 0.68};
    const eyeX = Number(eye.x) || 0.35;
    const eyeY = Number(eye.y) || -0.55;
    const radius = Math.hypot(eyeX, eyeY) || 0.65;
    const speed = Number(speedInput.value);
    const angle = Math.atan2(eyeY, eyeX) +
      elapsed * degreesPerSecond * speed * Math.PI / 180;
    applyingCamera = true;
    Promise.resolve(Plotly.relayout(plot, {
      'scene.camera.eye': {
        x: radius * Math.cos(angle),
        y: radius * Math.sin(angle),
        z: Number(eye.z) || 0.68
      }
    })).finally(function () {
      applyingCamera = false;
      if (rotating) {
        frameHandle = window.requestAnimationFrame(rotateFrame);
      }
    });
  }

  function pauseForManualCameraChange(update) {
    if (!rotating || applyingCamera || !update) {
      return;
    }
    if (Object.keys(update).some(function (key) {
      return key.indexOf('scene.camera') === 0;
    })) {
      setRotating(false);
    }
  }

  rotateButton.addEventListener('click', function () {
    setRotating(!rotating);
  });
  speedInput.addEventListener('input', function () {
    speedOutput.value = formatSpeed(speedInput.value);
    speedOutput.textContent = speedOutput.value;
  });
  downloadButton.addEventListener('click', function () {
    const resumeAfterExport = rotating;
    setRotating(false);
    Promise.resolve(Plotly.downloadImage(plot, {
      format: 'png',
      filename: __PNG_FILENAME__,
      width: 1600,
      height: 900,
      scale: 2
    })).finally(function () {
      if (resumeAfterExport) {
        setRotating(true);
      }
    });
  });
  plot.on('plotly_relayout', pauseForManualCameraChange);
  plot.on('plotly_relayouting', pauseForManualCameraChange);

  updateButton();
  if (__AUTO_ROTATE__ && !reducedMotion) {
    setRotating(true);
  }
})();
"""


class MapDataError(RuntimeError):
    """Raised when map data is missing, incompatible, or damaged."""


def _rotation_options(auto_rotate: bool, rotation_speed: float) -> tuple[bool, float]:
    if not isinstance(auto_rotate, bool):
        raise TypeError("auto_rotate must be True or False")
    if isinstance(rotation_speed, bool):
        raise TypeError("rotation_speed must be a number from 0.25 through 3")
    try:
        speed = float(rotation_speed)
    except (TypeError, ValueError) as error:
        raise TypeError("rotation_speed must be a number from 0.25 through 3") from error
    if not math.isfinite(speed) or not 0.25 <= speed <= 3:
        raise ValueError("rotation_speed must be from 0.25 through 3")
    return auto_rotate, speed


def _viewer_controls_script(
    *, auto_rotate: bool, rotation_speed: float, png_filename: str
) -> str:
    auto_rotate, rotation_speed = _rotation_options(auto_rotate, rotation_speed)
    return (
        _VIEWER_CONTROLS_SCRIPT.replace(
            "__AUTO_ROTATE__", json.dumps(auto_rotate)
        )
        .replace("__ROTATION_SPEED__", json.dumps(rotation_speed))
        .replace("__PNG_FILENAME__", json.dumps(png_filename))
    )


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

        The figure contains elevation and climate surface controls, terrain
        height choices, optional river and capital labels, a country outline,
        source-provided river centerlines, and the primary capital when
        coordinates are available.
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
        if self.capital_latitude is not None and self.capital_longitude is not None:
            capital_longitude = self.capital_longitude
            while capital_longitude < longitudes[0]:
                capital_longitude += 360.0
            while capital_longitude > longitudes[-1]:
                capital_longitude -= 360.0
            capital_elevation = _nearest_elevation(
                capital_longitude,
                self.capital_latitude,
                longitudes,
                latitudes,
                elevation,
            )
            traces.append(
                go.Scatter3d(
                    x=[capital_longitude],
                    y=[self.capital_latitude],
                    z=[capital_elevation + 125],
                    mode="markers",
                    marker={
                        "color": "#ff3b68",
                        "size": 8,
                        "symbol": "diamond",
                        "line": {"color": "#ffffff", "width": 3},
                    },
                    hovertemplate=(
                        f"<b>{self.capital_name}</b><br>Capital of {self.country_name}"
                        "<extra></extra>"
                    ),
                    name="Capital",
                    showlegend=False,
                )
            )
            capital_annotation = {
                "x": capital_longitude,
                "y": self.capital_latitude,
                "z": capital_elevation + 125,
                "text": f"<b>{self.capital_name}</b>",
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
        figure = go.Figure(data=traces)
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
        figure.update_layout(
            title={
                "text": f"{self.country_name} · {self.quality.title()} 3D map",
                "x": 0.03,
                "xanchor": "left",
            },
            template="plotly_white",
            margin={"l": 0, "r": 20, "t": 122, "b": 66},
            legend={"orientation": "h", "y": 1.08, "x": 0.76},
            uirevision=f"pyworldatlas-{self.alpha2}-{self.quality}",
            scene={
                "aspectmode": "manual",
                "aspectratio": {"x": 1, "y": 0.92, "z": 0.16},
                "annotations": map_annotations,
                "camera": {
                    "eye": {"x": 0.35, "y": -0.55, "z": 0.68},
                    "projection": {"type": "orthographic"},
                },
                "xaxis": {"title": "Longitude", "showbackground": False},
                "yaxis": {"title": "Latitude", "showbackground": False},
                "zaxis": {"title": "", "showticklabels": False, "showbackground": False},
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
        return figure

    def to_html(
        self,
        *,
        auto_rotate: bool = False,
        rotation_speed: float = 1.0,
    ) -> str:
        """Return a complete standalone HTML document with Plotly embedded.

        The document includes rotation, speed, and high-resolution PNG export
        controls. Set ``auto_rotate=True`` to begin rotating when the page
        opens. ``rotation_speed`` accepts values from ``0.25`` through ``3``;
        ``1`` completes a turn in about twenty seconds.
        """
        import plotly.io as pio

        filename = f"{self.alpha2.casefold()}-{self.quality}-3d-map"
        html = pio.to_html(
            self.figure(),
            include_plotlyjs=True,
            full_html=True,
            div_id="pyworldatlas-map",
            config={
                "responsive": True,
                "displaylogo": False,
                "scrollZoom": True,
                "toImageButtonOptions": {
                    "format": "png",
                    "filename": filename,
                    "width": 1600,
                    "height": 900,
                    "scale": 2,
                },
            },
            post_script=_viewer_controls_script(
                auto_rotate=auto_rotate,
                rotation_speed=rotation_speed,
                png_filename=filename,
            ),
        )
        title = f"{self.country_name} 3D map · PyWorldAtlas"
        return html.replace("<head>", f"<head><title>{title}</title>", 1)

    def write_html(
        self,
        path: str | Path,
        *,
        auto_rotate: bool = False,
        rotation_speed: float = 1.0,
    ) -> Path:
        """Write a standalone offline HTML map and return its resolved path.

        ``auto_rotate`` and ``rotation_speed`` select the document's initial
        motion state. The reader can still pause or adjust rotation in the
        exported viewer.
        """
        target = Path(path).expanduser().resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            self.to_html(
                auto_rotate=auto_rotate,
                rotation_speed=rotation_speed,
            ),
            encoding="utf-8",
            newline="\n",
        )
        return target

    def show(
        self,
        *,
        auto_rotate: bool = False,
        rotation_speed: float = 1.0,
    ) -> Path:
        """Open the interactive map in the default browser and return its path.

        Set ``auto_rotate=True`` to start the map in motion. The generated
        browser controls can pause rotation, change its speed, and download a
        high-resolution PNG of the current view.
        """
        directory = Path(tempfile.gettempdir()) / "pyworldatlas-maps"
        target = self.write_html(
            directory / f"{self.alpha2.casefold()}-{self.quality}.html",
            auto_rotate=auto_rotate,
            rotation_speed=rotation_speed,
        )
        webbrowser.open(target.as_uri(), new=2)
        return target
