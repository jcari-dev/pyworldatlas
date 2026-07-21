"""Inspect useful fields on a rich country profile."""

from pyworldatlas import Atlas


with Atlas() as atlas:
    japan = atlas.country("Japan")
    print(japan.name, japan.alpha2)
    print("Population snapshot:", japan.population)
    if japan.currency is not None:
        print("Currency:", japan.currency.code, japan.currency.name)
    print("Languages:", ", ".join(language.code for language in japan.languages))
    print("Calling codes:", ", ".join(japan.calling_codes))
    if japan.capital_coordinates is not None:
        print("Capital coordinates:", japan.capital_coordinates.as_tuple())
