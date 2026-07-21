import subprocess
import sys
import unittest


class ImportTests(unittest.TestCase):
    def test_import_is_silent(self):
        result = subprocess.run([sys.executable, "-c", "import pyworldatlas"], capture_output=True, text=True, check=True)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")

    def test_playground_audits_every_record(self):
        result = subprocess.run(
            [sys.executable, "playground.py", "--audit-only"],
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertIn("Countries tested: 12", result.stdout)
        self.assertIn("Cities tested   : 1429", result.stdout)
        self.assertIn("every currently exposed record was checked", result.stdout)


if __name__ == "__main__":
    unittest.main()
