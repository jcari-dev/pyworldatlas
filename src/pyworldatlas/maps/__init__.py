"""Interactive offline 3D country maps drawn from installed map packs.

Maps need a map pack, installed once with ``pyworldatlas get maps`` (Standard,
5 arc-minute terrain) or ``pyworldatlas get maps-lite`` (Overview, 20
arc-minute terrain). Building a map uses only the Python standard library; the
pack ships the plotly.js browser renderer, so no Python plotting package is
required and a displayed map never contacts a CDN.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import tempfile
from typing import Any
import webbrowser

from .. import packs
from ._html import document, rotation_options
from ._scene import MapDataError, build_figure, load_payload

__all__ = ["QUALITY_PACKS", "CountryMap", "MapDataError", "available_map_qualities"]

QUALITY_PACKS = {"overview": "maps-lite", "standard": "maps"}
"""The data pack that provides each map quality."""


def available_map_qualities(data_dir: str | Path | None = None) -> tuple[str, ...]:
    """Return installed map qualities from least to most detailed."""
    return tuple(
        quality
        for quality, pack in QUALITY_PACKS.items()
        if packs.pack_path(pack, data_dir) is not None
    )


def _select_quality(requested: str, data_dir: str | Path | None) -> str:
    if requested not in {"auto", *QUALITY_PACKS}:
        raise ValueError("quality must be 'auto', 'overview', or 'standard'")
    available = available_map_qualities(data_dir)
    if requested == "auto":
        if "standard" in available:
            return "standard"
        if "overview" in available:
            return "overview"
    elif requested in available:
        return requested
    pack = QUALITY_PACKS["standard" if requested == "auto" else requested]
    raise MapDataError(
        f"The {'standard' if requested == 'auto' else requested} map data is not "
        f"installed. Run: pyworldatlas get {pack}"
    )


@dataclass(frozen=True, slots=True)
class CountryMap:
    """A lazily loaded interactive 3D country map.

    Use :meth:`show` to open a standalone offline browser view, :meth:`write_html`
    to save one, or :meth:`to_dict` for the plain plotly.js figure data.
    """

    alpha2: str
    country_name: str
    flag: str | None = None
    capital_name: str | None = None
    capital_latitude: float | None = None
    capital_longitude: float | None = None
    requested_quality: str = "auto"
    data_dir: str | None = None

    @classmethod
    def from_country(
        cls,
        country: object,
        *,
        quality: str = "auto",
        data_dir: str | Path | None = None,
    ) -> CountryMap:
        """Create a map request from a PyWorldAtlas country profile."""
        capital = getattr(country, "capital", None)
        coordinates = getattr(capital, "coordinates", None) if capital else None
        return cls(
            alpha2=str(getattr(country, "alpha2")),  # noqa: B009
            country_name=str(getattr(country, "name")),  # noqa: B009
            flag=getattr(country, "flag", None),
            capital_name=getattr(capital, "name", None) if capital else None,
            capital_latitude=getattr(coordinates, "latitude", None) if coordinates else None,
            capital_longitude=getattr(coordinates, "longitude", None) if coordinates else None,
            requested_quality=quality,
            data_dir=None if data_dir is None else str(data_dir),
        )

    @property
    def quality(self) -> str:
        """Return the installed map quality this request will use."""
        return _select_quality(self.requested_quality, self.data_dir)

    def _pack(self) -> Path:
        quality = self.quality
        folder = packs.pack_path(QUALITY_PACKS[quality], self.data_dir)
        if folder is None:  # removed after quality was checked
            raise MapDataError(f"The {quality} map pack is no longer installed")
        return folder

    def _payload(self) -> tuple[str, Path, dict[str, Any]]:
        quality = self.quality
        folder = self._pack()
        return quality, folder, load_payload(folder / "maps.sqlite3", self.alpha2, quality)

    @property
    def resolution_arc_minutes(self) -> int:
        """Return the nominal elevation sampling interval in arc-minutes."""
        return int(self._payload()[2]["resolutionArcMinutes"])

    def to_dict(self) -> dict[str, Any]:
        """Return the figure as plain plotly.js ``data`` and ``layout`` dictionaries.

        The figure contains elevation and climate surface controls, terrain
        height choices, optional river and capital labels, a country outline,
        source-provided river centerlines, and the primary capital when
        coordinates are available.
        """
        quality, folder, payload = self._payload()
        template = json.loads(
            (folder / "plotly-template-white.json").read_text(encoding="utf-8")
        )
        return build_figure(self, payload, quality, template)

    def figure(self) -> Any:
        """Return a ``plotly.graph_objects.Figure`` for notebooks and customization.

        This is the only map feature that needs the separate ``plotly`` package
        (``pip install plotly``). Every other method works without it.
        """
        try:
            import plotly.graph_objects as go
        except ModuleNotFoundError as error:
            raise MapDataError(
                "figure() needs the optional plotly package (pip install plotly). "
                "show(), write_html(), and to_dict() work without it."
            ) from error
        return go.Figure(self.to_dict())

    def to_html(
        self,
        *,
        auto_rotate: bool = False,
        rotation_speed: float = 1.0,
    ) -> str:
        """Return a complete standalone HTML page with plotly.js embedded.

        The page fills the browser window and offers a control panel to color
        the terrain by elevation or climate, change terrain height, show or hide
        the capital, rivers, and river names, rotate the view, reset the camera,
        and download a high-resolution PNG. On narrow screens the panel becomes
        a collapsible bottom sheet, and it follows the reader's light or dark
        color scheme. Set ``auto_rotate=True`` to begin rotating when the page
        opens. ``rotation_speed`` accepts values from ``0.25`` through ``3``;
        ``1`` completes a turn in about twenty seconds.
        """
        rotation_options(auto_rotate, rotation_speed)
        quality, folder, payload = self._payload()
        return document(
            self.to_dict(),
            renderer=folder / "plotly.min.js",
            country=self.country_name,
            code=self.alpha2,
            subtitle=(
                f"{quality.title()} 3D map · "
                f"{payload['resolutionArcMinutes']} arc-minute terrain"
            ),
            auto_rotate=auto_rotate,
            rotation_speed=rotation_speed,
            png_filename=f"{self.alpha2.casefold()}-{quality}-3d-map",
        )

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
        html = self.to_html(auto_rotate=auto_rotate, rotation_speed=rotation_speed)
        target = Path(path).expanduser().resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(html, encoding="utf-8", newline="\n")
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
