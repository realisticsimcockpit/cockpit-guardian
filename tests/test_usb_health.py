import unittest
from unittest.mock import patch

from cockpit_guardian.models import Severity
from cockpit_guardian.services.usb_health import UsbHealthMonitor


class UsbHealthTests(unittest.TestCase):
    def test_officehub_event_is_not_usb_health_warning(self):
        monitor = UsbHealthMonitor()
        rows = [
            {
                "TimeCreated": "2026-06-14T20:00:00Z",
                "Message": "Windows installed package Microsoft.MicrosoftOfficeHub_8wekyb3d8bbwe",
            }
        ]

        with patch.object(UsbHealthMonitor, "_read_windows_events", return_value=rows):
            summary = monitor.check(cache_ttl_seconds=0)

        self.assertEqual(summary.severity, Severity.OK)
        self.assertEqual(summary.events, [])

    def test_usb_device_not_recognized_is_critical(self):
        monitor = UsbHealthMonitor()
        rows = [
            {
                "TimeCreated": "2026-06-14T20:00:00Z",
                "Message": "USB device not recognized after enumeration failed.",
            }
        ]

        with patch.object(UsbHealthMonitor, "_read_windows_events", return_value=rows):
            summary = monitor.check(cache_ttl_seconds=0)

        self.assertEqual(summary.severity, Severity.CRITICAL)
        self.assertEqual(len(summary.events), 1)


if __name__ == "__main__":
    unittest.main()
