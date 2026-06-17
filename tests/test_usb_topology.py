import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch

from cockpit_guardian.models import CockpitDevice, DeviceBus, HidIdentity
from cockpit_guardian.services.usb_speed_scanner import UsbSpeedRecord
from cockpit_guardian.services.usb_topology import UsbTopologyDetector


class UsbTopologyTests(unittest.TestCase):
    def test_detects_usb3_capable_path_from_root_hub30(self):
        detector = UsbTopologyDetector()

        info = detector.infer_connection(parent="USB\\ROOT_HUB30\\4&1234", name="Pedals")

        self.assertEqual(info.usb_generation, "USB 3.x")
        self.assertEqual(info.confidence, "medium")

    def test_detects_usb2_path_from_high_speed_hint(self):
        detector = UsbTopologyDetector()

        info = detector.infer_connection(bus_description="USB 2.0 High-Speed device")

        self.assertEqual(info.usb_generation, "USB 2.0")
        self.assertEqual(info.negotiated_speed_mbps, 480)

    def test_generic_ch340_bridge_reports_unknown_speed(self):
        detector = UsbTopologyDetector()

        info = detector.infer_connection(name="Wind Simulator", vid="1A86", pid="7523")

        self.assertEqual(info.label, "USB serial bridge")
        self.assertIsNone(info.usb_generation)
        self.assertEqual(info.confidence, "low")

    def test_generic_ch343_bridge_reports_unknown_speed(self):
        detector = UsbTopologyDetector()

        info = detector.infer_connection(name="USB-Enhanced-SERIAL CH343", vid="1A86", pid="55D3")

        self.assertEqual(info.label, "USB serial bridge")
        self.assertEqual(info.source, "WCH CH343 USB serial bridge")
        self.assertEqual(info.confidence, "low")

    def test_usb_identity_without_topology_requires_speed_scan(self):
        detector = UsbTopologyDetector()

        info = detector.infer_connection(name="SIMAGIC Alpha EVO Wheelbase", vid="3670", pid="0500")

        self.assertEqual(info.label, "USB speed scan needed")
        self.assertEqual(info.source, "Windows PnP identity")
        self.assertIn("USBTreeView", info.note)

    def test_cached_usb_speed_annotates_matching_device(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp) / "usb_speed_cache.json"
            detector = UsbTopologyDetector(speed_cache_path=cache)
            detector._save_speed_cache(
                [
                    UsbSpeedRecord(
                        vid="3670",
                        pid="0500",
                        label="USB Full-Speed",
                        usb_generation="USB 1.1",
                        negotiated_speed_mbps=12,
                        hub_path="hub",
                        port=3,
                    )
                ]
            )
            device = CockpitDevice(
                id="wheel",
                display_name="SIMAGIC Alpha EVO Wheelbase",
                bus=DeviceBus.HID,
                hid=HidIdentity(name="SIMAGIC Alpha EVO Wheelbase", vid="3670", pid="0500"),
            )

            detector.annotate_devices([device])

            self.assertEqual(device.usb.label, "USB Full-Speed")
            self.assertEqual(device.usb.negotiated_speed_mbps, 12)
            self.assertEqual(device.usb.source, "USB hub speed scan")

    def test_speed_scan_failure_keeps_existing_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp) / "usb_speed_cache.json"
            detector = UsbTopologyDetector(speed_cache_path=cache)
            detector._save_speed_cache(
                [
                    UsbSpeedRecord(
                        vid="303A",
                        pid="8331",
                        label="USB Full-Speed",
                        usb_generation="USB 1.1",
                        negotiated_speed_mbps=12,
                        hub_path="hub",
                        port=1,
                    )
                ]
            )

            with patch("cockpit_guardian.services.usb_topology.scan_usb_speed_records", return_value=None):
                records = detector.ensure_speed_cache(force=True)

            self.assertEqual(len(records), 1)
            self.assertEqual(records[0].vid_pid, "303A:8331")


if __name__ == "__main__":
    unittest.main()
