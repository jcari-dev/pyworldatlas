"""A compact tour of country profiles, rankings, and distances."""

from pyworldatlas import Atlas


with Atlas() as atlas:
    brazil = atlas.country("Brazil")
    print(f"{brazil.flag} {brazil.name_in('pt')} — {brazil.capital.name}")
    print(f"Anthem: {brazil.anthem.title} ({brazil.anthem.english_title})")
    print(f"Motto: {brazil.motto.text} — {brazil.motto.english_text}")
    print(f"Currency: {brazil.currency.name} ({brazil.currency.symbol})")

    print("\nLargest population snapshots:")
    for result in atlas.rank("population", limit=5):
        print(f"{result.position}. {result.country.name}: {result.value:,}")

    print("\nCapitals nearest to Tokyo:")
    for result in atlas.nearest_capitals("Tokyo", country="JP", limit=3):
        print(f"{result.capital.name}: {result.distance:,.0f} km")
