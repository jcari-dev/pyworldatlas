"""Coordinates, areas, and physical geography models."""

from __future__ import annotations

from dataclasses import dataclass
from math import asin, atan2, cos, degrees, isclose, radians, sin, sqrt

from ._display import friendly_repr
from .reference import SourceReference


@dataclass(frozen=True, slots=True)
class Coordinate:
    """A signed WGS84 coordinate in decimal degrees.

    Use :meth:`format` for a compact classroom-friendly label, :meth:`dms` for
    degrees/minutes/seconds, and the calculation methods for great-circle
    distance and direction. Latitude always comes before longitude.
    """

    latitude: float
    longitude: float

    def __post_init__(self) -> None:
        if not -90 <= self.latitude <= 90:
            raise ValueError("latitude must be between -90 and 90")
        if not -180 <= self.longitude <= 180:
            raise ValueError("longitude must be between -180 and 180")

    def as_tuple(self) -> tuple[float, float]:
        """Return ``(latitude, longitude)``."""
        return (self.latitude, self.longitude)

    @property
    def hemispheres(self) -> tuple[str, str]:
        """Return the latitude and longitude hemispheres, such as ``("N", "E")``."""
        return (
            "N" if self.latitude >= 0 else "S",
            "E" if self.longitude >= 0 else "W",
        )

    def format(self, *, precision: int = 4) -> str:
        """Return signed coordinates as an easy-to-read hemisphere label.

        ``Coordinate(35.6895, 139.6917).format()`` returns
        ``"35.6895° N, 139.6917° E"``. ``precision`` controls decimal places
        and must be an integer from 0 through 8.
        """
        if isinstance(precision, bool) or not isinstance(precision, int):
            raise TypeError("precision must be an integer")
        if not 0 <= precision <= 8:
            raise ValueError("precision must be between 0 and 8")
        latitude_hemisphere, longitude_hemisphere = self.hemispheres
        return (
            f"{abs(self.latitude):.{precision}f}° {latitude_hemisphere}, "
            f"{abs(self.longitude):.{precision}f}° {longitude_hemisphere}"
        )

    def dms(self, *, seconds_precision: int = 1) -> str:
        """Return degrees, minutes, and seconds with hemisphere letters.

        ``seconds_precision`` controls decimal places on the seconds value and
        must be an integer from 0 through 6.
        """
        if isinstance(seconds_precision, bool) or not isinstance(seconds_precision, int):
            raise TypeError("seconds_precision must be an integer")
        if not 0 <= seconds_precision <= 6:
            raise ValueError("seconds_precision must be between 0 and 6")

        def component(value: float, hemisphere: str) -> str:
            total_seconds = round(abs(value) * 3600, seconds_precision)
            degrees_value = int(total_seconds // 3600)
            remaining = total_seconds - degrees_value * 3600
            minutes_value = int(remaining // 60)
            seconds_value = remaining - minutes_value * 60
            seconds = f"{seconds_value:.{seconds_precision}f}"
            return f"{degrees_value}° {minutes_value}′ {seconds}″ {hemisphere}"

        latitude_hemisphere, longitude_hemisphere = self.hemispheres
        return (
            f"{component(self.latitude, latitude_hemisphere)}, "
            f"{component(self.longitude, longitude_hemisphere)}"
        )

    def distance_to(self, other: Coordinate, *, unit: str = "km") -> float:
        """Return great-circle distance using the WGS84 mean Earth radius.

        ``unit`` accepts kilometres (``"km"``), statute miles (``"mi"``), or
        nautical miles (``"nmi"``). This is a surface measurement, not a road
        or flight route.
        """
        lat1, lon1, lat2, lon2 = map(radians, (self.latitude, self.longitude, other.latitude, other.longitude))
        delta_lat, delta_lon = lat2 - lat1, lon2 - lon1
        haversine = sin(delta_lat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(delta_lon / 2) ** 2
        kilometers = 2 * 6371.0088 * asin(min(1.0, sqrt(haversine)))
        factors = {"km": 1.0, "mi": 0.621371192237334, "nmi": 0.539956803455724}
        if unit not in factors:
            raise ValueError("unit must be 'km', 'mi', or 'nmi'")
        return kilometers * factors[unit]

    def _relative_position(self, other: Coordinate) -> tuple[bool, bool]:
        """Return whether two coordinates are coincident or antipodal."""
        def unit_vector(coordinate: Coordinate) -> tuple[float, float, float]:
            latitude = radians(coordinate.latitude)
            longitude = radians(coordinate.longitude)
            return (
                cos(latitude) * cos(longitude),
                cos(latitude) * sin(longitude),
                sin(latitude),
            )

        first = unit_vector(self)
        second = unit_vector(other)
        coincident = all(
            isclose(left, right, rel_tol=0.0, abs_tol=1e-12)
            for left, right in zip(first, second, strict=True)
        )
        antipodal = all(
            isclose(left, -right, rel_tol=0.0, abs_tol=1e-12)
            for left, right in zip(first, second, strict=True)
        )
        return coincident, antipodal

    def bearing_to(self, other: Coordinate) -> float:
        """Return the initial bearing to ``other`` in degrees from true north.

        The bearing is in the half-open range ``[0, 360)`` and may change along
        a great-circle path. Coincident and antipodal points have no unique
        initial bearing and raise :class:`ValueError`.
        """
        coincident, antipodal = self._relative_position(other)
        if coincident:
            raise ValueError("initial bearing is undefined for coincident coordinates")
        if antipodal:
            raise ValueError("initial bearing is undefined for antipodal coordinates")
        lat1, lat2 = radians(self.latitude), radians(other.latitude)
        delta_lon = radians(other.longitude - self.longitude)
        y = sin(delta_lon) * cos(lat2)
        x = cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(delta_lon)
        return (degrees(atan2(y, x)) + 360.0) % 360.0

    def compass_direction_to(self, other: Coordinate, *, points: int = 16) -> str:
        """Return a compass direction such as ``"SE"`` for the initial bearing.

        ``points`` selects a 4-, 8-, or 16-point compass rose. The result
        describes the initial great-circle direction, which can change along a
        long route.
        """
        labels = {
            4: ("N", "E", "S", "W"),
            8: ("N", "NE", "E", "SE", "S", "SW", "W", "NW"),
            16: (
                "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW",
            ),
        }
        if points not in labels:
            raise ValueError("points must be 4, 8, or 16")
        step = 360 / points
        index = int((self.bearing_to(other) + step / 2) // step) % points
        return labels[points][index]

    def midpoint_to(self, other: Coordinate) -> Coordinate:
        """Return the spherical midpoint on the great-circle path to ``other``."""
        _, antipodal = self._relative_position(other)
        if antipodal:
            raise ValueError("great-circle midpoint is undefined for antipodal coordinates")
        lat1, lon1, lat2 = map(radians, (self.latitude, self.longitude, other.latitude))
        delta_lon = radians(other.longitude - self.longitude)
        bx, by = cos(lat2) * cos(delta_lon), cos(lat2) * sin(delta_lon)
        latitude = atan2(sin(lat1) + sin(lat2), sqrt((cos(lat1) + bx) ** 2 + by**2))
        longitude = lon1 + atan2(by, cos(lat1) + bx)
        normalized_longitude = (degrees(longitude) + 540.0) % 360.0 - 180.0
        return Coordinate(degrees(latitude), normalized_longitude)


@dataclass(frozen=True, slots=True)
class Area:
    """Country area measurements in square kilometres.

    ``water_percent`` is derived from ``water_km2 / total_km2`` when both
    source values are available. Missing components remain ``None``.
    """

    total_km2: float | None = None
    land_km2: float | None = None
    water_km2: float | None = None
    water_percent: float | None = None

    def __str__(self) -> str:
        if self.total_km2 is None:
            return "area unknown"
        text = f"{self.total_km2:,} km²"
        return f"{text}, {self.water_percent:g}% water" if self.water_percent is not None else text

    def __repr__(self) -> str:
        return friendly_repr(self, f"{str(self)!r}")


@dataclass(frozen=True, slots=True)
class ElevationPoint:
    """A named highest or lowest point and its elevation above sea level.

    A negative value is below sea level. ``is_approximate`` preserves an
    explicit approximation in the source; the numeric value is not made more
    precise by the package. ``source_label`` retains the exact compact label
    from which the structured fields were parsed.
    """

    name: str
    elevation_m: float
    is_approximate: bool = False
    source_label: str | None = None

    def __str__(self) -> str:
        about = "about " if self.is_approximate else ""
        return f"{self.name}, {about}{self.elevation_m:,} m"

    def __repr__(self) -> str:
        return friendly_repr(self, f"{str(self)!r}")


@dataclass(frozen=True, slots=True)
class River:
    """A source-listed major river associated with a country profile.

    ``length_km`` is the full river length reported by the source, including
    for rivers shared across countries. It is not the length inside this one
    profile. ``source_label`` preserves shared/source/mouth context.
    """

    name: str
    length_km: float | None
    source_label: str

    def __str__(self) -> str:
        return f"{self.name}, {self.length_km:,} km" if self.length_km is not None else self.name

    def __repr__(self) -> str:
        return friendly_repr(self, f"{str(self)!r}")


@dataclass(frozen=True, slots=True)
class Lake:
    """A source-listed major lake associated with a country profile.

    ``area_km2`` is the full lake area reported by the source, including for a
    shared lake. ``water_type`` is ``"freshwater"`` or ``"saltwater"`` when
    the source supplies that classification.
    """

    name: str
    area_km2: float | None
    water_type: str | None
    source_label: str

    def __str__(self) -> str:
        return f"{self.name}, {self.area_km2:,} km²" if self.area_km2 is not None else self.name

    def __repr__(self) -> str:
        return friendly_repr(self, f"{str(self)!r}")


@dataclass(frozen=True, slots=True)
class ClimateZone:
    """A Köppen-Geiger class detected within a country or area profile.

    ``share_percent`` is a latitude-area-weighted share derived from the
    source's 0.1-degree 1991-2020 raster and pinned map-unit polygons. Classes
    below the documented extraction threshold are omitted.
    """

    code: str
    name: str
    group: str
    share_percent: float

    def __str__(self) -> str:
        return f"{self.code} · {self.name} · {self.share_percent:.1f}%"

    def __repr__(self) -> str:
        return friendly_repr(self, f"{str(self)!r}")


@dataclass(frozen=True, slots=True)
class ClimateProfile:
    """A plain-language climate summary and reviewed Köppen-Geiger classes."""

    summary: str | None = None
    koppen_geiger_zones: tuple[ClimateZone, ...] = ()
    reference_period: str | None = None
    resolution_degrees: float | None = None
    minimum_share_percent: float | None = None
    summary_source: SourceReference | None = None
    classification_source: SourceReference | None = None

    def __str__(self) -> str:
        zones = ", ".join(
            f"{zone.code} {zone.share_percent:.0f}%" if zone.share_percent >= 1 else f"{zone.code} {zone.share_percent:.1f}%"
            for zone in self.koppen_geiger_zones
        )
        return zones or self.summary or "climate unknown"

    def __repr__(self) -> str:
        return friendly_repr(self, f"{str(self)!r}")

    @property
    def dominant_zone(self) -> ClimateZone | None:
        """Return the largest represented Köppen-Geiger class, if available."""
        return self.koppen_geiger_zones[0] if self.koppen_geiger_zones else None

    @property
    def zone_codes(self) -> tuple[str, ...]:
        """Return represented Köppen-Geiger codes in descending area share."""
        return tuple(zone.code for zone in self.koppen_geiger_zones)


@dataclass(frozen=True, slots=True)
class PhysicalGeography:
    """Structured physical facts extracted for a country or area profile.

    Rivers and lakes are source-listed major features, not exhaustive
    inventories. A missing tuple means that the source did not list a feature;
    it does not assert that the feature does not exist.
    """

    coastline_km: float | None = None
    mean_elevation_m: float | None = None
    highest_point: ElevationPoint | None = None
    lowest_point: ElevationPoint | None = None
    rivers: tuple[River, ...] = ()
    lakes: tuple[Lake, ...] = ()
    climate: ClimateProfile = ClimateProfile()
    source: SourceReference | None = None
    source_locator: str | None = None

    def __repr__(self) -> str:
        return friendly_repr(self, f"coastline_km={self.coastline_km!r}, highest_point={str(self.highest_point) if self.highest_point else None!r}, rivers={len(self.rivers)}, lakes={len(self.lakes)}")

    @property
    def is_coastal(self) -> bool | None:
        """Return whether the sourced coastline is positive, or ``None``."""
        return self.coastline_km > 0 if self.coastline_km is not None else None

    @property
    def is_landlocked(self) -> bool | None:
        """Return whether the source reports zero coastline, or ``None``."""
        coastal = self.is_coastal
        return None if coastal is None else not coastal


@dataclass(frozen=True, slots=True)
class Geography:
    """Core geographic classification and physical measurements."""

    continent: str | None
    region: str | None
    subregion: str | None
    area: Area = Area()
    landlocked: bool | None = None
    physical: PhysicalGeography = PhysicalGeography()

    def __str__(self) -> str:
        place = " · ".join(dict.fromkeys(part for part in (self.continent, self.region, self.subregion) if part))
        return f"{place} · {self.area}" if place else str(self.area)

    def __repr__(self) -> str:
        return friendly_repr(self, f"{str(self)!r}")
