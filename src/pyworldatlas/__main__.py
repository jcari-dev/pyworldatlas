"""Command-line interface for exploring the atlas and managing data packs."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
import sys
from collections.abc import Sequence

from . import Atlas, AtlasError, __version__, packs


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

    names = [pack.name for pack in packs.available()]
    get = subcommands.add_parser(
        "get",
        help="download and install data packs",
        description=(
            "Download data packs from this release on GitHub, check their "
            "fingerprints, and install them. This is the only command that "
            "uses the network."
        ),
    )
    get.add_argument("names", nargs="+", choices=[*names, "all"], metavar="NAME",
                     help=f"pack to install: {', '.join(names)}, or all")
    add = subcommands.add_parser(
        "add",
        help="install a data pack from a local file",
        description="Install a downloaded .pack file, for example on a machine without internet.",
    )
    add.add_argument("files", nargs="+", metavar="FILE", help="path to a .pack file")
    subcommands.add_parser("packs", help="list installed and available data packs")
    remove = subcommands.add_parser("remove", help="delete an installed data pack")
    remove.add_argument("names", nargs="+", metavar="NAME", help="pack to delete")
    for command in (get, add, remove, subcommands.choices["packs"]):
        command.add_argument(
            "--data-dir", help="pack folder (default: PYWORLDATLAS_DATA or a per-user folder)"
        )
    return parser


def _megabytes(size: int) -> str:
    return f"{size / 1_000_000:.1f} MB"


def _pack_command(args: argparse.Namespace) -> int:
    folder = packs.data_dir(args.data_dir)
    if args.command == "get":
        wanted = [pack.name for pack in packs.available()] if "all" in args.names else args.names
        for name in dict.fromkeys(wanted):
            info = packs.pack_info(name)
            print(f"Downloading {name} ({_megabytes(info.size_bytes)}) ...", flush=True)
            installed = packs.get(name, folder)
            print(f"Installed {installed.name} in {installed.path}")
    elif args.command == "add":
        for file in args.files:
            installed = packs.add(file, folder)
            print(f"Installed {installed.name} in {installed.path}")
    elif args.command == "remove":
        for name in args.names:
            removed = packs.remove(name, folder)
            print(f"Removed {name}" if removed else f"{name} is not installed")
    else:
        present = {pack.name: pack for pack in packs.installed(folder)}
        print(f"Pack folder: {folder}")
        for info in packs.available():
            found = present.get(info.name)
            if found is None:
                state = f"available   -> pyworldatlas get {info.name}"
            elif found.current:
                state = "installed"
            else:
                state = f"update available -> pyworldatlas get {info.name}"
            print(f"  {info.name:<10} {_megabytes(info.size_bytes):>8}  {state}")
            print(f"  {'':<10} {'':>8}  {info.title}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the read-only PyWorldAtlas command-line interface."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
    parser = _parser()
    args = parser.parse_args(argv)
    if args.command in {"get", "add", "packs", "remove"}:
        try:
            return _pack_command(args)
        except (AtlasError, OSError) as error:
            parser.exit(1, f"pyworldatlas: error: {error}\n")
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
