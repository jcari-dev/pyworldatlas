from pyworldatlas import Atlas

with Atlas() as atlas:
    for match in atlas.search_countries("united"):
        print(match.country.name, match.country.alpha2)

