from pyworldatlas import Atlas

with Atlas() as atlas:
    japan = atlas.country("Japan")
    print(japan.name, japan.alpha2, japan.capital.name)

