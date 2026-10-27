"""Build the data packs once per test run and install them into a temporary folder."""

from __future__ import annotations

import atexit
from pathlib import Path
import shutil
import tempfile

from pyworldatlas import packs
from pyworldatlas._packbuild import build_packs

ROOT = Path(__file__).resolve().parents[1]
_STATE: dict[str, Path] = {}


def _workspace() -> Path:
    if "root" not in _STATE:
        folder = Path(tempfile.mkdtemp(prefix="pyworldatlas-test-packs-"))
        atexit.register(shutil.rmtree, folder, ignore_errors=True)
        _STATE["root"] = folder
    return _STATE["root"]


def pack_files() -> Path:
    """Return a folder holding freshly built ``.pack`` files."""
    if "files" not in _STATE:
        folder = _workspace() / "files"
        build_packs(ROOT / "packs", folder)
        _STATE["files"] = folder
    return _STATE["files"]


def installed_packs() -> Path:
    """Return a pack folder with every pack installed."""
    if "installed" not in _STATE:
        folder = _workspace() / "installed"
        for file in sorted(pack_files().glob("*.pack")):
            packs.add(file, folder)
        _STATE["installed"] = folder
    return _STATE["installed"]
