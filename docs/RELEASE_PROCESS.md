# Release Process

Cockpit Guardian releases are built from GitHub tags.

## Versioning

The current version is stored in:

- `pyproject.toml`
- `src/cockpit_guardian/__init__.py`
- `CHANGELOG.md`

The installer script reads the Python package version and passes it to Inno
Setup, so the installer filename follows the package version.

Publisher, repository URLs, license, GitHub templates, and release automation are
already filled in for `Realistic Sim Cockpit`.

## Local Release Check

```bash
python -m compileall -q src tests
python -m pytest -q
```

## Windows Installer Build

On Windows:

```powershell
powershell -ExecutionPolicy Bypass -File .\packaging\windows\build_installer.ps1
```

## GitHub Release

Create and push a tag:

```bash
git tag v0.1.0
git push origin v0.1.0
```

The `Release` GitHub Actions workflow builds the installer and attaches it to a
GitHub release.

The release workflow can also be started manually from GitHub Actions with
`workflow_dispatch`; tag-based releases are preferred for public versions.
