"""Explore reviewed land borders and a shortest border path."""

from pyworldatlas import Atlas


with Atlas() as atlas:
    france = atlas.neighbors("France")
    print("France:", ", ".join(country.name for country in france))

    path = atlas.border_path("Portugal", "China")
    if path is not None:
        route = " -> ".join(country.name for country in path.countries)
        print(f"{path.crossings} crossings: {route}")

    print("Japan to China by land:", atlas.border_path("Japan", "China"))
