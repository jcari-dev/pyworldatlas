# Documentation development

PyWorldAtlas supports Python 3.10 through 3.14. Documentation dependencies use
interpreter-specific pins because Sphinx 8.2 and newer require Python 3.11:

- Python 3.10 uses Sphinx 8.1.3.
- Python 3.11 and newer use Sphinx 8.2.3.

From an activated development environment, install the complete toolchain once:

```console
python maintain.py bootstrap
```

Then use the maintainer commands:

```console
python maintain.py test
python maintain.py preview
python maintain.py check
```

`python maintain.py preview` validates the documentation and serves it at
`http://127.0.0.1:8000/`. Press Ctrl+C to stop the server. The complete
`check` command also builds and audits the package distributions.

Python versions are release-supported only after the CI matrix passes on that
version. Maintainer-facing data and publication references live in
[`docs/project`](project/README.md).
