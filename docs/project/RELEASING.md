# Maintainer release process

PyWorldAtlas builds, verifies, publishes, and documents each release from one
Git tag. PyPI publishing uses short-lived Trusted Publishing credentials; no
PyPI API token is stored in GitHub.

## What a release publishes

Each release publishes one PyPI project and attaches data packs to the GitHub
release:

| Artifact | Where | Purpose |
|---|---|---|
| `pyworldatlas` wheel and sdist | PyPI | Dependency-free package, atlas database, and map viewer |
| `pyworldatlas-maps.pack` | GitHub release | Standard 3D map data and renderer |
| `pyworldatlas-maps-lite.pack` | GitHub release | Overview 3D map data and renderer |

Packs are built byte for byte reproducibly from `packs/` by
`python maintain.py packs`, which also records their SHA-256 checksums in
`src/pyworldatlas/_pack_index.json`. The library accepts only packs with those
checksums and downloads them from the release that matches its own version.

The `pyworldatlas-mapview` and `pyworldatlas-mapdata-*` PyPI projects were last
published at 0.9.5 and are no longer released.

## One-time repository setup

The canonical source repository is `jcari-dev/pyworldatlas`. Pushes and pull
requests to `main` run CI on Python 3.10 through 3.14, plus the complete wheel,
example, map-rendering, and documentation gate on Python 3.12.

Create one protected GitHub environment named `pypi`. Requiring maintainer
approval before deployment is recommended.

On the PyPI **Publishing** page for `pyworldatlas`, configure a GitHub Actions
trusted publisher with owner `jcari-dev`, repository `pyworldatlas`, workflow
`release.yml`, and environment `pypi`. The publishing job receives only the
wheel and source distribution.

## Documentation deployment

Create a fine-grained GitHub personal access token restricted to
`jcari-dev/pyworldatlas-documentation` with **Contents: Read and write**. Add it
to the source repository as an Actions secret named `DOCS_DEPLOY_TOKEN`.

The release workflow builds Sphinx from the exact release wheels and replaces
the generated files in the documentation repository. Source documentation
remains in this repository under `docs/source/`.

Each release deploys its own documentation from the release workflow after
the package is published. Merges to `main` do not deploy, so the public site
never describes unreleased features.

Documentation-only fixes do not require a new PyPI version. Commit the fix to a
branch made from the release tag, then run **Actions > Documentation > Run
workflow** and choose that branch under **Use workflow from**. Do not run it from
`main` while `main` holds unreleased work. The workflow also refuses to deploy
when the source version is not on PyPI.

## Prepare version 0.9.5

From the repository root on a focused release branch:

```console
python maintain.py bootstrap
python maintain.py prepare-release 0.9.5
git status
git add -A
git commit -m "Prepare PyWorldAtlas 0.9.5"
git push -u origin HEAD
```

Open a pull request from the release branch into `main`. Wait for every CI job to
pass, review the changed source and generated artifacts, and merge the pull
request. Do not create the release tag from the release branch.

If Windows reports that a file under `dist` is in use, close the terminal,
upload dialog, or file preview holding it. A separate ignored output directory
can also be used:

```console
python maintain.py prepare-release 0.9.5 --output-dir build/release-dist
```

## Tag and publish

After the pull request is merged, tag the exact merged `main` commit. Run each
command separately and stop immediately if any command fails:

```console
git switch main
git pull --ff-only origin main
python maintain.py prepare-release 0.9.5
git status
git tag -a v0.9.5 -m "Release 0.9.5"
git push origin v0.9.5
```

Before creating the tag, the release command must finish successfully and
`git status` must show a clean `main` branch. Confirm that `pyproject.toml`
contains the requested version. Do not paste these commands into a shell mode
that continues after a failed command; an incorrect tag can otherwise start a
release workflow from the previous version.

The tag starts the release workflow. Approve the protected PyPI environments
when GitHub requests it. The workflow must complete these outcomes:

1. Build and audit the wheel and source distribution, and rebuild the data
   packs, failing if their checksums differ from the pinned index.
2. Publish `pyworldatlas` to PyPI.
3. Create the GitHub Release with the distributions, data packs, checksums, and
   manifest.
4. Build and deploy the public documentation from the release wheel.

## Verify the public release

Create a clean environment, install the package from PyPI, and download the
map pack from the new GitHub release:

```console
py -3.10 -m venv .venv-live
.venv-live\Scripts\python -m pip install --no-cache-dir "pyworldatlas==VERSION"
.venv-live\Scripts\pyworldatlas --version
.venv-live\Scripts\pyworldatlas get maps
.venv-live\Scripts\python -c "from pyworldatlas import Atlas; a=Atlas(); m=a.map('Brazil'); print(a.dataset_info().library_version, m.quality, m.resolution_arc_minutes); p=m.write_html('brazil-map.html'); print(p); a.close()"
```

Open `brazil-map.html` and confirm that the terrain rotates and both Elevation
and Climate controls work. Then verify:

- <https://github.com/jcari-dev/pyworldatlas/actions>
- <https://github.com/jcari-dev/pyworldatlas/releases>
- <https://pypi.org/project/pyworldatlas/>
- <https://jcari-dev.github.io/pyworldatlas-documentation/>

## Release rules

For every data or documentation release, confirm that:

- Each public field has a clear educational purpose and declared source role.
- Sensitive claims have the review required by
  `EDUCATIONAL_AND_NEUTRALITY_POLICY.md`.
- Examples and release notes use respectful, factual language.
- Naming and border conventions are attributed rather than endorsed.
- Source notices, limitations, correction guidance, and community standards
  remain publicly linked.

Keep `pyproject.toml`, `src/pyworldatlas/_version.py`, companion-project
versions, `docs/source/conf.py`, and `CHANGELOG.md` synchronized. Regenerate
status artifacts when package or coverage metadata changes.

Never reuse, delete, or move a published version tag. If publication fails
before PyPI accepts the version, repair the workflow and rerun it. If PyPI has
accepted the version, preserve it and publish corrections as a patch release.
Never tag a dirty branch or an unmerged candidate.
