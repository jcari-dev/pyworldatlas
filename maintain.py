"""Human-facing maintainer commands for PyWorldAtlas."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import venv


ROOT = Path(__file__).resolve().parent


def run(command: list[str], *, env: dict[str, str] | None = None) -> None:
    print("  $", " ".join(command), flush=True)
    subprocess.run(command, cwd=ROOT, check=True, env=env)


def builder_env() -> dict[str, str]:
    env = os.environ.copy()
    parts = [str(ROOT / "pipeline/src"), str(ROOT / "src")]
    if env.get("PYTHONPATH"):
        parts.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(parts)
    return env


def refresh() -> None:
    stages = [
        "Reading captured source snapshots", "Normalizing source records",
        "Merging and applying reviewed naming overrides", "Validating normalized data",
        "Building SQLite", "Validating SQLite", "Generating reports",
        "Installing accepted database", "Running runtime tests",
    ]
    for number, label in enumerate(stages[:1], 1):
        print(f"[{number}/9] {label} ...", flush=True)
    run([sys.executable, "-m", "pyworldatlas_builder", "all"], env=builder_env())
    for number, label in enumerate(stages[1:8], 2):
        print(f"[{number}/9] {label} ... PASS")
    status(write=True)
    print("[9/9] Running runtime tests ...", flush=True)
    run_tests()


def run_tests() -> None:
    run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], env=builder_env())


def status(*, write: bool = True) -> None:
    path = ROOT / "build_data/reports/status.json"
    if not path.exists():
        print("Status is unavailable until `python maintain.py refresh --offline` is run.")
        return
    data = json.loads(path.read_text(encoding="utf-8"))
    coverage = data["coverage"]
    lines = [
        "PyWorldAtlas project status", "", f"Library version: {data['library_version']}",
        f"Dataset version: {data['dataset_version']}", f"Schema version: {data['schema_version']}", "",
        f"Countries: {coverage['countries']} / 12 (Release 0.1.0 scope)",
        f"Capitals: {coverage['capitals']}", f"Capital coordinates: {coverage['capital_coordinates']} / {coverage['capitals']}",
        f"Major cities: {coverage['major_cities']}", f"Last validation: {coverage['validation']}",
    ]
    print("\n".join(lines))
    if write:
        table = ["| Milestone | Version | Status | Implemented functions | Tests | Dataset coverage | Documentation | Release |", "|---|---:|---|---|---|---|---|---|"]
        table += [f"| {m['name']} | {m['version']} | {m['status']} | {m['functions']} | {m['tests']} | {m['dataset']} | {m['docs']} | {m['release']} |" for m in data["milestones"]]
        markdown = "# Roadmap status\n\n> This file is generated from `build_data/reports/status.json`.\n\n" + "\n".join(lines[2:]) + "\n\n" + "\n".join(table) + "\n"
        (ROOT / "ROADMAP_STATUS.md").write_text(markdown, encoding="utf-8")
        generated = ROOT / "docs/source/_generated"
        generated.mkdir(parents=True, exist_ok=True)
        rst = "Project status\n==============\n\n.. THIS FILE IS GENERATED. DO NOT EDIT DIRECTLY.\n\n" + "\n".join(lines[2:]) + "\n"
        (generated / "project_status.rst").write_text(rst, encoding="utf-8")


def build_wheel() -> Path:
    dist = ROOT / "dist"
    if dist.exists():
        shutil.rmtree(dist)
    run([sys.executable, "-m", "pip", "wheel", ".", "--no-deps", "--no-build-isolation", "--wheel-dir", "dist"])
    wheels = list(dist.glob("*.whl"))
    if len(wheels) != 1:
        raise RuntimeError("Expected exactly one wheel")
    return wheels[0]


def demo() -> Path:
    wheel = build_wheel()
    with tempfile.TemporaryDirectory(prefix="pyworldatlas-demo-") as folder:
        environment = Path(folder) / "venv"
        venv.EnvBuilder(with_pip=True).create(environment)
        python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        run([str(python), "-m", "pip", "install", "--no-index", "--no-deps", str(wheel)])
        for example in sorted((ROOT / "examples").glob("*.py")):
            run([str(python), str(example)])
    return wheel


def docs(wheel: Path | None = None) -> None:
    status(write=True)
    python = Path(sys.executable)
    temporary: tempfile.TemporaryDirectory[str] | None = None
    env = builder_env()
    if wheel is not None:
        temporary = tempfile.TemporaryDirectory(prefix="pyworldatlas-docs-")
        environment = Path(temporary.name) / "venv"
        venv.EnvBuilder(with_pip=True, system_site_packages=True).create(environment)
        python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        run([str(python), "-m", "pip", "install", "--no-index", "--no-deps", str(wheel)])
        env = os.environ.copy()
        env.pop("PYTHONPATH", None)
    try:
        run([str(python), "-m", "sphinx", "-W", "--keep-going", "-b", "html", "docs/source", "docs/_build/html"], env=env)
        run([str(python), "-m", "sphinx", "-W", "--keep-going", "-b", "doctest", "docs/source", "docs/_build/doctest"], env=env)
    finally:
        if temporary is not None:
            temporary.cleanup()


def check() -> None:
    print("[1/4] Runtime and pipeline tests")
    run_tests()
    print("[2/4] Offline wheel demo")
    wheel = demo()
    print("[3/4] Documentation")
    docs(wheel)
    print("[4/4] Wheel content audit")
    import zipfile
    wheel = next((ROOT / "dist").glob("*.whl"))
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
    databases = [name for name in names if name.endswith(".sqlite3")]
    forbidden = [name for name in names if name.startswith(("pipeline/", "tests/", "docs/", "build_data/"))]
    if len(databases) != 1 or forbidden:
        raise RuntimeError(f"Wheel audit failed: databases={databases}, forbidden={forbidden}")
    print("All checks passed.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    refresh_parser = sub.add_parser("refresh")
    refresh_parser.add_argument("--offline", action="store_true", help="use captured raw snapshots only")
    sub.add_parser("status")
    sub.add_parser("test")
    sub.add_parser("demo")
    sub.add_parser("docs")
    sub.add_parser("check")
    args = parser.parse_args()
    if args.command == "refresh":
        if not args.offline:
            parser.error("Release 0.1.0 currently requires --offline; fetch is intentionally separate from the deterministic build")
        refresh()
    elif args.command == "status":
        status()
    elif args.command == "test":
        run_tests()
    elif args.command == "demo":
        demo()
    elif args.command == "docs":
        docs()
    else:
        check()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
