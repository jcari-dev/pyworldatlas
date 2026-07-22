"""Extract compact currency and language metadata from Unicode CLDR 48.2."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile


ARCHIVE_URL = "https://unicode.org/Public/cldr/48.2/cldr-common-48.2.zip"
EXPECTED_ARCHIVE_SHA256 = "d2844f9dbf6124d11a7b047f5381a467902d82a673be3d658f4c0791ffa0b83b"


def file_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def required_codes(root: Path) -> tuple[set[str], set[str]]:
    currencies: set[str] = set()
    languages: set[str] = set()
    path = root / "build_data/raw/geonames/2026-07-20/countryInfo.txt"
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        columns = line.split("\t")
        if columns[10]:
            currencies.add(columns[10])
        for locale in columns[15].split(","):
            locale = locale.strip()
            if locale:
                languages.add(locale)
    return currencies, languages


def child_text(parent: ET.Element, name: str) -> str | None:
    for child in parent.findall(name):
        if child.get("alt") is None and child.get("count") is None and child.text:
            return child.text
    return None


def read_iana_languages(path: Path) -> dict[str, dict[str, str]]:
    """Read language descriptions and suppress-script values from IANA."""
    records: dict[str, dict[str, str]] = {}
    for block in path.read_text(encoding="utf-8").split("%%"):
        fields: dict[str, list[str]] = {}
        for line in block.strip().splitlines():
            if ": " not in line:
                continue
            key, value = line.split(": ", 1)
            fields.setdefault(key, []).append(value)
        code = next(iter(fields.get("Subtag", [])), "").lower()
        record_type = next(iter(fields.get("Type", [])), "")
        if code and record_type in {"language", "extlang"}:
            records[code] = {
                "name": next(iter(fields.get("Description", [])), ""),
                "script_code": next(iter(fields.get("Suppress-Script", [])), ""),
            }
    return records


def extract(root: Path, archive: Path, iana_registry: Path) -> dict[str, object]:
    archive_hash = file_sha256(archive)
    if archive_hash != EXPECTED_ARCHIVE_SHA256:
        raise ValueError(f"Unexpected CLDR archive checksum: {archive_hash}")

    required_currencies, required_locales = required_codes(root)
    primary_languages = {locale.split("-", 1)[0].lower() for locale in required_locales}
    iana_languages = read_iana_languages(iana_registry)

    with zipfile.ZipFile(archive) as bundle:
        english = ET.fromstring(bundle.read("common/main/en.xml"))
        likely_subtags = ET.fromstring(
            bundle.read("common/supplemental/likelySubtags.xml")
        )
        supplemental = ET.fromstring(
            bundle.read("common/supplemental/supplementalData.xml")
        )

    language_names = {
        element.get("type"): element.text
        for element in english.findall("./localeDisplayNames/languages/language")
        if element.get("type")
        and element.get("alt") is None
        and element.text
    }
    scripts: dict[str, str] = {}
    for element in likely_subtags.findall("./likelySubtags/likelySubtag"):
        source = element.get("from")
        target = element.get("to")
        if not source or not target or "_" in source:
            continue
        parts = target.split("_")
        if len(parts) >= 2 and len(parts[1]) == 4:
            scripts[source.lower()] = parts[1]

    default_digits = 2
    fraction_digits: dict[str, int] = {}
    for element in supplemental.findall("./currencyData/fractions/info"):
        code = element.get("iso4217")
        digits = element.get("digits")
        if code == "DEFAULT" and digits is not None:
            default_digits = int(digits)
        elif code and digits is not None:
            fraction_digits[code] = int(digits)

    currencies: list[dict[str, object]] = []
    currency_elements = {
        element.get("type"): element
        for element in english.findall("./numbers/currencies/currency")
        if element.get("type")
    }
    for code in sorted(required_currencies):
        element = currency_elements.get(code)
        currencies.append(
            {
                "code": code,
                "name": child_text(element, "displayName") if element is not None else None,
                "symbol": child_text(element, "symbol") if element is not None else None,
                "minor_unit_digits": fraction_digits.get(code, default_digits),
                "source_locator": f"common/main/en.xml currency[@type='{code}']; supplementalData.xml fractions",
            }
        )

    languages: list[dict[str, object]] = []
    for code in sorted(required_locales):
        primary = code.split("-", 1)[0].lower()
        cldr_name = language_names.get(primary)
        iana = iana_languages.get(primary, {})
        name = cldr_name or iana.get("name") or None
        script_code = scripts.get(primary) or iana.get("script_code") or None
        name_source_id = (
            "unicode-cldr-48.2-reference"
            if cldr_name
            else "iana-language-subtags-2026-06-14"
        )
        languages.append(
            {
                "code": code,
                "primary_code": primary,
                "name": name,
                "script_code": script_code,
                "name_source_id": name_source_id,
                "source_locator": (
                    f"common/main/en.xml language[@type='{primary}']; likelySubtags.xml; "
                    f"IANA language subtag '{primary}'"
                ),
            }
        )

    resolved_names = {
        row["primary_code"] for row in languages if row["name"] is not None
    }
    missing_names = sorted(primary_languages - resolved_names)
    if missing_names:
        raise ValueError(f"Missing CLDR language names: {missing_names}")
    return {
        "source_id": "unicode-cldr-48.2-reference",
        "source_name": "Unicode CLDR currency and language metadata",
        "archive_url": ARCHIVE_URL,
        "archive_sha256": archive_hash,
        "license_name": "Unicode License v3",
        "license_url": "https://www.unicode.org/license.txt",
        "currencies": currencies,
        "languages": languages,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("iana_registry", type=Path)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    snapshot = extract(args.root, args.archive, args.iana_registry)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(
        f"Wrote {len(snapshot['currencies'])} currencies and "
        f"{len(snapshot['languages'])} language records to {args.output}"
    )


if __name__ == "__main__":
    main()
