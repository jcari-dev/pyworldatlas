from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import json
import subprocess
import sys
import unittest

from pyworldatlas.__main__ import main


class CommandLineTests(unittest.TestCase):
    def run_cli(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        """Run the module entry point with captured UTF-8 text."""
        return subprocess.run(
            [sys.executable, "-m", "pyworldatlas", *arguments],
            capture_output=True,
            encoding="utf-8",
            errors="strict",
            check=False,
        )

    def test_version_and_country_summary_are_readable(self) -> None:
        version = self.run_cli("--version")
        self.assertEqual(version.returncode, 0)
        self.assertEqual(version.stdout.strip(), "PyWorldAtlas 0.12.1")

        country = self.run_cli("country", "JP")
        self.assertEqual(country.returncode, 0)
        self.assertEqual(country.stderr, "")
        self.assertIn("Japan (JP)", country.stdout)
        self.assertIn("Capital: Tokyo", country.stdout)

    def test_find_lists_countries_and_places(self) -> None:
        result = self.run_cli("find", "Georgia", "--limit", "2")
        self.assertEqual(result.returncode, 0)
        lines = result.stdout.splitlines()
        self.assertTrue(lines[0].startswith("Georgia, country (GE)"))
        self.assertTrue(lines[1].startswith("Georgia, state or province (US)"))
        missing = self.run_cli("find", "Zzyzx Qwertyland")
        self.assertEqual(missing.returncode, 1)
        self.assertIn("Nothing found", missing.stderr)

    def test_country_json_is_valid(self) -> None:
        result = self.run_cli("country", "Japan", "--json")
        self.assertEqual(result.returncode, 0)
        profile = json.loads(result.stdout)
        self.assertEqual(profile["codes"]["alpha2"], "JP")

    def test_lookup_errors_are_concise(self) -> None:
        missing = self.run_cli("country", "Atlantis")
        self.assertEqual(missing.returncode, 1)
        self.assertEqual(missing.stdout, "")
        self.assertIn("No country matches 'Atlantis'", missing.stderr)
        self.assertNotIn("Traceback", missing.stderr)

        search = self.run_cli("search", "zzz-no-match")
        self.assertEqual(search.returncode, 1)
        self.assertEqual(search.stdout, "")
        self.assertEqual(
            search.stderr,
            "No countries found for 'zzz-no-match'.\n",
        )


class InProcessCommandLineTests(unittest.TestCase):
    def call(self, *arguments: str) -> tuple[int, str, str]:
        """Run ``main`` in this process and return its exit code and output."""
        stdout, stderr = StringIO(), StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            try:
                code = main(list(arguments))
            except SystemExit as exit_:
                code = int(exit_.code or 0)
        return code, stdout.getvalue(), stderr.getvalue()

    def test_country_summary_and_json(self) -> None:
        code, output, _ = self.call("country", "France")
        self.assertEqual(code, 0)
        self.assertIn("France (FR) | Capital: Paris", output)
        code, output, _ = self.call("country", "FR", "--json")
        self.assertEqual(json.loads(output)["codes"]["alpha3"], "FRA")

    def test_search_lists_matches(self) -> None:
        code, output, _ = self.call("search", "united")
        self.assertEqual(code, 0)
        self.assertIn("GB\tUnited Kingdom", output)

    def test_dataset_info_is_json(self) -> None:
        code, output, _ = self.call("dataset-info")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(output)["country_count"], 248)

    def test_errors_exit_with_one(self) -> None:
        self.assertEqual(self.call("country", "Atlantis")[0], 1)
        self.assertEqual(self.call("search", "zzz-no-match")[0], 1)


if __name__ == "__main__":
    unittest.main()
