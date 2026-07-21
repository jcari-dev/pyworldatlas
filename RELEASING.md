# Releasing PyWorldAtlas

This repository builds, tests, publishes, and deploys each release from one Git
tag. PyPI publishing uses short-lived Trusted Publishing credentials; no PyPI
API token is stored in GitHub.

A `v0.1.0` tag and release artifacts preserve the rebuilt baseline. Verify that
the intended version appears in the package index before running its
installation smoke test.

## Repository setup

The canonical source repository is `jcari-dev/pyworldatlas`. Verify the remote
from a terminal in the repository root:

```console
git remote -v
```

Pushes and pull requests to `main` run CI on Python 3.10 through 3.14 and the
complete wheel, example, and documentation gate on Python 3.12.

## Production PyPI publisher

On the existing PyPI project's **Publishing** page, add a GitHub Actions trusted
publisher with:

| Setting | Value |
|---|---|
| Owner | `jcari-dev` |
| Repository | `pyworldatlas` |
| Workflow | `release.yml` |
| Environment | `pypi` |

Create a protected GitHub environment named `pypi` and require your approval
before deployment.

## Documentation deployment

Create a fine-grained GitHub personal access token restricted to
`jcari-dev/pyworldatlas-documentation` with **Contents: Read and write**. Add it
to the `pyworldatlas` repository as an Actions secret named
`DOCS_DEPLOY_TOKEN`.

The release workflow builds Sphinx from the exact release wheel and replaces the
generated files in the documentation repository. Source documentation remains
in this repository under `docs/source/`.

## Prepare and publish a release

For example, to publish the next planned feature release, run the local release
gate first:

```console
python maintain.py bootstrap
python maintain.py prepare-release 0.2.0
```

If Windows reports that an existing file under `dist` is in use, close the
terminal, upload dialog, or file preview holding it. To run the same release
gate without replacing that directory, choose another ignored output path:

```console
python maintain.py prepare-release 0.2.0 --output-dir build/release-dist
```

Review `release-manifest.json` and `SHA256SUMS` in the selected output directory.
Install that wheel into a disposable local environment if a final manual smoke
test is useful. Merge the release candidate to `main`, confirm that CI is green
and the working tree is clean, then create and push the release tag:

```console
git status
git tag -a v0.2.0 -m "Release 0.2.0"
git push origin main
git push origin v0.2.0
```

The tag workflow publishes the wheel and source distribution to PyPI, creates a
GitHub Release with checksums and the release manifest, and deploys the Sphinx
site.

Verify the public package in a new environment:

```console
py -3.10 -m venv .venv-live
.venv-live\Scripts\python -m pip install --no-cache-dir pyworldatlas==0.2.0
.venv-live\Scripts\python -c "from pyworldatlas import Atlas; a=Atlas(); print(len(a), a.country('Mexico').capital.name); a.close()"
```

Finally, verify the public pages:

- <https://github.com/jcari-dev/pyworldatlas/actions>
- <https://github.com/jcari-dev/pyworldatlas/releases>
- <https://pypi.org/project/pyworldatlas/>
- <https://jcari-dev.github.io/pyworldatlas-documentation/>

## Future releases

For each feature or data release, update `pyproject.toml`,
`src/pyworldatlas/_version.py`, `docs/source/conf.py`, and `CHANGELOG.md` together.
Regenerate the data/status artifacts when coverage changes, run
`python maintain.py prepare-release VERSION`, and publish a matching `vVERSION`
tag only after CI is green.

Never reuse, delete, or move a published version tag. If publication fails
before PyPI accepts the version, repair the workflow and rerun it. If PyPI has
accepted the version, preserve it and use a patch release for any code or
metadata correction.
