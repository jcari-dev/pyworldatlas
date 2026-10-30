"""One naming style: the new names, the one rank, quiz, and filter, and the tour."""

from __future__ import annotations

import contextlib
import io
import re
import unittest

from pack_fixtures import installed_packs

from pyworldatlas import Atlas, CountryRanking, PlaceQuestion, QuizQuestion
from pyworldatlas.__main__ import main
from pyworldatlas._tour import TOUR


class NamingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.atlas = Atlas(data_dir=installed_packs())

    @classmethod
    def tearDownClass(cls) -> None:
        cls.atlas.close()

    def test_old_names_still_work(self) -> None:
        atlas = self.atlas
        self.assertEqual(atlas.nearest_capitals("Paris", limit=3), atlas.capitals_near("Paris", limit=3))
        self.assertEqual(atlas.nearest_cities("Lima", limit=3), atlas.cities_near("Lima", limit=3))
        self.assertEqual(atlas.world_heritage_sites_near("Rome", limit=3), atlas.heritage_sites_near("Rome", limit=3))
        self.assertEqual(atlas.lookup("Georgia"), atlas.find("Georgia"))
        self.assertEqual(atlas.place_quiz("higher", count=2), atlas.quiz("higher", count=2))
        self.assertEqual(atlas.countries_with_river("Danube"), atlas.countries(river="Danube"))
        self.assertEqual(atlas.countries_with_lake("Victoria"), atlas.countries(lake="Victoria"))
        self.assertEqual(atlas.countries_with_river(), atlas.countries(has_rivers=True))
        self.assertEqual(atlas.countries_in_climate_zone("Cfb"), atlas.countries(climate_zone="cfb"))
        self.assertEqual(atlas.rank_countries("area", limit=3), atlas.rank("area", limit=3))

    def test_one_country_filter(self) -> None:
        islands = self.atlas.countries(land_borders=False)
        self.assertIn(self.atlas["Japan"], islands)
        self.assertNotIn(self.atlas["France"], islands)
        self.assertEqual(islands, self.atlas.countries_with_no_land_borders())
        joined = self.atlas.countries(continent="Europe", river="Danube")
        self.assertIn(self.atlas["Austria"], joined)
        self.assertEqual(len(self.atlas.countries(land_borders=True)) + len(islands), len(self.atlas))
        with self.assertRaisesRegex(ValueError, "Choose from .*Cfb"):
            self.atlas.countries(climate_zone="Cfx")

    def test_rank_covers_statistics(self) -> None:
        rows = self.atlas.rank("life_expectancy", year=2020, limit=3)
        self.assertEqual(len(rows), 3)
        self.assertIsInstance(rows[0], CountryRanking)
        self.assertEqual([row.position for row in rows], [1, 2, 3])
        self.assertEqual(rows[0].year, 2020)
        self.assertTrue(rows[0].source and rows[0].source.startswith("World Bank"))
        self.assertRegex(str(rows[0]), r"^#1 .+: [\d.,]+ years \(2020\)$")
        same = self.atlas.sort_by_statistic("life_expectancy", year=2020, limit=3)
        self.assertEqual([row.country.alpha2 for row in rows], [item.area for item in same])
        africa = self.atlas.rank("population", year=2020, continent="Africa", limit=1)
        self.assertEqual(africa[0].country.name, "Nigeria")
        self.assertIsNone(self.atlas.rank("population", limit=1)[0].year)  # the GeoNames snapshot

    def test_rank_explains_unknown_metrics(self) -> None:
        with self.assertRaisesRegex(ValueError, "Did you mean area"):
            self.atlas.rank("aera")
        with self.assertRaisesRegex(ValueError, "life_expectancy"):
            self.atlas.rank("area", year=2020)  # profile metrics have no years

    def test_one_quiz(self) -> None:
        places = self.atlas.quiz("higher", count=2)
        self.assertTrue(all(isinstance(item, PlaceQuestion) for item in places))
        countries = self.atlas.quiz("capitals", count=2)
        self.assertTrue(all(isinstance(item, QuizQuestion) for item in countries))
        with self.assertRaisesRegex(ValueError, "continent and region do not apply"):
            self.atlas.quiz("higher", continent="Asia")
        with self.assertRaisesRegex(ValueError, "Did you mean higher"):
            self.atlas.quiz("highr")

    def test_every_tour_line_runs(self) -> None:
        calls = [
            re.split(r"\s{2,}", line.strip())[0].removesuffix(".show()")
            for line in TOUR.splitlines()
            if line.strip().startswith(("atlas.", "atlas["))
        ]
        self.assertGreaterEqual(len(calls), 12)
        for call in calls:
            with self.subTest(call=call):
                self.assertIsNotNone(eval(call, {"atlas": self.atlas}))

    def test_help_and_tour_print_the_same_text(self) -> None:
        printed = io.StringIO()
        with contextlib.redirect_stdout(printed):
            self.atlas.help()
        self.assertEqual(printed.getvalue().strip(), TOUR)
        printed = io.StringIO()
        with contextlib.redirect_stdout(printed):
            self.assertEqual(main(["tour"]), 0)
        self.assertEqual(printed.getvalue().strip(), TOUR)


if __name__ == "__main__":
    unittest.main()
