# Releasing PyNetDesign

This project uses [`setuptools_scm`](https://setuptools-scm.readthedocs.io), so the package
version is derived from Git tags. Use strict semantic version tags of the form `vX.Y.Z`
(for example `v1.0.1`). Any commit that is not exactly on a tag resolves to a development
version such as `1.0.1.dev3+g1a2b3c4`.

## Versioning rules

- Tags must match `vMAJOR.MINOR.PATCH` exactly. Pre-release and metadata suffixes are
  rejected by CI.
- A release tag must point at a commit contained in `main`. Tags created on other branches
  are rejected during validation.
- Development happens on `dev`; `dev` is merged into `main` through a pull request, and the
  tag is placed on the resulting merge commit on `main`.

## Standard release flow

1. Make sure `dev` is green and up to date with `main`.
2. Update `CHANGELOG.md`: move the relevant `## [Unreleased]` entries into a new
   `## [vX.Y.Z] - YYYY-MM-DD` section and add the comparison links at the bottom.
3. Update `.zenodo.json`: set `version` to the new release and refresh `description` with
   the release highlights.
4. Open and merge the `dev` → `main` pull request.
5. Tag the merge commit on `main` and push the tag:

   ```bash
   git checkout main
   git pull
   git tag -a vX.Y.Z -m "PyNetDesign vX.Y.Z"
   git push origin vX.Y.Z
   ```

6. Verify the version resolves correctly before publishing:

   ```bash
   git describe --tags          # -> vX.Y.Z
   python -m build              # -> dist/pynetdesign-X.Y.Z.tar.gz
   ```

7. Publish the GitHub Release for that tag, using the new `CHANGELOG.md` section as the
   release body.
8. Merge `main` back into `dev` so that `dev` contains the tag in its history and
   `setuptools_scm` resolves a sensible development version there.

## Continuous integration

| Workflow | Trigger | What it does |
| --- | --- | --- |
| `pytest.yml` | push / PR on `main`, `dev` | Runs `pytest pytests/` on Python 3.9-3.12 |
| `validate-zenodo.yml` | push / PR on `main`, `dev`; reusable | Validates `.zenodo.json` against the Zenodo schema |
| `validate-tag.yml` | reusable only | Enforces strict semver and that the tag is contained in `main` |
| `release-on-published.yml` | GitHub Release `published` | Validates the tag, validates the Zenodo metadata, then builds and checks the distributions |

`release-on-published.yml` also accepts a `workflow_dispatch` with a `tag` input, so a
release can be re-validated without republishing it.

Notes:

- Zenodo metadata validation must pass before the package build starts.
- Tag validation is shared through `validate-tag.yml`, so the same rules apply to every
  workflow that acts on a tag.
- PyNetDesign is not published to PyPI. Installation is from source; see `README.md`.

## Zenodo

The repository is archived on Zenodo through the GitHub integration.

- GitHub repository ID: `958300487`
- Original manual deposit (v1.0.0): [10.5281/zenodo.14945917](https://doi.org/10.5281/zenodo.14945917)

### One-time integration setup

1. Sign in to <https://zenodo.org> (test the flow on <https://sandbox.zenodo.org> first if
   you prefer).
2. In Zenodo's GitHub settings, enable the `PyNetDesign` repository.
3. Confirm the repository has a valid `.zenodo.json` — `validate-zenodo.yml` checks this on
   every push.

> **Important:** v1.0.0 was deposited manually before the GitHub integration existed.
> The integration was therefore enabled only *after* the `v1.0.0` GitHub release was
> published, so that Zenodo would not mint a second, duplicate DOI for that version. The
> first integration-created deposit is `v1.0.1`, which starts a new concept DOI.

### Per-release checklist

1. **Before tagging** — update `.zenodo.json` (`version`, `description`, `keywords`,
   `creators`, `related_identifiers` as needed) and make sure `LICENSE` and `README.md`
   are consistent with the release notes.
2. **Create the release** — push the `vX.Y.Z` tag, then publish the GitHub Release with
   the highlights from `CHANGELOG.md`.
3. **Validate the deposition** — confirm Zenodo auto-created a new versioned deposition
   from the GitHub release, and check the title, version, creators, ORCID, license and
   description in the Zenodo UI. Verify the source archive is attached.
4. **Communicate the DOIs** — copy the version DOI and the concept DOI into the release
   notes, `README.md` and `docs/source/citing.rst`. The concept DOI always resolves to the
   latest version; the version DOI pins one release.
5. **Post-release verification** — open the DOI link, check that the citation metadata
   resolves, and confirm the new version appears under the concept record.

### Linking the pre-integration record

Because the manual v1.0.0 deposit and the integration-created records are separate Zenodo
lineages, they must be cross-linked by hand in both directions:

- **Forward**, in the repository: `.zenodo.json` carries a `related_identifiers` entry with
  relation `isNewVersionOf` pointing at `10.5281/zenodo.14945917`. Zenodo honours this on
  every deposit, so it persists across releases.
- **Backward**, on Zenodo: open record `14945917`, choose *Edit*, add a related identifier
  with relation `isPreviousVersionOf` pointing at the new version DOI, and publish. This is
  a metadata-only edit and preserves the existing DOI.
