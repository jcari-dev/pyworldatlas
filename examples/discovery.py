"""Build reproducible country-learning material from the offline atlas."""

from pyworldatlas import Atlas


with Atlas() as atlas:
    japan = atlas.country("Japan")
    card = japan.discovery_card()
    print(card.flag_emoji, card.country.name, card.capital)
    print(f"Population density: {card.population_density:.2f} people/km²")

    sample = atlas.sample_countries(count=3, continent="Africa", seed=42)
    print("Sample:", ", ".join(country.name for country in sample))

    for flashcard in atlas.flashcards(topic="capitals", count=2, seed=42):
        print(f"Q: {flashcard.prompt}")
        print(f"A: {flashcard.answer}")
