"""Build byte-for-byte reproducible data packs from the repository's packs folder.

Maintainers run this through ``python maintain.py packs``. It is shipped with
the package only so tests and maintainers share one implementation; the
library never calls it at runtime.
"""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import zipfile

from .packs import PACK_FORMAT

# A fixed timestamp keeps archives identical across machines and runs.
_TIMESTAMP = (1980, 1, 1, 0, 0, 0)


def build_packs(source: Path, output: Path) -> dict[str, dict[str, object]]:
    """Write every pack in ``source/packs.json`` to ``output`` and return the index.

    Archives are stored uncompressed with fixed metadata and sorted entries, so
    the same inputs always produce the same SHA-256 checksum.
    """
    config = json.loads((source / "packs.json").read_text(encoding="utf-8"))
    output.mkdir(parents=True, exist_ok=True)
    index: dict[str, dict[str, object]] = {}
    for name, spec in sorted(config["packs"].items()):
        contents = {
            member: (source / relative).read_bytes()
            for member, relative in sorted(spec["files"].items())
        }
        manifest = {
            "format": PACK_FORMAT,
            "name": name,
            "title": spec["title"],
            "files": {member: sha256(data).hexdigest() for member, data in contents.items()},
        }
        file = f"pyworldatlas-{name}.pack"
        target = output / file
        with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_STORED) as archive:
            entries = [("manifest.json", (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode())]
            entries += list(contents.items())
            for member, data in entries:
                info = zipfile.ZipInfo(member, date_time=_TIMESTAMP)
                info.compress_type = zipfile.ZIP_STORED
                info.external_attr = 0o644 << 16
                info.create_system = 3
                archive.writestr(info, data)
        payload = target.read_bytes()
        index[name] = {
            "title": spec["title"],
            "file": file,
            "sha256": sha256(payload).hexdigest(),
            "size_bytes": len(payload),
        }
    return index


def index_document(index: dict[str, dict[str, object]]) -> str:
    """Return the ``_pack_index.json`` text for a built index."""
    return json.dumps({"format": PACK_FORMAT, "packs": index}, indent=2, sort_keys=True) + "\n"
