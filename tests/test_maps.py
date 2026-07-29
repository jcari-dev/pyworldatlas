from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import re
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch
import zlib


ROOT = Path(__file__).resolve().parents[1]
for source in (
    ROOT / "packages/mapview/src",
    ROOT / "packages/mapdata-overview/src",
    ROOT / "packages/mapdata-standard/src",
):
    sys.path.insert(0, str(source))

from pyworldatlas import Atlas
from pyworldatlas_mapview import available_map_qualities


class MapDataTests(unittest.TestCase):
    def test_both_map_editions_cover_the_complete_atlas(self) -> None:
        with Atlas() as atlas:
            expected = {country.alpha2 for country in atlas}
        for path, quality in (
            (
                ROOT / "packages/mapdata-overview/src/pyworldatlas_mapdata_overview/data/maps.sqlite3",
                "overview",
            ),
            (
                ROOT / "packages/mapdata-standard/src/pyworldatlas_mapdata_standard/data/maps.sqlite3",
                "standard",
            ),
        ):
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
        for path in (
            ROOT / "packages/mapdata-overview/src/pyworldatlas_mapdata_overview/data/maps.sqlite3",
            ROOT / "packages/mapdata-standard/src/pyworldatlas_mapdata_standard/data/maps.sqlite3",
        ):
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
    def test_quality_discovery_and_selection(self) -> None:
        self.assertEqual(available_map_qualities(), ("overview", "standard"))
        with Atlas() as atlas:
            automatic = atlas.map("Brazil")
            overview = atlas.map("BR", quality="overview")
        self.assertEqual(automatic.quality, "standard")
        self.assertEqual(automatic.resolution_arc_minutes, 5)
        self.assertEqual(overview.quality, "overview")
        self.assertEqual(overview.resolution_arc_minutes, 20)

    def test_country_map_builds_an_offline_interactive_figure(self) -> None:
        with Atlas() as atlas:
            brazil = atlas.map("Brazil", quality="overview")
        figure = brazil.figure()
        names = {trace.name for trace in figure.data}
        self.assertIn("Terrain", names)
        self.assertIn("Country outline", names)
        self.assertIn("Rivers", names)
        self.assertIn("Capital", names)
        self.assertEqual(len(figure.layout.updatemenus[0].buttons), 2)

    def test_map_controls_adjust_height_and_optional_labels(self) -> None:
        with Atlas() as atlas:
            iceland = atlas.map("Iceland", quality="standard")
        figure = iceland.figure()

        self.assertEqual(
            [step.label for step in figure.layout.sliders[0].steps],
            ["0.5×", "1×", "1.5×", "2×", "3×"],
        )
        self.assertEqual(figure.layout.sliders[0].active, 1)
        self.assertEqual(
            [button.label for button in figure.layout.updatemenus[1].buttons],
            ["Capital only", "All names", "River names", "Hide names"],
        )
        self.assertLess(figure.layout.updatemenus[0].y, 1)
        self.assertLess(figure.layout.updatemenus[1].y, figure.layout.updatemenus[0].y)
        annotations = figure.layout.scene.annotations
        self.assertEqual(annotations[0].text, "<b>Reykjavík</b>")
        self.assertTrue(annotations[0].visible)
        self.assertEqual(
            {annotation.text for annotation in annotations[1:]},
            {"<b>Þjórsá</b>"},
        )
        self.assertTrue(all(not annotation.visible for annotation in annotations[1:]))

        capital = next(trace for trace in figure.data if trace.name == "Capital")
        self.assertEqual(capital.marker.size, 8)
        self.assertEqual(capital.marker.line.color, "#ffffff")

    def test_show_opens_a_standalone_local_html_document(self) -> None:
        with Atlas() as atlas:
            brazil = atlas.map("Brazil", quality="overview")
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "brazil.html"
            result = brazil.write_html(target)
            html = result.read_text(encoding="utf-8")
            self.assertIn("Brazil 3D map", html)
            self.assertIn("plotly.js", html)
            self.assertNotRegex(html, r'<script[^>]+src=["\']https?://')
        with patch("webbrowser.open", return_value=True) as opened:
            shown = brazil.show()
        opened.assert_called_once_with(shown.as_uri(), new=2)
        self.assertTrue(shown.is_file())


if __name__ == "__main__":
    unittest.main()
