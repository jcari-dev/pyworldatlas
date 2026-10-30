"""Metric names, units, sources, and per-country values for :meth:`Atlas.rank`.

Each metric has one unit and one named source, so every ranking row can say
where its number comes from. Statistics from the statistics pack are ranked
separately in :mod:`pyworldatlas.atlas`, because they are dated by year.
"""

from __future__ import annotations

from collections.abc import Callable

from .models import Country

METRIC_ALIASES = {
    "area_km2": "area",
    "density": "population_density",
    "land_area_km2": "land_area",
    "water_area_km2": "water_area",
    "coastline_km": "coastline",
    "mean_elevation_m": "mean_elevation",
    "highest_point": "highest_elevation",
    "lowest_point": "lowest_elevation",
}
METRIC_UNITS = {
    "population": "people",
    "area": "km²",
    "population_density": "people/km²",
    "border_count": "countries",
    "major_city_count": "places",
    "land_area": "km²",
    "water_area": "km²",
    "water_percent": "%",
    "coastline": "km",
    "mean_elevation": "m",
    "highest_elevation": "m",
    "lowest_elevation": "m",
    "river_count": "rivers",
    "lake_count": "lakes",
    "climate_zone_count": "classes",
}

_FACTBOOK = "CIA World Factbook"
METRIC_SOURCES = {
    "population": "GeoNames country population snapshot",
    "area": "CIA World Factbook, or GeoNames where it has no value",
    "population_density": "GeoNames population divided by total area",
    "border_count": "PyWorldAtlas reviewed land-border graph",
    "major_city_count": "GeoNames",
    "land_area": _FACTBOOK,
    "water_area": _FACTBOOK,
    "water_percent": "CIA World Factbook water area divided by total area",
    "coastline": _FACTBOOK,
    "mean_elevation": _FACTBOOK,
    "highest_elevation": _FACTBOOK,
    "lowest_elevation": _FACTBOOK,
    "river_count": _FACTBOOK,
    "lake_count": _FACTBOOK,
    "climate_zone_count": "Köppen-Geiger 1991-2020 maps (Beck et al.)",
}
"""Where each ranking metric comes from, shown on every :class:`CountryRanking`."""


def normalize_metric(metric: str) -> str:
    """Resolve a documented metric name or alias, or raise ``ValueError``."""
    normalized_metric = METRIC_ALIASES.get(metric.casefold(), metric.casefold())
    if normalized_metric not in METRIC_UNITS:
        raise ValueError(
            "metric must be a documented population, area, border, city, "
            "coastline, elevation, physical-feature, or climate-zone metric"
        )
    return normalized_metric


def metric_value(
    country: Country, metric: str, border_count: Callable[[Country], int]
) -> int | float | None:
    """Return one country's value for a normalized metric, or ``None`` if missing."""
    if metric == "population":
        return country.population
    if metric == "area":
        return country.area_km2
    if metric == "population_density":
        return country.population_density
    if metric == "border_count":
        return border_count(country)
    if metric == "major_city_count":
        return country.major_city_count
    if metric == "land_area":
        return country.land_area_km2
    if metric == "water_area":
        return country.water_area_km2
    if metric == "water_percent":
        return country.water_percent
    if metric == "coastline":
        return country.coastline_km
    if metric == "mean_elevation":
        return country.mean_elevation_m
    if metric == "highest_elevation":
        return country.highest_point.elevation_m if country.highest_point else None
    if metric == "lowest_elevation":
        return country.lowest_point.elevation_m if country.lowest_point else None
    if metric == "river_count":
        return len(country.rivers) if country.rivers else None
    if metric == "lake_count":
        return len(country.lakes) if country.lakes else None
    return (
        len(country.climate.koppen_geiger_zones)
        if country.climate.koppen_geiger_zones
        else None
    )
