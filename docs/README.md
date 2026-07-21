# Documentation environment

PyWorldAtlas 0.x supports Python 3.10 through 3.14 at runtime. Documentation
dependencies use interpreter-specific pins because Sphinx 8.2 and later require
Python 3.11 or newer:

- Python 3.10 uses Sphinx 8.1.3.
- Python 3.11 and newer use Sphinx 8.2.3.

Both use `sphinx-rtd-theme` 3.0.2 and build the same documentation source.

From an activated development environment:

```console
python -m pip install -r docs/requirements.txt -e . -e pipeline
python maintain.py test
python maintain.py preview
python maintain.py check
```

`python maintain.py preview` builds the HTML and doctests, then serves the site
at `http://127.0.0.1:8000/`. Press Ctrl+C in the terminal to stop it.

Python versions are not claimed as release-supported until the CI matrix has
passed on that version.
