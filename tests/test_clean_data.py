"""Every country's values look like clean, sensible data."""

from __future__ import annotations

import re
import unittest

from pyworldatlas import Atlas
from pyworldatlas._profiles import _feature_name, _sentence

AREA_NOTE = re.compile(r"\d[\d,.]*\s*(sq km|km|m)\b")


class FeatureNameTests(unittest.TestCase):
    def test_notes_are_removed_from_names(self) -> None:
        cases = {
            "Biwa-ko 688 sq km": "Biwa-ko",
            "Huron* – 23,597 sq km": "Huron",
            "Nettilling Lake - 5,542 sq km note": "Nettilling Lake",
            "Lake Chad (endorheic lake shared with Niger, Nigeria, and Chad) - 10,360-25,900 sq km note": "Lake Chad",
            "Lake Torrens (ephemeral)": "Lake Torrens (ephemeral)",
            "An Nīl (Nile)": "An Nīl (Nile)",
        }
        for text, name in cases.items():
            self.assertEqual(_feature_name(text), name)

    def test_sentences_are_not_names(self) -> None:
        self.assertIsNone(_feature_name("9.6 times saltier than the ocean"))
        self.assertIsNone(_feature_name("lake shore is 431 meters below sea level"))
        self.assertIsNone(_feature_name("the Tigris and Euphrates join to form the Shatt al Arab"))

    def test_sentence_case(self) -> None:
        self.assertEqual(_sentence("arid to semiarid"), "Arid to semiarid.")
        self.assertEqual(_sentence("Temperate."), "Temperate.")
        self.assertIsNone(_sentence(None))


class CleanCountryDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.atlas = Atlas()
        cls.countries = tuple(cls.atlas)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.atlas.close()

    def test_feature_names_hold_no_measurements(self) -> None:
        for country in self.countries:
            for feature in (*country.rivers, *country.lakes):
                self.assertIsNone(AREA_NOTE.search(feature.name), (country.alpha2, feature.name))
                self.assertFalse(feature.name.endswith("*"), (country.alpha2, feature.name))
                self.assertTrue(feature.name[0].isupper(), (country.alpha2, feature.name))
        self.assertEqual([lake.name for lake in self.atlas["Israel"].lakes], ["Dead Sea"])

    def test_areas_are_positive_or_missing(self) -> None:
        for country in self.countries:
            if country.area_km2 is not None:
                self.assertGreater(country.area_km2, 0, country.alpha2)
        self.assertIsNone(self.atlas["Vatican City"].area_km2)

    def test_subregion_never_repeats_region(self) -> None:
        for country in self.countries:
            if country.subregion is not None:
                self.assertNotEqual(country.subregion, country.region, country.alpha2)
        self.assertEqual(self.atlas["Jamaica"].subregion, "Caribbean")

    def test_climate_notes_are_sentences(self) -> None:
        for country in self.countries:
            summary = country.climate.summary
            if summary:
                self.assertTrue(summary[0].isupper() and summary.endswith("."), (country.alpha2, summary))

    def test_rankings_name_their_source(self) -> None:
        for metric in ("population", "area", "coastline", "border_count", "climate_zone_count"):
            self.assertTrue(self.atlas.rank(metric, limit=1)[0].source, metric)

    def test_nearby_places_skip_the_named_origin(self) -> None:
        names = {item.place.english_name for item in self.atlas.places_near("Tokyo", limit=5)}
        self.assertNotIn("Tokyo", names)
        named = {item.place.english_name for item in self.atlas.places_near((35.6895, 139.69171), limit=5)}
        self.assertIn("Tokyo", named)  # a plain point has no name to skip
        self.assertIn("Tokyo", {item.place.english_name for item in self.atlas.places_near("Tokyo", include_origin=True)})

    def test_antipodes_prefer_well_known_places(self) -> None:
        first = self.atlas.antipode("Madrid").nearest[0]
        self.assertGreater(first.place.fame, 0)
        self.assertLessEqual(first.distance, 500)


if __name__ == "__main__":
    unittest.main()
