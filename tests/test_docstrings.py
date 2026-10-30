"""Every public Atlas method explains itself with a tested example."""

from __future__ import annotations

import doctest
import inspect
import re
import unittest
from pathlib import Path

from pack_fixtures import installed_packs

from pyworldatlas import Atlas

API_PAGE = Path(__file__).resolve().parents[1] / "docs" / "source" / "api.rst"


def public_methods() -> dict[str, object]:
    """Return the public Atlas methods, including the older names."""
    return {
        name: member
        for name, member in inspect.getmembers(Atlas, inspect.isfunction)
        if not name.startswith("_")
    }


def is_older_name(member: object) -> bool:
    return (inspect.getdoc(member) or "").startswith("Older name")


class DocstringTests(unittest.TestCase):
    def test_every_method_has_an_example(self) -> None:
        for name, member in public_methods().items():
            if is_older_name(member):
                continue
            doc = inspect.getdoc(member) or ""
            with self.subTest(method=name):
                self.assertIn("Example:", doc)
                self.assertIn(">>>", doc)
                parameters = [p for p in inspect.signature(member).parameters if p != "self"]
                if parameters:
                    self.assertIn("Args:", doc)
                    for parameter in parameters:
                        self.assertRegex(doc, rf"\n    {parameter}: ", parameter)
                if inspect.signature(member).return_annotation not in ("None", None):
                    self.assertIn("Returns:", doc)

    def test_examples_give_what_they_show(self) -> None:
        atlas = Atlas(data_dir=installed_packs())
        self.addCleanup(atlas.close)
        finder = doctest.DocTestFinder(recurse=False)
        runner = doctest.DocTestRunner(optionflags=doctest.ELLIPSIS)
        tried = 0
        for name, member in public_methods().items():
            for test in finder.find(member, f"Atlas.{name}", globs={"atlas": atlas, "Atlas": Atlas}):
                tried += len(test.examples)
                result = runner.run(test, out=lambda text: None)
                self.assertEqual(result.failed, 0, f"Atlas.{name} has a failing example; run its doctest")
        self.assertGreater(tried, 70)

    def test_api_page_lists_every_method_once(self) -> None:
        listed = re.findall(r"^\.\. automethod:: pyworldatlas\.Atlas\.(\w+)$", API_PAGE.read_text(encoding="utf-8"), re.M)
        self.assertEqual(len(listed), len(set(listed)))
        self.assertEqual(set(public_methods()) - set(listed), set())


if __name__ == "__main__":
    unittest.main()
