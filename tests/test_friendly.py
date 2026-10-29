"""Forgiving input: typo suggestions, flexible topics, and sensible defaults."""

from __future__ import annotations

import unittest

from pack_fixtures import installed_packs

from pyworldatlas import Atlas, CountryNotFoundError, PlaceNotFoundError
from pyworldatlas._suggest import by_prefix, choice, closest, did_you_mean, similarity


class SuggestionHelperTests(unittest.TestCase):
    def test_similarity_prefers_whole_names_and_skips_short_words(self) -> None:
        self.assertGreater(similarity("Tokio", "Tokyo"), similarity("Tokio", "Nishi-Tokyo-shi"))
        self.assertLess(similarity("Japn", "Svalbard and Jan Mayen"), 0.75)
        self.assertGreater(similarity("Everst", "Mount Everest"), 0.9)

    def test_closest_and_sentence(self) -> None:
        self.assertEqual(closest("Germny", ["Germany", "Guernsey", "Kenya"]), ["Germany"])
        self.assertEqual(closest("zzzz", ["Germany"]), [])
        self.assertEqual(did_you_mean([]), "")
        self.assertEqual(did_you_mean(["Japan"]), " Did you mean Japan?")
        self.assertEqual(did_you_mean(["A", "B", "C"]), " Did you mean A, B or C?")

    def test_by_prefix_collects_candidates_from_shorter_beginnings(self) -> None:
        index = {"evers": ["Everson"], "ever": ["Everson", "Mount Everest"]}
        self.assertEqual(by_prefix("Everst", lambda text: index.get(text, []), limit=1), ["Mount Everest"])

    def test_choice_forgives_case_spaces_and_plurals(self) -> None:
        topics = ("capitals", "plug_types", "currencies", "higher")
        self.assertEqual(choice("Capital", topics), "capitals")
        self.assertEqual(choice("plug types", topics), "plug_types")
        self.assertEqual(choice("currency", topics), None)  # "currency" is not a plain plural
        self.assertEqual(choice("currencies", topics), "currencies")
        self.assertEqual(choice("highers", topics), "higher")
        self.assertIsNone(choice("trivia", topics))


class FriendlyAtlasTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.atlas = Atlas(data_dir=installed_packs())

    @classmethod
    def tearDownClass(cls) -> None:
        cls.atlas.close()

    def test_typos_get_suggestions(self) -> None:
        with self.assertRaisesRegex(CountryNotFoundError, r"'Japn'\. Did you mean Japan\?$"):
            self.atlas.country("Japn")
        with self.assertRaisesRegex(PlaceNotFoundError, "Did you mean .*Mount Everest"):
            self.atlas.place("Everst")
        with self.assertRaisesRegex(PlaceNotFoundError, r"Did you mean Tokyo\b"):
            self.atlas.city("Tokio")
        with self.assertRaisesRegex(ValueError, "Did you mean life_expectancy"):
            self.atlas.statistic("Japan", "life expectancey")
        with self.assertRaisesRegex(ValueError, "Did you mean higher"):
            self.atlas.place_quiz("highr")
        with self.assertRaisesRegex(ValueError, "Did you mean capitals"):
            self.atlas.quiz("capitel")
        # Partial names still list the countries that contain the text.
        with self.assertRaisesRegex(CountryNotFoundError, "Did you mean .*Korea"):
            self.atlas.country("Kore")

    def test_border_methods_accept_country_profiles(self) -> None:
        france, spain = self.atlas["France"], self.atlas["Spain"]
        self.assertEqual(self.atlas.neighbors(france), self.atlas.neighbors("France"))
        self.assertTrue(self.atlas.shares_border(france, spain))
        self.assertEqual(self.atlas.shared_neighbors(france, spain), self.atlas.shared_neighbors("FR", "ES"))
        path = self.atlas.border_path(france, self.atlas["China"])
        self.assertIsNotNone(path)
        self.assertEqual(self.atlas.border_crossings(france, spain), 1)
        self.assertTrue(self.atlas.has_land_route(france, spain))
        self.assertIn(spain, self.atlas.countries_reachable_by_land(france))

    def test_topics_are_forgiving_and_counts_have_defaults(self) -> None:
        self.assertEqual(len(self.atlas.quiz("Capital")), 5)
        self.assertEqual(len(self.atlas.flashcards("capitals")), 10)
        self.assertEqual(self.atlas.quiz("capitals"), self.atlas.quiz(topic="capitals", count=5))
        self.assertEqual(len(self.atlas.place_quiz("Kind")), 5)
        self.assertEqual(
            self.atlas.statistic("Japan", "Life Expectancy"), self.atlas.statistic("Japan", "life_expectancy")
        )
        with self.assertRaises(TypeError):
            self.atlas.quiz(3)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
