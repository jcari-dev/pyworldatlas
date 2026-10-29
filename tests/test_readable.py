"""Results print as one clear line and keep tidy, consistent values."""

from __future__ import annotations

from datetime import date, datetime, timezone
import copy
import json
import pickle
import unittest

from pack_fixtures import installed_packs

import pyworldatlas
from pyworldatlas import Atlas, Coordinate, Distance, SunTimes
from pyworldatlas.models._display import details_shown
from pyworldatlas.models.units import SummaryText


class DistanceTests(unittest.TestCase):
    def test_distance_is_a_number_that_prints_with_its_unit(self) -> None:
        far = Distance(9712.518, "km")
        self.assertEqual(str(far), "9,713 km")
        self.assertEqual(repr(far), "Distance(9712.5, 'km')")
        self.assertEqual(far + 1, 9713.518)
        self.assertEqual(str(Distance(0.06, "mi")), "0.1 mi")
        self.assertEqual(json.dumps({"d": far}), '{"d": 9712.518}')
        for clone in (copy.copy(far), pickle.loads(pickle.dumps(far))):
            self.assertEqual((clone, clone.unit), (far, "km"))
        with self.assertRaises(ValueError):
            Distance(1, "furlong")


class SummaryTextTests(unittest.TestCase):
    def test_summary_works_as_text_and_as_a_call(self) -> None:
        text = SummaryText("Japan", lambda **options: f"Japan {options}")
        self.assertEqual(text, "Japan")
        self.assertEqual(text(), "Japan")
        self.assertEqual(text(local_language="ja"), "Japan {'local_language': 'ja'}")


class ReadableResultTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.atlas = Atlas(data_dir=installed_packs())

    @classmethod
    def tearDownClass(cls) -> None:
        cls.atlas.close()

    def test_country_summary_is_a_property(self) -> None:
        japan = self.atlas["Japan"]
        self.assertTrue(japan.summary.startswith("🇯🇵 Japan"))
        self.assertEqual(japan.summary(), japan.summary)
        self.assertIn("Capital: Tokyo", japan.summary(local_language="ja"))

    def test_results_print_as_one_clear_line(self) -> None:
        atlas = self.atlas
        self.assertEqual(str(atlas.rank("area", limit=1)[0]), "#1 Russia: 17,098,242 km²")
        self.assertEqual(repr(atlas.rank("area", limit=1)[0]), "CountryRanking('#1 Russia: 17,098,242 km²')")
        self.assertEqual(str(atlas.nearest_capitals("Tokyo", limit=1)[0]), "Seoul, South Korea · 1,153 km")
        self.assertRegex(str(atlas.nearest_cities("Tokyo", limit=1)[0]), r"^\S.* \(JP\) · [\d.,]+ km$")
        self.assertRegex(str(atlas.places_near("Tokyo", limit=1)[0]), r" · [\d.,]+ km$")
        self.assertRegex(str(atlas.world_heritage_sites_near("Rome", limit=1)[0]), r" · [\d.,]+ km$")
        self.assertEqual(
            str(atlas.border_path("France", "Spain")), "France → Spain (1 border crossing)"
        )
        self.assertEqual(repr(atlas.place("Mount Fuji")), "Place(english_name='Mount Fuji', kind='volcano', country_code='JP')")
        self.assertEqual(repr(atlas.city("Osaka")), "City(name='Osaka', country_code='JP')")
        self.assertEqual(repr(atlas.airport("HND")), "Airport(iata_code='HND', name='Tokyo Haneda International Airport')")
        question = atlas.quiz("capitals", count=1)[0]
        self.assertIn("1) ", str(question))
        self.assertTrue(repr(question).startswith("QuizQuestion(topic='capitals'"))
        self.assertEqual(str(atlas.flashcards("capitals", count=1)[0]).split("? ")[1], atlas.flashcards("capitals", count=1)[0].answer)
        self.assertTrue(repr(atlas.antipode("Madrid")).startswith("Antipode('40.42° S"))
        self.assertEqual(repr(atlas.statistic("Japan", "population", 2000)), "StatisticValue(indicator='population', area='JP', year=2000, value=126843000)")
        self.assertEqual(repr(atlas.time_series("Japan", "population")).split("years=")[0], "StatisticSeries(indicator='population', area='JP', ")
        self.assertEqual(repr(atlas.indicators()[0]), "Indicator(key='birth_rate', unit='per 1,000 people a year')")

    def test_distances_are_distance_values(self) -> None:
        between = self.atlas.distance_between("Tokyo", "Paris", unit="mi")
        self.assertIsInstance(between, Distance)
        self.assertEqual(between.unit, "mi")
        nearby = self.atlas.nearest_capitals("Tokyo", limit=1, unit="nmi")[0]
        self.assertIsInstance(nearby.distance, Distance)
        self.assertEqual(nearby.distance.unit, "nmi")
        self.assertIsInstance(nearby.to_dict()["distance"], float)

    def test_numbers_are_tidy(self) -> None:
        japan = self.atlas["Japan"]
        self.assertIsInstance(japan.area_km2, int)
        self.assertIsInstance(japan.highest_point.elevation_m, int)
        self.assertEqual(japan.geography.area.water_percent, round(japan.geography.area.water_percent, 2))
        self.assertIn('"total_km2": 377915,', japan.to_json())

    def test_country_codes_have_one_name(self) -> None:
        ranking = self.atlas.rank("area", limit=1)[0]
        self.assertEqual(ranking.country.country_code, "RU")
        self.assertEqual(self.atlas.statistic("Japan", "population").country_code, "JP")
        self.assertIsNone(self.atlas.time_series("world", "population").country_code)

    def test_sun_times_print_and_use_local_time_when_known(self) -> None:
        paris = self.atlas.sun("Paris", date(2026, 6, 21))
        self.assertEqual(paris.timezone_id, "Europe/Paris")
        self.assertEqual(str(paris), paris.summary)
        self.assertTrue(repr(paris).startswith("SunTimes(2026-06-21, sunrise='03:"))
        self.assertEqual(self.atlas.sun("France", date(2026, 6, 21)).timezone_id, "Europe/Paris")
        self.assertIsNone(self.atlas.sun((0.0, 0.0), date(2026, 6, 21)).timezone_id)
        if paris.local_sunrise is not None:  # the computer has time zone data
            self.assertEqual(paris.local_sunrise.hour, 5)
            self.assertIn("local time", paris.summary)
        else:
            self.assertIn("UTC", paris.summary)

    def test_every_model_reads_well(self) -> None:
        japan = self.atlas["Japan"]
        expected = {
            japan.geography.area: "Area('377,915 km², 3.55% water')",
            japan.highest_point: "ElevationPoint('Mount Fuji, 3,776 m')",
            japan.climate.koppen_geiger_zones[0]: "ClimateZone('Cfa · Temperate, no dry season, hot summer · 57.9%')",
            japan.codes: "CountryCodes(alpha2='JP', alpha3='JPN', numeric='392')",
            japan.currency: "Currency('Japanese Yen (JPY, ¥)')",
            japan.travel: "TravelBasics('Plugs A, B · 100 V, 50/60 Hz · drives on the left')",
            japan.anthem: "NationalAnthem('Kimigayo')",
            japan.discovery_card(): "CountryDiscoveryCard('Japan')",
        }
        for value, text in expected.items():
            self.assertEqual(repr(value), text)
        for value in (japan.geography, japan.physical, japan.climate, *japan.languages, *japan.timezones,
                      *japan.names, *japan.sources, japan.demonym, self.atlas.dataset_info(),
                      self.atlas.world_map("population"), self.atlas.map("Japan")):
            self.assertLess(len(repr(value)), 160, type(value).__name__)
            self.assertTrue(str(value))

    def test_show_details_prints_every_field(self) -> None:
        ranking = self.atlas.rank("area", limit=1)[0]
        self.assertFalse(details_shown())
        with pyworldatlas.show_details():
            self.assertTrue(details_shown())
            self.assertIn("alpha3='RUS'", repr(ranking))
            self.assertEqual(repr(Distance(1.23456, "km")), "Distance(1.23456, 'km')")
            with pyworldatlas.show_details(False):
                self.assertEqual(repr(ranking), "CountryRanking('#1 Russia: 17,098,242 km²')")
            self.assertIn("alpha3='RUS'", repr(ranking))
        self.assertEqual(repr(ranking), "CountryRanking('#1 Russia: 17,098,242 km²')")
        pyworldatlas.show_details()
        try:
            self.assertTrue(details_shown())
        finally:
            pyworldatlas.show_details(False)

    def test_unknown_time_zone_falls_back_to_utc(self) -> None:
        noon = datetime(2026, 6, 21, 12, tzinfo=timezone.utc)
        times = SunTimes(Coordinate(0, 0), date(2026, 6, 21), noon, noon, noon, 12.0, 60.0, "Not/AZone")
        self.assertIsNone(times.local_sunrise)
        self.assertIn("UTC", times.summary)


if __name__ == "__main__":
    unittest.main()
