"""Build the place files: the bundled school atlas and the explorer and world packs.

Reads the pinned GeoNames snapshot (every place on Earth plus alternate names),
ranks each place by educational value, and writes three place files:

- ``src/pyworldatlas/data/places.pwpl``: the school atlas, shipped in every install
- ``packs/places-explorer/places.pwpl``: every town over 1,000 people and every
  named natural feature (adds to the school atlas)
- ``packs/places-world/places.pwpl``: every remaining village, stream and hill

Educational value uses only signals in the data: what a place is, how big or
high it is, and how widely it is known (named in other writing systems and
languages, with an English Wikipedia article). Shops, hotels, farms, roads and
similar spots are left out. ``pipeline/config/must_have_places.json`` lists a few
famous places whose GeoNames entries lack those signals.

Usage: python pipeline/scripts/build_places.py [school|explorer|world ...]
Only the Python standard library is used. Memory peaks around 6 GB.
"""

from __future__ import annotations

from array import array
from hashlib import sha256
import io
import json
from math import log2
from pathlib import Path
import sys
import time
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from pyworldatlas._placefile import PlaceRecord, encode, hilbert_key  # noqa: E402

SNAPSHOT = ROOT / "build_data/raw/geonames/2026-10-27"
MUST_HAVE = ROOT / "pipeline/config/must_have_places.json"
OUTPUTS = {
    1: (ROOT / "src/pyworldatlas/data/places.pwpl", 1_000, "school"),
    2: (ROOT / "packs/places-explorer/places.pwpl", 1_000, "explorer"),
    3: (ROOT / "packs/places-world/places.pwpl", 1_000, "world"),
}

NATION_LEVEL = {
    "A.PCLI", "A.PCLD", "A.PCLF", "A.PCLS", "A.PCLIX", "A.PCL", "A.TERR", "A.ADM1",
    "L.CONT", "H.OCN", "H.SEA",
}
SEATS_TOP = {"P.PPLC", "P.PPLG", "P.PPLA"}
SEATS_MID = {"P.PPLA2", "P.PPLA3"}
PEAKS = {"T.MT", "T.PK", "T.VLC"}
GEOGRAPHY = set("HTLUV")
# Built places with lasting educational value (no shops, hotels, farms or roads).
LANDMARKS = {
    "S.ANS", "S.CSTL", "S.MNMT", "S.PYR", "S.PYRS", "S.RUIN", "S.PAL", "S.FT", "S.OBS",
    "S.AIRP", "S.PRT", "S.MUS", "S.UNIV", "S.ZOO", "S.DAM", "S.LTHSE", "S.BDG",
    "S.TOWR", "S.STDM", "S.OBPT", "S.HSTS", "S.WALL", "S.ARCH", "S.CAVE",
}
NOT_LANGUAGES = {"", "link", "wkdt", "post", "iata", "icao", "faac", "abbr", "unlc", "tcid", "fr_1793", "phon", "piny"}
LATIN_LIMIT = 0x24F


def log(message: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {message}", flush=True)


def verify_snapshot() -> None:
    manifest = json.loads((SNAPSHOT / "manifest.json").read_text(encoding="utf-8"))
    for entry in manifest["files"]:
        path = SNAPSHOT / entry["path"]
        if not path.is_file():
            raise SystemExit(f"Missing {path}. Download it from {entry['url']}")
        digest = sha256()
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1 << 20), b""):
                digest.update(block)
        if digest.hexdigest() != entry["sha256"]:
            raise SystemExit(f"{path.name} does not match the pinned checksum")


class Places:
    """Every GeoNames place as compact columns."""

    def __init__(self) -> None:
        self.ids = array("L")
        self.lat, self.lon = array("d"), array("d")
        self.pop, self.elev = array("q"), array("l")
        self.code, self.country = array("H"), array("H")
        self.names_in = array("H")
        self.scripts = array("Q")
        self.names: list[str] = []
        self.codes: dict[str, int] = {}
        self.countries: dict[str, int] = {}
        self.script_bits: dict[str, int] = {"LATIN": 0}
        self.script_of_block: dict[int, str] = {}

    def _script(self, char: str) -> str:
        block = ord(char) >> 7
        label = self.script_of_block.get(block)
        if label is None:
            import unicodedata

            label = self.script_of_block[block] = unicodedata.name(char, "OTHER").split()[0]
        return label

    def read(self, archive_path: Path) -> None:
        with zipfile.ZipFile(archive_path) as archive, archive.open("allCountries.txt") as raw:
            for count, line in enumerate(io.TextIOWrapper(raw, encoding="utf-8"), 1):
                p = line.rstrip("\n").split("\t")
                if not p[1]:
                    continue
                self.ids.append(int(p[0]))
                self.names.append(p[1])
                self.lat.append(float(p[4]))
                self.lon.append(float(p[5]))
                self.pop.append(int(p[14] or 0))
                value = p[15] or p[16]
                self.elev.append(int(value) if value not in ("", "-9999") else -32768)
                self.code.append(self.codes.setdefault(f"{p[6]}.{p[7]}", len(self.codes)))
                self.country.append(self.countries.setdefault(p[8], len(self.countries)))
                others = set(p[3].split(",")) if p[3] else set()
                self.names_in.append(min(65535, len(others)))
                bits = 0
                for other in others:
                    label = "LATIN"
                    for char in other:
                        if ord(char) > LATIN_LIMIT and char.isalpha():
                            label = self._script(char)
                            break
                    bit = self.script_bits.setdefault(label, len(self.script_bits))
                    if bit < 64:
                        bits |= 1 << bit
                self.scripts.append(bits)
                if count % 2_000_000 == 0:
                    log(f"  {count:,} rows")
        self.code_names = list(self.codes)
        self.home = self._home_scripts()

    def _home_scripts(self) -> dict[int, int]:
        """Writing systems used by at least 10% of a country's named places."""
        seen: dict[int, int] = {}
        tally: dict[int, list[int]] = {}
        for i, bits in enumerate(self.scripts):
            if bits:
                country = self.country[i]
                seen[country] = seen.get(country, 0) + 1
                counts = tally.setdefault(country, [0] * 64)
                while bits:
                    low = bits & -bits
                    counts[low.bit_length() - 1] += 1
                    bits ^= low
        return {
            country: 1 | sum(1 << bit for bit, count in enumerate(counts) if count >= 0.1 * seen[country])
            for country, counts in tally.items()
        }

    def foreign(self, i: int) -> int:
        """How many writing systems from outside its own country name a place."""
        return bin(self.scripts[i] & ~self.home.get(self.country[i], 1)).count("1")


def read_alternate_names(places: Places, archive_path: Path) -> tuple[array, array, dict[int, str]]:
    """Return languages per place, English Wikipedia flags, and English names."""
    n = len(places.ids)
    order = sorted(range(n), key=places.ids.__getitem__)
    row_of = {places.ids[i]: i for i in order} if n < 1_000 else None
    keys = array("L", (places.ids[i] for i in order))
    from bisect import bisect_left

    def row(geonameid: int) -> int:
        if row_of is not None:
            return row_of.get(geonameid, -1)
        k = bisect_left(keys, geonameid)
        return order[k] if k < n and keys[k] == geonameid else -1

    languages = array("H", bytes(2 * n))
    enwiki = array("B", bytes(n))
    english: dict[int, tuple[int, str]] = {}
    language_ids: dict[str, int] = {}
    pairs = array("Q")
    with zipfile.ZipFile(archive_path) as archive, archive.open("alternateNamesV2.txt") as raw:
        last_id = current = -1
        for line in io.TextIOWrapper(raw, encoding="utf-8"):
            p = line.rstrip("\n").split("\t")
            geonameid = int(p[1])
            if geonameid != last_id:
                last_id, current = geonameid, row(geonameid)
            if current < 0:
                continue
            language, name = p[2], p[3]
            if language == "link":
                if "//en.wikipedia.org/" in name:
                    enwiki[current] = 1
                continue
            if language in NOT_LANGUAGES:
                continue
            pairs.append(current << 12 | language_ids.setdefault(language.split("-")[0], len(language_ids)))
            if language == "en" and p[6] != "1" and p[7] != "1":  # not colloquial or historic
                score = 2 * (p[4] == "1") + (p[5] == "1")  # preferred, then short
                if current not in english or score > english[current][0]:
                    english[current] = (score, name)
    for pair in set(pairs):
        place = pair >> 12
        languages[place] = min(65535, languages[place] + 1)
    return languages, enwiki, {place: name for place, (_, name) in english.items()}


def rank(places: Places, languages: array, enwiki: array, must_have: set[int]) -> array:
    """Return a tier per place: 1 school atlas, 2 explorer, 3 world, 4 left out."""
    tiers = array("B", bytes(len(places.ids)))
    for i in range(len(places.ids)):
        code = places.code_names[places.code[i]]
        kind = code[0]
        foreign = places.foreign(i)
        known = enwiki[i] and languages[i] >= 5
        tier = 4
        if code in NATION_LEVEL or code in SEATS_TOP or places.ids[i] in must_have:
            tier = 1
        elif kind == "P":
            if places.pop[i] >= 5_000 or (code in SEATS_MID and foreign >= 1) or known:
                tier = 1
            elif places.pop[i] >= 1_000 or code in SEATS_MID:
                tier = 2
            else:
                tier = 3
        elif kind == "A":
            tier = 1 if known else 2 if code.startswith("A.ADM2") else 3
        elif kind in GEOGRAPHY:
            high = code in PEAKS and places.elev[i] >= 6_000
            if foreign >= 1 or places.names_in[i] >= 10 or high or known:
                tier = 1
            elif places.names_in[i] >= 1 or (code in PEAKS and places.elev[i] >= 1_500):
                tier = 2
            else:
                tier = 3
        elif code in LANDMARKS:
            if foreign >= 2 or known:
                tier = 1
            else:
                tier = 2 if places.names_in[i] >= 1 or code in {"S.AIRP", "S.PRT"} else 3
        elif known and kind == "S" and languages[i] >= 10:
            tier = 1
        tiers[i] = tier
    return tiers


def fame(places: Places, languages: array, enwiki: array, i: int) -> int:
    """How widely a place is known, 0 to 255; used to order search results."""
    score = min(250, languages[i]) + 5 * enwiki[i]
    code = places.code_names[places.code[i]]
    # A village "named in 70 languages" has names copied from a famous namesake.
    if code[0] == "P" and code not in SEATS_TOP and places.pop[i] < 5_000 and languages[i] > 20:
        score = min(score, 10)
    # Only the order matters, so keep six steps per doubling: smaller to store.
    return min(255, round(2 ** (round(6 * log2(1 + score)) / 6) - 1))


def main() -> None:
    verify_snapshot()
    must_have = {int(item["geonames_id"]) for item in json.loads(MUST_HAVE.read_text(encoding="utf-8"))["places"]}
    log("Reading every place")
    places = Places()
    places.read(SNAPSHOT / "allCountries.zip")
    log(f"Read {len(places.ids):,} places; reading alternate names")
    languages, enwiki, english = read_alternate_names(places, SNAPSHOT / "alternateNamesV2.zip")
    log("Ranking by educational value")
    tiers = rank(places, languages, enwiki, must_have)
    missing = must_have - {places.ids[i] for i in range(len(places.ids)) if tiers[i] == 1}
    if missing:
        raise SystemExit(f"Must-have places not found: {sorted(missing)}")
    countries = list(places.countries)
    wanted = set(sys.argv[1:]) or {label for _, _, label in OUTPUTS.values()}
    for tier, (path, precision, label) in OUTPUTS.items():
        if label not in wanted:
            continue
        chosen = [i for i in range(len(places.ids)) if tiers[i] == tier]
        chosen.sort(key=lambda i: hilbert_key(places.lat[i], places.lon[i]))
        records = [
            PlaceRecord(
                places.names[i],
                english.get(i, places.names[i]),
                places.code_names[places.code[i]],
                countries[places.country[i]],
                places.lat[i],
                places.lon[i],
                places.pop[i] if places.code_names[places.code[i]][0] == "P" and places.pop[i] > 0 else None,
                places.elev[i] if places.elev[i] != -32768 and places.code_names[places.code[i]][0] in "TU" else None,
                fame(places, languages, enwiki, i),
            )
            for i in chosen
        ]
        meta = {"edition": label, "source": "GeoNames 2026-10-27 (CC BY 4.0)"}
        data = encode(records, precision=precision, meta=meta)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        log(f"{label}: {len(records):,} places, {len(data) / 1e6:.2f} MB -> {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
