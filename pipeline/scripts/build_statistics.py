"""Build the statistics pack: basic World Bank indicators from 1960, by country.

Reads the pinned World Development Indicators snapshot (one API response per
indicator, plus its metadata) and writes ``packs/statistics/statistics.json.xz``.
Values are kept exactly as published, matched to PyWorldAtlas profiles by ISO
alpha-3 code. The World Bank's "World" total is kept for comparison; its other
regional and income groupings are left out. Every indicator's own license is
checked to be CC BY 4.0 before it is used.

Usage: python pipeline/scripts/build_statistics.py
Only the Python standard library is used.
"""

from __future__ import annotations

from hashlib import sha256
import json
import lzma
from pathlib import Path
import sqlite3

ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT = ROOT / "build_data/raw/worldbank/2026-10-28"
DATABASE = ROOT / "src/pyworldatlas/data/atlas.sqlite3"
OUTPUT = ROOT / "packs/statistics/statistics.json.xz"
FIRST_YEAR, LAST_YEAR = 1960, 2025

# key: (WDI code, plain name, unit, decimals)
INDICATORS = {
    "population": ("SP.POP.TOTL", "Population", "people", 0),
    "population_density": ("EN.POP.DNST", "Population density", "people per km² of land", 1),
    "urban_population": ("SP.URB.TOTL.IN.ZS", "Urban population", "% of people", 1),
    "life_expectancy": ("SP.DYN.LE00.IN", "Life expectancy at birth", "years", 1),
    "birth_rate": ("SP.DYN.CBRT.IN", "Births", "per 1,000 people a year", 1),
    "death_rate": ("SP.DYN.CDRT.IN", "Deaths", "per 1,000 people a year", 1),
    "forest_area": ("AG.LND.FRST.ZS", "Forest area", "% of land", 1),
    "farmland": ("AG.LND.AGRI.ZS", "Agricultural land", "% of land", 1),
    "electricity_access": ("EG.ELC.ACCS.ZS", "Access to electricity", "% of people", 1),
    "drinking_water": ("SH.H2O.BASW.ZS", "At least basic drinking water", "% of people", 1),
    "internet_users": ("IT.NET.USER.ZS", "Internet users", "% of people", 1),
}


def main() -> None:
    manifest = json.loads((SNAPSHOT / "manifest.json").read_text(encoding="utf-8"))
    pinned = {item["path"]: item["sha256"] for item in manifest["files"]}
    connection = sqlite3.connect(DATABASE)
    alpha3 = {row[0]: row[1] for row in connection.execute("SELECT alpha3, alpha2 FROM country WHERE alpha3 IS NOT NULL")}
    alpha3["WLD"] = "world"
    indicators: dict[str, object] = {}
    series: dict[str, dict[str, list[object]]] = {}
    for key, (code, name, unit, decimals) in INDICATORS.items():
        for path in (f"{code}.json", f"{code}.metadata.json"):
            if sha256((SNAPSHOT / path).read_bytes()).hexdigest() != pinned[path]:
                raise SystemExit(f"{path} does not match the checksum pinned in its manifest")
        metadata = json.loads((SNAPSHOT / f"{code}.metadata.json").read_text(encoding="utf-8"))
        fields = {item["id"]: item["value"] for item in metadata["source"][0]["concept"][0]["variable"][0]["metatype"]}
        if fields.get("License_Type") != "CC BY-4.0":
            raise SystemExit(f"{code} is not licensed CC BY 4.0")
        indicators[key] = {
            "code": code, "name": name, "unit": unit, "decimals": decimals,
            "source": f"World Bank, World Development Indicators ({code}); original source: "
                      + fields.get("Source", "").split(", uri:")[0].split(", publisher:")[0].strip(),
        }
        rows = json.loads((SNAPSHOT / f"{code}.json").read_text(encoding="utf-8"))[1]
        values: dict[str, dict[int, float]] = {}
        for row in rows:
            target = alpha3.get(row["countryiso3code"])
            if target is None or row["value"] is None:
                continue
            values.setdefault(target, {})[int(row["date"])] = row["value"]
        series[key] = {}
        for target, by_year in sorted(values.items()):
            first, last = min(by_year), max(by_year)
            series[key][target] = [first, [
                (round(by_year[year], decimals) if decimals else int(by_year[year]))
                if year in by_year else None
                for year in range(first, last + 1)
            ]]
    document = {
        "format": 1,
        "snapshot": manifest["retrieved_at"][:10],
        "years": [FIRST_YEAR, LAST_YEAR],
        "license": "CC BY 4.0",
        "indicators": indicators,
        "series": series,
    }
    data = json.dumps(document, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    packed = lzma.compress(data, format=lzma.FORMAT_XZ, preset=9 | lzma.PRESET_EXTREME)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_bytes(packed)
    count = sum(len(values) for by_country in series.values() for _, values in by_country.values())
    print(f"{len(indicators)} indicators, {count:,} yearly values, {len(packed):,} bytes -> {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
