"""Extract compact country-name facts from a pinned factbook.json checkout.

The source repository contains structured transcriptions of the public-domain
CIA World Factbook. This script retains only name fields used by PyWorldAtlas;
it does not copy narrative profile text.
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
                "source_path": path.relative_to(checkout).as_posix(),
                "source_locator": "Government > Country name",
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
