# Releasing PyWorldAtlas

This repository builds, tests, publishes, and deploys each release from one Git
tag. PyPI publishing uses short-lived Trusted Publishing credentials; no PyPI
API token is stored in GitHub.

## One-time repository setup

Create an empty public repository named `pyworldatlas` under `jcari-dev`. Do not
initialize it with a README, license, or `.gitignore`; those files already exist
in this checkout.

From the VS Code terminal:

```console
git remote add origin https://github.com/jcari-dev/pyworldatlas.git
git remote -v
git push -u origin main
```

The first push runs CI on Python 3.10 through 3.14 and runs the complete wheel,
example, and documentation quality gate on Python 3.12.

## Configure TestPyPI

TestPyPI uses a separate account from PyPI. In TestPyPI's publishing settings,
register a pending GitHub publisher with:

| Setting | Value |
|---|---|
| PyPI project name | `pyworldatlas` |
| Owner | `jcari-dev` |
| Repository | `pyworldatlas` |
| Workflow | `test-release.yml` |
| Environment | `testpypi` |

Create a GitHub environment named `testpypi`. Run the **TestPyPI release**
workflow manually from the repository's Actions page.

Verify the uploaded wheel in a disposable environment without activating it:

```console
py -3.10 -m venv .venv-testpypi
.venv-testpypi\Scripts\python -m pip install --index-url https://test.pypi.org/simple/ --no-deps pyworldatlas==0.1.0
.venv-testpypi\Scripts\python -c "from pyworldatlas import Atlas; a=Atlas(); print(len(a), a.country('Japan').capital.name); a.close()"
```

## Configure production PyPI

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

## Configure documentation deployment

Create a fine-grained GitHub personal access token restricted to
`jcari-dev/pyworldatlas-documentation` with **Contents: Read and write**. Add it
to the `pyworldatlas` repository as an Actions secret named
`DOCS_DEPLOY_TOKEN`.

The release workflow builds Sphinx from the exact release wheel and replaces the
generated files in the documentation repository. Source documentation remains
in this repository under `docs/source/`.

## Prepare and publish a release

Run the local release gate first:

```console
python maintain.py bootstrap
python maintain.py prepare-release 0.1.0
```

Review `dist/release-manifest.json` and `dist/SHA256SUMS`, then create and push
the release tag:

```console
git status
git tag -a v0.1.0 -m "Release 0.1.0"
git push origin main
git push origin v0.1.0
```

The tag workflow publishes the wheel and source distribution to PyPI, creates a
GitHub Release with checksums and the release manifest, and deploys the Sphinx
site.

Verify the public package in a new environment:

```console
py -3.10 -m venv .venv-live
.venv-live\Scripts\python -m pip install --no-cache-dir pyworldatlas==0.1.0
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
