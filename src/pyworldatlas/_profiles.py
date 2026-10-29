"""Build immutable country and place models from database rows."""

from __future__ import annotations

from collections.abc import Callable
import json
import sqlite3
from typing import overload

from .models import (Area, Capital, City, ClimateProfile, ClimateZone, Coordinate,
                     Country, CountryCodes, Currency, Demonym, ElevationPoint,
                     Geography, Lake, Language, LocalizedName, NationalAnthem,
                     NationalMotto, PhysicalGeography, PostalCodeFormat, River,
                     SourceReference, Timezone, TravelBasics)


@overload
def _tidy(value: float) -> float: ...


@overload
def _tidy(value: None) -> None: ...


def _tidy(value: float | None) -> float | None:
    """Return a whole number as an ``int`` (``377915.0`` becomes ``377915``).

    Sources store measurements as decimals even when they are whole, which
    prints as ``3776.0 m``. Values with a real fraction, such as Vatican City's
    0.49 km², are kept exactly.
    """
    if value is None:
        return None
    return int(value) if float(value).is_integer() else value


def flag(alpha2: str) -> str:
    """Return the regional-indicator flag emoji for an alpha-2 code."""
    return "".join(chr(0x1F1E6 + ord(letter) - ord("A")) for letter in alpha2)


def city_from_row(row: sqlite3.Row) -> City:
    """Build one populated place from a city row joined with its country code."""
    return City(row["name"], row["alpha2"], Coordinate(row["latitude"], row["longitude"]), row["population"], _tidy(row["elevation_m"]), row["timezone_id"], ("official",) if row["is_capital"] else (), row["geonames_id"])


def build_country(
    row: sqlite3.Row,
    child_rows: Callable[[str], list[sqlite3.Row]],
    local_names: tuple[LocalizedName, ...],
) -> Country:
    """Build one complete profile from its country row and per-country queries.

    ``child_rows`` runs a query whose only parameter is the country id, either
    directly or from a bulk read shared by every profile.
    """
    names_rows = child_rows("SELECT * FROM country_name WHERE country_id=? ORDER BY preferred DESC, kind, name")
    names = tuple(LocalizedName(n["name"], n["language_code"], n["kind"], bool(n["preferred"])) for n in names_rows)
    aliases = tuple(n.text for n in names if n.kind == "alias")
    capital_rows = child_rows("SELECT * FROM capital WHERE country_id=? ORDER BY is_primary DESC, name")
    capitals = tuple(Capital(c["name"], row["alpha2"], Coordinate(c["latitude"], c["longitude"]), c["role"], bool(c["is_primary"]), c["population"], _tidy(c["elevation_m"]), c["timezone_id"], c["geonames_id"]) for c in capital_rows)
    city_rows = child_rows("SELECT * FROM city WHERE country_id=? ORDER BY population DESC, name")
    cities = tuple(City(c["name"], row["alpha2"], Coordinate(c["latitude"], c["longitude"]), c["population"], _tidy(c["elevation_m"]), c["timezone_id"], ("official",) if c["is_capital"] else (), c["geonames_id"]) for c in city_rows)
    source_rows = child_rows("SELECT DISTINCT f.country_id AS country_id, s.* FROM source s JOIN field_source f ON f.source_id=s.id WHERE f.country_id=? ORDER BY s.id")
    sources = tuple(
        SourceReference(
            s["id"], s["name"], s["homepage"], s["retrieved_at"],
            s["version"], s["license_name"], s["license_url"], s["notes"],
        )
        for s in source_rows
    )
    source_by_id = {source.id: source for source in sources}
    physical_row = next(iter(child_rows("SELECT * FROM country_physical WHERE country_id=?")), None)
    river_rows = child_rows("SELECT * FROM country_river WHERE country_id=? ORDER BY length_km DESC, name")
    lake_rows = child_rows("SELECT * FROM country_lake WHERE country_id=? ORDER BY area_km2 DESC, name")
    climate_rows = child_rows("SELECT * FROM country_climate_zone WHERE country_id=? ORDER BY position")
    zones = tuple(
        ClimateZone(
            item["code"], item["name"], item["climate_group"],
            item["share_percent"],
        )
        for item in climate_rows
    )
    climate = ClimateProfile(
        summary=physical_row["climate_summary"] if physical_row else None,
        koppen_geiger_zones=zones,
        reference_period=climate_rows[0]["reference_period"] if climate_rows else None,
        resolution_degrees=climate_rows[0]["resolution_degrees"] if climate_rows else None,
        minimum_share_percent=(
            climate_rows[0]["minimum_share_percent"] if climate_rows else None
        ),
        summary_source=source_by_id.get("cia-world-factbook-2025"),
        classification_source=source_by_id.get("koppen-geiger-1991-2020"),
    )
    highest_point = (
        ElevationPoint(
            physical_row["highest_point_name"],
            _tidy(physical_row["highest_point_elevation_m"]),
            bool(physical_row["highest_point_is_approximate"]),
            physical_row["highest_point_source_label"],
        )
        if physical_row and physical_row["highest_point_name"]
        else None
    )
    lowest_point = (
        ElevationPoint(
            physical_row["lowest_point_name"],
            _tidy(physical_row["lowest_point_elevation_m"]),
            bool(physical_row["lowest_point_is_approximate"]),
            physical_row["lowest_point_source_label"],
        )
        if physical_row and physical_row["lowest_point_name"]
        else None
    )
    physical = PhysicalGeography(
        coastline_km=_tidy(physical_row["coastline_km"]) if physical_row else None,
        mean_elevation_m=(
            _tidy(physical_row["mean_elevation_m"]) if physical_row else None
        ),
        highest_point=highest_point,
        lowest_point=lowest_point,
        rivers=tuple(
            River(item["name"], _tidy(item["length_km"]), item["source_label"])
            for item in river_rows
        ),
        lakes=tuple(
            Lake(
                item["name"], _tidy(item["area_km2"]), item["water_type"],
                item["source_label"],
            )
            for item in lake_rows
        ),
        climate=climate,
        source=source_by_id.get("cia-world-factbook-2025"),
        source_locator=physical_row["source_locator"] if physical_row else None,
    )
    land_area = _tidy(physical_row["land_area_km2"]) if physical_row else None
    water_area = _tidy(physical_row["water_area_km2"]) if physical_row else None
    total_area = _tidy(row["total_area_km2"])
    water_percent = (
        round(water_area / total_area * 100, 2)
        if water_area is not None
        and total_area is not None
        and total_area > 0
        and water_area <= total_area
        else None
    )
    geography = Geography(
        continent=row["continent"],
        region=row["region"],
        subregion=row["subregion"],
        area=Area(total_area, land_area, water_area, water_percent),
        landlocked=physical.is_landlocked,
        physical=physical,
    )
    currency = (
        Currency(
            row["currency_code"], row["currency_name"], row["currency_symbol"],
            row["currency_minor_unit_digits"],
            source_by_id.get("unicode-cldr-48.2-reference"),
        )
        if row["currency_code"] else None
    )
    language_rows = child_rows("SELECT * FROM country_language WHERE country_id=? ORDER BY code")
    languages = tuple(
        Language(
            item["code"], item["primary_code"], item["name"], item["script_code"],
            source_by_id.get(item["source_id"]),
        )
        for item in language_rows
    )
    calling_codes = tuple(json.loads(row["calling_codes"]))
    observed_timezones = tuple(sorted({city.timezone_id for city in cities if city.timezone_id}))
    timezone_rows = child_rows("SELECT * FROM country_timezone WHERE country_id=? ORDER BY timezone_id")
    timezones = tuple(
        Timezone(
            item["timezone_id"], item["january_utc_offset_hours"],
            item["july_utc_offset_hours"], item["raw_utc_offset_hours"],
            source_by_id.get(item["source_id"]),
        )
        for item in timezone_rows
    )
    anthem_rows = child_rows("SELECT * FROM country_anthem WHERE country_id=? ORDER BY title")
    anthems = tuple(
        NationalAnthem(
            item["title"], item["english_title"], source_by_id[item["source_id"]],
            item["source_locator"],
        )
        for item in anthem_rows
    )
    motto_rows = child_rows("SELECT * FROM country_motto WHERE country_id=? ORDER BY text")
    mottos = tuple(
        NationalMotto(
            item["text"], item["language_code"], item["english_text"],
            source_by_id[item["source_id"]], item["source_locator"],
        )
        for item in motto_rows
    )
    demonym_rows = child_rows("SELECT * FROM country_demonym WHERE country_id=? ORDER BY language_code")
    demonyms = tuple(
        Demonym(
            item["noun"], item["adjective"], item["language_code"],
            source_by_id[item["source_id"]], item["source_locator"],
        )
        for item in demonym_rows
    )
    travel_row = next(iter(child_rows("SELECT * FROM country_travel WHERE country_id=?")), None)
    travel = (
        TravelBasics(
            tuple(filter(None, travel_row["plug_types"].split(","))),
            tuple(int(value) for value in filter(None, travel_row["voltages_v"].split(","))),
            tuple(int(value) for value in filter(None, travel_row["frequencies_hz"].split(","))),
            travel_row["driving_side"],
            source_by_id.get(travel_row["source_id"]),
        )
        if travel_row else None
    )
    postal_code = (
        PostalCodeFormat(
            row["postal_code_format"], row["postal_code_regex"],
            source_by_id.get("geonames"),
        )
        if row["postal_code_format"] else None
    )
    formal_name = next((name.text for name in names if name.kind == "formal"), None)
    return Country(
        name=row["name"],
        official_name=row["official_name"],
        names=names,
        aliases=aliases,
        codes=CountryCodes(row["alpha2"], row["alpha3"], row["numeric_code"], row["geonames_id"]),
        flag=flag(row["alpha2"]),
        geography=geography,
        capitals=capitals,
        major_cities=cities,
        sources=sources,
        local_names=local_names,
        population=row["population"],
        currency=currency,
        languages=languages,
        calling_codes=calling_codes,
        top_level_domain=row["top_level_domain"],
        observed_timezones=observed_timezones,
        formal_name=formal_name,
        anthems=anthems,
        mottos=mottos,
        demonyms=demonyms,
        timezones=timezones,
        postal_code=postal_code,
        travel=travel,
    )


def read_local_names(connection: sqlite3.Connection) -> dict[int, tuple[LocalizedName, ...]]:
    """Read every local identity name, grouped by country id."""
    rows = connection.execute(
        """SELECT n.*, s.name AS source_name, s.homepage, s.retrieved_at
           FROM country_local_name n JOIN source s ON s.id=n.source_id
           ORDER BY n.country_id, n.language_code"""
    ).fetchall()
    grouped: dict[int, list[LocalizedName]] = {}
    for row in rows:
        source = SourceReference(row["source_id"], row["source_name"], row["homepage"], row["retrieved_at"])
        grouped.setdefault(int(row["country_id"]), []).append(
            LocalizedName(
                text=row["short_name"],
                language_code=row["language_code"],
                kind=row["name_kind"],
                preferred=True,
                language_name=row["language_name"],
                script_code=row["script_code"],
                official_name=row["official_name"],
                romanized_short_name=row["romanized_short_name"],
                romanized_official_name=row["romanized_official_name"],
                is_official_language=bool(row["is_official_language"]),
                source=source,
                source_locator=row["source_locator"],
                language_status=row["language_status"],
            )
        )
    return {country_id: tuple(names) for country_id, names in grouped.items()}
