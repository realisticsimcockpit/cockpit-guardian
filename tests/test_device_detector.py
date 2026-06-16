import unittest
from unittest.mock import patch

from cockpit_guardian.models import DeviceBus, DeviceKind
from cockpit_guardian.services.device_detector import DeviceDetector, _guess_kind
from cockpit_guardian.services.integration_notices import is_generic_usb_serial_bridge, serial_identity_notice


class FakePort:
    def __init__(self, vid=None, pid=None, hwid="", location=None) -> None:
        self.vid = vid
        self.pid = pid
        self.hwid = hwid
        self.location = location


class DeviceDetectorTests(unittest.TestCase):
    def test_wind_name_wins_over_generic_ch340_bridge(self):
        kind = _guess_kind("Wind Simulator USB-SERIAL CH340", DeviceBus.SERIAL, "1A86", "7523")

        self.assertEqual(kind, DeviceKind.WIND_SIMULATOR)

    def test_generic_esp_bridge_falls_back_to_arduino_simhub(self):
        kind = _guess_kind("USB-SERIAL CH340", DeviceBus.SERIAL, "1A86", "7523")

        self.assertEqual(kind, DeviceKind.ARDUINO_SIMHUB)

    def test_ch343_bridge_falls_back_to_arduino_simhub(self):
        kind = _guess_kind("USB-Enhanced-SERIAL CH343", DeviceBus.SERIAL, "1A86", "55D3")

        self.assertEqual(kind, DeviceKind.ARDUINO_SIMHUB)

    def test_product_catalog_distinguishes_wheelbase_from_steering_wheel(self):
        wheelbase = _guess_kind("SIMAGIC Alpha EVO Wheelbase", DeviceBus.HID, "3670", "0500")
        gt_neo = _guess_kind("SIMAGIC GT Neo", DeviceBus.HID)
        active_pedal = _guess_kind("DIY_FFB_PEDAL_JOYSTICK", DeviceBus.HID, "303A", "8331")
        yoke = _guess_kind("Saitek Pro Flight Yoke", DeviceBus.HID, "06A3", "0BAC")
        throttle = _guess_kind("TWCS Throttle", DeviceBus.HID, "044F", "B687")

        self.assertEqual(wheelbase, DeviceKind.WHEEL)
        self.assertEqual(gt_neo, DeviceKind.STEERING_WHEEL)
        self.assertEqual(active_pedal, DeviceKind.ACTIVE_PEDAL)
        self.assertEqual(yoke, DeviceKind.OTHER)
        self.assertEqual(throttle, DeviceKind.OTHER)

    def test_legacy_non_usb_com_port_is_not_cockpit_serial(self):
        port = FakePort(hwid="ACPI\\PNP0501\\0")

        self.assertFalse(DeviceDetector._is_usb_serial_port(port, {"device_instance_id": "ACPI\\PNP0501\\0"}))

    def test_usb_serial_port_is_cockpit_serial_even_without_vid(self):
        port = FakePort(hwid="USB\\VID_303A&PID_8331\\ABC")

        self.assertTrue(DeviceDetector._is_usb_serial_port(port, {}))

    def test_winmm_joysticks_use_oem_names_and_pnp_instance_ids(self):
        detector = DeviceDetector()
        winmm_rows = [
            {"index": 1, "name": "Microsoft PC-joystick driver", "vid": "044F", "pid": "B687"},
            {"index": 2, "name": "Microsoft PC-joystick driver", "vid": "044F", "pid": "B10A"},
        ]
        pnp_rows = [
            {"FriendlyName": "Contrôleur de jeu HID", "InstanceId": "HID\\VID_044F&PID_B687\\A"},
            {"FriendlyName": "Contrôleur de jeu HID", "InstanceId": "HID\\VID_044F&PID_B10A\\B"},
        ]

        def oem_name(vid, pid):
            return {("044F", "B687"): "TWCS Throttle", ("044F", "B10A"): "T.16000M"}[(vid, pid)]

        with patch.object(DeviceDetector, "_read_winmm_joysticks", return_value=winmm_rows), patch.object(
            DeviceDetector, "_windows_joystick_pnp_rows", return_value=pnp_rows
        ), patch.object(DeviceDetector, "_joystick_oem_name", side_effect=oem_name), patch(
            "cockpit_guardian.services.device_detector.run_powershell_json", return_value=[]
        ):
            devices = detector.detect_hid_devices(cache_ttl_seconds=0)

        self.assertEqual([device.display_name for device in devices], ["TWCS Throttle", "T.16000M"])
        self.assertEqual([device.hid.joystick_order for device in devices if device.hid], [2, 3])
        self.assertEqual(devices[0].hid.device_instance_id, "HID\\VID_044F&PID_B687\\A")

    def test_generic_bridge_notice_warns_when_identity_is_weak(self):
        self.assertTrue(is_generic_usb_serial_bridge("1a86", "7523"))

        notice = serial_identity_notice("1A86", "7523", None, None)

        self.assertIn("automatic COM restore is not safe", notice)


if __name__ == "__main__":
    unittest.main()
