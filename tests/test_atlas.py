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
        self.assertEqual(japan.formal_name, "Japan")
        self.assertFalse(japan.has_distinct_formal_name)
        self.assertEqual(japan.population, 126_529_100)
        self.assertEqual(
            (japan.currency.code, japan.currency.name, japan.currency.symbol),
            ("JPY", "Japanese Yen", "¥"),
        )
        self.assertEqual(japan.currency.minor_unit_digits, 0)
        self.assertEqual(japan.calling_codes, ("+81",))
        self.assertEqual(japan.top_level_domain, ".jp")
        self.assertEqual(tuple(language.code for language in japan.languages), ("ja",))
        self.assertEqual(
            (japan.languages[0].name, japan.languages[0].script_code),
            ("Japanese", "Jpan"),
        )
        self.assertIn("Asia/Tokyo", japan.observed_timezones)
        self.assertEqual(japan.timezone_ids, ("Asia/Tokyo",))
        self.assertEqual(japan.postal_code.format, "###-####")
        self.assertEqual(japan.capital_coordinates, japan.capital.coordinates)

    def test_discovery_properties_and_card(self):
        japan = self.atlas.country("Japan")
        self.assertEqual((japan.flag, japan.flag_emoji), ("🇯🇵", "🇯🇵"))
        self.assertEqual(japan.language_codes, ("ja",))
        self.assertEqual(japan.currency_code, "JPY")
        self.assertEqual(japan.major_city_count, len(japan.major_cities))
        self.assertAlmostEqual(japan.population_density, 334.808, places=3)

        card = japan.discovery_card()
        self.assertEqual(card.country, japan.reference())
        self.assertEqual(card.country.numeric, "392")
        self.assertEqual(card.capital, "Tokyo")
        self.assertEqual(card.flag_emoji, "🇯🇵")
        self.assertEqual(card.formal_name, "Japan")
        self.assertEqual(card.language_codes, ("ja",))
        self.assertEqual(card.anthem_title, "Kimigayo")
        self.assertEqual(card.demonym, "Japanese (singular and plural)")
        self.assertEqual(card.timezone_ids, ("Asia/Tokyo",))
        self.assertEqual(card.coastline_km, 29_751)
        self.assertEqual(card.highest_point.name, "Mount Fuji")
        self.assertIn("Cfa", card.climate_zone_codes)
        self.assertEqual(card.to_dict()["country"]["alpha2"], "JP")
        self.atlas.close()
        self.assertIn('"flag_emoji": "🇯🇵"', card.to_json())

    def test_deterministic_country_sampling(self):
        sample = self.atlas.sample_countries(count=5, seed=42)
        self.assertEqual(
            [country.codes.numeric for country in sample],
            ["414", "044", "108", "784", "788"],
        )
        self.assertEqual(sample, self.atlas.sample_countries(count=5, seed=42))
        self.assertEqual(
            [country.alpha2 for country in self.atlas.sample_countries(
                count=4, continent="Africa", seed="class"
            )],
            ["BJ", "MW", "CV", "DZ"],
        )
        with self.assertRaisesRegex(ValueError, "positive integer"):
            self.atlas.sample_countries(count=0)
        with self.assertRaisesRegex(ValueError, "positive integer"):
            self.atlas.sample_countries(count=True)
        with self.assertRaisesRegex(ValueError, "exceeds"):
            self.atlas.sample_countries(count=999)

    def test_structured_flashcards(self):
        cards = self.atlas.flashcards(topic="capitals", count=3, seed=42)
        self.assertEqual(
            [(card.country.alpha2, card.answer) for card in cards],
            [("KW", "Kuwait City"), ("BS", "Nassau"), ("BI", "Gitega")],
        )
        self.assertEqual(cards[0].to_dict()["topic"], "capitals")
        topics = (
            "alpha_2_codes", "alpha_3_codes", "areas", "border_counts", "calling_codes",
            "climate_zones", "coastlines", "continents", "countries_from_capitals",
            "currencies", "flags", "highest_points", "language_codes", "lakes",
            "local_names", "m49_codes", "neighbors", "population_density",
            "populations", "regions", "rivers", "top_level_domains",
        )
        for topic in topics:
            card = self.atlas.flashcards(topic=topic, count=1, seed="lesson")[0]
            self.assertEqual(card.topic, topic)
            self.assertTrue(card.prompt)
            self.assertTrue(card.answer)
        local_names = self.atlas.flashcards(topic="local_names", count=2, seed=42)
        self.assertEqual(
            [(card.country.alpha2, card.answer) for card in local_names],
            [("KW", "الكويت"), ("BS", "Bahamas")],
        )
        neighbor_cards = self.atlas.flashcards(topic="neighbors", count=3, seed=42)
        self.assertEqual(
            [(card.country.alpha2, card.answer) for card in neighbor_cards],
            [
                ("KW", "Iraq, Saudi Arabia"),
                ("BI", "Democratic Republic of the Congo, Rwanda, Tanzania"),
                ("AE", "Oman, Saudi Arabia"),
            ],
        )
        count_cards = self.atlas.flashcards(topic="border_counts", count=3, seed=42)
        self.assertEqual(
            [(card.country.alpha2, card.answer) for card in count_cards],
            [("KW", "2"), ("BS", "0"), ("BI", "3")],
        )
        with self.assertRaisesRegex(ValueError, "unsupported flashcard topic"):
            self.atlas.flashcards(topic="trivia", count=1)
        with self.assertRaisesRegex(ValueError, "exceeds"):
            self.atlas.flashcards(topic="local_names", count=249)

    def test_deterministic_multiple_choice_quiz(self):
        self.assertIn("local_names", self.atlas.learning_topics())
        questions = self.atlas.quiz(
            topic="local_names", count=2, choices=4, seed=42
        )
        self.assertEqual(
            tuple(question.country.alpha2 for question in questions),
            ("KW", "BS"),
        )
        self.assertEqual(
            questions,
            self.atlas.quiz(topic="local_names", count=2, choices=4, seed=42),
        )
        for question in questions:
            self.assertEqual(len(question.choices), 4)
            self.assertIn(question.answer, question.choices)
            self.assertTrue(question.is_correct(question.answer))
            self.assertTrue(question.is_correct(question.answer_number))
            self.assertFalse(question.is_correct(99))
            self.assertEqual(question.to_dict()["answer"], question.answer)
            self.assertIn('"choices":', question.to_json())
        with self.assertRaisesRegex(ValueError, "distinct answers"):
            self.atlas.quiz(
                topic="continents",
                count=1,
                choices=4,
                continent="Asia",
            )
        with self.assertRaisesRegex(ValueError, "between 2 and 6"):
            self.atlas.quiz(topic="capitals", count=1, choices=1)

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

    def test_coordinate_display_and_compass_helpers(self):
        tokyo = Coordinate(35.6895, 139.6917)
        london = Coordinate(51.5074, -0.1278)
        paris = Coordinate(48.8566, 2.3522)

        self.assertEqual(tokyo.hemispheres, ("N", "E"))
        self.assertEqual(tokyo.format(), "35.6895° N, 139.6917° E")
        self.assertEqual(
            tokyo.dms(),
            "35° 41′ 22.2″ N, 139° 41′ 30.1″ E",
        )
        self.assertEqual(london.compass_direction_to(paris), "SSE")
        self.assertEqual(london.compass_direction_to(paris, points=8), "SE")
        with self.assertRaisesRegex(ValueError, "between 0 and 8"):
            tokyo.format(precision=9)
        with self.assertRaisesRegex(ValueError, "4, 8, or 16"):
            london.compass_direction_to(paris, points=12)

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

    def test_city_search_and_nearby_discovery(self):
        matches = self.atlas.search_cities("santo", country="DO", limit=3)
        self.assertEqual(
            tuple(city.name for city in matches),
            ("Santo Domingo", "Santo Domingo Oeste", "Santo Domingo Este"),
        )
        self.assertEqual(str(matches[0]), "Santo Domingo (DO)")
        self.assertEqual(matches[0].label, "Santo Domingo (DO)")
        self.assertEqual(self.atlas.search_cities("not-a-real-city"), ())

        nearby = self.atlas.nearest_cities(
            "Santo Domingo",
            origin_country="DO",
            within_country="DO",
            limit=3,
        )
        self.assertEqual(
            tuple(result.city.name for result in nearby),
            ("Santo Domingo Este", "Bella Vista", "Santo Domingo Oeste"),
        )
        self.assertTrue(all(result.country.alpha2 == "DO" for result in nearby))
        self.assertTrue(nearby[0].distance < nearby[-1].distance)
        self.assertEqual(nearby[0].to_dict()["city"]["country_code"], "DO")
        self.assertIn('"distance":', nearby[0].to_json())
        with self.assertRaisesRegex(ValueError, "positive integer"):
            self.atlas.search_cities("santo", limit=0)

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

    def test_readable_country_summary(self):
        brazil = self.atlas.country("Brazil")
        summary = brazil.summary()
        self.assertTrue(summary.startswith("🇧🇷 Brazil · Brasil"))
        self.assertIn("Capital: Brasília", summary)
        self.assertIn("Anthem title: Hino Nacional Brasileiro", summary)
        self.assertIn("Motto: Ordem e Progresso · Order and Progress", summary)
        self.assertIn("Highest point: Pico da Neblina (2,994 m)", summary)
        self.assertIn("Source-listed rivers: Amazon", summary)

        japan = self.atlas.country("Japan")
        self.assertTrue(japan.summary(local_language="ja").startswith("🇯🇵 Japan · 日本"))
        heading = japan.summary(local_language="es").splitlines()[0]
        self.assertNotIn(" · 日本", heading)

    def test_search_and_filter(self):
        self.assertEqual(self.atlas.search_countries("vatican")[0].country.alpha2, "VA")
        self.assertEqual(self.atlas.search_countries("not-a-country"), ())
        with self.assertRaisesRegex(TypeError, "query must be a string"):
            self.atlas.search_countries(None)
        with self.assertRaisesRegex(ValueError, "at least one"):
            self.atlas.search_countries("  ")
        with self.assertRaisesRegex(ValueError, "positive integer"):
            self.atlas.search_countries("japan", limit=0)
        self.assertIn("Japan", [c.name for c in self.atlas.countries(continent="Asia")])
        self.assertEqual(
            tuple(country.alpha2 for country in self.atlas.countries(currency_code="jpy")),
            ("JP",),
        )
        self.assertIn("JP", {country.alpha2 for country in self.atlas.countries(language_code="ja")})
        self.assertIn("JP", {country.alpha2 for country in self.atlas.countries(script_code="Jpan")})
        self.assertIn(
            "JP",
            {country.alpha2 for country in self.atlas.countries(timezone_id="Asia/Tokyo")},
        )

    def test_reference_facts_are_typed_and_sourced(self):
        japan = self.atlas.country("Japan")
        self.assertEqual(
            (japan.anthem.title, japan.anthem.english_title),
            ("Kimigayo", "His Majesty’s Reign"),
        )
        self.assertEqual(japan.anthem.source.id, "cia-world-factbook-2025")
        self.assertEqual(japan.demonym.adjective, "Japanese")

        brazil = self.atlas.country("Brazil")
        self.assertEqual(
            (brazil.motto.text, brazil.motto.english_text, brazil.motto.language_code),
            ("Ordem e Progresso", "Order and Progress", "pt"),
        )
        self.assertEqual(brazil.motto.source.id, "wikidata-national-mottos-2026-07-22")
        self.assertIn("reviewed-national-mottos", {source.id for source in brazil.sources})
        self.assertIsNone(self.atlas.country("China").motto)

        countries = self.atlas.countries()
        self.assertEqual(sum(country.anthem is not None for country in countries), 234)
        self.assertEqual(sum(country.motto is not None for country in countries), 32)
        self.assertEqual(sum(country.demonym is not None for country in countries), 227)

    def test_rankings_and_nearest_capitals(self):
        population = self.atlas.rank_countries("population", limit=3)
        self.assertEqual(
            tuple(result.country.alpha2 for result in population),
            ("CN", "IN", "US"),
        )
        self.assertEqual((population[0].position, population[0].unit), (1, "people"))
        self.assertIn('"metric": "population"', population[0].to_json())

        density = self.atlas.rank("density", limit=3, descending=False)
        self.assertEqual(tuple(result.position for result in density), (1, 2, 3))
        self.assertLessEqual(density[0].value, density[1].value)

        nearest = self.atlas.nearest_capitals("Tokyo", country="JP", limit=3)
        self.assertEqual(
            tuple(result.country.alpha2 for result in nearest),
            ("KR", "KP", "CN"),
        )
        self.assertGreater(nearest[0].distance, 0)
        self.assertEqual(nearest[0].to_dict()["capital"]["name"], "Seoul")
        self.assertIn('"distance":', nearest[0].to_json())
        with self.assertRaisesRegex(ValueError, "metric"):
            self.atlas.rank_countries("happiness")
        with self.assertRaisesRegex(ValueError, "positive integer"):
            self.atlas.rank_countries("population", limit=True)

    def test_physical_geography_profiles_and_discovery(self):
        brazil = self.atlas.country("Brazil")
        self.assertEqual(
            (brazil.land_area_km2, brazil.water_area_km2, brazil.coastline_km),
            (8_358_140, 157_630, 7_491),
        )
        self.assertAlmostEqual(brazil.water_percent, 1.851, places=3)
        self.assertEqual(
            (brazil.highest_point.name, brazil.highest_point.elevation_m),
            ("Pico da Neblina", 2_994),
        )
        self.assertEqual(brazil.rivers[0].name, "Amazon")
        self.assertEqual(brazil.rivers[0].length_km, 6_400)
        self.assertEqual(brazil.lakes[0].name, "Lagoa dos Patos")
        self.assertEqual(brazil.climate.dominant_zone.code, "Aw")
        self.assertEqual(brazil.climate.reference_period, "1991-2020")
        self.assertEqual(brazil.climate.summary_source.id, "cia-world-factbook-2025")
        self.assertEqual(
            brazil.climate.classification_source.id,
            "koppen-geiger-1991-2020",
        )

        switzerland = self.atlas.country("Switzerland")
        self.assertFalse(switzerland.is_coastal)
        self.assertTrue(switzerland.is_landlocked)
        self.assertEqual(switzerland.lowest_point.name, "Lake Maggiore")
        self.assertIn("ET", switzerland.climate.zone_codes)

        self.assertIn(
            "Brazil",
            {country.name for country in self.atlas.countries_with_river("Amazon")},
        )
        self.assertEqual(
            {country.alpha2 for country in self.atlas.countries_with_lake("Geneva")},
            {"CH", "FR"},
        )
        self.assertIn(
            "CH",
            {country.alpha2 for country in self.atlas.countries_in_climate_zone("ET")},
        )
        self.assertEqual(len(self.atlas.countries(coastal=True)), 193)
        self.assertEqual(len(self.atlas.countries(coastal=False)), 45)
        self.assertEqual(len(self.atlas.countries(has_rivers=True)), 80)
        self.assertEqual(len(self.atlas.countries(has_lakes=True)), 69)
        self.assertEqual(
            self.atlas.rank("coastline", limit=1)[0].country.alpha2,
            "CA",
        )
        self.assertEqual(
            self.atlas.rank("mean_elevation", limit=1)[0].country.alpha2,
            "TJ",
        )
        with self.assertRaisesRegex(ValueError, "Köppen-Geiger"):
            self.atlas.countries_in_climate_zone("H")
        with self.assertRaisesRegex(TypeError, "coastal"):
            self.atlas.countries(coastal="yes")

    def test_reviewed_neighbors_and_shared_neighbors(self):
        self.assertEqual(
            tuple(country.name for country in self.atlas.neighbors("France")),
            ("Andorra", "Belgium", "Germany", "Italy", "Luxembourg", "Monaco", "Spain", "Switzerland"),
        )
        self.assertTrue(self.atlas.shares_border("Spain", "Morocco"))
        self.assertTrue(self.atlas.shares_border("China", "Hong Kong"))
        self.assertFalse(self.atlas.shares_border("United States", "Cuba"))
        self.assertFalse(self.atlas.shares_border("France", "France"))
        self.assertEqual(
            tuple(country.name for country in self.atlas.shared_neighbors("Germany", "Italy")),
            ("Austria", "France", "Switzerland"),
        )

    def test_shortest_border_paths_and_components(self):
        path = self.atlas.border_path("Portugal", "China")
        self.assertIsNotNone(path)
        self.assertEqual(path.origin.alpha2, "PT")
        self.assertEqual(path.destination.alpha2, "CN")
        self.assertEqual(path.crossings, len(path.countries) - 1)
        self.assertEqual(path.names, tuple(country.name for country in path.countries))
        self.assertEqual(path.alpha2_codes, tuple(country.alpha2 for country in path.countries))
        self.assertEqual(path.crossings, self.atlas.border_crossings("Portugal", "China"))
        self.assertTrue(self.atlas.has_land_route("Portugal", "China"))
        for first, second in zip(path.countries, path.countries[1:]):
            self.assertTrue(self.atlas.shares_border(first.alpha2, second.alpha2))

        same = self.atlas.border_path("Japan", "JP")
        self.assertEqual(same.crossings, 0)
        self.assertEqual(tuple(country.alpha2 for country in same.countries), ("JP",))
        self.assertIsNone(self.atlas.border_path("Japan", "China"))
        self.assertIsNone(self.atlas.border_crossings("Japan", "China"))
        self.assertFalse(self.atlas.has_land_route("Japan", "China"))
        self.assertTrue(self.atlas.has_land_route("Japan", "JP"))
        self.assertEqual(self.atlas.countries_reachable_by_land("Japan"), ())
        reachable = {country.name for country in self.atlas.countries_reachable_by_land("Portugal")}
        self.assertIn("China", reachable)

    def test_borderless_entities_and_graph_symmetry(self):
        borderless = self.atlas.countries_with_no_land_borders()
        borderless_codes = {country.alpha2 for country in borderless}
        self.assertEqual(len(borderless), 85)
        self.assertIn("JP", borderless_codes)
        self.assertIn("CU", borderless_codes)
        self.assertNotIn("BR", borderless_codes)
        for country in self.atlas:
            for neighbor in self.atlas.neighbors(country.alpha2):
                self.assertTrue(self.atlas.shares_border(neighbor.alpha2, country.alpha2))

    def test_models_are_immutable_and_serializable(self):
        country = self.atlas.country("DO")
        with self.assertRaises(dataclasses.FrozenInstanceError):
            country.name = "x"
        self.assertEqual(country.to_dict()["codes"]["alpha2"], "DO")
        path = self.atlas.border_path("Portugal", "Spain")
        with self.assertRaises(dataclasses.FrozenInstanceError):
            path.crossings = 9
        self.assertEqual(path.to_dict()["countries"][0]["alpha2"], "PT")
        self.assertIn('"crossings": 1', path.to_json())

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
        self.assertEqual((info.library_version, info.schema_version, info.dataset_version), ("0.9.3", 7, "2026.07.22.7"))
        self.assertEqual(info.country_count, 248)

    def test_english_formal_names_are_sourced_and_discoverable(self):
        self.assertEqual(
            self.atlas.country("Turkey").formal_name,
            "Republic of Türkiye",
        )
        self.assertEqual(
            self.atlas.country("Guyana").formal_name,
            "Co-operative Republic of Guyana",
        )
        self.assertEqual(
            self.atlas.country("Viet Nam").formal_name,
            "Socialist Republic of Viet Nam",
        )
        self.assertTrue(self.atlas.country("Afghanistan").has_distinct_formal_name)
        self.assertIsNone(self.atlas.country("Aland Islands").formal_name)
        self.assertEqual(self.atlas.country("Republic of Türkiye").alpha2, "TR")
        self.assertEqual(
            self.atlas.country("Co-operative Republic of Guyana").alpha2,
            "GY",
        )

        covered = self.atlas.countries_with_formal_names()
        self.assertEqual(len(covered), 240)
        self.assertEqual(
            {country.alpha2 for country in self.atlas.countries()} -
            {country.alpha2 for country in covered},
            {"AX", "BQ", "GF", "GP", "MQ", "RE", "UM", "YT"},
        )
        source_ids = {source.id for source in self.atlas.country("Guyana").sources}
        self.assertIn("wikidata-official-names-2026-07-21", source_ids)

    def test_reviewed_official_local_names(self):
        brazil = self.atlas.country("Brazil")
        self.assertEqual(brazil.name_in("pt"), "Brasil")
        self.assertEqual(brazil.official_name_in("pt"), "República Federativa do Brasil")
        self.assertIsNone(brazil.name_in("en"))
        self.assertIsNone(brazil.romanized_name_in("pt"))
        self.assertEqual(brazil.local_names[0].script_code, "Latn")
        self.assertEqual(brazil.local_names[0].source.id, "ungegn-country-names-2017")
        self.assertTrue(brazil.local_names[0].is_national_official)

        switzerland = self.atlas.country("Switzerland")
        self.assertEqual(
            {name.language_code: name.short_name for name in switzerland.local_names},
            {"de": "Schweiz"},
        )
        self.assertEqual(
            switzerland.official_name_in("de"),
            "Schweizerische Eidgenossenschaft",
        )

        dominican = self.atlas.country("DO")
        self.assertEqual(dominican.local_name_languages, ("es",))
        self.assertEqual(dominican.name_in("ES"), "República Dominicana")
        self.assertEqual(dominican.local_name("es").formal_name, "República Dominicana")

        china = self.atlas.country("China")
        self.assertEqual(china.name_in("zh"), "中国")
        self.assertEqual(china.official_name_in("zh"), "中华人民共和国")
        self.assertEqual(china.romanized_name_in("zh"), "Zhongguo")
        self.assertEqual(
            china.romanized_official_name_in("zh"),
            "Zhonghua Renmin Gongheguo",
        )

        india = self.atlas.country("India")
        self.assertEqual(india.local_name_languages, ("hi",))
        self.assertEqual(india.name_in("hi"), "भारत")
        self.assertEqual(india.romanized_name_in("hi"), "Bhārat")
        self.assertIn("PDF page 44", india.local_name("hi").source_locator)

        japan = self.atlas.country("Japan")
        self.assertEqual(japan.name_in("ja"), "日本")
        self.assertEqual(japan.romanized_name_in("ja"), "Nihon, or Nippon")

        reviewed = self.atlas.countries_with_local_names()
        self.assertEqual(len(reviewed), 248)
        self.assertEqual(
            len(self.atlas.countries_with_local_names(name_kind="national_official")),
            10,
        )
        self.assertEqual(
            len(self.atlas.countries_with_local_names(name_kind="LOCALE_DISPLAY")),
            238,
        )
        with self.assertRaisesRegex(ValueError, "name_kind"):
            self.atlas.countries_with_local_names(name_kind="translated")
        self.assertEqual(
            tuple(country.alpha2 for country in self.atlas.countries_with_local_names(script_code="Jpan")),
            ("JP",),
        )
        spanish = {
            country.alpha2
            for country in self.atlas.countries_with_local_names(language_code="ES")
        }
        self.assertTrue({"CL", "DO", "ES", "MX"} <= spanish)

        andorra = self.atlas.country("Andorra")
        self.assertEqual(andorra.name_in("ca"), "Andorra")
        self.assertIsNone(andorra.official_name_in("ca"))
        self.assertEqual(andorra.local_name("ca").kind, "locale_display")
        self.assertEqual(andorra.local_name("ca").source.id, "unicode-cldr-48.2")
        self.assertEqual(andorra.local_name("ca").language_status, "official")

        antarctica = self.atlas.country("Antarctica").local_names[0]
        self.assertFalse(antarctica.is_official_language)
        self.assertEqual(antarctica.language_status, "not_applicable")

    def test_local_names_survive_close_and_serialize_as_unicode(self):
        brazil = self.atlas.country("Brazil")
        self.atlas.close()
        self.assertEqual(brazil.official_name_in("pt"), "República Federativa do Brasil")
        self.assertIn("República Federativa do Brasil", brazil.to_json())
        self.assertIn("PDF page 17", brazil.to_json())

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
