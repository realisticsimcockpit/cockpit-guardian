from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from .check_engine import CheckEngine
from .config_manager import ConfigManager
from .models import CheckReport, DeviceKind, RestoreAction, RestoreReport, Settings, Snapshot
from .services.device_detector import DeviceDetector
from .services.joystick_manager import JoystickOrderManager
from .services.restore_engine import RestoreEngine
from .services.software_detector import SoftwareDetector


@dataclass(slots=True)
class AppController:
    config: ConfigManager
    check_engine: CheckEngine
    restore_engine: RestoreEngine
    detector: DeviceDetector
    joystick_manager: JoystickOrderManager
    software_detector: SoftwareDetector
    logger: logging.Logger
    last_report: CheckReport | None = None
    _initial_deep_scan_used_this_session: bool = False

    def load_settings(self) -> Settings:
        return self.config.load_settings()

    def save_settings(self, settings: Settings) -> None:
        self.config.save_settings(settings)
        self.logger.info("Settings saved")

    def load_snapshot(self) -> Snapshot | None:
        return self.config.load_snapshot()

    def save_configuration(self) -> Snapshot:
        settings = self.load_settings()
        return self._capture_snapshot(settings)

    def _capture_snapshot(self, settings: Settings) -> Snapshot:
        deep_scan = self._deep_scan_for_operation(settings, persist_initial=True)
        devices = self.detector.detect_all(include_windows_metadata=deep_scan)
        software = [
            item
            for item in self.software_detector.detect(
                required={"SimHub"} if settings.simhub_required else set(),
                installed_cache_ttl_seconds=settings.software_scan_interval_seconds,
            )
            if item.state.value != "Not detected" or item.required
        ]
        joystick_order = self.joystick_manager.read_current_order(devices)
        snapshot = self.config.create_snapshot(settings.profile_name, devices, software, joystick_order)
        self.logger.info("Configuration snapshot saved with %d devices", len(devices))
        return snapshot

    def check_now(self) -> CheckReport:
        settings = self.load_settings()
        snapshot = self.load_snapshot()
        if snapshot is None:
            snapshot = self._capture_snapshot(settings)
            settings = self.load_settings()
            self.logger.info("Initial configuration snapshot created automatically")
        deep_scan = self._deep_scan_for_operation(settings, persist_initial=snapshot is not None)
        report = self.check_engine.run_check(
            snapshot,
            simhub_required=settings.simhub_required,
            ffb_clipping_threshold=settings.ffb_clipping_threshold,
            deep_windows_scan=deep_scan,
            software_scan_interval_seconds=settings.software_scan_interval_seconds,
            usb_health_scan_interval_seconds=settings.usb_health_scan_interval_seconds,
        )
        if snapshot is not None and self._repair_incomplete_joystick_order(snapshot, report):
            report.joystick_order = self.joystick_manager.compare(snapshot.joystick_order, report.joystick_order.current)
        self.last_report = report
        return report

    def _deep_scan_for_operation(self, settings: Settings, persist_initial: bool) -> bool:
        if settings.initial_deep_windows_scan_done:
            return settings.deep_windows_scan
        if not persist_initial and self._initial_deep_scan_used_this_session:
            return settings.deep_windows_scan
        self._initial_deep_scan_used_this_session = True
        if not persist_initial:
            self.logger.info("Initial Deep Windows scan enabled for first startup check")
            return True
        settings.initial_deep_windows_scan_done = True
        self.config.save_settings(settings)
        self.logger.info("Initial Deep Windows scan enabled for baseline capture")
        return True

    def restore(self) -> RestoreReport:
        report = self.last_report or self.check_now()
        restore_report = self.restore_engine.restore(report, self.load_snapshot())
        self.last_report = self.check_now()
        return restore_report

    def rollback_last_restore(self) -> RestoreAction:
        action = self.restore_engine.rollback_last_restore()
        self.last_report = self.check_now()
        return action

    def default_config_backup_name(self) -> str:
        snapshot = self.load_snapshot()
        settings = self.load_settings()
        profile_name = snapshot.profile_name if snapshot else settings.profile_name
        return self.config.default_config_backup_name(profile_name)

    def export_config_backup(self, target: Path) -> Path:
        exported = self.config.export_config_backup(target)
        self.logger.info("Configuration backup exported to %s", exported)
        return exported

    def import_config_backup(self, source: Path) -> Path:
        backup = self.config.import_config_backup(source)
        self.logger.info("Configuration backup imported from %s", source)
        self.last_report = self.check_now()
        return backup

    def update_joystick_order(self, order: list[str]) -> Snapshot:
        snapshot = self.load_snapshot()
        if snapshot is None:
            raise ValueError("No saved configuration found. Use Save Configuration first.")
        snapshot.joystick_order = list(order)
        self.config.save_snapshot(snapshot)
        if self.last_report:
            self.last_report.joystick_order = self.joystick_manager.compare(order, self.last_report.joystick_order.current)
        self.logger.info("Joystick order updated: %s", ", ".join(order))
        return snapshot

    def update_device_role(self, device_id: str, role: str, kind: DeviceKind | None = None) -> Snapshot:
        snapshot = self.load_snapshot()
        if snapshot is None:
            raise ValueError("No saved configuration found. Use Save Configuration first.")

        role = " ".join(role.strip().split())
        if not role:
            raise ValueError("Role cannot be empty.")
        kind = kind or self._kind_from_role(role)
        updated = False
        for device in snapshot.devices:
            if device.id == device_id:
                device.kind = kind
                device.custom_role = role
                updated = True
                break

        if not updated and self.last_report:
            source = self._device_from_last_report(device_id)
            if source is not None:
                source.kind = kind
                source.custom_role = role
                snapshot.devices.append(source)
                updated = True

        if not updated:
            raise ValueError("Device is not part of the saved configuration yet.")

        self.config.save_snapshot(snapshot)
        if self.last_report:
            for check in self.last_report.device_checks:
                if any(device and device.id == device_id for device in (check.expected, check.detected)):
                    for device in (check.expected, check.detected):
                        if device:
                            device.kind = kind
                            device.custom_role = role
        self.logger.info("Device role updated: %s -> %s", device_id, role)
        return snapshot

    def scan_usb_speeds(self, force: bool = True) -> int:
        if not hasattr(self.detector, "scan_usb_speeds"):
            return 0
        count = self.detector.scan_usb_speeds(force=force)
        self.logger.info("USB speed scan cached %d records", count)
        self.last_report = self.check_now()
        return count

    def _device_from_last_report(self, device_id: str):
        if not self.last_report:
            return None
        for check in self.last_report.device_checks:
            for device in (check.detected, check.expected):
                if device and device.id == device_id:
                    return device
        return None

    @staticmethod
    def _kind_from_role(role: str) -> DeviceKind:
        normalized = role.lower().replace("-", " ").replace("_", " ")
        aliases = {
            DeviceKind.WHEEL: ["wheel base", "wheelbase", "base volant"],
            DeviceKind.STEERING_WHEEL: ["steering wheel", "volant", "gt neo"],
            DeviceKind.PEDALS: ["pedals", "pedalier", "pédalier", "pedales", "pédales"],
            DeviceKind.ACTIVE_PEDAL: ["diy active pedal", "active pedal", "activepedal"],
            DeviceKind.SHIFTER: ["shifter", "boite", "boîte"],
            DeviceKind.HANDBRAKE: ["handbrake", "hand brake", "frein a main", "frein à main"],
            DeviceKind.BUTTON_BOX: ["button box", "buttonbox", "boitier boutons", "boîtier boutons"],
            DeviceKind.DDU: ["ddu", "dash", "display"],
            DeviceKind.ARDUINO_SIMHUB: ["simhub arduino", "arduino simhub", "arduino"],
            DeviceKind.WIND_SIMULATOR: ["wind simulator", "wind", "ventilation"],
            DeviceKind.SEAT_MOVER: ["seatmover", "seat mover", "motion"],
            DeviceKind.AMBILIGHT: ["ambilight", "ambient light"],
        }
        for kind, values in aliases.items():
            if normalized in values:
                return kind
        return DeviceKind.OTHER

    def _repair_incomplete_joystick_order(self, snapshot: Snapshot, report: CheckReport) -> bool:
        expected = [name for name in snapshot.joystick_order if name]
        current = [name for name in report.joystick_order.current if name]
        if not expected or len(expected) >= len(current):
            return False
        current_names = {name.lower() for name in current}
        if not all(name.lower() in current_names for name in expected):
            return False
        snapshot.joystick_order = current
        self.config.save_snapshot(snapshot)
        self.logger.info("Incomplete joystick order repaired from Windows order: %s", ", ".join(current))
        return True
