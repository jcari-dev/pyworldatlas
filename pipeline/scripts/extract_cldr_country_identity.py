"""Extract one local country or area name per UN M49 record from Unicode CLDR.

The script reads a pinned ``cldr-common`` release archive and writes the small,
inspectable source snapshot used by the offline PyWorldAtlas build. It does not
download anything and is deterministic for a given archive and country list.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile


CLDR_VERSION = "48.2"
CLDR_RELEASE_DATE = "2026-03-17"
CLDR_ARCHIVE_URL = (
    "https://unicode.org/Public/cldr/48.2/cldr-common-48.2.zip"
)
CLDR_LICENSE_URL = "https://www.unicode.org/license.txt"


def file_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def country_codes(root: Path) -> list[str]:
    records = root / "build_data" / "normalized" / "countries.jsonl"
    codes = {
        json.loads(line)["country_code"]
        for line in records.read_text(encoding="utf-8").splitlines()
        if line
    }
    if len(codes) != 248:
        raise ValueError(f"Expected 248 canonical country and area codes, found {len(codes)}")
    return sorted(codes)


class CldrArchive:
    def __init__(self, archive: Path) -> None:
        self.zip = zipfile.ZipFile(archive)
        self.members = set(self.zip.namelist())
        self.supplemental = ET.fromstring(
            self.zip.read("common/supplemental/supplementalData.xml")
        )
        self.likely = ET.fromstring(
            self.zip.read("common/supplemental/likelySubtags.xml")
        )
        self.parent_locales = self._parent_locale_map()
        self.english = self._locale_root("en")
        self._locale_cache: dict[str, ET.Element] = {"en": self.english}

    def close(self) -> None:
        self.zip.close()

    def _locale_root(self, locale: str) -> ET.Element:
        member = f"common/main/{locale}.xml"
        if member not in self.members:
            raise KeyError(member)
        return ET.fromstring(self.zip.read(member))

    def _parent_locale_map(self) -> dict[str, str]:
        parents: dict[str, str] = {}
        for item in self.supplemental.findall(".//parentLocale"):
            parent = item.attrib["parent"]
            for locale in item.attrib["locales"].split():
                parents[locale] = parent
        return parents

    def locale_root(self, locale: str) -> ET.Element:
        if locale not in self._locale_cache:
            self._locale_cache[locale] = self._locale_root(locale)
        return self._locale_cache[locale]

    def locale_chain(self, locale: str) -> list[str]:
        chain: list[str] = []
        current = locale
        while current and current not in chain:
            chain.append(current)
            explicit = self.parent_locales.get(current)
            if explicit:
                current = explicit
            elif "_" in current:
                current = current.rsplit("_", 1)[0]
            elif current != "root":
                current = "root"
            else:
                break
        return chain

    def territory_name(self, locale: str, code: str) -> tuple[str, str]:
        candidates = [locale]
        if "_" in locale:
            candidates.append(locale.split("_", 1)[0])
        for candidate in candidates:
            for inherited in self.locale_chain(candidate):
                member = f"common/main/{inherited}.xml"
                if member not in self.members:
                    continue
                root = self.locale_root(inherited)
                for element in root.findall(".//localeDisplayNames/territories/territory"):
                    if element.attrib.get("type") == code and "alt" not in element.attrib:
                        if element.text:
                            return element.text, inherited
        raise ValueError(f"CLDR has no territory display name for {code} in {locale}")

    def language_name(self, code: str) -> str:
        exact = code.replace("_", "-")
        base = code.split("_", 1)[0]
        for element in self.english.findall(".//localeDisplayNames/languages/language"):
            if "alt" in element.attrib or not element.text:
                continue
            if element.attrib.get("type") in {exact, base}:
                return element.text
        return exact

    def script_code(self, language: str) -> str:
        parts = language.split("_")
        if len(parts) > 1 and len(parts[1]) == 4:
            return parts[1].title()
        base = parts[0]
        candidates: list[tuple[int, str]] = []
        for element in self.likely.findall(".//likelySubtag"):
            source = element.attrib.get("from", "")
            target = element.attrib.get("to", "")
            target_parts = target.split("_")
            if len(target_parts) < 2 or source.split("_", 1)[0] != base:
                continue
            candidates.append((0 if source == base else 1, target_parts[1]))
        if not candidates:
            raise ValueError(f"CLDR has no likely script for language {language}")
        return min(candidates)[1]

    def territory_languages(self, code: str) -> list[ET.Element]:
        for territory in self.supplemental.findall(".//territoryInfo/territory"):
            if territory.attrib.get("type") == code:
                return territory.findall("languagePopulation")
        return []


def select_language(rows: list[ET.Element]) -> tuple[str, str, float | None]:
    status_priority = {
        "official": 0,
        "de_facto_official": 1,
        "official_regional": 2,
    }
    usable = [row for row in rows if row.attrib.get("type") != "und"]
    official = [row for row in usable if row.attrib.get("officialStatus") in status_priority]
    candidates = official or usable
    if not candidates:
        return "en", "not_applicable", None

    def sort_key(row: ET.Element) -> tuple[int, float, str]:
        status = row.attrib.get("officialStatus")
        population = float(row.attrib.get("populationPercent", "0"))
        return status_priority.get(status, 3), -population, row.attrib["type"]

    selected = min(candidates, key=sort_key)
    status = selected.attrib.get("officialStatus", "population_language")
    population = selected.attrib.get("populationPercent")
    return selected.attrib["type"], status, float(population) if population else None


def build_snapshot(root: Path, archive: Path) -> dict[str, object]:
    cldr = CldrArchive(archive)
    try:
        records: list[dict[str, object]] = []
        for code in country_codes(root):
            language_rows = cldr.territory_languages(code)
            remaining = list(language_rows)
            while True:
                language, status, population_percent = select_language(remaining)
                try:
                    name, locale = cldr.territory_name(language, code)
                    break
                except ValueError:
                    remaining = [
                        row for row in remaining if row.attrib.get("type") != language
                    ]
                    if not remaining and language == "en":
                        raise
            normalized_language = language.replace("_", "-")
            records.append(
                {
                    "country_code": code,
                    "language_code": normalized_language,
                    "language_name": cldr.language_name(language),
                    "script_code": cldr.script_code(language),
                    "local_name": name,
                    "language_status": status,
                    "language_population_percent": population_percent,
                    "is_official_language": status
                    in {"official", "de_facto_official", "official_regional"},
                    "source_locale": locale,
                    "source_locator": (
                        f"common/main/{locale}.xml territory[@type='{code}']; "
                        f"supplementalData.xml territory[@type='{code}']"
                    ),
                }
            )
        if len(records) != 248:
            raise ValueError(f"Expected 248 extracted names, found {len(records)}")
        return {
            "source_id": "unicode-cldr-48.2",
            "source_version": CLDR_VERSION,
            "source_release_date": CLDR_RELEASE_DATE,
            "archive_url": CLDR_ARCHIVE_URL,
            "archive_sha256": file_sha256(archive),
            "license_name": "Unicode License v3",
            "license_url": CLDR_LICENSE_URL,
            "records": records,
        }
    finally:
        cldr.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path, help="Pinned cldr-common release archive")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="PyWorldAtlas repository root",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output JSON path (defaults to the pinned raw-data folder)",
    )
    args = parser.parse_args()
    output = args.output or (
        args.root
        / "build_data"
        / "raw"
        / "unicode-cldr"
        / CLDR_VERSION
        / "country_identity.json"
    )
    snapshot = build_snapshot(args.root, args.archive)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"Wrote {len(snapshot['records'])} records to {output}")


if __name__ == "__main__":
    main()
