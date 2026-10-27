"""Install and locate optional PyWorldAtlas data packs.

A data pack is a ``.pack`` file (an uncompressed zip archive) that holds extra
offline data, such as the 3D map editions. Packs are published as files on the
project's GitHub releases. Each library release pins the SHA-256 checksum of
every pack it accepts, so a modified, damaged, or mismatched file is refused.

Normal use never touches the network. Only :func:`get` (``pyworldatlas get``)
downloads, and only when it is called explicitly. Packs can also be installed
from a local file with :func:`add`, for example on a machine without internet.

Packs are stored in one folder, chosen in this order:

1. the ``data_dir`` argument (also accepted by :class:`pyworldatlas.Atlas`);
2. the ``PYWORLDATLAS_DATA`` environment variable;
3. a per-user folder: ``%LOCALAPPDATA%\\PyWorldAtlas\\packs`` on Windows,
   ``~/Library/Application Support/PyWorldAtlas/packs`` on macOS, and
   ``$XDG_DATA_HOME/pyworldatlas/packs`` (default ``~/.local/share``) elsewhere.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
from typing import Any
import zipfile

from ._version import __version__
from .exceptions import AtlasError

PACK_FORMAT = 1
RELEASE_URL = "https://github.com/jcari-dev/pyworldatlas/releases/download/v{version}/{file}"
_INDEX_FILE = Path(__file__).with_name("_pack_index.json")
_MANIFEST = "manifest.json"


class PackError(AtlasError):
    """Raised when a data pack cannot be found, verified, or installed."""


@dataclass(frozen=True, slots=True)
class PackInfo:
    """One data pack this library release accepts."""

    name: str
    title: str
    file: str
    sha256: str
    size_bytes: int

    @property
    def url(self) -> str:
        """Return the GitHub release download address for this pack."""
        return RELEASE_URL.format(version=__version__, file=self.file)


@dataclass(frozen=True, slots=True)
class InstalledPack:
    """One data pack found in a pack folder."""

    name: str
    path: Path
    sha256: str
    current: bool
    """True when the installed pack is the exact one this release pins."""


def _index() -> dict[str, PackInfo]:
    data = json.loads(_INDEX_FILE.read_text(encoding="utf-8"))
    return {
        name: PackInfo(name, item["title"], item["file"], item["sha256"], item["size_bytes"])
        for name, item in data["packs"].items()
    }


def available() -> tuple[PackInfo, ...]:
    """Return every pack this library release can install, by name."""
    return tuple(sorted(_index().values(), key=lambda pack: pack.name))


def pack_info(name: str) -> PackInfo:
    """Return the pinned description of one pack, or raise :class:`PackError`."""
    index = _index()
    if name not in index:
        choices = ", ".join(sorted(index))
        raise PackError(f"Unknown data pack {name!r}. Available packs: {choices}")
    return index[name]


def default_data_dir() -> Path:
    """Return the per-user pack folder used when no other folder is given."""
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
        return base / "PyWorldAtlas" / "packs"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "PyWorldAtlas" / "packs"
    base = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share")
    return base / "pyworldatlas" / "packs"


def data_dir(path: str | Path | None = None) -> Path:
    """Resolve the pack folder from ``path``, ``PYWORLDATLAS_DATA``, or the default."""
    if path is not None:
        return Path(path).expanduser()
    configured = os.environ.get("PYWORLDATLAS_DATA")
    if configured:
        return Path(configured).expanduser()
    return default_data_dir()


def _read_manifest(folder: Path) -> dict[str, Any] | None:
    try:
        manifest = json.loads((folder / _MANIFEST).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return manifest if isinstance(manifest, dict) else None


def installed(path: str | Path | None = None) -> tuple[InstalledPack, ...]:
    """Return the packs installed in a pack folder, by name."""
    root = data_dir(path)
    if not root.is_dir():
        return ()
    index = _index()
    found = []
    for folder in sorted(root.iterdir()):
        manifest = _read_manifest(folder) if folder.is_dir() else None
        if not manifest or manifest.get("format") != PACK_FORMAT:
            continue
        name = str(manifest.get("name"))
        if folder.name != name:
            continue
        digest = str(manifest.get("pack_sha256", ""))
        pin = index.get(name)
        found.append(InstalledPack(name, folder, digest, pin is not None and pin.sha256 == digest))
    return tuple(found)


def pack_path(name: str, path: str | Path | None = None) -> Path | None:
    """Return the folder of an installed pack, or ``None`` if it is missing."""
    folder = data_dir(path) / name
    manifest = _read_manifest(folder)
    if manifest and manifest.get("format") == PACK_FORMAT and manifest.get("name") == name:
        return folder
    return None


def _file_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def add(file: str | Path, path: str | Path | None = None) -> InstalledPack:
    """Install a pack from a local ``.pack`` file and return it.

    The file's SHA-256 checksum must match one of the packs this release pins,
    so only official, unmodified packs are accepted. An existing copy of the
    same pack is replaced.
    """
    source = Path(file).expanduser()
    if not source.is_file():
        raise PackError(f"Pack file not found: {source}")
    digest = _file_sha256(source)
    matches = [pack for pack in _index().values() if pack.sha256 == digest]
    if not matches:
        raise PackError(
            f"{source.name} is not a pack published for PyWorldAtlas {__version__} "
            "(its checksum does not match). Download it with: pyworldatlas get NAME"
        )
    pack = matches[0]
    root = data_dir(path)
    root.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{pack.name}-", dir=root))
    try:
        with zipfile.ZipFile(source) as archive:
            manifest = json.loads(archive.read(_MANIFEST))
            if manifest.get("format") != PACK_FORMAT or manifest.get("name") != pack.name:
                raise PackError(f"{source.name} has an unexpected manifest")
            expected: dict[str, str] = manifest["files"]
            for member, member_digest in expected.items():
                if Path(member).name != member or member in {".", "..", _MANIFEST}:
                    raise PackError(f"{source.name} contains an unsafe file name")
                data = archive.read(member)
                if sha256(data).hexdigest() != member_digest:
                    raise PackError(f"{member} in {source.name} failed its checksum")
                (staging / member).write_bytes(data)
        manifest["pack_sha256"] = digest
        (staging / _MANIFEST).write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        target = root / pack.name
        if target.exists():
            shutil.rmtree(target)
        staging.rename(target)
    except (OSError, KeyError, ValueError, zipfile.BadZipFile) as error:
        raise PackError(f"Could not install {source.name}: {error}") from error
    finally:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)
    return InstalledPack(pack.name, target, digest, True)


def get(
    name: str,
    path: str | Path | None = None,
    *,
    progress: Callable[[int, int], None] | None = None,
) -> InstalledPack:
    """Download one pack from this release on GitHub, verify it, and install it.

    ``progress`` is called with ``(downloaded_bytes, total_bytes)`` while the
    file downloads. This is the only function in PyWorldAtlas that uses the
    network.
    """
    from urllib.error import URLError
    from urllib.request import urlopen

    pack = pack_info(name)
    root = data_dir(path)
    root.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(prefix=f".{pack.name}-", suffix=".pack", dir=root)
    os.close(handle)
    download = Path(temporary)
    try:
        try:
            with urlopen(pack.url, timeout=60) as response, download.open("wb") as output:
                received = 0
                while block := response.read(1 << 16):
                    output.write(block)
                    received += len(block)
                    if progress is not None:
                        progress(received, pack.size_bytes)
        except (URLError, OSError) as error:
            raise PackError(
                f"Could not download {pack.file} from {pack.url}: {error}. "
                "If this machine has no internet access, download the file elsewhere "
                "and run: pyworldatlas add PATH"
            ) from error
        if _file_sha256(download) != pack.sha256:
            raise PackError(f"The downloaded {pack.file} failed its checksum; nothing was installed")
        return add(download, path)
    finally:
        download.unlink(missing_ok=True)


def remove(name: str, path: str | Path | None = None) -> bool:
    """Delete an installed pack. Return ``False`` when it was not installed."""
    folder = pack_path(name, path)
    if folder is None:
        return False
    shutil.rmtree(folder)
    return True
