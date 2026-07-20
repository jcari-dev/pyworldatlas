"""Command-line entry point for the builder."""

from __future__ import annotations

import argparse
from pathlib import Path

from .core import build_database, normalize, report, run, write_manifests


def main() -> int:
    parser = argparse.ArgumentParser(prog="pyworldatlas-builder")
    parser.add_argument("command", choices=("normalize", "build", "report", "all"), default="all", nargs="?")
    args = parser.parse_args()
    root = Path.cwd()
    if args.command == "all":
        run(root)
    else:
        write_manifests(root)
        normalized = normalize(root)
        if args.command in {"build", "report"}:
            database = build_database(root, normalized)
            if args.command == "report":
                report(root, normalized, database)
    return 0

