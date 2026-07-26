"""A friendly tour of the PyWorldAtlas 0.8 learning helpers."""

from pyworldatlas import Atlas


with Atlas() as atlas:
    print(atlas.country("Brazil").summary())

    print("\nWRITING SYSTEMS AROUND THE WORLD")
    for country_name, language_code in (
        ("Dominican Republic", "es"),
        ("China", "zh"),
        ("India", "hi"),
        ("Japan", "ja"),
    ):
        country = atlas.country(country_name)
        local = country.local_name(language_code)
        print(
            f"{country.flag} {country.name:<20} "
            f"{local.short_name:<24} [{local.script_code}]"
        )

    tokyo = atlas.city("Tokyo", country="JP")
    paris = atlas.city("Paris", country="FR")
    print("\nCOORDINATE LAB")
    print("Tokyo:", tokyo.coordinates.format())
    print("Tokyo in DMS:", tokyo.coordinates.dms())
    print(
        "Tokyo → Paris:",
        f"{tokyo.coordinates.distance_to(paris.coordinates):,.0f} km",
        tokyo.coordinates.compass_direction_to(paris.coordinates),
    )

    print("\nMULTIPLE-CHOICE NAME QUIZ")
    for number, question in enumerate(
        atlas.quiz(topic="local_names", count=2, seed="learning-lab"), 1
    ):
        print(f"{number}. {question.prompt}")
        for choice_number, choice in enumerate(question.choices, 1):
            print(f"   {choice_number}. {choice}")
        print(f"   Answer: {question.answer_number}\n")
