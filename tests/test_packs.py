from __future__ import annotations

from contextlib import redirect_stdout
from io import BytesIO, StringIO
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from pack_fixtures import ROOT, pack_files

from pyworldatlas import packs
from pyworldatlas.__main__ import main
from pyworldatlas._packbuild import build_packs, index_document


class PackBuildTests(unittest.TestCase):
    def test_committed_index_matches_a_fresh_reproducible_build(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            index = build_packs(ROOT / "packs", Path(folder))
        committed = (ROOT / "src/pyworldatlas/_pack_index.json").read_text(encoding="utf-8")
        self.assertEqual(index_document(index), committed)
        self.assertEqual({pack.name for pack in packs.available()}, {"maps", "maps-lite"})

    def test_every_pack_carries_its_licenses_and_notice(self) -> None:
        for file in pack_files().glob("*.pack"):
            with zipfile.ZipFile(file) as archive:
                names = set(archive.namelist())
            self.assertTrue(
                {"manifest.json", "maps.sqlite3", "plotly.min.js", "LICENSE-plotly.txt",
                 "NOTICE.md"} <= names,
                file.name,
            )


class PackInstallTests(unittest.TestCase):
    def setUp(self) -> None:
        self.folder = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.folder, True)
        self.lite = pack_files() / "pyworldatlas-maps-lite.pack"

    def test_add_list_and_remove(self) -> None:
        self.assertEqual(packs.installed(self.folder), ())
        installed = packs.add(self.lite, self.folder)
        self.assertEqual(installed.name, "maps-lite")
        self.assertTrue(installed.current)
        self.assertEqual(packs.pack_path("maps-lite", self.folder), self.folder / "maps-lite")
        self.assertEqual([pack.name for pack in packs.installed(self.folder)], ["maps-lite"])
        packs.add(self.lite, self.folder)  # reinstalling replaces cleanly
        self.assertEqual(len(packs.installed(self.folder)), 1)
        self.assertEqual(sorted(path.name for path in self.folder.iterdir()), ["maps-lite"])
        self.assertTrue(packs.remove("maps-lite", self.folder))
        self.assertFalse(packs.remove("maps-lite", self.folder))
        self.assertIsNone(packs.pack_path("maps-lite", self.folder))

    def test_modified_or_unknown_files_are_refused(self) -> None:
        tampered = self.folder / "tampered.pack"
        tampered.write_bytes(self.lite.read_bytes() + b"x")
        with self.assertRaisesRegex(packs.PackError, "checksum does not match"):
            packs.add(tampered, self.folder)
        with self.assertRaisesRegex(packs.PackError, "not found"):
            packs.add(self.folder / "missing.pack", self.folder)
        self.assertEqual(packs.installed(self.folder), ())

    def test_unsafe_member_names_are_refused(self) -> None:
        buffer = BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            manifest = {"format": 1, "name": "maps-lite", "files": {"../escape.txt": "0" * 64}}
            archive.writestr("manifest.json", json.dumps(manifest))
            archive.writestr("../escape.txt", "nope")
        evil = self.folder / "evil.pack"
        evil.write_bytes(buffer.getvalue())
        fake = packs.PackInfo("maps-lite", "x", "evil.pack", packs._file_sha256(evil), 1)
        with patch.object(packs, "_index", return_value={"maps-lite": fake}):
            with self.assertRaisesRegex(packs.PackError, "unsafe file name"):
                packs.add(evil, self.folder / "store")
        self.assertFalse((self.folder / "escape.txt").exists())

    def test_get_downloads_verifies_and_installs(self) -> None:
        data = self.lite.read_bytes()
        seen: list[int] = []
        with patch("urllib.request.urlopen", return_value=BytesIO(data)) as opened:
            installed = packs.get("maps-lite", self.folder, progress=lambda done, total: seen.append(done))
        self.assertEqual(installed.name, "maps-lite")
        self.assertEqual(seen[-1], len(data))
        url = opened.call_args.args[0]
        self.assertTrue(url.startswith("https://github.com/jcari-dev/pyworldatlas/releases/download/v"))
        self.assertTrue(url.endswith("/pyworldatlas-maps-lite.pack"))
        self.assertEqual([path.name for path in self.folder.iterdir()], ["maps-lite"])

    def test_get_rejects_a_corrupted_download(self) -> None:
        with patch("urllib.request.urlopen", return_value=BytesIO(b"not a pack")):
            with self.assertRaisesRegex(packs.PackError, "failed its checksum"):
                packs.get("maps-lite", self.folder)
        self.assertEqual(list(self.folder.iterdir()), [])
        with self.assertRaisesRegex(packs.PackError, "Unknown data pack"):
            packs.get("everything-else", self.folder)

    def test_folder_resolution(self) -> None:
        with patch.dict(os.environ, {"PYWORLDATLAS_DATA": str(self.folder)}):
            self.assertEqual(packs.data_dir(), self.folder)
            self.assertEqual(packs.data_dir("elsewhere"), Path("elsewhere"))
        without = {key: value for key, value in os.environ.items() if key != "PYWORLDATLAS_DATA"}
        with patch.dict(os.environ, without, clear=True):
            self.assertEqual(packs.data_dir(), packs.default_data_dir())

    def test_command_line_manages_packs(self) -> None:
        def call(*arguments: str) -> tuple[int, str]:
            output = StringIO()
            with redirect_stdout(output):
                try:
                    code = main([*arguments, "--data-dir", str(self.folder)])
                except SystemExit as exit_:
                    code = int(exit_.code or 0)
            return code, output.getvalue()

        code, listing = call("packs")
        self.assertEqual(code, 0)
        self.assertIn("available   -> pyworldatlas get maps-lite", listing)
        self.assertEqual(call("add", str(self.lite))[0], 0)
        self.assertIn("maps-lite", call("packs")[1].split("installed")[0])
        self.assertIn("Removed maps-lite", call("remove", "maps-lite")[1])
        self.assertEqual(call("add", str(ROOT / "README.md"))[0], 1)


if __name__ == "__main__":
    unittest.main()
