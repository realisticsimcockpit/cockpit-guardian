# Device Catalog

Cockpit Guardian classifies HID/USB devices through an editable JSON catalog.

On first launch the bundled catalog is copied to:

`%APPDATA%\Cockpit Guardian\device_catalog.json`

Edit that file to add or adjust products without rebuilding the app. Restart Cockpit Guardian after editing.

Example:

```json
{
  "name": "My Pedal Set",
  "kind": "pedals",
  "vid": "1234",
  "pid": "ABCD"
}
```

Use `vid` and `pid` for exact USB matches. Use `name_contains` when the same product can appear with several USB IDs:

```json
{
  "name": "My Button Wheel",
  "kind": "steering_wheel",
  "name_contains": ["my button wheel", "my gt rim"]
}
```

Supported `kind` values:

- `wheel`: wheel base / direct-drive base
- `steering_wheel`: USB wheel rim, button wheel, Formula/GT wheel
- `pedals`
- `shifter`
- `handbrake`
- `button_box`
- `ddu`
- `arduino_simhub`
- `wind_simulator`
- `other`
