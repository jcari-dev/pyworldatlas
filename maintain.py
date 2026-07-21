"""Human-facing maintainer commands for PyWorldAtlas."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import re
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


def bootstrap() -> None:
    """Install the runtime, builder, release, and documentation toolchain."""
    run([
        sys.executable, "-m", "pip", "install", "-r", "docs/requirements.txt",
        "build>=1.2,<2", "-e", ".", "-e", "pipeline",
    ])


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
        f"Countries and areas: {coverage['countries']} (UN M49 scope)",
        f"Capitals: {coverage['capitals']} / {coverage['countries']}", f"Capital coordinates: {coverage['capital_coordinates']} / {coverage['capitals']}",
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


def project_version() -> str:
    """Read the canonical package version without importing the project."""
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', text, flags=re.MULTILINE)
    if match is None:
        raise RuntimeError("Could not read the project version from pyproject.toml")
    return match.group(1)


def file_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def build_distributions() -> tuple[Path, Path]:
    """Build one wheel and one source distribution with the standard frontend."""
    dist = ROOT / "dist"
    if dist.exists():
        shutil.rmtree(dist)
    run([sys.executable, "-m", "build"])
    wheels = sorted(dist.glob("*.whl"))
    sdists = sorted(dist.glob("*.tar.gz"))
    if len(wheels) != 1 or len(sdists) != 1:
        raise RuntimeError(f"Expected one wheel and one sdist, found {wheels!r} and {sdists!r}")
    return wheels[0], sdists[0]


def demo(wheel: Path | None = None) -> Path:
    wheel = wheel or build_wheel()
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


def prepare_release(version: str) -> None:
    """Validate and build a release with checksums and a machine-readable manifest."""
    current = project_version()
    if version != current:
        raise RuntimeError(f"Requested release {version}, but pyproject.toml contains {current}")
    version_module = (ROOT / "src/pyworldatlas/_version.py").read_text(encoding="utf-8")
    if f'__version__ = "{version}"' not in version_module:
        raise RuntimeError("src/pyworldatlas/_version.py does not match pyproject.toml")
    docs_config = (ROOT / "docs/source/conf.py").read_text(encoding="utf-8")
    if f'release = "{version}"' not in docs_config:
        raise RuntimeError("docs/source/conf.py does not match pyproject.toml")
    if f"## {version} " not in (ROOT / "CHANGELOG.md").read_text(encoding="utf-8"):
        raise RuntimeError(f"CHANGELOG.md has no {version} release heading")

    print("[1/5] Runtime and pipeline tests")
    run_tests()
    print("[2/5] Build wheel and source distribution")
    wheel, sdist = build_distributions()
    print("[3/5] Clean installation and examples from release wheel")
    demo(wheel)
    print("[4/5] Documentation from release wheel")
    docs(wheel)
    print("[5/5] Release wheel content audit")
    audit_wheel(wheel)
    artifacts = [wheel, sdist]
    status_data = json.loads((ROOT / "build_data/reports/status.json").read_text(encoding="utf-8"))
    if status_data["library_version"] != version:
        raise RuntimeError("Generated status metadata does not match the release version")
    git_result = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True,
        capture_output=True, text=True,
    )
    manifest = {
        "library_version": version,
        "dataset_version": status_data["dataset_version"],
        "schema_version": status_data["schema_version"],
        "git_commit": git_result.stdout.strip(),
        "country_count": status_data["coverage"]["countries"],
        "capital_count": status_data["coverage"]["capitals"],
        "major_city_count": status_data["coverage"]["major_cities"],
        "artifacts": {
            path.name: {"sha256": file_sha256(path), "size_bytes": path.stat().st_size}
            for path in artifacts
        },
        "tests": "passed",
        "wheel_smoke_test": "passed",
        "docs_html": "passed",
        "docs_doctest": "passed",
        "wheel_audit": "passed",
    }
    (ROOT / "dist/release-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8",
    )
    (ROOT / "dist/SHA256SUMS").write_text(
        "".join(f"{file_sha256(path)}  {path.name}\n" for path in artifacts),
        encoding="utf-8",
    )
    print(f"Release {version} prepared in {ROOT / 'dist'}")


def preview(*, host: str = "127.0.0.1", port: int = 8000) -> None:
    """Build the documentation and serve it until the user presses Ctrl+C."""
    docs()
    output = ROOT / "docs/_build/html"
    url = f"http://{host}:{port}/"
    print(f"\nDocumentation preview: {url}")
    print("Press Ctrl+C to stop the preview server.\n")
    command = [
        sys.executable, "-m", "http.server", str(port),
        "--bind", host, "--directory", str(output),
    ]
    print("  $", " ".join(command), flush=True)
    try:
        subprocess.run(command, cwd=ROOT, check=True)
    except KeyboardInterrupt:
        print("\nDocumentation preview stopped.")


def check() -> None:
    print("[1/4] Runtime and pipeline tests")
    run_tests()
    print("[2/4] Offline wheel demo")
    wheel = demo()
    print("[3/4] Documentation")
    docs(wheel)
    print("[4/4] Wheel content audit")
    audit_wheel(wheel)


def audit_wheel(wheel: Path) -> None:
    """Ensure the runtime wheel contains one database and no development tree."""
    import zipfile
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
    sub.add_parser("bootstrap")
    refresh_parser = sub.add_parser("refresh")
    refresh_parser.add_argument("--offline", action="store_true", help="use captured raw snapshots only")
    sub.add_parser("status")
    sub.add_parser("test")
    sub.add_parser("demo")
    docs_parser = sub.add_parser("docs")
    docs_parser.add_argument("--wheel", type=Path, help="build documentation from this wheel")
    preview_parser = sub.add_parser("preview")
    preview_parser.add_argument("--host", default="127.0.0.1")
    preview_parser.add_argument("--port", default=8000, type=int)
    release_parser = sub.add_parser("prepare-release")
    release_parser.add_argument("version")
    sub.add_parser("check")
    args = parser.parse_args()
    if args.command == "bootstrap":
        bootstrap()
    elif args.command == "refresh":
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
        docs(args.wheel)
    elif args.command == "preview":
        preview(host=args.host, port=args.port)
    elif args.command == "prepare-release":
        prepare_release(args.version)
    else:
        check()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
