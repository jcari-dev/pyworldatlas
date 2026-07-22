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
import tarfile
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
        "build>=1.2,<2", "setuptools>=77", "-e", ".", "-e", "pipeline",
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
        f"Dataset version: {data['dataset_version']}", f"Schema version: {data['schema_version']}",
        "",
        f"Countries and areas: {coverage['countries']} (UN M49 scope)",
        f"Capitals: {coverage['capitals']} / {coverage['countries']}", f"Capital coordinates: {coverage['capital_coordinates']} / {coverage['capitals']}",
        f"Populated places: {coverage['major_cities']}", f"Last validation: {coverage['validation']}",
    ]
    if "local_names" in coverage:
        details = (
            f"Local identity names: {coverage['local_names']} / "
            f"{coverage['countries']} countries and areas"
        )
        if "local_name_languages" in coverage:
            details += (
                f" / {coverage['local_name_languages']} languages / "
                f"{coverage['local_name_scripts']} scripts"
            )
        lines.insert(-1, details)
        if "national_official_local_names" in coverage:
            lines.insert(
                -1,
                "Reviewed national official forms: "
                f"{coverage['national_official_local_names']} / "
                f"official-language selections: "
                f"{coverage['official_language_local_names']} / "
                f"{coverage['countries']}",
            )
        if "english_formal_names" in coverage:
            lines.insert(
                -1,
                "English formal names: "
                f"{coverage['english_formal_names']} / "
                f"{coverage['countries']} profiles / "
                f"{coverage['distinct_english_formal_names']} distinct long forms",
            )
    if "population_profiles" in coverage:
        lines.insert(-1, f"Profile fields: {coverage['population_profiles']} population / {coverage['currency_profiles']} currency / {coverage['language_profiles']} language-code records")
    if "anthem_titles" in coverage:
        lines.insert(
            -1,
            "Reference facts: "
            f"{coverage['anthem_titles']} anthem titles / "
            f"{coverage['mottos']} reviewed mottos / "
            f"{coverage['demonyms']} English demonym profiles",
        )
        lines.insert(
            -1,
            "Practical profiles: "
            f"{coverage['timezone_profiles']} timezone profiles / "
            f"{coverage['postal_code_formats']} postal formats / "
            f"{coverage['currency_symbols']} currency symbols",
        )
    if "reviewed_land_borders" in coverage:
        lines.insert(-1, f"Reviewed land borders: {coverage['reviewed_land_borders']} / borderless entities: {coverage['countries_with_no_land_borders']}")
    if "physical_profiles" in coverage:
        lines.insert(
            -1,
            "Physical profiles: "
            f"{coverage['physical_profiles']} source profiles / "
            f"{coverage['coastline_profiles']} coastlines / "
            f"{coverage['elevation_extreme_profiles']} elevation-extreme pairs",
        )
        lines.insert(
            -1,
            "Named physical features: "
            f"{coverage['river_records']} rivers across {coverage['river_profiles']} profiles / "
            f"{coverage['lake_records']} lakes across {coverage['lake_profiles']} profiles",
        )
        lines.insert(
            -1,
            "Climate: "
            f"{coverage['climate_summary_profiles']} summaries / "
            f"{coverage['koppen_geiger_profiles']} Köppen-Geiger profiles",
        )
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


def build_distributions(output_dir: Path | None = None) -> tuple[Path, Path]:
    """Build one wheel and one source distribution with the standard frontend."""
    dist = output_dir or ROOT / "dist"
    if dist.exists():
        try:
            shutil.rmtree(dist)
        except PermissionError as error:
            raise RuntimeError(
                f"Could not replace {dist}; close any process using its release artifacts"
            ) from error
    run([sys.executable, "-m", "build", "--no-isolation", "--outdir", str(dist)])
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
        clean_env = os.environ.copy()
        clean_env.pop("PYTHONPATH", None)
        clean_env["PYTHONUTF8"] = "1"
        run([
            str(python), "-m", "pip", "install", "--force-reinstall",
            "--no-index", "--no-deps", str(wheel),
        ], env=clean_env)
        for example in sorted((ROOT / "examples").glob("*.py")):
            run([str(python), str(example)], env=clean_env)
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
        env = os.environ.copy()
        env.pop("PYTHONPATH", None)
        run([
            str(python), "-m", "pip", "install", "--force-reinstall",
            "--no-index", "--no-deps", str(wheel),
        ], env=env)
    try:
        run([str(python), "-m", "sphinx", "-W", "--keep-going", "-b", "html", "docs/source", "docs/_build/html"], env=env)
        run([str(python), "-m", "sphinx", "-W", "--keep-going", "-b", "doctest", "docs/source", "docs/_build/doctest"], env=env)
    finally:
        if temporary is not None:
            temporary.cleanup()


def prepare_release(version: str, output_dir: Path | None = None) -> None:
    """Validate and build a release with checksums and a machine-readable manifest."""
    requested = (output_dir or ROOT / "dist").absolute()
    root = ROOT.resolve()
    dist_dir = (ROOT / "dist").absolute()
    build_dir = (ROOT / "build").absolute()
    if requested != dist_dir and build_dir not in requested.parents:
        raise RuntimeError(
            "Release output directory must be dist or a subdirectory of build"
        )
    relative_parts = requested.relative_to(ROOT.absolute()).parts
    current_path = ROOT.absolute()
    for part in relative_parts:
        current_path /= part
        is_junction = getattr(current_path, "is_junction", lambda: False)
        if current_path.is_symlink() or is_junction():
            raise RuntimeError("Release output directory cannot contain links or junctions")
    output_dir = requested.resolve()
    if output_dir == root or root not in output_dir.parents:
        raise RuntimeError("Release output directory must remain inside the repository")
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
    wheel, sdist = build_distributions(output_dir)
    print("[3/5] Clean installation and examples from release wheel")
    demo(wheel)
    print("[4/5] Documentation from release wheel")
    docs(wheel)
    print("[5/5] Release content and policy audit")
    audit_wheel(wheel)
    audit_sdist(sdist)
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
        "populated_place_count": status_data["coverage"]["major_cities"],
        "artifacts": {
            path.name: {"sha256": file_sha256(path), "size_bytes": path.stat().st_size}
            for path in artifacts
        },
        "tests": "passed",
        "wheel_smoke_test": "passed",
        "docs_html": "passed",
        "docs_doctest": "passed",
        "wheel_audit": "passed",
        "sdist_policy_audit": "passed",
    }
    (output_dir / "release-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8",
    )
    (output_dir / "SHA256SUMS").write_text(
        "".join(f"{file_sha256(path)}  {path.name}\n" for path in artifacts),
        encoding="utf-8",
    )
    print(f"Release {version} prepared in {output_dir}")


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
    with tempfile.TemporaryDirectory(prefix="pyworldatlas-check-") as folder:
        print("[2/4] Build distributions and run offline wheel demo")
        wheel, sdist = build_distributions(Path(folder) / "dist")
        demo(wheel)
        print("[3/4] Documentation")
        docs(wheel)
        print("[4/4] Release content and policy audit")
        audit_wheel(wheel)
        audit_sdist(sdist)


def audit_wheel(wheel: Path) -> None:
    """Ensure the runtime wheel contains one database and no development tree."""
    import zipfile
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
    databases = [name for name in names if name.endswith(".sqlite3")]
    forbidden = [name for name in names if name.startswith(("pipeline/", "tests/", "docs/", "build_data/"))]
    unicode_licenses = [name for name in names if name.endswith("UNICODE_LICENSE.txt")]
    if len(databases) != 1 or len(unicode_licenses) != 1 or forbidden:
        raise RuntimeError(
            "Wheel audit failed: "
            f"databases={databases}, unicode_licenses={unicode_licenses}, "
            f"forbidden={forbidden}"
        )
    print("All checks passed.")


def audit_sdist(sdist: Path) -> None:
    """Ensure the source distribution carries the public policy documents."""
    required = {
        "BOUNDARIES_AND_DISPUTES.md",
        "CODE_OF_CONDUCT.md",
        "CONTRIBUTING.md",
        "DATA_QUALITY.md",
        "DATA_SOURCES.md",
        "EDUCATIONAL_AND_NEUTRALITY_POLICY.md",
        "THIRD_PARTY_NOTICES.md",
    }
    with tarfile.open(sdist, "r:gz") as archive:
        included = {Path(name).name for name in archive.getnames()}
    missing = sorted(required - included)
    if missing:
        raise RuntimeError(
            f"Source distribution policy audit failed; missing={missing}"
        )
    print("Source distribution policy documents: PASS")


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
    release_parser.add_argument("--output-dir", type=Path, default=Path("dist"))
    sub.add_parser("check")
    args = parser.parse_args()
    if args.command == "bootstrap":
        bootstrap()
    elif args.command == "refresh":
        if not args.offline:
            parser.error("Refresh requires --offline; update captured source snapshots separately")
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
        output_dir = args.output_dir if args.output_dir.is_absolute() else ROOT / args.output_dir
        prepare_release(args.version, output_dir)
    else:
        check()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
