from __future__ import annotations

import time
from dataclasses import dataclass, field

from ..models import CockpitDevice, UsbConnectionInfo
from .integration_notices import generic_usb_serial_bridge_name, normalize_usb_id
from .windows_util import is_windows, run_powershell_json


USB3_TOKENS = [
    "root_hub30",
    "usb 3",
    "usb3",
    "xhci",
    "superspeed",
    "super speed",
    "super-speed",
]
USB2_TOKENS = [
    "root_hub20",
    "usb 2",
    "usb2",
    "ehci",
    "high-speed",
    "high speed",
]
USB1_TOKENS = [
    "full-speed",
    "full speed",
    "low-speed",
    "low speed",
]


@dataclass(slots=True)
class UsbTopologyDetector:
    """Best-effort USB generation detector.

    Accurate negotiated USB speed on Windows requires hub IOCTL queries like the
    USBView sample uses. This service keeps a lightweight PnP-based path for the
    Dashboard and records confidence so the UI does not overpromise.
    """

    _metadata_cache: dict[str, dict[str, str | None]] = field(default_factory=dict)
    _metadata_cache_at: float = 0.0

    def annotate_devices(self, devices: list[CockpitDevice], include_windows_metadata: bool = False) -> list[CockpitDevice]:
        metadata = self._windows_usb_metadata() if include_windows_metadata else {}
        for device in devices:
            instance_id = self._device_instance_id(device)
            row = metadata.get((instance_id or "").upper(), {})
            device.usb = self.infer_connection(
                instance_id=instance_id,
                location_path=self._location_path(device) or row.get("location_path"),
                name=device.label,
                product=self._product(device),
                vid=self._vid(device),
                pid=self._pid(device),
                parent=row.get("parent"),
                bus_description=row.get("bus_description"),
            )
        return devices

    def infer_connection(
        self,
        instance_id: str | None = None,
        location_path: str | None = None,
        name: str | None = None,
        product: str | None = None,
        vid: str | None = None,
        pid: str | None = None,
        parent: str | None = None,
        bus_description: str | None = None,
    ) -> UsbConnectionInfo:
        text = " ".join(
            item
            for item in [instance_id, location_path, name, product, parent, bus_description]
            if item
        ).lower()
        hub_or_port = location_path or parent

        if any(token in text for token in USB3_TOKENS):
            return UsbConnectionInfo(
                label="USB 3.x capable path",
                usb_generation="USB 3.x",
                hub_or_port=hub_or_port,
                confidence="medium",
                source="Windows PnP topology",
                note="This indicates hub/path capability. Negotiated speed requires USB hub IOCTL data.",
            )
        if any(token in text for token in USB2_TOKENS):
            return UsbConnectionInfo(
                label="USB 2.0 path",
                usb_generation="USB 2.0",
                negotiated_speed_mbps=480 if "high" in text else None,
                hub_or_port=hub_or_port,
                confidence="medium",
                source="Windows PnP topology",
                note="This is a topology hint, not a guaranteed negotiated speed.",
            )
        if any(token in text for token in USB1_TOKENS):
            return UsbConnectionInfo(
                label="USB 1.x/full-speed path",
                usb_generation="USB 1.x",
                negotiated_speed_mbps=12 if "full" in text else 1,
                hub_or_port=hub_or_port,
                confidence="medium",
                source="Windows PnP topology",
                note="This is a topology hint, not a guaranteed negotiated speed.",
            )

        bridge_name = generic_usb_serial_bridge_name(vid, pid)
        normalized_vid = normalize_usb_id(vid)
        if bridge_name:
            return UsbConnectionInfo(
                label="USB serial bridge",
                usb_generation=None,
                hub_or_port=hub_or_port,
                confidence="low",
                source=bridge_name,
                note="CH340, CP210x, FTDI, and similar bridges usually do not expose negotiated USB generation through PnP alone.",
            )
        if normalized_vid:
            return UsbConnectionInfo(
                label="USB speed unknown",
                usb_generation=None,
                hub_or_port=hub_or_port,
                confidence="unknown",
                source="Windows PnP identity",
                note="Negotiated speed requires a USBView-level hub query.",
            )
        return UsbConnectionInfo()

    def _windows_usb_metadata(self, cache_ttl_seconds: int = 30) -> dict[str, dict[str, str | None]]:
        now = time.monotonic()
        if self._metadata_cache and now - self._metadata_cache_at <= cache_ttl_seconds:
            return dict(self._metadata_cache)
        if not is_windows():
            return {}

        script = (
            "Get-PnpDevice -PresentOnly | "
            "Where-Object { $_.Class -in @('USB','HIDClass','Ports') } | "
            "ForEach-Object { "
            "$p = Get-PnpDeviceProperty -InstanceId $_.InstanceId -KeyName "
            "'DEVPKEY_Device_LocationPaths','DEVPKEY_Device_Parent','DEVPKEY_Device_BusReportedDeviceDesc' "
            "-ErrorAction SilentlyContinue; "
            "[PSCustomObject]@{ "
            "InstanceId=$_.InstanceId; FriendlyName=$_.FriendlyName; "
            "LocationPaths=($p | Where-Object KeyName -eq 'DEVPKEY_Device_LocationPaths').Data; "
            "Parent=($p | Where-Object KeyName -eq 'DEVPKEY_Device_Parent').Data; "
            "BusReportedDeviceDesc=($p | Where-Object KeyName -eq 'DEVPKEY_Device_BusReportedDeviceDesc').Data "
            "} }"
        )
        metadata: dict[str, dict[str, str | None]] = {}
        for row in run_powershell_json(script, timeout=15):
            instance_id = str(row.get("InstanceId") or "").upper()
            if not instance_id:
                continue
            location_paths = row.get("LocationPaths")
            if isinstance(location_paths, list):
                location_path = " | ".join(str(item) for item in location_paths if item)
            else:
                location_path = str(location_paths) if location_paths else None
            metadata[instance_id] = {
                "location_path": location_path,
                "parent": row.get("Parent"),
                "bus_description": row.get("BusReportedDeviceDesc") or row.get("FriendlyName"),
            }
        self._metadata_cache = dict(metadata)
        self._metadata_cache_at = now
        return metadata

    @staticmethod
    def _device_instance_id(device: CockpitDevice) -> str | None:
        if device.serial:
            return device.serial.device_instance_id
        if device.hid:
            return device.hid.device_instance_id
        return None

    @staticmethod
    def _location_path(device: CockpitDevice) -> str | None:
        return device.serial.location_path if device.serial else None

    @staticmethod
    def _product(device: CockpitDevice) -> str | None:
        if device.serial:
            return device.serial.product or device.serial.friendly_name
        if device.hid:
            return device.hid.name
        return None

    @staticmethod
    def _vid(device: CockpitDevice) -> str | None:
        if device.serial:
            return device.serial.vid
        if device.hid:
            return device.hid.vid
        return None

    @staticmethod
    def _pid(device: CockpitDevice) -> str | None:
        if device.serial:
            return device.serial.pid
        if device.hid:
            return device.hid.pid
        return None
