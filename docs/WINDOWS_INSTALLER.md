# Windows Installer

Cockpit Guardian uses a standalone Windows build plus an Inno Setup installer.
This is intentionally not a one-file executable: one-file bundles are convenient,
but they generally start slower because they extract files before launching.

## Build Requirements

- Windows 10 or 11, 64-bit.
- Python 3.12.
- Inno Setup 7, available through `winget install --id JRSoftware.InnoSetup.7 -e -s winget -i`.

## Build

From the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File .\packaging\windows\build_installer.ps1
```

Outputs:

- Standalone application: `build\windows\CockpitGuardian`
- Installer: `dist\CockpitGuardianSetup-0.1.0.exe`

The installer version is read from `pyproject.toml`, so no manual edit is needed
when creating a release.

To build only the standalone application:

```powershell
powershell -ExecutionPolicy Bypass -File .\packaging\windows\build_installer.ps1 -SkipInstaller
```

## Runtime Performance Choices

- Build mode is `standalone`, not `onefile`, to avoid startup extraction.
- The Windows console is disabled for lower visual noise and cleaner startup.
- Qt WebEngine and unrelated UI stacks are not imported by the app.
- Installed software and USB event scans are cached by default.
- HID detection has a short in-memory cache to avoid duplicate PowerShell scans
  during startup and after saving a configuration.
- Deep Windows serial metadata scans are disabled by default and can be enabled
  in Settings when troubleshooting COM identity issues.

## Installer Notes

The installer runs with standard user privileges by default. Restore actions that
need administrator rights should request elevation only for those actions rather
than forcing the entire UI to run elevated.

The optional startup task creates a shortcut in the current user's Startup folder.
The installer publisher is `Realistic Sim Cockpit`, and support/update URLs point
to the GitHub repository.

## Sources Checked

- Qt for Python `pyside6-deploy` documentation:
  https://doc.qt.io/qtforpython-6/deployment/deployment-pyside6-deploy.html
- Qt for Python and Nuitka documentation:
  https://doc.qt.io/qtforpython-6/deployment/deployment-nuitka.html
- Nuitka standalone use case:
  https://nuitka.net/user-documentation/use-cases.html
- Inno Setup command-line compiler:
  https://jrsoftware.org/ishelp/topic_compilercmdline.htm
- Inno Setup downloads:
  https://jrsoftware.org/isdl.php/Inno-Setup-Downloads
