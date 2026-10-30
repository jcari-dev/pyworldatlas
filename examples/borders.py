"""Explore reviewed land borders and a shortest border path."""

from pyworldatlas import Atlas


with Atlas() as atlas:
    france = atlas.neighbors("France")
    print("France:", ", ".join(country.name for country in france))

    path = atlas.border_path("Portugal", "Poland")
    if path is not None:
        route = " -> ".join(path.names)
        print(f"{path.crossings} crossings: {route}")
        print("Codes:", " -> ".join(path.alpha2_codes))

    print("Japan to Iceland by land:", atlas.border_path("Japan", "Iceland"))
    print("Portugal and Austria are land-connected:", atlas.has_land_route("Portugal", "Austria"))

    card = atlas.flashcards(topic="neighbors", count=1, seed=17)[0]
    print(card.prompt)
    print(card.answer)
