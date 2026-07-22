"""Explore English formal names, local identities, and writing systems."""

import sys

from pyworldatlas import Atlas


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


with Atlas() as atlas:
    print("Three English name fields")
    turkey = atlas.country("TR")
    print("Display:", turkey.name)
    print("Canonical:", turkey.official_name)
    print("Formal:", turkey.formal_name)
    print(len(atlas.countries_with_formal_names()), "formal-name profiles")

    print("\nA reviewed national official name")
    dominican = atlas.country("DO")
    print(dominican.flag, dominican.name, "->", dominican.name_in("es"))
    print("Formal:", dominican.official_name_in("es"))

    print("\nAcross writing systems")
    for code, language in (
        ("AE", "ar"),
        ("CN", "zh"),
        ("IN", "hi"),
        ("JP", "ja"),
    ):
        country = atlas.country(code)
        name = country.local_name(language)
        print(f"{country.flag} {name.short_name} [{name.script_code}]")
        print("  Evidence:", name.kind)
        if name.formal_name:
            print("  Formal:", name.formal_name)
        if name.romanized_short_name:
            print("  Romanized:", name.romanized_short_name)

    print("\nComplete local identity coverage")
    print(len(atlas.countries_with_local_names()), "countries and areas")

    print("\nDisplay name versus formal official name")
    andorra = atlas.country("AD").local_name("ca")
    print(andorra.short_name, andorra.kind)
    print("Formal name reviewed:", andorra.formal_name)
