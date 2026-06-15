import logging
import tempfile
import unittest
from pathlib import Path

from cockpit_guardian.config_manager import ConfigManager
from cockpit_guardian.controller import AppController
from cockpit_guardian.models import CheckReport, GlobalStatus, JoystickOrderResult, Settings, utc_now_iso
from cockpit_guardian.paths import AppPaths


class FakeCheckEngine:
    def __init__(self):
        self.deep_scan_values = []

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
        return CheckReport(timestamp=utc_now_iso(), global_status=GlobalStatus.CHECK_NOT_DONE)


class FakeRestoreEngine:
    pass


class FakeDetector:
    def __init__(self):
        self.deep_scan_values = []

    def detect_all(self, include_windows_metadata=False):
        self.deep_scan_values.append(include_windows_metadata)
        return []


class FakeJoystickManager:
    def read_current_order(self, devices):
        return []

    def compare(self, expected, current):
        return JoystickOrderResult(expected=list(expected), current=list(current), ok=list(expected) == list(current))


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


if __name__ == "__main__":
    unittest.main()
