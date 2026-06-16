from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path

from ..models import CockpitDevice, UsbConnectionInfo, utc_now_iso
from .integration_notices import generic_usb_serial_bridge_name, normalize_usb_id
from .usb_speed_scanner import UsbSpeedRecord, UsbSpeedScanner
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
    speed_cache_path: Path | None = None
    _speed_records: list[UsbSpeedRecord] = field(default_factory=list)
    _speed_cache_loaded: bool = False

    def annotate_devices(self, devices: list[CockpitDevice], include_windows_metadata: bool = False) -> list[CockpitDevice]:
        metadata = self._windows_usb_metadata() if include_windows_metadata else {}
        speed_records = self.ensure_speed_cache(force=False) if self.speed_cache_path else []
        for device in devices:
            instance_id = self._device_instance_id(device)
            row = metadata.get((instance_id or "").upper(), {})
            cached_speed = self._match_speed_record(device, speed_records)
            if cached_speed is not None:
                device.usb = UsbConnectionInfo(
                    label=cached_speed.label,
                    usb_generation=cached_speed.usb_generation,
                    negotiated_speed_mbps=cached_speed.negotiated_speed_mbps or None,
                    hub_or_port=f"USB hub port {cached_speed.port}",
                    confidence=cached_speed.confidence,
                    source=cached_speed.source,
                    note=cached_speed.note,
                )
                continue
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

    def ensure_speed_cache(self, force: bool = False) -> list[UsbSpeedRecord]:
        if not force and self._speed_cache_loaded:
            return list(self._speed_records)
        if not force:
            cached = self._load_speed_cache()
            if cached:
                self._speed_records = cached
                self._speed_cache_loaded = True
                return list(self._speed_records)
        records = UsbSpeedScanner().scan()
        self._speed_records = list(records)
        self._speed_cache_loaded = True
        if records:
            self._save_speed_cache(records)
        return list(self._speed_records)

    def _has_speed_cache(self) -> bool:
        return bool(self.speed_cache_path and self.speed_cache_path.exists())

    def _load_speed_cache(self) -> list[UsbSpeedRecord]:
        if not self.speed_cache_path or not self.speed_cache_path.exists():
            return []
        try:
            data = json.loads(self.speed_cache_path.read_text(encoding="utf-8"))
        except Exception:
            return []
        raw_records = data.get("records") if isinstance(data, dict) else None
        if not isinstance(raw_records, list):
            return []
        records = [UsbSpeedRecord.from_dict(item) for item in raw_records if isinstance(item, dict)]
        return [record for record in records if record is not None]

    def _save_speed_cache(self, records: list[UsbSpeedRecord]) -> None:
        if not self.speed_cache_path:
            return
        self.speed_cache_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "schema": "cockpit_guardian.usb_speed_cache.v1",
            "scanned_at": utc_now_iso(),
            "records": [record.to_dict() for record in records],
        }
        self.speed_cache_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def _match_speed_record(self, device: CockpitDevice, records: list[UsbSpeedRecord]) -> UsbSpeedRecord | None:
        vid = normalize_usb_id(self._vid(device))
        pid = normalize_usb_id(self._pid(device))
        if not vid or not pid:
            return None
        matches = [record for record in records if record.vid == vid and record.pid == pid]
        if not matches:
            return None
        speeds = {(record.label, record.usb_generation, record.negotiated_speed_mbps) for record in matches}
        if len(speeds) == 1:
            return matches[0]
        return matches[0]

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
                label="USB speed scan needed",
                usb_generation=None,
                hub_or_port=hub_or_port,
                confidence="unknown",
                source="Windows PnP identity",
                note="Negotiated speed requires a USBView or USBTreeView-level hub query.",
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
