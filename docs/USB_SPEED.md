# USB Speed Scan

Cockpit Guardian can infer a USB path from Windows PnP metadata, but this is not the same thing as the negotiated device speed.

Windows PnP can expose identifiers, parent hubs, and location paths. It does not reliably expose whether the device is currently negotiated as Low-Speed, Full-Speed, High-Speed, SuperSpeed, or faster.

Use a USBView-level scan for the first real cockpit audit:

- USB Device Tree Viewer / USBTreeView: portable, fast, and easier to deploy than the Windows Driver Kit.
- Microsoft USBView: official Microsoft viewer, usually installed with Windows debugging tools or SDK/WDK components.

In the app, `USB speed scan needed` means the device has a USB identity but Cockpit Guardian has not yet received hub-level speed data. It is better to show that honestly than to display a fake speed from VID/PID or PnP identity alone.
