import logging
import tempfile
import unittest
from pathlib import Path

from cockpit_guardian.config_manager import ConfigManager
from cockpit_guardian.controller import AppController
from cockpit_guardian.models import CheckReport, CockpitDevice, DeviceBus, DeviceKind, GlobalStatus, HidIdentity, JoystickOrderResult, Settings, utc_now_iso
from cockpit_guardian.paths import AppPaths


class FakeCheckEngine:
    def __init__(self):
        self.deep_scan_values = []
        self.current_order = []

    def run_check(
        self,
        snapshot,
        simhub_required=False,
        ffb_clipping_threshold=10.0,
        deep_windows_scan=False,
        software_scan_interval_seconds=300,
        usb_health_scan_interval_seconds=120,
    ):
        self.deep_scan_values.append(deep_windows_scan)
        return CheckReport(
            timestamp=utc_now_iso(),
            global_status=GlobalStatus.CHECK_NOT_DONE,
            joystick_order=JoystickOrderResult(expected=snapshot.joystick_order if snapshot else [], current=list(self.current_order), ok=True),
        )


class FakeRestoreEngine:
    pass


class FakeDetector:
    def __init__(self):
        self.deep_scan_values = []
        self.devices = []

    def detect_all(self, include_windows_metadata=False):
        self.deep_scan_values.append(include_windows_metadata)
        return list(self.devices)


class FakeJoystickManager:
    def __init__(self):
        self.current_order = []
        self.restore_calls = []

    def read_current_order(self, devices):
        return list(self.current_order)

    def compare(self, expected, current):
        return JoystickOrderResult(expected=list(expected), current=list(current), ok=list(expected) == list(current))

    def restore(self, expected, backup_path, current_devices=None):
        self.restore_calls.append((list(expected), backup_path, list(current_devices or [])))
        self.current_order = list(expected)
        return True, "Joystick order restored.", False


class FakeSoftwareDetector:
    def detect(self, required=None, installed_cache_ttl_seconds=300):
        return []


def _controller(tmp_path: str):
    config = ConfigManager(AppPaths(Path(tmp_path)))
    check_engine = FakeCheckEngine()
    detector = FakeDetector()
    controller = AppController(
        config=config,
        check_engine=check_engine,
        restore_engine=FakeRestoreEngine(),
        detector=detector,
        joystick_manager=FakeJoystickManager(),
        software_detector=FakeSoftwareDetector(),
        logger=logging.getLogger("test"),
    )
    return controller, check_engine, detector


class ControllerTests(unittest.TestCase):
    def test_first_check_creates_initial_configuration_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            controller, check_engine, _ = _controller(tmp)
            controller.save_settings(Settings(deep_windows_scan=False))

            controller.check_now()
            controller.check_now()

            self.assertIsNotNone(controller.load_snapshot())
            self.assertEqual(check_engine.deep_scan_values, [False, False])
            self.assertTrue(controller.load_settings().initial_deep_windows_scan_done)

    def test_first_save_configuration_forces_deep_windows_scan_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            controller, _, detector = _controller(tmp)
            controller.save_settings(Settings(deep_windows_scan=False))

            controller.save_configuration()
            controller.save_configuration()

            self.assertEqual(detector.deep_scan_values, [True, False])
            self.assertTrue(controller.load_settings().initial_deep_windows_scan_done)

    def test_first_check_with_snapshot_persists_initial_deep_scan_done(self):
        with tempfile.TemporaryDirectory() as tmp:
            controller, check_engine, _ = _controller(tmp)
            controller.save_settings(Settings(deep_windows_scan=False))
            controller.config.create_snapshot("Rig", [], [], [])

            controller.check_now()
            controller.check_now()

            self.assertEqual(check_engine.deep_scan_values, [True, False])
            self.assertTrue(controller.load_settings().initial_deep_windows_scan_done)

    def test_update_joystick_order_persists_snapshot_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            controller, _, _ = _controller(tmp)
            controller.config.create_snapshot("Rig", [], [], ["Wheel", "Pedals"])

            controller.update_joystick_order(["Pedals", "Wheel"])

            self.assertEqual(controller.load_snapshot().joystick_order, ["Pedals", "Wheel"])

    def test_save_configuration_preserves_desired_joystick_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            controller, _, _ = _controller(tmp)
            controller.config.create_snapshot("Rig", [], [], ["Pedals", "Wheel"])
            controller.joystick_manager.current_order = ["Wheel", "Pedals"]

            controller.save_configuration()

            self.assertEqual(controller.load_snapshot().joystick_order, ["Pedals", "Wheel"])
            self.assertEqual(controller.joystick_manager.restore_calls[0][0], ["Pedals", "Wheel"])

    def test_save_configuration_appends_new_joystick_after_desired_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            controller, _, _ = _controller(tmp)
            controller.config.create_snapshot("Rig", [], [], ["Pedals", "Wheel"])
            controller.joystick_manager.current_order = ["Wheel", "Button Box", "Pedals"]

            controller.save_configuration()

            self.assertEqual(controller.load_snapshot().joystick_order, ["Pedals", "Wheel", "Button Box"])

    def test_update_device_role_persists_snapshot_kind(self):
        with tempfile.TemporaryDirectory() as tmp:
            controller, _, _ = _controller(tmp)
            controller.config.create_snapshot(
                "Rig",
                [CockpitDevice(id="serial-a", display_name="USB Serial", kind=DeviceKind.OTHER, bus=DeviceBus.SERIAL)],
                [],
                [],
            )

            controller.update_device_role("serial-a", "SeatMover")

            self.assertEqual(controller.load_snapshot().devices[0].kind, DeviceKind.SEAT_MOVER)
            self.assertEqual(controller.load_snapshot().devices[0].custom_role, "SeatMover")

    def test_check_repairs_incomplete_saved_joystick_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            controller, check_engine, _ = _controller(tmp)
            check_engine.current_order = ["vJoy Device", "TWCS Throttle", "Wheel"]
            controller.joystick_manager.current_order = ["vJoy Device", "TWCS Throttle", "Wheel"]
            controller.config.create_snapshot(
                "Rig",
                [
                    CockpitDevice(id="vjoy", display_name="vJoy Device", bus=DeviceBus.HID, hid=HidIdentity(name="vJoy Device")),
                    CockpitDevice(id="twcs", display_name="TWCS Throttle", bus=DeviceBus.HID, hid=HidIdentity(name="TWCS Throttle")),
                    CockpitDevice(id="wheel", display_name="Wheel", bus=DeviceBus.HID, hid=HidIdentity(name="Wheel")),
                ],
                [],
                ["TWCS Throttle", "Wheel"],
            )

            controller.check_now()

            self.assertEqual(controller.load_snapshot().joystick_order, ["TWCS Throttle", "Wheel", "vJoy Device"])


if __name__ == "__main__":
    unittest.main()
