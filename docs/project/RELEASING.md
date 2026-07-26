# Maintainer release process

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

Documentation-only updates do not require a new PyPI version. Changes under
`docs/` or `examples/` run the dedicated `Documentation` workflow after they
are merged to `main`. That workflow builds strict HTML and doctests from the
current checkout before updating the documentation repository. The release
workflow remains the authoritative path when the package API, data, or version
changes.

## Prepare and publish a release

> **Current candidate:** 0.8.1 is a documentation-presentation patch for the
> published education-and-usability milestone. Publish 0.8.1 only after its
> pull request is merged to
> `main` and CI is green.

### Current 0.8.1 sequence

From the repository root on the `codex/docs-seo-polish` branch:

```console
python maintain.py prepare-release 0.8.1
git status
git add -A
git commit -m "Prepare PyWorldAtlas 0.8.1"
git push -u origin codex/docs-seo-polish
```

On GitHub, open a pull request with:

- Base branch: `main`
- Compare branch: `codex/docs-seo-polish`
- Title: `Release PyWorldAtlas 0.8.1`

Wait for every CI job to pass, review the file and source changes, and merge the
pull request. Do not create the release tag from the feature branch.

After the merge, return to the terminal and tag the exact merged `main` commit:

```console
git switch main
git pull --ff-only origin main
python maintain.py prepare-release 0.8.1
git status
git tag -a v0.8.1 -m "Release 0.8.1"
git push origin v0.8.1
```

The tag starts the release workflow. Approve the protected `pypi` environment
when GitHub requests it. The workflow must finish all four jobs: build,
PyPI publication, GitHub Release creation, and documentation deployment.

For example, to publish the next planned feature release, run the local release
gate first:

```console
python maintain.py bootstrap
python maintain.py prepare-release 0.8.1
```

If Windows reports that an existing file under `dist` is in use, close the
terminal, upload dialog, or file preview holding it. To run the same release
gate without replacing that directory, choose another ignored output path:

```console
python maintain.py prepare-release 0.8.1 --output-dir build/release-dist
```

Review `release-manifest.json` and `SHA256SUMS` in the selected output directory.
Install that wheel into a disposable local environment if a final manual smoke
test is useful.

For every data or documentation release, also confirm that:

- Each public field has a clear educational purpose and declared source role.
- Sensitive claims have the review required by
  `EDUCATIONAL_AND_NEUTRALITY_POLICY.md`.
- Examples and release notes use respectful, factual language.
- Naming and border conventions are attributed rather than endorsed.
- `CODE_OF_CONDUCT.md`, source notices, limitations, and correction guidance
  remain publicly linked.

The tag workflow publishes the wheel and source distribution to PyPI, creates a
GitHub Release with checksums and the release manifest, and deploys the Sphinx
site.

Verify the public package in a new environment:

```console
py -3.10 -m venv .venv-live
.venv-live\Scripts\python -m pip install --no-cache-dir pyworldatlas==0.8.1
.venv-live\Scripts\python -c "from pyworldatlas import Atlas; a=Atlas(); print(a.country('Japan').summary()); print(a.quiz(topic='capitals', count=1, seed=8)[0].choices); a.close()"
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

Version 0.8.1 preserves the reviewed 0.8.0 API and dataset while improving
documentation titles, discovery metadata, the favicon, and the shared GitHub
and PyPI README. It must pass the policy-integrity tests alongside the runtime,
pipeline, browser, documentation, and clean-wheel gates.

Never tag a dirty branch or an unmerged candidate. The tag-triggered workflow
is the single path to PyPI, the GitHub Release, and the documentation site.
