"""Extract compact country and physical-geography facts from the Factbook.

The source repository contains structured transcriptions of the public-domain
CIA World Factbook. This script retains country-name fields, national-anthem
titles, English nationality terms, and the structured physical fields used by
PyWorldAtlas. It does not copy lyrics, contributor credits, adoption history,
political narrative, or unrelated profile text.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import html
import json
from pathlib import Path
import re


FACTBOOK_COMMIT = "8662a8b17a784841ab4528631b04090eb2f183eb"
FACTBOOK_REPOSITORY = "https://github.com/factbook/factbook.json"
CIA_SITE_POLICY = "https://www.cia.gov/site-policies/"
NUMBER_PATTERN = r"-?[\d,.]+(?:\s+million)?"


def file_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def clean_text(value: str | None) -> str | None:
    if not value:
        return None
    value = html.unescape(value)
    value = re.sub(r"<[^>]+>", " ", value)
    value = " ".join(value.replace("\xa0", " ").split())
    if value.casefold() in {"na", "none"}:
        return None
    return value or None


def repair_mojibake(value: str | None) -> str | None:
    """Repair the source repository's occasional double-decoded UTF-8 text."""
    cleaned = clean_text(value)
    if cleaned is None:
        return None
    for _ in range(2):
        if not any(marker in cleaned for marker in ("Ã", "Â", "â€", "â€™", "â€œ")):
            break
        try:
            repaired = cleaned.encode("latin-1").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            break
        if repaired == cleaned:
            break
        cleaned = repaired
    return cleaned


def parse_number(value: str) -> float:
    """Parse a Factbook number, including compact values such as 1.284 million."""
    normalized = value.casefold().replace(",", "").strip()
    multiplier = 1_000_000 if normalized.endswith(" million") else 1
    if multiplier != 1:
        normalized = normalized.removesuffix(" million").strip()
    return float(normalized) * multiplier


def measurement(value: str | None, unit: str, *, implied: bool = False) -> float | None:
    """Return the last numeric measurement with the expected source unit."""
    cleaned = repair_mojibake(value)
    if cleaned is None:
        return None
    suffix = rf"\s*{re.escape(unit)}\b" if not implied else rf"(?:\s*{re.escape(unit)}\b)?"
    match = re.search(rf"({NUMBER_PATTERN}){suffix}", cleaned, flags=re.IGNORECASE)
    return parse_number(match.group(1)) if match else None


def elevation_point(value: str | None) -> dict[str, object] | None:
    """Split a named Factbook elevation extreme into label and metres."""
    cleaned = repair_mojibake(value)
    if cleaned is None:
        return None
    match = re.search(
        rf"^(.*?)\s+({NUMBER_PATTERN})(?:\s*m\b|$)", cleaned, re.IGNORECASE
    )
    if match is None:
        return None
    return {
        "name": re.sub(
            r"\s+(?:more\s+than|about|approximately)$",
            "",
            match.group(1).strip(),
            flags=re.IGNORECASE,
        ),
        "elevation_m": parse_number(match.group(2)),
        "is_approximate": bool(
            re.search(r"\b(?:more\s+than|about|approximately)\b", cleaned, re.IGNORECASE)
        ),
        "source_label": cleaned,
    }


def feature_name(label: str, feature_type: str) -> str:
    """Return a concise name while retaining the exact label separately."""
    name = re.split(r"\s+\(shared\s+with\b", label, maxsplit=1, flags=re.IGNORECASE)[0]
    if feature_type == "river":
        name = re.sub(
            r"\s+river(?:\s+(?:source(?:\s+and\s+mouth)?|mouth))?$",
            "",
            name,
            flags=re.IGNORECASE,
        )
    return name.strip()


def physical_features(
    value: str | None,
    *,
    feature_type: str,
    unit: str,
    subtype: str | None = None,
) -> list[dict[str, object]]:
    """Parse semicolon-delimited named rivers or lakes from one source field."""
    cleaned = repair_mojibake(value)
    if cleaned is None:
        return []
    cleaned = re.split(r"\bnote:\s*", cleaned, maxsplit=1, flags=re.IGNORECASE)[0].strip()
    records: list[dict[str, object]] = []
    for item in (part.strip() for part in cleaned.split(";")):
        if not item:
            continue
        label, separator, measure = item.rpartition(" - ")
        source_label = label.strip() if separator else item
        numeric = measurement(measure if separator else item, unit, implied=True)
        records.append(
            {
                "name": feature_name(source_label, feature_type),
                "feature_type": feature_type,
                "subtype": subtype,
                "length_km": numeric if feature_type == "river" else None,
                "area_km2": numeric if feature_type == "lake" else None,
                "source_label": source_label,
            }
        )
    return records


def extract_physical_geography(payload: dict[str, object]) -> dict[str, object]:
    """Extract only documented structured physical-geography fields."""
    geography = payload.get("Geography", {})
    if not isinstance(geography, dict):
        geography = {}
    area = geography.get("Area", {})
    elevation = geography.get("Elevation", {})
    lakes = geography.get("Major lakes (area sq km)", {})

    def item_text(container: object, key: str) -> str | None:
        item = container.get(key) if isinstance(container, dict) else None
        return item.get("text") if isinstance(item, dict) else None

    rivers = geography.get("Major rivers (by length in km)", {})
    river_text = rivers.get("text") if isinstance(rivers, dict) else None
    lake_records: list[dict[str, object]] = []
    if isinstance(lakes, dict):
        for key, subtype in (
            ("fresh water lake(s)", "freshwater"),
            ("salt water lake(s)", "saltwater"),
        ):
            lake_records.extend(
                physical_features(
                    item_text(lakes, key),
                    feature_type="lake",
                    unit="sq km",
                    subtype=subtype,
                )
            )
    return {
        "total_area_km2": measurement(item_text(area, "total "), "sq km", implied=True),
        "land_area_km2": measurement(item_text(area, "land"), "sq km", implied=True),
        "water_area_km2": measurement(item_text(area, "water"), "sq km", implied=True),
        "coastline_km": measurement(item_text(geography, "Coastline"), "km"),
        "climate_summary": repair_mojibake(item_text(geography, "Climate")),
        "highest_point": elevation_point(item_text(elevation, "highest point")),
        "lowest_point": elevation_point(item_text(elevation, "lowest point")),
        "mean_elevation_m": measurement(
            item_text(elevation, "mean elevation"), "m", implied=True
        ),
        "rivers": physical_features(
            river_text, feature_type="river", unit="km"
        ),
        "lakes": lake_records,
    }


def split_anthem_title(value: str | None) -> tuple[str | None, str | None]:
    """Split the Factbook's compact title and parenthetical English label."""
    cleaned = clean_text(value)
    if cleaned is None:
        return (None, None)
    normalized = cleaned.translate(str.maketrans({"“": '"', "”": '"'})).strip()
    title_part, separator, english_part = normalized.rpartition(" (")
    if separator and english_part.endswith(")"):
        title = title_part.strip().strip('"').strip()
        english = english_part[:-1].strip().strip('"').strip()
        return (title or None, english or None)
    return (normalized.strip('"').strip() or None, None)


def canonical_country_codes(root: Path) -> set[str]:
    path = root / "build_data" / "normalized" / "countries.jsonl"
    codes = {
        json.loads(line)["country_code"]
        for line in path.read_text(encoding="utf-8").splitlines()
        if line
    }
    if len(codes) != 248:
        raise ValueError(f"Expected 248 canonical country and area codes, found {len(codes)}")
    return codes


def fips_to_iso(root: Path) -> dict[str, str]:
    path = root / "build_data" / "raw" / "geonames" / "2026-07-20" / "countryInfo.txt"
    mapping: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        columns = line.split("\t")
        if columns[3]:
            mapping[columns[3].casefold()] = columns[0]
    return mapping


def extract(root: Path, checkout: Path) -> dict[str, object]:
    country_codes = canonical_country_codes(root)
    code_map = fips_to_iso(root)
    records: list[dict[str, object]] = []
    seen: set[str] = set()

    for path in sorted(checkout.glob("*/*.json")):
        country_code = code_map.get(path.stem.casefold())
        if country_code not in country_codes or country_code in seen:
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        names = payload.get("Government", {}).get("Country name", {})

        def field(name: str) -> str | None:
            item = names.get(name)
            return clean_text(item.get("text")) if isinstance(item, dict) else None

        anthem_fields = payload.get("Government", {}).get("National anthem(s)", {})
        anthem_source_text = (
            clean_text(anthem_fields.get("title", {}).get("text"))
            if isinstance(anthem_fields, dict)
            else None
        )
        anthem_title, anthem_english_title = split_anthem_title(anthem_source_text)
        nationality = payload.get("People and Society", {}).get("Nationality", {})

        def nationality_field(name: str) -> str | None:
            item = nationality.get(name) if isinstance(nationality, dict) else None
            return clean_text(item.get("text")) if isinstance(item, dict) else None

        if not names:
            continue
        seen.add(country_code)
        records.append(
            {
                "country_code": country_code,
                "conventional_short_name": field("conventional short form"),
                "conventional_formal_name": field("conventional long form"),
                "local_short_name": field("local short form"),
                "local_formal_name": field("local long form"),
                "anthem_title": anthem_title,
                "anthem_english_title": anthem_english_title,
                "anthem_source_text": anthem_source_text,
                "demonym_noun": nationality_field("noun"),
                "demonym_adjective": nationality_field("adjective"),
                "physical_geography": extract_physical_geography(payload),
                "source_path": path.relative_to(checkout).as_posix(),
                "source_locator": "Government > Country name",
                "source_locators": {
                    "country_names": "Government > Country name",
                    "anthem": "Government > National anthem(s) > title",
                    "demonym": "People and Society > Nationality",
                    "physical_geography": "Geography",
                    "area": "Geography > Area",
                    "coastline": "Geography > Coastline",
                    "climate": "Geography > Climate",
                    "elevation": "Geography > Elevation",
                    "lakes": "Geography > Major lakes (area sq km)",
                    "rivers": "Geography > Major rivers (by length in km)",
                },
                "source_sha256": file_sha256(path),
            }
        )

    return {
        "source_id": "cia-world-factbook-2025",
        "source_name": "CIA World Factbook structured country profiles",
        "structured_repository": FACTBOOK_REPOSITORY,
        "structured_repository_commit": FACTBOOK_COMMIT,
        "public_domain_notice": CIA_SITE_POLICY,
        "records": records,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkout", type=Path, help="Pinned factbook.json checkout")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="PyWorldAtlas repository root",
    )
    parser.add_argument("--output", type=Path, required=True, help="Compact JSON output")
    args = parser.parse_args()

    snapshot = extract(args.root, args.checkout)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"Wrote {len(snapshot['records'])} records to {args.output}")


if __name__ == "__main__":
    main()
