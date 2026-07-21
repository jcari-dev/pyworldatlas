import subprocess
import sys
import unittest


class ImportTests(unittest.TestCase):
    def test_import_is_silent(self):
        result = subprocess.run([sys.executable, "-c", "import pyworldatlas"], capture_output=True, text=True, check=True)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")

if __name__ == "__main__":
    unittest.main()
