import unittest

from cockpit_guardian.models import DeviceBus, DeviceKind
from cockpit_guardian.services.device_detector import _guess_kind
from cockpit_guardian.services.integration_notices import is_generic_usb_serial_bridge, serial_identity_notice


class DeviceDetectorTests(unittest.TestCase):
    def test_wind_name_wins_over_generic_ch340_bridge(self):
        kind = _guess_kind("Wind Simulator USB-SERIAL CH340", DeviceBus.SERIAL, "1A86", "7523")

        self.assertEqual(kind, DeviceKind.WIND_SIMULATOR)

    def test_generic_esp_bridge_falls_back_to_arduino_simhub(self):
        kind = _guess_kind("USB-SERIAL CH340", DeviceBus.SERIAL, "1A86", "7523")

        self.assertEqual(kind, DeviceKind.ARDUINO_SIMHUB)

    def test_generic_bridge_notice_warns_when_identity_is_weak(self):
        self.assertTrue(is_generic_usb_serial_bridge("1a86", "7523"))

        notice = serial_identity_notice("1A86", "7523", None, None)

        self.assertIn("automatic COM restore is not safe", notice)


if __name__ == "__main__":
    unittest.main()
