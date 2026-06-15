from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from ..config_manager import ConfigManager
from ..models import CheckReport, RestoreAction, RestoreReport, Severity, Snapshot, utc_now_iso
from .com_manager import ComPortManager, UsbRescanService
from .joystick_manager import JoystickOrderManager


@dataclass(slots=True)
class RestoreEngine:
    config: ConfigManager
    com_manager: ComPortManager
    joystick_manager: JoystickOrderManager
    usb_rescan: UsbRescanService
    logger: logging.Logger

    def restore(self, report: CheckReport, snapshot: Snapshot | None) -> RestoreReport:
        backup = self.config.make_backup("restore", payload={"report_timestamp": report.timestamp})
        actions: list[RestoreAction] = []

        for check in report.device_checks:
            if check.severity == Severity.RESTORE_NEEDED and check.expected and check.detected and check.restore_available:
                ok, message, requires_admin = self.com_manager.restore_port(check.expected, check.detected, backup)
                actions.append(RestoreAction("Restore COM port", ok, message, str(backup), requires_admin))
                self.logger.info("Restore COM action: %s", message)
            elif check.severity == Severity.CRITICAL and check.restore_available:
                ok, message, requires_admin = self.usb_rescan.rescan()
                actions.append(RestoreAction("USB rescan", ok, message, str(backup), requires_admin))
                self.logger.info("USB rescan action: %s", message)

        if snapshot and report.joystick_order.restore_available:
            current_devices = [check.detected for check in report.device_checks if check.detected]
            ok, message, requires_admin = self.joystick_manager.restore(snapshot.joystick_order, backup, current_devices)
            actions.append(RestoreAction("Restore joystick order", ok, message, str(backup), requires_admin))
            self.logger.info("Joystick restore action: %s", message)

        if not actions:
            actions.append(RestoreAction("Restore", True, "No automatic restore action was needed.", str(backup), False))

        restore_report = RestoreReport(timestamp=utc_now_iso(), actions=actions, backup_path=str(backup))
        self.logger.info("Restore completed with %d actions", len(actions))
        return restore_report

    def rollback_last_restore(self) -> RestoreAction:
        backup = self.config.latest_backup()
        if backup is None:
            return RestoreAction("Rollback Last Restore", False, "No restore backup found.")
        joystick_ok, joystick_message = self.joystick_manager.rollback_registry_backup(Path(backup))
        try:
            self.config.rollback_backup(backup)
        except Exception as exc:
            self.logger.exception("Rollback failed")
            return RestoreAction("Rollback Last Restore", False, f"Rollback failed: {exc}", str(backup))
        self.logger.info("Rollback completed from %s", backup)
        if not joystick_ok:
            return RestoreAction("Rollback Last Restore", False, f"Configuration rolled back from {backup}, but joystick rollback failed: {joystick_message}", str(backup))
        return RestoreAction("Rollback Last Restore", True, f"Rolled back configuration from {backup}. {joystick_message}", str(backup))
