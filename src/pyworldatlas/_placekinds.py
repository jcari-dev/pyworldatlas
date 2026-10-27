"""Plain-English names for GeoNames feature codes.

Each place has a GeoNames feature code such as ``"T.MT"``. The letter before
the dot is the feature class; the rest names the kind. Codes not listed here
fall back to their class's general name.
"""

from __future__ import annotations

CATEGORIES = {
    "A": "region",
    "H": "water",
    "L": "area",
    "P": "town",
    "R": "route",
    "S": "landmark",
    "T": "landform",
    "U": "undersea",
    "V": "forest",
}

KINDS = {
    # Regions and areas
    "A.ADM1": "state or province", "A.ADM1H": "former state or province",
    "A.ADM2": "county or district", "A.ADM2H": "former county or district",
    "A.ADM3": "municipality", "A.ADM4": "local area", "A.ADM5": "local area",
    "A.ADMD": "administrative area", "A.LTER": "leased area", "A.PCL": "country",
    "A.PCLD": "dependent territory", "A.PCLF": "freely associated state",
    "A.PCLH": "former country", "A.PCLI": "country", "A.PCLIX": "part of a country",
    "A.PCLS": "semi-independent territory", "A.PRSH": "parish", "A.TERR": "territory",
    "A.ZN": "zone", "A.ZNB": "buffer zone",
    "L.AREA": "area", "L.BTL": "battlefield", "L.CONT": "continent", "L.CST": "coast",
    "L.DEVH": "housing area", "L.FLD": "field", "L.GRAZ": "grazing area",
    "L.LCTY": "locality", "L.MILB": "military base", "L.MNA": "mining area",
    "L.OAS": "oasis area", "L.PRK": "park", "L.RESN": "nature reserve",
    "L.RESF": "forest reserve", "L.RESW": "wildlife reserve", "L.RGN": "region",
    "L.RGNE": "economic region", "L.RGNH": "historical region", "L.RES": "reserve",
    "L.RESV": "reservation", "L.PRT": "port", "L.TRB": "tribal area", "L.PEN": "peninsula",
    # Water
    "H.BAY": "bay", "H.BAYS": "bays", "H.BGHT": "bight", "H.CHN": "channel",
    "H.CNL": "canal", "H.COVE": "cove", "H.DLTA": "delta", "H.ESTY": "estuary",
    "H.FJD": "fjord", "H.FLLS": "waterfall", "H.GLCR": "glacier", "H.GULF": "gulf",
    "H.GYSR": "geyser", "H.HBR": "harbour", "H.INLT": "inlet", "H.LBED": "dry lake bed",
    "H.LGN": "lagoon", "H.LK": "lake", "H.LKS": "lakes", "H.LKI": "seasonal lake",
    "H.LKSL": "salt lake", "H.LKX": "part of a lake", "H.MRSH": "marsh", "H.OCN": "ocean",
    "H.PND": "pond", "H.PNDS": "ponds", "H.RPDS": "rapids", "H.RSV": "reservoir",
    "H.SEA": "sea", "H.SPNG": "spring", "H.SPNT": "hot spring", "H.STM": "river",
    "H.STMI": "seasonal river", "H.STMM": "river mouth", "H.STMS": "rivers",
    "H.STRT": "strait", "H.SWMP": "swamp", "H.WAD": "dry river bed", "H.WTRH": "waterhole",
    "H.CNLN": "navigation canal", "H.SD": "sound", "H.BNK": "bank", "H.RF": "reef",
    "H.WLL": "well",
    # Towns
    "P.PPL": "town", "P.PPLA": "regional capital", "P.PPLA2": "district seat",
    "P.PPLA3": "local seat", "P.PPLA4": "local seat", "P.PPLA5": "local seat",
    "P.PPLC": "capital city", "P.PPLCH": "former capital", "P.PPLF": "farm village",
    "P.PPLG": "seat of government", "P.PPLH": "former town", "P.PPLL": "village",
    "P.PPLQ": "abandoned town", "P.PPLR": "religious community", "P.PPLS": "towns",
    "P.PPLW": "destroyed town", "P.PPLX": "neighbourhood", "P.STLMT": "settlement",
    # Landforms
    "T.ATOL": "atoll", "T.BCH": "beach", "T.CAPE": "cape", "T.CLF": "cliff",
    "T.CNYN": "canyon", "T.CRTR": "crater", "T.DSRT": "desert", "T.DUNE": "dunes",
    "T.GRGE": "gorge", "T.HLL": "hill", "T.HLLS": "hills", "T.ISL": "island",
    "T.ISLET": "islet", "T.ISLS": "islands", "T.ISLX": "part of an island",
    "T.ISTH": "isthmus", "T.MESA": "mesa", "T.MT": "mountain", "T.MTS": "mountain range",
    "T.PASS": "mountain pass", "T.PEN": "peninsula", "T.PK": "peak", "T.PKS": "peaks",
    "T.PLAT": "plateau", "T.PLN": "plain", "T.PROM": "promontory", "T.PT": "point",
    "T.RDGE": "ridge", "T.RK": "rock", "T.RKS": "rocks", "T.SAND": "sandy area",
    "T.SPIT": "spit", "T.UPLD": "upland", "T.VAL": "valley", "T.VALS": "valleys",
    "T.VLC": "volcano", "T.CAVE": "cave", "T.SLP": "slope", "T.MND": "mound",
    "T.HMDA": "rocky desert", "T.ERG": "sand sea", "T.CRQ": "cirque", "T.PKLT": "peaklet",
    # Undersea
    "U.BNKU": "undersea bank", "U.CNYU": "undersea canyon", "U.DPR": "undersea basin",
    "U.FRZU": "fracture zone", "U.PLNU": "abyssal plain", "U.RDGU": "undersea ridge",
    "U.RFU": "reef", "U.SMU": "seamount", "U.SMSU": "seamounts", "U.TRNU": "ocean trench",
    "U.HLLU": "undersea hill", "U.PLTU": "undersea plateau", "U.RISU": "undersea rise",
    "U.SHFU": "continental shelf", "U.SLPU": "continental slope",
    # Forests and vegetation
    "V.FRST": "forest", "V.GRSLD": "grassland", "V.HTH": "heath", "V.SCRB": "scrubland",
    "V.TUND": "tundra", "V.MDW": "meadow", "V.GRVO": "olive grove", "V.VIN": "vineyard",
    # Landmarks
    "S.AIRP": "airport", "S.ANS": "ancient site", "S.ARCH": "arch", "S.BDG": "bridge",
    "S.CAVE": "cave", "S.CSTL": "castle", "S.CH": "church", "S.DAM": "dam", "S.FT": "fort",
    "S.HSTS": "historic site", "S.LTHSE": "lighthouse", "S.MNMT": "monument",
    "S.MUS": "museum", "S.OBPT": "viewpoint", "S.OBS": "observatory", "S.PAL": "palace",
    "S.PRT": "port", "S.PYR": "pyramid", "S.PYRS": "pyramids", "S.RUIN": "ruins",
    "S.STDM": "stadium", "S.TOWR": "tower", "S.UNIV": "university", "S.WALL": "wall",
    "S.ZOO": "zoo", "S.THTR": "theatre", "S.BLDG": "building", "S.SCH": "school",
    "S.RSTN": "railway station", "S.HSP": "hospital", "S.TMPL": "temple",
    "S.MSQE": "mosque", "S.CTHSE": "courthouse", "S.GDN": "garden", "S.MSTY": "monastery",
    "S.SHRN": "shrine", "S.CMTY": "cemetery", "S.TMB": "tomb", "S.SQR": "square",
    "S.LIBR": "library", "S.PSTB": "border post", "S.STNM": "weather station",
}


def kind_of(code: str) -> str:
    """Return a plain-English kind for a feature code, such as ``"mountain"``."""
    return KINDS.get(code) or CATEGORIES.get(code[:1], "place")


def category_of(code: str) -> str:
    """Return the general category for a feature code, such as ``"landform"``."""
    return CATEGORIES.get(code[:1], "place")
