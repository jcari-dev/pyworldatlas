"""Every "Try it" example in the docs runs as a script with no packs installed.

The docs mark an example with ``.. rst-class:: atlas-try-these``, and
``docs/source/_static/copy.js`` turns it into a script for the browser
playground, which has the core data only. This file repeats those rules so the
scripts are checked in plain Python.
"""

from __future__ import annotations

import contextlib
import io
import re
import tempfile
import unittest
from pathlib import Path

DOCS = Path(__file__).resolve().parents[1] / "docs" / "source"
MARKER = ".. rst-class:: atlas-try-these"
SETUP = {"from datetime import date", "from pyworldatlas import Atlas", "atlas = Atlas()", "atlas.close()"}
STATEMENT = re.compile(
    r"^(?:import|from|for|while|with|if|def|class|try|print\(|"
    r"[A-Za-z_][\w.]*(?:\s*,\s*[A-Za-z_][\w.]*)*\s*=[^=])"
)


def marked_examples(path: Path) -> list[list[str]]:
    """Return the doctest lines of every marked example on one page."""
    lines = path.read_text(encoding="utf-8").splitlines()
    examples = []
    for index, line in enumerate(lines):
        if line.strip() != MARKER:
            continue
        directive = next(i for i in range(index + 1, len(lines)) if lines[i].strip())
        if lines[directive].strip() != ".. doctest::":
            raise AssertionError(f"{path.name}:{index + 1}: the marker must come before a doctest")
        block = []
        for body in lines[directive + 1:]:
            if body.strip() and not body.startswith("   "):
                break
            block.append(body[3:])
        examples.append([line for line in block if line.strip()])
    return examples


def script_of(lines: list[str]) -> str:
    """Turn doctest lines into the script the playground receives."""
    code = []
    for index, line in enumerate(lines):
        if line.startswith(">>> "):
            source = re.sub(r"\s*#\s*doctest:.*$", "", line[4:])
            following = lines[index + 1] if index + 1 < len(lines) else None
            shows = following is not None and not following.startswith((">>> ", "..."))
            code.append(f"print({source})" if shows and not STATEMENT.match(source) else source)
        elif line.startswith("... ") or line == "...":
            code.append(line[4:])
    return "\n".join(line for line in code if line not in SETUP).strip()


class TryLinkTests(unittest.TestCase):
    def test_marked_examples_run_without_packs(self) -> None:
        pages = sorted(path for path in DOCS.glob("*.rst") if MARKER in path.read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(pages), 3)
        count = 0
        with tempfile.TemporaryDirectory() as empty:
            from pyworldatlas import Atlas

            for page in pages:
                for number, lines in enumerate(marked_examples(page), 1):
                    script = script_of(lines)
                    with self.subTest(page=page.name, example=number):
                        self.assertTrue(script)
                        namespace = {"Atlas": Atlas}
                        exec("from datetime import date", namespace)
                        namespace["atlas"] = Atlas(data_dir=empty)
                        try:
                            with contextlib.redirect_stdout(io.StringIO()) as output:
                                exec(compile(script, f"{page.name} example {number}", "exec"), namespace)
                        finally:
                            namespace["atlas"].close()
                        self.assertTrue(output.getvalue().strip(), "the script prints nothing")
                        count += 1
        self.assertGreaterEqual(count, 15)


if __name__ == "__main__":
    unittest.main()
