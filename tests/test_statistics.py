"""World Bank statistics from the statistics pack."""

from __future__ import annotations

import tempfile
import unittest

from pack_fixtures import installed_packs

from pyworldatlas import (Atlas, Indicator, PackNotInstalledError, StatisticSeries,
                          StatisticValue)


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


if __name__ == "__main__":
    unittest.main()
