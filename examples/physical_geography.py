"""Explore physical geography without a network connection."""

from pyworldatlas import Atlas


with Atlas() as atlas:
    brazil = atlas.country("Brazil")
    print(
        brazil.flag,
        brazil.name,
        f"{brazil.land_area_km2:,.0f} km² of land",
        f"{brazil.water_area_km2:,.0f} km² of water",
    )
    print(
        "Highest point:",
        brazil.highest_point.name,
        f"({brazil.highest_point.elevation_m:,.0f} m)",
    )
    print("Source-listed rivers:", ", ".join(river.name for river in brazil.rivers))
    print("Climate classes:", ", ".join(brazil.climate.zone_codes))

    print(
        "Amazon profiles:",
        ", ".join(country.name for country in atlas.countries_with_river("Amazon")),
    )
    print(
        "Lake Geneva profiles:",
        ", ".join(country.name for country in atlas.countries_with_lake("Geneva")),
    )

    print("Longest sourced coastlines:")
    for row in atlas.rank("coastline", limit=5):
        print(f"{row.position}. {row.country.name}: {row.value:,.0f} {row.unit}")
