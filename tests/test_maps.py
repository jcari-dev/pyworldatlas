from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zlib

from pack_fixtures import ROOT, installed_packs

from pyworldatlas import Atlas, MapSupportNotInstalledError
from pyworldatlas.maps import CountryMap, MapDataError, available_map_qualities

EDITIONS = (
    (ROOT / "packs/maps-lite/maps.sqlite3", "overview"),
    (ROOT / "packs/maps/maps.sqlite3", "standard"),
)


def fingerprint(figure: dict[str, object]) -> str:
    text = json.dumps(figure, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return sha256(text.encode("utf-8")).hexdigest()


class MapDataTests(unittest.TestCase):
    def test_both_map_editions_cover_the_complete_atlas(self) -> None:
        with Atlas() as atlas:
            expected = {country.alpha2 for country in atlas}
        for path, quality in EDITIONS:
            connection = sqlite3.connect(path)
            try:
                metadata = dict(connection.execute("SELECT key, value FROM metadata"))
                actual = {row[0] for row in connection.execute("SELECT alpha2 FROM country_map")}
            finally:
                connection.close()
            self.assertEqual(metadata["format_version"], "1")
            self.assertEqual(metadata["quality"], quality)
            self.assertEqual(actual, expected)

    def test_every_map_record_passes_its_integrity_hash(self) -> None:
        for path, _ in EDITIONS:
            connection = sqlite3.connect(path)
            try:
                rows = connection.execute(
                    "SELECT alpha2, payload, uncompressed_bytes, sha256 FROM country_map"
                ).fetchall()
            finally:
                connection.close()
            for alpha2, compressed, size, expected_hash in rows:
                raw = zlib.decompress(compressed)
                self.assertEqual(len(raw), size, alpha2)
                self.assertEqual(sha256(raw).hexdigest(), expected_hash, alpha2)
                payload = json.loads(raw)
                self.assertEqual(payload["alpha2"], alpha2)
                self.assertGreaterEqual(payload["rows"], 3)
                self.assertGreaterEqual(payload["columns"], 3)
                self.assertGreater(payload["landCells"], 0)


class MapViewerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = installed_packs()

    def atlas(self) -> Atlas:
        return Atlas(data_dir=self.data)

    def test_quality_discovery_and_selection(self) -> None:
        self.assertEqual(available_map_qualities(self.data), ("overview", "standard"))
        with self.atlas() as atlas:
            automatic = atlas.map("Brazil")
            overview = atlas.map("BR", quality="overview")
        self.assertEqual(automatic.quality, "standard")
        self.assertEqual(automatic.resolution_arc_minutes, 5)
        self.assertEqual(overview.quality, "overview")
        self.assertEqual(overview.resolution_arc_minutes, 20)

    def test_missing_pack_explains_how_to_install_it(self) -> None:
        with tempfile.TemporaryDirectory() as empty, Atlas(data_dir=empty) as atlas:
            self.assertEqual(available_map_qualities(empty), ())
            with self.assertRaisesRegex(MapSupportNotInstalledError, "pyworldatlas get maps$"):
                atlas.map("Brazil")
            with self.assertRaisesRegex(MapSupportNotInstalledError, "get maps-lite"):
                atlas.map("Brazil", quality="overview")
        with self.assertRaises(ValueError):
            _ = CountryMap("BR", "Brazil", requested_quality="ultra").quality

    def test_figures_are_unchanged(self) -> None:
        """Pin two complete figures so rendering changes are always deliberate."""
        with self.atlas() as atlas:
            iceland = atlas.map("IS", quality="overview").to_dict()
            brazil = atlas.map("BR", quality="standard").to_dict()
        self.assertEqual(
            fingerprint(iceland),
            "815ad7f1ae2ab05606d5900e310812528415c21110bd7be759d1eac03c32170d",
        )
        self.assertEqual(
            fingerprint(brazil),
            "8e7e9a0002e9ebbcbca9c4f27188ba7e8e2d8e603b31a818bd33448954fb4fea",
        )

    def test_country_map_builds_an_offline_interactive_figure(self) -> None:
        with self.atlas() as atlas:
            figure = atlas.map("Brazil", quality="overview").to_dict()
        names = {trace["name"] for trace in figure["data"]}
        self.assertEqual(names, {"Terrain", "Country outline", "Rivers", "Capital"})
        self.assertEqual(len(figure["layout"]["updatemenus"][0]["buttons"]), 2)
        self.assertEqual(figure["layout"]["template"]["layout"]["paper_bgcolor"], "white")

    def test_map_controls_adjust_height_and_optional_labels(self) -> None:
        with self.atlas() as atlas:
            layout = atlas.map("Iceland", quality="standard").to_dict()["layout"]
        slider = layout["sliders"][0]
        self.assertEqual(
            [step["label"] for step in slider["steps"]],
            ["0.5×", "1×", "1.5×", "2×", "3×"],
        )
        self.assertEqual(slider["active"], 1)
        menus = layout["updatemenus"]
        self.assertEqual(
            [button["label"] for button in menus[1]["buttons"]],
            ["Capital only", "All names", "River names", "Hide names"],
        )
        self.assertLess(menus[1]["y"], menus[0]["y"])
        annotations = layout["scene"]["annotations"]
        self.assertEqual(annotations[0]["text"], "<b>Reykjavík</b>")
        self.assertTrue(annotations[0]["visible"])
        self.assertEqual({item["text"] for item in annotations[1:]}, {"<b>Þjórsá</b>"})
        self.assertTrue(all(not item["visible"] for item in annotations[1:]))

    def test_figure_uses_plotly_only_when_it_is_installed(self) -> None:
        with self.atlas() as atlas:
            brazil = atlas.map("Brazil", quality="overview")
        with patch.dict(sys.modules, {"plotly": None, "plotly.graph_objects": None}):
            with self.assertRaisesRegex(MapDataError, "pip install plotly"):
                brazil.figure()

    def test_show_opens_a_standalone_local_html_document(self) -> None:
        with self.atlas() as atlas:
            brazil = atlas.map("Brazil", quality="overview")
        with tempfile.TemporaryDirectory() as folder:
            html = brazil.write_html(Path(folder) / "brazil.html").read_text(encoding="utf-8")
            self.assertIn("<title>Brazil 3D map · PyWorldAtlas</title>", html)
            self.assertIn("plotly.js v3.7.0", html)
            self.assertIn("Map motion and export controls", html)
            self.assertIn("Download PNG", html)
            self.assertIn("prefers-reduced-motion", html)
            self.assertIn("width: 1600", html)
            self.assertIn("height: 900", html)
            self.assertIn("scale: 2", html)
            self.assertNotRegex(html, r'<script[^>]+src=["\']https?://')
            self.assertEqual(html.count("</script>"), 3)
        with patch("webbrowser.open", return_value=True) as opened:
            shown = brazil.show(auto_rotate=True, rotation_speed=1.5)
        opened.assert_called_once_with(shown.as_uri(), new=2)
        shown_html = shown.read_text(encoding="utf-8")
        self.assertIn("if (true && !reducedMotion)", shown_html)
        self.assertIn("speedInput.value = String(1.5)", shown_html)

    def test_rotation_options_are_validated(self) -> None:
        with self.atlas() as atlas:
            brazil = atlas.map("Brazil", quality="overview")
        for speed in (0, 3.1, float("inf"), float("nan")):
            with self.subTest(speed=speed), self.assertRaises(ValueError):
                brazil.to_html(rotation_speed=speed)
        with self.assertRaises(TypeError):
            brazil.to_html(auto_rotate="yes")  # type: ignore[arg-type]
        with self.assertRaises(TypeError):
            brazil.to_html(rotation_speed=True)

    def test_documentation_gif_tool_has_a_standalone_help_command(self) -> None:
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools/create_map_gif.py"), "--help"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertIn("360-degree PyWorldAtlas map rotation", result.stdout)
        self.assertIn("--output", result.stdout)


if __name__ == "__main__":
    unittest.main()
