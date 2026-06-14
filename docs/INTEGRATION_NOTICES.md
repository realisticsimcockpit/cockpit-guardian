# Integration Notices

These notes describe the assumptions Cockpit Guardian makes for SimHub, Arduino,
ESP boards, and Windows restore actions.

Vendor application/API checks are tracked in
[`VENDOR_API_NOTICES.md`](VENDOR_API_NOTICES.md). That file documents which
manufacturer tools can be handled through safe Windows/HID/USB detection and
which ones may justify a deeper official SDK integration.

## SimHub

SimHub Custom Serial Devices must be enabled and configured by the user. The
plugin lets SimHub drive serial devices by defining a protocol, but it is not
enabled by default. It also does not add predefined start or terminator
characters; the protocol must include them when the device firmware expects
them.

FFB clipping is treated as optional telemetry. Cockpit Guardian can show the
value when an adapter/plugin provides it, but a missing SimHub signal must not
block the cockpit check unless SimHub is marked as required in Settings.

## Arduino

Arduino boards can be identified through serial-port metadata such as COM port,
VID, PID, USB serial number, manufacturer, product, friendly name, location path,
and device instance ID.

Do not rely on VID/PID alone for boards using generic USB-to-serial bridges such
as CH340, CP210x, FTDI, or PL2303. Those bridge chips can report the same VID/PID
for many unrelated boards. Cockpit Guardian therefore avoids treating a generic
bridge VID/PID match as a safe device match unless a serial number, device
instance ID, or saved USB location also matches.

## ESP / ESP32

Many ESP boards appear as USB-to-UART bridges instead of board-specific USB
devices. Espressif documents CP210x and FTDI bridges for ESP32 boards, and many
third-party boards also use CH340-class bridges.

When an ESP board has no USB serial number, Cockpit Guardian uses the Windows
device instance ID and USB location when available. Moving that board to another
hub or USB port can therefore legitimately trigger a warning.

## Windows

Windows device instance IDs are assigned by Plug and Play and are expected to be
persistent across restarts. Cockpit Guardian stores them in the snapshot whenever
available.

Operations such as USB rescan or COM port restoration can require administrator
rights. Cockpit Guardian creates a backup before each restore attempt and reports
clearly when elevation is required.

## USB 2 / USB 3 Detection

Cockpit Guardian shows USB generation information on the Dashboard when Windows
exposes enough topology data.

There are two levels of USB information:

- Reliable negotiated speed: requires querying the USB hub with Windows USB IOCTLs,
  the same family of APIs used by USBView.
- Lightweight dashboard hint: uses Plug and Play topology strings such as USB 3
  root hubs, xHCI controllers, high-speed hints, and USB serial bridge IDs.

The Dashboard therefore uses confidence labels:

- `medium`: Windows topology suggests a USB 2.0 or USB 3.x path.
- `low`: the device is a generic USB serial bridge such as CH340, CP210x, FTDI,
  or PL2303, and PnP alone does not expose negotiated speed.
- `unknown`: Cockpit Guardian cannot infer the USB generation without a deeper
  USBView-level hub query.

This is useful for spotting obvious problems, for example a saved cockpit device
that used to be on a USB 3 path and is now only visible through a USB 2 path. It
should not be treated as a lab-grade USB speed measurement.

For the best topology hints, enable `Deep Windows scan` in Settings. With the
default lightweight scan, Cockpit Guardian avoids extra PowerShell/PnP queries and
may show `USB speed unknown` for devices that require hub topology data.

Cockpit Guardian runs one Deep Windows scan automatically on first launch so the
initial cockpit baseline captures richer USB topology. The Settings toggle remains
available for later hardware changes, such as adding a USB hub or moving devices.
If no configuration has been saved yet, the first startup check can use the deep
scan without marking the baseline as complete; the first `Save Configuration`
still captures a deep scan. Imported config backups also reset this first-scan
flag for the new Windows installation.

## Sources Checked

- SimHub Custom Serial Devices wiki:
  https://github.com/SHWotever/SimHub/wiki/Custom-serial-devices
- pySerial list_ports documentation:
  https://pyserial.readthedocs.io/en/latest/tools.html
- ESP-IDF ESP32 serial connection documentation:
  https://docs.espressif.com/projects/esp-idf/en/stable/esp32/get-started/establish-serial-connection.html
- Arduino CLI FAQ:
  https://docs.arduino.cc/arduino-cli/FAQ/
- Arduino CLI pluggable discovery specification:
  https://docs.arduino.cc/arduino-cli/pluggable-discovery-specification
- Arduino platform VID/PID specification:
  https://docs.arduino.cc/arduino-cli/platform-specification/
- Microsoft Win32_SerialPort:
  https://learn.microsoft.com/en-us/windows/win32/cimwin32prov/win32-serialport
- Microsoft Win32_PnPEntity:
  https://learn.microsoft.com/en-us/windows/win32/cimwin32prov/win32-pnpentity
- Microsoft device instance IDs:
  https://learn.microsoft.com/en-us/windows-hardware/drivers/install/device-instance-ids
- Microsoft PnPUtil syntax:
  https://learn.microsoft.com/en-us/windows-hardware/drivers/devtest/pnputil-command-syntax
- Microsoft USBView:
  https://learn.microsoft.com/en-us/windows-hardware/drivers/debugger/usbview
- Microsoft IOCTL_USB_GET_NODE_CONNECTION_INFORMATION_EX_V2:
  https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/usbioctl/ni-usbioctl-ioctl_usb_get_node_connection_information_ex_v2
- Microsoft USB_NODE_CONNECTION_INFORMATION_EX_V2:
  https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/usbioctl/ns-usbioctl-_usb_node_connection_information_ex_v2
