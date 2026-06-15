import logging
import unittest

from cockpit_guardian.check_engine import CheckEngine
from cockpit_guardian.models import (
    CockpitDevice,
    DeviceBus,
    DeviceKind,
    GlobalStatus,
    HidIdentity,
    SerialIdentity,
    Snapshot,
    SoftwareState,
    SoftwareStatus,
    TelemetryStatus,
    utc_now_iso,
)
from cockpit_guardian.services.joystick_manager import JoystickOrderManager
from cockpit_guardian.services.usb_health import UsbHealthMonitor


class FakeDetector:
    def __init__(self, devices):
        self.devices = devices

    def detect_all(self, include_windows_metadata=False):
        return self.devices


class FakeSoftware:
    def __init__(self, statuses=None):
        self.statuses = statuses

    def detect(self, required=None, installed_cache_ttl_seconds=300):
        if self.statuses is not None:
            return self.statuses
        return [SoftwareStatus("SimHub", SoftwareState.NOT_DETECTED, required="SimHub" in (required or set()))]


class FakeUsb(UsbHealthMonitor):
    def check(self, cache_ttl_seconds=120):
        from cockpit_guardian.models import UsbHealthSummary

        return UsbHealthSummary()


class FakeTelemetry:
    def __init__(self, status=None):
        self.status = status or TelemetryStatus()

    def get_status(self, software=None):
        return self.status


def _engine(devices, software=None, telemetry=None):
    return CheckEngine(
        detector=FakeDetector(devices),
        joystick_manager=JoystickOrderManager(),
        usb_health=FakeUsb(),
        software_detector=FakeSoftware(software),
        telemetry_service=FakeTelemetry(telemetry),
        logger=logging.getLogger("test"),
    )


class CheckEngineTests(unittest.TestCase):
    def test_check_reports_com_restore_needed(self):
        expected = CockpitDevice(
            id="ddu",
            display_name="DDU",
            kind=DeviceKind.DDU,
            bus=DeviceBus.SERIAL,
            serial=SerialIdentity(current_com="COM5", vid="2341", pid="0043", serial_number="ABC", product="DDU"),
        )
        current = CockpitDevice(
            id="ddu-now",
            display_name="DDU",
            kind=DeviceKind.DDU,
            bus=DeviceBus.SERIAL,
            serial=SerialIdentity(current_com="COM8", vid="2341", pid="0043", serial_number="ABC", product="DDU"),
        )
        snapshot = Snapshot(utc_now_iso(), "Rig", "test", [expected], [], [])

        report = _engine([current]).run_check(snapshot)

        self.assertEqual(report.global_status, GlobalStatus.RESTORE_NEEDED)
        self.assertIs(report.device_checks[0].restore_available, True)
        self.assertIn("expected COM5", report.device_checks[0].message)

    def test_check_reports_missing_required_as_critical(self):
        expected = CockpitDevice(
            id="wheel",
            display_name="Wheelbase",
            kind=DeviceKind.WHEEL,
            bus=DeviceBus.HID,
            hid=HidIdentity(name="Wheelbase", vid="1234", pid="5678", joystick_order=1),
        )
        snapshot = Snapshot(utc_now_iso(), "Rig", "test", [expected], [], ["Wheelbase"])

        report = _engine([]).run_check(snapshot)

        self.assertEqual(report.global_status, GlobalStatus.CRITICAL_DEVICE_MISSING)
        self.assertIn("Wheelbase absent", report.issues)

    def test_saved_software_not_detected_becomes_optional_missing_warning(self):
        wheel = CockpitDevice(
            id="wheel",
            display_name="Wheelbase",
            kind=DeviceKind.WHEEL,
            bus=DeviceBus.HID,
            hid=HidIdentity(name="Wheelbase", vid="1234", pid="5678", joystick_order=1),
        )
        snapshot = Snapshot(
            utc_now_iso(),
            "Rig",
            "test",
            [wheel],
            [SoftwareStatus("CrewChief", SoftwareState.RUNNING, required=False)],
            ["Wheelbase"],
        )

        report = _engine(
            [wheel],
            software=[
                SoftwareStatus("SimHub", SoftwareState.NOT_DETECTED),
                SoftwareStatus("CrewChief", SoftwareState.NOT_DETECTED),
            ],
        ).run_check(snapshot)

        self.assertEqual(report.global_status, GlobalStatus.WARNING)
        self.assertIn("CrewChief: Optional missing", report.issues)

    def test_generic_usb_serial_bridge_does_not_match_by_vid_pid_only(self):
        expected = CockpitDevice(
            id="wind-a",
            display_name="Wind Simulator",
            kind=DeviceKind.WIND_SIMULATOR,
            bus=DeviceBus.SERIAL,
            serial=SerialIdentity(current_com="COM5", vid="1A86", pid="7523", product="USB-SERIAL CH340"),
        )
        current = CockpitDevice(
            id="wind-b",
            display_name="Other CH340 Device",
            kind=DeviceKind.ARDUINO_SIMHUB,
            bus=DeviceBus.SERIAL,
            serial=SerialIdentity(current_com="COM8", vid="1A86", pid="7523", product="USB-SERIAL CH340"),
        )
        snapshot = Snapshot(utc_now_iso(), "Rig", "test", [expected], [], [])

        report = _engine([current]).run_check(snapshot)

        self.assertEqual(report.global_status, GlobalStatus.CRITICAL_DEVICE_MISSING)
        self.assertIn("Wind Simulator absent", report.issues)

    def test_generic_usb_serial_bridge_can_match_same_location(self):
        expected = CockpitDevice(
            id="wind-a",
            display_name="Wind Simulator",
            kind=DeviceKind.WIND_SIMULATOR,
            bus=DeviceBus.SERIAL,
            serial=SerialIdentity(
                current_com="COM5",
                vid="1A86",
                pid="7523",
                product="USB-SERIAL CH340",
                location_path="USBROOT(0)#USB(2)",
            ),
        )
        current = CockpitDevice(
            id="wind-b",
            display_name="Wind Simulator",
            kind=DeviceKind.WIND_SIMULATOR,
            bus=DeviceBus.SERIAL,
            serial=SerialIdentity(
                current_com="COM8",
                vid="1A86",
                pid="7523",
                product="USB-SERIAL CH340",
                location_path="USBROOT(0)#USB(2)",
            ),
        )
        snapshot = Snapshot(utc_now_iso(), "Rig", "test", [expected], [], [])

        report = _engine([current]).run_check(snapshot)

        self.assertEqual(report.global_status, GlobalStatus.RESTORE_NEEDED)
        self.assertIn("expected COM5", report.device_checks[0].message)

    def test_telemetry_clipping_warns_on_wheel(self):
        wheel = CockpitDevice(
            id="wheel",
            display_name="Wheelbase",
            kind=DeviceKind.WHEEL,
            bus=DeviceBus.HID,
            hid=HidIdentity(name="Wheelbase", vid="1234", pid="5678", joystick_order=1),
        )
        snapshot = Snapshot(utc_now_iso(), "Rig", "test", [wheel], [], ["Wheelbase"])

        report = _engine(
            [wheel],
            telemetry=TelemetryStatus(source="iRacing", available=True, ffb_clipping_percent=18.0, message="FFB clipping 18%"),
        ).run_check(snapshot, ffb_clipping_threshold=10.0)

        self.assertEqual(report.global_status, GlobalStatus.WARNING)
        self.assertEqual(report.telemetry.source, "iRacing")
        self.assertEqual(report.device_checks[0].ffb_clipping_percent, 18.0)


if __name__ == "__main__":
    unittest.main()
