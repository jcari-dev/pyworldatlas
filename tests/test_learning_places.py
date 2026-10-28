"""Antipodes and place quizzes."""

from __future__ import annotations

import unittest

from pyworldatlas import Antipode, Atlas, PlaceQuestion


class AntipodeTests(unittest.TestCase):
    def test_antipode(self) -> None:
        with Atlas() as atlas:
            madrid = atlas.antipode("Madrid")
            point = atlas.antipode((10.0, -170.0), limit=1)
        self.assertIsInstance(madrid, Antipode)
        self.assertAlmostEqual(madrid.antipode.latitude, -madrid.origin.latitude)
        self.assertAlmostEqual(abs(madrid.antipode.longitude - madrid.origin.longitude), 180, places=4)
        self.assertEqual(madrid.nearest[0].place.country_code, "NZ")
        self.assertEqual((point.antipode.latitude, point.antipode.longitude), (-10.0, 10.0))
        self.assertEqual(len(point.nearest), 1)
        self.assertIn("Straight through the centre of the Earth", madrid.summary)
        self.assertEqual(madrid.to_dict()["origin"], {"latitude": madrid.origin.latitude, "longitude": madrid.origin.longitude})


class PlaceQuizTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.atlas = Atlas()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.atlas.close()

    def test_topics_are_deterministic_and_correct(self) -> None:
        for topic in Atlas.PLACE_QUIZ_TOPICS:
            questions = self.atlas.place_quiz(topic, count=10, seed="class-5")
            self.assertEqual(questions, self.atlas.place_quiz(topic, count=10, seed="class-5"))
            self.assertEqual(len(questions), 10)
            for question in questions:
                self.assertIsInstance(question, PlaceQuestion)
                self.assertTrue(question.is_correct(question.answer_number))
                self.assertTrue(question.is_correct(question.answer.upper()))

    def test_answers_match_the_facts(self) -> None:
        for question in self.atlas.place_quiz("higher", count=10, seed=3):
            winner = max(question.places, key=lambda place: place.elevation_m or 0)
            self.assertEqual(question.answer, winner.english_name)
        for question in self.atlas.place_quiz("closer_to_equator", count=10, seed=3):
            winner = min(question.places, key=lambda place: abs(place.coordinates.latitude))
            self.assertEqual(question.answer, winner.english_name)
        for question in self.atlas.place_quiz("kinds", count=10, seed=3):
            self.assertEqual(question.answer, question.places[0].kind)
            self.assertEqual(len(question.choices), 4)

    def test_bad_input(self) -> None:
        with self.assertRaises(ValueError):
            self.atlas.place_quiz("capitals")
        with self.assertRaises(ValueError):
            self.atlas.place_quiz("kinds", count=0)
        question = self.atlas.place_quiz("kinds", count=1)[0]
        self.assertFalse(question.is_correct(True))
        with self.assertRaises(ValueError):
            PlaceQuestion("kinds", "?", ("a",), "a", ())


if __name__ == "__main__":
    unittest.main()
