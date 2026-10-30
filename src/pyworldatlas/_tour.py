"""The short tour printed by ``atlas.help()`` and ``pyworldatlas tour``.

Every line starting with ``atlas.`` is a real call; a test runs each one, so
the tour can never drift from the API.
"""

TOUR = """\
PyWorldAtlas: things to try

  from pyworldatlas import Atlas
  atlas = Atlas()

Look things up
  atlas["Japan"]                               a country profile
  atlas.find("Georgia")                        anything by name
  atlas.city("Lagos")                          one city

Measure
  atlas.distance_between("Paris", "Tokyo")     great-circle distance
  atlas.cities_near("Lima", limit=3)           closest cities
  atlas.antipode("Madrid")                     the other side of the Earth
  atlas.sun("Reykjavik")                       sunrise and sunset today

Compare
  atlas.rank("area", limit=5)                  biggest countries
  atlas.countries(continent="Africa", coastal=False)
  atlas.border_path("France", "China")         crossing borders by land

Learn
  atlas.quiz("capitals", count=3)              multiple-choice questions
  atlas.flashcards("flags", count=3)           flashcards

Numbers and maps (first run: pyworldatlas get statistics)
  atlas.rank("life_expectancy", year=2020, limit=5)
  atlas.world_map("life_expectancy").show()    opens in your browser

Print any result for a short answer. show_details() shows every field."""
