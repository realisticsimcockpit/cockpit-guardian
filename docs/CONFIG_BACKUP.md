# Configuration Backup

Cockpit Guardian is designed for a common simracing problem: Windows has been
reinstalled, and the cockpit needs to be restored quickly.

## Recommended Workflow

1. Connect the cockpit exactly as it should be used.
2. Open Cockpit Guardian.
3. Click `Save Configuration`.
4. Click `Export Config Backup` on the Dashboard.
5. Save the `.json` file in a cloud-synced location such as OneDrive, Google
   Drive, Dropbox, iCloud Drive, or a NAS-synced folder.
6. Reinstall Windows when needed.
7. Install Cockpit Guardian again.
8. Click `Import Config Backup` on the Dashboard.
9. Run `Check Now`.
10. Run `Restore` if Cockpit Guardian reports changed COM ports, joystick order,
    or other restoreable differences.

## What Is Included

The exported backup includes:

- Saved cockpit snapshot.
- Device identities.
- Expected COM ports.
- Joystick order.
- Software statuses saved with the snapshot.
- Cockpit Guardian settings.
- App version used to export the file.
- Export timestamp.

## What Is Not Included

The exported backup does not include:

- Windows drivers.
- SimHub profiles.
- Game settings.
- Vendor software profiles.
- Large logs.

Keep those in their own vendor-specific cloud backups when needed.

## Safety

Importing a backup first creates a local safety backup of the current
configuration. This makes it possible to roll back if the wrong backup file was
selected.
