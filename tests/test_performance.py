"""Speed guards for the performance budgets in docs/project/PLAN.md.

Shared CI machines vary a lot, so each limit sits well above the budget measured
on a typical laptop. The guards catch regressions of the kind that once made
ranking by border count take nearly half a second, without flaky failures.
Each timing is the best of several runs.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import time
import unittest

from pyworldatlas import Atlas


def best_ms(action, *, repeat: int = 5) -> float:
    timings = []
    for _ in range(repeat):
        start = time.perf_counter()
        action()
        timings.append((time.perf_counter() - start) * 1000)
    return min(timings)


class PerformanceBudgetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.atlas = Atlas()
        cls.atlas.countries()  # warm the shared caches once

    @classmethod
    def tearDownClass(cls) -> None:
        cls.atlas.close()

    def test_import_is_quick(self) -> None:
        program = (
            "import time; start = time.perf_counter(); import pyworldatlas; "
            "print((time.perf_counter() - start) * 1000)"
        )
        timings = [
            float(subprocess.run(
                [sys.executable, "-c", program], check=True, capture_output=True, text=True,
            ).stdout)
            for _ in range(3)
        ]
        self.assertLess(min(timings), 400, "budget 50 ms")

    def test_first_full_load_is_quick(self) -> None:
        def load() -> None:
            with Atlas() as fresh:
                fresh.countries()

        self.assertLess(best_ms(load, repeat=3), 600, "budget well under 100 ms")

    def test_common_calls_are_instant_once_loaded(self) -> None:
        atlas = self.atlas
        calls = {
            "country": lambda: atlas.country("Japan"),
            "search_countries": lambda: atlas.search_countries("an"),
            "rank population": lambda: atlas.rank("population"),
            "rank border_count": lambda: atlas.rank("border_count"),
            "border_path": lambda: atlas.border_path("Portugal", "China"),
            "nearest_capitals": lambda: atlas.nearest_capitals("Paris", country="FR"),
            "nearest_cities": lambda: atlas.nearest_cities((48.85, 2.35)),
            "quiz neighbors": lambda: atlas.quiz(topic="neighbors", count=10),
            "search_cities": lambda: atlas.search_cities("san"),
        }
        atlas.nearest_cities((0.0, 0.0))  # load place positions once
        for name, call in calls.items():
            with self.subTest(call=name):
                self.assertLess(best_ms(call), 60, f"{name}: budget 10 ms")

    def test_place_searches_are_instant_once_indexed(self) -> None:
        with tempfile.TemporaryDirectory() as folder, Atlas(data_dir=folder) as atlas:
            started = time.perf_counter()
            atlas.search_places("Paris")  # builds the school atlas index once
            self.assertLess(time.perf_counter() - started, 30, "budget about 3 s on a laptop")
            calls = {
                "search_places": lambda: atlas.search_places("Kilimanjaro"),
                "search_places prefix": lambda: atlas.search_places("a"),
                "place": lambda: atlas.place("Lake Titicaca"),
                "places_near": lambda: atlas.places_near((48.85, 2.35)),
                "places_near open ocean": lambda: atlas.places_near((-48.9, -123.4)),
                "places_near water": lambda: atlas.places_near((0.0, 0.0), category="water"),
            }
            for name, call in calls.items():
                with self.subTest(call=name):
                    self.assertLess(best_ms(call), 60, f"{name}: budget 10 ms")


if __name__ == "__main__":
    unittest.main()
