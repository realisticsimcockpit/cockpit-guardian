from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from .check_engine import CheckEngine
from .config_manager import ConfigManager
from .models import CheckReport, RestoreAction, RestoreReport, Settings, Snapshot
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

    def load_settings(self) -> Settings:
        return self.config.load_settings()

    def save_settings(self, settings: Settings) -> None:
        self.config.save_settings(settings)
        self.logger.info("Settings saved")

    def load_snapshot(self) -> Snapshot | None:
        return self.config.load_snapshot()

    def save_configuration(self) -> Snapshot:
        settings = self.load_settings()
        devices = self.detector.detect_all(include_windows_metadata=settings.deep_windows_scan)
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
        report = self.check_engine.run_check(
            self.load_snapshot(),
            simhub_required=settings.simhub_required,
            ffb_clipping_threshold=settings.ffb_clipping_threshold,
            deep_windows_scan=settings.deep_windows_scan,
            software_scan_interval_seconds=settings.software_scan_interval_seconds,
            usb_health_scan_interval_seconds=settings.usb_health_scan_interval_seconds,
        )
        self.last_report = report
        return report

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
