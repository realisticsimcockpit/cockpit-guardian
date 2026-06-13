# Contributing

Thanks for helping improve Cockpit Guardian.

## Development Setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

On Windows:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[windows,dev]"
```

## Checks Before Committing

```bash
python -m compileall -q src tests
python -m pytest -q
```

## Coding Guidelines

- Keep the user interface focused on cockpit readiness, not Windows internals.
- Keep COM, USB, DirectInput, registry, and SetupAPI details inside services.
- Create a backup before any restore action that changes Windows state.
- Avoid heavy Windows scans on every check. Prefer cached or targeted reads.
- Add tests for matching logic, restore decisions, and regression-prone Windows behavior.

## Branches

- `main` contains the current working baseline.
- Feature branches should use short descriptive names such as `feature/simhub-adapter`.
- Pull requests should include test results and screenshots when the UI changes.
