"""Inspect the typed reference facts attached to a country profile."""

from pyworldatlas import Atlas


with Atlas() as atlas:
    japan = atlas.country("Japan")

    print(japan.flag, japan.name, japan.name_in("ja"))
    print(japan.anthem)
    print(japan.demonym)
    print(japan.currency)
    print(japan.languages)
    print(japan.timezones)
    print(japan.postal_code)

    # Every fact-bearing record keeps a source reference.
    print(japan.anthem.source.name)
    print(japan.currency.source.license_name)
