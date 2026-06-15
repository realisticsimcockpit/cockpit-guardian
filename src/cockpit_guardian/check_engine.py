from __future__ import annotations

import logging
from dataclasses import dataclass

from .models import (
    CheckReport,
    CockpitDevice,
    DeviceBus,
    DeviceCheck,
    GlobalStatus,
    Priority,
    Severity,
    Snapshot,
    SoftwareState,
    utc_now_iso,
)
from .services.integration_notices import is_generic_usb_serial_bridge, serial_identity_notice
from .services.device_detector import DeviceDetector
from .services.joystick_manager import JoystickOrderManager
from .services.software_detector import SoftwareDetector
from .services.telemetry import TelemetryService
from .services.usb_health import UsbHealthMonitor


@dataclass(slots=True)
class CheckEngine:
    detector: DeviceDetector
    joystick_manager: JoystickOrderManager
    usb_health: UsbHealthMonitor
    software_detector: SoftwareDetector
    telemetry_service: TelemetryService
    logger: logging.Logger

    def run_check(
        self,
        snapshot: Snapshot | None,
        simhub_required: bool = False,
        ffb_clipping_threshold: float = 10.0,
        deep_windows_scan: bool = False,
        software_scan_interval_seconds: int = 300,
        usb_health_scan_interval_seconds: int = 120,
    ) -> CheckReport:
        current_devices = self.detector.detect_all(include_windows_metadata=deep_windows_scan)
        required_software = {"SimHub"} if simhub_required else set()
        software = self.software_detector.detect(
            required=required_software,
            installed_cache_ttl_seconds=software_scan_interval_seconds,
        )
        usb_health = self.usb_health.check(cache_ttl_seconds=usb_health_scan_interval_seconds)
        current_order = self.joystick_manager.read_current_order(current_devices)
        telemetry = self.telemetry_service.get_status(software)

        if snapshot is None:
            report = CheckReport(
                timestamp=utc_now_iso(),
                global_status=GlobalStatus.CHECK_NOT_DONE,
                device_checks=[
                    DeviceCheck(None, device, Severity.INFO, device.label)
                    for device in current_devices
                    if device.priority != Priority.IGNORED
                ],
                usb_health=usb_health,
                software=[item for item in software if item.state != SoftwareState.NOT_DETECTED or item.required],
                telemetry=telemetry,
                issues=["No saved configuration. Use Save Configuration first."],
                snapshot_loaded=False,
            )
            self.logger.info("Check completed without saved snapshot")
            return report

        device_checks = self._compare_devices(snapshot.devices, current_devices)
        software = self._merge_snapshot_software(snapshot, software)
        self._apply_telemetry_to_wheel(device_checks, telemetry, ffb_clipping_threshold)
        joystick_result = self.joystick_manager.compare(snapshot.joystick_order, current_order)
        issues = [check.message for check in device_checks if check.severity in {Severity.WARNING, Severity.RESTORE_NEEDED, Severity.CRITICAL}]
        if not joystick_result.ok:
            issues.append(joystick_result.message)
        if usb_health.severity in {Severity.WARNING, Severity.CRITICAL}:
            issues.append(usb_health.message)

        for item in software:
            if item.state in {SoftwareState.REQUIRED_MISSING, SoftwareState.OPTIONAL_MISSING}:
                issues.append(f"{item.name}: {item.state.value}")

        report = CheckReport(
            timestamp=utc_now_iso(),
            global_status=self._global_status(device_checks, joystick_result.ok, usb_health.severity, software),
            device_checks=device_checks,
            joystick_order=joystick_result,
            usb_health=usb_health,
            software=[
                item
                for item in software
                if item.state != SoftwareState.NOT_DETECTED
                or item.required
                or any(saved.name == item.name for saved in snapshot.software)
            ],
            telemetry=telemetry,
            issues=issues,
            snapshot_loaded=True,
        )
        self.logger.info("Check completed: %s (%d issues)", report.global_status.value, len(report.issues))
        return report

    @staticmethod
    def _merge_snapshot_software(snapshot: Snapshot, current: list) -> list:
        by_name = {item.name: item for item in current}
        for saved in snapshot.software:
            current_item = by_name.get(saved.name)
            if current_item is None:
                state = SoftwareState.REQUIRED_MISSING if saved.required else SoftwareState.OPTIONAL_MISSING
                by_name[saved.name] = type(saved)(
                    name=saved.name,
                    state=state,
                    path=saved.path,
                    process_name=saved.process_name,
                    required=saved.required,
                )
            elif current_item.state == SoftwareState.NOT_DETECTED and (saved.required or saved.state != SoftwareState.NOT_DETECTED):
                current_item.state = SoftwareState.REQUIRED_MISSING if saved.required else SoftwareState.OPTIONAL_MISSING
                current_item.path = saved.path
                current_item.process_name = saved.process_name
                current_item.required = saved.required
        return list(by_name.values())

    def _compare_devices(self, expected_devices: list[CockpitDevice], current_devices: list[CockpitDevice]) -> list[DeviceCheck]:
        checks: list[DeviceCheck] = []
        matched_current: set[str] = set()
        for expected in expected_devices:
            if expected.priority == Priority.IGNORED:
                continue
            detected = self._find_match(expected, current_devices)
            if detected:
                matched_current.add(detected.id)
                check = self._check_matched_device(expected, detected)
            else:
                severity = Severity.CRITICAL if expected.priority == Priority.REQUIRED else Severity.WARNING
                suffix = "absent" if expected.priority == Priority.REQUIRED else "optional absent"
                check = DeviceCheck(
                    expected=expected,
                    detected=None,
                    severity=severity,
                    message=f"{expected.label} {suffix}",
                    restore_available=expected.bus == DeviceBus.SERIAL,
                )
            checks.append(check)

        for detected in current_devices:
            if detected.id in matched_current:
                continue
            checks.append(DeviceCheck(None, detected, Severity.INFO, detected.label, detail="New or unsaved device detected."))
        return checks

    def _check_matched_device(self, expected: CockpitDevice, detected: CockpitDevice) -> DeviceCheck:
        if expected.bus == DeviceBus.SERIAL and expected.serial and detected.serial:
            expected_com = expected.serial.current_com
            current_com = detected.serial.current_com
            if expected_com and current_com and expected_com != current_com:
                return DeviceCheck(
                    expected=expected,
                    detected=detected,
                    severity=Severity.RESTORE_NEEDED,
                    message=f"{expected.label} expected {expected_com}, detected {current_com}, restore needed",
                    restore_available=True,
                )
        if self._location_changed(expected, detected):
            return DeviceCheck(
                expected=expected,
                detected=detected,
                severity=Severity.WARNING,
                message=f"{expected.label} detected on a new USB location",
                restore_available=False,
            )
        detail = None
        if expected.serial and detected.serial:
            detail = serial_identity_notice(
                detected.serial.vid,
                detected.serial.pid,
                detected.serial.serial_number,
                detected.serial.location_path,
            )
        return DeviceCheck(expected=expected, detected=detected, severity=Severity.OK, message=expected.label, detail=detail)

    @staticmethod
    def _location_changed(expected: CockpitDevice, detected: CockpitDevice) -> bool:
        if expected.serial and detected.serial:
            return bool(expected.serial.location_path and detected.serial.location_path and expected.serial.location_path != detected.serial.location_path)
        return False

    @staticmethod
    def _find_match(expected: CockpitDevice, current_devices: list[CockpitDevice]) -> CockpitDevice | None:
        for candidate in current_devices:
            if expected.id == candidate.id:
                return candidate
        for candidate in current_devices:
            if expected.serial and candidate.serial:
                if expected.serial.device_instance_id and expected.serial.device_instance_id == candidate.serial.device_instance_id:
                    return candidate
                if expected.serial.serial_number and expected.serial.serial_number == candidate.serial.serial_number:
                    return candidate
                if expected.serial.vid and expected.serial.pid and expected.serial.vid == candidate.serial.vid and expected.serial.pid == candidate.serial.pid:
                    if is_generic_usb_serial_bridge(expected.serial.vid, expected.serial.pid):
                        if expected.serial.location_path and expected.serial.location_path == candidate.serial.location_path:
                            return candidate
                        continue
                    if expected.serial.product == candidate.serial.product or expected.display_name == candidate.display_name:
                        return candidate
            if expected.hid and candidate.hid:
                if expected.hid.device_instance_id and expected.hid.device_instance_id == candidate.hid.device_instance_id:
                    return candidate
                if expected.hid.vid and expected.hid.pid and expected.hid.vid == candidate.hid.vid and expected.hid.pid == candidate.hid.pid:
                    if expected.hid.name == candidate.hid.name or expected.display_name == candidate.display_name:
                        return candidate
        return None

    @staticmethod
    def _apply_telemetry_to_wheel(
        device_checks: list[DeviceCheck],
        telemetry_status,
        ffb_clipping_threshold: float,
    ) -> None:
        wheel = next((check for check in device_checks if check.expected and check.expected.kind.value == "wheel"), None)
        if not wheel:
            return
        if not telemetry_status.available:
            wheel.detail = telemetry_status.message
            return
        wheel.detail = telemetry_status.message
        if telemetry_status.ffb_clipping_percent is not None and telemetry_status.ffb_clipping_percent >= ffb_clipping_threshold:
            wheel.ffb_clipping_percent = telemetry_status.ffb_clipping_percent
            wheel.severity = Severity.WARNING if wheel.severity == Severity.OK else wheel.severity
            wheel.message = f"{wheel.message} - FFB clipping {telemetry_status.ffb_clipping_percent:.0f}% from {telemetry_status.source} - Reduce in-game FFB gain"

    @staticmethod
    def _global_status(device_checks: list[DeviceCheck], joystick_ok: bool, usb_severity: Severity, software) -> GlobalStatus:
        if any(check.severity == Severity.CRITICAL for check in device_checks):
            return GlobalStatus.CRITICAL_DEVICE_MISSING
        if any(check.severity == Severity.RESTORE_NEEDED for check in device_checks) or not joystick_ok:
            return GlobalStatus.RESTORE_NEEDED
        if usb_severity in {Severity.WARNING, Severity.CRITICAL}:
            return GlobalStatus.WARNING
        if any(check.severity == Severity.WARNING for check in device_checks):
            return GlobalStatus.WARNING
        if any(item.state in {SoftwareState.REQUIRED_MISSING, SoftwareState.OPTIONAL_MISSING} for item in software):
            return GlobalStatus.WARNING
        return GlobalStatus.COCKPIT_READY
