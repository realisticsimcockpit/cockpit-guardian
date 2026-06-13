from __future__ import annotations

import hashlib
import os
import time
from dataclasses import dataclass, field

from ..models import CockpitDevice, DeviceBus, DeviceKind, HidIdentity, SerialIdentity
from .integration_notices import ARDUINO_VIDS, ESPRESSIF_VIDS, generic_usb_serial_bridge_name, normalize_usb_id
from .windows_util import parse_vid_pid, run_powershell_json


def _stable_id(*parts: object) -> str:
    text = "|".join(str(part or "") for part in parts)
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:16]


def _guess_kind(name: str | None, bus: DeviceBus, vid: str | None = None, pid: str | None = None) -> DeviceKind:
    normalized = (name or "").lower()
    checks = [
        (DeviceKind.WHEEL, ["wheel", "wheelbase", "simagic", "moza", "fanatec", "simucube", "alpha"]),
        (DeviceKind.PEDALS, ["pedal", "heusinkveld", "p1000", "p2000", "clubsport"]),
        (DeviceKind.SHIFTER, ["shifter", "seq", "h-pattern"]),
        (DeviceKind.HANDBRAKE, ["handbrake", "hand brake"]),
        (DeviceKind.BUTTON_BOX, ["button", "stream deck", "box"]),
        (DeviceKind.DDU, ["ddu", "dash", "display"]),
        (DeviceKind.ARDUINO_SIMHUB, ["arduino", "simhub"]),
        (DeviceKind.WIND_SIMULATOR, ["wind", "fan"]),
    ]
    for kind, needles in checks:
        if any(needle in normalized for needle in needles):
            return kind
    normalized_vid = normalize_usb_id(vid)
    if normalized_vid in ESPRESSIF_VIDS or any(token in normalized for token in ["esp32", "esp8266", "espressif"]):
        return DeviceKind.ARDUINO_SIMHUB
    if normalized_vid in ARDUINO_VIDS or any(token in normalized for token in ["arduino", "genuino"]):
        return DeviceKind.ARDUINO_SIMHUB
    if bus == DeviceBus.SERIAL and generic_usb_serial_bridge_name(vid, pid):
        return DeviceKind.ARDUINO_SIMHUB
    if bus == DeviceBus.SERIAL:
        return DeviceKind.OTHER
    return DeviceKind.OTHER


@dataclass(slots=True)
class DeviceDetector:
    """Collects cockpit-relevant serial and HID devices.

    The detector uses pyserial and PowerShell where available. It intentionally
    returns empty lists instead of raising when a backend is unavailable so the UI
    can still explain the current state.
    """

    _hid_cache: list[CockpitDevice] = field(default_factory=list)
    _hid_cache_at: float = 0.0
    _serial_metadata_cache: dict[str, dict[str, str | None]] = field(default_factory=dict)
    _serial_metadata_cache_at: float = 0.0

    def detect_all(self, include_windows_metadata: bool = False, hid_cache_ttl_seconds: int = 5) -> list[CockpitDevice]:
        if os.environ.get("COCKPIT_GUARDIAN_MOCK") == "1":
            return self._mock_devices()
        devices = self.detect_serial_devices(include_windows_metadata=include_windows_metadata)
        devices.extend(self.detect_hid_devices(cache_ttl_seconds=hid_cache_ttl_seconds))
        return devices

    def detect_serial_devices(self, include_windows_metadata: bool = False) -> list[CockpitDevice]:
        try:
            from serial.tools import list_ports
        except Exception:
            return []

        detected: list[CockpitDevice] = []
        windows_metadata = self._windows_serial_metadata(cache_ttl_seconds=30) if include_windows_metadata else {}
        for port in list_ports.comports():
            metadata = windows_metadata.get(str(port.device).upper(), {})
            vid = f"{port.vid:04X}" if port.vid is not None else None
            pid = f"{port.pid:04X}" if port.pid is not None else None
            friendly = metadata.get("friendly_name") or port.description or port.name or port.device
            identity = SerialIdentity(
                current_com=port.device,
                vid=vid,
                pid=pid,
                serial_number=port.serial_number or metadata.get("serial_number"),
                manufacturer=metadata.get("manufacturer") or port.manufacturer,
                product=metadata.get("product") or port.product,
                friendly_name=friendly,
                location_path=metadata.get("location_path") or getattr(port, "location", None),
                device_instance_id=metadata.get("device_instance_id") or getattr(port, "hwid", None),
            )
            device_id = _stable_id("serial", identity.device_instance_id, identity.serial_number, vid, pid, port.device)
            detected.append(
                CockpitDevice(
                    id=device_id,
                    display_name=friendly,
                    kind=_guess_kind(friendly, DeviceBus.SERIAL, vid, pid),
                    bus=DeviceBus.SERIAL,
                    serial=identity,
                )
            )
        return detected

    def detect_hid_devices(self, cache_ttl_seconds: int = 5) -> list[CockpitDevice]:
        now = time.monotonic()
        if self._hid_cache and now - self._hid_cache_at <= max(0, cache_ttl_seconds):
            return list(self._hid_cache)
        script = (
            "Get-PnpDevice -PresentOnly | "
            "Where-Object { $_.Class -in @('HIDClass','USB','MEDIA') -and "
            "($_.FriendlyName -match 'wheel|pedal|joystick|game|shifter|handbrake|button|simagic|moza|fanatec|simucube|ddu|arduino') } | "
            "Select-Object FriendlyName, InstanceId, Manufacturer, Status, Class"
        )
        rows = run_powershell_json(script)
        devices: list[CockpitDevice] = []
        for index, row in enumerate(rows):
            instance_id = row.get("InstanceId")
            name = row.get("FriendlyName") or row.get("Manufacturer") or "HID device"
            vid, pid = parse_vid_pid(instance_id)
            identity = HidIdentity(
                name=name,
                vid=vid,
                pid=pid,
                device_instance_id=instance_id,
                joystick_order=index + 1,
            )
            devices.append(
                CockpitDevice(
                    id=_stable_id("hid", instance_id, name, vid, pid),
                    display_name=name,
                    kind=_guess_kind(name, DeviceBus.HID, vid, pid),
                    bus=DeviceBus.HID,
                    hid=identity,
                )
            )
        self._hid_cache = list(devices)
        self._hid_cache_at = now
        return devices

    def _windows_serial_metadata(self, cache_ttl_seconds: int = 30) -> dict[str, dict[str, str | None]]:
        now = time.monotonic()
        if self._serial_metadata_cache and now - self._serial_metadata_cache_at <= max(0, cache_ttl_seconds):
            return dict(self._serial_metadata_cache)
        script = (
            "Get-CimInstance Win32_SerialPort | "
            "Select-Object DeviceID, PNPDeviceID, Manufacturer, Description, Name"
        )
        metadata: dict[str, dict[str, str | None]] = {}
        for row in run_powershell_json(script, timeout=10):
            device_id = str(row.get("DeviceID") or "").upper()
            if not device_id:
                continue
            pnp_id = row.get("PNPDeviceID")
            metadata[device_id] = {
                "device_instance_id": pnp_id,
                "manufacturer": row.get("Manufacturer"),
                "product": row.get("Description"),
                "friendly_name": row.get("Name") or row.get("Description"),
                "serial_number": self._serial_from_instance_id(str(pnp_id or "")),
                "location_path": None,
            }
        self._serial_metadata_cache = dict(metadata)
        self._serial_metadata_cache_at = now
        return metadata

    @staticmethod
    def _serial_from_instance_id(instance_id: str) -> str | None:
        if not instance_id or "\\" not in instance_id:
            return None
        return instance_id.rsplit("\\", 1)[-1] or None

    @staticmethod
    def _mock_devices() -> list[CockpitDevice]:
        return [
            CockpitDevice(
                id="mock-wheel",
                display_name="Simagic Alpha Ultimate",
                kind=DeviceKind.WHEEL,
                bus=DeviceBus.HID,
                hid=HidIdentity(name="Simagic Alpha Ultimate", vid="0483", pid="A355", joystick_order=1),
            ),
            CockpitDevice(
                id="mock-pedals",
                display_name="mBooster Active Pedals",
                kind=DeviceKind.PEDALS,
                bus=DeviceBus.HID,
                hid=HidIdentity(name="mBooster Active Pedals", vid="3416", pid="0301", joystick_order=2),
            ),
            CockpitDevice(
                id="mock-ddu",
                display_name="DDU",
                kind=DeviceKind.DDU,
                bus=DeviceBus.SERIAL,
                serial=SerialIdentity(
                    current_com="COM5",
                    vid="2341",
                    pid="0043",
                    serial_number="CG-MOCK-DDU",
                    manufacturer="Arduino",
                    product="DDU",
                    friendly_name="DDU",
                    location_path="MOCK-USB-1",
                    device_instance_id="USB\\VID_2341&PID_0043\\CG-MOCK-DDU",
                ),
            ),
            CockpitDevice(
                id="mock-wind",
                display_name="Wind Simulator",
                kind=DeviceKind.WIND_SIMULATOR,
                bus=DeviceBus.SERIAL,
                serial=SerialIdentity(
                    current_com="COM8",
                    vid="1A86",
                    pid="7523",
                    serial_number="CG-MOCK-WIND",
                    manufacturer="wch.cn",
                    product="USB-SERIAL CH340",
                    friendly_name="Wind Simulator",
                    location_path="MOCK-USB-2",
                    device_instance_id="USB\\VID_1A86&PID_7523\\CG-MOCK-WIND",
                ),
            ),
        ]
