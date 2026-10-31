import os
import subprocess
import sys
import unittest


class ImportTests(unittest.TestCase):
    def test_import_is_silent(self):
        result = subprocess.run([sys.executable, "-c", "import pyworldatlas"], capture_output=True, text=True, check=True)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")

    def test_results_print_when_output_uses_a_legacy_code_page(self):
        # Redirected output on Windows often uses cp1252, which has no arrow.
        env = {**os.environ, "PYTHONIOENCODING": "cp1252"}
        env.pop("PYTHONUTF8", None)
        code = "import pyworldatlas; print('Portugal → Spain · 503 km²')"
        result = subprocess.run([sys.executable, "-X", "utf8=0", "-c", code], capture_output=True, env=env, check=True)
        self.assertEqual(result.stdout.decode("utf-8").strip(), "Portugal → Spain · 503 km²")

    def test_utf8_output_is_left_alone(self):
        env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
        code = "import sys, pyworldatlas; print(sys.stdout.encoding)"
        result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env, check=True)
        self.assertEqual(result.stdout.strip(), "utf-8")


if __name__ == "__main__":
    unittest.main()
