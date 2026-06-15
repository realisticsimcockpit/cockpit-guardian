import unittest

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


if __name__ == "__main__":
    unittest.main()
