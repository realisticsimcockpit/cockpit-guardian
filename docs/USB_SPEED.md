# USB Speed Scan

Cockpit Guardian can infer a USB path from Windows PnP metadata, but this is not the same thing as the negotiated device speed.

Windows PnP can expose identifiers, parent hubs, and location paths. It does not reliably expose whether the device is currently negotiated as Low-Speed, Full-Speed, High-Speed, SuperSpeed, or faster.

Cockpit Guardian runs a USBView-style scan automatically the first time it sees no cached speed data, then stores the result in:

`%APPDATA%\Cockpit Guardian\usb_speed_cache.json`

The Dashboard also exposes a `USB Speed Scan` button to force a fresh scan after moving hardware, adding a hub, or changing cables.

The integrated scanner follows the same principle as Microsoft USBView: enumerate USB hubs, query each downstream port, and read negotiated speed through Windows hub IOCTLs such as `IOCTL_USB_GET_NODE_CONNECTION_INFORMATION_EX` and `_EX_V2`.

Reference tools:

- USB Device Tree Viewer / USBTreeView: useful external visual checker.
- Microsoft USBView: official sample and source reference.

In the app, `USB speed scan needed` means the device has a USB identity but Cockpit Guardian has not yet received hub-level speed data. It is better to show that honestly than to display a fake speed from VID/PID or PnP identity alone.
