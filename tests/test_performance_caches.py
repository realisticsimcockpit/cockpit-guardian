import unittest
from unittest.mock import patch

from cockpit_guardian.services.device_detector import DeviceDetector
from cockpit_guardian.services.software_detector import SoftwareDetector
from cockpit_guardian.services.usb_health import UsbHealthMonitor


class PerformanceCacheTests(unittest.TestCase):
    def test_hid_detection_uses_short_cache(self):
        rows = [{"FriendlyName": "Simagic Alpha", "InstanceId": "HID\\VID_0483&PID_A355\\1"}]
        detector = DeviceDetector()

        with patch.object(DeviceDetector, "_read_directinput_joysticks", return_value=[]), patch.object(
            DeviceDetector, "_read_winmm_joysticks", return_value=[]
        ), patch(
            "cockpit_guardian.services.device_detector.run_powershell_json", return_value=rows
        ) as powershell:
            first = detector.detect_hid_devices(cache_ttl_seconds=60)
            second = detector.detect_hid_devices(cache_ttl_seconds=60)

        self.assertEqual(len(first), 1)
        self.assertEqual(len(second), 1)
        self.assertEqual(powershell.call_count, 2)

    def test_installed_software_uses_cache(self):
        rows = [{"DisplayName": "SimHub", "InstallLocation": "C:\\SimHub"}]
        detector = SoftwareDetector()

        with patch("cockpit_guardian.services.software_detector.run_powershell_json", return_value=rows) as powershell:
            first = detector._installed_programs(cache_ttl_seconds=60)
            second = detector._installed_programs(cache_ttl_seconds=60)

        self.assertEqual(first, second)
        self.assertEqual(powershell.call_count, 1)

    def test_usb_health_uses_cache(self):
        monitor = UsbHealthMonitor()

        with patch.object(UsbHealthMonitor, "_read_windows_events", return_value=[]) as read_events:
            first = monitor.check(cache_ttl_seconds=60)
            second = monitor.check(cache_ttl_seconds=60)

        self.assertIs(first, second)
        self.assertEqual(read_events.call_count, 1)


if __name__ == "__main__":
    unittest.main()
