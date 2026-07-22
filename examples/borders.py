"""Explore reviewed land borders and a shortest border path."""

from pyworldatlas import Atlas


with Atlas() as atlas:
    france = atlas.neighbors("France")
    print("France:", ", ".join(country.name for country in france))

    path = atlas.border_path("Portugal", "China")
    if path is not None:
        route = " -> ".join(path.names)
        print(f"{path.crossings} crossings: {route}")
        print("Codes:", " -> ".join(path.alpha2_codes))

    print("Japan to China by land:", atlas.border_path("Japan", "China"))
    print("Portugal and China are land-connected:", atlas.has_land_route("Portugal", "China"))

    card = atlas.flashcards(topic="neighbors", count=1, seed=42)[0]
    print(card.prompt)
    print(card.answer)
