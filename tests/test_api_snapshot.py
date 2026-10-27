"""Fail when the public API changes without an intentional snapshot update.

To accept an intentional change, run:

    PYWORLDATLAS_UPDATE_API_SNAPSHOT=1 python -m unittest tests.test_api_snapshot
"""

import json
import os
from pathlib import Path
import unittest

from api_surface import public_api


SNAPSHOT = Path(__file__).with_name("api_snapshot.json")


class PublicApiSnapshotTests(unittest.TestCase):
    def test_public_api_matches_snapshot(self) -> None:
        current = public_api()
        if os.environ.get("PYWORLDATLAS_UPDATE_API_SNAPSHOT") == "1":
            SNAPSHOT.write_text(
                json.dumps(current, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
                newline="\n",
            )
        recorded = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
        self.assertEqual(current, recorded)


if __name__ == "__main__":
    unittest.main()
