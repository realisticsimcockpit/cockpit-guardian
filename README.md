# Cockpit Guardian

[![CI](https://github.com/realisticsimcockpit/cockpit-guardian/actions/workflows/ci.yml/badge.svg)](https://github.com/realisticsimcockpit/cockpit-guardian/actions/workflows/ci.yml)
[![Release](https://github.com/realisticsimcockpit/cockpit-guardian/actions/workflows/release.yml/badge.svg)](https://github.com/realisticsimcockpit/cockpit-guardian/actions/workflows/release.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Cockpit Guardian is a Windows desktop application for simracing cockpit supervision.
Its main question is deliberately simple:

> Is my cockpit ready to race?

The application is built with Python and PySide6. Low-level Windows operations are
kept behind service classes so the UI stays focused on simracing devices instead of
COM ports, registry keys, DirectInput internals, or USB event logs.

## Current scope

This repository contains a working first version with:

- Dashboard, USB Health, Logs, Settings, and Advanced / Debug tabs.
- Save Configuration to a JSON snapshot.
- Automatic check on launch and manual Check Now.
- Device comparison for serial/COM and HID/joystick devices.
- Best-effort USB 2/3 path display on Dashboard device rows.
- Joystick order status on the Dashboard.
- SimHub availability and FFB clipping hook.
- Software detection for common simracing tools.
- Restore engine with backups, COM restore path, USB rescan path, joystick restore hook,
  and Rollback Last Restore.
- Windows system tray status colors and menu actions.
- Non-Windows fallbacks so core logic can be tested on development machines.

Some hardware-specific restore paths need real Windows hardware validation before they
should be considered complete. The code returns explicit messages when an operation
needs administrator rights or when a native API is unavailable.

## Project Status

Version: `0.1.0`

Status: alpha. The application structure, UI, snapshot/check/restore flow, tests,
and Windows installer pipeline are in place. Hardware-specific restore operations
still need validation on a real Windows simracing cockpit before being treated as
production-ready.

## Install

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -e ".[windows,dev]"
```

On macOS/Linux for development only:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

## Run

```bash
cockpit-guardian
```

or:

```bash
python -m cockpit_guardian
```

## Windows Installer

For a fast, low-overhead Windows package, use the standalone Nuitka build plus
Inno Setup installer described in [docs/WINDOWS_INSTALLER.md](docs/WINDOWS_INSTALLER.md).
This project intentionally avoids a one-file bundle for release builds because a
standalone install starts faster and avoids temporary extraction on each launch.

Runtime checks are also tuned to avoid repeated heavy Windows scans: installed
software, USB Health, and HID detection use short caches, and deep Windows serial
metadata enrichment is disabled by default.

## Reinstalling Windows

The Dashboard includes `Export Config Backup` and `Import Config Backup` for the
main recovery workflow after a Windows reinstall. Export the backup to a
cloud-synced folder before reinstalling Windows, then import it after installing
Cockpit Guardian again.

Read [Configuration Backup](docs/CONFIG_BACKUP.md) for the full workflow.

## Data files

Runtime files are stored in the user data directory:

- Windows: `%APPDATA%\Cockpit Guardian`
- Other platforms: `~/.cockpit_guardian`

Important files:

- `snapshot.json`: saved cockpit configuration.
- `settings.json`: user preferences.
- `logs/cockpit_guardian.log`: app log.
- `backups/`: backups created before restore actions.

## Development

Install development dependencies:

```bash
python -m pip install -e ".[dev]"
```

Run tests:

```bash
python -m compileall -q src tests
python -m pytest -q
```

Run with deterministic mock devices:

```bash
COCKPIT_GUARDIAN_MOCK=1 cockpit-guardian
```

## Integration Notices

Read [docs/INTEGRATION_NOTICES.md](docs/INTEGRATION_NOTICES.md) before validating
with real SimHub, Arduino, ESP, or Windows hardware. In short:

- SimHub Custom Serial Devices must be enabled and configured; Cockpit Guardian
  must not assume a default serial protocol.
- Generic USB-to-serial bridges such as CH340, CP210x, FTDI, and PL2303 are not
  unique board identifiers by themselves.
- ESP boards can appear as bridge chips rather than as board-specific devices.
- Windows restore actions can require administrator rights and always create a
  backup first.

## Architecture

Main docs:

- [Architecture](docs/ARCHITECTURE.md)
- [Configuration backup](docs/CONFIG_BACKUP.md)
- [Integration notices](docs/INTEGRATION_NOTICES.md)
- [Windows installer](docs/WINDOWS_INSTALLER.md)
- [Release process](docs/RELEASE_PROCESS.md)
- [Repository setup](docs/REPOSITORY_SETUP.md)
- [Changelog](CHANGELOG.md)
- [Contributing](CONTRIBUTING.md)
- [Security](SECURITY.md)
- [Support](SUPPORT.md)

Main modules:

- `cockpit_guardian.ui`: PySide6 UI, dashboard, tabs, tray integration.
- `cockpit_guardian.controller`: coordinates UI actions.
- `cockpit_guardian.check_engine`: compares current state with the saved snapshot.
- `cockpit_guardian.services.device_detector`: serial and HID detection.
- `cockpit_guardian.services.com_manager`: COM port restore and backups.
- `cockpit_guardian.services.joystick_manager`: joystick order snapshot/check/restore hook.
- `cockpit_guardian.services.usb_health`: USB health summary and event history.
- `cockpit_guardian.services.simhub`: SimHub and FFB clipping integration hook.
- `cockpit_guardian.services.software_detector`: simracing software detection.
- `cockpit_guardian.services.restore_engine`: restore and rollback orchestration.

## License

Cockpit Guardian is released under the [MIT License](LICENSE).
