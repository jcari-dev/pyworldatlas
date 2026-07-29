# Maintainer release process

PyWorldAtlas builds, verifies, publishes, and documents each release from one
Git tag. PyPI publishing uses short-lived Trusted Publishing credentials; no
PyPI API token is stored in GitHub.

## What version 0.9 publishes

The 0.9 release consists of four coordinated PyPI projects:

| Project | Purpose |
|---|---|
| `pyworldatlas` | Dependency-free core package and atlas database |
| `pyworldatlas-mapview` | Plotly-based browser viewer |
| `pyworldatlas-mapdata-overview` | Compact global map edition |
| `pyworldatlas-mapdata-standard` | Recommended global map edition |

All four projects use the same version. The `maps-overview` and `maps` extras
on the core package install the correct viewer and data project.

## One-time repository setup

The canonical source repository is `jcari-dev/pyworldatlas`. Pushes and pull
requests to `main` run CI on Python 3.10 through 3.14, plus the complete wheel,
example, map-rendering, and documentation gate on Python 3.12.

Create four protected GitHub environments. Requiring maintainer approval before
deployment is recommended.

| PyPI project | GitHub environment |
|---|---|
| `pyworldatlas` | `pypi` |
| `pyworldatlas-mapview` | `pypi-mapview` |
| `pyworldatlas-mapdata-overview` | `pypi-maps-overview` |
| `pyworldatlas-mapdata-standard` | `pypi-maps-standard` |

On the **Publishing** page for each PyPI project, configure a GitHub Actions
trusted publisher with owner `jcari-dev`, repository `pyworldatlas`, workflow
`release.yml`, and the environment listed above. The distinct environment names
allow all three new companion projects to be registered as pending publishers
at the same time.

For a companion project that does not exist yet, create its pending trusted
publisher on PyPI before pushing the first release tag. The first successful
publication creates the project. Each publishing job receives only the two
distribution files that belong to its project.

## Documentation deployment

Create a fine-grained GitHub personal access token restricted to
`jcari-dev/pyworldatlas-documentation` with **Contents: Read and write**. Add it
to the source repository as an Actions secret named `DOCS_DEPLOY_TOKEN`.

The release workflow builds Sphinx from the exact release wheels and replaces
the generated files in the documentation repository. Source documentation
remains in this repository under `docs/source/`.

Documentation-only changes do not require a new PyPI version. Changes to the
documentation, examples, runtime documentation surface, or map viewer run the
dedicated documentation workflow after they are merged to `main`. That workflow
deploys only when the version in the source tree is already available on PyPI;
new-release documentation is deployed by the release workflow after package
publication succeeds.

## Prepare version 0.9.3

From the repository root on a focused release branch:

```console
python maintain.py bootstrap
python maintain.py prepare-release 0.9.3
git status
git add -A
git commit -m "Prepare PyWorldAtlas 0.9.3"
git push -u origin HEAD
```

Open a pull request from the release branch into `main`. Wait for every CI job to
pass, review the changed source and generated artifacts, and merge the pull
request. Do not create the release tag from the release branch.

If Windows reports that a file under `dist` is in use, close the terminal,
upload dialog, or file preview holding it. A separate ignored output directory
can also be used:

```console
python maintain.py prepare-release 0.9.3 --output-dir build/release-dist
```

## Tag and publish

After the pull request is merged, tag the exact merged `main` commit:

```console
git switch main
git pull --ff-only origin main
python maintain.py prepare-release 0.9.3
git status
git tag -a v0.9.3 -m "Release 0.9.3"
git push origin v0.9.3
```

The tag starts the release workflow. Approve the protected PyPI environments
when GitHub requests it. The workflow must complete these outcomes:

1. Build and audit four wheels and four source distributions.
2. Publish all four coordinated projects to PyPI.
3. Create the GitHub Release with distributions, checksums, and manifest.
4. Build and deploy the public documentation from the release wheels.

## Verify the public release

Create a clean environment and install the recommended map edition from PyPI:

```console
py -3.10 -m venv .venv-live
.venv-live\Scripts\python -m pip install --no-cache-dir "pyworldatlas[maps]==0.9.3"
.venv-live\Scripts\python -c "from pyworldatlas import Atlas; a=Atlas(); m=a.map('Brazil'); print(a.dataset_info().library_version, m.quality, m.resolution_arc_minutes); p=m.write_html('brazil-map.html'); print(p); a.close()"
```

Open `brazil-map.html` and confirm that the terrain rotates and both Elevation
and Climate controls work. Then verify:

- <https://github.com/jcari-dev/pyworldatlas/actions>
- <https://github.com/jcari-dev/pyworldatlas/releases>
- <https://pypi.org/project/pyworldatlas/>
- <https://pypi.org/project/pyworldatlas-mapview/>
- <https://pypi.org/project/pyworldatlas-mapdata-overview/>
- <https://pypi.org/project/pyworldatlas-mapdata-standard/>
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
