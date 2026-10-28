"""Sunrise, sunset, and day length."""

from __future__ import annotations

from datetime import date, datetime
import unittest

from pyworldatlas import Atlas, SunTimes
from pyworldatlas._sun import sun_times


class SunTests(unittest.TestCase):
    def test_matches_almanac_times(self) -> None:
        # London, June solstice: sunrise 03:43 UTC, sunset 20:21 UTC.
        _, sunrise, sunset, hours, _ = sun_times(51.5074, -0.1278, date(2026, 6, 21))
        assert sunrise is not None and sunset is not None
        self.assertEqual((sunrise.strftime("%H:%M"), sunset.strftime("%H:%M")), ("03:43", "20:21"))
        self.assertAlmostEqual(hours, 16.64, places=1)
        # At the equator on an equinox, day and night are close to equal.
        _, _, _, equator, height = sun_times(0, 0, date(2026, 3, 20))
        self.assertAlmostEqual(equator, 12.1, places=1)
        self.assertGreater(height, 89)

    def test_midnight_sun_and_polar_night(self) -> None:
        summer = sun_times(69.65, 18.96, date(2026, 6, 21))
        winter = sun_times(69.65, 18.96, date(2026, 12, 21))
        self.assertEqual((summer[1], summer[3]), (None, 24.0))
        self.assertEqual((winter[2], winter[3]), (None, 0.0))
        self.assertLess(winter[4], 0)

    def test_atlas_sun(self) -> None:
        with Atlas() as atlas:
            london = atlas.sun("London", date(2026, 12, 21))
            everest = atlas.sun("Mount Everest", date(2026, 3, 20))
            point = atlas.sun((-33.87, 151.21), datetime(2026, 1, 1, 9, 30))
            with self.assertRaises(TypeError):
                atlas.sun("London", "2026-01-01")  # type: ignore[arg-type]
        self.assertIsInstance(london, SunTimes)
        self.assertEqual(london.daylight, "7 h 49 min")
        self.assertIn("sets at 15:53 UTC", london.summary)
        self.assertGreater(everest.day_length_hours, 12)
        self.assertIn("on 31 December", point.summary)
        self.assertEqual(london.to_dict()["date"], "2026-12-21")
        polar = SunTimes(london.coordinates, london.date, london.solar_noon, None, None, 24.0, 40.0)
        self.assertIn("midnight sun", polar.summary)


if __name__ == "__main__":
    unittest.main()
