import dataclasses
import math
import unittest

from pyworldatlas import (AmbiguousPlaceError, Atlas, AtlasClosedError,
                          CapitalNotFoundError, Coordinate, CountryNotFoundError,
                          PlaceNotFoundError)


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

    def test_rich_country_profile(self):
        japan = self.atlas.country("Japan")
        self.assertEqual(japan.population, 126_529_100)
        self.assertEqual((japan.currency.code, japan.currency.name), ("JPY", "Yen"))
        self.assertEqual(japan.calling_codes, ("+81",))
        self.assertEqual(japan.top_level_domain, ".jp")
        self.assertEqual(tuple(language.code for language in japan.languages), ("ja",))
        self.assertIn("Asia/Tokyo", japan.observed_timezones)
        self.assertEqual(japan.capital_coordinates, japan.capital.coordinates)

    def test_coordinate_calculations(self):
        london = Coordinate(51.5074, -0.1278)
        paris = Coordinate(48.8566, 2.3522)
        self.assertAlmostEqual(london.distance_to(paris), 343.6, delta=0.5)
        self.assertAlmostEqual(london.distance_to(paris, unit="mi"), 213.5, delta=0.5)
        self.assertAlmostEqual(london.distance_to(paris, unit="nmi"), 185.5, delta=0.5)
        self.assertAlmostEqual(london.bearing_to(paris), 148.1, delta=0.5)
        midpoint = london.midpoint_to(paris)
        self.assertAlmostEqual(midpoint.latitude, 50.1886, delta=0.01)
        self.assertAlmostEqual(midpoint.longitude, 1.1466, delta=0.01)
        with self.assertRaises(ValueError):
            Coordinate(91, 0)
        with self.assertRaises(ValueError):
            Coordinate(math.nan, 0)
        with self.assertRaises(ValueError):
            Coordinate(0, math.inf)
        with self.assertRaises(ValueError):
            london.distance_to(paris, unit="lightyears")

    def test_undefined_geodesic_operations(self):
        point = Coordinate(0, 0)
        antipode = Coordinate(0, 180)
        north_pole = Coordinate(90, 0)
        same_north_pole = Coordinate(90, 90)
        south_pole = Coordinate(-90, 20)
        with self.assertRaisesRegex(ValueError, "coincident"):
            point.bearing_to(point)
        with self.assertRaisesRegex(ValueError, "antipodal"):
            point.bearing_to(antipode)
        with self.assertRaisesRegex(ValueError, "antipodal"):
            point.midpoint_to(antipode)
        with self.assertRaisesRegex(ValueError, "coincident"):
            north_pole.bearing_to(same_north_pole)
        with self.assertRaisesRegex(ValueError, "antipodal"):
            north_pole.bearing_to(south_pole)
        with self.assertRaisesRegex(ValueError, "antipodal"):
            north_pole.midpoint_to(south_pole)

    def test_city_lookup_and_distance_between_places(self):
        tokyo = self.atlas.city("Tokyo", country="Japan")
        paris = self.atlas.city("Paris", country="France")
        self.assertEqual(tokyo.coordinates, self.atlas.coordinates("Tokyo", country="JP"))
        self.assertAlmostEqual(self.atlas.distance_between(tokyo, paris), 9712, delta=30)
        self.assertAlmostEqual(
            self.atlas.distance_between("Tokyo", "Paris", first_country="JP", second_country="FR"),
            tokyo.coordinates.distance_to(paris.coordinates),
            places=6,
        )
        self.assertAlmostEqual(self.atlas.distance_between((51.5074, -0.1278), (48.8566, 2.3522)), 343.6, delta=0.5)
        with self.assertRaises(AmbiguousPlaceError):
            self.atlas.city("London")

    def test_country_and_capital_distance_inputs(self):
        japan = self.atlas.country("Japan")
        france = self.atlas.country("France")
        expected = japan.capital.coordinates.distance_to(france.capital.coordinates)
        self.assertAlmostEqual(self.atlas.distance_between(japan, france), expected)
        self.assertAlmostEqual(
            self.atlas.distance_between(japan.capital, france.capital), expected
        )
        with self.assertRaises(PlaceNotFoundError):
            self.atlas.distance_between("Japan", "France")
        with self.assertRaises(CapitalNotFoundError):
            self.atlas.distance_between(self.atlas.country("Antarctica"), france)

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
        self.assertEqual((info.library_version, info.schema_version, info.dataset_version), ("0.2.0", 2, "2026.07.20.1"))
        self.assertEqual(info.country_count, 248)

    def test_official_local_names_pilot(self):
        brazil = self.atlas.country("Brazil")
        self.assertEqual(brazil.name_in("pt"), "Brasil")
        self.assertEqual(brazil.official_name_in("pt"), "República Federativa do Brasil")
        self.assertIsNone(brazil.name_in("en"))
        self.assertIsNone(brazil.romanized_name_in("pt"))
        self.assertEqual(brazil.local_names[0].script_code, "Latn")
        self.assertEqual(brazil.local_names[0].source.id, "ungegn-country-names-2017")

        switzerland = self.atlas.country("Switzerland")
        self.assertEqual(
            {name.language_code: name.short_name for name in switzerland.local_names},
            {"de": "Schweiz", "fr": "Suisse", "it": "Svizzera", "rm": "Svizra"},
        )
        self.assertEqual(switzerland.official_name_in("rm"), "Confederaziun svizra")

    def test_local_names_survive_close_and_serialize_as_unicode(self):
        brazil = self.atlas.country("Brazil")
        self.atlas.close()
        self.assertEqual(brazil.official_name_in("pt"), "República Federativa do Brasil")
        self.assertIn("República Federativa do Brasil", brazil.to_json())

    def test_collection_loads_local_names_once(self):
        statements = []
        self.atlas._db.connection.set_trace_callback(statements.append)
        countries = self.atlas.countries()
        self.assertEqual(len(countries), 248)
        local_name_queries = [sql for sql in statements if "FROM country_local_name" in sql]
        self.assertEqual(len(local_name_queries), 1)

    def test_missing_capital_is_explicit(self):
        self.assertIsNone(self.atlas.country("Antarctica").capital)


if __name__ == "__main__":
    unittest.main()
