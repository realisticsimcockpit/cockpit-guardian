# Integration Notices

These notes describe the assumptions Cockpit Guardian makes for SimHub, Arduino,
ESP boards, and Windows restore actions.

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
