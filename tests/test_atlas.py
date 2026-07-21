import dataclasses
import unittest

from pyworldatlas import Atlas, AtlasClosedError, CountryNotFoundError


class AtlasTests(unittest.TestCase):
    def setUp(self):
        self.atlas = Atlas()

    def tearDown(self):
        self.atlas.close()

    def test_lookup_by_codes_names_and_aliases(self):
        self.assertEqual(self.atlas.country("JP").name, "Japan")
        self.assertEqual(self.atlas.country("USA").name, "United States")
        self.assertEqual(self.atlas.country("840").alpha2, "US")
        self.assertEqual(self.atlas.country("Holy See").name, "Vatican City")
        self.assertIn(
            "reviewed-overrides",
            {source.id for source in self.atlas.country("US").sources},
        )

    def test_country_capital(self):
        tokyo = self.atlas.country("Japan").capital
        self.assertEqual(tokyo.name, "Tokyo")
        self.assertAlmostEqual(tokyo.coordinates.latitude, 35.6895, places=3)

    def test_collection_protocol(self):
        self.assertEqual(len(self.atlas), 248)
        self.assertIn("Japan", self.atlas)
        self.assertIn("Zimbabwe", self.atlas)
        self.assertNotIn("Atlantis", self.atlas)
        names = [country.name for country in self.atlas]
        self.assertEqual(names, sorted(names))
        for country in self.atlas:
            self.assertEqual(self.atlas.country(country.name).alpha2, country.alpha2)

    def test_search_and_filter(self):
        self.assertEqual(self.atlas.search_countries("vatican")[0].country.alpha2, "VA")
        self.assertIn("Japan", [c.name for c in self.atlas.countries(continent="Asia")])

    def test_models_are_immutable_and_serializable(self):
        country = self.atlas.country("DO")
        with self.assertRaises(dataclasses.FrozenInstanceError):
            country.name = "x"
        self.assertEqual(country.to_dict()["codes"]["alpha2"], "DO")

    def test_missing_and_closed_behavior(self):
        with self.assertRaises(CountryNotFoundError):
            self.atlas.country("Atlantis")
        self.atlas.close()
        with self.assertRaises(AtlasClosedError):
            len(self.atlas)
        with self.assertRaises(AtlasClosedError):
            self.atlas.country("DO")

    def test_dataset_versions(self):
        info = self.atlas.dataset_info()
        self.assertEqual((info.library_version, info.schema_version, info.dataset_version), ("0.1.0", 1, "2026.07.20"))
        self.assertEqual(info.country_count, 248)

    def test_missing_capital_is_explicit(self):
        self.assertIsNone(self.atlas.country("Antarctica").capital)


if __name__ == "__main__":
    unittest.main()
