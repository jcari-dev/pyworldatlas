import json
import subprocess
import sys
import unittest


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
        self.assertEqual(version.stdout.strip(), "PyWorldAtlas 0.9.5")

        country = self.run_cli("country", "JP")
        self.assertEqual(country.returncode, 0)
        self.assertEqual(country.stderr, "")
        self.assertIn("Japan (JP)", country.stdout)
        self.assertIn("Capital: Tokyo", country.stdout)

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


if __name__ == "__main__":
    unittest.main()
