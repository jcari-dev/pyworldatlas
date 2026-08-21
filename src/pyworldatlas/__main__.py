"""Small command-line interface for exploring the installed atlas."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
import sys
from typing import Sequence

from . import Atlas, AtlasError, __version__


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pyworldatlas",
        description="Explore the bundled PyWorldAtlas country database.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"PyWorldAtlas {__version__}",
    )
    subcommands = parser.add_subparsers(dest="command", required=True)

    country = subcommands.add_parser(
        "country",
        help="show one country profile",
        description="Look up one profile by name, alias, or standard code.",
    )
    country.add_argument(
        "query",
        help="country name, alias, alpha code, or M49 code",
    )
    country.add_argument(
        "--json",
        action="store_true",
        help="print the complete profile as JSON",
    )

    search = subcommands.add_parser(
        "search",
        help="search country names and aliases",
        description="Find partial country-name and alias matches.",
    )
    search.add_argument("query", help="partial country name or alias")
    subcommands.add_parser("dataset-info", help="show bundled dataset metadata")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the read-only PyWorldAtlas command-line interface."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        with Atlas() as atlas:
            if args.command == "country":
                found = atlas.country(args.query)
                capital = found.capital.name if found.capital else "not listed"
                output = (
                    found.to_json(indent=2)
                    if args.json
                    else (
                        f"{found.flag} {found.name} ({found.alpha2})"
                        f" | Capital: {capital}"
                    )
                )
                print(output)
            elif args.command == "search":
                matches = atlas.search_countries(args.query)
                if not matches:
                    parser.exit(1, f"No countries found for {args.query!r}.\n")
                for match in matches:
                    print(
                        f"{match.country.alpha2}\t{match.country.name}"
                        f"\tmatched {match.matched_name}"
                    )
            else:
                print(json.dumps(asdict(atlas.dataset_info()), indent=2))
    except (AtlasError, ValueError, TypeError) as error:
        parser.exit(1, f"pyworldatlas: error: {error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
