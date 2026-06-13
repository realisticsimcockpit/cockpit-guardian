from __future__ import annotations

from dataclasses import dataclass


GENERIC_USB_SERIAL_BRIDGES: dict[tuple[str, str], str] = {
    ("0403", "6001"): "FTDI FT232 USB serial bridge",
    ("0403", "6015"): "FTDI USB serial bridge",
    ("067B", "2303"): "Prolific PL2303 USB serial bridge",
    ("10C4", "EA60"): "Silicon Labs CP210x USB-to-UART bridge",
    ("1A86", "7523"): "WCH CH340 USB serial bridge",
    ("1A86", "5523"): "WCH CH341 USB serial bridge",
    ("1A86", "55D4"): "WCH CH9102 USB serial bridge",
    ("303A", "1001"): "Espressif USB JTAG/serial bridge",
}

ARDUINO_VIDS = {"2341", "2A03", "1B4F", "239A"}
ESPRESSIF_VIDS = {"303A"}


@dataclass(frozen=True, slots=True)
class IntegrationNotice:
    title: str
    body: str


def normalize_usb_id(value: str | None) -> str | None:
    if not value:
        return None
    normalized = value.upper().replace("0X", "")
    return normalized.zfill(4)[-4:]


def generic_usb_serial_bridge_name(vid: str | None, pid: str | None) -> str | None:
    normalized_vid = normalize_usb_id(vid)
    normalized_pid = normalize_usb_id(pid)
    if not normalized_vid or not normalized_pid:
        return None
    return GENERIC_USB_SERIAL_BRIDGES.get((normalized_vid, normalized_pid))


def is_generic_usb_serial_bridge(vid: str | None, pid: str | None) -> bool:
    return generic_usb_serial_bridge_name(vid, pid) is not None


def serial_identity_notice(vid: str | None, pid: str | None, serial_number: str | None, location_path: str | None) -> str | None:
    bridge_name = generic_usb_serial_bridge_name(vid, pid)
    if not bridge_name:
        return None
    if serial_number:
        return f"{bridge_name} detected with USB serial number."
    if location_path:
        return f"{bridge_name} has no serial number; Cockpit Guardian will rely on the USB location."
    return f"{bridge_name} has no serial number or USB location; automatic COM restore is not safe."


INTEGRATION_NOTICES: tuple[IntegrationNotice, ...] = (
    IntegrationNotice(
        "SimHub Custom Serial",
        "SimHub's Custom Serial Devices plugin must be enabled and configured. It does not send a predefined protocol, start byte, or terminator by default.",
    ),
    IntegrationNotice(
        "Arduino USB Serial",
        "Arduino boards with unique VID/PID can be identified by model. Boards using generic FTDI, CH340, or CP210x bridges may need serial number or stable USB location to avoid false matches.",
    ),
    IntegrationNotice(
        "ESP USB Serial",
        "Many ESP32 boards appear through CP210x, CH340, FTDI, or Espressif USB JTAG/serial bridges. Without a USB serial number, the physical USB port can be part of the identity.",
    ),
    IntegrationNotice(
        "Windows Restore",
        "COM and device restore actions use Windows Plug and Play data and can require administrator rights. A backup is created before every restore attempt.",
    ),
)
