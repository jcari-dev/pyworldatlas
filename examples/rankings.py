"""Filter profiles, rank sourced values, and find nearby capitals."""

from pyworldatlas import Atlas


with Atlas() as atlas:
    yen_profiles = atlas.countries(currency_code="JPY")
    print([country.name for country in yen_profiles])

    for result in atlas.rank("area", limit=5):
        print(result.position, result.country.name, result.value, result.unit)

    for result in atlas.capitals_near((18.4861, -69.9312), limit=4):
        print(result.country.name, result.capital.name, round(result.distance), result.unit)
