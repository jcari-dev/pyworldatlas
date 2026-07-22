"""A compact tour of country profiles, physical geography, and distances."""

from pyworldatlas import Atlas


with Atlas() as atlas:
    brazil = atlas.country("Brazil")
    print(f"{brazil.flag} {brazil.name_in('pt')} — {brazil.capital.name}")
    print(f"Anthem: {brazil.anthem.title} ({brazil.anthem.english_title})")
    print(f"Motto: {brazil.motto.text} — {brazil.motto.english_text}")
    print(f"Currency: {brazil.currency.name} ({brazil.currency.symbol})")
    print(
        f"Highest point: {brazil.highest_point.name} "
        f"({brazil.highest_point.elevation_m:,.0f} m)"
    )
    print(f"Climate: {brazil.climate.dominant_zone.code} — {brazil.climate.dominant_zone.name}")
    print("Rivers:", ", ".join(river.name for river in brazil.rivers[:3]))

    print("\nLargest population snapshots:")
    for result in atlas.rank("population", limit=5):
        print(f"{result.position}. {result.country.name}: {result.value:,}")

    print("\nLongest sourced coastlines:")
    for result in atlas.rank("coastline", limit=5):
        print(f"{result.position}. {result.country.name}: {result.value:,.0f} km")

    print("\nCapitals nearest to Tokyo:")
    for result in atlas.nearest_capitals("Tokyo", country="JP", limit=3):
        print(f"{result.capital.name}: {result.distance:,.0f} km")
