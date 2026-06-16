from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields, is_dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class DeviceKind(str, Enum):
    WHEEL = "wheel"
    STEERING_WHEEL = "steering_wheel"
    PEDALS = "pedals"
    ACTIVE_PEDAL = "active_pedal"
    SHIFTER = "shifter"
    HANDBRAKE = "handbrake"
    BUTTON_BOX = "button_box"
    DDU = "ddu"
    ARDUINO_SIMHUB = "arduino_simhub"
    WIND_SIMULATOR = "wind_simulator"
    SEAT_MOVER = "seat_mover"
    AMBILIGHT = "ambilight"
    OTHER = "other"


class Priority(str, Enum):
    REQUIRED = "required"
    OPTIONAL = "optional"
    IGNORED = "ignored"


class DeviceBus(str, Enum):
    SERIAL = "serial"
    HID = "hid"
    SOFTWARE = "software"
    UNKNOWN = "unknown"


class Severity(str, Enum):
    OK = "ok"
    INFO = "info"
    WARNING = "warning"
    RESTORE_NEEDED = "restore_needed"
    CRITICAL = "critical"


class GlobalStatus(str, Enum):
    COCKPIT_READY = "Cockpit Ready"
    RESTORE_NEEDED = "Restore Needed"
    WARNING = "Warning"
    CRITICAL_DEVICE_MISSING = "Critical Device Missing"
    CHECK_NOT_DONE = "Check Not Done"


class SoftwareState(str, Enum):
    RUNNING = "Running"
    INSTALLED_CLOSED = "Installed but closed"
    NOT_DETECTED = "Not detected"
    REQUIRED_MISSING = "Required missing"
    OPTIONAL_MISSING = "Optional missing"


@dataclass(slots=True)
class UsbConnectionInfo:
    label: str = "USB speed unknown"
    usb_generation: str | None = None
    negotiated_speed_mbps: int | None = None
    hub_or_port: str | None = None
    confidence: str = "unknown"
    source: str = "not detected"
    note: str | None = None


@dataclass(slots=True)
class SerialIdentity:
    current_com: str | None = None
    vid: str | None = None
    pid: str | None = None
    serial_number: str | None = None
    manufacturer: str | None = None
    product: str | None = None
    friendly_name: str | None = None
    location_path: str | None = None
    device_instance_id: str | None = None


@dataclass(slots=True)
class HidIdentity:
    name: str | None = None
    vid: str | None = None
    pid: str | None = None
    serial_number: str | None = None
    device_instance_id: str | None = None
    joystick_order: int | None = None


@dataclass(slots=True)
class CockpitDevice:
    id: str
    display_name: str
    kind: DeviceKind = DeviceKind.OTHER
    bus: DeviceBus = DeviceBus.UNKNOWN
    priority: Priority = Priority.REQUIRED
    custom_name: str | None = None
    custom_role: str | None = None
    serial: SerialIdentity | None = None
    hid: HidIdentity | None = None
    usb: UsbConnectionInfo | None = None

    @property
    def label(self) -> str:
        return self.custom_name or self.display_name


@dataclass(slots=True)
class DeviceCheck:
    expected: CockpitDevice | None
    detected: CockpitDevice | None
    severity: Severity
    message: str
    restore_available: bool = False
    detail: str | None = None
    ffb_clipping_percent: float | None = None

    @property
    def label(self) -> str:
        if self.expected:
            return self.expected.label
        if self.detected:
            return self.detected.label
        return "Unknown device"


@dataclass(slots=True)
class JoystickOrderResult:
    expected: list[str] = field(default_factory=list)
    current: list[str] = field(default_factory=list)
    ok: bool = True
    restore_available: bool = False
    message: str = "Joystick Order OK"


@dataclass(slots=True)
class UsbEvent:
    timestamp: str
    severity: Severity
    device_name: str
    message: str
    raw: str | None = None


@dataclass(slots=True)
class UsbHealthSummary:
    severity: Severity = Severity.OK
    message: str = "USB Health : No event"
    events: list[UsbEvent] = field(default_factory=list)
    stability_score: int = 100


@dataclass(slots=True)
class SoftwareStatus:
    name: str
    state: SoftwareState
    path: str | None = None
    process_name: str | None = None
    required: bool = False


@dataclass(slots=True)
class TelemetryStatus:
    source: str = "Telemetry"
    available: bool = False
    message: str = "Telemetry not available"
    ffb_clipping_percent: float | None = None
    ffb_signal_percent: float | None = None
    raw_value: float | None = None


@dataclass(slots=True)
class Settings:
    profile_name: str = "Default Cockpit"
    ffb_clipping_threshold: float = 10.0
    notifications_enabled: bool = True
    launch_at_startup: bool = False
    auto_restore: bool = False
    theme: str = "dark"
    language: str = "en"
    simhub_required: bool = False
    deep_windows_scan: bool = False
    initial_deep_windows_scan_done: bool = False
    software_scan_interval_seconds: int = 300
    usb_health_scan_interval_seconds: int = 120


@dataclass(slots=True)
class Snapshot:
    snapshot_date: str
    profile_name: str
    app_version: str
    devices: list[CockpitDevice] = field(default_factory=list)
    software: list[SoftwareStatus] = field(default_factory=list)
    joystick_order: list[str] = field(default_factory=list)


@dataclass(slots=True)
class CheckReport:
    timestamp: str
    global_status: GlobalStatus
    device_checks: list[DeviceCheck] = field(default_factory=list)
    joystick_order: JoystickOrderResult = field(default_factory=JoystickOrderResult)
    usb_health: UsbHealthSummary = field(default_factory=UsbHealthSummary)
    software: list[SoftwareStatus] = field(default_factory=list)
    telemetry: TelemetryStatus = field(default_factory=TelemetryStatus)
    issues: list[str] = field(default_factory=list)
    snapshot_loaded: bool = False


@dataclass(slots=True)
class RestoreAction:
    name: str
    success: bool
    message: str
    backup_path: str | None = None
    requires_admin: bool = False


@dataclass(slots=True)
class RestoreReport:
    timestamp: str
    actions: list[RestoreAction] = field(default_factory=list)
    backup_path: str | None = None

    @property
    def success(self) -> bool:
        return bool(self.actions) and all(action.success for action in self.actions)


def to_plain(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {key: to_plain(item) for key, item in asdict(value).items()}
    if isinstance(value, list):
        return [to_plain(item) for item in value]
    if isinstance(value, dict):
        return {key: to_plain(item) for key, item in value.items()}
    return value


def _enum(enum_type: type[Enum], value: Any) -> Any:
    if isinstance(value, enum_type):
        return value
    return enum_type(value)


def dataclass_from_dict(cls: type, data: dict[str, Any]):
    kwargs: dict[str, Any] = {}
    for item in fields(cls):
        if item.name in data:
            kwargs[item.name] = data[item.name]
    return cls(**kwargs)


def serial_from_dict(data: dict[str, Any] | None) -> SerialIdentity | None:
    return None if data is None else dataclass_from_dict(SerialIdentity, data)


def hid_from_dict(data: dict[str, Any] | None) -> HidIdentity | None:
    return None if data is None else dataclass_from_dict(HidIdentity, data)


def usb_from_dict(data: dict[str, Any] | None) -> UsbConnectionInfo | None:
    return None if data is None else dataclass_from_dict(UsbConnectionInfo, data)


def device_from_dict(data: dict[str, Any]) -> CockpitDevice:
    return CockpitDevice(
        id=data["id"],
        display_name=data.get("display_name", "Unknown device"),
        kind=_enum(DeviceKind, data.get("kind", DeviceKind.OTHER.value)),
        bus=_enum(DeviceBus, data.get("bus", DeviceBus.UNKNOWN.value)),
        priority=_enum(Priority, data.get("priority", Priority.REQUIRED.value)),
        custom_name=data.get("custom_name"),
        custom_role=data.get("custom_role"),
        serial=serial_from_dict(data.get("serial")),
        hid=hid_from_dict(data.get("hid")),
        usb=usb_from_dict(data.get("usb")),
    )


def software_from_dict(data: dict[str, Any]) -> SoftwareStatus:
    return SoftwareStatus(
        name=data["name"],
        state=_enum(SoftwareState, data.get("state", SoftwareState.NOT_DETECTED.value)),
        path=data.get("path"),
        process_name=data.get("process_name"),
        required=bool(data.get("required", False)),
    )


def settings_from_dict(data: dict[str, Any]) -> Settings:
    return dataclass_from_dict(Settings, data)


def snapshot_from_dict(data: dict[str, Any]) -> Snapshot:
    return Snapshot(
        snapshot_date=data.get("snapshot_date", utc_now_iso()),
        profile_name=data.get("profile_name", "Default Cockpit"),
        app_version=data.get("app_version", "unknown"),
        devices=[device_from_dict(item) for item in data.get("devices", [])],
        software=[software_from_dict(item) for item in data.get("software", [])],
        joystick_order=list(data.get("joystick_order", [])),
    )
