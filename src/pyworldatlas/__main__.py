"""Minimal command-line interface for the current release."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json

from . import Atlas


def main() -> int:
    parser = argparse.ArgumentParser(prog="python -m pyworldatlas")
    sub = parser.add_subparsers(dest="command", required=True)
    country = sub.add_parser("country", help="show a country profile")
    country.add_argument("query")
    country.add_argument("--json", action="store_true")
    search = sub.add_parser("search", help="search country names and aliases")
    search.add_argument("query")
    sub.add_parser("dataset-info", help="show bundled dataset metadata")
    args = parser.parse_args()
    with Atlas() as atlas:
        if args.command == "country":
            found = atlas.country(args.query)
            print(found.to_json(indent=2) if args.json else f"{found.name} ({found.alpha2}) — capital: {found.capital.name if found.capital else 'unknown'}")
        elif args.command == "search":
            for match in atlas.search_countries(args.query):
                print(f"{match.country.alpha2}\t{match.country.name}\t{match.matched_name}")
        else:
            print(json.dumps(asdict(atlas.dataset_info()), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
