from __future__ import annotations

import hashlib
import os
import time
import ctypes
import unicodedata
from dataclasses import dataclass, field
from ctypes import wintypes
from typing import Any

from ..models import CockpitDevice, DeviceBus, DeviceKind, HidIdentity, SerialIdentity, UsbConnectionInfo
from .device_catalog import DeviceCatalog
from .integration_notices import ARDUINO_VIDS, ESPRESSIF_VIDS, generic_usb_serial_bridge_name, normalize_usb_id
from .usb_topology import UsbTopologyDetector
from .windows_util import is_windows, parse_vid_pid, run_powershell_json


ACTIVE_PEDAL_USB_IDS = {("303A", "8331"), ("3035", "8213"), ("3035", "8215")}


def _stable_id(*parts: object) -> str:
    text = "|".join(str(part or "") for part in parts)
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:16]


def _guess_kind(
    name: str | None,
    bus: DeviceBus,
    vid: str | None = None,
    pid: str | None = None,
    catalog: DeviceCatalog | None = None,
) -> DeviceKind:
    normalized = _normalized_device_name(name)
    normalized_vid = normalize_usb_id(vid)
    normalized_pid = normalize_usb_id(pid)
    if (normalized_vid == "044F" and normalized_pid == "B687") or "twcs throttle" in normalized:
        return DeviceKind.OTHER
    if (normalized_vid, normalized_pid) in ACTIVE_PEDAL_USB_IDS:
        return DeviceKind.ACTIVE_PEDAL
    if any(token in normalized for token in ["diy_ffb_pedal", "ffb_pedal", "activepedal", "active pedal"]):
        return DeviceKind.ACTIVE_PEDAL
    if any(token in normalized for token in ["seatmover", "seat mover", "motion platform"]):
        return DeviceKind.SEAT_MOVER
    if any(token in normalized for token in ["ambilight", "ambient light"]):
        return DeviceKind.AMBILIGHT

    match = (catalog or DeviceCatalog.load_default()).match(name, vid, pid)
    if match is not None:
        return match.kind
    checks = [
        (DeviceKind.WHEEL, ["wheel base", "wheelbase", "simagic alpha", "moza r", "fanatec", "simucube", "asetek"]),
        (DeviceKind.STEERING_WHEEL, ["steering wheel", "rim", "gt neo", "formula wheel"]),
        (DeviceKind.PEDALS, ["pedal", "heusinkveld", "p1000", "p2000", "clubsport"]),
        (DeviceKind.SHIFTER, ["shifter", "seq", "h-pattern"]),
        (DeviceKind.HANDBRAKE, ["handbrake", "hand brake"]),
        (DeviceKind.BUTTON_BOX, ["button", "stream deck", "box", "gt neo"]),
        (DeviceKind.DDU, ["ddu", "dash", "display"]),
        (DeviceKind.ARDUINO_SIMHUB, ["arduino", "simhub"]),
        (DeviceKind.WIND_SIMULATOR, ["wind", "fan"]),
    ]
    for kind, needles in checks:
        if any(needle in normalized for needle in needles):
            return kind
    if normalized_vid in ESPRESSIF_VIDS or any(token in normalized for token in ["esp32", "esp8266", "espressif"]):
        return DeviceKind.ARDUINO_SIMHUB
    if normalized_vid in ARDUINO_VIDS or any(token in normalized for token in ["arduino", "genuino"]):
        return DeviceKind.ARDUINO_SIMHUB
    if bus == DeviceBus.SERIAL and generic_usb_serial_bridge_name(vid, pid):
        return DeviceKind.ARDUINO_SIMHUB
    if bus == DeviceBus.SERIAL:
        return DeviceKind.OTHER
    return DeviceKind.OTHER


def _normalized_device_name(name: str | None) -> str:
    normalized = unicodedata.normalize("NFKD", str(name or "").strip().lower())
    return "".join(character for character in normalized if not unicodedata.combining(character)).replace("’", "'")


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
    _usb_topology: UsbTopologyDetector = field(default_factory=UsbTopologyDetector)
    _catalog: DeviceCatalog = field(default_factory=DeviceCatalog.load_default)

    def detect_all(self, include_windows_metadata: bool = False, hid_cache_ttl_seconds: int = 5) -> list[CockpitDevice]:
        if os.environ.get("COCKPIT_GUARDIAN_MOCK") == "1":
            return self._mock_devices()
        devices = self.detect_serial_devices(include_windows_metadata=include_windows_metadata)
        devices.extend(self.detect_hid_devices(cache_ttl_seconds=hid_cache_ttl_seconds))
        return self._usb_topology.annotate_devices(devices, include_windows_metadata=include_windows_metadata)

    def detect_serial_devices(self, include_windows_metadata: bool = False) -> list[CockpitDevice]:
        try:
            from serial.tools import list_ports
        except Exception:
            return []

        detected: list[CockpitDevice] = []
        windows_metadata = self._windows_serial_metadata(cache_ttl_seconds=30) if include_windows_metadata else {}
        for port in list_ports.comports():
            metadata = windows_metadata.get(str(port.device).upper(), {})
            if not self._is_usb_serial_port(port, metadata):
                continue
            vid = f"{port.vid:04X}" if port.vid is not None else None
            pid = f"{port.pid:04X}" if port.pid is not None else None
            friendly = metadata.get("friendly_name") or port.description or port.name or port.device
            catalog_match = self._catalog.match(friendly, vid, pid)
            if (vid, pid) in ACTIVE_PEDAL_USB_IDS:
                catalog_name = "DIY Active Pedal"
            else:
                catalog_name = catalog_match.name if catalog_match else None
            if catalog_name and self._is_generic_device_name(friendly):
                friendly = f"{catalog_name} ({port.device})"
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
                    kind=_guess_kind(friendly, DeviceBus.SERIAL, vid, pid, self._catalog),
                    bus=DeviceBus.SERIAL,
                    serial=identity,
                )
            )
        return detected

    def detect_hid_devices(self, cache_ttl_seconds: int = 5) -> list[CockpitDevice]:
        now = time.monotonic()
        if self._hid_cache and now - self._hid_cache_at <= max(0, cache_ttl_seconds):
            return list(self._hid_cache)
        joystick_pnp_rows = self._windows_joystick_pnp_rows()
        devices = self._detect_winmm_joysticks(joystick_pnp_rows)
        known_instance_ids = {
            device.hid.device_instance_id.upper()
            for device in devices
            if device.hid and device.hid.device_instance_id and not device.hid.device_instance_id.upper().startswith("WINMM\\")
        }
        script = (
            "Get-PnpDevice -PresentOnly | "
            "Where-Object { $_.Class -eq 'HIDClass' -and "
            "($_.FriendlyName -match 'wheel|pedal|shifter|throttle|yoke|handbrake|button|stream deck|simagic|moza|fanatec|simucube|ddu|arduino') } | "
            "Select-Object FriendlyName, InstanceId, Manufacturer, Status, Class"
        )
        rows = run_powershell_json(script)
        if not devices:
            rows = joystick_pnp_rows + rows
        for index, row in enumerate(rows):
            instance_id = row.get("InstanceId")
            if instance_id and str(instance_id).upper() in known_instance_ids:
                continue
            if devices and self._is_generic_game_controller_row(row):
                continue
            name = row.get("FriendlyName") or row.get("Manufacturer") or "HID device"
            vid, pid = parse_vid_pid(instance_id)
            catalog_match = self._catalog.match(name, vid, pid)
            if catalog_match and catalog_match.name and self._is_generic_device_name(name):
                name = catalog_match.name
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
                    kind=_guess_kind(name, DeviceBus.HID, vid, pid, self._catalog),
                    bus=DeviceBus.HID,
                    hid=identity,
                )
            )
            if instance_id:
                known_instance_ids.add(str(instance_id).upper())
        devices = self._deduplicate_hid_display_names(devices)
        self._hid_cache = list(devices)
        self._hid_cache_at = now
        return devices

    def _detect_winmm_joysticks(self, pnp_rows: list[dict[str, Any]] | None = None) -> list[CockpitDevice]:
        rows = self._read_winmm_joysticks()
        if not rows:
            return []
        pnp_by_vid_pid: dict[tuple[str, str], list[dict[str, Any]]] = {}
        vjoy_rows: list[dict[str, Any]] = []
        for row in pnp_rows if pnp_rows is not None else self._windows_joystick_pnp_rows():
            instance_id = str(row.get("InstanceId") or "")
            vid, pid = parse_vid_pid(instance_id)
            if vid and pid:
                pnp_by_vid_pid.setdefault((vid, pid), []).append(row)
            elif str(row.get("FriendlyName") or "").lower() == "vjoy device":
                vjoy_rows.append(row)

        devices: list[CockpitDevice] = []
        for row in rows:
            vid = normalize_usb_id(row.get("vid"))
            pid = normalize_usb_id(row.get("pid"))
            pnp_row = None
            if vid and pid:
                candidates = pnp_by_vid_pid.get((vid, pid), [])
                if candidates:
                    pnp_row = candidates.pop(0)
            if pnp_row is None and vid == "1234" and pid == "BEAD" and vjoy_rows:
                pnp_row = vjoy_rows.pop(0)

            instance_id = str(pnp_row.get("InstanceId")) if pnp_row else None
            if not instance_id:
                id_part = f"VID_{vid or '0000'}&PID_{pid or '0000'}"
                instance_id = f"WINMM\\{id_part}\\JOY{row['index']}"

            name = self._joystick_oem_name(vid, pid) or row.get("name") or f"Joystick {row['index'] + 1}"
            catalog_match = self._catalog.match(name, vid, pid)
            if catalog_match and catalog_match.name and self._is_generic_device_name(name):
                name = catalog_match.name
            order = int(row["index"]) + 1
            identity = HidIdentity(
                name=name,
                vid=vid,
                pid=pid,
                device_instance_id=instance_id,
                joystick_order=order,
            )
            devices.append(
                CockpitDevice(
                    id=_stable_id("hid", instance_id, name, vid, pid),
                    display_name=name,
                    kind=_guess_kind(name, DeviceBus.HID, vid, pid, self._catalog),
                    bus=DeviceBus.HID,
                    hid=identity,
                )
            )
        return devices

    @staticmethod
    def _read_winmm_joysticks() -> list[dict[str, Any]]:
        if not is_windows():
            return []
        try:
            winmm = ctypes.WinDLL("winmm")
        except OSError:
            return []

        class JoyCapsW(ctypes.Structure):
            _fields_ = [
                ("wMid", wintypes.WORD),
                ("wPid", wintypes.WORD),
                ("szPname", wintypes.WCHAR * 32),
                ("wXmin", wintypes.UINT),
                ("wXmax", wintypes.UINT),
                ("wYmin", wintypes.UINT),
                ("wYmax", wintypes.UINT),
                ("wZmin", wintypes.UINT),
                ("wZmax", wintypes.UINT),
                ("wNumButtons", wintypes.UINT),
                ("wPeriodMin", wintypes.UINT),
                ("wPeriodMax", wintypes.UINT),
                ("wRmin", wintypes.UINT),
                ("wRmax", wintypes.UINT),
                ("wUmin", wintypes.UINT),
                ("wUmax", wintypes.UINT),
                ("wVmin", wintypes.UINT),
                ("wVmax", wintypes.UINT),
                ("wCaps", wintypes.UINT),
                ("wMaxAxes", wintypes.UINT),
                ("wNumAxes", wintypes.UINT),
                ("wMaxButtons", wintypes.UINT),
                ("szRegKey", wintypes.WCHAR * 32),
                ("szOEMVxD", wintypes.WCHAR * 260),
            ]

        try:
            joy_get_num_devs = winmm.joyGetNumDevs
            joy_get_num_devs.restype = wintypes.UINT
            joy_get_dev_caps = winmm.joyGetDevCapsW
            joy_get_dev_caps.argtypes = [wintypes.UINT, ctypes.POINTER(JoyCapsW), wintypes.UINT]
            joy_get_dev_caps.restype = wintypes.UINT
        except AttributeError:
            return []

        devices: list[dict[str, Any]] = []
        for index in range(int(joy_get_num_devs())):
            caps = JoyCapsW()
            if joy_get_dev_caps(index, ctypes.byref(caps), ctypes.sizeof(caps)) != 0:
                continue
            devices.append(
                {
                    "index": index,
                    "name": caps.szPname.strip(),
                    "vid": f"{int(caps.wMid):04X}" if caps.wMid else None,
                    "pid": f"{int(caps.wPid):04X}" if caps.wPid else None,
                }
            )
        return devices

    @staticmethod
    def _windows_joystick_pnp_rows() -> list[dict[str, Any]]:
        script = (
            "Get-PnpDevice -PresentOnly | "
            "Where-Object { $_.Class -eq 'HIDClass' -and "
            "($_.FriendlyName -match 'Contrôleur de jeu HID|Controleur de jeu HID|HID-compliant game controller|game controller|joystick|vJoy Device') } | "
            "Select-Object FriendlyName, InstanceId, Manufacturer, Status, Class"
        )
        return run_powershell_json(script, timeout=10)

    @staticmethod
    def _joystick_oem_name(vid: str | None, pid: str | None) -> str | None:
        normalized_vid = normalize_usb_id(vid)
        normalized_pid = normalize_usb_id(pid)
        if not normalized_vid or not normalized_pid or not is_windows():
            return None
        try:
            import winreg
        except ImportError:
            return None
        subkey = (
            "System\\CurrentControlSet\\Control\\MediaProperties\\"
            f"PrivateProperties\\Joystick\\OEM\\VID_{normalized_vid}&PID_{normalized_pid}"
        )
        for root in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
            try:
                with winreg.OpenKey(root, subkey) as key:
                    value, _ = winreg.QueryValueEx(key, "OEMName")
                    return str(value) if value else None
            except OSError:
                continue
        return None

    @staticmethod
    def _is_generic_game_controller_row(row: dict[str, Any]) -> bool:
        name = str(row.get("FriendlyName") or "").lower()
        return name in {"contrôleur de jeu hid", "controleur de jeu hid", "hid-compliant game controller", "game controller", "vjoy device"}

    @staticmethod
    def _is_generic_device_name(name: str | None) -> bool:
        normalized = _normalized_device_name(name)
        if normalized.startswith(("peripherique serie usb", "usb serial device")):
            return True
        return normalized in {
            "",
            "hid device",
            "hid-compliant game controller",
            "game controller",
            "contrôleur de jeu hid",
            "contrã´leur de jeu hid",
            "controleur de jeu hid",
            "périphérique d'entrée usb",
            "périphérique d’entrée usb",
            "pã©riphã©rique dâ€™entrã©e usb",
            "pã©riphã©rique d'entrã©e usb",
            "microsoft pc-joystick driver",
            "pilote de joystick pc microsoft",
        }

    @staticmethod
    def _deduplicate_hid_display_names(devices: list[CockpitDevice]) -> list[CockpitDevice]:
        counts: dict[str, int] = {}
        for device in devices:
            counts[device.display_name] = counts.get(device.display_name, 0) + 1
        seen: dict[str, int] = {}
        for device in devices:
            if counts.get(device.display_name, 0) <= 1 or not device.hid:
                continue
            seen[device.display_name] = seen.get(device.display_name, 0) + 1
            suffix = DeviceDetector._short_instance_label(device.hid.device_instance_id) or f"Joy {device.hid.joystick_order}"
            device.display_name = f"{device.display_name} ({suffix})"
            device.hid.name = device.display_name
        return devices

    @staticmethod
    def _short_instance_label(instance_id: str | None) -> str | None:
        if not instance_id:
            return None
        tail = instance_id.rsplit("\\", 1)[-1]
        parts = [part for part in tail.split("&") if part and part not in {"0", "0000"}]
        if len(parts) >= 2 and parts[0].isdigit():
            return parts[1][:12]
        if parts:
            return parts[0][:12]
        return tail[:12] if tail else None

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
    def _is_usb_serial_port(port: object, metadata: dict[str, str | None]) -> bool:
        if getattr(port, "vid", None) is not None or getattr(port, "pid", None) is not None:
            return True
        text = " ".join(
            str(item or "")
            for item in [
                getattr(port, "hwid", None),
                getattr(port, "location", None),
                metadata.get("device_instance_id"),
                metadata.get("location_path"),
            ]
        ).upper()
        return "USB" in text

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
                usb=UsbConnectionInfo(
                    label="USB 2.0 path",
                    usb_generation="USB 2.0",
                    negotiated_speed_mbps=480,
                    confidence="medium",
                    source="mock topology",
                ),
            ),
            CockpitDevice(
                id="mock-pedals",
                display_name="mBooster Active Pedals",
                kind=DeviceKind.PEDALS,
                bus=DeviceBus.HID,
                hid=HidIdentity(name="mBooster Active Pedals", vid="3416", pid="0301", joystick_order=2),
                usb=UsbConnectionInfo(
                    label="USB 3.x capable path",
                    usb_generation="USB 3.x",
                    confidence="medium",
                    source="mock topology",
                    note="Path capability, not negotiated speed.",
                ),
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
                usb=UsbConnectionInfo(
                    label="USB serial bridge",
                    confidence="low",
                    source="mock Arduino serial",
                    note="Negotiated speed requires a USBView-level hub query.",
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
                usb=UsbConnectionInfo(
                    label="USB serial bridge",
                    confidence="low",
                    source="mock CH340 serial",
                    note="Generic USB serial bridge; speed unknown from PnP alone.",
                ),
            ),
        ]
