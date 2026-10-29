"""World Bank statistics from the statistics pack."""

from __future__ import annotations

import re
import tempfile
import unittest
from xml.etree import ElementTree

from pack_fixtures import installed_packs, pack_files

from pyworldatlas import (Atlas, Indicator, MapSupportNotInstalledError, PackNotInstalledError,
                          StatisticSeries, StatisticValue, packs)
from pyworldatlas.maps import StatisticMap
from pyworldatlas.maps._world import COLORS, _class_edges, _short


class StatisticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.atlas = Atlas(data_dir=installed_packs())

    @classmethod
    def tearDownClass(cls) -> None:
        cls.atlas.close()

    def test_indicators(self) -> None:
        keys = [indicator.key for indicator in self.atlas.indicators()]
        self.assertIn("life_expectancy", keys)
        self.assertEqual(len(keys), 11)
        for indicator in self.atlas.indicators():
            self.assertIsInstance(indicator, Indicator)
            self.assertTrue(indicator.source.startswith("World Bank, World Development Indicators"))

    def test_time_series(self) -> None:
        japan = self.atlas.time_series("Japan", "life_expectancy")
        self.assertIsInstance(japan, StatisticSeries)
        self.assertEqual(japan.area, "JP")
        self.assertEqual(japan.first_year, 1960)
        self.assertGreater(japan.value(2020) or 0, 80)
        self.assertIsNone(japan.value(1900))
        self.assertTrue(japan.summary.startswith("Life expectancy at birth in Japan rose from"))
        line = japan.sparkline(width=10)
        self.assertLessEqual(len(line), 10)
        self.assertIn(line[0], "▁▂")  # life expectancy rose, so the chart climbs
        self.assertEqual(line[-1], "█")
        world = self.atlas.time_series("world", "population")
        self.assertEqual(world.area_name, "the world")
        self.assertGreater(world.latest.value, 7_000_000_000)
        with self.assertRaises(ValueError):
            japan.sparkline(width=0)

    def test_missing_values_stay_missing(self) -> None:
        kenya = self.atlas.time_series("Kenya", "internet_users")
        self.assertIn(None, kenya.values)
        self.assertTrue(all(value is not None for _, value in kenya.points))
        # Areas the World Bank does not cover have an empty series, not a guess.
        empty = self.atlas.time_series("Antarctica", "population")
        self.assertEqual(empty.values, ())
        self.assertIsNone(empty.latest)
        self.assertIn("No population values", empty.summary)

    def test_statistic_and_sorting(self) -> None:
        value = self.atlas.statistic("Brazil", "urban population", 1960)
        self.assertIsInstance(value, StatisticValue)
        self.assertEqual(value.year, 1960)
        self.assertTrue(str(value).endswith("% of people (1960)"))
        self.assertIsNone(self.atlas.statistic("Brazil", "urban_population", 1900))
        top = self.atlas.sort_by_statistic("forest_area", limit=5)
        values = [item.value for item in top]
        self.assertEqual(values, sorted(values, reverse=True))
        bottom = self.atlas.sort_by_statistic("forest_area", descending=False, limit=3)
        self.assertLessEqual(bottom[0].value, top[-1].value)
        self.assertNotIn("world", [item.area for item in self.atlas.sort_by_statistic("population", limit=None)])
        with self.assertRaises(ValueError):
            self.atlas.statistic("Japan", "happiness")
        with self.assertRaises(ValueError):
            self.atlas.sort_by_statistic("population", limit=0)

    def test_missing_pack_explains_how_to_install_it(self) -> None:
        with tempfile.TemporaryDirectory() as empty, Atlas(data_dir=empty) as atlas:
            with self.assertRaisesRegex(PackNotInstalledError, "pyworldatlas get statistics"):
                atlas.indicators()


class StatisticMapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.atlas = Atlas(data_dir=installed_packs())
        cls.map = cls.atlas.statistic_map("life expectancy")

    @classmethod
    def tearDownClass(cls) -> None:
        cls.atlas.close()

    def test_map_holds_every_country_and_only_published_values(self) -> None:
        chart = self.map
        self.assertIsInstance(chart, StatisticMap)
        self.assertEqual(len(chart.names), len(list(self.atlas)))
        self.assertEqual(chart.title, "Life expectancy at birth (years), latest year")
        japan = next(item for item in chart.values if item.area == "JP")
        self.assertEqual(japan, self.atlas.time_series("Japan", "life_expectancy").latest)
        self.assertNotIn("AQ", {item.area for item in chart.values})  # no value, so not drawn as one
        names = [dict(chart.names)[item.area] for item in chart.values]
        self.assertEqual(names, sorted(names, key=str.casefold))  # alphabetical, never ranked
        in_2000 = self.atlas.statistic_map("population", year=2000)
        self.assertTrue(all(item.year == 2000 for item in in_2000.values))
        self.assertIn("in 2000", in_2000.title)
        with self.assertRaises(TypeError):
            self.atlas.statistic_map("population", year="2000")  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            self.atlas.statistic_map("happiness")

    def test_svg_is_valid_accessible_and_offline(self) -> None:
        svg = self.map.to_svg()
        root = ElementTree.fromstring(svg)
        self.assertEqual(root.get("role"), "img")
        self.assertIn("aria-labelledby", root.attrib)
        self.assertNotIn("http://", svg.replace("http://www.w3.org/2000/svg", ""))
        self.assertNotIn("https://", svg)
        self.assertIn("Japan: 8", svg)  # hover title with value and year
        self.assertIn("Antarctica: no data", svg)
        self.assertIn("prefers-color-scheme:dark", svg)
        for color in COLORS:
            self.assertIn(color, svg)
        self.assertLess(len(svg), 400_000)
        # Every number in a path stays inside the drawing, so nothing spills over the legend.
        paths = " ".join(element.get("d", "") for element in root.iter("{http://www.w3.org/2000/svg}path"))
        numbers = [float(n) for n in re.findall(r"-?\d+(?:\.\d+)?", paths)]
        self.assertGreater(min(numbers), -1100)
        self.assertLess(max(numbers), 2100)

    def test_html_page_has_a_table_of_every_value(self) -> None:
        page = self.map.to_html()
        self.assertIn("<table>", page)
        self.assertEqual(page.count("<tr><th scope=row>"), len(self.map.values))
        self.assertIn("No data: ", page)
        with tempfile.TemporaryDirectory() as folder:
            html_file = self.map.write_html(f"{folder}/map.html")
            svg_file = self.map.write_svg(f"{folder}/map.svg")
            self.assertEqual(html_file.read_text(encoding="utf-8"), page)
            ElementTree.fromstring(svg_file.read_text(encoding="utf-8"))
        self.assertEqual(self.map._repr_html_(), self.map.to_svg())

    def test_classes_split_countries_evenly(self) -> None:
        edges = self.map.class_edges
        self.assertEqual(len(edges), 4)
        self.assertEqual(list(edges), sorted(set(edges)))
        self.assertEqual(_class_edges([1.0] * 10), ())  # identical values share one class
        self.assertEqual(_class_edges([float(n) for n in range(10)]), (2.0, 4.0, 6.0, 8.0))
        self.assertEqual(_short(1_463_865_525, 0), "1.5 billion")
        self.assertEqual(_short(466_000, 0), "466 thousand")
        self.assertEqual(_short(72.46, 1), "72.5")

    def test_missing_map_pack_explains_how_to_install_it(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            packs.add(pack_files() / "pyworldatlas-statistics.pack", folder)
            with Atlas(data_dir=folder) as atlas:
                with self.assertRaisesRegex(MapSupportNotInstalledError, "pyworldatlas get maps-lite"):
                    atlas.statistic_map("population")


if __name__ == "__main__":
    unittest.main()
