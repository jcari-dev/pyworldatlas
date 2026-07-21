"""Explore and validate everything in the current PyWorldAtlas checkout.

Run this file with VS Code's "Run Python File" button or press F5 and choose
"PyWorldAtlas: Full Playground". The default run validates every country,
capital, and major-city record before showing each part of the public API.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys
from typing import Iterable


# A repository playground should work from VS Code immediately, even before the
# project has been installed into the selected virtual environment. Installed
# package usage remains unchanged; this fallback applies only to this script.
try:
    from pyworldatlas import Atlas, Country
except ModuleNotFoundError as error:
    if error.name != "pyworldatlas":
        raise
    sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
    from pyworldatlas import Atlas, Country


LINE = "=" * 88
SUBLINE = "-" * 88

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def heading(title: str) -> None:
    """Print a clear playground section heading."""
    print(f"\n{LINE}\n{title}\n{LINE}")


def number(value: int | float | None) -> str:
    """Format an optional number for terminal output."""
    if value is None:
        return "unknown"
    return f"{value:,.0f}" if isinstance(value, (int, float)) else str(value)


def audit_every_record(atlas: Atlas) -> dict[str, int]:
    """Validate every country and every stored capital and city record."""
    countries = tuple(atlas)
    alpha2_codes: set[str] = set()
    alpha3_codes: set[str] = set()
    numeric_codes: set[str] = set()
    geonames_ids: set[int] = set()
    capital_count = 0
    missing_capital_count = 0
    city_count = 0
    local_name_count = 0
    population_profile_count = 0

    assert countries, "The dataset must contain at least one country"
    assert tuple(country.name for country in countries) == tuple(
        sorted(country.name for country in countries)
    ), "Country iteration must be alphabetical"

    for country in countries:
        assert country.name.strip(), f"Blank country name: {country!r}"
        assert len(country.alpha2) == 2 and country.alpha2.isupper()
        assert country.alpha2 not in alpha2_codes, f"Duplicate alpha-2 code: {country.alpha2}"
        alpha2_codes.add(country.alpha2)

        if country.alpha3 is not None:
            assert len(country.alpha3) == 3 and country.alpha3.isupper()
            assert country.alpha3 not in alpha3_codes, f"Duplicate alpha-3 code: {country.alpha3}"
            alpha3_codes.add(country.alpha3)

        if country.codes.numeric is not None:
            assert len(country.codes.numeric) == 3 and country.codes.numeric.isdigit()
            assert country.codes.numeric not in numeric_codes
            numeric_codes.add(country.codes.numeric)

        assert country.names, f"{country.name} has no sourced names"
        assert country.sources, f"{country.name} has no source references"
        assert country.population is None or country.population >= 0
        if country.population is not None:
            population_profile_count += 1
        assert country.currency is None or len(country.currency.code) == 3
        assert country.top_level_domain is None or country.top_level_domain.startswith(".")
        assert all(code.startswith("+") for code in country.calling_codes)
        assert all(language.code for language in country.languages)
        for local_name in country.local_names:
            local_name_count += 1
            assert local_name.language_code
            assert local_name.language_name
            assert local_name.script_code
            assert local_name.short_name
            assert local_name.official_name
            assert local_name.source is not None
        if country.capital is None:
            missing_capital_count += 1

        for capital in country.capitals:
            capital_count += 1
            assert capital.country_code == country.alpha2
            assert -90 <= capital.coordinates.latitude <= 90
            assert -180 <= capital.coordinates.longitude <= 180
            assert capital.name.strip()

        for city in country.major_cities:
            city_count += 1
            assert city.country_code == country.alpha2
            assert city.name.strip()
            assert -90 <= city.coordinates.latitude <= 90
            assert -180 <= city.coordinates.longitude <= 180
            assert city.population is None or city.population >= 0
            if city.geonames_id is not None:
                assert city.geonames_id not in geonames_ids, (
                    f"Duplicate GeoNames ID: {city.geonames_id}"
                )
                geonames_ids.add(city.geonames_id)

    return {
        "countries": len(countries),
        "capitals": capital_count,
        "missing_capitals": missing_capital_count,
        "major_cities": city_count,
        "unique_geonames_ids": len(geonames_ids),
        "local_names": local_name_count,
        "population_profiles": population_profile_count,
    }


def print_dataset_overview(atlas: Atlas, audit: dict[str, int]) -> None:
    """Show version metadata and full-record audit results."""
    info = atlas.dataset_info()
    heading(f"PYWORLDATLAS {info.library_version} — DATASET AND FULL-RECORD AUDIT")
    print(f"Library version : {info.library_version}")
    print(f"Schema version  : {info.schema_version}")
    print(f"Dataset version : {info.dataset_version}")
    print(f"Dataset built   : {info.built_at}")
    print(f"Countries tested: {audit['countries']}")
    print(f"Capitals tested : {audit['capitals']}")
    print(f"Without capital : {audit['missing_capitals']} explicit missing values")
    print(f"Cities tested   : {audit['major_cities']}")
    print(f"GeoNames IDs    : {audit['unique_geonames_ids']} unique")
    print(f"Local names     : {audit['local_names']} sourced records")
    print(f"Rich profiles   : {audit['population_profiles']} with population snapshots")
    print("Result          : PASS — every currently exposed record was checked")


def print_country_directory(countries: Iterable[Country]) -> None:
    """Print a compact directory covering the entire current country scope."""
    heading("ALL COUNTRIES CURRENTLY INCLUDED")
    print(f"{'Flag':<6} {'Code':<8} {'Country':<24} {'Capital':<20} {'Cities':>7}  Continent")
    print(SUBLINE)
    for country in countries:
        capital = country.capital.name if country.capital else "unknown"
        print(
            f"{country.flag:<6} {country.alpha2 + '/' + (country.alpha3 or '---'):<8} "
            f"{country.name:<24} {capital:<20} {len(country.major_cities):>7}  "
            f"{country.continent or 'unknown'}"
        )


def print_lookup_showcase(atlas: Atlas) -> None:
    """Demonstrate lookup, aliases, collection behavior, search, and filters."""
    heading("LOOKUP, ALIASES, COLLECTION PROTOCOL, SEARCH, AND FILTERS")
    examples = ("Japan", "JP", "JPN", "392", "USA", "Holy See", "Bolivia")
    for query in examples:
        result = atlas.country(query)
        print(f"atlas.country({query!r:<12}) -> {result!r}")

    print("\nCollection behavior:")
    print(f"  atlas['DO']          -> {atlas['DO']!r}")
    print(f"  'France' in atlas    -> {'France' in atlas}")
    print(f"  'Atlantis' in atlas  -> {'Atlantis' in atlas}")
    print(f"  atlas.get('Atlantis')-> {atlas.get('Atlantis')}")
    print(f"  len(atlas)           -> {len(atlas)}")

    print("\nSearch for 'united':")
    for match in atlas.search_countries("united"):
        print(
            f"  score={match.score:<3} matched={match.matched_name!r:<28} "
            f"country={match.country.name}"
        )

    continents = sorted({country.continent for country in atlas if country.continent})
    print("\nContinent filters:")
    for continent in continents:
        names = ", ".join(country.name for country in atlas.countries(continent=continent))
        print(f"  {continent:<10}: {names}")


def print_coordinate_showcase(atlas: Atlas) -> None:
    """Demonstrate city lookup and great-circle calculations."""
    heading("LATITUDE, LONGITUDE, DISTANCE, BEARING, AND MIDPOINTS")
    tokyo = atlas.city("Tokyo", country="Japan")
    paris = atlas.city("Paris", country="France")
    distance_km = atlas.distance_between(tokyo, paris)
    distance_mi = atlas.distance_between(tokyo, paris, unit="mi")
    midpoint = tokyo.coordinates.midpoint_to(paris.coordinates)
    print(f"Tokyo coordinates : {tokyo.coordinates.as_tuple()}")
    print(f"Paris coordinates : {paris.coordinates.as_tuple()}")
    print(f"Great-circle route: {distance_km:,.1f} km / {distance_mi:,.1f} mi")
    print(f"Initial bearing   : {tokyo.coordinates.bearing_to(paris.coordinates):.1f}°")
    print(f"Spherical midpoint: {midpoint.as_tuple()}")
    print(f"Named-place API   : atlas.distance_between('Tokyo', 'Paris', first_country='JP', second_country='FR')")


def print_country_profile(country: Country, *, all_cities: bool = False) -> None:
    """Print every field currently available on one country profile."""
    heading(f"{country.flag}  {country.name.upper()} — COMPLETE CURRENT PROFILE")
    print(f"Python object : {country!r}")
    print(f"Official name : {country.official_name or 'unknown'}")
    print(f"Status        : {country.status.value}")
    print(
        f"Codes         : alpha-2={country.codes.alpha2}, alpha-3={country.codes.alpha3}, "
        f"M49={country.codes.numeric}, GeoNames={country.codes.geonames}"
    )
    print(f"Continent     : {country.continent or 'unknown'}")
    print(f"Region        : {country.region or 'unknown'}")
    print(f"Subregion     : {country.subregion or 'unknown'}")
    print(f"Area          : {number(country.area_km2)} km²")
    print(f"Population    : {number(country.population)} (source snapshot)")
    currency = f"{country.currency.code} — {country.currency.name or 'name unavailable'}" if country.currency else "unknown"
    print(f"Currency      : {currency}")
    print(f"Languages     : {', '.join(language.code for language in country.languages) or 'unknown'}")
    print(f"Calling codes : {', '.join(country.calling_codes) or 'unknown'}")
    print(f"Internet TLD  : {country.top_level_domain or 'unknown'}")
    print(f"Timezones seen: {', '.join(country.observed_timezones) or 'none in stored cities'}")
    print(f"Capital lat/lon: {country.capital_coordinates.as_tuple() if country.capital_coordinates else 'unknown'}")
    print(f"Aliases       : {', '.join(country.aliases) if country.aliases else 'none'}")

    print("\nSourced names:")
    for name in country.names:
        marker = "preferred" if name.preferred else name.kind
        print(f"  - {name.text} [{marker}]")

    print("\nOfficial local names:")
    if not country.local_names:
        print("  - not yet covered by the Country Discovery data family")
    for name in country.local_names:
        print(
            f"  - {name.language_name} ({name.language_code}, {name.script_code}): "
            f"{name.short_name} — {name.official_name}"
        )
        print(f"    source: {name.source.name} ({name.source.id})")

    print("\nCapital records:")
    for capital in country.capitals:
        print(
            f"  - {capital.name}: {capital.coordinates.as_tuple()}, role={capital.role}, "
            f"population={number(capital.population)}, elevation={number(capital.elevation_m)} m, "
            f"timezone={capital.timezone_id}, GeoNames={capital.geonames_id}"
        )

    city_limit = None if all_cities else 5
    cities = country.major_cities if city_limit is None else country.major_cities[:city_limit]
    label = "all" if all_cities else f"top {len(cities)}"
    print(f"\nMajor cities ({len(country.major_cities)} stored; showing {label}):")
    for city in cities:
        print(
            f"  - {city.name:<24} population={number(city.population):>12}  "
            f"coordinates={city.coordinates.as_tuple()}  timezone={city.timezone_id}"
        )

    print("\nSources used:")
    for source in country.sources:
        print(f"  - {source.name} ({source.id}), retrieved {source.retrieved_at}")
        print(f"    {source.homepage}")


def print_serialization_showcase(atlas: Atlas) -> None:
    """Show that public objects serialize to JSON-compatible primitives."""
    country = atlas.country("Japan")
    data = country.to_dict()
    data["major_cities"] = data["major_cities"][:2]
    data["major_cities_note"] = (
        f"Showing 2 of {len(country.major_cities)} cities in this terminal preview"
    )
    heading("SERIALIZATION PREVIEW — COUNTRY.TO_DICT() / JSON")
    print(json.dumps(data, ensure_ascii=False, indent=2))


def print_coverage(atlas: Atlas) -> None:
    """Summarize geographic and source coverage across the current dataset."""
    countries = tuple(atlas)
    continent_counts = Counter(country.continent or "unknown" for country in countries)
    source_counts = Counter(source.name for country in countries for source in country.sources)
    heading("CURRENT COVERAGE SUMMARY")
    print("Countries by continent:")
    for name, count in sorted(continent_counts.items()):
        print(f"  {name:<10}: {count}")
    print("\nCountry profiles referencing each source:")
    for name, count in sorted(source_counts.items()):
        print(f"  {name:<24}: {count}")
    print("\nHonest milestone boundary:")
    print("  Implemented now : identity, aliases, codes, regions, capitals, coordinates,")
    print("                    area, population, currency, language/calling codes,")
    print("                    major cities, distance, bearing, midpoint, serialization,")
    print("                    and a Brazil/Switzerland official-local-name pilot,")
    print("                    and full UN M49 country-and-area coverage")
    print("  Coming later    : borders, boundary geometry, historical statistics, leaders,")
    print("                    rich culture, quizzes, exports, and release hardening")


def parse_args() -> argparse.Namespace:
    """Parse optional focused-playground arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--country", help="show one country instead of all country profiles")
    parser.add_argument(
        "--all-cities", action="store_true", help="print every stored city instead of the top five"
    )
    parser.add_argument("--json", metavar="COUNTRY", help="print the complete country JSON and exit")
    parser.add_argument("--audit-only", action="store_true", help="validate all records and print only the audit")
    return parser.parse_args()


def main() -> int:
    """Run the full or focused PyWorldAtlas playground."""
    args = parse_args()
    with Atlas() as atlas:
        if args.json:
            print(atlas.country(args.json).to_json(indent=2))
            return 0

        audit = audit_every_record(atlas)
        print_dataset_overview(atlas, audit)
        if args.audit_only:
            return 0

        countries = tuple(atlas)
        print_country_directory(countries)
        print_lookup_showcase(atlas)
        print_coordinate_showcase(atlas)

        if args.country:
            print_country_profile(atlas.country(args.country), all_cities=args.all_cities)
        else:
            for country in countries:
                print_country_profile(country, all_cities=args.all_cities)

        print_serialization_showcase(atlas)
        print_coverage(atlas)

    heading("PLAYGROUND COMPLETE")
    print("Everything currently available through the checkout's public API ran successfully.")
    print("Tip: run `playground.py --help` for focused country, JSON, and all-city modes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
